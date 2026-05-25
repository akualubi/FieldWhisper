from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    lat: float
    lon: float
    plot_id: Optional[str] = None


class DataItem(BaseModel):
    """采集层产物。Collector 只搬不判，所以这里没有任何风险字段。"""

    id: str = Field(default_factory=lambda: f"di_{uuid4().hex[:10]}")
    source: str  # weather_api | open_meteo | sentinel | news | field_cam | farmer_chat | manual_injection ...
    type: str   # forecast | ndvi | notice | image | post | soil | crop_stage ...
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    geo: Optional[GeoPoint] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    injected_by: Optional[str] = None  # 标记 demo 注入者，None 表示真实采集
