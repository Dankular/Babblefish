"""
Google Text-to-Speech Engine (gTTS)
Simple, reliable multilingual TTS using Google's API
"""
import logging
import numpy as np
from gtts import gTTS
import io
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Language mapping (ISO 639-1)
SUPPORTED_LANGUAGES = {
    'en': 'en',  # English
    'es': 'es',  # Spanish
    'fr': 'fr',  # French
    'de': 'de',  # German
    'it': 'it',  # Italian
    'pt': 'pt',  # Portuguese
    'pl': 'pl',  # Polish
    'tr': 'tr',  # Turkish
    'ru': 'ru',  # Russian
    'nl': 'nl',  # Dutch
    'cs': 'cs',  # Czech
    'ar': 'ar',  # Arabic
    'zh': 'zh-CN',  # Chinese (Simplified)
    'ja': 'ja',  # Japanese
    'ko': 'ko',  # Korean
    'hi': 'hi',  # Hindi
    'bn': 'bn',  # Bengali
    'ta': 'ta',  # Tamil
    'te': 'te',  # Telugu
    'uk': 'uk',  # Ukrainian
    'vi': 'vi',  # Vietnamese
    'th': 'th',  # Thai
    'id': 'id',  # Indonesian
}

SAMPLE_RATE = 24000  # gTTS typically outputs 24kHz


class GTTSEngine:
    """
    Simple Google Text-to-Speech engine.
    Uses gTTS library for reliable multilingual synthesis.
    """

    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        logger.info("gTTS engine initialized")

    def synthesize(self, text: str, language: str = 'en', voice_id: str = None) -> np.ndarray:
        """
        Synthesize speech from text using Google TTS.

        Args:
            text: Text to synthesize
            language: Language code (ISO 639-1)

        Returns:
            Audio samples as float32 numpy array
        """
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return np.array([], dtype=np.float32)

        # Map language code
        lang_code = SUPPORTED_LANGUAGES.get(language, 'en')
        logger.info(f"Synthesizing with gTTS: '{text[:50]}...' ({lang_code})")

        try:
            # Create TTS object
            tts = gTTS(text=text, lang=lang_code, slow=False)

            # Generate audio to bytes (MP3 format)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)

            # Load MP3 and convert to PCM
            audio_segment = AudioSegment.from_mp3(audio_fp)

            # Convert to mono if stereo
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)

            # Set sample rate
            audio_segment = audio_segment.set_frame_rate(self.sample_rate)

            # Get raw PCM data
            audio_bytes = audio_segment.raw_data

            # Convert to numpy array (16-bit PCM)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            logger.info(f"Generated {len(audio_float32)} samples ({len(audio_float32) / self.sample_rate:.2f}s)")
            return audio_float32

        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            raise RuntimeError(f"TTS synthesis failed: {e}")

    def get_sample_rate(self) -> int:
        """Get the sample rate of generated audio."""
        return self.sample_rate

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in SUPPORTED_LANGUAGES
