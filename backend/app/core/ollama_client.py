from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings


class OllamaClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            tags = response.json()
            models = [m.get("name", "") for m in tags.get("models", [])]
            return {
                "reachable": True,
                "models": models,
                "chat_model_available": any(
                    settings.chat_model.split(":")[0] in m for m in models
                ),
            }

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model or settings.chat_model,
            "messages": messages,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if chunk.get("done"):
                        break
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> str:
        parts: list[str] = []
        async for token in self.chat_stream(messages, model=model):
            parts.append(token)
        return "".join(parts)

    async def embeddings(
        self,
        prompt: str,
        model: str | None = None,
    ) -> list[float]:
        payload = {
            "model": model or settings.embed_model,
            "prompt": prompt,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])


ollama_client = OllamaClient()
