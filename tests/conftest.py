import os
import sys
import logging
from dotenv import load_dotenv

import pytest
from livekit import agents

# Ensure our app modules can be found
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_root)

# Load ENV variables for tests
load_dotenv(".env.local")

# As per Livekit docs, suppress verbose CLI output for tests [cite: 26]
# Initialize logger to suppress CLI output. The equivalent in Python is adjusting log levels.
logging.getLogger("livekit").setLevel(logging.WARNING)
logging.getLogger("livekit.agents").setLevel(logging.WARNING)

@pytest.fixture(scope="session")
def setup_test_llm():
    """
    Creates a single LLM instance used for evaluating (judging) agent behavior.
    """
    from livekit.plugins import openai
    llm = openai.LLM(
        model=os.getenv("MODEL_NAME_LLM", "qwen3-235b-a22b-instruct-2507"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=0.0  # Zero temp is better for deterministic evaluation
    )
    return llm