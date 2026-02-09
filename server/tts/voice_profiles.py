"""
Voice Profile Manager for Chatterbox TTS
Stores and loads custom reference voices for voice cloning
"""
import logging
import numpy as np
import librosa
from pathlib import Path
from typing import Optional, Dict
import json
import urllib.request

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000  # Chatterbox expects 24kHz


class VoiceProfile:
    """Represents a voice profile with reference audio"""

    def __init__(self, name: str, audio: np.ndarray, description: str = ""):
        self.name = name
        self.audio = audio  # float32 numpy array at 24kHz
        self.description = description

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "audio_shape": self.audio.shape,
            "audio_duration": len(self.audio) / SAMPLE_RATE
        }


class VoiceProfileManager:
    """Manages voice profiles for Chatterbox voice cloning"""

    def __init__(self, profiles_dir: str = "models/voice_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, VoiceProfile] = {}
        self._load_profiles()
        logger.info(f"VoiceProfileManager initialized with {len(self.profiles)} profiles")

    def _load_profiles(self):
        """Load all saved voice profiles from disk"""
        metadata_file = self.profiles_dir / "profiles.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            for profile_data in metadata.get("profiles", []):
                name = profile_data["name"]
                audio_file = self.profiles_dir / f"{name}.npy"
                if audio_file.exists():
                    audio = np.load(audio_file)
                    self.profiles[name] = VoiceProfile(
                        name=name,
                        audio=audio,
                        description=profile_data.get("description", "")
                    )
                    logger.info(f"Loaded voice profile: {name}")

    def _save_metadata(self):
        """Save profiles metadata to disk"""
        metadata = {
            "profiles": [
                {
                    "name": p.name,
                    "description": p.description,
                    "audio_duration": len(p.audio) / SAMPLE_RATE
                }
                for p in self.profiles.values()
            ]
        }
        metadata_file = self.profiles_dir / "profiles.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def add_profile_from_url(self, name: str, url: str, description: str = "", max_duration: float = 2.0) -> VoiceProfile:
        """
        Download audio from URL and create a voice profile

        Args:
            name: Profile name
            url: URL to audio file (mp3, wav, etc.)
            description: Optional description
            max_duration: Maximum duration in seconds for reference audio (default 10s)

        Returns:
            Created VoiceProfile
        """
        logger.info(f"Downloading audio from {url} for profile '{name}'...")

        # Download audio file
        temp_file = self.profiles_dir / f"{name}_temp.mp3"
        urllib.request.urlretrieve(url, temp_file)

        # Load and convert to 24kHz
        logger.info(f"Converting audio to {SAMPLE_RATE}Hz...")
        audio, sr = librosa.load(temp_file, sr=SAMPLE_RATE, mono=True)
        audio = audio.astype(np.float32)

        # Trim to max_duration if needed
        max_samples = int(max_duration * SAMPLE_RATE)
        if len(audio) > max_samples:
            logger.info(f"Trimming audio from {len(audio) / SAMPLE_RATE:.2f}s to {max_duration}s")
            audio = audio[:max_samples]

        # Clean up temp file
        temp_file.unlink()

        # Create profile
        profile = VoiceProfile(name=name, audio=audio, description=description)
        self.profiles[name] = profile

        # Save to disk
        audio_file = self.profiles_dir / f"{name}.npy"
        np.save(audio_file, audio)
        self._save_metadata()

        logger.info(f"Created voice profile '{name}' ({len(audio) / SAMPLE_RATE:.2f}s)")
        logger.info(f"Voice profile audio - shape: {audio.shape}, dtype: {audio.dtype}, samples: {len(audio)}")
        return profile

    def add_profile_from_file(self, name: str, file_path: str, description: str = "") -> VoiceProfile:
        """
        Load audio from file and create a voice profile

        Args:
            name: Profile name
            file_path: Path to audio file
            description: Optional description

        Returns:
            Created VoiceProfile
        """
        logger.info(f"Loading audio from {file_path} for profile '{name}'...")

        # Load and convert to 24kHz
        audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        audio = audio.astype(np.float32)

        # Create profile
        profile = VoiceProfile(name=name, audio=audio, description=description)
        self.profiles[name] = profile

        # Save to disk
        audio_file = self.profiles_dir / f"{name}.npy"
        np.save(audio_file, audio)
        self._save_metadata()

        logger.info(f"Created voice profile '{name}' ({len(audio) / SAMPLE_RATE:.2f}s)")
        return profile

    def get_profile(self, name: str) -> Optional[VoiceProfile]:
        """Get a voice profile by name"""
        profile = self.profiles.get(name)
        if profile:
            logger.info(f"Retrieved voice profile '{name}' - shape: {profile.audio.shape}, dtype: {profile.audio.dtype}")
        return profile

    def list_profiles(self) -> Dict[str, dict]:
        """List all available profiles"""
        return {name: profile.to_dict() for name, profile in self.profiles.items()}

    def delete_profile(self, name: str):
        """Delete a voice profile"""
        if name in self.profiles:
            del self.profiles[name]
            audio_file = self.profiles_dir / f"{name}.npy"
            if audio_file.exists():
                audio_file.unlink()
            self._save_metadata()
            logger.info(f"Deleted voice profile '{name}'")
