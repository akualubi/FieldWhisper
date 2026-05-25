from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..harness import harness
from ..models import Evaluation, Feedback
from ..storage.data_pool import pool

router = APIRouter()


@router.post("/{warning_id}", response_model=Evaluation)
async def post_feedback(warning_id: str, feedback: Feedback) -> Evaluation:
    if feedback.warning_id != warning_id:
        feedback.warning_id = warning_id
    w = await pool.get_warning(warning_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"warning {warning_id} not found")
    return await harness.run(w, feedback)
