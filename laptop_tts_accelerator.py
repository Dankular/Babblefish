"""
Laptop TTS Accelerator - F5-TTS Voice Cloning on 3050 GPU

This laptop connects to the server as an optional "TTS accelerator"
Receives text + speaker ID, synthesizes with F5-TTS cloned voice, sends back audio

Phase 2 addition - server works without this, but quality improves with it
"""

import asyncio
import websockets
import json
import numpy as np
import torch
import io
import base64
from typing import Dict, Optional
import time
from pathlib import Path

# Check GPU availability
if torch.cuda.is_available():
    print(f"[GPU] Found: {torch.cuda.get_device_name(0)}")
    print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("[WARNING] No GPU found, F5-TTS will be slow on CPU")


class F5TTSEngine:
    """
    F5-TTS for voice cloning
    Runs on 3050 GPU (4GB VRAM fits perfectly)
    """

    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.model = None
        self.sample_rate = 24000

        # Speaker voice references (collected passively or from samples)
        self.speaker_references: Dict[str, np.ndarray] = {}
        self.reference_path = Path("./speaker_references")
        self.reference_path.mkdir(exist_ok=True)

    def load_model(self):
        """Load F5-TTS model"""
        print(f"Loading F5-TTS on {self.device}...")

        try:
            # Placeholder - actual F5-TTS loading would go here
            # from f5_tts import F5TTS
            # self.model = F5TTS.from_pretrained("F5-TTS", device=self.device)

            print("[OK] F5-TTS loaded (PLACEHOLDER)")
            print(f"[INFO] Using device: {self.device}")

            if self.device == "cuda":
                print(f"[INFO] VRAM allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")

        except Exception as e:
            print(f"[ERROR] Could not load F5-TTS: {e}")
            print("[INFO] Using placeholder - install F5-TTS for actual voice cloning")
            self.model = "placeholder"

    def synthesize(
        self,
        text: str,
        speaker_id: str,
        speaker_name: str
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech with cloned voice

        Args:
            text: Text to synthesize
            speaker_id: Speaker identifier
            speaker_name: Speaker name

        Returns:
            Audio samples (24kHz, float32)
        """
        if self.model is None:
            return None

        start_time = time.time()

        try:
            # Get or create reference for this speaker
            reference_audio = self._get_speaker_reference(speaker_id, speaker_name)

            if reference_audio is None:
                print(f"[F5-TTS] No reference for {speaker_name}, using default")
                # Could fallback to generic voice or wait for more samples
                return None

            # TODO: Actual F5-TTS synthesis
            # audio = self.model.synthesize(
            #     text=text,
            #     reference_audio=reference_audio,
            #     reference_text="",  # F5-TTS can work without reference text
            # )

            # Placeholder: Return silence
            audio = np.zeros(int(self.sample_rate * 2), dtype=np.float32)

            latency = (time.time() - start_time) * 1000
            print(f"[F5-TTS] Synthesized {len(text)} chars in {latency:.1f}ms ({speaker_name})")

            if self.device == "cuda":
                vram_used = torch.cuda.memory_allocated(0) / 1024**3
                print(f"[GPU] VRAM used: {vram_used:.2f} GB")

            return audio

        except Exception as e:
            print(f"[ERROR] F5-TTS synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_speaker_reference(self, speaker_id: str, speaker_name: str) -> Optional[np.ndarray]:
        """Get reference audio for speaker"""

        # Check cache
        if speaker_id in self.speaker_references:
            return self.speaker_references[speaker_id]

        # Check disk
        reference_file = self.reference_path / f"{speaker_id}_reference.wav"
        if reference_file.exists():
            import soundfile as sf
            audio, sr = sf.read(reference_file)
            self.speaker_references[speaker_id] = audio
            print(f"[F5-TTS] Loaded reference for {speaker_name}")
            return audio

        # No reference available
        print(f"[F5-TTS] No reference for {speaker_name} ({speaker_id})")
        return None

    def add_reference_sample(
        self,
        speaker_id: str,
        speaker_name: str,
        audio: np.ndarray
    ):
        """
        Add reference sample for speaker
        Can be called from server when collecting passive training data
        """
        reference_file = self.reference_path / f"{speaker_id}_reference.wav"

        # Save reference
        import soundfile as sf
        sf.write(reference_file, audio, self.sample_rate)

        # Cache
        self.speaker_references[speaker_id] = audio

        print(f"[F5-TTS] Added reference for {speaker_name}")


class TTSAccelerator:
    """Connects to server and provides F5-TTS acceleration"""

    def __init__(self, server_url: str = "ws://localhost:9000/ws/tts-accelerator"):
        self.server_url = server_url
        self.f5_tts = F5TTSEngine()
        self.websocket = None

    async def connect(self):
        """Connect to server and start processing"""
        print(f"[Accelerator] Connecting to {self.server_url}...")

        # Load F5-TTS model
        self.f5_tts.load_model()

        try:
            async with websockets.connect(self.server_url) as websocket:
                self.websocket = websocket
                print("[Accelerator] Connected to server")

                # Process messages
                async for message in websocket:
                    data = json.loads(message)

                    if data["type"] == "ready":
                        print(f"[Accelerator] {data['message']}")
                        print(f"[Accelerator] Known speakers: {len(data.get('known_speakers', {}))}")

                    elif data["type"] == "tts_request":
                        # Server requesting cloned voice
                        await self._handle_tts_request(data)

        except websockets.exceptions.ConnectionClosed:
            print("[Accelerator] Connection closed by server")
        except Exception as e:
            print(f"[Accelerator] Error: {e}")
            import traceback
            traceback.print_exc()

    async def _handle_tts_request(self, data: Dict):
        """Handle TTS synthesis request from server"""
        request_id = data["request_id"]
        text = data["text"]
        speaker_id = data["speaker_id"]
        speaker_name = data["speaker_name"]

        print(f"[Request] {speaker_name}: {text[:50]}...")

        start_time = time.time()

        # Synthesize with F5-TTS
        audio = self.f5_tts.synthesize(text, speaker_id, speaker_name)

        if audio is None:
            print(f"[F5-TTS] Synthesis failed for {speaker_name}")
            return

        # Encode to base64 WAV
        try:
            import soundfile as sf
            buffer = io.BytesIO()
            sf.write(buffer, audio, 24000, format='WAV')
            audio_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            total_latency = (time.time() - start_time) * 1000

            # Send result back to server
            await self.websocket.send(json.dumps({
                "type": "tts_result",
                "request_id": request_id,
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "audio": audio_b64,
                "latency_ms": round(total_latency, 2)
            }))

            print(f"[F5-TTS] Sent cloned voice for {speaker_name} ({total_latency:.0f}ms)")

        except Exception as e:
            print(f"[ERROR] Failed to encode audio: {e}")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="BabbleFish TTS Accelerator")
    parser.add_argument(
        "--server",
        default="ws://localhost:9000/ws/tts-accelerator",
        help="Server WebSocket URL"
    )
    args = parser.parse_args()

    print("="*60)
    print("BabbleFish TTS Accelerator - F5-TTS Voice Cloning")
    print("="*60)
    print(f"Server: {args.server}")
    print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only'}")
    print("="*60)
    print()

    accelerator = TTSAccelerator(server_url=args.server)

    while True:
        try:
            await accelerator.connect()
            print("\n[Accelerator] Disconnected. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\n[Accelerator] Shutting down...")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            print("Reconnecting in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
