from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..storage.data_pool import pool
from ..storage.knowledge import knowledge

router = APIRouter()


KNOWN_AGENTS = ["weather", "crop", "plot", "pest", "sentiment", "simulator", "decision"]


@router.get("")
async def list_agents() -> dict:
    return {"agents": KNOWN_AGENTS}


@router.get("/{name}/assets")
async def get_assets(name: str) -> dict:
    if name not in KNOWN_AGENTS:
        raise HTTPException(status_code=404, detail=f"unknown agent {name}")
    return knowledge.snapshot(name)


@router.get("/{name}/history")
async def get_history(name: str, limit: int = 50) -> list[dict]:
    if name not in KNOWN_AGENTS:
        raise HTTPException(status_code=404, detail=f"unknown agent {name}")
    return await pool.list_asset_history(name, limit=limit)
