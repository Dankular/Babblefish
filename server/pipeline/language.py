"""
Language code mapping and utilities.
Maps between ISO 639-1 codes and Flores-200 codes used by NLLB.
"""
from typing import Optional

# ISO 639-1 → Flores-200 mapping for NLLB-200
# Format: {iso_code: flores_code}
ISO_TO_FLORES = {
    # Major European languages
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "nl": "nld_Latn",
    "pl": "pol_Latn",
    "ru": "rus_Cyrl",
    "uk": "ukr_Cyrl",
    "cs": "ces_Latn",
    "sk": "slk_Latn",
    "ro": "ron_Latn",
    "hu": "hun_Latn",
    "el": "ell_Grek",
    "sv": "swe_Latn",
    "no": "nob_Latn",
    "da": "dan_Latn",
    "fi": "fin_Latn",
    "bg": "bul_Cyrl",
    "hr": "hrv_Latn",
    "sr": "srp_Cyrl",
    "sl": "slv_Latn",
    "lt": "lit_Latn",
    "lv": "lvs_Latn",
    "et": "est_Latn",
    # Asian languages
    "zh": "zho_Hans",  # Simplified Chinese
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "hi": "hin_Deva",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "id": "ind_Latn",
    "ms": "zsm_Latn",
    "tl": "tgl_Latn",  # Tagalog
    "my": "mya_Mymr",  # Burmese
    "km": "khm_Khmr",  # Khmer
    # Middle Eastern & African
    "ar": "arb_Arab",
    "he": "heb_Hebr",
    "tr": "tur_Latn",
    "fa": "pes_Arab",
    "sw": "swh_Latn",
    "am": "amh_Ethi",
    "yo": "yor_Latn",
    "ig": "ibo_Latn",
    "ha": "hau_Latn",
    "zu": "zul_Latn",
}

# Reverse mapping: Flores-200 → ISO 639-1
FLORES_TO_ISO = {v: k for k, v in ISO_TO_FLORES.items()}

# Language display names
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "uk": "Ukrainian",
    "cs": "Czech",
    "sk": "Slovak",
    "ro": "Romanian",
    "hu": "Hungarian",
    "el": "Greek",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "sl": "Slovenian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "tl": "Tagalog",
    "my": "Burmese",
    "km": "Khmer",
    "ar": "Arabic",
    "he": "Hebrew",
    "tr": "Turkish",
    "fa": "Persian",
    "sw": "Swahili",
    "am": "Amharic",
    "yo": "Yoruba",
    "ig": "Igbo",
    "ha": "Hausa",
    "zu": "Zulu",
}


def to_flores(iso_code: str) -> str:
    """
    Convert ISO 639-1 code to Flores-200 code.

    Args:
        iso_code: ISO 639-1 language code (e.g., "en", "fr")

    Returns:
        Flores-200 code (e.g., "eng_Latn", "fra_Latn")

    Raises:
        ValueError: If language code is not supported
    """
    flores_code = ISO_TO_FLORES.get(iso_code.lower())
    if not flores_code:
        raise ValueError(f"Unsupported language code: {iso_code}")
    return flores_code


def from_flores(flores_code: str) -> str:
    """
    Convert Flores-200 code to ISO 639-1 code.

    Args:
        flores_code: Flores-200 code (e.g., "eng_Latn", "fra_Latn")

    Returns:
        ISO 639-1 code (e.g., "en", "fr")

    Raises:
        ValueError: If Flores code is not recognized
    """
    iso_code = FLORES_TO_ISO.get(flores_code)
    if not iso_code:
        raise ValueError(f"Unrecognized Flores code: {flores_code}")
    return iso_code


def get_language_name(iso_code: str) -> str:
    """
    Get the display name for a language code.

    Args:
        iso_code: ISO 639-1 language code

    Returns:
        Human-readable language name

    Raises:
        ValueError: If language code is not supported
    """
    name = LANGUAGE_NAMES.get(iso_code.lower())
    if not name:
        raise ValueError(f"Unknown language code: {iso_code}")
    return name


def is_supported(iso_code: str) -> bool:
    """Check if a language code is supported."""
    return iso_code.lower() in ISO_TO_FLORES


def get_supported_languages() -> list[str]:
    """Get list of all supported ISO 639-1 language codes."""
    return list(ISO_TO_FLORES.keys())
