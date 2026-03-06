import logging
import traceback
from livekit.agents.beta.workflows import TaskGroup
from tasks.identity import IdentityTask
from tasks.symptoms import SymptomsTask

logger = logging.getLogger("medical-triage.tasks.intake_group")

async def run_patient_intake(chat_ctx):
    """Orchestrates the patient intake process by grouping Identity and Symptoms tasks."""
    try:
        logger.info("Initializing Patient Intake TaskGroup...")
        group = TaskGroup()
        
        group.add(
            lambda: IdentityTask(chat_ctx=chat_ctx), 
            id="identity_step", 
            description="Collects the patient's name and age."
        )
        
        group.add(
            lambda: SymptomsTask(chat_ctx=chat_ctx), 
            id="symptoms_step", 
            description="Collects the primary complaint, duration, and severity."
        )

        logger.info("Starting TaskGroup execution.")
        
        try:
            result = await group
        except RuntimeError as e:
            if "already done" in str(e):
                logger.warning("TaskGroup completed internally and raised an already done error. Capturing results safely.")
                # If it's already done, we can safely access the results
                logger.warning(f"Accessing TaskGroup results after already done error: {group}")
                return group
            else:
                raise e
        
        logger.info("TaskGroup execution completed successfully.")
        return result.task_results

    except Exception as e:
        logger.error(f"Error executing Patient Intake TaskGroup: {str(e)}")
        logger.error(traceback.format_exc())
        raise