"""
Participant model for Babblefish rooms.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from fastapi import WebSocket


@dataclass
class ClientCapabilities:
    """Client device capabilities for adaptive TTS routing (Phase 2/3)."""

    webgpu: bool = False
    gpu_adapter: Optional[str] = None
    vram_estimate: int = 0  # MB
    wasm: bool = True
    max_model_size: str = "small"  # "small", "medium", "large"
    preferred_mode: str = "text_only"  # "local_tts", "server_tts", "text_only"

    @classmethod
    from_dict(cls, data: Dict[str, Any]) -> "ClientCapabilities":
        """Create from dictionary (from client message)."""
        return cls(
            webgpu=data.get("webgpu", False),
            gpu_adapter=data.get("gpu_adapter"),
            vram_estimate=data.get("vram_estimate", 0),
            wasm=data.get("wasm", True),
            max_model_size=data.get("max_model_size", "small"),
            preferred_mode=data.get("preferred_mode", "text_only"),
        )


@dataclass
class Participant:
    """Represents a participant in a Babblefish room."""

    participant_id: str
    name: str
    language: str  # ISO 639-1 code (target language)
    websocket: WebSocket
    joined_at: float
    speaker_id: Optional[str] = None  # For Phase 3 (speaker diarization)
    capabilities: ClientCapabilities = field(default_factory=ClientCapabilities)
    tts_mode: str = "text_only"  # "local", "server", "text_only"
    tts_model: Optional[str] = None  # "f5-tts", "kokoro", None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.participant_id,
            "name": self.name,
            "language": self.language,
            "speaker_id": self.speaker_id,
            "tts_mode": self.tts_mode,
            "tts_model": self.tts_model,
        }
