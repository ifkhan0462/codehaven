from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ConversationSummary(BaseModel):
    id: str
    title: str
    mode: str
    created_at: str
    updated_at: str


class SavedMessage(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    sources: list[dict[str, Any]] | None = None
    timestamp: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    mode: str
    created_at: str
    updated_at: str
    messages: list[SavedMessage] = []


class CreateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1)
    mode: Literal["chat", "notes_qa", "exam", "codegen", "debug"] = "chat"
    id: str | None = None


class CreateMessageRequest(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    sources: list[dict[str, Any]] | None = None
    id: str | None = None


class ExamPaperRecord(BaseModel):
    id: str
    title: str
    subject: str
    difficulty: str
    total_marks: int
    duration_minutes: int
    content_markdown: str
    created_at: str


class SaveExamRequest(BaseModel):
    title: str
    subject: str
    difficulty: str
    total_marks: int
    duration_minutes: int
    content_markdown: str
    id: str | None = None
