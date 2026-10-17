from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings

DB_PATH: Path = settings.data_dir / "codehaven.db"


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exam_papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_marks INTEGER NOT NULL,
                duration_minutes INTEGER NOT NULL,
                content_markdown TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_conv_mode ON conversations(mode);
            """)

    # --- Conversation Operations ---

    def create_conversation(self, title: str, mode: str, conv_id: str | None = None) -> dict[str, Any]:
        cid = conv_id or str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (cid, title, mode, now, now),
            )
        return {
            "id": cid,
            "title": title,
            "mode": mode,
            "created_at": now,
            "updated_at": now,
        }

    def get_conversations(self, mode: str | None = None) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            if mode:
                rows = conn.execute(
                    "SELECT * FROM conversations WHERE mode = ? ORDER BY updated_at DESC",
                    (mode,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM conversations ORDER BY updated_at DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    def get_conversation(self, conv_id: str) -> dict[str, Any] | None:
        with self.get_connection() as conn:
            conv_row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conv_id,)
            ).fetchone()
            if not conv_row:
                return None

            msg_rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conv_id,),
            ).fetchall()

            messages = []
            for m in msg_rows:
                msg_dict = dict(m)
                if msg_dict.get("sources"):
                    try:
                        msg_dict["sources"] = json.loads(msg_dict["sources"])
                    except Exception:
                        msg_dict["sources"] = None
                messages.append(msg_dict)

            res = dict(conv_row)
            res["messages"] = messages
            return res

    def update_conversation_title(self, conv_id: str, title: str) -> bool:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conv_id),
            )
            return cur.rowcount > 0

    def delete_conversation(self, conv_id: str) -> bool:
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            return cur.rowcount > 0

    # --- Message Operations ---

    def add_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        sources: Any | None = None,
        msg_id: str | None = None,
    ) -> dict[str, Any]:
        mid = msg_id or str(uuid.uuid4())
        now = datetime.now().isoformat()
        sources_json = json.dumps(sources) if sources is not None else None

        with self.get_connection() as conn:
            # Touch conversation updated_at
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conv_id),
            )
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, sources, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (mid, conv_id, role, content, sources_json, now),
            )

        return {
            "id": mid,
            "conversation_id": conv_id,
            "role": role,
            "content": content,
            "sources": sources,
            "timestamp": now,
        }

    # --- Exam Operations ---

    def save_exam_paper(
        self,
        title: str,
        subject: str,
        difficulty: str,
        total_marks: int,
        duration_minutes: int,
        content_markdown: str,
        exam_id: str | None = None,
    ) -> dict[str, Any]:
        eid = exam_id or str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO exam_papers 
                (id, title, subject, difficulty, total_marks, duration_minutes, content_markdown, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (eid, title, subject, difficulty, total_marks, duration_minutes, content_markdown, now),
            )
        return {
            "id": eid,
            "title": title,
            "subject": subject,
            "difficulty": difficulty,
            "total_marks": total_marks,
            "duration_minutes": duration_minutes,
            "content_markdown": content_markdown,
            "created_at": now,
        }

    def get_exam_papers(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM exam_papers ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def get_exam_paper(self, exam_id: str) -> dict[str, Any] | None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM exam_papers WHERE id = ?", (exam_id,)).fetchone()
        return dict(row) if row else None

    def delete_exam_paper(self, exam_id: str) -> bool:
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM exam_papers WHERE id = ?", (exam_id,))
            return cur.rowcount > 0


db = Database()
