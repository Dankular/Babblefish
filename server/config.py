"""
Server configuration for Babblefish.
"""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Model paths
    MODELS_DIR: Path = Path("models")
    WHISPER_MODEL_SIZE: str = "medium"
    NLLB_MODEL_PATH: str = "models/nllb-200-distilled-600M-ct2"

    # Device configuration
    DEVICE: Literal["cpu", "cuda"] = "cpu"
    COMPUTE_TYPE: Literal["int8", "int16", "float16", "float32"] = "int8"

    # ASR settings
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_VAD_FILTER: bool = True

    # Translation settings
    NLLB_BEAM_SIZE: int = 4

    # Audio settings
    SAMPLE_RATE: int = 16000
    AUDIO_CHUNK_SIZE: int = 4096

    # Room settings
    MAX_PARTICIPANTS_PER_ROOM: int = 10
    MAX_ROOMS: int = 100
    ROOM_TIMEOUT_SECONDS: int = 3600  # 1 hour

    # TTS Router settings (Phase 2/3)
    MAX_SERVER_TTS_CLIENTS: int = 4  # Max clients receiving server-side TTS
    GPU_BUDGET_MS: int = 2000  # Max TTS synthesis time per utterance

    # Client capability thresholds
    MIN_VRAM_F5TTS_MB: int = 4096  # Minimum VRAM for F5-TTS (WebGPU)
    MIN_VRAM_KOKORO_MB: int = 2048  # Minimum VRAM for Kokoro (WebGPU)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
