import logging
import math
import hashlib
from typing import List

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

logger = logging.getLogger("embeddings")

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import get_settings
            settings = get_settings()
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Using deterministic fallback embedder.")
            _model = "fallback"
    return _model

def compute_embedding(text: str) -> List[float]:
    """Compute a 384-dimensional normalized vector for a single text."""
    model = get_embedding_model()
    if model != "fallback":
        try:
            vec = model.encode(text, normalize_embeddings=True)
            return vec.tolist() if hasattr(vec, "tolist") else list(vec)
        except Exception as e:
            logger.error(f"Error computing embedding with SentenceTransformer: {e}")
    
    # Deterministic 384-dimensional pseudo-embedding fallback in pure Python
    vec = [0.0] * 384
    words = text.lower().split()
    for word in words:
        h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
        idx = h % 384
        val = ((h >> 8) % 1000) / 500.0 - 1.0
        vec[idx] += val
    
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def compute_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Compute 384-dimensional normalized vectors for a batch of texts."""
    model = get_embedding_model()
    if model != "fallback":
        try:
            vectors = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
            return vectors.tolist()
        except Exception as e:
            logger.error(f"Error computing batch embeddings with SentenceTransformer: {e}")

    return [compute_embedding(t) for t in texts]
