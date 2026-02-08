"""
Real-time Speech Translation Server
WebSocket endpoint with VAD, streaming transcription, and translation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import numpy as np
import torch
import json
import io
import time
from collections import deque
from typing import Optional

# Audio processing
import wave
import struct

# VAD model
import onnxruntime

app = FastAPI()

class SileroVAD:
    """Silero VAD for speech detection"""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model = None
        self.sample_rate = 16000

    def load_model(self):
        """Load Silero VAD model"""
        print("Loading Silero VAD model...")
        try:
            # Download and load Silero VAD
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.model = model
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils

            print("[OK] Silero VAD loaded")
        except Exception as e:
            print(f"[WARNING] Could not load Silero VAD: {e}")
            print("          VAD will be disabled")

    def is_speech(self, audio_chunk: np.ndarray) -> float:
        """
        Check if audio chunk contains speech

        Args:
            audio_chunk: Audio data (numpy array, 16kHz, float32, [-1, 1])

        Returns:
            Confidence score (0-1)
        """
        if self.model is None:
            return 1.0  # No VAD, assume speech

        try:
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_chunk).float()

            # Get VAD prediction
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.sample_rate).item()

            return speech_prob
        except Exception as e:
            print(f"VAD error: {e}")
            return 1.0


class AudioBuffer:
    """Rolling audio buffer with VAD-based segmentation"""

    def __init__(
        self,
        vad: SileroVAD,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 300,
        silence_threshold_ms: int = 500,
        max_segment_duration_s: int = 5
    ):
        self.vad = vad
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.silence_threshold_samples = int(sample_rate * silence_threshold_ms / 1000)
        self.max_segment_samples = sample_rate * max_segment_duration_s

        self.buffer = deque()
        self.current_segment = []
        self.silence_counter = 0
        self.is_speaking = False

    def add_chunk(self, audio_chunk: np.ndarray):
        """Add audio chunk and return completed segments"""
        # Check if speech
        speech_prob = self.vad.is_speech(audio_chunk)
        is_speech = speech_prob > self.vad.threshold

        if is_speech:
            # Speech detected
            self.current_segment.append(audio_chunk)
            self.silence_counter = 0
            self.is_speaking = True
        else:
            # Silence
            if self.is_speaking:
                # We were speaking, now silence
                self.silence_counter += len(audio_chunk)
                self.current_segment.append(audio_chunk)  # Include trailing silence

                # Check if enough silence to end segment
                if self.silence_counter >= self.silence_threshold_samples:
                    segment = self._get_segment()
                    self._reset()
                    return segment

        # Check max duration (force flush)
        if len(self.current_segment) > 0:
            total_samples = sum(len(chunk) for chunk in self.current_segment)
            if total_samples >= self.max_segment_samples:
                segment = self._get_segment()
                self._reset()
                return segment

        return None

    def _get_segment(self) -> Optional[np.ndarray]:
        """Get current segment as numpy array"""
        if len(self.current_segment) == 0:
            return None
        return np.concatenate(self.current_segment)

    def _reset(self):
        """Reset segment buffer"""
        self.current_segment = []
        self.silence_counter = 0
        self.is_speaking = False

    def flush(self) -> Optional[np.ndarray]:
        """Force flush current segment"""
        segment = self._get_segment()
        self._reset()
        return segment


class RealtimeTranslationHandler:
    """Handle real-time transcription and translation"""

    def __init__(self, whisper_model, nllb_translator):
        self.whisper = whisper_model
        self.nllb = nllb_translator
        self.vad = SileroVAD(threshold=0.5)
        self.vad.load_model()

    async def handle_audio_stream(
        self,
        websocket: WebSocket,
        target_lang: str = "spa_Latn"
    ):
        """Process streaming audio from WebSocket"""

        buffer = AudioBuffer(self.vad)
        segment_counter = 0

        try:
            while True:
                # Receive audio chunk
                data = await websocket.receive_bytes()

                # Convert bytes to numpy array (assuming 16-bit PCM, 16kHz)
                audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                # Add to buffer and check for completed segment
                segment = buffer.add_chunk(audio_chunk)

                if segment is not None and len(segment) > 0:
                    segment_counter += 1

                    # Save segment to temporary file for Whisper
                    temp_audio = self._save_temp_audio(segment, buffer.sample_rate)

                    # Transcribe with language detection
                    segments, info = self.whisper.transcribe(
                        temp_audio,
                        language=None,  # Auto-detect
                        task="transcribe",
                        vad_filter=False  # We already did VAD
                    )

                    # Collect transcription
                    transcription = " ".join([seg.text for seg in segments])
                    detected_lang = info.language
                    lang_probability = info.language_probability

                    if transcription.strip():
                        # Translate if not already in target language
                        translation = ""
                        if detected_lang != target_lang.split('_')[0]:
                            # Convert ISO to Flores code
                            flores_source = self._iso_to_flores(detected_lang)

                            translation = self.nllb.translate(
                                transcription,
                                source_lang=flores_source,
                                target_lang=target_lang
                            )

                        # Get full language name
                        lang_name = self._get_language_name(detected_lang)
                        flores_code = self._iso_to_flores(detected_lang)

                        # Send results back
                        result = {
                            "type": "result",
                            "segment": segment_counter,
                            "transcription": transcription,
                            "language": detected_lang,
                            "language_name": lang_name,
                            "language_confidence": round(lang_probability, 3),
                            "source_flores": flores_code,
                            "translation": translation,
                            "target_lang": target_lang,
                            "timestamp": time.time()
                        }

                        await websocket.send_json(result)

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error in audio stream: {e}")
            import traceback
            traceback.print_exc()

    def _save_temp_audio(self, audio: np.ndarray, sample_rate: int) -> str:
        """Save audio segment to temporary WAV file"""
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)

        # Convert float32 to int16
        audio_int16 = (audio * 32768).astype(np.int16)

        # Write WAV
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return temp_file.name

    def _iso_to_flores(self, iso_code: str) -> str:
        """Convert ISO 639-1 to Flores-200 language code"""
        mapping = {
            "en": "eng_Latn", "es": "spa_Latn", "fr": "fra_Latn",
            "de": "deu_Latn", "it": "ita_Latn", "pt": "por_Latn",
            "ru": "rus_Cyrl", "ja": "jpn_Jpan", "ko": "kor_Hang",
            "zh": "zho_Hans", "ar": "ara_Arab", "hi": "hin_Deva",
            "vi": "vie_Latn", "th": "tha_Thai", "id": "ind_Latn",
            "tr": "tur_Latn", "nl": "nld_Latn", "pl": "pol_Latn",
            "uk": "ukr_Cyrl", "ro": "ron_Latn"
        }
        return mapping.get(iso_code, f"{iso_code}_Latn")

    def _get_language_name(self, iso_code: str) -> str:
        """Get full language name from ISO code"""
        names = {
            "en": "English", "es": "Spanish", "fr": "French",
            "de": "German", "it": "Italian", "pt": "Portuguese",
            "ru": "Russian", "ja": "Japanese", "ko": "Korean",
            "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
            "vi": "Vietnamese", "th": "Thai", "id": "Indonesian",
            "tr": "Turkish", "nl": "Dutch", "pl": "Polish",
            "uk": "Ukrainian", "ro": "Romanian", "cs": "Czech",
            "sv": "Swedish", "da": "Danish", "fi": "Finnish",
            "no": "Norwegian", "el": "Greek", "he": "Hebrew",
            "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
            "mr": "Marathi", "ur": "Urdu", "fa": "Persian",
            "sw": "Swahili", "am": "Amharic", "my": "Burmese",
            "km": "Khmer", "lo": "Lao", "si": "Sinhala",
            "ne": "Nepali", "ka": "Georgian", "hy": "Armenian",
            "az": "Azerbaijani", "kk": "Kazakh", "uz": "Uzbek"
        }
        return names.get(iso_code, iso_code.upper())


# Initialize (will be set on startup)
realtime_handler = None


@app.on_event("startup")
async def startup():
    """Load models on startup"""
    global realtime_handler

    from faster_whisper import WhisperModel
    from nllb_ct2_fixed import NLLBTranslatorCT2

    print("Loading models for real-time translation...")

    # Load Whisper
    whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")

    # Load NLLB
    nllb_translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
    nllb_translator.load_model()

    # Create handler
    realtime_handler = RealtimeTranslationHandler(whisper_model, nllb_translator)

    print("[OK] Real-time translation ready!")


@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()

    # Get target language from query params (default: Spanish)
    target_lang = websocket.query_params.get("target_lang", "spa_Latn")

    print(f"New WebSocket connection - translating to {target_lang}")

    await websocket.send_json({
        "type": "ready",
        "message": "Ready for audio stream",
        "target_lang": target_lang
    })

    # Handle audio stream
    await realtime_handler.handle_audio_stream(websocket, target_lang)


@app.get("/")
async def get_client():
    """Serve the client HTML"""
    html_content = open("realtime_client.html", "r").read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
