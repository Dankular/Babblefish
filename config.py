"""
Configuration settings for BabbleFish

Adjust these settings based on your hardware and requirements
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"
UPLOAD_DIR = BASE_DIR / "uploads"

# Create directories
MODELS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# NLLB Model Configuration
NLLB_MODEL_NAME = "facebook/nllb-200-distilled-1.3B"  # Options: 600M, 1.3B, 3.3B
NLLB_CT2_PATH = MODELS_DIR / "nllb-ct2"

# Whisper Model Configuration
WHISPER_MODEL_SIZE = "medium"  # Options: tiny, base, small, medium, large-v2

# Device Configuration
# Set to "cuda" if you have a GPU, "cpu" otherwise
DEVICE = os.environ.get("DEVICE", "cpu")

# Compute Type
# CPU: "int8" (fastest), "int16", "float32"
# GPU: "float16" (recommended), "float32"
if DEVICE == "cuda":
    COMPUTE_TYPE = "float16"
else:
    COMPUTE_TYPE = "int8"

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 1  # Increase for production

# Model Loading
# Set to True to load models at startup (slower startup, faster first request)
# Set to False for lazy loading (faster startup, slower first request)
PRELOAD_MODELS = True

# Transcription Settings
WHISPER_VAD_FILTER = True  # Voice Activity Detection (removes silence)
WHISPER_VAD_MIN_SILENCE_MS = 500

# Translation Settings
NLLB_BEAM_SIZE = 4  # Higher = better quality but slower (1-8)
NLLB_MAX_BATCH_SIZE = 32

# File Upload Limits
MAX_UPLOAD_SIZE_MB = 100  # Maximum audio file size in MB
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"}

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Performance Tuning
# Number of threads for inter/intra operations
# Adjust based on your CPU cores
CPU_THREADS = 4

# Cache Settings
ENABLE_CACHE = False  # Cache translations (not implemented yet)
CACHE_TTL_SECONDS = 3600

# Feature Flags
ENABLE_BATCH_TRANSLATION = False  # Not implemented yet
ENABLE_STREAMING = False  # Not implemented yet
ENABLE_METRICS = False  # Prometheus metrics (not implemented yet)

# Development
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
RELOAD = DEBUG

# Print configuration on import
if __name__ == "__main__":
    print("BabbleFish Configuration")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Compute Type: {COMPUTE_TYPE}")
    print(f"NLLB Model: {NLLB_MODEL_NAME}")
    print(f"Whisper Model: {WHISPER_MODEL_SIZE}")
    print(f"Models Directory: {MODELS_DIR}")
    print(f"API Port: {API_PORT}")
    print("=" * 60)
