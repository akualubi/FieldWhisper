"""LLM 客户端 —— 按 seed/llm_api_notes.md。

四家（deepseek / qwen / moonshot / anthropic）全部 OpenAI Chat Completions 兼容，
仅换 base_url + api_key + model。Anthropic 用官方 SDK。

任何异常 → 静默回退 None，上游走规则模板。这是 demo 现场不翻车的底线。
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from ..config import settings


PROVIDERS = {
    "deepseek":  {"base": "https://api.deepseek.com",                                "model": "deepseek-chat"},
    "qwen":      {"base": "https://dashscope.aliyuncs.com/compatible-mode/v1",       "model": "qwen-turbo"},
    "moonshot":  {"base": "https://api.moonshot.cn/v1",                              "model": "moonshot-v1-8k"},
}


class LLMClient:
    def __init__(self) -> None:
        self.provider = (settings.llm_provider or "none").lower()
        if self.provider not in (*PROVIDERS.keys(), "anthropic", "none"):
            self.provider = "none"
        if self.provider != "none" and not settings.llm_api_key:
            self.provider = "none"

    @property
    def available(self) -> bool:
        return self.provider != "none"

    def describe(self) -> dict:
        if not self.available:
            return {"provider": "none", "model": None, "note": "running on rule fallback"}
        if self.provider == "anthropic":
            return {"provider": "anthropic", "model": settings.llm_model or "claude-haiku-4-5"}
        spec = PROVIDERS[self.provider]
        return {"provider": self.provider, "model": settings.llm_model or spec["model"], "base": spec["base"]}

    async def complete_json(self, system: str, user: str, max_tokens: int = 800) -> Optional[dict[str, Any]]:
        text = await self.complete_text(system, user, max_tokens)
        return self._extract_json(text) if text else None

    async def complete_text(self, system: str, user: str, max_tokens: int = 600) -> Optional[str]:
        if not self.available:
            return None
        try:
            if self.provider == "anthropic":
                return await self._anthropic_call(system, user, max_tokens)
            return await self._openai_compatible_call(system, user, max_tokens)
        except Exception:
            return None

    async def _anthropic_call(self, system: str, user: str, max_tokens: int) -> Optional[str]:
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            return None
        client = AsyncAnthropic(api_key=settings.llm_api_key)
        resp = await client.messages.create(
            model=settings.llm_model or "claude-haiku-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "\n".join(parts).strip() if parts else None

    async def _openai_compatible_call(self, system: str, user: str, max_tokens: int) -> Optional[str]:
        import httpx

        spec = PROVIDERS[self.provider]
        url = spec["base"].rstrip("/") + "/chat/completions"
        model = settings.llm_model or spec["model"]
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
        }
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_json(text: str) -> Optional[dict[str, Any]]:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return None


llm = LLMClient()
