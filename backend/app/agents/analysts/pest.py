from __future__ import annotations

from typing import Any

from ...models import DataItem, Plot, RiskJudgment, RiskLevel
from .base import AnalystAgent


class PestAnalyst(AnalystAgent):
    name = "pest"
    agent_kind = "pest"
    subscribed_types = ("notice", "image", "post")

    async def analyze(
        self,
        plot: Plot,
        items: list[DataItem],
        assets: dict[str, Any],
    ) -> list[RiskJudgment]:
        rules = assets.get("rules") or {}
        crop_pests = (rules.get("crop_pests") or {}).get(plot.crop, [])
        # 退化：用 keyword 简单匹配
        notices = [i for i in items if i.type == "notice"]
        images = [i for i in items if i.type == "image"]
        posts = [i for i in items if i.type == "post"]

        signals: dict[str, dict] = {}  # pest_name -> {level_score, sources}

        for it in notices:
            pest = it.payload.get("pest")
            sev = it.payload.get("severity", "")
            if pest:
                add = 2 if "重" in sev else 1
                s = signals.setdefault(pest, {"score": 0, "evidence": []})
                s["score"] += add
                s["evidence"].append(it.id)

        for it in images:
            pest = it.payload.get("candidate_disease") or it.payload.get("pest")
            conf = float(it.payload.get("confidence") or 0.5)
            if pest:
                s = signals.setdefault(pest, {"score": 0, "evidence": []})
                s["score"] += 1 if conf < 0.7 else 2
                s["evidence"].append(it.id)

        # 农户帖子里出现的关键词模糊命中
        keywords = {p: p for p in (crop_pests or [
            "条锈病", "叶锈病", "草地贪夜蛾", "大斑病", "稻瘟病", "蚜虫", "二化螟", "白粉病"
        ])}
        for it in posts:
            content = it.payload.get("content", "")
            for k, pest in keywords.items():
                if k in content:
                    s = signals.setdefault(pest, {"score": 0, "evidence": []})
                    s["score"] += 1
                    s["evidence"].append(it.id)

        judgments: list[RiskJudgment] = []
        for pest, info in signals.items():
            sc = info["score"]
            level = (
                RiskLevel.HIGH if sc >= 4 else
                RiskLevel.MEDIUM if sc >= 2 else
                RiskLevel.LOW
            )
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type=pest, level=level,
                confidence=min(0.9, 0.4 + 0.15 * sc),
                rationale=f"综合通报/图像/舆情 {len(info['evidence'])} 条线索 → 累计信号 {sc}",
                evidence=info["evidence"],
                rule_refs=["crop_pests"],
            ))
        return judgments


pest_analyst = PestAnalyst()
