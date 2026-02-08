"""
NLLB-200 Translation using CTranslate2 (WORKING VERSION)
Uses transformers tokenizer with CT2 model for proper inference
"""

import ctranslate2
from transformers import AutoTokenizer
from typing import Union, List
import os

class NLLBTranslatorCT2:
    """NLLB translator using CTranslate2 with transformers tokenizer"""

    def __init__(
        self,
        model_path: str = "./models/nllb-ct2-fixed",
        original_model: str = "facebook/nllb-200-distilled-1.3B",
        cache_dir: str = "./cache",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_path = model_path
        self.original_model = original_model
        self.cache_dir = cache_dir
        self.device = device
        self.compute_type = compute_type

        self.translator = None
        self.tokenizer = None

    def load_model(self):
        """Load CT2 model and transformers tokenizer"""
        print(f"Loading NLLB CT2 model from {self.model_path}...")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"CT2 model not found at {self.model_path}\n"
                "Run: python fix_nllb_conversion.py"
            )

        # Load CT2 model
        self.translator = ctranslate2.Translator(
            self.model_path,
            device=self.device,
            compute_type=self.compute_type,
            inter_threads=4,
            intra_threads=4
        )

        # Load transformers tokenizer (this is the key!)
        # The tokenizer properly handles NLLB language codes
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.original_model,
            cache_dir=self.cache_dir
        )

        print(f"[OK] NLLB CT2 model loaded successfully on {self.device}")

    def translate(
        self,
        text: Union[str, List[str]],
        source_lang: str,
        target_lang: str,
        beam_size: int = 4,
        max_length: int = 256
    ) -> Union[str, List[str]]:
        """
        Translate text using CT2 backend

        Args:
            text: Input text or list of texts
            source_lang: Source language (Flores-200 code)
            target_lang: Target language (Flores-200 code)
            beam_size: Beam search size
            max_length: Maximum output length

        Returns:
            Translated text or list of texts
        """
        if self.translator is None:
            raise RuntimeError("Model not loaded. Call load_model() first")

        # Handle single string
        single_input = isinstance(text, str)
        if single_input:
            text = [text]

        # Set source language
        self.tokenizer.src_lang = source_lang

        # Tokenize with transformers (returns token IDs)
        inputs = self.tokenizer(
            text,
            return_tensors=None,
            padding=False,
            truncation=True,
            max_length=512
        )

        # Convert token IDs to tokens (subword pieces)
        # CT2 works with token strings, not IDs
        source_tokens = []
        for input_ids in (inputs['input_ids'] if isinstance(inputs['input_ids'][0], list) else [inputs['input_ids']]):
            tokens = self.tokenizer.convert_ids_to_tokens(input_ids)
            source_tokens.append(tokens)

        # Get target language token
        target_prefix = [[target_lang]]

        # Translate with CT2
        results = self.translator.translate_batch(
            source_tokens,
            target_prefix=target_prefix * len(source_tokens),
            beam_size=beam_size,
            max_decoding_length=max_length,
            return_scores=False
        )

        # Decode outputs
        translations = []
        for result in results:
            # Get output tokens
            output_tokens = result.hypotheses[0]

            # Convert tokens back to IDs for proper decoding
            # This is crucial - we need to use the tokenizer's vocabulary
            output_ids = self.tokenizer.convert_tokens_to_ids(output_tokens)

            # Decode using transformers tokenizer
            translation = self.tokenizer.decode(
                output_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )

            translations.append(translation)

        return translations[0] if single_input else translations

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
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


# Test the fixed version
if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("Testing NLLB CT2 (Fixed Version)...")
    print()

    translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
    translator.load_model()

    print()
    print("Test 1: English → Spanish")
    result = translator.translate(
        "Hello, how are you?",
        source_lang="eng_Latn",
        target_lang="spa_Latn"
    )
    print(f"Result: {result}")
    print()

    print("Test 2: English → French")
    result = translator.translate(
        "The weather is beautiful today",
        source_lang="eng_Latn",
        target_lang="fra_Latn"
    )
    print(f"Result: {result}")
    print()

    print("Test 3: English → Japanese")
    result = translator.translate(
        "I love learning new languages",
        source_lang="eng_Latn",
        target_lang="jpn_Jpan"
    )
    print(f"Result: {result}")
