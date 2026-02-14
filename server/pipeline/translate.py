"""
NLLB-200 translation using CTranslate2.
"""
import logging
from typing import Dict, List
from pathlib import Path
import ctranslate2
import transformers
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

            # Load transformers AutoTokenizer (required for correct NLLB usage)
            # Note: tokenizer will be reinitialized with src_lang for each translation
            self.tokenizer_path = self.model_path

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

            # Initialize tokenizer with source language
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.tokenizer_path,
                src_lang=source_flores,
                clean_up_tokenization_spaces=True
            )

            # Tokenize source text (tokenizer handles language prefix automatically)
            source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))

            # Translate with target language prefix
            results = self.translator.translate_batch(
                [source_tokens],
                target_prefix=[[target_flores]],
                beam_size=settings.NLLB_BEAM_SIZE,
                max_decoding_length=256,
            )

            # Decode - skip first token (target language code)
            translated_tokens = results[0].hypotheses[0][1:]
            translated = tokenizer.decode(tokenizer.convert_tokens_to_ids(translated_tokens))

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
        return self.translator is not None
