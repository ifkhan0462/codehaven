from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.ollama_client import ollama_client
from app.modules.chat.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "You are CodeHaven, a helpful offline coding assistant for students. "
    "You specialize in Python and JavaScript (React, Node.js). "
    "Give clear, practical answers with code examples when useful. "
    "If you are unsure, say so instead of inventing APIs."
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse | StreamingResponse:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(m.model_dump() for m in request.messages)

    model = request.model or settings.chat_model

    if request.stream:
        async def event_stream():
            try:
                async for token in ollama_client.chat_stream(messages, model=model):
                    yield token
            except Exception as exc:
                yield f"\n\n[Error: {exc}]"

        return StreamingResponse(event_stream(), media_type="text/plain")

    try:
        content = await ollama_client.chat(messages, model=model)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {exc}") from exc

    return ChatResponse(content=content, model=model)
