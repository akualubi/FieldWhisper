"""Demo 层：把前端的"拖图标到省份"等高级交互翻译成后端 pipeline 输入。"""
from .province_map import PROVINCES, resolve_province
from .weather_intents import WEATHER_INTENTS, build_intent_items

__all__ = ["PROVINCES", "resolve_province", "WEATHER_INTENTS", "build_intent_items"]
