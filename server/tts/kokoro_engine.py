"""
Kokoro-82M TTS Engine
Fast, high-quality TTS for generating reference voices
"""
import logging
import numpy as np
from pathlib import Path
from kokoro_onnx import Kokoro

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000  # Kokoro outputs at 24kHz
GITHUB_RELEASE_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"


class KokoroEngine:
    """Kokoro-82M TTS engine"""

    def __init__(self, cache_dir="models/kokoro"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.kokoro = None
        logger.info("Kokoro engine initialized")

    def load(self):
        """Load Kokoro ONNX models"""
        logger.info("Loading Kokoro models...")

        try:
            import urllib.request

            # Download model from GitHub releases
            model_path = self.cache_dir / "kokoro-v1.0.onnx"
            voices_path = self.cache_dir / "voices-v1.0.bin"

            if not model_path.exists():
                logger.info("Downloading Kokoro ONNX model from GitHub...")
                model_url = f"{GITHUB_RELEASE_URL}/kokoro-v1.0.onnx"
                urllib.request.urlretrieve(model_url, model_path)
                logger.info(f"Model downloaded to {model_path}")

            if not voices_path.exists():
                logger.info("Downloading Kokoro voices from GitHub...")
                voices_url = f"{GITHUB_RELEASE_URL}/voices-v1.0.bin"
                urllib.request.urlretrieve(voices_url, voices_path)
                logger.info(f"Voices downloaded to {voices_path}")

            # Initialize Kokoro
            self.kokoro = Kokoro(str(model_path), str(voices_path))
            logger.info("Kokoro models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Kokoro models: {e}")
            raise

    def synthesize(self, text: str, language: str = 'en', voice: str = 'af') -> np.ndarray:
        """
        Synthesize speech with Kokoro

        Args:
            text: Text to synthesize
            language: Language code (en, es, fr, etc.)
            voice: Voice ID (af, af_bella, af_sarah, etc.)

        Returns:
            Audio samples as float32 numpy array at 24kHz
        """
        if self.kokoro is None:
            raise RuntimeError("Kokoro not loaded. Call load() first.")

        logger.info(f"Synthesizing with Kokoro: '{text[:50]}...' (voice={voice})")

        try:
            # Generate audio using Kokoro
            samples, sample_rate = self.kokoro.create(
                text,
                voice=voice,
                speed=1.0,
                lang=language
            )

            # Convert to numpy array if needed
            audio = np.array(samples, dtype=np.float32)

            logger.info(f"Kokoro generated {len(audio)} samples ({len(audio) / sample_rate:.2f}s)")
            return audio

        except Exception as e:
            logger.error(f"Kokoro synthesis failed: {e}")
            raise RuntimeError(f"Kokoro TTS failed: {e}")

    def get_sample_rate(self) -> int:
        return SAMPLE_RATE
