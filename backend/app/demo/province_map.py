"""34 个省级行政区 → 大致地理中心 + 默认作物 + 当前生育期。

只用于"用户拖图标到省"这种粗粒度演示。
如果该省已有 seed plot，优先使用；否则按需创建 `P-DEMO-<省>` 临时地块。
"""
from __future__ import annotations

# (lat, lon, default_crop, default_stage_zh)
PROVINCES: dict[str, tuple[float, float, str, str]] = {
    # 直辖市
    "北京": (39.9, 116.4, "summer_maize", "苗期"),
    "天津": (39.1, 117.2, "summer_maize", "苗期"),
    "上海": (31.2, 121.5, "水稻", "返青分蘖"),
    "重庆": (29.6, 106.5, "水稻", "返青分蘖"),

    # 黄淮海 / 华北 - 小麦带
    "河北": (38.0, 114.5, "winter_wheat", "灌浆末-蜡熟初"),
    "河南": (34.8, 113.6, "winter_wheat", "灌浆末"),
    "山东": (36.7, 117.0, "winter_wheat", "灌浆末-蜡熟初"),
    "山西": (37.9, 112.5, "summer_maize", "拔节期"),
    "陕西": (34.3, 108.9, "winter_wheat", "灌浆末"),

    # 东北 - 春玉米/大豆
    "辽宁": (41.8, 123.4, "spring_maize", "三叶期-五叶期"),
    "吉林": (43.9, 125.3, "spring_maize", "三叶期-五叶期"),
    "黑龙江": (46.6, 126.9, "spring_maize", "三叶期-五叶期"),

    # 内蒙古 / 西北
    "内蒙古": (43.0, 112.0, "spring_maize", "苗期"),
    "甘肃": (36.1, 103.8, "spring_maize", "拔节期"),
    "青海": (36.6, 101.8, "青稞", "拔节期"),
    "宁夏": (38.5, 106.2, "winter_wheat", "灌浆末"),
    "新疆": (43.8, 87.6, "spring_maize", "拔节期"),

    # 长江中下游 - 水稻
    "江苏": (32.0, 118.8, "水稻", "返青分蘖"),
    "浙江": (30.3, 120.2, "水稻", "返青分蘖"),
    "安徽": (31.9, 117.3, "winter_wheat", "灌浆末"),
    "湖北": (30.5, 114.3, "水稻", "返青分蘖"),
    "湖南": (28.2, 113.0, "水稻", "返青分蘖"),
    "江西": (28.7, 115.9, "水稻", "返青分蘖"),

    # 华南
    "福建": (26.1, 119.3, "水稻", "返青分蘖"),
    "广东": (23.1, 113.3, "水稻", "返青分蘖"),
    "广西": (22.8, 108.4, "水稻", "返青分蘖"),
    "海南": (20.0, 110.3, "水稻", "返青分蘖"),

    # 西南
    "四川": (30.7, 104.1, "水稻", "返青分蘖"),
    "贵州": (26.6, 106.7, "水稻", "返青分蘖"),
    "云南": (25.0, 102.7, "水稻", "返青分蘖"),
    "西藏": (29.7, 91.1, "青稞", "拔节期"),

    # 特别行政区/台湾（演示陪跑）
    "台湾": (23.6, 121.0, "水稻", "返青分蘖"),
    "香港": (22.3, 114.2, "水稻", "成熟"),
    "澳门": (22.2, 113.5, "水稻", "成熟"),
}


# seed/mock/parcels.json 已有的 3 块地，按省优先使用
SEED_PROVINCE_TO_PLOT: dict[str, str] = {
    "河北": "P-HEB-GUANTAO-001",
    "河南": "P-HEN-ZHONGMU-002",
    "黑龙江": "P-HLJ-SUIHUA-003",
    "山东": "P-SD-YANTAI-EXTRA",   # 冰雹场景临时果园（如已创建）
}


def resolve_province(name: str) -> dict | None:
    """name 可以是 '山东'/'山东省'/'sd' 等，做容错匹配。"""
    if not name:
        return None
    key = name.replace("省", "").replace("市", "").replace("自治区", "").replace("特别行政区", "").strip()
    # 简单别名
    aliases = {
        "内蒙": "内蒙古", "蒙古": "内蒙古",
        "新": "新疆", "藏": "西藏", "宁": "宁夏", "桂": "广西",
    }
    key = aliases.get(key, key)
    if key not in PROVINCES:
        return None
    lat, lon, crop, stage = PROVINCES[key]
    return {
        "province": key,
        "lat": lat, "lon": lon,
        "default_crop": crop, "default_stage_zh": stage,
        "seed_plot_id": SEED_PROVINCE_TO_PLOT.get(key),
    }


def make_demo_plot_id(province: str) -> str:
    return f"P-DEMO-{province}"
