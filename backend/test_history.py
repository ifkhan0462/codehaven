import asyncio
import httpx
from app.main import app

async def run_history_tests():
    print("=== Testing CodeHaven SQLite History Backend ===")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Create a conversation
        conv_payload = {"title": "Binary Trees Discussion", "mode": "chat"}
        r = await client.post("/api/history/conversations", json=conv_payload)
        assert r.status_code == 200, f"Create conv failed: {r.text}"
        conv = r.json()
        conv_id = conv["id"]
        print(f"[PASS] Created conversation: {conv['title']} (ID: {conv_id})")

        # 2. Add user and assistant messages
        msg1 = {"role": "user", "content": "How do I invert a binary tree in Python?"}
        r = await client.post(f"/api/history/conversations/{conv_id}/messages", json=msg1)
        assert r.status_code == 200
        print("[PASS] Added user message to conversation.")

        msg2 = {
            "role": "assistant",
            "content": "To invert a binary tree, swap left and right pointers recursively.",
            "sources": [{"filename": "trees.txt", "chunk_index": 1, "similarity": 0.89}],
        }
        r = await client.post(f"/api/history/conversations/{conv_id}/messages", json=msg2)
        assert r.status_code == 200
        print("[PASS] Added assistant message with sources to conversation.")

        # 3. Retrieve conversation detail
        r = await client.get(f"/api/history/conversations/{conv_id}")
        assert r.status_code == 200
        data = r.json()
        assert len(data["messages"]) == 2
        assert data["messages"][1]["sources"][0]["filename"] == "trees.txt"
        print(f"[PASS] Retrieved conversation with {len(data['messages'])} messages and parsed sources.")

        # 4. List conversations
        r = await client.get("/api/history/conversations?mode=chat")
        assert r.status_code == 200
        assert any(c["id"] == conv_id for c in r.json())
        print(f"[PASS] Listed conversations filtered by mode=chat: {len(r.json())} items found.")

        # 5. Save and retrieve an exam paper
        exam_payload = {
            "title": "Semester Examination 2026",
            "subject": "Data Structures",
            "difficulty": "medium",
            "total_marks": 50,
            "duration_minutes": 90,
            "content_markdown": "# Semester Exam\n\n### SECTION A\n1. What is BFS? [2 Marks]",
        }
        r = await client.post("/api/history/exams", json=exam_payload)
        assert r.status_code == 200
        exam_id = r.json()["id"]
        print(f"[PASS] Saved exam paper: {exam_payload['title']} (ID: {exam_id})")

        # List exams
        r = await client.get("/api/history/exams")
        assert r.status_code == 200
        assert any(e["id"] == exam_id for e in r.json())
        print(f"[PASS] Listed saved exams: {len(r.json())} paper(s) found.")

        # 6. Delete conversation and exam
        r = await client.delete(f"/api/history/conversations/{conv_id}")
        assert r.status_code == 200
        r = await client.delete(f"/api/history/exams/{exam_id}")
        assert r.status_code == 200
        print("[PASS] Successfully deleted test conversation and exam paper.")

    print("\nALL SQLITE HISTORY TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_history_tests())
