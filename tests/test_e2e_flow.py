import pytest
import asyncio
from livekit.agents import AgentSession, mock_tools
from agents.receptionist import ReceptionistAgent
from agents.ortho_specialist import OrthoSpecialistAgent

@pytest.mark.asyncio
async def test_full_system_e2e_flow(setup_test_llm):
    """
    E2E Test: Receptionist -> Consent -> Intake -> Ortho Handoff -> Scheduling -> End Call
    """
    llm = setup_test_llm
    with mock_tools(
        ReceptionistAgent, {"end_call": lambda: "Call ended successfully in test mode"}
    ), mock_tools(
        OrthoSpecialistAgent, {"end_call": lambda: "Call ended successfully in test mode"}
    ):
        async with AgentSession(llm=llm) as session:
            # 1. Start with Receptionist
            await session.start(agent=ReceptionistAgent())

            # Turn 1: Welcome & Consent
            res1 = await session.run(user_input="Hi, I need to see a doctor.")
            await res1.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Politely asks for recording consent."
            )

            # Turn 2: Consent Given -> Moves to Identity
            res2 = await session.run(user_input="Yes, I consent.")
            res2.expect.contains_function_call(name="consent_given")
            
            await asyncio.sleep(1.0)
            
            # Turn 3: Identity Given -> Moves to Symptoms
            res3 = await session.run(user_input="My name is Omar and I am 40 years old.")
            res3.expect.contains_function_call(name="save_identity")
            
            await asyncio.sleep(1.0)

            # Turn 4: Symptoms Given -> Receptionist takes back control
            res4 = await session.run(user_input="I injured my shoulder playing tennis 3 days ago. The pain is 7 out of 10.")
            res4.expect.contains_function_call(name="save_symptoms")
            
            await asyncio.sleep(1.0)
            
            # Turn 5: Trigger Proactive Summary and Handoff
            res5 = await session.run(user_input="That's all the info.")

            # 1. Verify the receptionist summarizes the data
            await res5.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Thanks Omar, acknowledges the shoulder injury and says he will be transferred."
            )

            # 2. Verify the handoff to Orthopedics happens
            res5.expect.next_event().is_agent_handoff(new_agent_type=OrthoSpecialistAgent)
            
            # 3. Verify Ortho Specialist takes over automatically and asks the follow-up question
            await res5.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Introduces himself as the Orthopedic Specialist, mentions the shoulder injury, and asks a follow-up question."
            )
            res5.expect.no_more_events()
            
            # 💡 التعديل 2: حذفنا أسطر الحقن اليدوي لأن الـ AgentSession قام بها بالفعل!

            # Turn 6: Interact with Ortho Specialist
            res6 = await session.run(user_input="I can't lift my arm above my head at all.")
            
            # Doctor should call the scheduling tool
            res6.expect.contains_function_call(name="schedule_appointment")
            res6.expect.skip_next(2) # Skip tool output events
            
            # Relay the scheduled appointment info
            await res6.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Informs the patient about the scheduled appointment details (Date, Time, Reference ID)."
            )

            # Turn 7: Acknowledge appointment -> Triggers End Call
            res7 = await session.run(user_input="Perfect, thank you doctor. That's all.")
            
            # The doctor should gracefully end the call
            res7.expect.contains_function_call(name="end_call")