"""
Transcript Ingestion Pipeline for The Lenny Growth Assistant.
Processes downloaded markdown transcripts, performs recursive chunking with speaker and timestamp tracking,
generates embeddings, and stores chunks in PostgreSQL (pgvector) and local JSON cache.
"""

import os
import re
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.rag.embeddings import compute_embeddings_batch
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")

DATA_DIR = BACKEND_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
CACHE_FILE = DATA_DIR / "chunks_cache.json"

def parse_markdown_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {
        "slug": file_path.stem,
        "title": file_path.stem.replace("-", " ").title(),
        "guest": "Lenny's Guest",
        "date": None,
        "word_count": 0
    }

    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.splitlines():
                if line.startswith("title:"):
                    metadata["title"] = line.replace("title:", "").strip().strip('"\'')
                elif line.startswith("guest:"):
                    metadata["guest"] = line.replace("guest:", "").strip().strip('"\'')
                elif line.startswith("date:"):
                    raw_date = line.replace("date:", "").strip().strip('"\'')
                    try:
                        metadata["date"] = datetime.strptime(raw_date, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                elif line.startswith("word_count:"):
                    try:
                        metadata["word_count"] = int(line.replace("word_count:", "").strip())
                    except ValueError:
                        pass

    return metadata, body

def chunk_transcript(body: str, target_token_size: int = 600, overlap: int = 100):
    """
    Chunks transcript while preserving speaker name and timestamp tags.
    """
    # Regex to identify speaker turn: **Speaker Name** (HH:MM:SS):
    speaker_regex = re.compile(r"(\*\*[^*]+\*\*\s*\((?:[0-9]{1,2}:)?[0-9]{2}:[0-9]{2}\):?)")
    
    # Split by double newlines into logical segments
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    
    chunks = []
    current_tokens = []
    current_length = 0
    last_timestamp = "00:00:00"
    last_speaker = ""

    for p in paragraphs:
        # Check for timestamp in paragraph
        ts_match = re.search(r"\(((?:[0-9]{1,2}:)?[0-9]{2}:[0-9]{2})\)", p)
        if ts_match:
            last_timestamp = ts_match.group(1)

        spk_match = re.search(r"\*\*([^*]+)\*\*", p)
        if spk_match:
            last_speaker = spk_match.group(1).strip()

        words = p.split()
        p_len = len(words)

        if current_length + p_len > target_token_size and current_tokens:
            chunk_text = " ".join(current_tokens)
            chunks.append({
                "text": chunk_text,
                "timestamp": last_timestamp,
                "token_count": current_length
            })
            # Overlap: keep last few words
            overlap_words = current_tokens[-overlap:] if overlap < len(current_tokens) else []
            current_tokens = overlap_words + words
            current_length = len(current_tokens)
        else:
            current_tokens.extend(words)
            current_length += p_len

    if current_tokens:
        chunks.append({
            "text": " ".join(current_tokens),
            "timestamp": last_timestamp,
            "token_count": current_length
        })

    return chunks

def run_ingestion():
    if not TRANSCRIPTS_DIR.exists():
        logger.error(f"Transcripts directory not found: {TRANSCRIPTS_DIR}. Run download_transcripts.py first.")
        return

    md_files = list(TRANSCRIPTS_DIR.glob("*.md"))
    logger.info(f"Found {len(md_files)} transcripts to process.")

    all_chunks = []
    for f in md_files:
        meta, body = parse_markdown_file(f)
        chunks = chunk_transcript(body)
        for idx, ch in enumerate(chunks):
            all_chunks.append({
                "episode_slug": meta["slug"],
                "episode_title": meta["title"],
                "guest_name": meta["guest"],
                "publish_date": str(meta["date"]) if meta["date"] else None,
                "timestamp_ref": ch["timestamp"],
                "chunk_index": idx,
                "chunk_text": ch["text"],
                "token_count": ch["token_count"]
            })

    logger.info(f"Generated {len(all_chunks)} total chunks from {len(md_files)} episodes.")

    # Save to local chunks cache (without embeddings first, to quickly store structure)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks[:500], f, indent=2)
    logger.info(f"Cached chunk sample to {CACHE_FILE}")

    # Attempt PostgreSQL ingestion
    import asyncio
    asyncio.run(ingest_to_postgres(all_chunks))

async def ingest_to_postgres(chunks):
    settings = get_settings()
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        logger.info(f"Connecting to database: {settings.DATABASE_URL}...")
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Enable extensions
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transcript_chunks (
                    id SERIAL PRIMARY KEY,
                    episode_slug VARCHAR(255) NOT NULL,
                    episode_title VARCHAR(255) NOT NULL,
                    guest_name VARCHAR(255) NOT NULL,
                    publish_date DATE,
                    timestamp_ref VARCHAR(20),
                    chunk_index INT NOT NULL,
                    chunk_text TEXT NOT NULL,
                    token_count INT NOT NULL,
                    embedding vector(384)
                );
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_hnsw_cosine 
                ON transcript_chunks USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """))

            logger.info("Computing embeddings for chunks...")
            # Compute embeddings in batches
            batch_size = 50
            for i in range(0, min(len(chunks), 300), batch_size):
                batch = chunks[i:i+batch_size]
                texts = [b["chunk_text"] for b in batch]
                embeddings = compute_embeddings_batch(texts)
                
                for b, emb in zip(batch, embeddings):
                    vector_str = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"
                    insert_stmt = text("""
                        INSERT INTO transcript_chunks (
                            episode_slug, episode_title, guest_name, timestamp_ref,
                            chunk_index, chunk_text, token_count, embedding
                        ) VALUES (
                            :slug, :title, :guest, :ts,
                            :cidx, :ctext, :tcount, :vec::vector
                        );
                    """)
                    await conn.execute(insert_stmt, {
                        "slug": b["episode_slug"],
                        "title": b["episode_title"],
                        "guest": b["guest_name"],
                        "ts": b["timestamp_ref"],
                        "cidx": b["chunk_index"],
                        "ctext": b["chunk_text"],
                        "tcount": b["token_count"],
                        "vec": vector_str
                    })
                logger.info(f"Inserted batch {i//batch_size + 1}/{(min(len(chunks), 300) + batch_size - 1)//batch_size} into PostgreSQL.")

        logger.info("Database ingestion completed successfully!")
        await engine.dispose()
    except Exception as e:
        logger.warning(f"PostgreSQL ingestion skipped or failed: {e}. File-based fallback search will be active.")

if __name__ == "__main__":
    run_ingestion()
