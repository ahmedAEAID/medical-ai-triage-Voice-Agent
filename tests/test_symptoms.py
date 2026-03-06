import pytest
import json
from livekit.agents import AgentSession
from tasks.symptoms import SymptomsTask

@pytest.mark.asyncio
async def test_symptoms_incomplete_data(setup_test_llm):
    llm = setup_test_llm

    async with AgentSession(llm=llm) as session:
        await session.start(agent=SymptomsTask())

        # Only provide complaint and duration, missing severity
        result1 = await session.run(user_input="I've had a headache for 3 days.")
        
        # The agent should NOT call 'save_symptoms'. Instead, it should ask for severity.
        await result1.expect.next_event().is_message(role="assistant").judge(
            llm, intent="Acknowledges the headache and asks the patient to rate the severity on a scale of 1 to 10."
        )
        
        # Now provide severity
        result2 = await session.run(user_input="It's pretty bad, maybe an 8.")
        
        # Now it should call the tool
        tool_call = result2.expect.next_event().is_function_call(name="save_symptoms")
        args = tool_call.event().item.arguments
        args = json.loads(args) if isinstance(args, str) else args
        assert args["duration_days"] == 3
        assert args["severity_level"] == 8
        assert "headache" in args["primary_complaint"].lower()
        
        result2.expect.next_event().is_function_call_output(output="", is_error=False) 
        result2.expect.no_more_events()