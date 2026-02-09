"""
Room manager for Babblefish.
Global singleton managing all active rooms.
"""
import secrets
import logging
from typing import Dict, Optional
from server.rooms.room import Room
from server.config import settings

logger = logging.getLogger(__name__)


class RoomManager:
    """
    Global room manager.
    Handles room creation, retrieval, and cleanup.
    """

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._room_id_length = 6

    def create_room(self, room_id: Optional[str] = None) -> Room:
        """
        Create a new room.

        Args:
            room_id: Optional room ID. If not provided, generates random ID.

        Returns:
            Created Room instance

        Raises:
            ValueError: If room limit exceeded or room ID already exists
        """
        if len(self.rooms) >= settings.MAX_ROOMS:
            raise ValueError(f"Maximum number of rooms ({settings.MAX_ROOMS}) reached")

        if room_id is None:
            room_id = self._generate_room_id()
        elif room_id in self.rooms:
            raise ValueError(f"Room {room_id} already exists")

        room = Room(room_id)
        self.rooms[room_id] = room

        logger.info(f"Created room {room_id}")
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        """
        Get a room by ID.

        Args:
            room_id: Room ID to retrieve

        Returns:
            Room instance if found, None otherwise
        """
        return self.rooms.get(room_id)

    def get_or_create_room(self, room_id: str) -> Room:
        """
        Get an existing room or create it if it doesn't exist.

        Args:
            room_id: Room ID

        Returns:
            Room instance
        """
        room = self.get_room(room_id)
        if room is None:
            room = self.create_room(room_id)
        return room

    def delete_room(self, room_id: str) -> bool:
        """
        Delete a room.

        Args:
            room_id: Room ID to delete

        Returns:
            True if room was deleted, False if not found
        """
        if room_id in self.rooms:
            del self.rooms[room_id]
            logger.info(f"Deleted room {room_id}")
            return True
        return False

    def cleanup_empty_rooms(self) -> int:
        """
        Remove all empty rooms.

        Returns:
            Number of rooms deleted
        """
        empty_rooms = [
            room_id for room_id, room in self.rooms.items() if room.is_empty()
        ]
        for room_id in empty_rooms:
            self.delete_room(room_id)
        return len(empty_rooms)

    def cleanup_idle_rooms(self, max_idle_seconds: Optional[int] = None) -> int:
        """
        Remove rooms that have been idle for too long.

        Args:
            max_idle_seconds: Maximum idle time. Defaults to settings.ROOM_TIMEOUT_SECONDS

        Returns:
            Number of rooms deleted
        """
        if max_idle_seconds is None:
            max_idle_seconds = settings.ROOM_TIMEOUT_SECONDS

        idle_rooms = [
            room_id
            for room_id, room in self.rooms.items()
            if room.get_idle_time_seconds() > max_idle_seconds
        ]
        for room_id in idle_rooms:
            logger.info(
                f"Cleaning up idle room {room_id} "
                f"(idle for {self.rooms[room_id].get_idle_time_seconds():.0f}s)"
            )
            self.delete_room(room_id)
        return len(idle_rooms)

    def get_room_count(self) -> int:
        """Get the total number of active rooms."""
        return len(self.rooms)

    def get_total_participants(self) -> int:
        """Get the total number of participants across all rooms."""
        return sum(room.get_participant_count() for room in self.rooms.values())

    def _generate_room_id(self) -> str:
        """
        Generate a unique random room ID.

        Returns:
            6-character uppercase alphanumeric room ID
        """
        while True:
            # Generate random alphanumeric ID
            room_id = secrets.token_urlsafe(self._room_id_length)[:self._room_id_length].upper()
            # Ensure it doesn't exist
            if room_id not in self.rooms:
                return room_id

    def __repr__(self) -> str:
        return (
            f"RoomManager(rooms={self.get_room_count()}, "
            f"participants={self.get_total_participants()})"
        )
