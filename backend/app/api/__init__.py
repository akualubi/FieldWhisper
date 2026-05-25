from fastapi import APIRouter

from . import plots, collect, analyze, warnings, feedback, agents, events, batch, seed

router = APIRouter()
router.include_router(plots.router, prefix="/plots", tags=["plots"])
router.include_router(collect.router, prefix="/collect", tags=["collect"])
router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
router.include_router(warnings.router, prefix="/warnings", tags=["warnings"])
router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(batch.router, prefix="/batch", tags=["batch"])
router.include_router(seed.router, prefix="/seed", tags=["seed"])
