"""
Speaker management package (Phase 3).
"""
from server.speakers.registry import SpeakerRegistry
from server.speakers import embeddings

__all__ = ["SpeakerRegistry", "embeddings"]
