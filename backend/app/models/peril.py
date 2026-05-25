"""统一的 peril_code 体系（与 seed/mock/manual_injection_scenarios.json
和 seed/mock/insurance_payload.json 对齐）。

每个 risk_type 都映射到一个 peril_code，作为对接保险的标准化字段。"""
from __future__ import annotations

from enum import Enum


class PerilCode(str, Enum):
    HEAVY_RAIN_AT_HARVEST = "HEAVY_RAIN_AT_HARVEST"       # 烂场雨
    HEAT_STRESS_AT_FLOWERING = "HEAT_STRESS_AT_FLOWERING" # 抽雄期高温
    DRY_HOT_WIND = "DRY_HOT_WIND"                         # 干热风
    WIND_LODGING = "WIND_LODGING"                         # 风致倒伏
    WIND_LODGING_CUMULATIVE = "WIND_LODGING_CUMULATIVE"   # 多次台风累积倒伏
    LATE_FROST = "LATE_FROST"                             # 晚霜冻
    DROUGHT_SEASONAL = "DROUGHT_SEASONAL"                 # 季节性干旱
    HAIL = "HAIL"                                         # 冰雹
    SCLEROTINIA_HUMIDITY = "SCLEROTINIA_HUMIDITY"         # 菌核病(湿度型)
    STRIPE_RUST = "STRIPE_RUST"                           # 条锈病
    FUSARIUM_HEAD_BLIGHT = "FUSARIUM_HEAD_BLIGHT"         # 赤霉病
    NORTHERN_LEAF_BLIGHT = "NORTHERN_LEAF_BLIGHT"         # 玉米大斑病
    POWDERY_MILDEW = "POWDERY_MILDEW"                     # 白粉病
    FALL_ARMYWORM = "FALL_ARMYWORM"                       # 草地贪夜蛾
    ARMYWORM_GENERIC = "ARMYWORM_GENERIC"                 # 一代/普通粘虫
    CONTINUOUS_RAIN = "CONTINUOUS_RAIN"                   # 连阴雨（非收获期）
    SANDSTORM = "SANDSTORM"                               # 沙尘暴
    SNOW_DISASTER = "SNOW_DISASTER"                       # 暴雪灾害
    TYPHOON = "TYPHOON"                                   # 台风（综合）
    GENERIC = "GENERIC"

    @property
    def zh(self) -> str:
        return PERIL_NAMES_ZH.get(self.value, self.value)


PERIL_NAMES_ZH = {
    "HEAVY_RAIN_AT_HARVEST":   "成熟期烂场雨",
    "HEAT_STRESS_AT_FLOWERING":"抽雄/灌浆期高温热害",
    "DRY_HOT_WIND":            "干热风",
    "WIND_LODGING":            "大风倒伏",
    "WIND_LODGING_CUMULATIVE": "多次台风累积倒伏",
    "LATE_FROST":              "苗期晚霜冻",
    "DROUGHT_SEASONAL":        "季节性干旱",
    "HAIL":                    "冰雹",
    "SCLEROTINIA_HUMIDITY":    "湿度型菌核病",
    "STRIPE_RUST":             "条锈病",
    "FUSARIUM_HEAD_BLIGHT":    "小麦赤霉病",
    "NORTHERN_LEAF_BLIGHT":    "玉米大斑病",
    "POWDERY_MILDEW":          "白粉病",
    "FALL_ARMYWORM":           "草地贪夜蛾",
    "ARMYWORM_GENERIC":        "粘虫",
    "CONTINUOUS_RAIN":         "连阴雨",
    "SANDSTORM":               "沙尘暴",
    "SNOW_DISASTER":           "暴雪/雪灾",
    "TYPHOON":                 "台风",
    "GENERIC":                 "一般风险",
}


# 把 Agent 内部使用的中文 risk_type 映射到标准 peril_code
RISK_TYPE_TO_PERIL = {
    "高温热害":   PerilCode.HEAT_STRESS_AT_FLOWERING,
    "大风":       PerilCode.WIND_LODGING,
    "倒伏":       PerilCode.WIND_LODGING,
    "暴雨":       PerilCode.HEAVY_RAIN_AT_HARVEST,
    "烂场雨":     PerilCode.HEAVY_RAIN_AT_HARVEST,
    "连阴雨":     PerilCode.CONTINUOUS_RAIN,
    "干旱":       PerilCode.DROUGHT_SEASONAL,
    "干热风":     PerilCode.DRY_HOT_WIND,
    "晚霜冻":     PerilCode.LATE_FROST,
    "冰雹":       PerilCode.HAIL,
    "条锈病":     PerilCode.STRIPE_RUST,
    "小麦条锈病": PerilCode.STRIPE_RUST,
    "赤霉病":     PerilCode.FUSARIUM_HEAD_BLIGHT,
    "大斑病":     PerilCode.NORTHERN_LEAF_BLIGHT,
    "白粉病":     PerilCode.POWDERY_MILDEW,
    "草地贪夜蛾": PerilCode.FALL_ARMYWORM,
    "粘虫":       PerilCode.ARMYWORM_GENERIC,
    "菌核病":     PerilCode.SCLEROTINIA_HUMIDITY,
    "沙尘暴":     PerilCode.SANDSTORM,
    "暴雪":       PerilCode.SNOW_DISASTER,
    "雪灾":       PerilCode.SNOW_DISASTER,
    "台风":       PerilCode.TYPHOON,
}


def to_peril(risk_type: str) -> PerilCode:
    if not risk_type:
        return PerilCode.GENERIC
    base = risk_type.split("·")[-1] if "·" in risk_type else risk_type
    return RISK_TYPE_TO_PERIL.get(base, PerilCode.GENERIC)
