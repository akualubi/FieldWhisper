from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CropStage(str, Enum):
    """简化的英文生育期枚举（兼容旧调用）。

    Demo 实际用自由文本（如 "灌浆末-蜡熟初"）存到 Plot.stage_zh，
    本枚举只在没有 stage_zh 时做回退。"""

    SEEDING = "seeding"
    JOINTING = "jointing"
    TASSELING = "tasseling"
    BOOTING = "booting"
    FLOWERING = "flowering"
    GRAIN_FILLING = "grain_filling"
    MATURITY = "maturity"


class Plot(BaseModel):
    """地块档案。字段对齐 seed/mock/parcels.json。"""

    plot_id: str = Field(alias="plot_id")
    name: str
    lat: float
    lon: float
    area_mu: float = 100.0
    crop: str                                  # "winter_wheat" | "summer_maize" | "spring_maize" | "apple" ...
    variety: Optional[str] = None              # 品种（济麦22 / 郑单958 等）
    sowing_date: Optional[str] = None
    stage_zh: str = ""                         # 中文自由文本生育期（"灌浆末-蜡熟初"）
    stage: CropStage = CropStage.JOINTING      # 兼容旧调用的英文枚举
    stage_risks: list[str] = Field(default_factory=list)
    terrain: str = "平原"
    soil_drainage: str = "中等"
    historical_disasters: list[str] = Field(default_factory=list)
    owner_id: Optional[str] = None
    policy_no: Optional[str] = None
    notes: str = ""

    model_config = {"populate_by_name": True}

    @classmethod
    def from_seed(cls, raw: dict) -> "Plot":
        """从 seed/mock/parcels.json 的一条记录构造 Plot。"""
        crop = raw.get("crop", "")
        stage_zh = raw.get("crop_stage", "")
        stage_enum = _infer_stage_enum(stage_zh)
        return cls(
            plot_id=raw["id"],
            name=raw["name"],
            lat=raw["lat"],
            lon=raw["lon"],
            area_mu=raw.get("area_mu", 100),
            crop=crop,
            variety=raw.get("variety"),
            sowing_date=raw.get("sowing_date"),
            stage_zh=stage_zh,
            stage=stage_enum,
            stage_risks=raw.get("stage_risks") or [],
            owner_id=raw.get("owner_id"),
            policy_no=raw.get("policy_no"),
        )


_STAGE_HINTS = [
    ("灌浆", CropStage.GRAIN_FILLING),
    ("蜡熟", CropStage.MATURITY),
    ("抽雄", CropStage.TASSELING),
    ("孕穗", CropStage.BOOTING),
    ("开花", CropStage.FLOWERING),
    ("拔节", CropStage.JOINTING),
    ("苗", CropStage.SEEDING),
    ("叶", CropStage.SEEDING),
    ("播", CropStage.SEEDING),
]


def _infer_stage_enum(stage_zh: str) -> CropStage:
    for kw, st in _STAGE_HINTS:
        if kw in stage_zh:
            return st
    return CropStage.JOINTING
