"""
TTS Manager - Orchestrates Kokoro + Chatterbox pipeline
Strategy: Use Kokoro to generate reference voice, then Chatterbox clones it
Supports custom voice profiles for direct voice cloning
"""
import logging
import numpy as np
from server.tts.kokoro_engine import KokoroEngine
from server.tts.chatterbox_onnx import ChatterboxONNX
from server.tts.voice_profiles import VoiceProfileManager

logger = logging.getLogger(__name__)


class TTSManager:
    """
    Manages the Kokoro → Chatterbox TTS pipeline

    Pipeline:
    1. Synthesize text with Kokoro (fast, high-quality) OR use custom voice profile
    2. Use Kokoro audio / profile audio as reference voice for Chatterbox
    3. Chatterbox clones the voice for multilingual synthesis
    """

    def __init__(self, cache_dir="models/chatterbox"):
        self.kokoro = KokoroEngine()
        self.chatterbox = ChatterboxONNX(cache_dir=cache_dir)
        self.voice_profiles = VoiceProfileManager()
        logger.info("TTS Manager initialized")

    def load(self, use_gpu=False):
        """Load both Kokoro and Chatterbox models"""
        logger.info("Loading TTS engines...")
        self.kokoro.load()
        self.chatterbox.load(use_gpu=use_gpu)
        logger.info("TTS engines loaded successfully")

    def synthesize(self, text: str, language: str = 'en', exaggeration: float = 0.5, voice_id: str = None, voice_profile: str = None) -> np.ndarray:
        """
        Synthesize speech using Kokoro → Chatterbox pipeline or custom voice profile

        Args:
            text: Text to synthesize
            language: Target language code
            exaggeration: Chatterbox emotion intensity (0.0-1.0)
            voice_id: Kokoro voice ID (af_sarah, etc.) - used if no voice_profile specified
            voice_profile: Voice profile name to use as reference (overrides voice_id)

        Returns:
            Audio samples as float32 numpy array at 24kHz
        """
        if not text or not text.strip():
            return np.array([], dtype=np.float32)

        # Check if using custom voice profile
        if voice_profile:
            profile = self.voice_profiles.get_profile(voice_profile)
            if profile:
                logger.info(f"TTS Manager: '{text[:50]}...' → {language} (profile={voice_profile})")
                try:
                    # Use profile audio directly as reference
                    logger.info(f"[1/1] Chatterbox voice cloning with profile '{voice_profile}'...")
                    chatterbox_audio = self.chatterbox.synthesize(
                        text=text,
                        language=language,
                        exaggeration=exaggeration,
                        reference_audio=profile.audio
                    )
                    logger.info(f"TTS complete: {len(chatterbox_audio)} samples")
                    return chatterbox_audio
                except Exception as e:
                    logger.error(f"Voice profile synthesis failed: {e}")
                    # Fall through to Kokoro synthesis
            else:
                logger.warning(f"Voice profile '{voice_profile}' not found, using Kokoro")

        # Kokoro only supports English - use direct Chatterbox for other languages
        if language != 'en':
            logger.info(f"TTS Manager: '{text[:50]}...' → {language} (Chatterbox direct)")
            logger.info(f"[1/1] Chatterbox synthesis (Kokoro doesn't support {language})...")
            chatterbox_audio = self.chatterbox.synthesize(
                text=text,
                language=language,
                exaggeration=exaggeration,
                reference_audio=None  # No reference for non-English
            )
            logger.info(f"TTS complete: {len(chatterbox_audio)} samples")
            return chatterbox_audio

        # Use Kokoro → Chatterbox pipeline for English
        voice = voice_id or 'af_sarah'  # Default Kokoro voice
        logger.info(f"TTS Manager: '{text[:50]}...' → {language} (Kokoro + Chatterbox)")

        try:
            # Step 1: Generate reference voice with Kokoro (English only)
            logger.info(f"[1/2] Kokoro synthesis...")
            kokoro_audio = self.kokoro.synthesize(
                text=text,
                language='en-us',
                voice=voice
            )

            # Step 2: Clone voice with Chatterbox using Kokoro as reference
            logger.info(f"[2/2] Chatterbox voice cloning...")
            chatterbox_audio = self.chatterbox.synthesize(
                text=text,
                language=language,
                exaggeration=exaggeration,
                reference_audio=kokoro_audio
            )

            logger.info(f"TTS pipeline complete: {len(chatterbox_audio)} samples")
            return chatterbox_audio

        except Exception as e:
            logger.error(f"TTS pipeline failed: {e}")
            # Fallback to Kokoro only for English
            logger.warning("Falling back to Kokoro-only synthesis")
            return self.kokoro.synthesize(text, 'en-us', voice)

    def get_sample_rate(self) -> int:
        return 24000
