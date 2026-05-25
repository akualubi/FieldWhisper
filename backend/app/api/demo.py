"""Demo 层 API —— 给"拖图标到省份"前端用。

唯一一个端点 `/api/demo/drop` 是核心：
  前端 POST {province, weather, intensity?, duration_h?}
  后端：
    1) 解析省份 → 找/造对应 plot
    2) weather intent → DataItem[] 注入 DataPool
    3) 跑完整 pipeline (analyze_only)
    4) 返回 Warning 列表 + 渲染到地图色块的 risk_level
    5) 全过程 SSE 推送给大屏
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agents.collector import collector
from ..agents.delivery import delivery
from ..demo import PROVINCES, build_intent_items, resolve_province
from ..demo.province_map import make_demo_plot_id
from ..demo.weather_intents import list_intents
from ..events import bus
from ..models import CropStage, Plot, RiskLevel
from ..orchestrator import analyze_only
from ..storage.data_pool import pool

router = APIRouter()


class DropRequest(BaseModel):
    province: str = Field(..., description="省级名称，如 '山东' / '黑龙江' / '内蒙古'")
    weather: str = Field(..., description="气象 intent：暴雨/大风/暴雪/沙尘暴/台风/干旱/高温/冰雹")
    intensity: str = Field(default="中", description="轻/中/重")
    duration_h: int = Field(default=48, ge=6, le=168)
    plot_id: Optional[str] = Field(default=None, description="可选：指定 plot；否则自动选 seed plot 或新建 P-DEMO-<省>")
    customer: str = Field(default="coop", description="可选：直接渲染到某 B 端客户")


@router.get("/weathers")
async def get_weathers() -> list[dict]:
    """前端图标库 —— 列出所有可拖的气象 intent。"""
    return list_intents()


@router.get("/provinces")
async def get_provinces() -> list[dict]:
    """前端地图层 —— 列出所有支持的省份 + 默认作物。"""
    return [
        {"province": k, "lat": v[0], "lon": v[1], "default_crop": v[2], "default_stage_zh": v[3]}
        for k, v in PROVINCES.items()
    ]


@router.post("/drop")
async def drop(req: DropRequest) -> dict:
    """前端拖一个图标到省份 → 后端走完整 pipeline。"""
    resolved = resolve_province(req.province)
    if not resolved:
        raise HTTPException(status_code=400, detail=f"unknown province: {req.province}")

    # 1) 解析 plot：优先用户指定 > 该省 seed plot > 新建 P-DEMO-<省>
    plot = await _resolve_plot(resolved, req.plot_id)

    # 2) 注入 DataItem
    items = build_intent_items(req.weather, plot, req.intensity, req.duration_h)
    await bus.publish("demo.drop", {
        "province": resolved["province"],
        "weather": req.weather,
        "intensity": req.intensity,
        "plot_id": plot.plot_id,
        "items_count": len(items),
    })
    for it in items:
        await collector.inject(it)

    # 3) 跑 pipeline
    result = await analyze_only(plot)

    # 4) 总等级（取最高）
    overall = "无"
    if result.warnings:
        overall = max(result.warnings, key=lambda w: w.risk_level.numeric).risk_level.value

    # 5) 按客户渲染（默认合作社视图，B 端可指定 insurance）
    rendered = []
    for w in result.warnings:
        try:
            rendered.append(delivery.render(w, customer=req.customer, plot=plot))  # type: ignore[arg-type]
        except Exception:
            pass

    return {
        "province": resolved["province"],
        "weather": req.weather,
        "intensity": req.intensity,
        "plot": plot.model_dump(mode="json"),
        "data_items_injected": len(items),
        "overall_risk_level": overall,
        "warnings": [w.model_dump(mode="json") for w in result.warnings],
        "rendered": rendered,
    }


@router.get("/map")
async def get_map(limit_per_plot: int = 1) -> dict:
    """前端地图色块刷新用 —— 按省份给出当前最高风险等级 + 灾种。

    逻辑：把所有 plots 按 province 聚合，每个 plot 取最近的 Warning。
    """
    plots = await pool.list_plots()
    by_province: dict[str, list[dict]] = {}

    for p in plots:
        province = _plot_to_province(p)
        if not province:
            continue
        warnings = await pool.query_warnings(plot_id=p.plot_id, limit=limit_per_plot)
        bucket = by_province.setdefault(province, [])
        if not warnings:
            bucket.append({
                "plot_id": p.plot_id, "name": p.name,
                "risk_level": "安全", "peril_codes": [], "warning_count": 0,
            })
        else:
            top = max(warnings, key=lambda w: w.risk_level.numeric)
            bucket.append({
                "plot_id": p.plot_id, "name": p.name,
                "risk_level": top.risk_level.value,
                "peril_codes": list({w.peril_code.value for w in warnings}),
                "headline": top.headline,
                "warning_count": len(warnings),
            })

    summary = []
    for province, plots_data in by_province.items():
        max_level = max(plots_data, key=lambda d: _level_rank(d["risk_level"]))["risk_level"]
        all_perils = sorted({p for d in plots_data for p in d["peril_codes"]})
        summary.append({
            "province": province,
            "risk_level": max_level,
            "peril_codes": all_perils,
            "plots": plots_data,
        })

    counts = {"极高": 0, "高": 0, "中": 0, "低": 0, "无": 0, "安全": 0}
    for s in summary:
        counts[s["risk_level"]] = counts.get(s["risk_level"], 0) + 1

    return {
        "as_of": _iso_now(),
        "overview": {
            "高风险": counts["极高"] + counts["高"],
            "中风险": counts["中"],
            "低风险": counts["低"],
            "安全":   counts["安全"] + counts["无"],
        },
        "provinces": summary,
    }


@router.post("/reset")
async def reset_demo() -> dict:
    """演讲下一轮前清空 demo 数据（保留 seed plots，清掉 P-DEMO-* 注入产生的 warnings/judgments）。

    注意：这只是清当前 DB 的运行时数据，不动 knowledge/ 资产文件。
    要彻底重置：`git checkout backend/knowledge/ && rm backend/suian.db`。
    """
    from ..storage.db import get_conn

    async with get_conn() as db:
        for tbl in ("data_items", "judgments", "warnings", "feedbacks", "evaluations"):
            await db.execute(f"DELETE FROM {tbl}")
        await db.commit()
    await bus.publish("demo.reset", {"ok": True})
    return {"ok": True, "cleared": ["data_items", "judgments", "warnings", "feedbacks", "evaluations"]}


# ---------- helpers ----------

async def _resolve_plot(resolved: dict, requested_id: str | None) -> Plot:
    if requested_id:
        p = await pool.get_plot(requested_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"plot {requested_id} not found")
        return p

    seed_id = resolved.get("seed_plot_id")
    if seed_id:
        p = await pool.get_plot(seed_id)
        if p:
            return p

    # 自动创建临时 demo plot
    pid = make_demo_plot_id(resolved["province"])
    p = await pool.get_plot(pid)
    if p:
        return p
    crop = resolved["default_crop"]
    stage_zh = resolved["default_stage_zh"]
    p = Plot(
        plot_id=pid,
        name=f"{resolved['province']} · 演示地块",
        lat=resolved["lat"], lon=resolved["lon"],
        crop=crop, stage_zh=stage_zh,
        stage=_infer_stage(stage_zh),
        area_mu=100, terrain="平原", soil_drainage="中等",
    )
    await pool.upsert_plot(p)
    return p


def _plot_to_province(plot: Plot) -> str | None:
    # 优先用 plot 名前缀（"河北馆陶..." → "河北"）
    for prov in PROVINCES:
        if plot.name.startswith(prov) or plot.plot_id.startswith(f"P-DEMO-{prov}"):
            return prov
    # 用 seed plot 反查
    from ..demo.province_map import SEED_PROVINCE_TO_PLOT
    for prov, pid in SEED_PROVINCE_TO_PLOT.items():
        if plot.plot_id == pid:
            return prov
    # 用经纬度找最近的省（粗略）
    best, best_dist = None, 1e9
    for prov, (lat, lon, *_) in PROVINCES.items():
        d = (lat - plot.lat) ** 2 + (lon - plot.lon) ** 2
        if d < best_dist:
            best, best_dist = prov, d
    return best


def _level_rank(level: str) -> int:
    return {"无": 0, "安全": 0, "低": 1, "中": 2, "高": 3, "极高": 4}.get(level, 0)


def _infer_stage(stage_zh: str) -> CropStage:
    if "灌浆" in stage_zh or "蜡熟" in stage_zh:
        return CropStage.GRAIN_FILLING
    if "抽雄" in stage_zh:
        return CropStage.TASSELING
    if "孕穗" in stage_zh:
        return CropStage.BOOTING
    if "拔节" in stage_zh:
        return CropStage.JOINTING
    if "苗" in stage_zh or "叶" in stage_zh:
        return CropStage.SEEDING
    return CropStage.JOINTING


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
