import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Date,
    JSON,
    Uuid
)
from sqlalchemy.orm import relationship
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    Vector = None

class ChatSession(Base):
    __tablename__ = "sessions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, default="New Conversation")
    provider = Column(String(50), nullable=False, default="ollama")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at", lazy="selectin")
    artifacts = relationship("ArtifactRecord", back_populates="session", cascade="all, delete-orphan", order_by="ArtifactRecord.created_at", lazy="selectin")

class ChatMessage(Base):
    __tablename__ = "messages"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages", lazy="selectin")
    artifacts = relationship("ArtifactRecord", back_populates="message", cascade="all, delete-orphan", lazy="selectin")

class ArtifactRecord(Base):
    __tablename__ = "artifacts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Uuid, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    identifier = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    artifact_type = Column(String(20), nullable=False)  # markdown, html
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="artifacts", lazy="selectin")
    message = relationship("ChatMessage", back_populates="artifacts", lazy="selectin")


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_slug = Column(String(255), nullable=False)
    episode_title = Column(String(255), nullable=False)
    guest_name = Column(String(255), nullable=False)
    publish_date = Column(Date, nullable=True)
    timestamp_ref = Column(String(20), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)

    if VECTOR_AVAILABLE:
        embedding = Column(Vector(384), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)
