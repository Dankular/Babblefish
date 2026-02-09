"""
WebSocket protocol message schemas for Babblefish.
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


# Client → Server Messages


class JoinMessage(BaseModel):
    """Client joining a room."""

    type: Literal["join"]
    room_id: str
    language: str  # ISO 639-1 code
    name: str
    capabilities: Optional[Dict[str, Any]] = None  # Phase 2/3: client capabilities
    voice_reference: Optional[Dict[str, Any]] = None  # Phase 3: voice reference data


class AudioMessage(BaseModel):
    """Audio chunk from client."""

    type: Literal["audio"]
    data: str  # Base64-encoded Opus audio
    timestamp: int


class UtteranceEndMessage(BaseModel):
    """Client VAD detected end of utterance."""

    type: Literal["utterance_end"]
    timestamp: int


class LeaveMessage(BaseModel):
    """Client leaving room."""

    type: Literal["leave"]


class EnrolMessage(BaseModel):
    """Speaker enrollment audio (Phase 3)."""

    type: Literal["enrol"]
    audio: str  # Base64-encoded PCM audio (15s, 16kHz mono)


class VoiceReferenceMessage(BaseModel):
    """Voice reference from client (Phase 3)."""

    type: Literal["voice_reference"]
    speaker_id: str
    voice_data: str  # Base64-encoded audio
    sample_rate: int
    timestamp: int


# Server → Client Messages


class JoinedMessage(BaseModel):
    """Confirmation that client joined room."""

    type: Literal["joined"] = "joined"
    room_id: str
    participant_id: str
    participants: List[Dict[str, Any]]
    tts_mode: str = "text_only"  # Phase 2/3: assigned TTS mode
    tts_model: Optional[str] = None  # Phase 2/3: assigned TTS model


class TranslationMessage(BaseModel):
    """Translation result broadcast to room."""

    type: Literal["translation"] = "translation"
    speaker_id: str
    speaker_name: str
    source_lang: str
    source_text: str
    translations: Dict[str, str]  # {language: translated_text}
    timestamp: float
    audio: Optional[str] = None  # Phase 2/3: Base64 Opus audio (for server TTS clients)


class ParticipantJoinedMessage(BaseModel):
    """Notification that another participant joined."""

    type: Literal["participant_joined"] = "participant_joined"
    participant: Dict[str, Any]


class ParticipantLeftMessage(BaseModel):
    """Notification that a participant left."""

    type: Literal["participant_left"] = "participant_left"
    participant_id: str


class SpeakerEnrolledMessage(BaseModel):
    """New speaker enrolled (Phase 3)."""

    type: Literal["speaker_enrolled"] = "speaker_enrolled"
    participant_id: str
    name: str
    language: str
    reference_audio: str  # Base64 PCM (~200KB for 15s @ 16kHz)
    reference_text: str  # Whisper transcription


class VoiceReferenceBroadcastMessage(BaseModel):
    """Broadcast voice reference to room participants (Phase 3)."""

    type: Literal["voice_reference_broadcast"] = "voice_reference_broadcast"
    speaker_id: str
    speaker_name: str
    voice_data: str  # Base64-encoded audio
    sample_rate: int
    timestamp: float


class ErrorMessage(BaseModel):
    """Error message to client."""

    type: Literal["error"] = "error"
    code: str
    message: str
