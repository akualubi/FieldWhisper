"""Source adapters：把不同来源的原始响应映射为统一 DataItem。

只搬不判 —— 解读和触发是 Analyst 的事。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from ...config import settings
from ...models import DataItem, GeoPoint


async def fetch_open_meteo_forecast(
    plot_id: str, lat: float, lon: float, hours: int = 72
) -> list[DataItem]:
    """Open-Meteo 完全免费，无需 API key。"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,soil_moisture_0_to_10cm",
        "forecast_days": max(1, (hours + 23) // 24),
        "timezone": "UTC",
    }
    items: list[DataItem] = []
    try:
        async with httpx.AsyncClient(timeout=15) as cli:
            r = await cli.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        # 网络拿不到就静默返回空，让上游降级或 mock
        return [DataItem(
            source="open_meteo",
            type="fetch_error",
            geo=GeoPoint(lat=lat, lon=lon, plot_id=plot_id),
            payload={"error": str(e)},
        )]

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])[:hours]
    for i, t in enumerate(times):
        payload = {
            "ts": t,
            "temperature_c": _safe(hourly.get("temperature_2m"), i),
            "humidity_pct": _safe(hourly.get("relative_humidity_2m"), i),
            "precipitation_mm": _safe(hourly.get("precipitation"), i),
            "wind_speed_ms": _safe(hourly.get("wind_speed_10m"), i),
            "soil_moisture_0_10cm": _safe(hourly.get("soil_moisture_0_to_10cm"), i),
        }
        items.append(
            DataItem(
                source="open_meteo",
                type="forecast",
                ts=_parse_ts(t),
                geo=GeoPoint(lat=lat, lon=lon, plot_id=plot_id),
                payload=payload,
            )
        )
    return items


def _safe(arr, i):
    if arr is None or i >= len(arr):
        return None
    return arr[i]


def _geo(plot):
    """Plot → GeoPoint helper."""
    return GeoPoint(lat=plot.lat, lon=plot.lon, plot_id=plot.plot_id)


def _guess_pest(*texts: str):
    blob = " ".join(t for t in texts if t)
    for kw in ("赤霉病", "条锈病", "草地贪夜蛾", "粘虫", "稻瘟病", "纹枯病", "大斑病", "白粉病", "锈病"):
        if kw in blob:
            return kw
    return None


def _parse_ts(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


# -------- Mock adapters（演示用，无外部依赖） --------

def mock_ndvi_series(plot_id: str, lat: float, lon: float, weeks: int = 8) -> list[DataItem]:
    """伪造 NDVI 时序，最近 1-2 周下降 → 模拟长势异常。"""
    items: list[DataItem] = []
    now = datetime.now(timezone.utc)
    for w in range(weeks):
        ts = now - timedelta(days=(weeks - w) * 7)
        # 后期下降
        ndvi = 0.72 - max(0, (w - 5)) * 0.05
        items.append(DataItem(
            source="sentinel_mock",
            type="ndvi",
            ts=ts,
            geo=GeoPoint(lat=lat, lon=lon, plot_id=plot_id),
            payload={"ndvi": round(ndvi, 3), "week_index": w},
        ))
    return items


def mock_pest_notice(plot_id: str, lat: float, lon: float, pest: str = "草地贪夜蛾") -> DataItem:
    return DataItem(
        source="moa_notice_mock",
        type="notice",
        geo=GeoPoint(lat=lat, lon=lon, plot_id=plot_id),
        payload={
            "title": f"周边县市{pest}发生程度上升",
            "body": f"近 7 日邻县{pest}诱蛾量明显上升，请加强田间监测。",
            "pest": pest,
            "severity": "中等",
        },
    )


def mock_farmer_post(plot_id: str, lat: float, lon: float, content: str) -> DataItem:
    return DataItem(
        source="farmer_chat_mock",
        type="post",
        geo=GeoPoint(lat=lat, lon=lon, plot_id=plot_id),
        payload={"content": content, "channel": "village_group_chat"},
    )
