from __future__ import annotations

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..events import bus

router = APIRouter()


@router.get("/stream")
async def stream():
    """SSE 实时事件流 —— 演讲屏幕直接订阅。

    事件 kind 包括：
      pipeline.start / pipeline.done
      collector.start / collector.done / data_item
      preset.start / preset.done
      analyst.start / analyst.done / judgment
      simulator.start / simulator.done / trajectory
      decision.start / decision.done / warning
      harness.start / harness.done
    """
    async def gen():
        async for line in bus.subscribe():
            yield {"data": line}
    return EventSourceResponse(gen())
