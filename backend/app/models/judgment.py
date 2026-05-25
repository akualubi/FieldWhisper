from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    NONE = "无"
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    EXTREME = "极高"

    @property
    def numeric(self) -> int:
        return {"无": 0, "低": 1, "中": 2, "高": 3, "极高": 4}[self.value]


class RiskJudgment(BaseModel):
    """单个 Analyst Agent 的领域结论。"""

    id: str = Field(default_factory=lambda: f"rj_{uuid4().hex[:10]}")
    agent_kind: str               # weather | crop | plot | pest | sentiment
    plot_id: str
    risk_type: str                # 高温热害 | 倒伏 | 条锈病 ...
    level: RiskLevel
    confidence: float = 0.5       # 0~1
    rationale: str = ""           # 人类可读的解释
    evidence: list[str] = Field(default_factory=list)  # DataItem.id 引用
    rule_refs: list[str] = Field(default_factory=list) # 命中的规则名，便于 Harness 归因
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extras: dict = Field(default_factory=dict)
