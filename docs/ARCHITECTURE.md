# CodeHaven — Architecture

## Overview

CodeHaven is an offline-first desktop coding assistant for students. All inference runs locally via Ollama; no code or documents leave the machine at runtime.

## Stack

| Layer | Technology |
|-------|------------|
| Desktop shell | Electron |
| UI | React + Vite + Monaco Editor |
| API | Python FastAPI (localhost:8765) |
| LLM | Ollama (`qwen2.5-coder:7b`) |
| Embeddings (Phase 4) | Ollama `nomic-embed-text` (768-dim) |
| Vector store (Phase 4) | Built-from-scratch pure Python cosine similarity + chunker |
| Persistence (Database) | Local SQLite (`codehaven.db`) via Python `sqlite3` |
| Exam Generator | University Reference Exam Paper Setter with MCQs & Marking Scheme |
| Speech (Phase 7) | faster-whisper |

## Module layout

```
backend/app/modules/
├── chat/       ✅ Phase 1 — streaming chat
├── codegen/    ✅ Phase 2 — boilerplate generation
├── debug/      ✅ Phase 3 — bug detection & fixes
├── rag/        ✅ Phase 4 & 5 — PDF/notes Q&A (RAG from scratch) & Exam Generator
├── history/    ✅ Phase 6 — persistent SQLite storage for chats, notes & exams
├── voice/      Phase 7 — push-to-talk STT
└── interview/  Phase 8 — DSA & mock interviews
```

Each module is a FastAPI router under `/api/<module>/`. The frontend calls these endpoints; modules share `core/ollama_client.py` and `core/database.py`.

## Runtime flow (Offline RAG & Exam Generator)

```
User (Upload Notes / Ask / Exam)
  → React UI (NotesPanel / ExamGeneratorPanel)
  → FastAPI /api/rag/upload or /api/rag/query or /api/rag/exam/generate
  → VectorStore (chunking, 768-dim nomic-embed-text embeddings, cosine ranking)
  → SQLite DB (persist conversation threads, citations, and generated exam papers)
  → Ollama /api/chat (qwen2.5-coder:7b stream tokens)
  → UI (real-time stream, citation cards, printable reference exam sheet)
```
