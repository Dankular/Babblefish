"""
Babblefish server - FastAPI + WebSocket entry point.
"""
import uuid
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    global pipeline

    logger.info("Starting Babblefish server...")
    logger.info(f"Settings: {settings.dict()}")

    # Initialize pipeline
    pipeline = PipelineOrchestrator()
    await pipeline.initialize()

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
    await handle_client(websocket, client_id, room_manager, pipeline)


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,
    )
