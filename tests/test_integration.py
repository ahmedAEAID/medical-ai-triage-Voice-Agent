import pytest
from livekit.agents import AgentSession, mock_tools
from agents.receptionist import ReceptionistAgent
from tasks.consent import ConsentTask
from tasks.identity import IdentityTask
from tasks.symptoms import SymptomsTask
import asyncio

@pytest.mark.asyncio
async def test_full_patient_intake_integration(setup_test_llm):
    """
    Integration Test: Verifies the full flow from Receptionist -> Consent -> Identity -> Symptoms -> Summary
    """
    llm = setup_test_llm

    # Start the session with the main Orchestrator Agent
    with mock_tools(
        ReceptionistAgent, {"end_call": lambda: "Call ended successfully in test mode"}
    ):
        async with AgentSession(llm=llm) as session:
            await session.start(agent=ReceptionistAgent())

            # Turn 1: User says hello. Agent should ask for consent.
            result1 = await session.run(user_input="Hello there.")
            await result1.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Introduces the system and asks for recording consent."
            )

            # Turn 2: User gives consent. Agent should transition to IdentityTask.
            result2 = await session.run(user_input="Yes, I agree to the recording.")
            
            # It should call the consent tool internally
            result2.expect.next_event().is_function_call(name="consent_given")
            result2.expect.next_event().is_function_call_output(output="", is_error=False) # The tool doesn't return data, just completes the task
            # We don't expect the Identity welcome message here because the turn completes on tool call.
            await asyncio.sleep(2.0)
            
            result2.expect.next_event().is_agent_handoff(new_agent_type=ReceptionistAgent) # The agent should handoff to itself but now with the IdentityTask active
            result2.expect.skip_next() # Skip the welcome message from IdentityTask since it's not relevant to this test
            result2.expect.next_event().is_agent_handoff(new_agent_type=IdentityTask) # The agent should handoff to itself but now with the SymptomsTask active
            

            # Turn 3: User provides Identity. Agent should transition to SymptomsTask.
            result3 = await session.run(user_input="My name is Ahmed and I am 35 years old.")
            
            # It should save identity
            result3.expect.next_event().is_function_call(name="save_identity")
            result3.expect.skip_next()
            
            # We don't expect the Identity welcome message here because the turn completes on tool call.
            await asyncio.sleep(2.0)
            
            # Then ask for symptoms
            result3.expect.contains_agent_handoff(new_agent_type=SymptomsTask)
            await asyncio.sleep(2.0)
            # Turn 4: User provides Symptoms. Agent should finish TaskGroup and summarize.
            result4 = await session.run(user_input="I have a mild headache and a runny nose for 2 days, severity is 3 out of 10.")

            # It should save symptoms
            result4.expect.next_event().is_function_call(name="save_symptoms")
            result4.expect.skip_next()

            await asyncio.sleep(1.5)
            result4.expect.contains_agent_handoff(new_agent_type=ReceptionistAgent)

            # Turn 5: Proactive Summary and asking for confirmation to end call
            result5 = await session.run(user_input="That's all the info.")

            # Now we expect a message asking for confirmation
            await result5.expect.next_event().is_message(role="assistant").judge(
                llm,
                intent="Thanks the user, acknowledges their symptoms, handles the non-orthopedic routing (e.g., advising a general doctor or offering general guidance), and clearly ASKS the user if they are ready to end the call."
            )