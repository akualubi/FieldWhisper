from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from ..models import PERIL_NAMES_ZH, Plot, Warning
from .base import Agent


CustomerKind = Literal["insurance", "coop", "gov", "grain", "agroinput"]

SCHEMA_VERSION = "suian.delivery.insurance.v1"
MODEL_VERSION = "suian-decision-2026.05.0"


def _mask_name(name: str | None) -> str:
    if not name:
        return "**"
    return name[0] + "**"


def _level_to_score(w: Warning) -> float:
    return round(min(1.0, 0.15 * w.risk_level.numeric + 0.5 * w.confidence), 3)


def _onset_window(w: Warning) -> dict[str, str]:
    if w.onset_window_start and w.onset_window_end:
        return {
            "start": w.onset_window_start.isoformat(),
            "end": w.onset_window_end.isoformat(),
        }
    now = datetime.now(timezone.utc)
    return {"start": now.isoformat(), "end": (now.replace(microsecond=0)).isoformat()}


class DeliveryAgent(Agent):
    """⑤ 推送 Agent —— 按 B 端客户类型适配输出。

    insurance 渲染对齐 seed/mock/insurance_payload.json 的 schema。
    """

    name = "delivery"

    def render(
        self,
        warning: Warning,
        customer: CustomerKind = "coop",
        plot: Optional[Plot] = None,
    ) -> dict[str, Any]:
        if customer == "insurance":
            return self._render_insurance(warning, plot)
        if customer == "coop":
            return self._render_coop(warning)
        if customer == "gov":
            return self._render_gov(warning)
        if customer == "grain":
            return self._render_grain(warning)
        if customer == "agroinput":
            return self._render_agroinput(warning)
        return warning.model_dump(mode="json")

    def _render_insurance(self, w: Warning, plot: Optional[Plot]) -> dict[str, Any]:
        peril_zh = PERIL_NAMES_ZH.get(w.peril_code.value, w.risk_type)
        intent_id = f"CI-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{uuid4().hex[:6].upper()}"

        rec_action = "AUTO_CLAIM_INITIATED" if w.risk_level.numeric >= 4 else (
            "PRE_CLAIM_PREP" if w.risk_level.numeric >= 3 else "MONITOR_ONLY"
        )
        rec_zh = {
            "AUTO_CLAIM_INITIATED": "T-0 立即触发现场查勘 + 集中报案通道开启",
            "PRE_CLAIM_PREP":       "建议进入查勘待命：通知投保人、协调资源、T+1 启动现场查勘",
            "MONITOR_ONLY":         "暂不触发查勘，建议监测 T+1 实际气象/苗情",
        }[rec_action]

        return {
            "schema_version": SCHEMA_VERSION,
            "claim_intent_id": intent_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "policy_no": (plot.policy_no if plot else None) or "POLICY-DEMO-0000",
            "insured_party": {
                "user_id": (plot.owner_id if plot else None) or "U-DEMO",
                "name_masked": _mask_name(plot.name if plot else None),
                "id_card_masked": "*" * 18,
            },
            "parcel": {
                "id": w.plot_id,
                "lat": (plot.lat if plot else None),
                "lon": (plot.lon if plot else None),
                "area_mu": (plot.area_mu if plot else None),
                "crop": w.crop,
                "growth_stage": w.stage,
            },
            "peril_code": w.peril_code.value,
            "peril_name_zh": peril_zh,
            "risk_level": w.risk_level.value,
            "confidence": round(w.confidence, 3),
            "risk_score": _level_to_score(w),
            "onset_window": _onset_window(w),
            "evidence": {
                "weather_summary": w.rationale[:240],
                "weather_provider": "open-meteo",
                "ndvi_anomaly": None,
                "photo_urls": [],
                "matched_history_case": w.matched_history_case,
            },
            "recommended_action": rec_action,
            "recommended_action_zh": rec_zh,
            "trajectory_summary": w.trajectory_summary,
            "model_version": MODEL_VERSION,
            "signed_by": "agent.decision@suian",
        }

    def _render_coop(self, w: Warning) -> dict[str, Any]:
        sms = (
            f"【穗安预警】{w.crop}地块 {w.plot_id} "
            f"{PERIL_NAMES_ZH.get(w.peril_code.value, w.risk_type)} "
            f"风险{w.risk_level.value}。建议：{w.actions[0] if w.actions else '加强监测'}。"
            f"窗口：{w.best_window}。"
        )
        return {
            "channel": "sms+console",
            "sms": sms,
            "console_payload": w.model_dump(mode="json"),
        }

    def _render_gov(self, w: Warning) -> dict[str, Any]:
        return {
            "channel": "pdf_brief",
            "title": f"农情简报 · {w.crop} · {PERIL_NAMES_ZH.get(w.peril_code.value, w.risk_type)}",
            "summary": w.headline,
            "rationale": w.rationale,
            "actions": w.actions,
            "matched_history_case": w.matched_history_case,
            "evidence_count": len(w.evidence_judgment_ids),
        }

    def _render_grain(self, w: Warning) -> dict[str, Any]:
        return {
            "channel": "quality_monthly",
            "key_signal": w.risk_type,
            "peril_code": w.peril_code.value,
            "expected_impact": w.risk_level.value,
            "trajectory_summary": w.trajectory_summary,
        }

    def _render_agroinput(self, w: Warning) -> dict[str, Any]:
        return {
            "channel": "stocking_signal",
            "region_hint": w.plot_id[:5],
            "risk_type": w.risk_type,
            "peril_code": w.peril_code.value,
            "level": w.risk_level.value,
            "recommended_inputs": w.actions[:3],
        }


delivery = DeliveryAgent()
