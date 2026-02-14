"""
Standalone TTS Server with XTTS-v2, ASR, and Translation
Run with: python tts_server.py

Environment Variables:
    DEVICE=cuda              # Use GPU acceleration
    COMPUTE_TYPE=int8        # Optimal for 4GB VRAM
    HOST=0.0.0.0            # Server host
    PORT=8000               # Server port
"""
import logging
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add server directory to path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir.parent))

from server.api.tts_endpoint import router, initialize_tts_manager
from server.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BabbleFish TTS Server",
    description="TTS API with XTTS-v2, ASR (faster-whisper), and Translation (NLLB-200)",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include TTS router
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize TTS manager on startup"""
    logger.info("=" * 80)
    logger.info("BabbleFish TTS Server Starting...")
    logger.info("=" * 80)
    logger.info(f"Device: {settings.DEVICE}")
    logger.info(f"Compute Type: {settings.COMPUTE_TYPE}")
    logger.info(f"Host: {settings.HOST}")
    logger.info(f"Port: {settings.PORT}")
    logger.info("=" * 80)

    try:
        # Initialize TTS manager with settings
        use_gpu = settings.DEVICE == "cuda"
        initialize_tts_manager(use_gpu=use_gpu, compute_type=settings.COMPUTE_TYPE)

        logger.info("=" * 80)
        logger.info("TTS Server Ready!")
        logger.info("=" * 80)
        logger.info(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"OpenAPI Schema: http://{settings.HOST}:{settings.PORT}/openapi.json")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Failed to initialize TTS server: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "BabbleFish TTS Server",
        "version": "2.0.0",
        "endpoints": {
            "status": "/api/tts/status",
            "synthesize": "/api/tts/synthesize",
            "transcribe": "/api/tts/transcribe",
            "translate": "/api/tts/translate",
            "process": "/api/tts/process",
            "voice_profiles": "/api/tts/voice-profiles",
            "languages": "/api/tts/languages"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


def main():
    """Run the TTS server"""
    uvicorn.run(
        "tts_server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
