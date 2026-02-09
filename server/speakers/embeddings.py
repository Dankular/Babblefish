"""
Speaker embedding extraction (Phase 3).
This is a stub implementation for Phase 1.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)


def extract_embedding(audio: np.ndarray) -> np.ndarray:
    """
    Extract speaker embedding from audio.

    Args:
        audio: Audio data as numpy array

    Returns:
        Speaker embedding vector

    Phase 3: Will use ECAPA-TDNN or similar model
    Phase 1: Stub returning zero vector
    """
    logger.debug("Extracting speaker embedding (stub)")
    # Return zero embedding for Phase 1
    return np.zeros(192, dtype=np.float32)


def compare_embeddings(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compare two speaker embeddings.

    Args:
        emb1: First embedding
        emb2: Second embedding

    Returns:
        Similarity score (0-1)

    Phase 3: Will use cosine similarity or distance metric
    Phase 1: Stub returning 0.0
    """
    logger.debug("Comparing speaker embeddings (stub)")
    return 0.0
