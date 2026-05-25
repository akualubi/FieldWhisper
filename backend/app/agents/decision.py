from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..llm import llm
from ..models import (
    PERIL_NAMES_ZH,
    PerilCode,
    Plot,
    RiskJudgment,
    RiskLevel,
    Trajectory,
    Warning,
    to_peril,
)
from ..storage.data_pool import pool
from .base import Agent


DEFAULT_ACTIONS: dict[str, list[str]] = {
    "高温热害": [
        "清晨/傍晚喷灌降温（避免正午灼伤）",
        "叶面喷施 0.3% 磷酸二氢钾增强抗逆",
        "对玉米抽雄期重点田块加强水分管理",
    ],
    "大风": [
        "对高秆作物提前查苗扶苗",
        "暂停喷药/灌水作业，防止次生倒伏",
    ],
    "倒伏": [
        "倒伏发生后 24h 内人工扶苗或机械辅助",
        "排查排水沟，避免根系长时间浸水",
        "叶面喷施芸苔素内酯，促进恢复",
    ],
    "暴雨": [
        "提前清沟理墒，确保排水顺畅",
        "对低洼地块准备应急排水",
    ],
    "烂场雨": [
        "T-3 天即触发抢收预案，协调附近烘干塔",
        "已收割粮食入库前用 80℃ 烘干至 13% 安全水分",
        "保险走『成熟期烂场雨附加险』预审",
    ],
    "晚霜冻": [
        "夜间地块灌跑马水增加比热（推荐 22:00 前完成）",
        "三叶期及以下苗弱地块覆盖薄膜或秸秆",
        "次日 9 点查苗，若有死苗及时补种短熟期品种",
    ],
    "干旱": [
        "优先保关键生育期地块",
        "灌水避开正午高温时段",
    ],
    "干热风": [
        "灌浆期叶面喷施磷酸二氢钾 + 适度补灌",
        "重点关注 14:00 风速与湿度组合",
    ],
    "条锈病": [
        "立即使用三唑酮 / 戊唑醇等三唑类药剂全田防治",
        "病点周边 50 米加密监测，3 天复查",
        "联系当地植保站确认是否上报",
    ],
    "草地贪夜蛾": [
        "夜间灯诱+性诱监测虫量",
        "幼虫 3 龄前使用氯虫苯甲酰胺",
    ],
    "冰雹": [
        "T-0 自动触发保险查勘启动（冰雹场景无法预防，重点是闭环效率）",
        "果园第一时间清理破损落果，避免病菌侵染",
        "已套袋果园检查袋子完好率",
    ],
}


def _bump(level: RiskLevel, delta: int) -> RiskLevel:
    n = max(0, min(4, level.numeric + delta))
    return [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.EXTREME][n]


def _extract_case_ids(text: str) -> list[str]:
    return re.findall(r"CASE-\d{3}", text or "")


def _match_history_case(experience_md: str, plot: Plot, risk_type: str) -> Optional[str]:
    """从经验文档中找最相关的 CASE 编号（粗匹配：作物 + 风险类型同时出现的段落）。"""
    if not experience_md:
        return None
    # 按 "## CASE-XXX" 切段
    sections = re.split(r"##\s+CASE-(\d{3})", experience_md)
    # sections = [head, id1, body1, id2, body2, ...]
    best, best_score = None, 0
    crop_keywords = {plot.crop, "玉米", "小麦", "苹果", "水稻", "稻"}
    for i in range(1, len(sections), 2):
        cid = f"CASE-{sections[i]}"
        body = sections[i + 1] if i + 1 < len(sections) else ""
        score = 0
        if risk_type and risk_type in body:
            score += 3
        if any(k and k in body for k in crop_keywords):
            score += 2
        if score > best_score:
            best, best_score = cid, score
    return best


def _onset_window(forecasts: list[RiskJudgment]) -> tuple[Optional[datetime], Optional[datetime]]:
    """从 evidence 时间戳推 onset 窗口（取最早 → 最晚）。"""
    ts_list = [j.ts for j in forecasts if j.ts]
    if not ts_list:
        return None, None
    start = min(ts_list)
    end = max(ts_list) + timedelta(days=1)
    return start, end


class DecisionAgent(Agent):
    """④ 决策 Agent —— Judgment + Trajectory → 结构化 Warning（含 peril_code）。"""

    name = "decision"

    async def run(
        self,
        plot: Plot,
        judgments: list[RiskJudgment],
        trajectories: list[Trajectory],
    ) -> list[Warning]:
        if not judgments:
            return []
        assets = self.load_assets()
        await self.emit("decision.start", {"plot_id": plot.plot_id})

        experience = (assets.get("experience") or "")
        # 把 seed 的 experience 也叠加进来（默认空，可以由 main.py 注入到 knowledge/decision/）
        from ..storage.seed_loader import load_experience_md
        experience_with_seed = experience + "\n\n" + load_experience_md()

        # 1) 聚合 by risk_type
        by_type: dict[str, list[RiskJudgment]] = {}
        for j in judgments:
            rt = j.risk_type.split("·")[-1] if "·" in j.risk_type else j.risk_type
            if j.agent_kind in ("crop", "plot"):  # 这两个不直接成 Warning
                continue
            by_type.setdefault(rt, []).append(j)
        traj_by_type = {t.risk_type: t for t in trajectories}

        crop_j = next((j for j in judgments if j.agent_kind == "crop"), None)
        plot_j = next((j for j in judgments if j.agent_kind == "plot"), None)

        # 2) 复合场景检测：高湿度 + 大风 + 关键生育期 → 升级为倒伏
        composite_warning = self._detect_composite(plot, judgments)

        warnings: list[Warning] = []
        seen_types: set[str] = set()

        if composite_warning:
            warnings.append(composite_warning)
            seen_types.add(composite_warning.risk_type)
            await pool.add_warning(composite_warning)
            await self._emit_warning(composite_warning)

        for rt, group in by_type.items():
            if rt in seen_types:
                continue
            level = max((j.level for j in group), key=lambda l: l.numeric)
            # 受 Crop / Plot 影响升级
            if crop_j:
                vmap = (crop_j.extras or {}).get("vuln_map") or {}
                if vmap.get(rt, 1.0) >= 1.3:
                    level = _bump(level, 1)
            if plot_j:
                emap = (plot_j.extras or {}).get("exposure") or {}
                if emap.get(rt, 1.0) >= 1.4:
                    level = _bump(level, 1)

            if level == RiskLevel.NONE:
                continue

            w = await self._build_warning(
                plot=plot,
                risk_type=rt,
                level=level,
                group=group,
                crop_j=crop_j,
                plot_j=plot_j,
                trajectory=traj_by_type.get(rt),
                assets=assets,
                experience_md=experience_with_seed,
            )
            await pool.add_warning(w)
            warnings.append(w)
            await self._emit_warning(w)

        await self.emit("decision.done", {"plot_id": plot.plot_id, "count": len(warnings)})
        return warnings

    def _detect_composite(self, plot: Plot, judgments: list[RiskJudgment]) -> Optional[Warning]:
        """玉米拔节/抽雄 + 土壤湿度高 + 大风 → 复合倒伏（doc.md 的核心 case）。"""
        if "玉米" not in plot.crop and "maize" not in plot.crop:
            return None
        stage_zh = plot.stage_zh
        if not any(k in stage_zh for k in ("拔节", "抽雄", "灌浆")):
            return None
        wind_j = next((j for j in judgments if j.agent_kind == "weather" and j.risk_type == "大风"), None)
        plot_j = next((j for j in judgments if j.agent_kind == "plot"), None)
        if not wind_j:
            return None
        avg_soil = (plot_j.extras or {}).get("avg_soil") if plot_j else None
        if avg_soil is None or avg_soil < 0.36:
            return None
        # 触发：直接出"倒伏 高/极高"
        level = RiskLevel.EXTREME if wind_j.level.numeric >= 3 else RiskLevel.HIGH
        return Warning(
            plot_id=plot.plot_id,
            crop=plot.crop,
            stage=plot.stage_zh or plot.stage.value,
            risk_level=level,
            risk_type="倒伏",
            peril_code=PerilCode.WIND_LODGING,
            peril_name_zh=PERIL_NAMES_ZH[PerilCode.WIND_LODGING.value],
            headline=f"{plot.crop}·倒伏 风险等级：{level.value}（复合场景）",
            actions=DEFAULT_ACTIONS["倒伏"],
            best_window="未来 48 小时",
            confidence=0.88,
            rationale=(
                f"{plot.crop} 处于 {stage_zh}，土壤湿度均值 {avg_soil:.2f} 偏高；"
                f"同时 {wind_j.rationale}。"
                "复合场景命中『拔节期 + 湿土壤 + 大风』经验规则（来自 doc.md 案例）。"
            ),
            evidence_judgment_ids=[j.id for j in judgments if j.agent_kind in ("weather", "plot")],
            data_source_ids=list({eid for j in judgments for eid in j.evidence})[:20],
        )

    async def _build_warning(
        self,
        plot: Plot,
        risk_type: str,
        level: RiskLevel,
        group: list[RiskJudgment],
        crop_j: Optional[RiskJudgment],
        plot_j: Optional[RiskJudgment],
        trajectory: Optional[Trajectory],
        assets: dict,
        experience_md: str,
    ) -> Warning:
        avg_conf = sum(j.confidence for j in group) / len(group)
        actions = self._pick_actions(risk_type, assets)
        peril = to_peril(risk_type)
        case_id = _match_history_case(experience_md, plot, risk_type)
        onset_start, onset_end = _onset_window(group)

        rationale_bits = [j.rationale for j in group if j.rationale]
        if crop_j and crop_j.rationale:
            rationale_bits.insert(0, crop_j.rationale)
        if plot_j and plot_j.rationale:
            rationale_bits.append(plot_j.rationale)
        if trajectory and trajectory.summary:
            rationale_bits.append(f"推演：{trajectory.summary}")
        rationale = " | ".join(rationale_bits)

        polished = await self._polish(plot, risk_type, level, rationale, actions, assets)
        if polished:
            rationale = polished.get("rationale", rationale)
            if isinstance(polished.get("actions"), list) and polished["actions"]:
                actions = polished["actions"]

        return Warning(
            plot_id=plot.plot_id,
            crop=plot.crop,
            stage=plot.stage_zh or plot.stage.value,
            risk_level=level,
            risk_type=risk_type,
            peril_code=peril,
            peril_name_zh=PERIL_NAMES_ZH.get(peril.value, risk_type),
            headline=f"{plot.crop}·{PERIL_NAMES_ZH.get(peril.value, risk_type)} 风险等级：{level.value}",
            actions=actions,
            best_window="未来 48 小时" if level.numeric >= 3 else "未来 72 小时",
            onset_window_start=onset_start,
            onset_window_end=onset_end,
            confidence=avg_conf,
            rationale=rationale,
            evidence_judgment_ids=[j.id for j in group],
            data_source_ids=list({eid for j in group for eid in j.evidence})[:20],
            trajectory_summary=trajectory.summary if trajectory else "",
            matched_history_case=case_id,
        )

    async def _emit_warning(self, w: Warning):
        await self.emit("warning", {
            "id": w.id,
            "plot_id": w.plot_id,
            "level": w.risk_level.value,
            "type": w.risk_type,
            "peril_code": w.peril_code.value,
            "headline": w.headline,
            "confidence": w.confidence,
            "matched_history_case": w.matched_history_case,
        })

    def _pick_actions(self, risk_type: str, assets: dict[str, Any]) -> list[str]:
        rules = assets.get("rules") or {}
        actions_map = rules.get("actions") or {}
        return actions_map.get(risk_type) or DEFAULT_ACTIONS.get(risk_type) or [
            f"加强对 {risk_type} 的田间监测，3 天内复查"
        ]

    async def _polish(
        self, plot: Plot, risk_type: str, level: RiskLevel,
        rationale: str, actions: list[str], assets: dict[str, Any],
    ) -> Optional[dict]:
        if not llm.available:
            return None
        prompt_md = assets.get("prompt") or ""
        exp_md = assets.get("experience") or ""
        system = (
            "你是穗安农业风险决策智能体，把分析结论转成农户能听懂、能马上做的话。"
            "输出 JSON：{\"rationale\": str, \"actions\": [str, ...]}。"
            "actions 必须可执行、有时间窗、有具体药剂或操作。"
            + (f"\n\n--- 角色提示 ---\n{prompt_md}" if prompt_md else "")
            + (f"\n\n--- 经验文档 ---\n{exp_md[:2000]}" if exp_md else "")
        )
        user = json.dumps({
            "plot": {"crop": plot.crop, "stage_zh": plot.stage_zh, "terrain": plot.terrain},
            "risk_type": risk_type, "level": level.value,
            "raw_rationale": rationale, "current_actions": actions,
        }, ensure_ascii=False)
        return await llm.complete_json(system, user, max_tokens=600)


decision = DecisionAgent()
