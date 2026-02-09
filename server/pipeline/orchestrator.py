"""
Pipeline orchestrator coordinating ASR and translation.
"""
import logging
import numpy as np
from typing import Dict, List
from server.pipeline.asr import FasterWhisperASR
from server.pipeline.translate import NLLBTranslator

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Coordinates the full ASR → Translation pipeline.
    """

    def __init__(self):
        self.asr = None
        self.translator = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize and load all models."""
        if self._initialized:
            logger.warning("Pipeline already initialized")
            return

        logger.info("Initializing pipeline orchestrator...")

        # Initialize ASR
        self.asr = FasterWhisperASR()
        self.asr.load()

        # Initialize translator
        self.translator = NLLBTranslator()
        try:
            self.translator.load()
        except Exception as e:
            logger.warning(f"Failed to load NLLB translator: {e}")
            logger.warning("Server will start but translations will be limited")
            self.translator = None

        self._initialized = True
        logger.info("Pipeline orchestrator initialized successfully")

    async def process_utterance(
        self, audio: np.ndarray, target_languages: List[str], sample_rate: int = 16000
    ) -> Dict:
        """
        Process a complete utterance through the pipeline.

        Args:
            audio: Audio data as numpy array (float32, mono)
            target_languages: List of target language codes (ISO 639-1)
            sample_rate: Sample rate of audio (default 16kHz)

        Returns:
            Dictionary with:
                - source_text: Transcribed text
                - source_lang: Detected language code
                - translations: Dict mapping language code to translated text
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        # Step 1: ASR - transcribe audio to text
        source_text, source_lang = self.asr.transcribe(audio, sample_rate)

        if not source_text:
            logger.warning("ASR returned empty transcription")
            return {
                "source_text": "",
                "source_lang": "en",
                "translations": {},
            }

        # Step 2: Translation - translate to all target languages
        if self.translator:
            translations = self.translator.translate_multi(
                text=source_text,
                source_lang=source_lang,
                target_langs=target_languages,
            )
        else:
            # Fallback: return source text for all languages (no translation)
            translations = {lang: f"[No translator] {source_text}" for lang in target_languages}

        logger.info(
            f"Processed utterance: '{source_text}' ({source_lang}) → "
            f"{len(translations)} translations"
        )

        return {
            "source_text": source_text,
            "source_lang": source_lang,
            "translations": translations,
        }

    def is_ready(self) -> bool:
        """Check if pipeline is initialized and ready."""
        return (
            self._initialized
            and self.asr is not None
            and self.asr.is_loaded()
            and self.translator is not None
            and self.translator.is_loaded()
        )
