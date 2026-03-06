import logging
import asyncio
import random
from datetime import datetime, timedelta

logger = logging.getLogger("medical-triage.tools.scheduling")

async def book_appointment(patient_name: str, department: str) -> str:
    """
    Simulates booking an appointment in the hospital's scheduling database.
    Returns a confirmation string with date, time, and reference ID.
    """
    try:
        logger.info(f"Accessing hospital database to book appointment for {patient_name} in {department}...")
        
        # Simulate network/database delay
        await asyncio.sleep(1.5)
        
        # Generate a mock appointment date (2 days from now)
        appt_date = datetime.now() + timedelta(days=2)
        appt_time = "10:00 AM"
        reference_id = f"REF-{random.randint(1000, 9999)}"
        
        confirmation_msg = (
            f"Appointment confirmed for {patient_name} with the {department} department "
            f"on {appt_date.strftime('%A, %B %d')} at {appt_time}. "
            f"Reference ID: {reference_id}"
        )
        
        logger.info(f"✅ Appointment booked successfully: {reference_id}")
        return confirmation_msg
        
    except Exception as e:
        logger.error(f"Database error while booking appointment: {str(e)}")
        return "SYSTEM_ERROR: Unable to book appointment at this time."