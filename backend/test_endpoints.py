"""Quick smoke test for all API endpoints."""
import asyncio
import json

import httpx

BASE = "http://127.0.0.1:8765"


async def main() -> None:
    async with httpx.AsyncClient(timeout=120.0) as client:
        for path in [
            "/api/health",
            "/api/debug/status",
            "/api/codegen/status",
        ]:
            r = await client.get(f"{BASE}{path}")
            print(f"GET {path}: {r.status_code} {r.text[:100]}")

        debug_payload = {
            "code": "print(undefined_var)",
            "error_message": "NameError: name 'undefined_var' is not defined",
            "language": "python",
            "stream": False,
        }
        r = await client.post(f"{BASE}/api/debug/analyze", json=debug_payload)
        print(f"POST /api/debug/analyze: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  diagnosis: {data.get('diagnosis', '')[:80]}")
            print(f"  fixed_code lines: {len(data.get('fixed_code', '').splitlines())}")
        else:
            print(f"  error: {r.text[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
