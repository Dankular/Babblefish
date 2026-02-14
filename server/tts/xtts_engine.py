"""
XTTS-v2 TTS Engine with Voice Cloning and GPU Acceleration
Supports multilingual synthesis with reference audio voice cloning
"""
import logging
import numpy as np
import torch
from pathlib import Path
from typing import Optional
from TTS.api import TTS

logger = logging.getLogger(__name__)

# XTTS-v2 supported languages (24 languages)
XTTS_LANGUAGES = {
    'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it',
    'pt': 'pt', 'pl': 'pl', 'tr': 'tr', 'ru': 'ru', 'nl': 'nl',
    'cs': 'cs', 'ar': 'ar', 'zh': 'zh-cn', 'ja': 'ja', 'ko': 'ko',
    'hi': 'hi', 'hu': 'hu', 'sv': 'sv', 'fi': 'fi', 'da': 'da',
    'no': 'no', 'he': 'he', 'el': 'el', 'sk': 'sk'
}

SAMPLE_RATE = 24000


class XTTSEngine:
    """
    XTTS-v2 TTS Engine with voice cloning capabilities

    Features:
    - Multilingual synthesis (24 languages)
    - Voice cloning from reference audio
    - GPU acceleration support
    - Emotional voice control
    """

    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2", cache_dir: str = "models/xtts"):
        """
        Initialize XTTS-v2 engine

        Args:
            model_name: HuggingFace model path for XTTS-v2
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.tts = None
        self.device = None
        self.sample_rate = SAMPLE_RATE

        logger.info(f"XTTS-v2 engine initialized (model={model_name})")

    def load(self, use_gpu: bool = True):
        """
        Load XTTS-v2 model with GPU acceleration

        Args:
            use_gpu: Enable CUDA GPU acceleration if available
        """
        try:
            # Determine device
            if use_gpu and torch.cuda.is_available():
                self.device = "cuda"
                logger.info(f"Using GPU acceleration: {torch.cuda.get_device_name(0)}")
                logger.info(f"VRAM available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            else:
                self.device = "cpu"
                logger.info("Using CPU (GPU not available or disabled)")

            # Load XTTS-v2 model
            logger.info(f"Loading XTTS-v2 model to {self.device}...")
            self.tts = TTS(self.model_name).to(self.device)

            logger.info("XTTS-v2 model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load XTTS-v2 model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        language: str = 'en',
        reference_audio: Optional[np.ndarray] = None,
        reference_audio_path: Optional[str] = None,
        speaker_wav: Optional[str] = None,
        temperature: float = 0.7,
        length_penalty: float = 1.0,
        repetition_penalty: float = 5.0,
        top_k: int = 50,
        top_p: float = 0.85,
        speed: float = 1.0
    ) -> np.ndarray:
        """
        Synthesize speech using XTTS-v2 with voice cloning

        Args:
            text: Text to synthesize
            language: Target language code (ISO 639-1)
            reference_audio: Reference voice audio as numpy array (float32, 24kHz)
            reference_audio_path: Path to reference audio file (alternative to reference_audio)
            speaker_wav: Path to speaker audio file (legacy parameter, same as reference_audio_path)
            temperature: Sampling temperature (0.1-1.0, higher = more variation)
            length_penalty: Length penalty for generation
            repetition_penalty: Penalty for repeating tokens
            top_k: Top-k sampling parameter
            top_p: Top-p (nucleus) sampling parameter
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            Audio samples as float32 numpy array at 24kHz
        """
        if not self.tts:
            raise RuntimeError("XTTS-v2 model not loaded. Call load() first.")

        if not text or not text.strip():
            return np.array([], dtype=np.float32)

        # Map language code to XTTS format
        xtts_lang = XTTS_LANGUAGES.get(language, 'en')

        logger.info(f"XTTS-v2 synthesis: '{text[:50]}...' (lang={xtts_lang}, device={self.device})")

        try:
            # Determine reference audio source
            ref_audio_path = speaker_wav or reference_audio_path

            # Handle reference audio from numpy array
            if reference_audio is not None and ref_audio_path is None:
                # Save reference audio temporarily
                import tempfile
                import soundfile as sf

                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    ref_audio_path = tmp_file.name
                    # Ensure audio is in correct format
                    if reference_audio.ndim > 1:
                        reference_audio = reference_audio.flatten()
                    sf.write(ref_audio_path, reference_audio, SAMPLE_RATE)
                    logger.info(f"Saved reference audio to temporary file: {ref_audio_path}")

            # Synthesize with XTTS-v2
            if ref_audio_path:
                logger.info(f"Using voice cloning with reference: {ref_audio_path}")
                audio = self.tts.tts(
                    text=text,
                    language=xtts_lang,
                    speaker_wav=ref_audio_path,
                    temperature=temperature,
                    length_penalty=length_penalty,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                    speed=speed
                )
            else:
                # Use default speaker if no reference provided
                logger.warning("No reference audio provided, using default speaker")
                audio = self.tts.tts(
                    text=text,
                    language=xtts_lang,
                    temperature=temperature,
                    length_penalty=length_penalty,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                    speed=speed
                )

            # Convert to numpy array
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()
            audio = np.array(audio, dtype=np.float32)

            # Flatten if needed
            if audio.ndim > 1:
                audio = audio.flatten()

            logger.info(f"XTTS-v2 synthesis complete: {len(audio)} samples ({len(audio) / SAMPLE_RATE:.2f}s)")

            # Clean up temporary file if created
            if reference_audio is not None and ref_audio_path and ref_audio_path.startswith('/tmp'):
                try:
                    import os
                    os.unlink(ref_audio_path)
                except:
                    pass

            return audio

        except Exception as e:
            logger.error(f"XTTS-v2 synthesis failed: {e}")
            raise RuntimeError(f"TTS synthesis failed: {e}")

    def get_sample_rate(self) -> int:
        """Get the sample rate for generated audio"""
        return SAMPLE_RATE

    def is_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self.tts is not None

    def get_device(self) -> str:
        """Get the current device (cpu or cuda)"""
        return self.device if self.device else "not_loaded"

    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        return list(XTTS_LANGUAGES.keys())
