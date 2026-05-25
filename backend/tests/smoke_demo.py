"""演讲拖拽 demo 冒烟测试 —— 模拟用户把 4 种气象拖到 4 个省。

python -m backend.tests.smoke_demo
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.agents.collector import collector
from backend.app.agents.delivery import delivery
from backend.app.api.demo import _resolve_plot, _plot_to_province
from backend.app.demo import build_intent_items, resolve_province
from backend.app.llm import llm
from backend.app.models import Plot
from backend.app.orchestrator import analyze_only
from backend.app.storage.data_pool import pool
from backend.app.storage.db import init_db
from backend.app.storage.seed_loader import load_parcels


DROPS = [
    {"province": "山东", "weather": "暴雨", "intensity": "重"},
    {"province": "黑龙江", "weather": "暴雪", "intensity": "重"},
    {"province": "内蒙古", "weather": "沙尘暴", "intensity": "重"},
    {"province": "广东", "weather": "台风", "intensity": "重"},
    {"province": "河南", "weather": "高温", "intensity": "中"},
    {"province": "山西", "weather": "干旱", "intensity": "中"},
]


def _line(s=""):
    print("=" * 8, s)


async def main():
    await init_db()
    for raw in load_parcels():
        p = Plot.from_seed(raw)
        if not await pool.get_plot(p.plot_id):
            await pool.upsert_plot(p)

    _line(f"LLM: {llm.describe()}")

    _line(f"Step 1 · 模拟 {len(DROPS)} 次拖拽")
    for drop in DROPS:
        resolved = resolve_province(drop["province"])
        plot = await _resolve_plot(resolved, None)
        items = build_intent_items(drop["weather"], plot, drop["intensity"], 48)
        for it in items:
            await collector.inject(it)
        result = await analyze_only(plot)
        if result.warnings:
            top = max(result.warnings, key=lambda w: w.risk_level.numeric)
            print(f"  [{drop['province']:6}] 拖入 『{drop['weather']}·{drop['intensity']}』 "
                  f"→ {plot.plot_id}（{plot.crop}/{plot.stage_zh}）")
            print(f"     → {top.headline}  peril={top.peril_code.value}  case={top.matched_history_case}")
            print(f"     → action: {top.actions[0] if top.actions else '-'}")
        else:
            print(f"  [{drop['province']:6}] {drop['weather']}·{drop['intensity']} → 无 Warning ⚠️")

    _line("Step 2 · /api/demo/map 聚合视图")
    from backend.app.api.demo import get_map
    m = await get_map()
    print(f"  overview = {m['overview']}")
    for s in m["provinces"]:
        print(f"  [{s['province']:6}] {s['risk_level']:3}  perils={s['peril_codes']}")

    _line("Step 3 · 切换到保险公司视角看一条 payload")
    plots = await pool.list_plots()
    for p in plots:
        ws = await pool.query_warnings(plot_id=p.plot_id, limit=1)
        if ws:
            payload = delivery.render(ws[0], customer="insurance", plot=p)
            print(f"  plot={p.plot_id}  peril={payload['peril_code']}  score={payload['risk_score']}")
            print(f"    action={payload['recommended_action']}  ({payload['recommended_action_zh'][:60]})")
            break

    _line("DONE")


if __name__ == "__main__":
    asyncio.run(main())
