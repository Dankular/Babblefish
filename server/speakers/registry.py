"""
Speaker registry for tracking speakers across sessions (Phase 3).
This is a stub implementation for Phase 1.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SpeakerRegistry:
    """
    Speaker registry for tracking and matching speakers.
    Phase 3: Will implement speaker diarization and voice tracking.
    Phase 1: Stub implementation.
    """

    def __init__(self):
        self.speakers: Dict[str, dict] = {}
        logger.info("SpeakerRegistry initialized (stub)")

    def register_speaker(
        self, participant_id: str, audio_sample: bytes
    ) -> str:
        """
        Register a new speaker with their voice sample.

        Args:
            participant_id: Participant ID
            audio_sample: Audio sample for voice enrollment

        Returns:
            Speaker ID
        """
        # Phase 3: Extract speaker embedding, match against existing speakers
        # For Phase 1: Just return participant_id as speaker_id
        speaker_id = participant_id
        self.speakers[speaker_id] = {
            "participant_id": participant_id,
            "enrolled": False,
        }
        logger.debug(f"Registered speaker {speaker_id} (stub)")
        return speaker_id

    def identify_speaker(self, audio_sample: bytes) -> Optional[str]:
        """
        Identify a speaker from an audio sample.

        Args:
            audio_sample: Audio sample

        Returns:
            Speaker ID if matched, None otherwise
        """
        # Phase 3: Extract embedding, compare with registered speakers
        # For Phase 1: Return None (no identification)
        logger.debug("Speaker identification (stub) - returning None")
        return None

    def get_speaker_info(self, speaker_id: str) -> Optional[dict]:
        """Get speaker information."""
        return self.speakers.get(speaker_id)
