"""
Automatic Speech Recognition using faster-whisper.
"""
import logging
import numpy as np
from typing import Tuple
from faster_whisper import WhisperModel
from server.config import settings

logger = logging.getLogger(__name__)


class FasterWhisperASR:
    """
    ASR using faster-whisper (CTranslate2 implementation of Whisper).
    Optimized for CPU inference with int8 quantization.
    """

    def __init__(
        self,
        model_size: str = None,
        device: str = None,
        compute_type: str = None,
    ):
        """
        Initialize the ASR model.

        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to use ("cpu" or "cuda")
            compute_type: Compute type ("int8", "int16", "float16", "float32")
        """
        self.model_size = model_size or settings.WHISPER_MODEL_SIZE
        self.device = device or settings.DEVICE
        self.compute_type = compute_type or settings.COMPUTE_TYPE

        self.model = None

        logger.info(
            f"Initializing faster-whisper (size={self.model_size}, "
            f"device={self.device}, compute_type={self.compute_type})"
        )

    def load(self) -> None:
        """Load the Whisper model."""
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
                num_workers=1,
            )
            logger.info(f"faster-whisper model loaded (size={self.model_size})")

        except Exception as e:
            logger.error(f"Failed to load faster-whisper model: {e}")
            raise

    def transcribe(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> Tuple[str, str]:
        """
        Transcribe audio to text and detect language.

        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate of audio (default 16kHz)

        Returns:
            Tuple of (transcribed_text, detected_language_code)
        """
        if not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)

        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize to [-1, 1] if needed
        if audio.max() > 1.0 or audio.min() < -1.0:
            audio = audio / np.abs(audio).max()

        try:
            # Transcribe with language detection
            segments, info = self.model.transcribe(
                audio,
                beam_size=settings.WHISPER_BEAM_SIZE,
                language=None,  # Auto-detect
                vad_filter=settings.WHISPER_VAD_FILTER,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400,
                ),
            )

            # Collect segments
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text.strip())

            text = " ".join(text_segments).strip()

            # Get detected language (ISO 639-1 code)
            language = info.language

            logger.debug(
                f"Transcribed {len(audio)/sample_rate:.1f}s audio: "
                f"'{text}' (lang={language}, prob={info.language_probability:.2f})"
            )

            return text, language

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Return empty string and default language on error
            return "", "en"

    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.model is not None
