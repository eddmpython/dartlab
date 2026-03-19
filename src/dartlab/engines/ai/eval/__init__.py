"""AI 답변 평가 프레임워크.

Golden dataset 기반 자동 채점 + 5차원 품질 평가.
"""

from __future__ import annotations

import json
from pathlib import Path

from dartlab.engines.ai.eval.scorer import ScoreCard, auto_score

_GOLDEN_PATH = Path(__file__).parent / "golden.json"


def load_golden_dataset() -> list[dict]:
    """golden.json에서 QA pair 로드."""
    if not _GOLDEN_PATH.exists():
        return []
    with open(_GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


__all__ = ["load_golden_dataset", "auto_score", "ScoreCard"]
