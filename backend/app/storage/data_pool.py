from __future__ import annotations

import json
from typing import Optional

from ..models import (
    DataItem,
    Plot,
    RiskJudgment,
    Warning,
    Feedback,
    Evaluation,
)
from .db import get_conn


class DataPool:
    """穗安统一持久化层 —— 所有 Agent 通过它读写。

    所有结构化对象用 JSON 整体存到 data 列；索引列方便筛选。
    """

    # ---------- Plot ----------
    async def upsert_plot(self, plot: Plot) -> None:
        async with get_conn() as db:
            await db.execute(
                "INSERT OR REPLACE INTO plots (plot_id, data) VALUES (?, ?)",
                (plot.plot_id, plot.model_dump_json()),
            )
            await db.commit()

    async def get_plot(self, plot_id: str) -> Optional[Plot]:
        async with get_conn() as db:
            async with db.execute(
                "SELECT data FROM plots WHERE plot_id = ?", (plot_id,)
            ) as cur:
                row = await cur.fetchone()
        return Plot.model_validate_json(row[0]) if row else None

    async def list_plots(self) -> list[Plot]:
        async with get_conn() as db:
            async with db.execute("SELECT data FROM plots") as cur:
                rows = await cur.fetchall()
        return [Plot.model_validate_json(r[0]) for r in rows]

    # ---------- DataItem ----------
    async def add_data_item(self, item: DataItem) -> None:
        async with get_conn() as db:
            await db.execute(
                "INSERT OR REPLACE INTO data_items (id, source, type, ts, plot_id, data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.id,
                    item.source,
                    item.type,
                    item.ts.isoformat(),
                    item.geo.plot_id if item.geo else None,
                    item.model_dump_json(),
                ),
            )
            await db.commit()

    async def query_data_items(
        self,
        plot_id: Optional[str] = None,
        types: Optional[list[str]] = None,
        limit: int = 200,
    ) -> list[DataItem]:
        clauses, args = [], []
        if plot_id:
            clauses.append("plot_id = ?")
            args.append(plot_id)
        if types:
            placeholders = ",".join("?" * len(types))
            clauses.append(f"type IN ({placeholders})")
            args.extend(types)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT data FROM data_items {where} ORDER BY ts DESC LIMIT ?"
        args.append(limit)
        async with get_conn() as db:
            async with db.execute(sql, args) as cur:
                rows = await cur.fetchall()
        return [DataItem.model_validate_json(r[0]) for r in rows]

    # ---------- Judgment ----------
    async def add_judgment(self, j: RiskJudgment) -> None:
        async with get_conn() as db:
            await db.execute(
                "INSERT OR REPLACE INTO judgments (id, plot_id, agent, risk_type, level, ts, data) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    j.id,
                    j.plot_id,
                    j.agent_kind,
                    j.risk_type,
                    j.level.value,
                    j.ts.isoformat(),
                    j.model_dump_json(),
                ),
            )
            await db.commit()

    async def query_judgments(self, plot_id: str, limit: int = 50) -> list[RiskJudgment]:
        async with get_conn() as db:
            async with db.execute(
                "SELECT data FROM judgments WHERE plot_id = ? ORDER BY ts DESC LIMIT ?",
                (plot_id, limit),
            ) as cur:
                rows = await cur.fetchall()
        return [RiskJudgment.model_validate_json(r[0]) for r in rows]

    # ---------- Warning ----------
    async def add_warning(self, w: Warning) -> None:
        async with get_conn() as db:
            await db.execute(
                "INSERT OR REPLACE INTO warnings (id, plot_id, level, type, ts, data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    w.id,
                    w.plot_id,
                    w.risk_level.value,
                    w.risk_type,
                    w.ts.isoformat(),
                    w.model_dump_json(),
                ),
            )
            await db.commit()

    async def get_warning(self, warning_id: str) -> Optional[Warning]:
        async with get_conn() as db:
            async with db.execute(
                "SELECT data FROM warnings WHERE id = ?", (warning_id,)
            ) as cur:
                row = await cur.fetchone()
        return Warning.model_validate_json(row[0]) if row else None

    async def query_warnings(
        self, plot_id: Optional[str] = None, limit: int = 50
    ) -> list[Warning]:
        clauses, args = [], []
        if plot_id:
            clauses.append("plot_id = ?")
            args.append(plot_id)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT data FROM warnings {where} ORDER BY ts DESC LIMIT ?"
        args.append(limit)
        async with get_conn() as db:
            async with db.execute(sql, args) as cur:
                rows = await cur.fetchall()
        return [Warning.model_validate_json(r[0]) for r in rows]

    # ---------- Feedback ----------
    async def add_feedback(self, f: Feedback) -> None:
        async with get_conn() as db:
            await db.execute(
                "INSERT OR REPLACE INTO feedbacks (id, warning_id, outcome, ts, data) "
                "VALUES (?, ?, ?, ?, ?)",
                (f.id, f.warning_id, f.outcome.value, f.ts.isoformat(), f.model_dump_json()),
            )
            await db.commit()

    # ---------- Evaluation ----------
    async def add_evaluation(self, e: Evaluation) -> None:
        async with get_conn() as db:
            await db.execute(
                "INSERT OR REPLACE INTO evaluations (id, warning_id, ts, data) VALUES (?, ?, ?, ?)",
                (e.id, e.warning_id, e.ts.isoformat(), e.model_dump_json()),
            )
            await db.commit()

    async def list_evaluations(self, limit: int = 50) -> list[Evaluation]:
        async with get_conn() as db:
            async with db.execute(
                "SELECT data FROM evaluations ORDER BY ts DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        return [Evaluation.model_validate_json(r[0]) for r in rows]

    # ---------- Asset history (for Harness audit) ----------
    async def record_asset_change(
        self,
        agent_name: str,
        asset: str,
        op: str,
        note: str,
        before: str,
        after: str,
    ) -> None:
        from uuid import uuid4
        from datetime import datetime, timezone

        async with get_conn() as db:
            await db.execute(
                "INSERT INTO asset_history (id, agent_name, asset, ts, op, note, before, after) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"ah_{uuid4().hex[:10]}",
                    agent_name,
                    asset,
                    datetime.now(timezone.utc).isoformat(),
                    op,
                    note,
                    before,
                    after,
                ),
            )
            await db.commit()

    async def list_asset_history(self, agent_name: str, limit: int = 50) -> list[dict]:
        async with get_conn() as db:
            async with db.execute(
                "SELECT id, asset, ts, op, note, before, after FROM asset_history "
                "WHERE agent_name = ? ORDER BY ts DESC LIMIT ?",
                (agent_name, limit),
            ) as cur:
                rows = await cur.fetchall()
        return [
            {
                "id": r[0],
                "asset": r[1],
                "ts": r[2],
                "op": r[3],
                "note": r[4],
                "before": r[5],
                "after": r[6],
            }
            for r in rows
        ]


pool = DataPool()
