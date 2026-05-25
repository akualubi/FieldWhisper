from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..agents.collector import collector, list_presets
from ..models import DataItem
from ..storage.data_pool import pool

router = APIRouter()


@router.post("/{plot_id}")
async def collect_for_plot(plot_id: str) -> dict:
    plot = await pool.get_plot(plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail=f"plot {plot_id} not found")
    items = await collector.collect_for_plot(plot)
    return {"count": len(items), "items": [i.model_dump(mode="json") for i in items[:20]]}


@router.post("/inject", response_model=DataItem)
async def inject_one(item: DataItem) -> DataItem:
    """演示用：直接注入一条 DataItem 到 DataPool。"""
    return await collector.inject(item)


@router.post("/inject/preset/{name}")
async def inject_preset(name: str, plot_id: Optional[str] = None) -> dict:
    """触发 seed/manual_injection_scenarios.json 中的一条 scenario。

    plot_id 可以省略 —— scenario 自带 parcel_id（甚至会自动创建临时地块如冰雹场景）。
    """
    plot = None
    if plot_id:
        plot = await pool.get_plot(plot_id)
        if not plot:
            raise HTTPException(status_code=404, detail=f"plot {plot_id} not found")
    try:
        items = await collector.trigger_preset(name, plot)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "preset": name,
        "plot_id": items[0].geo.plot_id if items and items[0].geo else None,
        "count": len(items),
    }


@router.get("/presets")
async def get_presets() -> list[dict]:
    return list_presets()
