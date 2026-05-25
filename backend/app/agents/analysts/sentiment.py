from __future__ import annotations

from typing import Any

from ...models import DataItem, Plot, RiskJudgment, RiskLevel
from .base import AnalystAgent


# 简化的关键词 → 异常类型映射
SIGNAL_KEYWORDS = {
    "倒伏": ["大风", "倒了", "倒伏", "刮倒"],
    "涝害": ["地里都是水", "积水", "排不出", "涝"],
    "干旱": ["天旱", "缺水", "干裂"],
    "病虫害": ["发黄", "病", "虫", "粉状", "斑点", "夏孢子"],
    "倒春寒/低温": ["霜", "冻", "冷害"],
}


class SentimentAnalyst(AnalystAgent):
    name = "sentiment"
    agent_kind = "sentiment"
    subscribed_types = ("post",)

    async def analyze(
        self,
        plot: Plot,
        items: list[DataItem],
        assets: dict[str, Any],
    ) -> list[RiskJudgment]:
        rules = assets.get("rules") or {}
        kw_map = rules.get("signal_keywords") or SIGNAL_KEYWORDS
        weights = assets.get("weights") or {}
        base_threshold = (weights.get("trigger") or {}).get("min_hits", 1)

        judgments: list[RiskJudgment] = []
        signals: dict[str, dict] = {}

        for it in items:
            text = (it.payload.get("content") or "")
            for kind, kws in kw_map.items():
                hits = [k for k in kws if k in text]
                if hits:
                    s = signals.setdefault(kind, {"hits": 0, "evidence": [], "quotes": []})
                    s["hits"] += len(hits)
                    s["evidence"].append(it.id)
                    s["quotes"].append(text[:60])

        for kind, info in signals.items():
            if info["hits"] < base_threshold:
                continue
            level = RiskLevel.MEDIUM if info["hits"] >= 2 else RiskLevel.LOW
            judgments.append(RiskJudgment(
                agent_kind=self.agent_kind, plot_id=plot.plot_id,
                risk_type=f"舆情信号·{kind}",
                level=level,
                confidence=min(0.85, 0.4 + 0.1 * info["hits"]),
                rationale="农户/群聊出现关键词："
                          + "；".join(f'"{q}"' for q in info["quotes"][:2]),
                evidence=info["evidence"],
                rule_refs=["signal_keywords", "trigger.min_hits"],
            ))
        return judgments


sentiment_analyst = SentimentAnalyst()
