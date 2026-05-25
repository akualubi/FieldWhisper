"""把前端"气象图标"翻译成 DataItem 批次。

每个 intent 都是一个 (plot, intensity, hours) → DataItem[] 的函数。
设计原则：注入的数值必须足够"狠"以保证 Analyst 一定能触发对应风险，否则演讲翻车。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from ..models import DataItem, GeoPoint, Plot


Intensity = str  # "轻" | "中" | "重"


def _geo(plot: Plot) -> GeoPoint:
    return GeoPoint(lat=plot.lat, lon=plot.lon, plot_id=plot.plot_id)


def _now(offset_h: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=offset_h)


def _injected_by(intent: str) -> str:
    return f"demo:drop:{intent}"


# ---------- 各气象 intent 的 builder ----------

def _heavy_rain(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    days = max(3, hours // 24)
    rain_per_day = {"轻": 25, "中": 50, "重": 90}.get(intensity, 50)
    items = []
    for d in range(days):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(d * 24), geo=_geo(plot),
            payload={
                "date": (_now(d * 24)).date().isoformat(),
                "temperature_c_max": 23, "temperature_c_min": 19,
                "precipitation_mm": rain_per_day, "rh_max_pct": 92,
                "wind_speed_max_ms": 3,
                "temperature_c": 23, "humidity_pct": 92,
                "wind_speed_ms": 3,
                "soil_moisture_0_10cm": 0.45,
            },
            injected_by=_injected_by("暴雨"),
        ))
    return items


def _strong_wind(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    speed = {"轻": 12, "中": 16, "重": 22}.get(intensity, 16)
    items = []
    for h in range(0, hours, 6):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(h), geo=_geo(plot),
            payload={
                "date": (_now(h)).date().isoformat(),
                "temperature_c_max": 26, "temperature_c_min": 18,
                "precipitation_mm": 2,
                "wind_speed_max_ms": speed,
                "wind_speed_ms": speed,
                "temperature_c": 26, "humidity_pct": 65,
                "soil_moisture_0_10cm": 0.30,
            },
            injected_by=_injected_by("大风"),
        ))
    return items


def _snow_storm(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    tmin = {"轻": -3, "中": -8, "重": -15}.get(intensity, -8)
    items = []
    for d in range(max(2, hours // 24)):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(d * 24), geo=_geo(plot),
            payload={
                "date": (_now(d * 24)).date().isoformat(),
                "temperature_c_max": tmin + 5, "temperature_c_min": tmin,
                "precipitation_mm": 18, "rh_max_pct": 85,
                "wind_speed_max_ms": 8,
                "wind_speed_ms": 8,
                "temperature_c": tmin + 5, "humidity_pct": 85,
                "soil_moisture_0_10cm": 0.30,
                "snow_depth_cm": 12 if intensity == "重" else 6,
            },
            injected_by=_injected_by("暴雪"),
        ))
    items.append(DataItem(
        source="manual_injection", type="notice", geo=_geo(plot),
        payload={
            "title": "局地暴雪预警（演示注入）",
            "body": f"未来 {hours}h 该区域将出现暴雪，最低气温 {tmin}℃，注意大棚/设施农业及越冬作物。",
            "severity": "重",
        },
        injected_by=_injected_by("暴雪"),
    ))
    return items


def _sandstorm(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    wind = {"轻": 10, "中": 14, "重": 18}.get(intensity, 14)
    items = []
    for h in range(0, hours, 6):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(h), geo=_geo(plot),
            payload={
                "date": (_now(h)).date().isoformat(),
                "temperature_c_max": 28, "temperature_c_min": 14,
                "precipitation_mm": 0,
                "wind_speed_max_ms": wind, "wind_speed_ms": wind,
                "rh_max_pct": 15, "humidity_pct": 15,
                "temperature_c": 28,
                "soil_moisture_0_10cm": 0.10,
                "visibility_km": 0.8,
                "pm10_ugm3": 1200,
            },
            injected_by=_injected_by("沙尘暴"),
        ))
    items.append(DataItem(
        source="manual_injection", type="notice", geo=_geo(plot),
        payload={
            "title": "强沙尘暴预警（演示注入）",
            "body": f"未来 {hours}h 持续强沙尘，能见度 < 1km，对幼苗及花期作物机械损伤风险高。",
            "severity": "重",
        },
        injected_by=_injected_by("沙尘暴"),
    ))
    return items


def _typhoon(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    wind = {"轻": 18, "中": 25, "重": 35}.get(intensity, 25)
    items = []
    for h in range(0, hours, 6):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(h), geo=_geo(plot),
            payload={
                "date": (_now(h)).date().isoformat(),
                "temperature_c_max": 27, "temperature_c_min": 23,
                "precipitation_mm": 30,
                "wind_speed_max_ms": wind, "wind_speed_ms": wind,
                "rh_max_pct": 95, "humidity_pct": 95,
                "temperature_c": 25,
                "soil_moisture_0_10cm": 0.48,
            },
            injected_by=_injected_by("台风"),
        ))
    items.append(DataItem(
        source="manual_injection", type="notice", geo=_geo(plot),
        payload={
            "title": "台风路径预警（演示注入）",
            "body": f"台风外围 {hours}h 内影响该区域，阵风 {wind} m/s，雨强大。",
            "severity": "重",
        },
        injected_by=_injected_by("台风"),
    ))
    return items


def _drought(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    soil = {"轻": 0.16, "中": 0.10, "重": 0.05}.get(intensity, 0.10)
    # tmax 故意压在 33（< 高温阈值 35），让 Decision 把焦点放在干旱本身
    tmax = {"轻": 30, "中": 33, "重": 34}.get(intensity, 33)
    items = []
    for d in range(max(3, hours // 24)):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(d * 24), geo=_geo(plot),
            payload={
                "date": (_now(d * 24)).date().isoformat(),
                "temperature_c_max": tmax, "temperature_c_min": 22,
                "precipitation_mm": 0, "rh_max_pct": 28,
                "wind_speed_max_ms": 3, "wind_speed_ms": 3,
                "temperature_c": tmax, "humidity_pct": 28,
                "soil_moisture_0_10cm": soil,
            },
            injected_by=_injected_by("干旱"),
        ))
    return items


def _heatwave(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    tmax = {"轻": 35, "中": 38, "重": 41}.get(intensity, 38)
    items = []
    for d in range(max(2, hours // 24)):
        items.append(DataItem(
            source="manual_injection", type="forecast",
            ts=_now(d * 24), geo=_geo(plot),
            payload={
                "date": (_now(d * 24)).date().isoformat(),
                "temperature_c_max": tmax, "temperature_c_min": 28,
                "precipitation_mm": 0, "rh_max_pct": 38,
                "wind_speed_max_ms": 3, "wind_speed_ms": 3,
                "temperature_c": tmax, "humidity_pct": 38,
                "soil_moisture_0_10cm": 0.18,
            },
            injected_by=_injected_by("高温"),
        ))
    return items


def _hail(plot: Plot, intensity: Intensity, hours: int) -> list[DataItem]:
    items = [
        DataItem(
            source="manual_injection", type="notice", geo=_geo(plot),
            payload={
                "title": "强对流冰雹预警（演示注入）",
                "body": f"该区域午后强对流明显，雷达回波 ≥55dBZ，预计 1-2h 内有冰雹。",
                "severity": "重", "peril": "冰雹",
            },
            injected_by=_injected_by("冰雹"),
        ),
        DataItem(
            source="manual_injection", type="post", geo=_geo(plot),
            payload={
                "content": "刚才那场雹子 我家苹果全砸了 [哭]",
                "channel": "village_group_chat",
            },
            injected_by=_injected_by("冰雹"),
        ),
        DataItem(
            source="manual_injection", type="post", geo=_geo(plot),
            payload={
                "content": "这边也下了 鸡蛋大小",
                "channel": "village_group_chat",
            },
            injected_by=_injected_by("冰雹"),
        ),
    ]
    return items


WEATHER_INTENTS: dict[str, dict] = {
    "暴雨":   {"peril_hint": "HEAVY_RAIN_AT_HARVEST", "icon": "⛈️", "build": _heavy_rain},
    "大风":   {"peril_hint": "WIND_LODGING",          "icon": "💨", "build": _strong_wind},
    "暴雪":   {"peril_hint": "SNOW_DISASTER",         "icon": "❄️", "build": _snow_storm},
    "沙尘暴": {"peril_hint": "SANDSTORM",             "icon": "🌪️", "build": _sandstorm},
    "台风":   {"peril_hint": "TYPHOON",               "icon": "🌀", "build": _typhoon},
    "干旱":   {"peril_hint": "DROUGHT_SEASONAL",      "icon": "☀️", "build": _drought},
    "高温":   {"peril_hint": "HEAT_STRESS_AT_FLOWERING","icon": "🔥","build": _heatwave},
    "冰雹":   {"peril_hint": "HAIL",                  "icon": "🧊", "build": _hail},
}


def build_intent_items(intent: str, plot: Plot, intensity: str = "中", hours: int = 48) -> list[DataItem]:
    if intent not in WEATHER_INTENTS:
        raise KeyError(f"unknown weather intent: {intent}")
    return WEATHER_INTENTS[intent]["build"](plot, intensity, hours)


def list_intents() -> list[dict]:
    return [
        {"name": k, "icon": v["icon"], "peril_hint": v["peril_hint"]}
        for k, v in WEATHER_INTENTS.items()
    ]
