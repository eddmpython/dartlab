"""등급 이력 관리 + 전이 매트릭스.

보고서 발행마다 등급을 JSON으로 축적하고,
등급 전이 매트릭스를 자동 업데이트한다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_CREDIT_DATA_DIR = Path("data/credit")
_HISTORY_DIR = _CREDIT_DATA_DIR / "history"
_TRANSITION_PATH = _CREDIT_DATA_DIR / "transition.json"


def _ensureDir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def recordGrade(stockCode: str, result: dict) -> Path:
    """등급 이력에 현재 결과 추가."""
    _ensureDir(_HISTORY_DIR)
    path = _HISTORY_DIR / f"{stockCode}.json"

    history = loadHistory(stockCode)

    previousGrade = history[-1]["grade"] if history else None
    changed = previousGrade != result.get("grade") if previousGrade else False

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "grade": result.get("grade"),
        "gradeRaw": result.get("gradeRaw"),
        "score": result.get("score"),
        "eCR": result.get("eCR"),
        "outlook": result.get("outlook"),
        "methodologyVersion": result.get("methodologyVersion"),
        "period": result.get("latestPeriod"),
        "previousGrade": previousGrade,
        "changed": changed,
    }

    history.append(entry)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    # 전이 매트릭스 업데이트
    if previousGrade and changed:
        _updateTransition(previousGrade, result.get("grade", ""))

    return path


def loadHistory(stockCode: str) -> list[dict]:
    """등급 이력 로드."""
    path = _HISTORY_DIR / f"{stockCode}.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def gradeChanged(stockCode: str, newGrade: str) -> bool:
    """이전 등급 대비 변경 여부."""
    history = loadHistory(stockCode)
    if not history:
        return True  # 첫 발행
    return history[-1].get("grade") != newGrade


def _updateTransition(fromGrade: str, toGrade: str) -> None:
    """전이 매트릭스 업데이트."""
    _ensureDir(_CREDIT_DATA_DIR)
    matrix = _loadTransition()

    if fromGrade not in matrix:
        matrix[fromGrade] = {}
    matrix[fromGrade][toGrade] = matrix[fromGrade].get(toGrade, 0) + 1

    _TRANSITION_PATH.write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _loadTransition() -> dict:
    """전이 매트릭스 로드."""
    if not _TRANSITION_PATH.exists():
        return {}
    try:
        return json.loads(_TRANSITION_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def updateTransitionMatrix() -> dict:
    """전체 히스토리에서 전이 매트릭스 재계산."""
    _ensureDir(_HISTORY_DIR)
    matrix: dict = {}

    for path in _HISTORY_DIR.glob("*.json"):
        try:
            history = json.loads(path.read_text(encoding="utf-8"))
            for i in range(1, len(history)):
                prev = history[i - 1].get("grade", "")
                curr = history[i].get("grade", "")
                if prev and curr and prev != curr:
                    if prev not in matrix:
                        matrix[prev] = {}
                    matrix[prev][curr] = matrix[prev].get(curr, 0) + 1
        except (json.JSONDecodeError, OSError):
            continue

    _ensureDir(_CREDIT_DATA_DIR)
    _TRANSITION_PATH.write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return matrix
