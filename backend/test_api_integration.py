import asyncio
import httpx
from app.main import app

async def run_integration_tests():
    print("=== Testing CodeHaven FastAPI Endpoints (In-Memory ASGI) ===")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        res = await client.get("/api/health")
        print(f"[PASS] GET /api/health -> Status: {res.status_code}")
        assert res.status_code == 200
        health_data = res.json()
        print(f"       App: {health_data['app']}, Ollama reachable: {health_data['ollama'].get('reachable')}")

        # 2. RAG status
        res = await client.get("/api/rag/status")
        print(f"[PASS] GET /api/rag/status -> Status: {res.status_code}, data: {res.json()}")
        assert res.status_code == 200

        # 3. Upload a sample document
        sample_doc_content = (
            "Subject: Operating Systems\n\n"
            "Chapter 1: Process Management\n"
            "A process is a program in execution. The Process Control Block (PCB) contains process state, "
            "program counter, CPU registers, and scheduling information.\n\n"
            "Chapter 2: Deadlocks\n"
            "Four Coffman conditions must hold simultaneously for a deadlock to occur: "
            "1. Mutual Exclusion, 2. Hold and Wait, 3. No Preemption, 4. Circular Wait.\n"
            "Banker's Algorithm is used for deadlock avoidance using Resource-Allocation Graphs.\n\n"
            "Chapter 3: Virtual Memory\n"
            "Paging allows physical address space of a process to be non-contiguous. "
            "Page Fault occurs when a referenced page is not present in main memory."
        )

        files = {"file": ("operating_systems_notes.txt", sample_doc_content.encode("utf-8"), "text/plain")}
        res = await client.post("/api/rag/upload", files=files)
        print(f"[PASS] POST /api/rag/upload -> Status: {res.status_code}")
        assert res.status_code == 200
        doc_data = res.json()
        doc_id = doc_data["id"]
        print(f"       Uploaded doc ID: {doc_id}, chunks: {doc_data['chunk_count']}")

        # 4. List documents
        res = await client.get("/api/rag/documents")
        print(f"[PASS] GET /api/rag/documents -> Found {len(res.json())} document(s)")
        assert any(d["id"] == doc_id for d in res.json())

        # 5. Semantic Search
        res = await client.post("/api/rag/search", params={"query": "What are the four conditions for deadlock?", "top_k": 2})
        print(f"[PASS] POST /api/rag/search -> Status: {res.status_code}, matches: {len(res.json())}")
        assert len(res.json()) > 0
        top_match = res.json()[0]
        print(f"       Top match similarity: {top_match['similarity']}, doc: {top_match['filename']}")

        # 6. Stream Query
        query_payload = {
            "question": "What is Banker's algorithm and what are the Coffman conditions?",
            "stream": True,
            "top_k": 2,
        }
        res = await client.post("/api/rag/query", json=query_payload, timeout=60.0)
        print(f"[PASS] POST /api/rag/query (stream) -> Status: {res.status_code}")
        assert res.status_code == 200
        first_chunk = res.text[:200]
        print(f"       Stream preview:\n{first_chunk}...\n")

        # 7. Exam Paper Generation
        exam_payload = {
            "title": "Semester Assessment in Operating Systems",
            "subject": "Operating Systems",
            "difficulty": "medium",
            "total_marks": 50,
            "duration_minutes": 60,
            "include_solutions": True,
            "stream": True,
        }
        res = await client.post("/api/rag/exam/generate", json=exam_payload, timeout=120.0)
        print(f"[PASS] POST /api/rag/exam/generate (stream) -> Status: {res.status_code}")
        assert res.status_code == 200
        print(f"       Exam paper stream preview:\n{res.text[:300]}...\n")

        # 8. Clean up document
        res = await client.delete(f"/api/rag/documents/{doc_id}")
        print(f"[PASS] DELETE /api/rag/documents/{doc_id} -> Status: {res.status_code}")
        assert res.status_code == 200

    print("\nALL FASTAPI INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
