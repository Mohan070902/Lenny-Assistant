from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.db_models import ChatSession, ChatMessage, ArtifactRecord
from app.models.schemas import (
    SessionCreate,
    SessionResponse,
    SessionListItem,
    MessageResponse,
    ArtifactResponse
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    session = ChatSession(
        title=payload.title or "New Conversation",
        provider=payload.provider or "ollama"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        provider=session.provider,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[]
    )


@router.get("", response_model=List[SessionListItem])
async def list_sessions(
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            ChatSession.id,
            ChatSession.title,
            ChatSession.provider,
            ChatSession.created_at,
            ChatSession.updated_at,
            func.count(ChatMessage.id).label("message_count")
        )
        .outerjoin(ChatMessage, ChatSession.id == ChatMessage.session_id)
        .group_by(ChatSession.id)
        .order_by(desc(ChatSession.updated_at))
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        SessionListItem(
            id=r.id,
            title=r.title,
            provider=r.provider,
            created_at=r.created_at,
            updated_at=r.updated_at,
            message_count=r.message_count
        )
        for r in rows
    ]

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(
            selectinload(ChatSession.messages).selectinload(ChatMessage.artifacts),
            selectinload(ChatSession.artifacts)
        )
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return None
