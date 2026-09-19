import pytest
import math
from app.rag.embeddings import compute_embedding, compute_embeddings_batch
from app.rag.retriever import TranscriptRetriever

def test_compute_embedding_dimension_and_norm():
    text = "Product-market fit requires 40 percent very disappointed users."
    vec = compute_embedding(text)
    
    assert len(vec) == 384
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-4

def test_batch_embeddings():
    texts = ["Growth loops exceed linear funnels.", "Retention is the king of metrics."]
    batch = compute_embeddings_batch(texts)

    assert len(batch) == 2
    assert len(batch[0]) == 384
    assert len(batch[1]) == 384

@pytest.mark.asyncio
async def test_fallback_file_retriever():
    retriever = TranscriptRetriever(session=None)
    results = await retriever.retrieve_relevant_chunks("authenticity and taste in AI product work", top_k=3)

    assert isinstance(results, list)
    if results:
        top = results[0]
        assert "episode" in top
        assert "guest" in top
        assert "text" in top
        assert "score" in top
        assert top["score"] > 0
