"""
Room state management for Babblefish.
"""
import time
import logging
from typing import Dict, List, Optional, Set
from server.rooms.participant import Participant

logger = logging.getLogger(__name__)


class Room:
    """
    Represents a Babblefish translation room.
    Manages participants and message broadcasting.
    """

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.participants: Dict[str, Participant] = {}
        self.created_at = time.time()
        self.last_activity = time.time()

    async def add_participant(self, participant: Participant) -> None:
        """
        Add a participant to the room.

        Args:
            participant: Participant to add

        Raises:
            ValueError: If participant ID already exists
        """
        if participant.participant_id in self.participants:
            raise ValueError(f"Participant {participant.participant_id} already in room")

        self.participants[participant.participant_id] = participant
        self.last_activity = time.time()

        logger.info(
            f"Participant {participant.name} ({participant.participant_id}) "
            f"joined room {self.room_id} (language: {participant.language})"
        )

        # Notify other participants
        await self.broadcast(
            {
                "type": "participant_joined",
                "participant": participant.to_dict(),
            },
            exclude=participant.participant_id,
        )

    async def remove_participant(self, participant_id: str) -> None:
        """
        Remove a participant from the room.

        Args:
            participant_id: ID of participant to remove
        """
        if participant_id in self.participants:
            participant = self.participants[participant_id]
            del self.participants[participant_id]
            self.last_activity = time.time()

            logger.info(
                f"Participant {participant.name} ({participant_id}) "
                f"left room {self.room_id}"
            )

            # Notify remaining participants
            await self.broadcast(
                {
                    "type": "participant_left",
                    "participant_id": participant_id,
                }
            )

    async def broadcast(
        self, message: Dict, exclude: Optional[str] = None
    ) -> None:
        """
        Broadcast a message to all participants in the room.

        Args:
            message: Message dictionary to send
            exclude: Optional participant ID to exclude from broadcast
        """
        for pid, participant in self.participants.items():
            if pid != exclude:
                try:
                    await participant.websocket.send_json(message)
                except Exception as e:
                    logger.error(
                        f"Error sending message to participant {pid}: {e}"
                    )

    def get_participant(self, participant_id: str) -> Optional[Participant]:
        """Get a participant by ID."""
        return self.participants.get(participant_id)

    def get_other_participants(self, participant_id: str) -> List[Participant]:
        """Get all participants except the specified one."""
        return [
            p for pid, p in self.participants.items() if pid != participant_id
        ]

    def get_target_languages(self, exclude: Optional[str] = None) -> List[str]:
        """
        Get list of unique target languages in the room.

        Args:
            exclude: Optional participant ID to exclude

        Returns:
            List of ISO 639-1 language codes
        """
        langs: Set[str] = set()
        for pid, participant in self.participants.items():
            if pid != exclude:
                langs.add(participant.language)
        return list(langs)

    def get_participant_count(self) -> int:
        """Get the number of participants in the room."""
        return len(self.participants)

    def is_empty(self) -> bool:
        """Check if the room has no participants."""
        return len(self.participants) == 0

    def get_age_seconds(self) -> float:
        """Get the age of the room in seconds."""
        return time.time() - self.created_at

    def get_idle_time_seconds(self) -> float:
        """Get the time since last activity in seconds."""
        return time.time() - self.last_activity

    def __repr__(self) -> str:
        return (
            f"Room(id={self.room_id}, "
            f"participants={self.get_participant_count()}, "
            f"age={self.get_age_seconds():.0f}s)"
        )
