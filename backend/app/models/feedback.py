from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .judgment import RiskLevel


class OutcomeKind(str, Enum):
    HIT = "hit"               # 预警准确，灾害发生且级别匹配
    FALSE_POSITIVE = "false_positive"   # 误报，未实际发生
    UNDERESTIMATED = "underestimated"   # 漏报/低估，实际损失大于预测
    NOT_ACTIONABLE = "not_actionable"   # 建议不可执行
    UNKNOWN = "unknown"


class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: f"fb_{uuid4().hex[:10]}")
    warning_id: str
    outcome: OutcomeKind
    actual_level: Optional[RiskLevel] = None
    actual_loss_pct: Optional[float] = None     # 实际损失比例 0~1
    adopted: bool = False                       # 用户是否采纳建议
    notes: str = ""
    reporter: str = "unknown"                   # 谁回写的（保险/合作社/农户...）
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
