from __future__ import annotations

from ..models import AssetPatch
from ..storage.data_pool import pool
from ..storage.knowledge import knowledge


async def apply_patches(patches: list[AssetPatch]) -> list[dict]:
    """把 Evaluator 给出的 AssetPatch 真正写到磁盘 + 留 audit trail。"""
    results = []
    for p in patches:
        before, after = "", ""
        try:
            if p.op == "append_md":
                before, after = knowledge.append_experience(
                    p.agent_name,
                    p.payload.get("section", "Untitled"),
                    p.payload.get("content", ""),
                )
            elif p.op == "update_yaml":
                before, after = knowledge.update_rules(
                    p.agent_name,
                    p.payload["path"],
                    p.payload["value"],
                )
            elif p.op == "update_json":
                before, after = knowledge.update_weights(
                    p.agent_name,
                    p.payload["path"],
                    p.payload["value"],
                )
            else:
                results.append({"patch_id": p.id, "ok": False, "error": f"unknown op {p.op}"})
                continue

            await pool.record_asset_change(
                agent_name=p.agent_name,
                asset=p.asset,
                op=p.op,
                note=p.note,
                before=before,
                after=after,
            )
            results.append({"patch_id": p.id, "ok": True, "agent": p.agent_name, "asset": p.asset, "note": p.note})
        except Exception as e:
            results.append({"patch_id": p.id, "ok": False, "error": str(e)})
    return results
