from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class RootCause(BaseModel):
    """归因到某个 Agent 的某个资产文件。"""

    agent_name: str       # weather | crop | plot | pest | sentiment | simulator | decision
    asset: Literal["rules.yaml", "weights.json", "experience.md", "prompt.md"]
    reason: str           # 人话描述：为什么是这里出了问题


class AssetPatch(BaseModel):
    """Evolver 应用到 Agent 资产上的具体 diff。"""

    id: str = Field(default_factory=lambda: f"ap_{uuid4().hex[:10]}")
    agent_name: str
    asset: str
    op: Literal["append_md", "update_yaml", "update_json"]
    payload: dict          # 具体改什么：append_md → {section, content}; update_yaml/json → {path, value}
    note: str = ""         # 这次修改的理由


class Evaluation(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:10]}")
    warning_id: str
    feedback_id: str
    score: float                              # 0~1，整体评分
    verdict: str                              # "hit" / "false_positive" / "underestimated" / "not_actionable"
    actionable_score: float = 0.0             # 建议是否可执行
    root_causes: list[RootCause] = Field(default_factory=list)
    patches: list[AssetPatch] = Field(default_factory=list)
    summary: str = ""
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
