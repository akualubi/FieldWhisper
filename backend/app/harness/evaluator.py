from __future__ import annotations

from typing import Optional

from ..models import (
    AssetPatch,
    Evaluation,
    Feedback,
    OutcomeKind,
    RiskLevel,
    RootCause,
    Warning,
    RiskJudgment,
)
from ..storage.data_pool import pool


def _level_delta(predicted: RiskLevel, actual: Optional[RiskLevel]) -> int:
    if actual is None:
        return 0
    return actual.numeric - predicted.numeric


async def evaluate(warning: Warning, feedback: Feedback) -> Evaluation:
    """规则化评估 + 归因（带 LLM 也可以润色，但默认规则跑通）。"""
    delta = _level_delta(warning.risk_level, feedback.actual_level)

    verdict = feedback.outcome.value
    if feedback.outcome == OutcomeKind.UNKNOWN:
        if delta >= 1:
            verdict = OutcomeKind.UNDERESTIMATED.value
        elif delta <= -1:
            verdict = OutcomeKind.FALSE_POSITIVE.value
        else:
            verdict = OutcomeKind.HIT.value

    # 评分（高越好）
    if verdict == OutcomeKind.HIT.value:
        score = 0.9 if feedback.adopted else 0.7
    elif verdict == OutcomeKind.UNDERESTIMATED.value:
        score = max(0.0, 0.4 - 0.1 * delta)
    elif verdict == OutcomeKind.FALSE_POSITIVE.value:
        score = 0.3
    elif verdict == OutcomeKind.NOT_ACTIONABLE.value:
        score = 0.4
    else:
        score = 0.5

    actionable = 0.9 if feedback.adopted else 0.5
    if verdict == OutcomeKind.NOT_ACTIONABLE.value:
        actionable = 0.2

    # 归因 + Patch（核心：把"哪里偏了"映射到具体 Agent 的具体资产）
    root_causes: list[RootCause] = []
    patches: list[AssetPatch] = []

    judgments = await pool.query_judgments(warning.plot_id, limit=50)
    j_for_type = [j for j in judgments if j.risk_type.endswith(warning.risk_type) or warning.risk_type in j.risk_type]

    if verdict == OutcomeKind.UNDERESTIMATED.value:
        # 漏报 → 调紧 Analyst 阈值 + 调高 crop/plot 权重 + 写经验
        weather_j = next((j for j in j_for_type if j.agent_kind == "weather"), None)
        crop_j = next((j for j in judgments if j.agent_kind == "crop"), None)
        plot_j = next((j for j in judgments if j.agent_kind == "plot"), None)

        if weather_j and warning.risk_type in {"高温热害", "大风", "暴雨", "干旱"}:
            root_causes.append(RootCause(
                agent_name="weather", asset="rules.yaml",
                reason=f"{warning.risk_type} 实际比预测更严重 → 阈值偏宽，需调紧",
            ))
            patches.append(_patch_weather_tighten(warning.risk_type))

        if crop_j and warning.risk_type in {"高温热害", "倒伏", "条锈病"}:
            stage = (crop_j.extras or {}).get("stage", crop_j.extras.get("stage") if crop_j.extras else "")
            root_causes.append(RootCause(
                agent_name="crop", asset="weights.json",
                reason=f"{warning.crop} {stage} 期对 {warning.risk_type} 的脆弱度权重不足",
            ))
            patches.append(AssetPatch(
                agent_name="crop", asset="weights.json", op="update_json",
                payload={"path": ["vulnerability", warning.crop, stage or "jointing", warning.risk_type], "value": 1.5},
                note=f"漏报修正：{warning.crop}·{stage}·{warning.risk_type} 1.0 → 1.5",
            ))

        if plot_j:
            root_causes.append(RootCause(
                agent_name="plot", asset="rules.yaml",
                reason="地块脆弱性触发阈值偏宽（土壤偏湿判定迟）",
            ))
            patches.append(AssetPatch(
                agent_name="plot", asset="rules.yaml", op="update_yaml",
                payload={"path": ["wet", "soil_moisture_min"], "value": 0.32},
                note="漏报修正：偏湿阈值 0.38 → 0.32",
            ))

        # Decision 经验文档：追加复合场景
        root_causes.append(RootCause(
            agent_name="decision", asset="experience.md",
            reason="Decision 未识别复合场景（生育期+地块+气象的叠加）",
        ))
        patches.append(AssetPatch(
            agent_name="decision", asset="experience.md", op="append_md",
            payload={
                "section": f"漏报案例：{warning.crop}·{warning.risk_type}·{warning.ts.date()}",
                "content": (
                    f"- 预测等级：{warning.risk_level.value}，实际：{feedback.actual_level.value if feedback.actual_level else '?'}\n"
                    f"- 反馈备注：{feedback.notes or '（无）'}\n"
                    f"- 教训：当 {warning.crop} 处于关键生育期且地块脆弱时，**单领域中风险即应升级为高**。\n"
                    f"- 下次见到类似组合时直接判定为高风险并触发 48h 行动窗口。"
                ),
            },
            note="经验文档追加复合场景案例",
        ))

    elif verdict == OutcomeKind.FALSE_POSITIVE.value:
        # 误报 → 放宽阈值
        weather_j = next((j for j in j_for_type if j.agent_kind == "weather"), None)
        if weather_j:
            root_causes.append(RootCause(
                agent_name="weather", asset="rules.yaml",
                reason=f"{warning.risk_type} 实际未发生 → 阈值偏紧或单点触发",
            ))
            patches.append(_patch_weather_relax(warning.risk_type))

    elif verdict == OutcomeKind.NOT_ACTIONABLE.value:
        root_causes.append(RootCause(
            agent_name="decision", asset="experience.md",
            reason="建议过于模糊或不可操作",
        ))
        patches.append(AssetPatch(
            agent_name="decision", asset="experience.md", op="append_md",
            payload={
                "section": f"不可执行反馈：{warning.risk_type}·{warning.ts.date()}",
                "content": (
                    f"- 农户/B 端反馈：『{feedback.notes or '（建议无法落地）'}』\n"
                    f"- 修正方向：所有 {warning.risk_type} 建议必须含 (1) 具体药剂/操作 (2) 时间窗口 (3) 复查节点。"
                ),
            },
            note="不可执行 → 提示规范更严格",
        ))

    summary = (
        f"评估结果：{verdict}（评分 {score:.2f}）。"
        f"归因 {len(root_causes)} 处，生成 {len(patches)} 条资产 patch。"
    )

    ev = Evaluation(
        warning_id=warning.id,
        feedback_id=feedback.id,
        score=score,
        verdict=verdict,
        actionable_score=actionable,
        root_causes=root_causes,
        patches=patches,
        summary=summary,
    )
    return ev


def _patch_weather_tighten(risk_type: str) -> AssetPatch:
    if risk_type == "高温热害":
        return AssetPatch(
            agent_name="weather", asset="rules.yaml", op="update_yaml",
            payload={"path": ["heat", "temp_c"], "value": 34.0},
            note="高温阈值 35 → 34",
        )
    if risk_type == "大风":
        return AssetPatch(
            agent_name="weather", asset="rules.yaml", op="update_yaml",
            payload={"path": ["wind", "speed_ms"], "value": 12.0},
            note="大风阈值 13.8 → 12.0（约 6 级提前触发）",
        )
    if risk_type == "暴雨":
        return AssetPatch(
            agent_name="weather", asset="rules.yaml", op="update_yaml",
            payload={"path": ["rain", "mm_24h"], "value": 40.0},
            note="暴雨阈值 50 → 40 mm/24h",
        )
    if risk_type == "干旱":
        return AssetPatch(
            agent_name="weather", asset="rules.yaml", op="update_yaml",
            payload={"path": ["drought", "soil_moisture_min"], "value": 0.20},
            note="干旱土壤湿度阈值 0.18 → 0.20",
        )
    return AssetPatch(
        agent_name="weather", asset="rules.yaml", op="update_yaml",
        payload={"path": ["misc", "tighten"], "value": True},
        note="泛化收紧标记",
    )


def _patch_weather_relax(risk_type: str) -> AssetPatch:
    if risk_type == "高温热害":
        return AssetPatch(
            agent_name="weather", asset="rules.yaml", op="update_yaml",
            payload={"path": ["heat", "consec_hours"], "value": 8},
            note="高温要求 6h → 8h 才触发",
        )
    if risk_type == "大风":
        return AssetPatch(
            agent_name="weather", asset="rules.yaml", op="update_yaml",
            payload={"path": ["wind", "consec_hours"], "value": 4},
            note="大风需 4h 持续才触发",
        )
    return AssetPatch(
        agent_name="weather", asset="rules.yaml", op="update_yaml",
        payload={"path": ["misc", "relax"], "value": True},
        note="泛化放宽标记",
    )
