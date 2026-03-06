import pytest
from livekit.agents import AgentSession, mock_tools
from agents.ortho_specialist import OrthoSpecialistAgent

@pytest.mark.asyncio
async def test_ortho_specialist_workflow(setup_test_llm):
    """
    Unit Test: Verifies that OrthoSpecialistAgent asks a follow-up, 
    schedules an appointment, and cleanly ends the call.
    """
    llm = setup_test_llm

    # Inject mock context
    agent = OrthoSpecialistAgent(
        chat_ctx=None,
        patient_name="Sarah",
        primary_complaint="severe knee pain",
        duration=5,
        severity=8
    )
    with mock_tools(OrthoSpecialistAgent, {"end_call": lambda: "Call ended successfully in test mode"}):
        async with AgentSession(llm=llm) as session:
            await session.start(agent=agent)

            # Turn 1: Initialization / Welcome
            # The agent should proactively welcome the patient based on context
            result1 = await session.run(user_input="Hello, doctor.")
            
            await result1.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Greets Sarah, acknowledges her severe knee pain, and asks a relevant orthopedic follow-up question."
            )

            # Turn 2: Patient answers the follow-up question
            result2 = await session.run(user_input="Yes, it swells up when I walk up the stairs.")
            
            # The agent MUST call the schedule_appointment tool
            result2.expect.next_event().is_function_call(name="schedule_appointment")
            
            # Skip the tool output event
            result2.expect.skip_next()
            
            # Wait for the agent to relay the appointment info
            await result2.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Informs the patient about the scheduled appointment details (Date, Time, Reference ID)."
            )

            # Turn 3: Patient says thank you, agent should trigger EndCallTool
            result3 = await session.run(user_input="Thank you very much, that sounds good.")
            
            # Verify the end_call tool is triggered
            result3.expect.next_event().is_function_call(name="end_call")