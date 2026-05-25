from __future__ import annotations

from abc import abstractmethod
from typing import Any

from ...models import DataItem, Plot, RiskJudgment
from ...storage.data_pool import pool
from ..base import Agent


class AnalystAgent(Agent):
    """Analyst 基类。每个领域 Analyst 只读自己关心的 DataItem.type。"""

    agent_kind: str = "analyst"     # weather / crop / plot / pest / sentiment
    subscribed_types: tuple[str, ...] = ()

    async def fetch_inputs(self, plot: Plot) -> list[DataItem]:
        items = await pool.query_data_items(
            plot_id=plot.plot_id,
            types=list(self.subscribed_types) if self.subscribed_types else None,
            limit=300,
        )
        return items

    async def run(self, plot: Plot) -> list[RiskJudgment]:
        assets = self.load_assets()
        await self.emit("analyst.start", {"kind": self.agent_kind, "plot_id": plot.plot_id})
        items = await self.fetch_inputs(plot)
        judgments = await self.analyze(plot, items, assets)
        for j in judgments:
            await pool.add_judgment(j)
            await self.emit("judgment", {
                "id": j.id, "kind": j.agent_kind, "plot_id": j.plot_id,
                "risk_type": j.risk_type, "level": j.level.value,
                "confidence": j.confidence, "rationale": j.rationale,
            })
        await self.emit("analyst.done", {
            "kind": self.agent_kind, "plot_id": plot.plot_id, "count": len(judgments),
        })
        return judgments

    @abstractmethod
    async def analyze(
        self,
        plot: Plot,
        items: list[DataItem],
        assets: dict[str, Any],
    ) -> list[RiskJudgment]:
        ...
