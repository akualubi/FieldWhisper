"""演示预设场景 —— 直接消费 seed/mock/manual_injection_scenarios.json。

不再硬编码场景逻辑；scenarios 来自 seed，由 Collector 翻译成 DataItem。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ...models import DataItem, GeoPoint, Plot
from ...storage.seed_loader import (
    load_scenarios,
    get_bulletin_by_label,
    get_farmer_chat_by_label,
)


def _ts(s: str | None = None) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _geo(plot: Plot) -> GeoPoint:
    return GeoPoint(lat=plot.lat, lon=plot.lon, plot_id=plot.plot_id)


def scenario_to_items(scenario_id: str, plot: Plot) -> list[DataItem]:
    """把 seed 里的一条 scenario 转成一组 DataItem。"""
    sc = next((s for s in load_scenarios() if s["id"] == scenario_id), None)
    if not sc:
        raise KeyError(f"unknown scenario: {scenario_id}")

    inj = sc.get("inject", {})
    injected_by = f"demo:scenario:{scenario_id}"
    items: list[DataItem] = []

    # 1) 气象覆盖 → forecast DataItem（按日）
    wx = inj.get("weather_override") or {}
    for day in wx.get("daily", []):
        items.append(DataItem(
            source="manual_injection",
            type="forecast",
            ts=_ts(day.get("date")),
            geo=_geo(plot),
            payload={
                "date": day.get("date"),
                "temperature_c_max": day.get("tmax"),
                "temperature_c_min": day.get("tmin"),
                "precipitation_mm": day.get("precip_mm", 0),
                "rh_max_pct": day.get("rh_max"),
                "wind_speed_max_ms": day.get("wind_max_ms"),
                # 兼容 Weather Analyst 现有字段
                "temperature_c": day.get("tmax"),
                "humidity_pct": day.get("rh_max"),
                "wind_speed_ms": day.get("wind_max_ms"),
                "soil_moisture_0_10cm": 0.42 if day.get("precip_mm", 0) >= 10 else 0.22,
            },
            injected_by=injected_by,
        ))

    # 2) NDVI 覆盖
    nd = inj.get("ndvi_override")
    if nd:
        for sample in nd:
            items.append(DataItem(
                source="manual_injection",
                type="ndvi",
                ts=_ts(sample.get("date")),
                geo=_geo(plot),
                payload=sample,
                injected_by=injected_by,
            ))

    # 3) 病虫情报通报
    for label in inj.get("bulletin_override") or []:
        b = get_bulletin_by_label(label)
        if not b:
            continue
        # 通报里抽 pest（粗匹配）
        pest = _guess_pest(b["body"], b["title"])
        items.append(DataItem(
            source="manual_injection",
            type="notice",
            geo=_geo(plot),
            payload={
                "title": b["title"],
                "body": b["body"],
                "pest": pest,
                "severity": "重" if "紧急" in b["title"] or "重" in b["title"] else "中等",
            },
            injected_by=injected_by,
        ))

    # 4) 舆情/社媒
    for label in inj.get("social_signal_override") or []:
        c = get_farmer_chat_by_label(label)
        if not c:
            continue
        for line in c["lines"][:5]:
            items.append(DataItem(
                source="manual_injection",
                type="post",
                geo=_geo(plot),
                payload={"content": line, "channel": c.get("group", "")},
                injected_by=injected_by,
            ))

    # 5) 当前生育期（让 Crop Analyst 用上 plot.stage_zh，无需额外注入）
    items.append(DataItem(
        source="manual_injection",
        type="crop_stage",
        geo=_geo(plot),
        payload={"crop": plot.crop, "stage_zh": plot.stage_zh, "stage": plot.stage.value},
        injected_by=injected_by,
    ))

    return items


def _guess_pest(*texts: str) -> str | None:
    blob = " ".join(texts)
    for kw in ("赤霉病", "条锈病", "草地贪夜蛾", "粘虫", "稻瘟病", "纹枯病", "大斑病", "白粉病"):
        if kw in blob:
            return kw
    return None


def list_presets() -> list[dict]:
    """对前端暴露的预设列表（直接转 seed scenarios）。"""
    out = []
    for s in load_scenarios():
        inj = s.get("inject", {})
        out.append({
            "name": s["id"],
            "title_zh": s["label"],
            "narrative_hook": s.get("narrative_hook", ""),
            "target_plot_id": inj.get("parcel_id"),
            "expected_decision": inj.get("expected_decision", {}),
        })
    return out


def parcel_extra(scenario_id: str) -> dict | None:
    """场景里可能定义"演示临时地块"（如冰雹场景的苹果园），
    Collector 在注入前用它创建/upsert Plot。"""
    sc = next((s for s in load_scenarios() if s["id"] == scenario_id), None)
    if not sc:
        return None
    return sc.get("inject", {}).get("parcel_extra")
