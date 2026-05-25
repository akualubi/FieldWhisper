from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..orchestrator import run_pipeline, analyze_only
from ..storage.data_pool import pool

router = APIRouter()


@router.post("/{plot_id}")
async def analyze(plot_id: str, collect_first: bool = Query(default=False)) -> dict:
    """触发一次完整 pipeline。collect_first=true 会先从真实/mock 源拉数据。"""
    plot = await pool.get_plot(plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail=f"plot {plot_id} not found")
    result = await run_pipeline(plot, collect_first=collect_first) if collect_first else await analyze_only(plot)
    return result.to_dict()
