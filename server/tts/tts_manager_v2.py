"""
TTS Manager V2 - XTTS-v2 with Voice Cloning, ASR, Translation
Complete pipeline: Audio → ASR → Translation → TTS
GPU Accelerated with int8 compute for optimal 4GB VRAM usage
"""
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict
from server.tts.xtts_engine import XTTSEngine
from server.tts.voice_profiles import VoiceProfileManager
from server.pipeline.asr import FasterWhisperASR
from server.pipeline.translate import NLLBTranslator
from server.config import settings

logger = logging.getLogger(__name__)


class TTSManagerV2:
    """
    Complete TTS pipeline with ASR, Translation, and Voice Cloning

    Pipeline:
    1. ASR: Audio → Text + Language Detection (faster-whisper)
    2. Translation: Text → Target Language (NLLB-200)
    3. TTS: Text → Speech with Voice Cloning (XTTS-v2)

    Features:
    - GPU acceleration (CUDA)
    - Optimal for 4GB VRAM (int8 compute)
    - Voice cloning from reference audio
    - 24 language support
    - Custom voice profiles
    """

    def __init__(
        self,
        models_dir: str = "models",
        use_gpu: bool = None,
        compute_type: str = None
    ):
        """
        Initialize TTS Manager V2

        Args:
            models_dir: Base directory for model storage
            use_gpu: Enable GPU acceleration (auto-detect if None)
            compute_type: Compute type for quantization (int8, int16, float16, float32)
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Device configuration
        self.use_gpu = use_gpu if use_gpu is not None else (settings.DEVICE == "cuda")
        self.compute_type = compute_type or settings.COMPUTE_TYPE

        # Initialize components
        self.xtts = XTTSEngine(cache_dir=str(self.models_dir / "xtts"))
        self.voice_profiles = VoiceProfileManager()
        self.asr = FasterWhisperASR(
            device="cuda" if self.use_gpu else "cpu",
            compute_type=self.compute_type
        )
        self.translator = NLLBTranslator(
            device="cuda" if self.use_gpu else "cpu"
        )

        logger.info(
            f"TTS Manager V2 initialized (GPU={self.use_gpu}, "
            f"compute_type={self.compute_type})"
        )

    def load(self):
        """Load all pipeline components"""
        logger.info("=" * 60)
        logger.info("Loading TTS Manager V2 Pipeline...")
        logger.info("=" * 60)

        try:
            # Load ASR
            logger.info("[1/4] Loading ASR (faster-whisper)...")
            self.asr.load()

            # Load Translation
            logger.info("[2/4] Loading Translation (NLLB-200)...")
            self.translator.load()

            # Load TTS
            logger.info("[3/4] Loading TTS (XTTS-v2)...")
            self.xtts.load(use_gpu=self.use_gpu)

            # Load Voice Profiles
            logger.info("[4/4] Loading Voice Profiles...")
            logger.info(f"Available voice profiles: {len(self.voice_profiles.list_profiles())}")

            logger.info("=" * 60)
            logger.info("TTS Manager V2 Pipeline Loaded Successfully!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Failed to load TTS Manager V2 pipeline: {e}")
            raise

    # ========== ASR Methods ==========

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Tuple[str, str]:
        """
        Transcribe audio to text with language detection

        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate of input audio

        Returns:
            Tuple of (transcribed_text, detected_language_code)
        """
        if not self.asr.is_loaded():
            raise RuntimeError("ASR not loaded. Call load() first.")

        return self.asr.transcribe(audio, sample_rate)

    # ========== Translation Methods ==========

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text between languages

        Args:
            text: Text to translate
            source_lang: Source language code (ISO 639-1)
            target_lang: Target language code (ISO 639-1)

        Returns:
            Translated text
        """
        if not self.translator.is_loaded():
            raise RuntimeError("Translator not loaded. Call load() first.")

        # No translation needed if same language
        if source_lang == target_lang:
            return text

        return self.translator.translate(text, source_lang, target_lang)

    def translate_multi(
        self,
        text: str,
        source_lang: str,
        target_langs: list
    ) -> Dict[str, str]:
        """
        Translate text to multiple target languages

        Args:
            text: Text to translate
            source_lang: Source language code
            target_langs: List of target language codes

        Returns:
            Dictionary mapping language codes to translated text
        """
        if not self.translator.is_loaded():
            raise RuntimeError("Translator not loaded. Call load() first.")

        return self.translator.translate_multi(text, source_lang, target_langs)

    # ========== TTS Methods ==========

    def synthesize(
        self,
        text: str,
        language: str = 'en',
        voice_profile: Optional[str] = None,
        reference_audio: Optional[np.ndarray] = None,
        reference_audio_path: Optional[str] = None,
        temperature: float = 0.7,
        speed: float = 1.0
    ) -> np.ndarray:
        """
        Synthesize speech from text with voice cloning

        Args:
            text: Text to synthesize
            language: Target language code (ISO 639-1)
            voice_profile: Name of voice profile to use (overrides reference_audio)
            reference_audio: Reference voice audio as numpy array (float32, 24kHz)
            reference_audio_path: Path to reference audio file
            temperature: Voice variation (0.1-1.0, higher = more variation)
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            Audio samples as float32 numpy array at 24kHz
        """
        if not self.xtts.is_loaded():
            raise RuntimeError("XTTS not loaded. Call load() first.")

        if not text or not text.strip():
            return np.array([], dtype=np.float32)

        # Use voice profile if specified
        if voice_profile:
            profile = self.voice_profiles.get_profile(voice_profile)
            if profile:
                logger.info(f"Using voice profile: {voice_profile}")
                reference_audio = profile.audio
            else:
                logger.warning(f"Voice profile '{voice_profile}' not found")

        # Synthesize with XTTS-v2
        return self.xtts.synthesize(
            text=text,
            language=language,
            reference_audio=reference_audio,
            reference_audio_path=reference_audio_path,
            temperature=temperature,
            speed=speed
        )

    # ========== Full Pipeline Methods ==========

    def process_audio(
        self,
        audio: np.ndarray,
        target_language: str,
        sample_rate: int = 16000,
        voice_profile: Optional[str] = None,
        reference_audio: Optional[np.ndarray] = None,
        temperature: float = 0.7,
        speed: float = 1.0
    ) -> Tuple[np.ndarray, Dict[str, str]]:
        """
        Complete pipeline: Audio → ASR → Translation → TTS

        Args:
            audio: Input audio (float32, mono)
            target_language: Target language for output speech
            sample_rate: Sample rate of input audio
            voice_profile: Voice profile name for TTS
            reference_audio: Reference audio for voice cloning
            temperature: Voice variation
            speed: Speech speed

        Returns:
            Tuple of:
            - Synthesized audio (float32 numpy array at 24kHz)
            - Metadata dict with keys: 'source_text', 'source_lang', 'translated_text'
        """
        logger.info("=" * 60)
        logger.info("Processing Full Pipeline: Audio → ASR → Translation → TTS")
        logger.info("=" * 60)

        metadata = {}

        # Step 1: ASR - Transcribe audio
        logger.info("[1/3] ASR: Transcribing audio...")
        text, detected_lang = self.transcribe(audio, sample_rate)
        metadata['source_text'] = text
        metadata['source_lang'] = detected_lang
        logger.info(f"Detected language: {detected_lang}")
        logger.info(f"Transcribed text: '{text[:100]}...'")

        if not text.strip():
            logger.warning("No speech detected in audio")
            return np.array([], dtype=np.float32), metadata

        # Step 2: Translation
        logger.info(f"[2/3] Translation: {detected_lang} → {target_language}")
        if detected_lang != target_language:
            translated_text = self.translate(text, detected_lang, target_language)
            metadata['translated_text'] = translated_text
            logger.info(f"Translated text: '{translated_text[:100]}...'")
        else:
            translated_text = text
            metadata['translated_text'] = text
            logger.info("No translation needed (same language)")

        # Step 3: TTS - Synthesize speech
        logger.info(f"[3/3] TTS: Synthesizing speech in {target_language}...")
        synthesized_audio = self.synthesize(
            text=translated_text,
            language=target_language,
            voice_profile=voice_profile,
            reference_audio=reference_audio,
            temperature=temperature,
            speed=speed
        )

        logger.info("=" * 60)
        logger.info("Pipeline Complete!")
        logger.info("=" * 60)

        return synthesized_audio, metadata

    # ========== Utility Methods ==========

    def get_sample_rate(self) -> int:
        """Get TTS output sample rate"""
        return self.xtts.get_sample_rate()

    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        return self.xtts.get_supported_languages()

    def get_voice_profiles(self) -> list:
        """Get list of available voice profiles"""
        return self.voice_profiles.list_profiles()

    def add_voice_profile(
        self,
        name: str,
        audio: np.ndarray,
        description: str = ""
    ):
        """
        Add a new voice profile

        Args:
            name: Profile name
            audio: Reference audio (float32, 24kHz)
            description: Optional description
        """
        self.voice_profiles.add_profile(name, audio, description)

    def get_device_info(self) -> Dict[str, str]:
        """Get device and compute information"""
        return {
            'device': self.xtts.get_device(),
            'compute_type': self.compute_type,
            'use_gpu': str(self.use_gpu)
        }
