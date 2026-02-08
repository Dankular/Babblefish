"""
BabbleFish CPU Server - Heavy Lifting Edition
Optimized for multi-core CPU processing (128 threads)

Components:
- SeamlessM4T v2 medium (ASR + Translation in one model)
- Kokoro TTS (ONNX Runtime, multi-threaded)
- Speaker diarization (pyannote.audio)
- Multi-client WebSocket server

Resource allocation:
- SeamlessM4T: 32 threads, ~3-4GB RAM
- Kokoro TTS: 16 threads per synthesis, ~500MB RAM
- Speaker embeddings: 4 threads, ~200MB RAM
- WebSocket: 8 threads, ~100MB RAM
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import numpy as np
import torch
import json
import io
import time
import base64
from collections import defaultdict
from typing import Dict, List, Optional, Set
import threading
import wave
import tempfile
from pathlib import Path

# Set CPU thread allocation
torch.set_num_threads(32)  # For SeamlessM4T
import os
os.environ["OMP_NUM_THREADS"] = "32"
os.environ["MKL_NUM_THREADS"] = "32"

app = FastAPI(title="BabbleFish CPU Server")

# CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SeamlessM4TProcessor:
    """
    SeamlessM4T v2 for simultaneous ASR + Translation
    Optimized for CPU inference
    """

    def __init__(self, model_name: str = "facebook/seamless-m4t-v2-large", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None

    def load_model(self):
        """Load SeamlessM4T model optimized for CPU"""
        print(f"Loading SeamlessM4T v2 ({self.model_name})...")
        print(f"Using {torch.get_num_threads()} CPU threads")

        try:
            from transformers import SeamlessM4Tv2Model, AutoProcessor

            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.model_name)

            # Load model with CPU optimizations
            self.model = SeamlessM4Tv2Model.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,  # CPU works best with float32
                low_cpu_mem_usage=True
            ).to(self.device)

            # Set to eval mode for inference
            self.model.eval()

            print("[OK] SeamlessM4T v2 loaded (CPU optimized)")

        except ImportError:
            print("[ERROR] transformers library not found. Install with:")
            print("  pip install transformers sentencepiece")
            raise

        except Exception as e:
            print(f"[ERROR] Could not load SeamlessM4T: {e}")
            raise

    def process_audio(
        self,
        audio_path: str,
        target_lang: str = "eng",
        source_lang: Optional[str] = None
    ) -> Dict:
        """
        Process audio: ASR + Translation in one shot

        Args:
            audio_path: Path to audio file
            target_lang: Target language code (eng, spa, fra, deu, pol, etc.)
            source_lang: Source language (auto-detected if None)

        Returns:
            {
                "source_text": str,
                "source_lang": str,
                "translation": str,
                "target_lang": str,
                "latency_ms": float
            }
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        try:
            # Load and process audio
            import librosa
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Process with SeamlessM4T
            with torch.no_grad():
                # Audio input
                audio_inputs = self.processor(
                    audios=audio,
                    sampling_rate=16000,
                    return_tensors="pt"
                ).to(self.device)

                # Generate transcription (ASR)
                output_tokens = self.model.generate(
                    **audio_inputs,
                    tgt_lang=target_lang,
                    generate_speech=False  # Text only, no speech synthesis
                )

                # Decode transcription
                translation = self.processor.decode(
                    output_tokens[0].cpu().tolist(),
                    skip_special_tokens=True
                )

                # For source transcription, we need to run ASR without translation
                # TODO: Implement proper source language detection
                # For now, assume source transcription = translation if same language
                source_text = translation  # Simplified
                detected_lang = source_lang or "auto"

            latency = (time.time() - start_time) * 1000

            return {
                "source_text": source_text,
                "source_lang": detected_lang,
                "translation": translation,
                "target_lang": target_lang,
                "latency_ms": round(latency, 2)
            }

        except Exception as e:
            print(f"[ERROR] SeamlessM4T processing failed: {e}")
            import traceback
            traceback.print_exc()
            raise


class KokoroTTSServer:
    """
    Kokoro TTS with ONNX Runtime
    Optimized for multi-threaded CPU inference
    """

    def __init__(self, num_threads: int = 16):
        self.num_threads = num_threads
        self.model = None
        self.sample_rate = 24000

    def load_model(self):
        """Load Kokoro with ONNX optimization"""
        print(f"Loading Kokoro TTS (ONNX, {self.num_threads} threads)...")

        try:
            import kokoro_onnx as kokoro

            # ONNX Runtime will use the specified threads
            os.environ["OMP_NUM_THREADS"] = str(self.num_threads)

            self.model = kokoro.Kokoro("kokoro-v0.19", lang="en-us")

            print(f"[OK] Kokoro TTS loaded ({self.num_threads} threads)")

        except ImportError:
            print("[WARNING] kokoro-onnx not installed. Install with:")
            print("  pip install kokoro-onnx")
            self.model = None

        except Exception as e:
            print(f"[WARNING] Could not load Kokoro: {e}")
            self.model = None

    def synthesize(
        self,
        text: str,
        voice: str = "af_sky",
        speed: float = 1.0
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            voice: Voice ID
            speed: Speech speed

        Returns:
            Audio samples (24kHz, float32)
        """
        if self.model is None:
            return None

        try:
            start_time = time.time()

            audio = self.model.create(text, voice=voice, speed=speed)

            latency = (time.time() - start_time) * 1000
            print(f"[TTS] Synthesized {len(text)} chars in {latency:.1f}ms")

            return audio

        except Exception as e:
            print(f"[ERROR] TTS synthesis failed: {e}")
            return None


class SpeakerDiarizationServer:
    """Speaker identification using pyannote embeddings"""

    def __init__(self):
        self.embedding_model = None
        self.known_speakers = {}  # speaker_id -> average embedding
        self.speaker_metadata = {}
        self.next_speaker_id = 1
        self.similarity_threshold = 0.75

        self.speaker_names = [
            "Pierre", "Dan", "Marek", "Alice", "Bob", "Charlie",
            "Diana", "Eve", "Frank", "Grace", "Henry", "Iris"
        ]

    def load_model(self):
        """Load pyannote speaker embedding model"""
        print("Loading pyannote speaker embedding...")

        try:
            from pyannote.audio import Model, Inference

            model = Model.from_pretrained("pyannote/embedding")
            self.embedding_model = Inference(model, window="whole")

            print("[OK] Speaker embedding loaded")

        except Exception as e:
            print(f"[WARNING] Could not load pyannote: {e}")
            self.embedding_model = None

    def identify_speaker(self, audio: np.ndarray, sample_rate: int = 16000) -> tuple:
        """
        Identify speaker from audio

        Returns:
            (speaker_id, speaker_name, confidence, embedding)
        """
        if self.embedding_model is None:
            return "speaker_1", "Speaker", 1.0, None

        try:
            # Extract embedding
            audio_tensor = torch.from_numpy(audio).float()
            with torch.no_grad():
                embedding = self.embedding_model({
                    "waveform": audio_tensor.unsqueeze(0),
                    "sample_rate": sample_rate
                })

            # Normalize
            embedding = embedding / np.linalg.norm(embedding)

            # Match with known speakers
            if not self.known_speakers:
                speaker_id = self._register_speaker(embedding)
                speaker_name = self.speaker_metadata[speaker_id]["name"]
                return speaker_id, speaker_name, 1.0, embedding

            # Find best match
            best_id = None
            best_sim = -1.0

            for sid, avg_emb in self.known_speakers.items():
                sim = np.dot(embedding, avg_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_id = sid

            # Check threshold
            if best_sim >= self.similarity_threshold:
                # Update embedding
                self._update_speaker(best_id, embedding)
                speaker_name = self.speaker_metadata[best_id]["name"]
                return best_id, speaker_name, best_sim, embedding
            else:
                # New speaker
                speaker_id = self._register_speaker(embedding)
                speaker_name = self.speaker_metadata[speaker_id]["name"]
                return speaker_id, speaker_name, 1.0, embedding

        except Exception as e:
            print(f"[ERROR] Speaker identification failed: {e}")
            return "speaker_1", "Speaker", 0.0, None

    def _register_speaker(self, embedding: np.ndarray) -> str:
        """Register new speaker"""
        speaker_id = f"speaker_{self.next_speaker_id}"
        name_idx = min(self.next_speaker_id - 1, len(self.speaker_names) - 1)
        speaker_name = self.speaker_names[name_idx]

        self.known_speakers[speaker_id] = embedding.copy()
        self.speaker_metadata[speaker_id] = {
            "id": speaker_id,
            "name": speaker_name,
            "first_seen": time.time(),
            "samples": 1
        }

        self.next_speaker_id += 1
        print(f"[Speaker] New: {speaker_name} ({speaker_id})")

        return speaker_id

    def _update_speaker(self, speaker_id: str, new_embedding: np.ndarray):
        """Update speaker embedding (running average)"""
        alpha = 0.1
        current = self.known_speakers[speaker_id]
        updated = (1 - alpha) * current + alpha * new_embedding
        self.known_speakers[speaker_id] = updated / np.linalg.norm(updated)
        self.speaker_metadata[speaker_id]["samples"] += 1


class MultiClientHandler:
    """
    Manages multiple connected clients
    Each client can request different target languages

    Supports optional TTS accelerator (laptop with F5-TTS on GPU)
    """

    def __init__(self, seamless: SeamlessM4TProcessor, tts: KokoroTTSServer, speaker: SpeakerDiarizationServer):
        self.seamless = seamless
        self.tts = tts
        self.speaker = speaker

        # Active connections: client_id -> {websocket, target_lang, name}
        self.clients: Dict[str, Dict] = {}
        self.client_lock = threading.Lock()

        # Optional TTS accelerator (laptop with F5-TTS)
        self.tts_accelerator = None
        self.tts_accelerator_lock = threading.Lock()
        self.pending_f5_requests: Dict[str, Dict] = {}  # request_id -> {text, speaker_id, callback}

    async def handle_client(self, websocket: WebSocket, client_id: str, target_lang: str, client_name: str):
        """Handle audio from a single client"""
        print(f"[Client] {client_name} connected (target: {target_lang})")

        # Register client
        with self.client_lock:
            self.clients[client_id] = {
                "websocket": websocket,
                "target_lang": target_lang,
                "name": client_name
            }

        # Send ready message
        await websocket.send_json({
            "type": "ready",
            "message": f"Server ready ({torch.get_num_threads()} threads)",
            "client_id": client_id,
            "target_lang": target_lang
        })

        try:
            while True:
                # Receive audio chunk
                data = await websocket.receive_bytes()
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                # Check if this is a complete utterance (client sends marker)
                # For now, assume each chunk is a complete utterance
                # In production, client would buffer and send on VAD end-of-speech

                if len(audio) < 16000:  # Skip very short audio
                    continue

                # Process in background thread pool
                asyncio.create_task(
                    self._process_utterance(audio, client_id, websocket)
                )

        except WebSocketDisconnect:
            print(f"[Client] {client_name} disconnected")
            with self.client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]

        except Exception as e:
            print(f"[ERROR] Client {client_name} error: {e}")
            import traceback
            traceback.print_exc()

    async def _process_utterance(self, audio: np.ndarray, client_id: str, websocket: WebSocket):
        """Process a complete utterance"""
        start_time = time.time()

        try:
            # Get client info
            with self.client_lock:
                if client_id not in self.clients:
                    return
                client_info = self.clients[client_id]
                target_lang = client_info["target_lang"]

            # 1. Identify speaker
            speaker_id, speaker_name, confidence, embedding = self.speaker.identify_speaker(audio)

            # 2. Save temp audio file
            temp_file = self._save_temp_audio(audio)

            # 3. Process with SeamlessM4T (ASR + Translation)
            result = self.seamless.process_audio(
                temp_file,
                target_lang=target_lang
            )

            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

            # 4. Synthesize TTS (Dual-path: Kokoro immediate + F5-TTS optional)
            kokoro_audio_b64 = None
            tts_voice_used = "none"

            if result["translation"]:
                # Fast path: Kokoro TTS (immediate, ~300ms)
                kokoro_audio = self.tts.synthesize(result["translation"])

                if kokoro_audio is not None:
                    # Encode to WAV and base64
                    import soundfile as sf
                    buffer = io.BytesIO()
                    sf.write(buffer, kokoro_audio, 24000, format='WAV')
                    kokoro_audio_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    tts_voice_used = "kokoro"

                # Quality path: Request F5-TTS from laptop accelerator (optional, ~800ms later)
                with self.tts_accelerator_lock:
                    if self.tts_accelerator is not None:
                        # Send request to laptop for cloned voice
                        asyncio.create_task(
                            self._request_f5_tts(
                                result["translation"],
                                speaker_id,
                                speaker_name,
                                client_id,
                                websocket
                            )
                        )

            # 5. Send result back to client (with Kokoro audio)
            total_latency = (time.time() - start_time) * 1000

            response = {
                "type": "result",
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "speaker_confidence": round(confidence, 3),
                "source_text": result["source_text"],
                "source_lang": result["source_lang"],
                "translation": result["translation"],
                "target_lang": result["target_lang"],
                "tts_audio": kokoro_audio_b64,
                "tts_voice": tts_voice_used,
                "has_f5_pending": self.tts_accelerator is not None,  # Will F5-TTS follow?
                "latency_ms": round(total_latency, 2),
                "timestamp": time.time()
            }

            await websocket.send_json(response)

            print(f"[Processing] {speaker_name}: {total_latency:.0f}ms ({result['source_lang']} → {target_lang})")

            # 6. Broadcast to other clients (if they want same translation)
            await self._broadcast_to_others(response, client_id)

        except Exception as e:
            print(f"[ERROR] Processing utterance: {e}")
            import traceback
            traceback.print_exc()

    async def _request_f5_tts(
        self,
        text: str,
        speaker_id: str,
        speaker_name: str,
        client_id: str,
        websocket: WebSocket
    ):
        """Request F5-TTS synthesis from laptop accelerator"""
        if self.tts_accelerator is None:
            return

        request_id = f"{client_id}_{int(time.time() * 1000)}"

        try:
            # Send F5-TTS request to laptop
            await self.tts_accelerator["websocket"].send_json({
                "type": "tts_request",
                "request_id": request_id,
                "text": text,
                "speaker_id": speaker_id,
                "speaker_name": speaker_name
            })

            print(f"[F5-TTS] Requested cloned voice for {speaker_name}")

        except Exception as e:
            print(f"[F5-TTS] Request failed: {e}")

    async def handle_tts_accelerator(self, websocket: WebSocket):
        """Handle connection from laptop TTS accelerator"""
        print("[TTS Accelerator] Laptop connected")

        with self.tts_accelerator_lock:
            self.tts_accelerator = {
                "websocket": websocket,
                "connected_at": time.time()
            }

        # Send ready message
        await websocket.send_json({
            "type": "ready",
            "message": "TTS accelerator registered",
            "known_speakers": self.speaker.speaker_metadata
        })

        try:
            while True:
                data = await websocket.receive_json()

                if data["type"] == "tts_result":
                    # Received cloned audio from laptop
                    await self._handle_f5_result(data)

        except WebSocketDisconnect:
            print("[TTS Accelerator] Laptop disconnected")
            with self.tts_accelerator_lock:
                self.tts_accelerator = None

        except Exception as e:
            print(f"[TTS Accelerator] Error: {e}")
            with self.tts_accelerator_lock:
                self.tts_accelerator = None

    async def _handle_f5_result(self, data: Dict):
        """Handle F5-TTS result from laptop"""
        request_id = data.get("request_id")
        f5_audio_b64 = data.get("audio")
        speaker_name = data.get("speaker_name")

        if not f5_audio_b64:
            return

        # Broadcast cloned audio to all relevant clients
        result = {
            "type": "f5_result",
            "speaker_name": speaker_name,
            "tts_audio": f5_audio_b64,
            "tts_voice": "f5_cloned",
            "timestamp": time.time()
        }

        # Send to all connected clients
        with self.client_lock:
            for client_info in self.clients.values():
                try:
                    await client_info["websocket"].send_json(result)
                except:
                    pass  # Client disconnected

        print(f"[F5-TTS] Sent cloned voice for {speaker_name}")

    async def _broadcast_to_others(self, result: Dict, sender_id: str):
        """Broadcast translation to other clients with matching target language"""
        with self.client_lock:
            for cid, client_info in self.clients.items():
                if cid == sender_id:
                    continue

                # Check if this client wants this language
                if client_info["target_lang"] == result["target_lang"]:
                    try:
                        await client_info["websocket"].send_json(result)
                    except:
                        pass  # Client disconnected

    def _save_temp_audio(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Save audio to temporary WAV file"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_int16 = (audio * 32768).astype(np.int16)

        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return temp_file.name


# Global instances
seamless_processor = None
kokoro_tts = None
speaker_diarization = None
multi_client_handler = None


@app.on_event("startup")
async def startup():
    """Load all models on startup"""
    global seamless_processor, kokoro_tts, speaker_diarization, multi_client_handler

    print("="*60)
    print("BabbleFish CPU Server - Initializing")
    print("="*60)

    # Load models
    seamless_processor = SeamlessM4TProcessor()
    seamless_processor.load_model()

    kokoro_tts = KokoroTTSServer(num_threads=16)
    kokoro_tts.load_model()

    speaker_diarization = SpeakerDiarizationServer()
    speaker_diarization.load_model()

    # Create multi-client handler
    multi_client_handler = MultiClientHandler(
        seamless_processor,
        kokoro_tts,
        speaker_diarization
    )

    print("="*60)
    print("[OK] Server ready for clients")
    print(f"[INFO] CPU threads: {torch.get_num_threads()}")
    print("="*60)


@app.websocket("/ws/client")
async def websocket_client(websocket: WebSocket):
    """
    WebSocket endpoint for thin clients

    Query params:
    - client_id: Unique client identifier
    - target_lang: Target language (eng, spa, fra, deu, pol, etc.)
    - name: Client display name
    """
    await websocket.accept()

    client_id = websocket.query_params.get("client_id", f"client_{time.time()}")
    target_lang = websocket.query_params.get("target_lang", "eng")
    client_name = websocket.query_params.get("name", "Unknown")

    await multi_client_handler.handle_client(websocket, client_id, target_lang, client_name)


@app.websocket("/ws/tts-accelerator")
async def websocket_tts_accelerator(websocket: WebSocket):
    """
    WebSocket endpoint for laptop TTS accelerator
    Laptop runs F5-TTS on GPU for voice cloning
    """
    await websocket.accept()

    await multi_client_handler.handle_tts_accelerator(websocket)


@app.get("/")
async def root():
    """Server status"""
    return {
        "service": "BabbleFish CPU Server",
        "status": "running",
        "models": {
            "seamless": seamless_processor is not None,
            "tts": kokoro_tts is not None,
            "speaker": speaker_diarization is not None
        },
        "cpu_threads": torch.get_num_threads(),
        "clients": len(multi_client_handler.clients) if multi_client_handler else 0
    }


@app.get("/speakers")
async def get_speakers():
    """Get all known speakers"""
    if speaker_diarization:
        return {
            "speakers": speaker_diarization.speaker_metadata,
            "count": len(speaker_diarization.known_speakers)
        }
    return {"speakers": {}, "count": 0}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("Starting BabbleFish CPU Server")
    print("Optimized for 128-core processing")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info",
        workers=1  # Single worker to share model memory
    )
