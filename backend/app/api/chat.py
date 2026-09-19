import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, AsyncSessionLocal
from app.models.db_models import ChatSession, ChatMessage, ArtifactRecord
from app.models.schemas import ChatRequest, SourceItem
from app.rag.retriever import TranscriptRetriever
from app.providers.factory import get_llm_provider
from app.skills.ship30_writer import build_ship30_prompt
from app.skills.artifact_generator import ARTIFACT_SYSTEM_INSTRUCTION, extract_artifacts

logger = logging.getLogger("chat_api")
router = APIRouter(prefix="/chat", tags=["Chat"])

DEFAULT_SYSTEM_PROMPT = """You are "The Lenny Growth Assistant", an authoritative AI advisor built strictly on the wisdom of Lenny's Podcast transcripts.

Your mission is to provide high-impact, actionable guidance for product managers, growth leaders, and founders.

### Non-Negotiable Grounding Rules:
1. Ground every claim and framework directly in the provided context from Lenny's Podcast guests.
2. Provide exact source attribution citations throughout your response in this exact format:
   `[Episode: <Episode Title> (Guest: <Guest Name>), Time: <Timestamp>]`
3. If the retrieved context does not contain enough information to answer the question, do NOT hallucinate or guess. State clearly:
   "I do not have sufficient information in Lenny's podcast archive to answer this question. Lenny's guests have not extensively covered this topic in the available transcripts."
4. Be structured, concise, and direct. Avoid fluff and corporate jargon.

""" + ARTIFACT_SYSTEM_INSTRUCTION

@router.post("")
async def stream_chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # Verify session exists or create on the fly
    session = None
    if req.session_id:
        stmt = select(ChatSession).where(ChatSession.id == req.session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

    if not session:
        session = ChatSession(
            id=req.session_id or uuid.uuid4(),
            title=req.message[:40] + ("..." if len(req.message) > 40 else ""),
            provider=req.provider or "ollama"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        req.session_id = session.id
    elif session.title == "New Conversation":
        session.title = req.message[:40] + ("..." if len(req.message) > 40 else "")
        await db.commit()


    retriever = TranscriptRetriever(session=db)
    llm = get_llm_provider(req.provider)

    async def event_stream():
        full_response_text = ""
        retrieved_sources = []

        try:
            # 1. Yield initial status
            yield f"data: {json.dumps({'type': 'status', 'content': 'Searching Lenny\'s podcast archive...'})}\n\n"

            # 2. Retrieve relevant transcripts
            chunks = await retriever.retrieve_relevant_chunks(req.message)
            retrieved_sources = [
                {
                    "episode": c["episode"],
                    "guest": c["guest"],
                    "timestamp": c.get("timestamp", "00:00"),
                    "score": c["score"],
                    "text": c["text"][:250] + "..."
                }
                for c in chunks
            ]

            # 3. Emit sources payload to client
            yield f"data: {json.dumps({'type': 'sources', 'sources': retrieved_sources})}\n\n"

            # 4. Construct prompt based on mode
            if req.mode == "ship30":
                yield f"data: {json.dumps({'type': 'status', 'content': 'Synthesizing Ship 30 for 30 essay...'})}\n\n"
                system_prompt = build_ship30_prompt(req.message, chunks)
                messages = [{"role": "user", "content": req.message}]
            else:
                context_str = "\n\n".join([
                    f"--- Episode: {c['episode']} (Guest: {c['guest']}, Time: {c.get('timestamp', '00:00')}) ---\n{c['text']}"
                    for c in chunks
                ]) if chunks else "No relevant transcripts found."

                system_prompt = DEFAULT_SYSTEM_PROMPT + f"\n\n### Retrieved Transcript Context:\n{context_str}"
                messages = [{"role": "user", "content": req.message}]

            # 5. Stream LLM tokens
            async for token in llm.generate_response(messages, system_prompt):
                full_response_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 6. Extract any generated artifacts
            cleaned_text, artifacts = extract_artifacts(full_response_text)
            for art in artifacts:
                yield f"data: {json.dumps({'type': 'artifact', 'artifact': art.model_dump()})}\n\n"

            # 7. Persist messages and artifacts asynchronously in a fresh session
            try:
                async with AsyncSessionLocal() as persist_db:
                    user_msg = ChatMessage(
                        session_id=req.session_id,
                        role="user",
                        content=req.message
                    )
                    persist_db.add(user_msg)
                    await persist_db.flush()

                    asst_msg = ChatMessage(
                        session_id=req.session_id,
                        role="assistant",
                        content=full_response_text,
                        sources=retrieved_sources
                    )
                    persist_db.add(asst_msg)
                    await persist_db.flush()

                    for art in artifacts:
                        record = ArtifactRecord(
                            session_id=req.session_id,
                            message_id=asst_msg.id,
                            identifier=art.identifier,
                            title=art.title,
                            artifact_type=art.artifact_type,
                            content=art.content
                        )
                        persist_db.add(record)

                    # Touch session updated_at
                    sess_res = await persist_db.execute(select(ChatSession).where(ChatSession.id == req.session_id))
                    active_sess = sess_res.scalar_one_or_none()
                    if active_sess:
                        active_sess.provider = req.provider or active_sess.provider

                    await persist_db.commit()
            except Exception as pe:
                logger.error(f"Error persisting chat messages: {pe}")

        except Exception as e:
            logger.error(f"Chat streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
