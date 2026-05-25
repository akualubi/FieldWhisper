from __future__ import annotations

from typing import Any

from ...models import DataItem, Plot, RiskJudgment, RiskLevel
from .base import AnalystAgent


def _level(score: float) -> RiskLevel:
    if score >= 4:
        return RiskLevel.EXTREME
    if score >= 3:
        return RiskLevel.HIGH
    if score >= 2:
        return RiskLevel.MEDIUM
    if score >= 1:
        return RiskLevel.LOW
    return RiskLevel.NONE


def _get(d: dict, *keys):
    """从 payload 取第一个非 None 的字段（兼容多个采集源命名）。"""
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


class WeatherAnalyst(AnalystAgent):
    name = "weather"
    agent_kind = "weather"
    subscribed_types = ("forecast",)

    async def analyze(
        self,
        plot: Plot,
        items: list[DataItem],
        assets: dict[str, Any],
    ) -> list[RiskJudgment]:
        rules = assets.get("rules") or {}
        heat = rules.get("heat", {"temp_c": 35.0, "consec_hours": 6})
        wind = rules.get("wind", {"speed_ms": 13.8, "consec_hours": 3})
        rain = rules.get("rain", {"mm_24h": 50.0})
        rain_cont = rules.get("rain_continuous", {"mm_per_day_min": 10.0, "consec_days": 4})
        drought = rules.get("drought", {"soil_moisture_min": 0.18, "rain_mm_24h_max": 1.0})
        frost = rules.get("frost", {"tmin_c": 0.0, "severe_tmin_c": -2.0})

        forecasts = [i for i in items if i.type == "forecast" and "error" not in i.payload]
        if not forecasts:
            return []

        forecasts.sort(key=lambda x: x.ts)
        ev_ids = [f.id for f in forecasts[:24]]

        # 提取序列（兼容多源字段名）
        temps_max = [_get(f.payload, "temperature_c_max", "temperature_c") for f in forecasts]
        temps_min = [_get(f.payload, "temperature_c_min") for f in forecasts]
        winds = [_get(f.payload, "wind_speed_max_ms", "wind_speed_ms") for f in forecasts]
        rains = [_get(f.payload, "precipitation_mm") or 0 for f in forecasts]
        humids = [_get(f.payload, "rh_max_pct", "humidity_pct") for f in forecasts]
        soils = [_get(f.payload, "soil_moisture_0_10cm") for f in forecasts]

        judgments: list[RiskJudgment] = []

        # ---- 高温 ----
        hot_pts = sum(1 for t in temps_max if t is not None and t >= heat["temp_c"])
        if hot_pts >= max(1, heat["consec_hours"] // 12):  # 容忍按日预报：每天≈12h
            score = 1 + min(3, hot_pts // 2)
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type="高温热害",
                level=_level(score),
                confidence=min(0.95, 0.5 + 0.1 * hot_pts),
                rationale=f"未来预报内有 {hot_pts} 个时段 ≥{heat['temp_c']}℃",
                evidence=ev_ids,
                rule_refs=["heat.temp_c", "heat.consec_hours"],
                extras={"hot_count": hot_pts, "max_temp": max([t for t in temps_max if t is not None], default=None)},
            ))

        # ---- 大风 ----
        wind_pts = sum(1 for w in winds if w is not None and w >= wind["speed_ms"])
        if wind_pts >= max(1, wind["consec_hours"] // 12):
            score = 1 + min(3, wind_pts // 2)
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type="大风",
                level=_level(score),
                confidence=min(0.95, 0.5 + 0.1 * wind_pts),
                rationale=f"未来预报内有 {wind_pts} 个时段风速 ≥{wind['speed_ms']} m/s",
                evidence=ev_ids,
                rule_refs=["wind.speed_ms", "wind.consec_hours"],
                extras={"wind_count": wind_pts, "max_wind": max([w for w in winds if w is not None], default=None)},
            ))

        # ---- 暴雨（单日） ----
        max_rain = max(rains[:8]) if rains else 0
        if max_rain >= rain["mm_24h"]:
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type="暴雨",
                level=RiskLevel.HIGH if max_rain >= rain["mm_24h"] * 2 else RiskLevel.MEDIUM,
                confidence=0.8,
                rationale=f"单日最大降水 {max_rain:.1f} mm",
                evidence=ev_ids,
                rule_refs=["rain.mm_24h"],
                extras={"max_rain_day": max_rain},
            ))

        # ---- 连阴雨 / 烂场雨 ----
        wet_days = [r for r in rains[:10] if r >= rain_cont["mm_per_day_min"]]
        total_wet = sum(wet_days)
        if len(wet_days) >= rain_cont["consec_days"]:
            # 收获/灌浆期 + 高湿 → 烂场雨
            stage = (plot.stage_zh or "")
            is_harvest_window = any(k in stage for k in ("灌浆", "蜡熟", "成熟"))
            risk_type = "烂场雨" if is_harvest_window else "连阴雨"
            avg_humid = sum(h for h in humids[:7] if h is not None) / max(1, sum(1 for h in humids[:7] if h is not None))
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type=risk_type,
                level=RiskLevel.HIGH if (total_wet >= 60 or avg_humid >= 88) else RiskLevel.MEDIUM,
                confidence=0.82,
                rationale=f"预报内有 {len(wet_days)} 天日降水 ≥{rain_cont['mm_per_day_min']}mm，累计 {total_wet:.0f}mm；日均湿度约 {avg_humid:.0f}%",
                evidence=ev_ids,
                rule_refs=["rain_continuous.consec_days", "rain_continuous.mm_per_day_min"],
                extras={"wet_days": len(wet_days), "total_wet_mm": total_wet, "avg_humid": avg_humid},
            ))

        # ---- 干旱 ----
        valid_soils = [s for s in soils[:24] if s is not None]
        rain_24 = sum(rains[:1]) if rains else 0
        if valid_soils:
            avg_soil = sum(valid_soils) / len(valid_soils)
            if avg_soil <= drought["soil_moisture_min"] and rain_24 <= drought["rain_mm_24h_max"]:
                judgments.append(RiskJudgment(
                    agent_kind=self.agent_kind, plot_id=plot.plot_id,
                    risk_type="干旱",
                    level=RiskLevel.MEDIUM,
                    confidence=0.7,
                    rationale=f"土壤湿度均值 {avg_soil:.2f}，近日降水 {rain_24:.1f} mm",
                    evidence=ev_ids,
                    rule_refs=["drought.soil_moisture_min"],
                    extras={"avg_soil": avg_soil},
                ))

        # ---- 晚霜冻 ----
        valid_tmins = [(i, t) for i, t in enumerate(temps_min) if t is not None]
        cold_hits = [(i, t) for i, t in valid_tmins if t <= frost["tmin_c"]]
        if cold_hits:
            severe = any(t <= frost["severe_tmin_c"] for _, t in cold_hits)
            level = RiskLevel.HIGH if severe else RiskLevel.MEDIUM
            min_t = min(t for _, t in cold_hits)
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type="晚霜冻",
                level=level,
                confidence=0.85,
                rationale=f"预报夜间最低温达到 {min_t:.1f}℃（≤ {frost['tmin_c']}℃ 触发；≤ {frost['severe_tmin_c']}℃ 为重霜冻）",
                evidence=ev_ids,
                rule_refs=["frost.tmin_c", "frost.severe_tmin_c"],
                extras={"min_tmin": min_t, "cold_days": len(cold_hits)},
            ))

        return judgments


weather_analyst = WeatherAnalyst()
