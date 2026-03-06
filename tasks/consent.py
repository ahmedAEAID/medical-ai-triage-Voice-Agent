# tasks/consent.py
import logging
import traceback
from livekit.agents import AgentTask, function_tool
from utils.helpers import load_prompt

logger = logging.getLogger("medical-triage.tasks.consent")

class ConsentTask(AgentTask[bool]):
    def __init__(self, chat_ctx=None):
        try:
            # Load the main system instructions for the task
            system_instruction = load_prompt(
                "consent_task.md", 
                fallback="You are a medical assistant. Ask for recording consent."
            )
            
            # Load the welcome message for the on_enter method
            self.welcome_instruction = load_prompt(
                "consent_welcome.md",
                fallback="Ask for recording consent."
            )

            super().__init__(
                instructions=system_instruction,
                chat_ctx=chat_ctx,
            )
            logger.info("ConsentTask initialized successfully.")
        except Exception as e:
            logger.error(f"Error during ConsentTask initialization: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def on_enter(self) -> None:
        try:
            logger.info("Entering ConsentTask. Prompting user for consent.")
            await self.session.generate_reply(
                instructions=self.welcome_instruction
            )
        except Exception as e:
            logger.error(f"Error in ConsentTask on_enter: {str(e)}")
            logger.error(traceback.format_exc())

    @function_tool
    async def consent_given(self) -> None:
        """Call this tool when the user explicitly agrees or says yes to recording."""
        try:
            logger.info("✅ User granted consent.")
            self.complete(True)
        except Exception as e:
            logger.error(f"Error executing consent_given tool: {str(e)}")
            logger.error(traceback.format_exc())

    @function_tool
    async def consent_denied(self) -> None:
        """Call this tool when the user refuses, says no, or declines recording."""
        try:
            logger.warning("❌ User denied consent.")
            self.complete(False)
        except Exception as e:
            logger.error(f"Error executing consent_denied tool: {str(e)}")
            logger.error(traceback.format_exc())
    