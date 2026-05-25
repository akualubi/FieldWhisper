from __future__ import annotations

from ...config import settings
from ...models import DataItem, Plot
from ...storage.data_pool import pool
from ...storage.seed_loader import (
    load_bulletins,
    load_ndvi,
    load_scenarios,
)
from ..base import Agent
from . import adapters
from .presets import parcel_extra, scenario_to_items


class CollectorAgent(Agent):
    """① 采集 Agent —— 只搬不判。"""

    name = "collector"

    async def collect_for_plot(self, plot: Plot) -> list[DataItem]:
        """从真实/seed/mock 源拉一遍数据。"""
        items: list[DataItem] = []

        # 1) 真实气象（Open-Meteo 零 key）
        await self.emit("collector.start", {"source": "open_meteo", "plot_id": plot.plot_id})
        wx = await adapters.fetch_open_meteo_forecast(plot.plot_id, plot.lat, plot.lon, hours=72)
        items.extend(wx)
        await self.emit("collector.done", {
            "source": "open_meteo", "plot_id": plot.plot_id, "count": len(wx),
        })

        # 2) NDVI (从 seed 取真实预设；落不到 seed 时退回 mock 时序)
        items.extend(self._ndvi_for(plot))

        # 3) 病虫情报通报（按 seed 的 5 条全量入池，让 Pest Analyst 自己匹配）
        for b in load_bulletins():
            items.append(DataItem(
                source="seed_bulletin",
                type="notice",
                geo=adapters._geo(plot),
                payload={
                    "title": b["title"],
                    "body": b["body"],
                    "pest": adapters._guess_pest(b["title"], b["body"]),
                    "severity": "中等",
                },
            ))

        await self._persist(items)
        return items

    def _ndvi_for(self, plot: Plot) -> list[DataItem]:
        series = load_ndvi().get(plot.plot_id)
        if series:
            return [
                DataItem(
                    source="seed_ndvi",
                    type="ndvi",
                    geo=adapters._geo(plot),
                    payload=s,
                )
                for s in series
            ]
        return adapters.mock_ndvi_series(plot.plot_id, plot.lat, plot.lon)

    async def inject(self, item: DataItem) -> DataItem:
        """演示用：直接注入一条 DataItem 到 DataPool。"""
        if not item.source:
            item.source = "manual_injection"
        if not item.injected_by:
            item.injected_by = "manual"
        await pool.add_data_item(item)
        await self.emit("data_item", {
            "id": item.id, "source": item.source, "type": item.type,
            "plot_id": item.geo.plot_id if item.geo else None,
            "injected_by": item.injected_by,
        })
        return item

    async def trigger_preset(self, scenario_id: str, plot: Plot | None = None) -> list[DataItem]:
        """运行 seed/manual_injection_scenarios.json 中的一条 scenario。

        如 scenario 自带 parcel_extra（如冰雹场景的临时果园）会自动 upsert。
        若 plot 未传，则按 scenario.inject.parcel_id 查/造。"""

        # 处理临时地块
        extra = parcel_extra(scenario_id)
        if extra and not await pool.get_plot(extra["id"]):
            tmp_plot = Plot.from_seed({
                **extra,
                "area_mu": extra.get("area_mu", 50),
            })
            await pool.upsert_plot(tmp_plot)

        if plot is None:
            sc = next((s for s in load_scenarios() if s["id"] == scenario_id), None)
            if not sc:
                raise KeyError(scenario_id)
            pid = sc["inject"]["parcel_id"]
            plot = await pool.get_plot(pid)
            if not plot:
                raise KeyError(f"plot {pid} not found (scenario {scenario_id})")

        await self.emit("preset.start", {"preset": scenario_id, "plot_id": plot.plot_id})
        items = scenario_to_items(scenario_id, plot)
        await self._persist(items)
        await self.emit("preset.done", {
            "preset": scenario_id, "plot_id": plot.plot_id, "count": len(items),
        })
        return items

    async def _persist(self, items: list[DataItem]) -> None:
        for it in items:
            await pool.add_data_item(it)
            await self.emit("data_item", {
                "id": it.id, "source": it.source, "type": it.type,
                "plot_id": it.geo.plot_id if it.geo else None,
                "injected_by": it.injected_by,
            })


collector = CollectorAgent()
