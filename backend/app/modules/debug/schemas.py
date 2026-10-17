from enum import Enum

from pydantic import BaseModel, Field


class CodeLanguage(str, Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    react = "react"


class DebugRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=16000)
    error_message: str | None = Field(None, max_length=8000)
    language: CodeLanguage = CodeLanguage.python
    stream: bool = True
    model: str | None = None


class DebugResponse(BaseModel):
    diagnosis: str
    explanation: str
    fixed_code: str
    language: str
    model: str
