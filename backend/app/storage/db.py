from __future__ import annotations

import aiosqlite

from ..config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS plots (
    plot_id TEXT PRIMARY KEY,
    data    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_items (
    id      TEXT PRIMARY KEY,
    source  TEXT NOT NULL,
    type    TEXT NOT NULL,
    ts      TEXT NOT NULL,
    plot_id TEXT,
    data    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_data_items_plot ON data_items(plot_id, type);
CREATE INDEX IF NOT EXISTS idx_data_items_ts   ON data_items(ts);

CREATE TABLE IF NOT EXISTS judgments (
    id        TEXT PRIMARY KEY,
    plot_id   TEXT NOT NULL,
    agent     TEXT NOT NULL,
    risk_type TEXT NOT NULL,
    level     TEXT NOT NULL,
    ts        TEXT NOT NULL,
    data      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_judgments_plot ON judgments(plot_id, agent);

CREATE TABLE IF NOT EXISTS warnings (
    id      TEXT PRIMARY KEY,
    plot_id TEXT NOT NULL,
    level   TEXT NOT NULL,
    type    TEXT NOT NULL,
    ts      TEXT NOT NULL,
    data    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_warnings_plot ON warnings(plot_id);

CREATE TABLE IF NOT EXISTS feedbacks (
    id         TEXT PRIMARY KEY,
    warning_id TEXT NOT NULL,
    outcome    TEXT NOT NULL,
    ts         TEXT NOT NULL,
    data       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedbacks_warning ON feedbacks(warning_id);

CREATE TABLE IF NOT EXISTS evaluations (
    id         TEXT PRIMARY KEY,
    warning_id TEXT NOT NULL,
    ts         TEXT NOT NULL,
    data       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_history (
    id         TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    asset      TEXT NOT NULL,
    ts         TEXT NOT NULL,
    op         TEXT NOT NULL,
    note       TEXT,
    before     TEXT,
    after      TEXT
);
CREATE INDEX IF NOT EXISTS idx_asset_history_agent ON asset_history(agent_name);
"""


async def init_db() -> None:
    async with aiosqlite.connect(settings.suian_db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


def get_conn():
    return aiosqlite.connect(settings.suian_db_path)
