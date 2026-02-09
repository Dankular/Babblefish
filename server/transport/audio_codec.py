"""
Audio codec utilities for Opus encoding/decoding.
"""
import base64
import logging
import numpy as np
import io
import soundfile as sf

logger = logging.getLogger(__name__)


def decode_opus(base64_data: str) -> np.ndarray:
    """
    Decode base64-encoded Opus audio to PCM float32.

    Args:
        base64_data: Base64-encoded Opus audio

    Returns:
        Audio data as float32 numpy array (mono, 16kHz)
    """
    try:
        # Decode base64
        audio_bytes = base64.b64decode(base64_data)

        # Opus decode using soundfile (via libsndfile)
        # Note: soundfile can read Opus if libsndfile is compiled with Opus support
        # Alternative: use opuslib directly for guaranteed Opus support
        try:
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        except Exception as e:
            # Fallback: try opuslib if available
            logger.debug(f"soundfile failed, trying opuslib: {e}")
            audio_data = _decode_opus_opuslib(audio_bytes)
            sample_rate = 16000  # Assume 16kHz

        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample to 16kHz if needed
        if sample_rate != 16000:
            audio_data = _resample(audio_data, sample_rate, 16000)

        return audio_data

    except Exception as e:
        logger.error(f"Error decoding Opus audio: {e}")
        # Return empty array on error
        return np.array([], dtype=np.float32)


def _decode_opus_opuslib(opus_bytes: bytes) -> np.ndarray:
    """
    Decode Opus audio using opuslib.

    Args:
        opus_bytes: Raw Opus bytes

    Returns:
        Audio data as float32 numpy array
    """
    try:
        import opuslib

        decoder = opuslib.Decoder(16000, 1)  # 16kHz, mono

        # Opus frame size is typically 960 samples at 48kHz
        # At 16kHz, that's 320 samples per frame
        frame_size = 960

        # Decode frames
        pcm_data = []
        offset = 0

        while offset < len(opus_bytes):
            # Try to decode a frame
            # Frame size varies, but we can try decoding chunks
            try:
                frame = decoder.decode(opus_bytes[offset : offset + 1024], frame_size)
                pcm_data.append(np.frombuffer(frame, dtype=np.int16))
                offset += 1024
            except:
                break

        if pcm_data:
            pcm_array = np.concatenate(pcm_data)
            # Convert int16 to float32 [-1, 1]
            return pcm_array.astype(np.float32) / 32768.0
        else:
            return np.array([], dtype=np.float32)

    except ImportError:
        logger.error("opuslib not available for Opus decoding")
        return np.array([], dtype=np.float32)


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Resample audio to target sample rate.

    Args:
        audio: Audio data
        orig_sr: Original sample rate
        target_sr: Target sample rate

    Returns:
        Resampled audio
    """
    try:
        import librosa

        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except Exception as e:
        logger.error(f"Resampling failed: {e}")
        return audio


def encode_pcm_to_base64(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Encode PCM audio to base64 string.

    Args:
        audio: Audio data as float32 numpy array
        sample_rate: Sample rate

    Returns:
        Base64-encoded audio string
    """
    try:
        # Convert float32 to int16
        audio_int16 = (audio * 32767).astype(np.int16)

        # Encode to bytes
        audio_bytes = audio_int16.tobytes()

        # Base64 encode
        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        logger.error(f"Error encoding PCM to base64: {e}")
        return ""
