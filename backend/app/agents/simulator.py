from __future__ import annotations

from typing import Any

from ..models import Plot, RiskJudgment, RiskLevel, Trajectory, TrajectoryPoint
from .base import Agent


def _bump(level: RiskLevel, delta: int) -> RiskLevel:
    n = max(0, min(4, level.numeric + delta))
    return [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.EXTREME][n]


class SimulatorAgent(Agent):
    """③ 推演 Agent —— 综合所有 Judgment 推 24/48/72h 演化轨迹。"""

    name = "simulator"

    async def run(self, plot: Plot, judgments: list[RiskJudgment]) -> list[Trajectory]:
        if not judgments:
            return []
        assets = self.load_assets()
        await self.emit("simulator.start", {"plot_id": plot.plot_id, "judgments": len(judgments)})

        rules = assets.get("rules") or {}
        decay_h24 = float((rules.get("baseline_growth") or {}).get("h24", 0.0))    # 不干预增量
        decay_h48 = float((rules.get("baseline_growth") or {}).get("h48", 1.0))
        decay_h72 = float((rules.get("baseline_growth") or {}).get("h72", 1.0))
        mitigation = float((rules.get("mitigation") or {}).get("level_delta", -1.0))

        # 按 risk_type 聚合：取最高级别 + 平均置信度
        agg: dict[str, dict] = {}
        for j in judgments:
            # 把"舆情信号·涝害"等映射成"暴雨/涝害"的根类型
            rt = j.risk_type.split("·")[-1] if "·" in j.risk_type else j.risk_type
            slot = agg.setdefault(rt, {"max_level": j.level, "judgments": [], "conf": []})
            if j.level.numeric > slot["max_level"].numeric:
                slot["max_level"] = j.level
            slot["judgments"].append(j.id)
            slot["conf"].append(j.confidence)

        # crop / plot vulnerability bump
        bump_table: dict[str, int] = {}
        for j in judgments:
            if j.agent_kind == "crop":
                vuln = (j.extras or {}).get("vuln_map") or {}
                for rt, w in vuln.items():
                    if w >= 1.3:
                        bump_table[rt] = max(bump_table.get(rt, 0), 1)
            if j.agent_kind == "plot":
                exposure = (j.extras or {}).get("exposure") or {}
                for rt, w in exposure.items():
                    if w >= 1.4:
                        bump_table[rt] = max(bump_table.get(rt, 0), 1)

        trajs: list[Trajectory] = []
        for rt, info in agg.items():
            base = info["max_level"]
            bump = bump_table.get(rt, 0)

            def _series(start_delta: int) -> list[TrajectoryPoint]:
                lv24 = _bump(base, start_delta + int(decay_h24))
                lv48 = _bump(base, start_delta + int(decay_h48) + bump)
                lv72 = _bump(base, start_delta + int(decay_h72) + bump)
                return [
                    TrajectoryPoint(horizon_hours=24, level=lv24, probability=min(0.95, 0.4 + 0.1 * lv24.numeric)),
                    TrajectoryPoint(horizon_hours=48, level=lv48, probability=min(0.95, 0.4 + 0.12 * lv48.numeric)),
                    TrajectoryPoint(horizon_hours=72, level=lv72, probability=min(0.95, 0.4 + 0.12 * lv72.numeric)),
                ]

            baseline = _series(0)
            mitigated = _series(int(mitigation))
            traj = Trajectory(
                plot_id=plot.plot_id,
                risk_type=rt,
                baseline=baseline,
                mitigated=mitigated,
                key_drivers=info["judgments"],
                summary=(
                    f"不干预：48h 后 {baseline[1].level.value} "
                    f"(p={baseline[1].probability:.2f})；"
                    f"采纳建议：48h 后 {mitigated[1].level.value} "
                    f"(p={mitigated[1].probability:.2f})"
                ),
            )
            trajs.append(traj)
            await self.emit("trajectory", {
                "plot_id": plot.plot_id, "risk_type": rt,
                "baseline_48h": baseline[1].level.value,
                "mitigated_48h": mitigated[1].level.value,
            })

        await self.emit("simulator.done", {"plot_id": plot.plot_id, "count": len(trajs)})
        return trajs


simulator = SimulatorAgent()
