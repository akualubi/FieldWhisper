"""端到端冒烟测试：注入 seed scenario → 跑分析 → 出 Warning → Harness 进化。

直接运行：
    python -m backend.tests.smoke
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.agents.collector import collector
from backend.app.harness import harness
from backend.app.models import Feedback, OutcomeKind, Plot, RiskLevel
from backend.app.orchestrator import analyze_only
from backend.app.storage.data_pool import pool
from backend.app.storage.db import init_db
from backend.app.storage.knowledge import knowledge
from backend.app.storage.seed_loader import load_parcels


def _line(s=""):
    print("=" * 8, s)


SCENARIOS_TO_TEST = ["DEMO-LANCHANG-YU", "DEMO-WAN-FROST", "DEMO-HAIL"]


async def main():
    await init_db()
    # 从 seed 种 plots
    for raw in load_parcels():
        p = Plot.from_seed(raw)
        if not await pool.get_plot(p.plot_id):
            await pool.upsert_plot(p)

    _line("Step 1 · 跑全部 3 个 seed scenario")
    last_warning = None
    for scenario in SCENARIOS_TO_TEST:
        print(f"\n--- scenario: {scenario} ---")
        items = await collector.trigger_preset(scenario)
        plot_id = items[0].geo.plot_id
        print(f"注入 {len(items)} 条 DataItem → plot {plot_id}")
        plot = await pool.get_plot(plot_id)
        assert plot, f"plot {plot_id} 应已存在"
        result = await analyze_only(plot)
        print(f"  Judgments={len(result.judgments)} Trajectories={len(result.trajectories)} Warnings={len(result.warnings)}")
        for w in result.warnings:
            print(f"  [WARN] {w.headline}  peril={w.peril_code.value}  case={w.matched_history_case}  conf={w.confidence:.2f}")
            last_warning = w
        assert result.warnings, f"scenario {scenario} 应至少产出一条 Warning"

    _line("Step 2 · 切换到保险公司视角看 payload")
    from backend.app.agents.delivery import delivery
    w = last_warning
    plot = await pool.get_plot(w.plot_id)
    payload = delivery.render(w, customer="insurance", plot=plot)
    print(f"schema_version: {payload['schema_version']}")
    print(f"peril_code:     {payload['peril_code']}")
    print(f"risk_score:     {payload['risk_score']}")
    print(f"recommended_action: {payload['recommended_action']} ({payload['recommended_action_zh']})")

    _line("Step 3 · 模拟漏报反馈 → Harness 写回")
    before = knowledge.snapshot("weather")
    fb = Feedback(
        warning_id=w.id,
        outcome=OutcomeKind.UNDERESTIMATED,
        actual_level=RiskLevel.EXTREME if w.risk_level != RiskLevel.EXTREME else RiskLevel.EXTREME,
        actual_loss_pct=0.45,
        adopted=False,
        notes="实际灾情较预测更严重",
        reporter="coop:demo",
    )
    ev = await harness.run(w, fb)
    print(f"verdict={ev.verdict}  score={ev.score:.2f}  patches={len(ev.patches)}")
    for rc in ev.root_causes:
        print(f"  - 归因 {rc.agent_name}/{rc.asset}: {rc.reason[:60]}")
    after = knowledge.snapshot("weather")
    print(f"weather/rules.heat before={before['rules'].get('heat')}  after={after['rules'].get('heat')}")

    _line("DONE")


if __name__ == "__main__":
    asyncio.run(main())
