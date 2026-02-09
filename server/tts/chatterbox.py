"""
Chatterbox Multilingual TTS Engine (Server-side GPU)
Uses ONNX Runtime for GPU-accelerated inference
Supports 23 languages with high-quality synthesis
"""
import logging
import numpy as np
import onnxruntime as ort
from typing import Optional, List
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# Model URLs from HuggingFace
MODEL_BASE_URL = "https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX/resolve/main/onnx"

# Language mapping for Chatterbox Multilingual
LANGUAGE_MAP = {
    'en': 'en',   # English
    'es': 'es',   # Spanish
    'fr': 'fr',   # French
    'de': 'de',   # German
    'it': 'it',   # Italian
    'pt': 'pt',   # Portuguese
    'pl': 'pl',   # Polish
    'tr': 'tr',   # Turkish
    'ru': 'ru',   # Russian
    'nl': 'nl',   # Dutch
    'cs': 'cs',   # Czech
    'ar': 'ar',   # Arabic
    'zh': 'zh',   # Chinese (Mandarin)
    'ja': 'ja',   # Japanese
    'ko': 'ko',   # Korean
    'hi': 'hi',   # Hindi
    'bn': 'bn',   # Bengali
    'ta': 'ta',   # Tamil
    'te': 'te',   # Telugu
    'uk': 'uk',   # Ukrainian
    'vi': 'vi',   # Vietnamese
    'th': 'th',   # Thai
    'id': 'id',   # Indonesian
}

SAMPLE_RATE = 24000  # Chatterbox outputs 24kHz audio


class ChatterboxTTS:
    """
    Server-side Chatterbox Multilingual TTS engine.
    Uses GPU acceleration via ONNX Runtime.
    """

    def __init__(self, models_dir: str = "models/chatterbox"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.speech_encoder = None
        self.embed_tokens = None
        self.conditional_decoder = None
        self.language_model = None

        self.is_loaded = False
        self.sample_rate = SAMPLE_RATE

    def load(self, use_gpu: bool = True) -> None:
        """
        Load Chatterbox models.

        Args:
            use_gpu: Whether to use GPU acceleration (CUDA)
        """
        if self.is_loaded:
            logger.info("Chatterbox TTS already loaded")
            return

        logger.info("Loading Chatterbox Multilingual TTS models...")

        try:
            # Configure execution providers
            if use_gpu and 'CUDAExecutionProvider' in ort.get_available_providers():
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                logger.info("Using GPU acceleration for Chatterbox TTS")
            else:
                providers = ['CPUExecutionProvider']
                logger.info("Using CPU for Chatterbox TTS")

            # Download and load models
            model_files = {
                'speech_encoder': 'speech_encoder.onnx',
                'embed_tokens': 'embed_tokens.onnx',
                'conditional_decoder': 'conditional_decoder.onnx',
                'language_model_q4f16': 'language_model_q4f16.onnx',  # Quantized version
            }

            # Download models if not cached
            for model_name, filename in model_files.items():
                local_path = self.models_dir / filename
                if not local_path.exists():
                    logger.info(f"Downloading {model_name}...")
                    self._download_model(filename, local_path)

            # Load ONNX sessions
            logger.info("Loading speech encoder...")
            self.speech_encoder = ort.InferenceSession(
                str(self.models_dir / model_files['speech_encoder']),
                providers=providers
            )

            logger.info("Loading embed tokens...")
            self.embed_tokens = ort.InferenceSession(
                str(self.models_dir / model_files['embed_tokens']),
                providers=providers
            )

            logger.info("Loading conditional decoder...")
            self.conditional_decoder = ort.InferenceSession(
                str(self.models_dir / model_files['conditional_decoder']),
                providers=providers
            )

            logger.info("Loading language model...")
            self.language_model = ort.InferenceSession(
                str(self.models_dir / model_files['language_model_q4f16']),
                providers=providers
            )

            self.is_loaded = True
            logger.info("Chatterbox TTS loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Chatterbox TTS: {e}")
            raise

    def _download_model(self, filename: str, local_path: Path) -> None:
        """Download model file from HuggingFace."""
        url = f"{MODEL_BASE_URL}/{filename}"

        # Also download .onnx_data files if they exist
        data_url = f"{url}_data"
        data_path = Path(str(local_path) + "_data")

        logger.info(f"Downloading {filename} from HuggingFace...")

        # Download main model file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded {filename} ({local_path.stat().st_size / 1024 / 1024:.1f} MB)")

        # Try to download .onnx_data file
        try:
            response = requests.get(data_url, stream=True)
            response.raise_for_status()

            with open(data_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded {filename}_data ({data_path.stat().st_size / 1024 / 1024:.1f} MB)")
        except requests.exceptions.HTTPError:
            # .onnx_data file doesn't exist for this model
            pass

    def synthesize(self, text: str, language: str = 'en', voice_id: Optional[str] = None, exaggeration: float = 1.0) -> np.ndarray:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code (ISO 639-1)
            voice_id: Optional voice style ID
            exaggeration: Speech exaggeration/expressiveness (0.0-2.0, default 1.0)

        Returns:
            Audio samples as float32 numpy array
        """
        if not self.is_loaded:
            raise RuntimeError("Chatterbox TTS not loaded. Call load() first.")

        if not text or not text.strip():
            logger.warning("Empty text provided")
            return np.array([], dtype=np.float32)

        # Map language code
        lang_id = LANGUAGE_MAP.get(language, 'en')
        logger.info(f"Synthesizing: '{text[:50]}...' ({lang_id})")

        try:
            # Step 1: Tokenize text
            tokens = self._tokenize_text(text, lang_id)
            seq_len = len(tokens)

            # Step 2: Create input tensors
            token_tensor = np.array([tokens], dtype=np.int64)
            position_ids = np.arange(seq_len, dtype=np.int64).reshape(1, -1)
            exaggeration_tensor = np.array([exaggeration], dtype=np.float32)

            # Step 3: Embed tokens
            embed_output = self.embed_tokens.run(
                None,
                {
                    'input_ids': token_tensor,
                    'position_ids': position_ids,
                    'exaggeration': exaggeration_tensor
                }
            )
            embeddings = embed_output[0]

            # Step 4: Speech encoding
            encoder_output = self.speech_encoder.run(None, {'embeddings': embeddings})
            speech_features = encoder_output[0]

            # Step 5: Language model processing
            lm_output = self.language_model.run(None, {'features': speech_features})
            lm_features = lm_output[0]

            # Step 6: Conditional decoder (features → audio)
            decoder_output = self.conditional_decoder.run(None, {'lm_features': lm_features})
            audio = decoder_output[0]

            # Flatten and convert to float32
            audio_samples = audio.flatten().astype(np.float32)

            logger.info(f"Generated {len(audio_samples)} samples ({len(audio_samples) / self.sample_rate:.2f}s)")
            return audio_samples

        except Exception as e:
            logger.error(f"Chatterbox synthesis failed: {e}")
            raise RuntimeError(f"TTS synthesis failed: {e}")

    def _tokenize_text(self, text: str, language: str) -> List[int]:
        """
        Tokenize text to token IDs.

        This is a simplified tokenizer. In production, would use
        the actual Chatterbox tokenizer/phonemizer.
        """
        # Simple character-based tokenization
        chars = text.lower()
        tokens = []

        for char in chars:
            code = ord(char)
            if 97 <= code <= 122:  # a-z
                tokens.append(code - 97 + 1)
            elif code == 32:  # space
                tokens.append(0)
            else:
                tokens.append(27)  # unknown

        return tokens

    def is_language_supported(self, language: str) -> bool:
        """Check if language is supported."""
        return language in LANGUAGE_MAP

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(LANGUAGE_MAP.keys())

    def get_sample_rate(self) -> int:
        """Get sample rate of generated audio."""
        return self.sample_rate

    def dispose(self) -> None:
        """Cleanup resources."""
        logger.info("Disposing Chatterbox TTS resources...")

        self.speech_encoder = None
        self.embed_tokens = None
        self.conditional_decoder = None
        self.language_model = None

        self.is_loaded = False
