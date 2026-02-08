"""
NLLB-200 Translation using CTranslate2

This module handles NLLB model loading and translation with CTranslate2
for optimized inference on CPU/GPU.
"""

import ctranslate2
from huggingface_hub import snapshot_download
from pathlib import Path
import os
from typing import List, Union

class NLLBTranslator:
    """NLLB-200 translator using CTranslate2"""

    def __init__(
        self,
        model_path: str = None,
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize NLLB translator

        Args:
            model_path: Path to CT2-converted NLLB model (default: ./models/nllb-ct2)
            device: "cpu" or "cuda"
            compute_type: "int8", "int16", "float16", "float32"
        """
        if model_path is None:
            # Try to import from config
            try:
                from config import NLLB_CT2_PATH
                self.model_path = str(NLLB_CT2_PATH)
            except ImportError:
                self.model_path = "./models/nllb-ct2"
        else:
            self.model_path = model_path

        self.device = device
        self.compute_type = compute_type

        self.translator = None
        self.tokenizer = None

    def load_model(self):
        """Load NLLB model in CTranslate2 format"""

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"NLLB model not found at {self.model_path}\n"
                "Please run: python setup_models.py\n"
                "Or manually convert with: ct2-transformers-converter "
                "--model facebook/nllb-200-distilled-1.3B "
                f"--output_dir {self.model_path} --quantization int8"
            )

        # Load CT2 model
        print(f"Loading NLLB model from {self.model_path}...")
        self.translator = ctranslate2.Translator(
            self.model_path,
            device=self.device,
            compute_type=self.compute_type,
            inter_threads=4,
            intra_threads=4
        )

        # Load tokenizer (sentencepiece) - using the one from original model
        import sentencepiece as spm
        tokenizer_path = os.path.join(self.model_path, "sentencepiece.model")

        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError(
                f"Tokenizer not found at {tokenizer_path}\n"
                "Make sure the model conversion included sentencepiece.model"
            )

        self.tokenizer = spm.SentencePieceProcessor()
        self.tokenizer.load(tokenizer_path)

        # Also store vocabulary for lookups
        self.vocab = {}
        vocab_path = os.path.join(self.model_path, "shared_vocabulary.json")
        if os.path.exists(vocab_path):
            import json
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab_list = json.load(f)
                self.vocab = {token: idx for idx, token in enumerate(vocab_list)}

        print(f"[OK] NLLB model loaded successfully on {self.device}")

    def translate(
        self,
        text: Union[str, List[str]],
        source_lang: str,
        target_lang: str,
        beam_size: int = 4,
        max_batch_size: int = 32
    ) -> Union[str, List[str]]:
        """
        Translate text from source to target language

        Args:
            text: Input text or list of texts
            source_lang: Source language code (Flores-200 format, e.g., "eng_Latn")
            target_lang: Target language code (Flores-200 format)
            beam_size: Beam search size (higher = better quality, slower)
            max_batch_size: Maximum batch size for processing

        Returns:
            Translated text or list of texts
        """
        if self.translator is None:
            raise RuntimeError("Model not loaded. Call load_model() first")

        # Handle single string
        single_input = isinstance(text, str)
        if single_input:
            text = [text]

        # Tokenize using sentencepiece
        source_tokens = []
        for t in text:
            # Encode to pieces (subword tokens)
            tokens = self.tokenizer.encode_as_pieces(t)
            # Prepend source language token
            tokens = [source_lang] + tokens
            source_tokens.append(tokens)

        # Translate using CTranslate2
        results = self.translator.translate_batch(
            source_tokens,
            beam_size=beam_size,
            max_batch_size=max_batch_size,
            target_prefix=[[target_lang]] * len(source_tokens),
            max_decoding_length=256,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3
        )

        # Decode results
        translations = []
        for result in results:
            # Get hypothesis (list of token pieces)
            pieces = result.hypotheses[0]
            # Skip the target language token at the beginning
            if len(pieces) > 0 and pieces[0] == target_lang:
                pieces = pieces[1:]
            # Decode pieces to text
            translation = self.tokenizer.decode_pieces(pieces)
            translations.append(translation)

        return translations[0] if single_input else translations

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        # NLLB-200 supports 200 languages
        # This is a subset of common ones
        return [
            "ace_Arab", "ace_Latn", "afr_Latn", "als_Latn", "amh_Ethi",
            "ara_Arab", "arz_Arab", "asm_Beng", "ast_Latn", "azj_Latn",
            "bel_Cyrl", "ben_Beng", "bos_Latn", "bul_Cyrl", "cat_Latn",
            "ceb_Latn", "ces_Latn", "ckb_Arab", "cym_Latn", "dan_Latn",
            "deu_Latn", "ell_Grek", "eng_Latn", "est_Latn", "eus_Latn",
            "fin_Latn", "fra_Latn", "gaz_Latn", "gle_Latn", "glg_Latn",
            "guj_Gujr", "heb_Hebr", "hin_Deva", "hrv_Latn", "hun_Latn",
            "hye_Armn", "ibo_Latn", "ind_Latn", "isl_Latn", "ita_Latn",
            "jav_Latn", "jpn_Jpan", "kan_Knda", "kat_Geor", "kaz_Cyrl",
            "khk_Cyrl", "khm_Khmr", "kir_Cyrl", "kor_Hang", "lao_Laoo",
            "lit_Latn", "ltz_Latn", "lvs_Latn", "mal_Mlym", "mar_Deva",
            "mkd_Cyrl", "mlt_Latn", "mni_Beng", "mya_Mymr", "nld_Latn",
            "nob_Latn", "npi_Deva", "pbt_Arab", "pes_Arab", "pol_Latn",
            "por_Latn", "ron_Latn", "rus_Cyrl", "slk_Latn", "slv_Latn",
            "sna_Latn", "snd_Arab", "som_Latn", "spa_Latn", "srp_Cyrl",
            "swe_Latn", "swh_Latn", "tam_Taml", "tel_Telu", "tgk_Cyrl",
            "tha_Thai", "tur_Latn", "ukr_Cyrl", "urd_Arab", "uzn_Latn",
            "vie_Latn", "yor_Latn", "yue_Hant", "zho_Hans", "zho_Hant",
            "zsm_Latn", "zul_Latn"
        ]

# Example usage
if __name__ == "__main__":
    translator = NLLBTranslator(device="cpu", compute_type="int8")

    try:
        translator.load_model()

        # Test translation
        result = translator.translate(
            "Hello, how are you?",
            source_lang="eng_Latn",
            target_lang="spa_Latn"
        )
        print(f"Translation: {result}")

    except Exception as e:
        print(f"Error: {e}")
