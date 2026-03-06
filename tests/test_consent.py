import pytest
from livekit.agents import AgentSession
from tasks.consent import ConsentTask

@pytest.mark.asyncio
async def test_consent_task_approval(setup_test_llm):
    llm = setup_test_llm

    # Using async with AgentSession as recommended in docs [cite: 28, 33]
    async with AgentSession(llm=llm) as session:
        # Start the specific task instead of the whole agent
        await session.start(agent=ConsentTask())
        
        # User agrees
        result = await session.run(user_input="Yes, I agree to the recording.")

        # Assert 1: The agent should call the 'consent_given' tool
        result.expect.next_event().is_function_call(name="consent_given")
        result.expect.next_event().is_function_call_output(output="", is_error=False) # The tool doesn't return data, just completes the task
        
        # Assert 2: The agent should not output any more events
        result.expect.no_more_events()

@pytest.mark.asyncio
async def test_consent_task_denial(setup_test_llm):
    llm = setup_test_llm

    async with AgentSession(llm=llm) as session:
        await session.start(agent=ConsentTask())
        
        # User disagrees
        result = await session.run(user_input="No, I don't want to be recorded.")
        
        # Assert: The agent should call the 'consent_denied' tool
        result.expect.next_event().is_function_call(name="consent_denied")
        result.expect.next_event().is_function_call_output(output="", is_error=False) # The tool doesn't return data, just completes the task
        result.expect.no_more_events()