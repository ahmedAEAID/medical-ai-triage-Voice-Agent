import logging
import traceback
from livekit.agents import Agent, RunContext, function_tool
from livekit.agents.beta.tools import EndCallTool
from utils.helpers import load_prompt
from tools.scheduling import book_appointment

logger = logging.getLogger("medical-triage.agents.ortho_specialist")

class OrthoSpecialistAgent(Agent):
    def __init__(self, chat_ctx, patient_name: str, primary_complaint: str, duration: int, severity: int):
        try:
            raw_instructions = load_prompt(
                "ortho_specialist.md",
                fallback="You are an orthopedic specialist."
            )
            
            # Inject variables directly into the complete prompt
            full_instructions = raw_instructions.format(
                patient_name=patient_name,
                primary_complaint=primary_complaint,
                duration=duration,
                severity=severity
            )
            
            # Initialize the prebuilt EndCallTool
            end_call_tool = EndCallTool(
                extra_description="Use this tool to gracefully end the call ONLY AFTER you have asked your follow-up questions and provided final instructions to the patient.",
                delete_room=True,
                end_instructions="Thank the patient for calling the Orthopedic AI Triage, wish them a speedy recovery, and say a warm goodbye."
            )
            
            super().__init__(
                instructions=full_instructions, 
                chat_ctx=chat_ctx,
                tools=end_call_tool.tools
            )
            
            self.patient_name = patient_name
            self.primary_complaint = primary_complaint
            
            raw_welcome = load_prompt(
                "ortho_welcome.md",
                fallback=f"Greet the patient {patient_name} and ask about their {primary_complaint}."
            )
            
            self.welcome_prompt = raw_welcome.format(
                patient_name=self.patient_name,
                primary_complaint=self.primary_complaint
            )
            
            logger.info("OrthoSpecialistAgent initialized with patient context and EndCallTool.")
        except Exception as e:
            logger.error(f"Failed to initialize OrthoSpecialistAgent: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def on_enter(self) -> None:
        try:
            logger.info("OrthoSpecialistAgent took control of the session.")
            await self.session.generate_reply(instructions=self.welcome_prompt)
        except Exception as e:
            logger.error(f"Error in OrthoSpecialistAgent on_enter: {str(e)}")
            logger.error(traceback.format_exc())
    
    
    @function_tool
    async def schedule_appointment(self, context: RunContext) -> str:
        """Call this tool to schedule an in-person X-ray or doctor appointment for the patient."""
        try:
            logger.info("Agent requested appointment scheduling...")
            result = await book_appointment(self.patient_name, "Orthopedics")
            return result
        except Exception as e:
            logger.error(f"Error executing schedule_appointment tool: {str(e)}")
            logger.error(traceback.format_exc())
            return "Failed to schedule appointment due to an internal error."