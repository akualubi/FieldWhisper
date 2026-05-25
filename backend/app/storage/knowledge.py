from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ..config import settings


class KnowledgeStore:
    """每个 Agent 的"可进化资产"读写。

    资产目录：backend/knowledge/<agent_name>/
        experience.md   - 经验文档（人话案例）
        prompt.md       - 系统提示词
        rules.yaml      - 阈值规则
        weights.json    - 权重
        knowledge/      - 历史案例片段 (*.md)
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or settings.knowledge_root

    def agent_dir(self, agent_name: str) -> Path:
        return self.root / agent_name

    # ----- 读 -----
    def read_experience(self, agent_name: str) -> str:
        f = self.agent_dir(agent_name) / "experience.md"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def read_prompt(self, agent_name: str) -> str:
        f = self.agent_dir(agent_name) / "prompt.md"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def read_rules(self, agent_name: str) -> dict[str, Any]:
        f = self.agent_dir(agent_name) / "rules.yaml"
        if not f.exists():
            return {}
        return yaml.safe_load(f.read_text(encoding="utf-8")) or {}

    def read_weights(self, agent_name: str) -> dict[str, float]:
        f = self.agent_dir(agent_name) / "weights.json"
        if not f.exists():
            return {}
        return json.loads(f.read_text(encoding="utf-8"))

    def read_knowledge_snippets(self, agent_name: str) -> list[dict]:
        d = self.agent_dir(agent_name) / "knowledge"
        if not d.exists():
            return []
        return [
            {"name": p.stem, "content": p.read_text(encoding="utf-8")}
            for p in sorted(d.glob("*.md"))
        ]

    def snapshot(self, agent_name: str) -> dict[str, Any]:
        return {
            "experience": self.read_experience(agent_name),
            "prompt": self.read_prompt(agent_name),
            "rules": self.read_rules(agent_name),
            "weights": self.read_weights(agent_name),
            "knowledge_snippets": self.read_knowledge_snippets(agent_name),
        }

    # ----- 写（Harness Evolver 调用） -----
    def append_experience(self, agent_name: str, section_title: str, body: str) -> tuple[str, str]:
        f = self.agent_dir(agent_name) / "experience.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        before = f.read_text(encoding="utf-8") if f.exists() else ""
        new_section = f"\n\n## {section_title}\n\n{body}\n"
        after = before + new_section
        f.write_text(after, encoding="utf-8")
        return before, after

    def update_rules(self, agent_name: str, path: list[str], value: Any) -> tuple[str, str]:
        f = self.agent_dir(agent_name) / "rules.yaml"
        f.parent.mkdir(parents=True, exist_ok=True)
        data = yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {}
        if data is None:
            data = {}
        before_text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        # path 例如 ["wind", "threshold_level"]
        cur = data
        for p in path[:-1]:
            cur = cur.setdefault(p, {})
        cur[path[-1]] = value
        after_text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        f.write_text(after_text, encoding="utf-8")
        return before_text, after_text

    def update_weights(self, agent_name: str, path: list[str], value: float) -> tuple[str, str]:
        f = self.agent_dir(agent_name) / "weights.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        before_text = json.dumps(data, ensure_ascii=False, indent=2)
        cur = data
        for p in path[:-1]:
            cur = cur.setdefault(p, {})
        cur[path[-1]] = value
        after_text = json.dumps(data, ensure_ascii=False, indent=2)
        f.write_text(after_text, encoding="utf-8")
        return before_text, after_text


knowledge = KnowledgeStore()
