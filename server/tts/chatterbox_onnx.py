"""
Chatterbox Multilingual TTS using ONNX models
Implements the actual Chatterbox architecture from onnx-community/chatterbox-multilingual-ONNX
"""
import logging
import numpy as np
import onnxruntime as ort
from pathlib import Path
from huggingface_hub import hf_hub_download
import soundfile as sf
import librosa

logger = logging.getLogger(__name__)

REPO_ID = "onnx-community/chatterbox-multilingual-ONNX"
SAMPLE_RATE = 24000
START_SPEECH_TOKEN = 6561
STOP_SPEECH_TOKEN = 6562

# Language mapping
LANGUAGE_MAP = {
    'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it',
    'pt': 'pt', 'pl': 'pl', 'tr': 'tr', 'ru': 'ru', 'nl': 'nl',
    'cs': 'cs', 'ar': 'ar', 'zh': 'zh', 'ja': 'ja', 'ko': 'ko',
    'hi': 'hi', 'ms': 'ms', 'sv': 'sv', 'fi': 'fi', 'da': 'da',
    'no': 'no', 'he': 'he', 'el': 'el', 'sw': 'sw'
}


class ChatterboxONNX:
    """Chatterbox Multilingual TTS using ONNX Runtime"""

    def __init__(self, cache_dir="models/chatterbox"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.speech_encoder = None
        self.embed_tokens = None
        self.conditional_decoder = None
        self.language_model = None
        self.tokenizer = None
        self.default_voice = None

        logger.info("Chatterbox ONNX initialized")

    def load(self, use_gpu=False):
        """Load all Chatterbox ONNX models"""
        logger.info("Loading Chatterbox Multilingual ONNX models...")

        try:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']

            # Download models from HuggingFace (in onnx/ subdirectory)
            logger.info("Downloading Chatterbox models from HuggingFace...")
            model_files = {
                'speech_encoder': 'onnx/speech_encoder.onnx',
                'embed_tokens': 'onnx/embed_tokens.onnx',
                'conditional_decoder': 'onnx/conditional_decoder.onnx',
                'language_model': 'onnx/language_model.onnx'
            }

            for name, filename in model_files.items():
                logger.info(f"Downloading {filename}...")
                model_path = hf_hub_download(
                    repo_id=REPO_ID,
                    filename=filename,
                    cache_dir=str(self.cache_dir)
                )

                # Also download .onnx_data files if they exist
                try:
                    data_file = f"{filename}_data"
                    hf_hub_download(
                        repo_id=REPO_ID,
                        filename=data_file,
                        cache_dir=str(self.cache_dir)
                    )
                except:
                    pass  # Not all models have separate data files

                # Load ONNX session
                logger.info(f"Loading {name}...")
                session = ort.InferenceSession(model_path, providers=providers)
                setattr(self, name, session)

            # Load tokenizer from same repository
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                REPO_ID,
                cache_dir=str(self.cache_dir)
            )

            # Download default voice audio
            logger.info("Downloading default voice...")
            voice_path = hf_hub_download(
                repo_id=REPO_ID,
                filename="default_voice.wav",
                cache_dir=str(self.cache_dir)
            )

            # Load default voice audio
            self.default_voice, _ = librosa.load(voice_path, sr=SAMPLE_RATE)
            self.default_voice = self.default_voice[np.newaxis, :].astype(np.float32)
            logger.info(f"Default voice loaded: {self.default_voice.shape}")

            logger.info("Chatterbox ONNX models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Chatterbox models: {e}")
            raise

    def synthesize(self, text: str, language: str = 'en', exaggeration: float = 0.5, voice_id: str = None, reference_audio: np.ndarray = None) -> np.ndarray:
        """
        Synthesize speech using Chatterbox

        Args:
            text: Text to synthesize
            language: Language code (ISO 639-1)
            exaggeration: Emotion intensity (0.0-1.0, default 0.5)
            voice_id: Unused (for API compatibility)
            reference_audio: Reference voice audio (float32 numpy array at 24kHz). If None, uses default voice.

        Returns:
            Audio samples as float32 numpy array at 24kHz
        """
        if not all([self.speech_encoder, self.embed_tokens, self.conditional_decoder, self.language_model]):
            raise RuntimeError("Chatterbox models not loaded. Call load() first.")

        if not text or not text.strip():
            return np.array([], dtype=np.float32)

        lang_id = LANGUAGE_MAP.get(language, 'en')
        logger.info(f"Synthesizing with Chatterbox: '{text[:50]}...' ({lang_id}, exag={exaggeration})")

        try:
            # Prepare text with language tag
            text_input = f"[{lang_id}]{text}"

            # Tokenize
            tokens = self.tokenizer.encode(text_input)
            input_ids = np.array([tokens], dtype=np.int64)

            # Create position_ids (special handling for speech tokens)
            position_ids = np.where(
                input_ids >= START_SPEECH_TOKEN,
                0,
                np.arange(input_ids.shape[1])[np.newaxis, :] - 1
            ).astype(np.int64)

            # Create exaggeration input
            exag_input = np.array([exaggeration], dtype=np.float32)

            # Initialize KV cache for language model
            num_hidden_layers = 30
            num_key_value_heads = 16
            head_dim = 64
            batch_size = 1

            past_key_values = {
                f"past_key_values.{layer}.{kv}": np.zeros([batch_size, num_key_value_heads, 0, head_dim], dtype=np.float32)
                for layer in range(num_hidden_layers)
                for kv in ("key", "value")
            }

            # Generate speech tokens autoregressively
            generated_speech_tokens = []  # Store only valid speech tokens
            max_new_tokens = 256

            # Variables to store speaker features for decoder
            speaker_embeddings = None
            speaker_features = None

            # Get voice conditioning from speech encoder
            # Use provided reference audio or default voice
            if reference_audio is not None:
                ref_voice = reference_audio if reference_audio.ndim == 2 else reference_audio[np.newaxis, :]
                logger.info(f"Using custom reference audio - shape: {ref_voice.shape}, dtype: {ref_voice.dtype}")
            else:
                ref_voice = self.default_voice
                logger.info(f"Using default voice - shape: {ref_voice.shape}, dtype: {ref_voice.dtype}")

            # Ensure ref_voice is exactly the right shape (batch, samples)
            if ref_voice.ndim != 2:
                logger.error(f"Invalid ref_voice dimensions: {ref_voice.ndim}, shape: {ref_voice.shape}")
                raise ValueError(f"Reference audio must be 2D (batch, samples), got shape {ref_voice.shape}")

            logger.info(f"Passing to speech_encoder: shape={ref_voice.shape}, dtype={ref_voice.dtype}, min={ref_voice.min():.4f}, max={ref_voice.max():.4f}")

            speech_encoder_output = self.speech_encoder.run(
                None,
                {"audio_values": ref_voice}
            )
            # Speech encoder returns: [cond_emb, prompt_token, ref_x_vector, prompt_feat]
            cond_emb = speech_encoder_output[0]
            # prompt_token = speech_encoder_output[1]  # Not used
            speaker_embeddings = speech_encoder_output[2]  # ref_x_vector
            speaker_features = speech_encoder_output[3]    # prompt_feat

            # First iteration: embed input text + conditioning
            embed_inputs = {
                "input_ids": input_ids,
                "position_ids": position_ids,
                "exaggeration": exag_input
            }
            inputs_embeds = self.embed_tokens.run(None, embed_inputs)[0]

            # Concatenate conditioning with text embeddings
            inputs_embeds = np.concatenate((cond_emb, inputs_embeds), axis=1)
            seq_len = inputs_embeds.shape[1]
            attention_mask = np.ones((batch_size, seq_len), dtype=np.int64)

            # Autoregressive generation loop
            for i in range(max_new_tokens):
                # Run language model
                lm_inputs = {
                    "inputs_embeds": inputs_embeds,
                    "attention_mask": attention_mask,
                    **past_key_values
                }
                lm_outputs = self.language_model.run(None, lm_inputs)
                logits = lm_outputs[0]

                # Update KV cache
                for layer in range(num_hidden_layers):
                    past_key_values[f"past_key_values.{layer}.key"] = lm_outputs[1 + layer * 2]
                    past_key_values[f"past_key_values.{layer}.value"] = lm_outputs[2 + layer * 2]

                # Sample next token (greedy)
                next_token = np.argmax(logits[:, -1, :], axis=-1, keepdims=True).astype(np.int64)

                # Check for stop token BEFORE adding to list
                if next_token[0, 0] == STOP_SPEECH_TOKEN:
                    break

                # Add valid speech token
                generated_speech_tokens.append(next_token[0, 0])

                # Embed next token for next iteration
                embed_inputs = {
                    "input_ids": next_token,
                    "position_ids": np.full((batch_size, 1), i + 1, dtype=np.int64),
                    "exaggeration": exag_input
                }
                inputs_embeds = self.embed_tokens.run(None, embed_inputs)[0]

                # Update attention mask
                attention_mask = np.concatenate([attention_mask, np.ones((batch_size, 1), dtype=np.int64)], axis=1)

            # Convert to numpy array for decoder
            generate_tokens = np.array([generated_speech_tokens], dtype=np.int64)

            # Decode generated tokens to audio with speaker conditioning
            decoder_outputs = self.conditional_decoder.run(
                None,
                {
                    "speech_tokens": generate_tokens,
                    "speaker_embeddings": speaker_embeddings,
                    "speaker_features": speaker_features
                }
            )
            audio = decoder_outputs[0]

            # Convert to float32 and flatten
            audio_samples = audio.flatten().astype(np.float32)

            logger.info(f"Generated {len(generate_tokens[0])} tokens, {len(audio_samples)} samples ({len(audio_samples) / SAMPLE_RATE:.2f}s)")
            return audio_samples

        except Exception as e:
            logger.error(f"Chatterbox synthesis failed: {e}")
            raise RuntimeError(f"TTS synthesis failed: {e}")

    def get_sample_rate(self) -> int:
        return SAMPLE_RATE
