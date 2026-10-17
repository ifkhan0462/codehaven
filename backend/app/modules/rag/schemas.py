from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    chunk_count: int
    char_count: int
    created_at: str


class SourceChunk(BaseModel):
    doc_id: str
    filename: str
    chunk_index: int
    similarity: float
    text: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    doc_id: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)
    model: str | None = None
    stream: bool = True


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    model: str


class ExamQuestionType(BaseModel):
    type: Literal["mcq", "short", "long"]
    count: int = 3
    marks_per_question: int = 5


class ExamGenerateRequest(BaseModel):
    title: str = "College Reference Examination Paper"
    subject: str = "Computer Science & Engineering"
    doc_ids: list[str] | None = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    total_marks: int = 50
    duration_minutes: int = 90
    include_solutions: bool = True
    model: str | None = None
    stream: bool = True


class ExamPaperResponse(BaseModel):
    title: str
    subject: str
    difficulty: str
    total_marks: int
    duration_minutes: int
    content: str
    model: str
