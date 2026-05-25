from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator


class EventBus:
    """简单的 in-process pub/sub，用于 SSE 实时事件流。

    Agent 在每个关键节点（采集到 DataItem、生成 Judgment、出 Warning、
    Harness 写回资产）都 publish 一条 event；前端通过 /events/stream 订阅。
    演讲时大屏点亮 pipeline 用。
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    async def publish(self, kind: str, payload: dict[str, Any]) -> None:
        evt = {
            "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        line = json.dumps(evt, ensure_ascii=False, default=str)
        for q in list(self._subscribers):
            try:
                q.put_nowait(line)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> AsyncIterator[str]:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.add(q)
        try:
            while True:
                line = await q.get()
                yield line
        finally:
            self._subscribers.discard(q)


bus = EventBus()
