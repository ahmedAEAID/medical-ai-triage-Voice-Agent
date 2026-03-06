import pytest
import json
from livekit.agents import AgentSession
from tasks.identity import IdentityTask

@pytest.mark.asyncio
async def test_identity_extraction(setup_test_llm):
    llm = setup_test_llm

    async with AgentSession(llm=llm) as session:
        await session.start(agent=IdentityTask())

        # Test Turn 1: Check the welcome message using the Judge LLM
        result1 = await session.run(user_input="Hello") 
        await result1.expect.next_event().is_message(role="assistant").judge(
            llm, intent="Politely asks the user for their full name and age." 
        )

        # Test Turn 2: Provide data and check if tool is called correctly
        result2 = await session.run(user_input="My name is John Doe and I am 45 years old.") 
        
        # Verify function call and arguments
        tool_call = result2.expect.next_event().is_function_call(name="save_identity")
        
        # Optional: You can explicitly check arguments if needed
        args = tool_call.event().item.arguments
        args = json.loads(args) if isinstance(args, str) else args
        assert args["name"].lower() == "john doe"
        assert args["age"] == 45
        
        result2.expect.next_event().is_function_call_output(output="", is_error=False)
        
        result2.expect.no_more_events()