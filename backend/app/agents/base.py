from __future__ import annotations

from typing import Any

from ..events import bus
from ..storage.knowledge import knowledge


class Agent:
    """Agent 基类：绑定一个资产目录，每次 run 都重新加载知识。"""

    name: str = "agent"

    def __init__(self, name: str | None = None) -> None:
        if name:
            self.name = name

    def load_assets(self) -> dict[str, Any]:
        """每次推理都重新读资产 —— Harness 写完立刻生效。"""
        return knowledge.snapshot(self.name)

    async def emit(self, kind: str, payload: dict) -> None:
        await bus.publish(kind, {"agent": self.name, **payload})
