from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import Plot
from ..storage.data_pool import pool

router = APIRouter()


@router.post("", response_model=Plot)
async def upsert_plot(plot: Plot) -> Plot:
    await pool.upsert_plot(plot)
    return plot


@router.get("", response_model=list[Plot])
async def list_plots() -> list[Plot]:
    return await pool.list_plots()


@router.get("/{plot_id}", response_model=Plot)
async def get_plot(plot_id: str) -> Plot:
    p = await pool.get_plot(plot_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"plot {plot_id} not found")
    return p
