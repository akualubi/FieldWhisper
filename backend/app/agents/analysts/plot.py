from __future__ import annotations

from typing import Any

from ...models import DataItem, Plot, RiskJudgment, RiskLevel
from .base import AnalystAgent


TERRAIN_RISK = {
    "洼地": {"暴雨": 1.4, "倒伏": 1.3},
    "坡地": {"暴雨": 0.8, "干旱": 1.2},
    "丘陵": {"大风": 1.2, "干旱": 1.1},
    "平原": {"大风": 1.1},
}
DRAINAGE_RISK = {
    "较差": {"暴雨": 1.5, "倒伏": 1.4},
    "中等": {"暴雨": 1.1, "倒伏": 1.1},
    "良好": {"暴雨": 0.8, "倒伏": 0.9},
}


class PlotAnalyst(AnalystAgent):
    name = "plot"
    agent_kind = "plot"
    subscribed_types = ("forecast",)   # 看土壤湿度

    async def analyze(
        self,
        plot: Plot,
        items: list[DataItem],
        assets: dict[str, Any],
    ) -> list[RiskJudgment]:
        rules = assets.get("rules") or {}
        wet_threshold = (rules.get("wet") or {}).get("soil_moisture_min", 0.38)

        soils = [i.payload.get("soil_moisture_0_10cm") for i in items
                 if i.type == "forecast" and i.payload.get("soil_moisture_0_10cm") is not None]
        avg_soil = sum(soils[:24]) / max(1, len(soils[:24])) if soils else None

        terrain_w = TERRAIN_RISK.get(plot.terrain, {})
        drain_w = DRAINAGE_RISK.get(plot.soil_drainage, {})
        # 合并曝光因子（按风险类型）
        exposure: dict[str, float] = {}
        for d in (terrain_w, drain_w):
            for k, v in d.items():
                exposure[k] = exposure.get(k, 1.0) * v

        rationale_bits = [f"地势={plot.terrain}", f"排水={plot.soil_drainage}"]
        if avg_soil is not None:
            rationale_bits.append(f"0-10cm 土壤湿度均值 {avg_soil:.2f}")
            if avg_soil >= wet_threshold:
                exposure["倒伏"] = exposure.get("倒伏", 1.0) * 1.2
                exposure["暴雨"] = exposure.get("暴雨", 1.0) * 1.1
                rationale_bits.append("（持续偏湿，根系松动）")

        if not exposure:
            return []

        max_e = max(exposure.values())
        level = RiskLevel.HIGH if max_e >= 1.5 else RiskLevel.MEDIUM if max_e >= 1.2 else RiskLevel.LOW
        return [RiskJudgment(
            agent_kind=self.agent_kind, plot_id=plot.plot_id,
            risk_type="地块脆弱性", level=level, confidence=0.75,
            rationale="；".join(rationale_bits)
                      + " → 暴露度 " + ", ".join(f"{k} x{v:.2f}" for k, v in exposure.items()),
            rule_refs=["wet.soil_moisture_min"],
            extras={"exposure": exposure, "avg_soil": avg_soil},
        )]


plot_analyst = PlotAnalyst()
