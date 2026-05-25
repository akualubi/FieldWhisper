from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .judgment import RiskLevel
from .peril import PerilCode


class Warning(BaseModel):
    """Decision Agent 输出的结构化预警 —— 给 B 端的最终产品。"""

    id: str = Field(default_factory=lambda: f"wn_{uuid4().hex[:10]}")
    plot_id: str
    crop: str
    stage: str                                       # 中文自由文本生育期
    risk_level: RiskLevel
    risk_type: str                                   # 内部中文（"高温热害"）
    peril_code: PerilCode = PerilCode.GENERIC        # 对外标准 code
    peril_name_zh: str = ""                          # peril 的中文名
    headline: str
    actions: list[str] = Field(default_factory=list)
    best_window: str = "未来 48 小时"
    onset_window_start: Optional[datetime] = None    # 灾害启动时点
    onset_window_end: Optional[datetime] = None      # 灾害结束时点
    confidence: float = 0.5
    rationale: str = ""
    evidence_judgment_ids: list[str] = Field(default_factory=list)
    data_source_ids: list[str] = Field(default_factory=list)
    trajectory_summary: str = ""
    matched_history_case: Optional[str] = None       # "CASE-001" etc.
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
