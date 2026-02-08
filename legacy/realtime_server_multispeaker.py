"""
Real-time Multi-Speaker Translation Server with TTS
Features:
- WebSocket streaming
- VAD-based segmentation
- Whisper transcription
- NLLB translation
- Speaker diarization (pyannote.audio)
- Per-speaker voice training (F5-TTS)
- Per-speaker TTS synthesis (Kokoro + F5-TTS)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import numpy as np
import torch
import json
import io
import time
import base64
from collections import deque
from typing import Optional, Dict
import wave

# Import existing components
import sys
sys.path.append('.')

from faster_whisper import WhisperModel
from nllb_ct2_fixed import NLLBTranslatorCT2
from tts_engine import TTSEngine

app = FastAPI()


# VAD and Buffer classes (same as before)
class SileroVAD:
    """Silero VAD for speech detection"""
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model = None
        self.sample_rate = 16000

    def load_model(self):
        print("Loading Silero VAD model...")
        try:
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.model = model
            print("[OK] Silero VAD loaded")
        except Exception as e:
            print(f"[WARNING] Could not load Silero VAD: {e}")

    def is_speech(self, audio_chunk: np.ndarray) -> float:
        if self.model is None:
            return 1.0
        try:
            audio_tensor = torch.from_numpy(audio_chunk).float()
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.sample_rate).item()
            return speech_prob
        except:
            return 1.0


class AudioBuffer:
    """Rolling audio buffer with VAD-based segmentation"""
    def __init__(self, vad, sample_rate=16000, chunk_duration_ms=300,
                 silence_threshold_ms=500, max_segment_duration_s=5):
        self.vad = vad
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.silence_threshold_samples = int(sample_rate * silence_threshold_ms / 1000)
        self.max_segment_samples = sample_rate * max_segment_duration_s

        self.current_segment = []
        self.silence_counter = 0
        self.is_speaking = False

    def add_chunk(self, audio_chunk: np.ndarray):
        speech_prob = self.vad.is_speech(audio_chunk)
        is_speech = speech_prob > self.vad.threshold

        if is_speech:
            self.current_segment.append(audio_chunk)
            self.silence_counter = 0
            self.is_speaking = True
        else:
            if self.is_speaking:
                self.silence_counter += len(audio_chunk)
                self.current_segment.append(audio_chunk)

                if self.silence_counter >= self.silence_threshold_samples:
                    segment = self._get_segment()
                    self._reset()
                    return segment

        if len(self.current_segment) > 0:
            total_samples = sum(len(chunk) for chunk in self.current_segment)
            if total_samples >= self.max_segment_samples:
                segment = self._get_segment()
                self._reset()
                return segment
        return None

    def _get_segment(self):
        if len(self.current_segment) == 0:
            return None
        return np.concatenate(self.current_segment)

    def _reset(self):
        self.current_segment = []
        self.silence_counter = 0
        self.is_speaking = False

    def flush(self):
        segment = self._get_segment()
        self._reset()
        return segment


class MultiSpeakerTranslationHandler:
    """Handle real-time multi-speaker transcription, translation, and TTS"""

    def __init__(self, whisper_model, nllb_translator, tts_engine):
        self.whisper = whisper_model
        self.nllb = nllb_translator
        self.tts = tts_engine
        self.vad = SileroVAD(threshold=0.5)
        self.vad.load_model()

        # Track current speakers in session
        self.active_speakers = {}  # speaker_id -> last_seen_time

    async def handle_audio_stream(
        self,
        websocket: WebSocket,
        target_lang: str = "eng_Latn",
        enable_tts: bool = True,
        use_trained_voice: bool = False
    ):
        """Process streaming audio from WebSocket with speaker identification"""
        buffer = AudioBuffer(self.vad)
        segment_counter = 0

        try:
            while True:
                data = await websocket.receive_bytes()
                audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                segment = buffer.add_chunk(audio_chunk)

                if segment is not None and len(segment) > 0:
                    segment_counter += 1

                    # Save segment to temp file
                    temp_audio = self._save_temp_audio(segment, buffer.sample_rate)

                    # Transcribe
                    segments, info = self.whisper.transcribe(
                        temp_audio,
                        language=None,
                        task="transcribe",
                        vad_filter=False
                    )

                    transcription = " ".join([seg.text for seg in segments])
                    detected_lang = info.language
                    lang_probability = info.language_probability

                    if transcription.strip():
                        # Identify speaker and add to training
                        speaker_id = self.tts.add_training_sample(
                            segment,
                            transcription,
                            detected_lang,
                            sample_rate=buffer.sample_rate
                        )

                        # Get speaker name
                        if speaker_id:
                            speaker_name = self.tts.get_speaker_name(speaker_id)
                            self.active_speakers[speaker_id] = time.time()
                        else:
                            speaker_id = "speaker_1"
                            speaker_name = "Speaker"

                        # Translate
                        translation = ""
                        if detected_lang != target_lang.split('_')[0]:
                            flores_source = self._iso_to_flores(detected_lang)
                            translation = self.nllb.translate(
                                transcription,
                                source_lang=flores_source,
                                target_lang=target_lang
                            )

                        # Generate TTS for this speaker's translation
                        tts_audio_b64 = None
                        tts_voice_used = "none"

                        if enable_tts and translation and target_lang == "eng_Latn":
                            try:
                                # Check if this speaker has trained voice
                                speaker_stats = self.tts.get_training_stats(speaker_id)
                                can_use_trained = False

                                if speaker_stats:
                                    if isinstance(speaker_stats, dict) and 'has_trained_model' in speaker_stats:
                                        can_use_trained = speaker_stats['has_trained_model'] and use_trained_voice

                                tts_audio = self.tts.synthesize(
                                    translation,
                                    language="en",
                                    use_trained_voice=can_use_trained,
                                    speaker_id=speaker_id if self.tts.multi_speaker else None
                                )

                                if tts_audio is not None:
                                    import soundfile as sf
                                    buffer_io = io.BytesIO()
                                    sf.write(buffer_io, tts_audio, 24000, format='WAV')
                                    tts_audio_b64 = base64.b64encode(buffer_io.getvalue()).decode('utf-8')
                                    tts_voice_used = f"{speaker_name}_trained" if can_use_trained else "kokoro"

                            except Exception as e:
                                print(f"TTS error: {e}")
                                import traceback
                                traceback.print_exc()

                        # Get all speaker stats
                        all_speaker_stats = self.tts.get_training_stats()

                        # Get active speakers list
                        active_speakers_list = self._get_active_speakers()

                        # Send results
                        result = {
                            "type": "result",
                            "segment": segment_counter,
                            "transcription": transcription,
                            "language": detected_lang,
                            "language_name": self._get_language_name(detected_lang),
                            "language_confidence": round(lang_probability, 3),
                            "source_flores": self._iso_to_flores(detected_lang),
                            "translation": translation,
                            "target_lang": target_lang,
                            "speaker_id": speaker_id,
                            "speaker_name": speaker_name,
                            "tts_audio": tts_audio_b64,
                            "tts_voice": tts_voice_used,
                            "training_stats": all_speaker_stats,
                            "active_speakers": active_speakers_list,
                            "timestamp": time.time()
                        }

                        await websocket.send_json(result)

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error in audio stream: {e}")
            import traceback
            traceback.print_exc()

    def _get_active_speakers(self) -> list:
        """Get list of active speakers (seen in last 60 seconds)"""
        current_time = time.time()
        timeout = 60.0

        active = []
        for speaker_id, last_seen in self.active_speakers.items():
            if current_time - last_seen < timeout:
                speaker_name = self.tts.get_speaker_name(speaker_id)
                stats = self.tts.get_training_stats(speaker_id)

                active.append({
                    "id": speaker_id,
                    "name": speaker_name,
                    "last_seen": last_seen,
                    "stats": stats
                })

        return active

    def _save_temp_audio(self, audio, sample_rate):
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_int16 = (audio * 32768).astype(np.int16)
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        return temp_file.name

    def _iso_to_flores(self, iso_code):
        mapping = {
            "en": "eng_Latn", "es": "spa_Latn", "fr": "fra_Latn",
            "de": "deu_Latn", "it": "ita_Latn", "pt": "por_Latn",
            "ru": "rus_Cyrl", "ja": "jpn_Jpan", "ko": "kor_Hang",
            "zh": "zho_Hans", "ar": "ara_Arab", "hi": "hin_Deva",
        }
        return mapping.get(iso_code, f"{iso_code}_Latn")

    def _get_language_name(self, iso_code):
        names = {
            "en": "English", "es": "Spanish", "fr": "French",
            "de": "German", "it": "Italian", "pt": "Portuguese",
            "ru": "Russian", "ja": "Japanese", "ko": "Korean",
            "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
        }
        return names.get(iso_code, iso_code.upper())


# Global handler
realtime_handler = None


@app.on_event("startup")
async def startup():
    """Load models on startup"""
    global realtime_handler

    print("Loading models for multi-speaker real-time translation with TTS...")

    whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")
    nllb_translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
    nllb_translator.load_model()

    # Initialize TTS engine in MULTI-SPEAKER mode
    tts_engine = TTSEngine(multi_speaker=True)
    tts_engine.load()

    realtime_handler = MultiSpeakerTranslationHandler(whisper_model, nllb_translator, tts_engine)

    print("[OK] Multi-speaker real-time translation with TTS ready!")


@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()

    # Get params
    target_lang = websocket.query_params.get("target_lang", "eng_Latn")
    enable_tts = websocket.query_params.get("enable_tts", "true").lower() == "true"
    use_trained_voice = websocket.query_params.get("use_trained_voice", "false").lower() == "true"

    print(f"New connection - target: {target_lang}, TTS: {enable_tts}, Trained: {use_trained_voice}")

    # Get all speaker stats
    training_stats = realtime_handler.tts.get_training_stats()
    all_speakers = realtime_handler.tts.get_all_speakers()

    await websocket.send_json({
        "type": "ready",
        "message": "Ready for multi-speaker audio stream with TTS",
        "target_lang": target_lang,
        "tts_enabled": enable_tts,
        "multi_speaker": True,
        "training_stats": training_stats,
        "known_speakers": all_speakers
    })

    await realtime_handler.handle_audio_stream(
        websocket,
        target_lang,
        enable_tts,
        use_trained_voice
    )


@app.get("/")
async def get_client():
    """Serve the multi-speaker client HTML"""
    try:
        html_content = open("realtime_client_multispeaker.html", "r", encoding="utf-8").read()
        return HTMLResponse(content=html_content)
    except:
        return HTMLResponse(content="<h1>BabbleFish Multi-Speaker TTS Server</h1><p>Client not found. Use realtime_client_multispeaker.html</p>")


@app.get("/speakers")
async def get_speakers():
    """Get all known speakers"""
    return {
        "speakers": realtime_handler.tts.get_all_speakers(),
        "training_stats": realtime_handler.tts.get_training_stats()
    }


@app.get("/training/stats")
async def get_training_stats():
    """Get all speaker training statistics"""
    return realtime_handler.tts.get_training_stats()


@app.get("/training/stats/{speaker_id}")
async def get_speaker_training_stats(speaker_id: str):
    """Get training statistics for specific speaker"""
    return realtime_handler.tts.get_training_stats(speaker_id)


@app.post("/training/start/{speaker_id}")
async def start_speaker_training(speaker_id: str):
    """Start F5-TTS training for specific speaker"""
    realtime_handler.tts.start_training(speaker_id)
    return {"status": "training_started", "speaker_id": speaker_id}


@app.post("/training/start-all")
async def start_all_training():
    """Start F5-TTS training for all ready speakers"""
    realtime_handler.tts.start_training()
    return {"status": "training_started_all"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)  # Port 8003 for multi-speaker version
