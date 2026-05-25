from __future__ import annotations

from typing import Any

from ...models import DataItem, Plot, RiskJudgment, RiskLevel
from .base import AnalystAgent


class CropAnalyst(AnalystAgent):
    """按 plot.stage_zh 做模糊关键词匹配查 weights.vulnerability。"""

    name = "crop"
    agent_kind = "crop"
    subscribed_types = ("crop_stage",)

    async def analyze(
        self,
        plot: Plot,
        items: list[DataItem],
        assets: dict[str, Any],
    ) -> list[RiskJudgment]:
        weights = assets.get("weights") or {}
        vuln_root: dict = weights.get("vulnerability") or {}

        # 优先 DataItem.crop_stage 覆盖，再退回 plot
        stage_zh = plot.stage_zh or plot.stage.value
        for it in items:
            if it.type == "crop_stage":
                stage_zh = it.payload.get("stage_zh") or it.payload.get("stage") or stage_zh

        crop_map = vuln_root.get(plot.crop) or {}
        merged: dict[str, float] = {}
        matched_keys: list[str] = []
        for kw, risks in crop_map.items():
            if kw in stage_zh:
                matched_keys.append(kw)
                for rt, w in (risks or {}).items():
                    merged[rt] = max(merged.get(rt, 0.0), float(w))

        if not merged:
            return [RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type="生育期脆弱度", level=RiskLevel.LOW,
                confidence=0.4,
                rationale=f"{plot.crop} 当前生育期『{stage_zh}』：无显著敏感性记录",
                rule_refs=["weights.vulnerability"],
                extras={"stage_zh": stage_zh, "vuln_map": {}},
            )]

        max_factor = max(merged.values())
        top = sorted(merged.items(), key=lambda kv: -kv[1])[:3]
        rationale = (
            f"{plot.crop} 处于『{stage_zh}』（命中关键期：{','.join(matched_keys)}），对 "
            + "、".join(f"{rt}(x{w:.1f})" for rt, w in top)
            + " 敏感"
        )
        level = RiskLevel.HIGH if max_factor >= 1.3 else RiskLevel.MEDIUM if max_factor >= 1.1 else RiskLevel.LOW
        return [RiskJudgment(
            agent_kind=self.agent_kind, plot_id=plot.plot_id,
            risk_type="生育期脆弱度", level=level, confidence=0.85,
            rationale=rationale,
            rule_refs=["weights.vulnerability"],
            extras={"stage_zh": stage_zh, "vuln_map": merged, "matched": matched_keys},
        )]


crop_analyst = CropAnalyst()
