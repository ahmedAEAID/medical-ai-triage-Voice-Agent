import logging
import traceback
from livekit.agents import AgentTask, function_tool
from utils.helpers import load_prompt
from models.patient import SymptomDetails

logger = logging.getLogger("medical-triage.tasks.symptoms")

class SymptomsTask(AgentTask[SymptomDetails]):
    def __init__(self, chat_ctx=None):
        try:
            system_instruction = load_prompt(
                "symptoms_task.md", 
                fallback="Ask for the primary complaint, duration, and severity (1-10)."
            )
            self.welcome_instruction = load_prompt(
                "symptoms_welcome.md",
                fallback="What is the main reason for your call today?"
            )
            super().__init__(instructions=system_instruction, chat_ctx=chat_ctx)
            logger.info("SymptomsTask initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize SymptomsTask: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def on_enter(self) -> None:
        try:
            logger.info("Prompting user for medical symptoms.")
            await self.session.generate_reply(instructions=self.welcome_instruction)
        except Exception as e:
            logger.error(f"Error in SymptomsTask on_enter: {str(e)}")
            logger.error(traceback.format_exc())

    @function_tool
    async def save_symptoms(self, primary_complaint: str, duration_days: int, severity_level: int) -> None:
        """Call this tool when you have collected the complaint, how many days it lasted, and severity from 1 to 10."""
        try:
            logger.info(f"💾 Saving Symptoms: {primary_complaint}, {duration_days} days, Severity: {severity_level}")
            result = SymptomDetails(
                primary_complaint=primary_complaint, 
                duration_days=duration_days, 
                severity_level=severity_level
            )
            self.complete(result)
        except Exception as e:
            logger.error(f"Error in save_symptoms tool: {str(e)}")
            logger.error(traceback.format_exc())