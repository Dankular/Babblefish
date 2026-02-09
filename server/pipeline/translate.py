"""
NLLB-200 translation using CTranslate2.
"""
import logging
from typing import Dict, List
from pathlib import Path
import ctranslate2
import sentencepiece as spm
from server.pipeline.language import to_flores, from_flores
from server.config import settings

logger = logging.getLogger(__name__)


class NLLBTranslator:
    """
    NLLB-200-distilled-600M translator using CTranslate2.
    Optimized for CPU inference with int8 quantization.
    """

    def __init__(self, model_path: str = None, device: str = None):
        """
        Initialize the translator.

        Args:
            model_path: Path to CTranslate2 model directory
            device: Device to use ("cpu" or "cuda")
        """
        self.model_path = model_path or str(settings.NLLB_MODEL_PATH)
        self.device = device or settings.DEVICE
        self.compute_type = settings.COMPUTE_TYPE

        self.translator = None
        self.tokenizer = None

        logger.info(
            f"Initializing NLLB translator (device={self.device}, "
            f"compute_type={self.compute_type})"
        )

    def load(self) -> None:
        """Load the model and tokenizer."""
        try:
            # Load CTranslate2 model
            self.translator = ctranslate2.Translator(
                self.model_path,
                device=self.device,
                compute_type=self.compute_type,
                inter_threads=4,
                intra_threads=4,
            )

            # Load SentencePiece tokenizer
            spm_path = Path(self.model_path) / "sentencepiece.model"
            if not spm_path.exists():
                # Try alternative path
                spm_path = Path(self.model_path).parent / "sentencepiece.model"

            self.tokenizer = spm.SentencePieceProcessor()
            self.tokenizer.load(str(spm_path))

            logger.info(f"NLLB translator loaded from {self.model_path}")

        except Exception as e:
            logger.error(f"Failed to load NLLB model: {e}")
            raise

    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """
        Translate text from source language to target language.

        Args:
            text: Text to translate
            source_lang: Source language (ISO 639-1 code)
            target_lang: Target language (ISO 639-1 code)

        Returns:
            Translated text
        """
        if not text.strip():
            return ""

        # Same language - no translation needed
        if source_lang == target_lang:
            return text

        try:
            # Convert to Flores codes
            source_flores = to_flores(source_lang)
            target_flores = to_flores(target_lang)

            # Tokenize with source language prefix
            source_tokens = self.tokenizer.encode(
                f"__{source_flores}__ {text}", out_type=str
            )

            # Translate
            results = self.translator.translate_batch(
                [source_tokens],
                target_prefix=[[target_flores]],
                beam_size=settings.NLLB_BEAM_SIZE,
                max_decoding_length=256,
            )

            # Decode
            translated_tokens = results[0].hypotheses[0]
            translated = self.tokenizer.decode(translated_tokens)

            # Remove target language prefix if present
            if translated.startswith(f"__{target_flores}__"):
                translated = translated[len(f"__{target_flores}__"):].strip()

            return translated

        except Exception as e:
            logger.error(
                f"Translation error ({source_lang}→{target_lang}): {e}"
            )
            # Return original text on error
            return text

    def translate_multi(
        self, text: str, source_lang: str, target_langs: List[str]
    ) -> Dict[str, str]:
        """
        Translate text to multiple target languages.

        Args:
            text: Text to translate
            source_lang: Source language (ISO 639-1 code)
            target_langs: List of target language codes

        Returns:
            Dictionary mapping language codes to translated text
        """
        translations = {}

        for target_lang in target_langs:
            translations[target_lang] = self.translate(
                text, source_lang, target_lang
            )

        return translations

    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.translator is not None and self.tokenizer is not None
