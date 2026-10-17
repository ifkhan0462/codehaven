from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.database import db
from app.modules.history.schemas import (
    ConversationDetail,
    ConversationSummary,
    CreateConversationRequest,
    CreateMessageRequest,
    ExamPaperRecord,
    SaveExamRequest,
    SavedMessage,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(mode: str | None = None) -> list[ConversationSummary]:
    items = db.get_conversations(mode=mode)
    return [ConversationSummary(**item) for item in items]


@router.get("/conversations/{conv_id}", response_model=ConversationDetail)
async def get_conversation(conv_id: str) -> ConversationDetail:
    item = db.get_conversation(conv_id)
    if not item:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ConversationDetail(**item)


@router.post("/conversations", response_model=ConversationSummary)
async def create_conversation(req: CreateConversationRequest) -> ConversationSummary:
    item = db.create_conversation(title=req.title, mode=req.mode, conv_id=req.id)
    return ConversationSummary(**item)


@router.post("/conversations/{conv_id}/messages", response_model=SavedMessage)
async def add_message(conv_id: str, req: CreateMessageRequest) -> SavedMessage:
    conv = db.get_conversation(conv_id)
    if not conv:
        # Auto-create conversation if not exists
        title = req.content[:40] + ("..." if len(req.content) > 40 else "")
        db.create_conversation(title=title, mode="chat", conv_id=conv_id)

    item = db.add_message(
        conv_id=conv_id,
        role=req.role,
        content=req.content,
        sources=req.sources,
        msg_id=req.id,
    )
    return SavedMessage(**item)


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str) -> dict[str, bool]:
    success = db.delete_conversation(conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True}


@router.get("/exams", response_model=list[ExamPaperRecord])
async def list_exam_papers() -> list[ExamPaperRecord]:
    items = db.get_exam_papers()
    return [ExamPaperRecord(**item) for item in items]


@router.get("/exams/{exam_id}", response_model=ExamPaperRecord)
async def get_exam_paper(exam_id: str) -> ExamPaperRecord:
    item = db.get_exam_paper(exam_id)
    if not item:
        raise HTTPException(status_code=404, detail="Exam paper not found.")
    return ExamPaperRecord(**item)


@router.post("/exams", response_model=ExamPaperRecord)
async def save_exam_paper(req: SaveExamRequest) -> ExamPaperRecord:
    item = db.save_exam_paper(
        title=req.title,
        subject=req.subject,
        difficulty=req.difficulty,
        total_marks=req.total_marks,
        duration_minutes=req.duration_minutes,
        content_markdown=req.content_markdown,
        exam_id=req.id,
    )
    return ExamPaperRecord(**item)


@router.delete("/exams/{exam_id}")
async def delete_exam_paper(exam_id: str) -> dict[str, bool]:
    success = db.delete_exam_paper(exam_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exam paper not found.")
    return {"success": True}
