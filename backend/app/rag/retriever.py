import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.rag.embeddings import compute_embedding
from app.config import get_settings
from pathlib import Path

logger = logging.getLogger("retriever")

class TranscriptRetriever:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.settings = get_settings()

    async def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        k = top_k or self.settings.TOP_K_RETRIEVAL
        threshold = similarity_threshold or self.settings.SIMILARITY_THRESHOLD
        
        # 1. Try PostgreSQL pgvector search if session is active and configured for postgres
        from app.database import active_db_url
        if self.session is not None and "postgresql" in active_db_url:
            try:

                query_vector = compute_embedding(query)
                vector_str = "[" + ",".join(f"{x:.6f}" for x in query_vector) + "]"

                stmt = text("""
                    SELECT
                        episode_title,
                        guest_name,
                        chunk_text,
                        timestamp_ref,
                        1 - (embedding <=> :vector::vector) AS similarity_score
                    FROM transcript_chunks
                    WHERE 1 - (embedding <=> :vector::vector) >= :threshold
                    ORDER BY similarity_score DESC
                    LIMIT :limit;
                """)

                result = await self.session.execute(
                    stmt,
                    {
                        "vector": vector_str,
                        "threshold": threshold,
                        "limit": k
                    }
                )

                rows = result.fetchall()
                if rows:
                    return [
                        {
                            "episode": r.episode_title,
                            "guest": r.guest_name,
                            "text": r.chunk_text,
                            "timestamp": r.timestamp_ref,
                            "score": float(r.similarity_score)
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.warning(f"Database pgvector query failed or table empty: {e}. Falling back to file search.")

        # 2. File-based fallback search from backend/data/transcripts/
        return self._fallback_file_search(query, k)

    def _fallback_file_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        transcripts_dir = Path(__file__).resolve().parent.parent.parent / "data" / "transcripts"
        if not transcripts_dir.exists():
            return []

        query_terms = [t.lower() for t in query.split() if len(t) > 3]
        if not query_terms:
            query_terms = [t.lower() for t in query.split()]

        results = []
        for file_path in transcripts_dir.glob("*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse frontmatter
                title = file_path.stem.replace("-", " ").title()
                guest = "Lenny's Guest"
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        for line in parts[1].splitlines():
                            if line.startswith("title:"):
                                title = line.replace("title:", "").strip().strip('"')
                            elif line.startswith("guest:"):
                                guest = line.replace("guest:", "").strip().strip('"')
                        body = parts[2]
                    else:
                        body = content
                else:
                    body = content

                # Paragraph-level scoring
                paragraphs = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 100]
                for p in paragraphs:
                    p_lower = p.lower()
                    matches = sum(1 for term in query_terms if term in p_lower)
                    if matches > 0:
                        score = min(0.95, 0.50 + (matches * 0.15))
                        # Extract timestamp if present (e.g., (00:14:22))
                        import re
                        ts_match = re.search(r"\((?:[0-9]{1,2}:)?[0-9]{2}:[0-9]{2}\)", p)
                        timestamp = ts_match.group(0).strip("()") if ts_match else "00:00"
                        results.append({
                            "episode": title,
                            "guest": guest,
                            "text": p[:800],
                            "timestamp": timestamp,
                            "score": round(score, 3)
                        })
            except Exception as e:
                logger.debug(f"Error reading {file_path}: {e}")

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
