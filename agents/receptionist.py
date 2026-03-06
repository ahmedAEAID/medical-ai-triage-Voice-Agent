import logging
import traceback
import asyncio
from livekit.agents import Agent, get_job_context, RunContext, function_tool
from livekit.agents.beta.tools import EndCallTool
from utils.helpers import load_prompt
from tasks.consent import ConsentTask
from tasks.intake_group import run_patient_intake
from agents.ortho_specialist import OrthoSpecialistAgent

logger = logging.getLogger("medical-triage.agents.receptionist")

class ReceptionistAgent(Agent):
    def __init__(self):
        try:
            instructions = load_prompt(
                "receptionist_agent.md",
                fallback="You are a medical receptionist. Guide the patient through intake."
            )
            
            # Initialize the prebuilt EndCallTool
            end_call_tool = EndCallTool(
                extra_description="Use this tool ONLY if the patient's complaint is NOT related to orthopedics AND they have explicitly confirmed they are ready to end the call.",
                delete_room=True,
                end_instructions="Thank the patient for their time, wish them well, and say goodbye."
            )

            # Pass the tools list to the parent Agent class
            super().__init__(
                instructions=instructions,
                tools=end_call_tool.tools
            )
            
            logger.info("ReceptionistAgent initialized successfully.")
            self.patient_name = None
            self.primary_complaint = None
            self.severity = None
            self.duration = None
            
        except Exception as e:
            logger.error(f"Failed to initialize ReceptionistAgent: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def on_enter(self) -> None:
        try:
            logger.info("ReceptionistAgent entered the session. Starting workflow.")

            # Step 1: Execute Consent Task
            logger.info("Triggering ConsentTask...")
            consent_task = ConsentTask(chat_ctx=self.chat_ctx)
            has_consent = await consent_task

            if not has_consent:
                logger.warning("Consent denied by user. Initiating graceful shutdown.")
                await self.session.generate_reply(
                    instructions="Politely inform the user that you cannot proceed without recording consent, wish them well, and say goodbye."
                )
                await asyncio.sleep(4) 
                
                try:
                    job_ctx = get_job_context()
                    job_ctx.shutdown()
                except RuntimeError:
                    logger.warning("No JobContext found. Skipping shutdown (Likely running in Test environment).")
                return

            # Step 2: Execute Patient Intake TaskGroup
            logger.info("Consent granted. Triggering Patient Intake TaskGroup...")
            intake_results = await run_patient_intake(chat_ctx=self.chat_ctx)
            
            identity_data = intake_results.get("identity_step")
            symptoms_data = intake_results.get("symptoms_step")

            logger.info(f"Intake completed. Identity: {identity_data}, Symptoms: {symptoms_data}")
            self.patient_name = identity_data.name
            self.primary_complaint = symptoms_data.primary_complaint
            self.severity = symptoms_data.severity_level
            self.duration = symptoms_data.duration_days

            # Step 3: Acknowledge and evaluate where to route the patient
            summary_instruction = f"""
            Thank {self.patient_name} for providing their information.
            Acknowledge that they are experiencing {self.primary_complaint}.
            
            ROUTING RULES:
            - If the complaint is related to bones, muscles, joints, or physical injuries, you MUST immediately call the `transfer_to_orthopedics` tool in this exact response. Do not just say you will transfer them, actually call the tool.
            - If it is something else, advise them regarding a general doctor, and ASK if they have any other questions or if you can end the call now. Do NOT call the `end_call` tool yet.
            """
            
            await self.session.generate_reply(instructions=summary_instruction)
            
        except Exception as e:
            logger.error(f"Critical error in ReceptionistAgent workflow: {str(e)}")
            logger.error(traceback.format_exc())
            
            try:
                # Need to check if an LLM is attached before replying
                if self.session and self.session.llm:
                    await self.session.generate_reply(
                        instructions="Apologize to the user that a system error occurred and you must end the call."
                    )
                    await asyncio.sleep(3)
                
                try:
                    get_job_context().shutdown()
                except RuntimeError:
                     logger.warning("No JobContext found. Skipping fallback shutdown.")

            except Exception as inner_e:
                logger.critical(f"Failed to execute fallback shutdown reply: {str(inner_e)}")
                try:
                    get_job_context().shutdown()
                except RuntimeError:
                    pass
    
    @function_tool
    async def transfer_to_orthopedics(self) -> Agent:
        """Call this tool ONLY when the patient's primary complaint is related to bones, joints, muscles, or physical injuries (e.g., knee pain, back pain, fractures)."""
        try:
            logger.info("Initiating Handoff to OrthoSpecialistAgent...")
            
            return OrthoSpecialistAgent(
                chat_ctx=self.chat_ctx, 
                patient_name=self.patient_name, 
                primary_complaint=self.primary_complaint, 
                duration=self.duration, 
                severity=self.severity
            )
        except Exception as e:
            logger.error(f"Error during handoff to orthopedics: {str(e)}")
            logger.error(traceback.format_exc())
            # raise