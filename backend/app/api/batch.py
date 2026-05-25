from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.delivery import delivery
from ..orchestrator import analyze_only
from ..storage.data_pool import pool

router = APIRouter()


class BatchScoreRequest(BaseModel):
    plot_ids: list[str]
    customer: str = "insurance"


@router.post("/score")
async def batch_score(req: BatchScoreRequest) -> dict:
    """保险公司视角：批量地块风险评分。"""
    if not req.plot_ids:
        raise HTTPException(status_code=400, detail="plot_ids is empty")

    async def _one(pid: str):
        plot = await pool.get_plot(pid)
        if not plot:
            return {"plot_id": pid, "error": "not_found"}
        result = await analyze_only(plot)
        if not result.warnings:
            return {
                "plot_id": pid,
                "risk_score": 0.1,
                "risk_level": "无",
                "warning_id": None,
            }
        w = max(result.warnings, key=lambda x: x.risk_level.numeric)
        return delivery.render(w, customer=req.customer, plot=plot)  # type: ignore[arg-type]

    out = await asyncio.gather(*[_one(pid) for pid in req.plot_ids])
    return {"customer": req.customer, "count": len(out), "results": out}
