"""Demo 用：把 seed/ 仓库内容直通暴露出来，方便前端/演讲者审计种子数据。"""
from __future__ import annotations

from fastapi import APIRouter

from ..storage import seed_loader

router = APIRouter()


@router.get("")
async def seed_index() -> dict:
    return {
        "parcels": len(seed_loader.load_parcels()),
        "scenarios": [s["id"] for s in seed_loader.load_scenarios()],
        "ndvi_parcels": list(seed_loader.load_ndvi().keys()),
        "bulletins": [b["title"] for b in seed_loader.load_bulletins()],
        "farmer_chats": [c["group"] for c in seed_loader.load_farmer_chats()],
        "insurance_examples": len(seed_loader.load_insurance_examples().get("examples", [])),
        "experience_chars": len(seed_loader.load_experience_md()),
    }


@router.get("/parcels")
async def get_parcels() -> list[dict]:
    return seed_loader.load_parcels()


@router.get("/scenarios")
async def get_scenarios() -> list[dict]:
    return seed_loader.load_scenarios()


@router.get("/scenarios/{name}")
async def get_scenario(name: str) -> dict:
    sc = seed_loader.get_scenario(name)
    if not sc:
        return {"error": f"unknown scenario {name}"}
    return sc


@router.get("/bulletins")
async def get_bulletins() -> list[dict]:
    return seed_loader.load_bulletins()


@router.get("/farmer-chats")
async def get_farmer_chats() -> list[dict]:
    return seed_loader.load_farmer_chats()


@router.get("/insurance/examples")
async def get_insurance_examples() -> dict:
    return seed_loader.load_insurance_examples()


@router.get("/experience")
async def get_experience() -> dict:
    return {"text": seed_loader.load_experience_md()}
