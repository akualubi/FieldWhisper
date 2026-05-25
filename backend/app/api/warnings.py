from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..agents.delivery import delivery
from ..models import Warning
from ..storage.data_pool import pool

router = APIRouter()


@router.get("", response_model=list[Warning])
async def list_warnings(plot_id: Optional[str] = None, limit: int = 50) -> list[Warning]:
    return await pool.query_warnings(plot_id=plot_id, limit=limit)


@router.get("/{warning_id}", response_model=Warning)
async def get_warning(warning_id: str) -> Warning:
    w = await pool.get_warning(warning_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"warning {warning_id} not found")
    return w


@router.get("/{warning_id}/render")
async def render_warning(warning_id: str, customer: str = "coop") -> dict:
    w = await pool.get_warning(warning_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"warning {warning_id} not found")
    plot = await pool.get_plot(w.plot_id)
    return delivery.render(w, customer=customer, plot=plot)  # type: ignore[arg-type]
