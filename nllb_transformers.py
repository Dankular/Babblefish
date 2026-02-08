"""
NLLB Translation using transformers library directly
This is slower than CTranslate2 but actually works
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Union, List
import os

class NLLBTransformerTranslator:
    """NLLB translator using transformers (slower but works)"""

    def __init__(
        self,
        model_name: str = "facebook/nllb-200-distilled-1.3B",
        cache_dir: str = "./cache",
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.device = device
        self.model = None
        self.tokenizer = None

    def load_model(self):
        """Load NLLB model using transformers"""
        print(f"Loading NLLB model from {self.model_name}...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir
        )

        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir
        )

        if self.device == "cuda":
            self.model = self.model.to("cuda")

        print(f"[OK] NLLB model loaded successfully on {self.device}")

    def translate(
        self,
        text: Union[str, List[str]],
        source_lang: str,
        target_lang: str,
        max_length: int = 256
    ) -> Union[str, List[str]]:
        """
        Translate text from source to target language

        Args:
            text: Input text or list of texts
            source_lang: Source language code (Flores-200 format)
            target_lang: Target language code (Flores-200 format)
            max_length: Maximum output length

        Returns:
            Translated text or list of texts
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first")

        # Handle single string
        single_input = isinstance(text, str)
        if single_input:
            text = [text]

        # Set source language
        self.tokenizer.src_lang = source_lang

        # Encode
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        if self.device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        # Get target language token ID
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(target_lang)

        # Generate translation
        outputs = self.model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=max_length,
            num_beams=4
        )

        # Decode
        translations = self.tokenizer.batch_decode(
            outputs,
            skip_special_tokens=True
        )

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

# Test
if __name__ == "__main__":
    translator = NLLBTransformerTranslator()
    translator.load_model()

    result = translator.translate(
        "Hello, how are you?",
        source_lang="eng_Latn",
        target_lang="spa_Latn"
    )

    print(f"Translation: {result}")
