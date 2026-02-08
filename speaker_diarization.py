"""
Speaker Diarization and Tracking
Uses pyannote.audio for speaker identification and embedding extraction
"""

import numpy as np
import torch
from typing import Dict, Optional, Tuple
from pathlib import Path
import json
import time
from collections import defaultdict

class SpeakerIdentifier:
    """
    Identifies and tracks speakers using pyannote.audio embeddings
    """

    def __init__(
        self,
        embedding_model: str = "pyannote/embedding",
        similarity_threshold: float = 0.75,
        min_speech_duration: float = 1.0
    ):
        """
        Args:
            embedding_model: Hugging Face model for speaker embeddings
            similarity_threshold: Cosine similarity threshold for same speaker (0-1)
            min_speech_duration: Minimum speech duration to extract embedding (seconds)
        """
        self.embedding_model_name = embedding_model
        self.similarity_threshold = similarity_threshold
        self.min_speech_duration = min_speech_duration

        self.embedding_model = None
        self.known_speakers = {}  # speaker_id -> average embedding
        self.speaker_metadata = {}  # speaker_id -> metadata
        self.next_speaker_id = 1

        # Speaker names (auto-assigned)
        self.speaker_names = [
            "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank",
            "Grace", "Henry", "Iris", "Jack", "Kate", "Liam",
            "Maya", "Noah", "Olivia", "Pierre", "Quinn", "Ruby"
        ]

    def load_model(self):
        """Load pyannote embedding model"""
        print("Loading pyannote speaker embedding model...")

        try:
            from pyannote.audio import Model, Inference

            # Load embedding model
            model = Model.from_pretrained(self.embedding_model_name)
            self.embedding_model = Inference(model, window="whole")

            print("[OK] Pyannote embedding model loaded")

        except ImportError:
            print("[WARNING] pyannote.audio not installed. Install with:")
            print("  pip install pyannote.audio")
            self.embedding_model = None

        except Exception as e:
            print(f"[WARNING] Could not load pyannote model: {e}")
            print("Note: You may need a Hugging Face token for pyannote models")
            print("  huggingface-cli login")
            self.embedding_model = None

    def extract_embedding(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Optional[np.ndarray]:
        """
        Extract speaker embedding from audio

        Args:
            audio: Audio samples (float32)
            sample_rate: Sample rate

        Returns:
            Speaker embedding vector (normalized)
        """
        if self.embedding_model is None:
            return None

        # Check minimum duration
        duration = len(audio) / sample_rate
        if duration < self.min_speech_duration:
            return None

        try:
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio).float()

            # Extract embedding
            with torch.no_grad():
                embedding = self.embedding_model({"waveform": audio_tensor.unsqueeze(0), "sample_rate": sample_rate})

            # Normalize
            embedding = embedding / np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return None

    def identify_speaker(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Tuple[str, float, np.ndarray]:
        """
        Identify speaker from audio segment

        Args:
            audio: Audio samples
            sample_rate: Sample rate

        Returns:
            Tuple of (speaker_id, confidence, embedding)
        """
        # Extract embedding
        embedding = self.extract_embedding(audio, sample_rate)

        if embedding is None:
            # Fallback to default speaker
            return "speaker_1", 0.0, None

        # If no known speakers, register as first speaker
        if not self.known_speakers:
            speaker_id = self._register_new_speaker(embedding)
            return speaker_id, 1.0, embedding

        # Compare with known speakers
        best_speaker = None
        best_similarity = -1.0

        for speaker_id, avg_embedding in self.known_speakers.items():
            similarity = self._cosine_similarity(embedding, avg_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_speaker = speaker_id

        # Check if similarity meets threshold
        if best_similarity >= self.similarity_threshold:
            # Update speaker's average embedding
            self._update_speaker_embedding(best_speaker, embedding)
            return best_speaker, best_similarity, embedding
        else:
            # New speaker
            speaker_id = self._register_new_speaker(embedding)
            return speaker_id, 1.0, embedding

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    def _register_new_speaker(self, embedding: np.ndarray) -> str:
        """Register a new speaker"""
        speaker_id = f"speaker_{self.next_speaker_id}"
        speaker_name = self.speaker_names[min(self.next_speaker_id - 1, len(self.speaker_names) - 1)]

        self.known_speakers[speaker_id] = embedding.copy()
        self.speaker_metadata[speaker_id] = {
            "id": speaker_id,
            "name": speaker_name,
            "first_seen": time.time(),
            "samples_count": 1,
            "total_duration": 0.0
        }

        self.next_speaker_id += 1

        print(f"[Speaker] New speaker detected: {speaker_name} ({speaker_id})")

        return speaker_id

    def _update_speaker_embedding(self, speaker_id: str, new_embedding: np.ndarray):
        """Update speaker's average embedding with new sample"""
        # Running average
        alpha = 0.1  # Weight for new embedding
        current_emb = self.known_speakers[speaker_id]
        updated_emb = (1 - alpha) * current_emb + alpha * new_embedding

        # Re-normalize
        self.known_speakers[speaker_id] = updated_emb / np.linalg.norm(updated_emb)

        # Update metadata
        self.speaker_metadata[speaker_id]["samples_count"] += 1

    def get_speaker_name(self, speaker_id: str) -> str:
        """Get friendly name for speaker"""
        if speaker_id in self.speaker_metadata:
            return self.speaker_metadata[speaker_id]["name"]
        return speaker_id

    def get_all_speakers(self) -> Dict:
        """Get all known speakers with metadata"""
        return self.speaker_metadata.copy()

    def save_speakers(self, filepath: str):
        """Save speaker data to disk"""
        data = {
            "speakers": self.speaker_metadata,
            "embeddings": {sid: emb.tolist() for sid, emb in self.known_speakers.items()},
            "next_id": self.next_speaker_id
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_speakers(self, filepath: str):
        """Load speaker data from disk"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.speaker_metadata = data["speakers"]
            self.known_speakers = {sid: np.array(emb) for sid, emb in data["embeddings"].items()}
            self.next_speaker_id = data["next_id"]

            print(f"[Speaker] Loaded {len(self.known_speakers)} known speakers")

        except FileNotFoundError:
            print("[Speaker] No previous speaker data found")
        except Exception as e:
            print(f"[Speaker] Error loading speakers: {e}")


class MultiSpeakerTrainer:
    """
    Manages F5-TTS training for multiple speakers
    Each speaker gets their own trained voice model
    """

    def __init__(
        self,
        storage_dir: str = "./speaker_data",
        min_chunks_per_speaker: int = 50,
        max_chunks_per_speaker: int = 500
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        self.min_chunks = min_chunks_per_speaker
        self.max_chunks = max_chunks_per_speaker

        # Per-speaker training data
        self.speaker_chunks = defaultdict(list)  # speaker_id -> [chunk_ids]
        self.chunk_metadata = {}  # chunk_id -> metadata

        # Per-speaker models
        self.trained_models = {}  # speaker_id -> trained_model
        self.training_status = {}  # speaker_id -> is_training

        # Load existing data
        self._load_existing_data()

    def _load_existing_data(self):
        """Load previously collected chunks"""
        metadata_file = self.storage_dir / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                self.chunk_metadata = data.get("chunks", {})

                # Rebuild speaker_chunks mapping
                for chunk_id, meta in self.chunk_metadata.items():
                    speaker_id = meta.get("speaker_id", "speaker_1")
                    self.speaker_chunks[speaker_id].append(chunk_id)

            print(f"[MultiSpeaker] Loaded {len(self.chunk_metadata)} chunks for {len(self.speaker_chunks)} speakers")

    def add_chunk(
        self,
        speaker_id: str,
        audio: np.ndarray,
        transcription: str,
        language: str,
        embedding: Optional[np.ndarray] = None,
        sample_rate: int = 16000
    ):
        """
        Add audio chunk for specific speaker

        Args:
            speaker_id: Speaker identifier
            audio: Audio samples
            transcription: Text transcription
            language: Language code
            embedding: Speaker embedding (optional)
            sample_rate: Sample rate
        """
        # Check duration
        duration = len(audio) / sample_rate
        if duration < 1.0 or duration > 10.0:
            return

        # Save chunk
        chunk_id = f"{speaker_id}_{int(time.time() * 1000)}"
        chunk_file = self.storage_dir / f"{chunk_id}.wav"

        import soundfile as sf
        sf.write(chunk_file, audio, sample_rate)

        # Store metadata
        metadata = {
            "id": chunk_id,
            "speaker_id": speaker_id,
            "file": str(chunk_file),
            "transcription": transcription,
            "language": language,
            "duration": duration,
            "sample_rate": sample_rate,
            "timestamp": time.time(),
            "embedding": embedding.tolist() if embedding is not None else None
        }

        self.chunk_metadata[chunk_id] = metadata
        self.speaker_chunks[speaker_id].append(chunk_id)

        # Keep only max_chunks per speaker
        if len(self.speaker_chunks[speaker_id]) > self.max_chunks:
            old_chunk = self.speaker_chunks[speaker_id].pop(0)
            if old_chunk in self.chunk_metadata:
                del self.chunk_metadata[old_chunk]

        # Save metadata
        self._save_metadata()

        # Check training readiness
        chunk_count = len(self.speaker_chunks[speaker_id])
        if chunk_count == self.min_chunks:
            print(f"[MultiSpeaker] ✓ {speaker_id} ready for training! ({chunk_count} chunks)")
        elif chunk_count % 10 == 0 and chunk_count < self.min_chunks:
            print(f"[MultiSpeaker] {speaker_id}: {chunk_count}/{self.min_chunks} chunks collected")

    def _save_metadata(self):
        """Save metadata to disk"""
        metadata_file = self.storage_dir / "metadata.json"
        data = {
            "chunks": self.chunk_metadata,
            "updated": time.time()
        }

        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_speaker_stats(self, speaker_id: str) -> Dict:
        """Get training statistics for a speaker"""
        chunks = self.speaker_chunks.get(speaker_id, [])

        total_duration = sum(
            self.chunk_metadata[cid]["duration"]
            for cid in chunks
            if cid in self.chunk_metadata
        )

        is_training = self.training_status.get(speaker_id, False)
        has_model = speaker_id in self.trained_models

        return {
            "speaker_id": speaker_id,
            "total_chunks": len(chunks),
            "total_duration": total_duration,
            "min_chunks_needed": self.min_chunks,
            "ready_to_train": len(chunks) >= self.min_chunks,
            "is_training": is_training,
            "has_trained_model": has_model,
            "progress": min(100, int(len(chunks) / self.min_chunks * 100))
        }

    def get_all_speaker_stats(self) -> Dict[str, Dict]:
        """Get stats for all speakers"""
        return {
            speaker_id: self.get_speaker_stats(speaker_id)
            for speaker_id in self.speaker_chunks.keys()
        }

    def synthesize_with_speaker_voice(
        self,
        speaker_id: str,
        text: str,
        reference_audio: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Synthesize speech using speaker's trained voice

        Args:
            speaker_id: Speaker to synthesize
            text: Text to synthesize
            reference_audio: Optional reference audio file

        Returns:
            Audio samples
        """
        if speaker_id not in self.trained_models:
            return None

        # TODO: Implement F5-TTS inference with speaker model
        # This is a placeholder
        print(f"[F5-TTS] Synthesizing for {speaker_id}: {text}")

        # Return silence for now
        return np.zeros(24000, dtype=np.float32)

    def start_training(self, speaker_id: str):
        """Start F5-TTS training for a specific speaker"""
        chunks = self.speaker_chunks.get(speaker_id, [])

        if len(chunks) < self.min_chunks:
            print(f"[Training] {speaker_id} needs {self.min_chunks - len(chunks)} more chunks")
            return

        if self.training_status.get(speaker_id, False):
            print(f"[Training] {speaker_id} already training...")
            return

        print(f"[Training] Starting F5-TTS training for {speaker_id}...")
        self.training_status[speaker_id] = True

        # Run in background thread
        import threading
        thread = threading.Thread(target=self._train_worker, args=(speaker_id,))
        thread.daemon = True
        thread.start()

    def _train_worker(self, speaker_id: str):
        """Background worker for F5-TTS training"""
        try:
            # TODO: Implement actual F5-TTS training
            print(f"[Training] Preparing training data for {speaker_id}...")
            time.sleep(2)

            print(f"[Training] Training F5-TTS model for {speaker_id}...")
            time.sleep(5)

            print(f"[Training] ✓ {speaker_id} training complete!")

            self.trained_models[speaker_id] = "trained_model_placeholder"
            self.training_status[speaker_id] = False

        except Exception as e:
            print(f"[Training] Error training {speaker_id}: {e}")
            self.training_status[speaker_id] = False


# Test
if __name__ == "__main__":
    # Test speaker identification
    identifier = SpeakerIdentifier()
    identifier.load_model()

    # Simulate two different speakers
    np.random.seed(42)
    audio1 = np.random.randn(16000 * 2).astype(np.float32) * 0.1
    audio2 = np.random.randn(16000 * 2).astype(np.float32) * 0.1

    speaker1, conf1, emb1 = identifier.identify_speaker(audio1)
    print(f"Speaker 1: {speaker1} (confidence: {conf1:.3f})")

    speaker2, conf2, emb2 = identifier.identify_speaker(audio2)
    print(f"Speaker 2: {speaker2} (confidence: {conf2:.3f})")

    # Test multi-speaker trainer
    trainer = MultiSpeakerTrainer()

    trainer.add_chunk(speaker1, audio1, "Hello world", "en")
    trainer.add_chunk(speaker2, audio2, "Bonjour monde", "fr")

    print("\nSpeaker stats:")
    for sid, stats in trainer.get_all_speaker_stats().items():
        print(f"  {sid}: {stats['total_chunks']} chunks ({stats['progress']}%)")
