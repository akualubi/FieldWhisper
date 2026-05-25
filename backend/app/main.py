from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .config import settings
from .llm import llm
from .models import Plot
from .storage.data_pool import pool
from .storage.db import init_db
from .storage.seed_loader import load_parcels


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 从 seed/mock/parcels.json 种 plots（幂等）
    for raw in load_parcels():
        plot = Plot.from_seed(raw)
        if not await pool.get_plot(plot.plot_id):
            await pool.upsert_plot(plot)
    yield


app = FastAPI(
    title="穗安 SuiAn",
    description=(
        "面向 B 端机构的大田作物风险智能预警平台。"
        "多 Agent 协同 + Harness 自进化。"
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {
        "name": "穗安 SuiAn",
        "version": app.version,
        "llm": llm.describe(),
        "docs": "/docs",
        "sse": "/api/events/stream",
        "presets": "/api/collect/presets",
        "seed": "/api/seed",
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
