from __future__ import annotations

from ..events import bus
from ..models import Evaluation, Feedback, Warning
from ..storage.data_pool import pool
from .evaluator import evaluate
from .evolver import apply_patches


class Harness:
    """⑥ Harness 元 Agent —— 训练场 + 裁判 + 写回。"""

    name = "harness"

    async def run(self, warning: Warning, feedback: Feedback) -> Evaluation:
        await bus.publish("harness.start", {
            "warning_id": warning.id, "feedback": feedback.outcome.value,
        })
        ev = await evaluate(warning, feedback)
        results = await apply_patches(ev.patches)
        await pool.add_evaluation(ev)
        await pool.add_feedback(feedback)
        await bus.publish("harness.done", {
            "warning_id": warning.id,
            "verdict": ev.verdict,
            "score": ev.score,
            "patches_applied": [r for r in results if r.get("ok")],
            "root_causes": [rc.model_dump() for rc in ev.root_causes],
        })
        return ev


harness = Harness()
