import os
import sys
import logging
import traceback
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentSession, JobContext, metrics
from livekit.plugins import openai, silero
from livekit.agents.voice.events import MetricsCollectedEvent

from agents.receptionist import ReceptionistAgent

load_dotenv(".env.local")

logger = logging.getLogger("medical-triage-system")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from custom_plugin.xtts import CustomXTTS
    logger.info("Custom XTTS plugin imported successfully.")
except ImportError as e:
    logger.error(f"Failed to import CustomXTTS. Ensure 'custom_plugin' directory exists. Error: {e}")
    sys.exit(1)


async def entrypoint(ctx: JobContext):
    logger.info(f"Starting new job processing. Job ID: {ctx.job.id}")
    
    try:
        await ctx.connect()
        logger.info(f"Successfully connected to room: {ctx.room.name}")

        stt_plugin = openai.STT(
            model=os.getenv("STT_MODEL_ID"),
            api_key=os.getenv("STT_API_KEY"),
            base_url=os.getenv("STT_BASE_URL")
        )

        llm_plugin = openai.LLM(
            model=os.getenv("MODEL_NAME_LLM"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        tts_plugin = CustomXTTS(
            base_url=os.getenv("XTTS_BASE_URL"),
            voice=os.getenv("VOICE_WAV_NAME"),
            language=os.getenv("XTTS_LANGUAGE")
        )

        session = AgentSession(
            stt=stt_plugin,
            llm=llm_plugin,
            tts=tts_plugin,
            vad=silero.VAD.load(),
            user_away_timeout=60.0 
        )

        usage_collector = metrics.UsageCollector()
        
        @session.on("metrics_collected")
        def on_metrics_collected(event: MetricsCollectedEvent):
            metrics.log_metrics(event.metrics)
            usage_collector.collect(event.metrics)

        logger.info("AgentSession initialized. Preparing to start Receptionist Agent...")
        
        agent = ReceptionistAgent()
        await session.start(room=ctx.room, agent=agent)
        
    except Exception as e:
        logger.error(f"Critical error during session initialization: {str(e)}")
        logger.error(traceback.format_exc())
        ctx.shutdown()

if __name__ == "__main__":
    try:
        logger.info("Initializing LiveKit Agent Server...")
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name="triage-receptionist"))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.critical(f"Server crashed: {str(e)}")
        logger.critical(traceback.format_exc())