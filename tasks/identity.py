import logging
import traceback
from livekit.agents import AgentTask, function_tool
from utils.helpers import load_prompt
from models.patient import IdentityDetails

logger = logging.getLogger("medical-triage.tasks.identity")

class IdentityTask(AgentTask[IdentityDetails]):
    def __init__(self, chat_ctx=None):
        try:
            system_instruction = load_prompt(
                "identity_task.md", 
                fallback="Ask for the patient's full name and age."
            )
            self.welcome_instruction = load_prompt(
                "identity_welcome.md",
                fallback="Could you please tell me your full name and age?"
            )
            super().__init__(instructions=system_instruction, chat_ctx=chat_ctx)
            logger.info("IdentityTask initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize IdentityTask: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def on_enter(self) -> None:
        try:
            logger.info("Prompting user for identity details.")
            await self.session.generate_reply(instructions=self.welcome_instruction)
        except Exception as e:
            logger.error(f"Error in IdentityTask on_enter: {str(e)}")
            logger.error(traceback.format_exc())

    @function_tool
    async def save_identity(self, name: str, age: int) -> None:
        """Call this tool ONLY when you have successfully extracted both the name and the age of the patient."""
        try:
            logger.info(f"💾 Saving Identity: {name}, Age: {age}")
            result = IdentityDetails(name=name, age=age)
            self.complete(result)
        except Exception as e:
            logger.error(f"Error in save_identity tool: {str(e)}")
            logger.error(traceback.format_exc())