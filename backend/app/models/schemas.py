from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SourceItem(BaseModel):
    episode: str
    guest: str
    timestamp: Optional[str] = None
    text: Optional[str] = None
    score: float

class ArtifactBase(BaseModel):
    identifier: str
    title: str
    artifact_type: str = Field(..., description="'markdown' or 'html'")
    content: str

class ArtifactResponse(ArtifactBase):
    id: UUID
    message_id: Optional[UUID] = None
    session_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: List[SourceItem] = []
    created_at: datetime
    artifacts: List[ArtifactResponse] = []
    model_config = ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    provider: Optional[str] = "ollama"

class SessionResponse(BaseModel):
    id: UUID
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    model_config = ConfigDict(from_attributes=True)

class SessionListItem(BaseModel):
    id: UUID
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str = Field(..., min_length=1)
    provider: Optional[str] = "ollama"  # "ollama" or "cloud"
    mode: Optional[str] = "default"      # "default" or "ship30"


class HealthResponse(BaseModel):
    status: str
    database: str
    pgvector: str
    chunks_indexed: int
    providers: Dict[str, Any]
