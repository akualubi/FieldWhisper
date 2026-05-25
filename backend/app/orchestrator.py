from __future__ import annotations

import asyncio
from typing import Optional

from .agents.analysts import ANALYSTS
from .agents.collector import collector
from .agents.decision import decision
from .agents.simulator import simulator
from .events import bus
from .models import Plot, RiskJudgment, Trajectory, Warning
from .storage.data_pool import pool


class PipelineResult:
    def __init__(
        self,
        plot: Plot,
        judgments: list[RiskJudgment],
        trajectories: list[Trajectory],
        warnings: list[Warning],
    ):
        self.plot = plot
        self.judgments = judgments
        self.trajectories = trajectories
        self.warnings = warnings

    def to_dict(self) -> dict:
        return {
            "plot": self.plot.model_dump(mode="json"),
            "judgments": [j.model_dump(mode="json") for j in self.judgments],
            "trajectories": [t.model_dump(mode="json") for t in self.trajectories],
            "warnings": [w.model_dump(mode="json") for w in self.warnings],
        }


async def run_pipeline(plot: Plot, collect_first: bool = True) -> PipelineResult:
    """完整链路：（Collect→）Analyst×N（并发）→ Simulator → Decision。"""
    await bus.publish("pipeline.start", {"plot_id": plot.plot_id})

    if collect_first:
        await collector.collect_for_plot(plot)

    # 5 个 Analyst 并行
    judgment_lists = await asyncio.gather(*[a.run(plot) for a in ANALYSTS])
    judgments: list[RiskJudgment] = [j for lst in judgment_lists for j in lst]

    trajs = await simulator.run(plot, judgments)
    warnings = await decision.run(plot, judgments, trajs)

    await bus.publish("pipeline.done", {
        "plot_id": plot.plot_id,
        "judgments": len(judgments),
        "trajectories": len(trajs),
        "warnings": len(warnings),
    })
    return PipelineResult(plot=plot, judgments=judgments, trajectories=trajs, warnings=warnings)


async def analyze_only(plot: Plot) -> PipelineResult:
    """跳过采集，直接基于 DataPool 现有数据跑分析（演讲注入后用）。"""
    return await run_pipeline(plot, collect_first=False)
