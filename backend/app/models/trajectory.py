from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .judgment import RiskLevel


class TrajectoryPoint(BaseModel):
    horizon_hours: int               # 24 / 48 / 72
    level: RiskLevel
    probability: float               # 0~1
    note: str = ""


class Trajectory(BaseModel):
    plot_id: str
    risk_type: str
    baseline: list[TrajectoryPoint] = Field(default_factory=list)   # 不干预
    mitigated: list[TrajectoryPoint] = Field(default_factory=list)  # 采纳建议
    key_drivers: list[str] = Field(default_factory=list)            # RiskJudgment.id 引用
    summary: str = ""
