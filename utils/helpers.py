import os
import logging
import traceback

logger = logging.getLogger("medical-triage.utils")

def load_prompt(filename: str, fallback: str = "") -> str:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", filename)
        
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        logger.error(f"Failed to load prompt file {filename}: {str(e)}")
        logger.error(traceback.format_exc())
        return fallback
