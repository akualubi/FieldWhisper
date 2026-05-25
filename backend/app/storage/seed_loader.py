"""读取 seed/ 仓库 —— 单一入口，启动时加载，给 Collector / Decision 复用。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..config import settings


def _read_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_parcels() -> list[dict]:
    data = _read_json(settings.seed_root / "mock" / "parcels.json")
    return data.get("parcels", [])


@lru_cache(maxsize=1)
def load_scenarios() -> list[dict]:
    data = _read_json(settings.seed_root / "mock" / "manual_injection_scenarios.json")
    return data.get("scenarios", [])


@lru_cache(maxsize=1)
def load_ndvi() -> dict[str, list[dict]]:
    data = _read_json(settings.seed_root / "mock" / "ndvi_series.json")
    return {row["parcel_id"]: row["samples"] for row in data.get("series", [])}


@lru_cache(maxsize=1)
def load_insurance_examples() -> dict:
    return _read_json(settings.seed_root / "mock" / "insurance_payload.json")


@lru_cache(maxsize=1)
def load_bulletins() -> list[dict]:
    """简单切分 agri_bulletins.md 成 list[{title, body}]，
    Collector 把它们当 notice 注入。"""
    text = _read_text(settings.seed_root / "mock" / "agri_bulletins.md")
    items: list[dict] = []
    cur_title = None
    cur_body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if cur_title:
                items.append({"title": cur_title, "body": "\n".join(cur_body).strip()})
            cur_title = line[3:].strip()
            cur_body = []
        elif cur_title:
            cur_body.append(line)
    if cur_title:
        items.append({"title": cur_title, "body": "\n".join(cur_body).strip()})
    return items


@lru_cache(maxsize=1)
def load_farmer_chats() -> list[dict]:
    """切分 farmer_chats.md 成 list[{group, lines:[...], signal:str}]."""
    text = _read_text(settings.seed_root / "mock" / "farmer_chats.md")
    chats: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            if cur:
                chats.append(cur)
            cur = {"group": line[3:].strip(), "lines": [], "signal": ""}
        elif cur and line.startswith("> ") and "**" in line:
            cur["lines"].append(line[2:].strip())
        elif cur and line.startswith("**抽取信号**"):
            cur["signal"] = line.replace("**抽取信号**：", "").strip()
    if cur:
        chats.append(cur)
    return chats


@lru_cache(maxsize=1)
def load_experience_md() -> str:
    return _read_text(settings.seed_root / "mock" / "experience.md")


def get_scenario(scenario_id: str) -> dict | None:
    for s in load_scenarios():
        if s["id"] == scenario_id:
            return s
    return None


def get_bulletin_by_index(idx: int) -> dict | None:
    items = load_bulletins()
    if 0 < idx <= len(items):
        return items[idx - 1]
    return None


def get_farmer_chat_by_index(idx: int) -> dict | None:
    items = load_farmer_chats()
    if 0 < idx <= len(items):
        return items[idx - 1]
    return None


def get_bulletin_by_label(label: str) -> dict | None:
    """支持 "通报 1" / "通报 4" 这种 label 直接取。"""
    if not label.startswith("通报"):
        return None
    try:
        idx = int(label.replace("通报", "").strip())
    except ValueError:
        return None
    return get_bulletin_by_index(idx)


def get_farmer_chat_by_label(label: str) -> dict | None:
    if not label.startswith("群聊"):
        return None
    try:
        idx = int(label.replace("群聊", "").strip())
    except ValueError:
        return None
    return get_farmer_chat_by_index(idx)
