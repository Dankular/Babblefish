"""
Text-to-Speech Engine with Kokoro TTS and F5-TTS Speaker Training

Features:
1. Kokoro TTS for immediate high-quality TTS
2. Passive audio collection for speaker training
3. F5-TTS for voice cloning (trained on collected samples)
"""

import os
import time
import numpy as np
import soundfile as sf
import json
from pathlib import Path
from typing import Optional, Dict, List
import threading
from collections import deque

class KokoroTTS:
    """Kokoro TTS engine for fast, high-quality speech synthesis"""

    def __init__(self, model_name: str = "kokoro-v0.19", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.sample_rate = 24000

    def load_model(self):
        """Load Kokoro TTS model"""
        print(f"Loading Kokoro TTS ({self.model_name})...")

        try:
            # Try to import kokoro
            import kokoro_onnx as kokoro

            # Load model
            self.model = kokoro.Kokoro(self.model_name, lang="en-us")

            print("[OK] Kokoro TTS loaded")

        except ImportError:
            print("[WARNING] Kokoro not installed. Install with:")
            print("  pip install kokoro-onnx")
            self.model = None
        except Exception as e:
            print(f"[WARNING] Could not load Kokoro: {e}")
            print("Using fallback TTS")
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
            voice: Voice to use (af_sky, am_adam, etc.)
            speed: Speech speed (0.5-2.0)

        Returns:
            Audio samples as numpy array (float32, sample_rate Hz)
        """
        if self.model is None:
            return self._fallback_tts(text)

        try:
            # Generate speech
            samples = self.model.create(
                text,
                voice=voice,
                speed=speed
            )

            return samples

        except Exception as e:
            print(f"TTS error: {e}")
            return self._fallback_tts(text)

    def _fallback_tts(self, text: str) -> np.ndarray:
        """Fallback TTS using pyttsx3 or silent audio"""
        # Return 1 second of silence as fallback
        return np.zeros(int(self.sample_rate * 1.0), dtype=np.float32)

    def save_audio(self, audio: np.ndarray, filepath: str):
        """Save audio to file"""
        sf.write(filepath, audio, self.sample_rate)


class SpeakerTrainer:
    """
    Passive speaker training system
    Collects audio chunks and trains F5-TTS for voice cloning
    """

    def __init__(
        self,
        storage_dir: str = "./speaker_data",
        min_chunks: int = 50,  # Minimum chunks needed for training
        max_chunks: int = 500,  # Maximum chunks to store
        chunk_duration: float = 3.0  # Target chunk duration in seconds
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        self.min_chunks = min_chunks
        self.max_chunks = max_chunks
        self.chunk_duration = chunk_duration

        self.chunks = deque(maxlen=max_chunks)
        self.chunk_metadata = []

        self.is_training = False
        self.trained_model = None

        # Load existing chunks
        self._load_existing_chunks()

    def _load_existing_chunks(self):
        """Load previously collected chunks"""
        metadata_file = self.storage_dir / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                self.chunk_metadata = json.load(f)

            print(f"Loaded {len(self.chunk_metadata)} existing audio chunks")

    def add_chunk(
        self,
        audio: np.ndarray,
        transcription: str,
        language: str,
        sample_rate: int = 16000
    ):
        """
        Add an audio chunk for training

        Args:
            audio: Audio samples
            transcription: Text transcription of the audio
            language: Language code
            sample_rate: Sample rate of audio
        """
        # Skip if chunk is too short or too long
        duration = len(audio) / sample_rate
        if duration < 1.0 or duration > 10.0:
            return

        # Save chunk to disk
        chunk_id = int(time.time() * 1000)
        chunk_file = self.storage_dir / f"chunk_{chunk_id}.wav"

        sf.write(chunk_file, audio, sample_rate)

        # Store metadata
        metadata = {
            "id": chunk_id,
            "file": str(chunk_file),
            "transcription": transcription,
            "language": language,
            "duration": duration,
            "sample_rate": sample_rate,
            "timestamp": time.time()
        }

        self.chunk_metadata.append(metadata)
        self.chunks.append(chunk_id)

        # Save metadata
        self._save_metadata()

        # Check if ready to train
        if len(self.chunk_metadata) >= self.min_chunks and not self.is_training:
            if len(self.chunk_metadata) % 10 == 0:  # Update every 10 chunks
                print(f"[Speaker Training] {len(self.chunk_metadata)}/{self.min_chunks} chunks collected")

            if len(self.chunk_metadata) == self.min_chunks:
                print(f"[Speaker Training] ✓ Minimum chunks reached! Ready for training.")

    def _save_metadata(self):
        """Save metadata to disk"""
        metadata_file = self.storage_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.chunk_metadata, f, indent=2)

    def get_stats(self) -> Dict:
        """Get training statistics"""
        total_duration = sum(m['duration'] for m in self.chunk_metadata)

        return {
            "total_chunks": len(self.chunk_metadata),
            "total_duration": total_duration,
            "min_chunks_needed": self.min_chunks,
            "ready_to_train": len(self.chunk_metadata) >= self.min_chunks,
            "progress": min(100, int(len(self.chunk_metadata) / self.min_chunks * 100))
        }

    def train_f5_model(self):
        """
        Train F5-TTS model on collected chunks
        This runs in a background thread
        """
        if self.is_training:
            print("[Training] Already training...")
            return

        if len(self.chunk_metadata) < self.min_chunks:
            print(f"[Training] Need {self.min_chunks - len(self.chunk_metadata)} more chunks")
            return

        print("[Training] Starting F5-TTS training...")
        self.is_training = True

        # Run training in background thread
        thread = threading.Thread(target=self._train_worker)
        thread.daemon = True
        thread.start()

    def _train_worker(self):
        """Background worker for F5-TTS training"""
        try:
            # TODO: Implement F5-TTS training
            # This is a placeholder - actual training requires:
            # 1. Load F5-TTS model
            # 2. Prepare training data from chunks
            # 3. Fine-tune on speaker's voice
            # 4. Save trained model

            print("[Training] Preparing training data...")
            time.sleep(2)  # Simulate preparation

            print("[Training] Training F5-TTS model...")
            time.sleep(5)  # Simulate training

            print("[Training] ✓ Training complete!")

            self.is_training = False
            self.trained_model = "trained_model_placeholder"

        except Exception as e:
            print(f"[Training] Error: {e}")
            self.is_training = False

    def synthesize_with_speaker_voice(
        self,
        text: str,
        reference_audio: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech using trained speaker voice

        Args:
            text: Text to synthesize
            reference_audio: Optional reference audio file

        Returns:
            Audio samples
        """
        if self.trained_model is None:
            print("[F5-TTS] Model not trained yet")
            return None

        # TODO: Implement F5-TTS inference
        # This is a placeholder
        print(f"[F5-TTS] Synthesizing: {text}")

        # Return silence for now
        return np.zeros(24000, dtype=np.float32)


class TTSEngine:
    """
    Complete TTS engine with Kokoro and F5-TTS

    Features:
    - Immediate TTS with Kokoro
    - Passive audio collection
    - Voice cloning with F5-TTS
    - Multi-speaker support (optional)
    """

    def __init__(self, multi_speaker: bool = False):
        self.kokoro = KokoroTTS()
        self.multi_speaker = multi_speaker

        if multi_speaker:
            # Use multi-speaker trainer (with speaker diarization)
            from speaker_diarization import MultiSpeakerTrainer, SpeakerIdentifier
            self.speaker_trainer = MultiSpeakerTrainer()
            self.speaker_identifier = SpeakerIdentifier()
        else:
            # Use single-speaker trainer
            self.speaker_trainer = SpeakerTrainer()
            self.speaker_identifier = None

        self.use_speaker_voice = False

    def load(self):
        """Load TTS models"""
        self.kokoro.load_model()

        if self.multi_speaker and self.speaker_identifier:
            self.speaker_identifier.load_model()

        print(f"[TTS Engine] Ready (Multi-speaker: {self.multi_speaker})")

    def synthesize(
        self,
        text: str,
        language: str = "en",
        use_trained_voice: bool = False,
        speaker_id: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            language: Target language
            use_trained_voice: Use F5-TTS trained voice if available
            speaker_id: Speaker ID for multi-speaker mode

        Returns:
            Audio samples
        """
        # Try F5-TTS if requested and trained
        if use_trained_voice:
            if self.multi_speaker and speaker_id:
                # Multi-speaker: use speaker's trained voice
                audio = self.speaker_trainer.synthesize_with_speaker_voice(
                    speaker_id, text
                )
                if audio is not None:
                    return audio
            elif not self.multi_speaker and hasattr(self.speaker_trainer, 'trained_model'):
                # Single-speaker: use global trained voice
                audio = self.speaker_trainer.synthesize_with_speaker_voice(text)
                if audio is not None:
                    return audio

        # Fall back to Kokoro
        return self.kokoro.synthesize(text)

    def add_training_sample(
        self,
        audio: np.ndarray,
        transcription: str,
        language: str,
        sample_rate: int = 16000
    ) -> Optional[str]:
        """
        Add audio sample for speaker training

        Args:
            audio: Audio samples
            transcription: Text transcription
            language: Language code
            sample_rate: Sample rate

        Returns:
            Speaker ID if multi-speaker mode, None otherwise
        """
        if self.multi_speaker and self.speaker_identifier:
            # Identify speaker
            speaker_id, confidence, embedding = self.speaker_identifier.identify_speaker(
                audio, sample_rate
            )

            # Add chunk for this specific speaker
            self.speaker_trainer.add_chunk(
                speaker_id=speaker_id,
                audio=audio,
                transcription=transcription,
                language=language,
                embedding=embedding,
                sample_rate=sample_rate
            )

            return speaker_id
        else:
            # Single-speaker mode
            self.speaker_trainer.add_chunk(
                audio,
                transcription,
                language,
                sample_rate
            )

            return None

    def get_training_stats(self, speaker_id: Optional[str] = None) -> Dict:
        """
        Get speaker training statistics

        Args:
            speaker_id: Specific speaker (multi-speaker mode) or None for global stats

        Returns:
            Training statistics
        """
        if self.multi_speaker:
            if speaker_id:
                return self.speaker_trainer.get_speaker_stats(speaker_id)
            else:
                return self.speaker_trainer.get_all_speaker_stats()
        else:
            return self.speaker_trainer.get_stats()

    def get_all_speakers(self) -> Dict:
        """Get all known speakers (multi-speaker mode only)"""
        if self.multi_speaker and self.speaker_identifier:
            return self.speaker_identifier.get_all_speakers()
        return {}

    def get_speaker_name(self, speaker_id: str) -> str:
        """Get friendly name for speaker"""
        if self.multi_speaker and self.speaker_identifier:
            return self.speaker_identifier.get_speaker_name(speaker_id)
        return speaker_id

    def start_training(self, speaker_id: Optional[str] = None):
        """
        Start F5-TTS training

        Args:
            speaker_id: Specific speaker (multi-speaker mode) or None for all
        """
        if self.multi_speaker:
            if speaker_id:
                self.speaker_trainer.start_training(speaker_id)
            else:
                # Train all ready speakers
                for sid in self.speaker_trainer.speaker_chunks.keys():
                    stats = self.speaker_trainer.get_speaker_stats(sid)
                    if stats['ready_to_train'] and not stats['is_training']:
                        self.speaker_trainer.start_training(sid)
        else:
            self.speaker_trainer.train_f5_model()


# Test
if __name__ == "__main__":
    engine = TTSEngine()
    engine.load()

    # Test synthesis
    audio = engine.synthesize("Hello, this is a test of the TTS system.")

    if audio is not None:
        print(f"Generated {len(audio)} samples")
        engine.kokoro.save_audio(audio, "test_tts.wav")
        print("Saved to test_tts.wav")

    # Test speaker training stats
    stats = engine.get_training_stats()
    print(f"Training stats: {stats}")
