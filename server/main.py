"""
Babblefish server - FastAPI + WebSocket entry point.
"""
import uuid
import logging
import asyncio
import base64
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from server.rooms.manager import RoomManager
from server.pipeline.orchestrator import PipelineOrchestrator
from server.transport.handler import handle_client
from server.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global singletons
room_manager = RoomManager()
pipeline = None
tts_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    global pipeline, tts_engine

    logger.info("Starting Babblefish server...")
    logger.info(f"Settings: {settings.dict()}")

    # Initialize pipeline
    pipeline = PipelineOrchestrator()
    await pipeline.initialize()

    # Initialize TTS engine - Kokoro → Chatterbox pipeline
    # TTS on GPU with int8 quantization - we have enough VRAM (4GB total, ~2.5GB free)
    try:
        from server.tts.tts_manager import TTSManager
        use_tts_gpu = settings.DEVICE == "cuda"  # Use GPU if available for faster TTS
        logger.info(f"Loading TTS Manager (Kokoro + Chatterbox, GPU={use_tts_gpu})...")
        tts_engine = TTSManager()
        tts_engine.load(use_gpu=use_tts_gpu)
        logger.info("TTS Manager loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load Chatterbox TTS: {e}")
        logger.warning("Server TTS will not be available")
        tts_engine = None

    logger.info("Babblefish server started successfully")
    logger.info(f"Server listening on {settings.HOST}:{settings.PORT}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_loop())

    yield

    # Shutdown
    logger.info("Shutting down Babblefish server...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Babblefish server shut down")


# Create FastAPI app
app = FastAPI(
    title="Babblefish Server",
    description="Real-time voice translation server",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def cleanup_loop():
    """Background task to cleanup empty and idle rooms."""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute

            # Cleanup empty rooms
            empty_count = room_manager.cleanup_empty_rooms()
            if empty_count > 0:
                logger.info(f"Cleaned up {empty_count} empty rooms")

            # Cleanup idle rooms
            idle_count = room_manager.cleanup_idle_rooms()
            if idle_count > 0:
                logger.info(f"Cleaned up {idle_count} idle rooms")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")


@app.websocket("/ws/client")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for client connections.
    """
    client_id = str(uuid.uuid4())[:8]
    await handle_client(websocket, client_id, room_manager, pipeline, tts_engine)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "pipeline_ready": pipeline.is_ready() if pipeline else False,
        "rooms": room_manager.get_room_count(),
        "participants": room_manager.get_total_participants(),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Babblefish Server",
        "version": "0.1.0",
        "description": "Real-time voice translation",
    }


class TTSRequest(BaseModel):
    """TTS synthesis request."""
    text: str
    language: str = "en"
    voice_id: str | None = None
    voice_profile: str | None = None  # Custom voice profile name


class VoiceProfileRequest(BaseModel):
    """Voice profile creation request."""
    name: str
    url: str | None = None
    description: str = ""
    max_duration: float = 2.0  # Chatterbox works best with short reference audio (1.5-2s)


class TTSResponse(BaseModel):
    """TTS synthesis response."""
    audio_base64: str
    sample_rate: int
    duration: float


@app.post("/api/voice_profiles")
async def create_voice_profile(request: VoiceProfileRequest):
    """
    Create a custom voice profile from URL or file path.
    The profile can then be used for voice cloning with Chatterbox.
    """
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS not available")

    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        profile = tts_engine.voice_profiles.add_profile_from_url(
            name=request.name,
            url=request.url,
            description=request.description,
            max_duration=request.max_duration
        )
        return {
            "name": profile.name,
            "description": profile.description,
            "duration": len(profile.audio) / 24000,
            "message": f"Voice profile '{request.name}' created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice_profiles")
async def list_voice_profiles():
    """List all available voice profiles."""
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS not available")

    return {"profiles": tts_engine.voice_profiles.list_profiles()}


@app.delete("/api/voice_profiles/{name}")
async def delete_voice_profile(name: str):
    """Delete a voice profile."""
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS not available")

    try:
        tts_engine.voice_profiles.delete_profile(name)
        return {"message": f"Voice profile '{name}' deleted"}
    except Exception as e:
        logger.error(f"Failed to delete voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Server-side TTS synthesis endpoint.
    Uses Chatterbox Multilingual for heavy lifting (GPU-accelerated).
    """
    if tts_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Server TTS not available. Use client-side TTS instead."
        )

    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        # Synthesize audio
        audio_samples = tts_engine.synthesize(
            text=request.text,
            language=request.language,
            voice_id=request.voice_id,
            voice_profile=request.voice_profile
        )

        # Encode audio as base64 (float32 PCM)
        audio_bytes = audio_samples.tobytes()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Calculate duration
        sample_rate = tts_engine.get_sample_rate()
        duration = len(audio_samples) / sample_rate

        logger.info(f"Synthesized {duration:.2f}s of audio for '{request.text[:50]}...'")

        return TTSResponse(
            audio_base64=audio_base64,
            sample_rate=sample_rate,
            duration=duration
        )

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,
    )
