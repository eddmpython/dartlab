"""AI 분석 전 데이터 준비 상태를 요약하는 헬퍼."""

from __future__ import annotations

from datetime import datetime
from typing import Any

_DATA_CATEGORIES = ("docs", "finance", "report")


def getDataReadyStatus(stockCode: str) -> dict[str, Any]:
    """종목의 docs/finance/report 로컬 준비 상태를 반환한다."""
    from dartlab.core.dataLoader import _dataDir

    categories: dict[str, dict[str, Any]] = {}
    available: list[str] = []
    missing: list[str] = []

    for category in _DATA_CATEGORIES:
        filePath = _dataDir(category) / f"{stockCode}.parquet"
        ready = filePath.exists()
        updatedAt = None
        if ready:
            updatedAt = datetime.fromtimestamp(filePath.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            available.append(category)
        else:
            missing.append(category)

        categories[category] = {
            "ready": ready,
            "updatedAt": updatedAt,
        }

    return {
        "stockCode": stockCode,
        "allReady": not missing,
        "available": available,
        "missing": missing,
        "categories": categories,
    }


def formatDataReadyStatus(stockCode: str, *, detailed: bool = False) -> str:
    """데이터 준비 상태를 LLM/UI용 텍스트로 렌더링한다."""
    status = getDataReadyStatus(stockCode)

    if not detailed:
        readyText = ", ".join(status["available"]) if status["available"] else "없음"
        missingText = ", ".join(status["missing"]) if status["missing"] else "없음"
        if status["allReady"]:
            return "- 데이터 상태: docs, finance, report가 모두 준비되어 있습니다."
        return (
            f"- 데이터 상태: 준비됨={readyText}; 누락={missingText}. "
            "누락된 데이터가 있으면 답변 범위가 제한될 수 있습니다."
        )

    lines = [f"## {stockCode} 데이터 상태", ""]
    for category in _DATA_CATEGORIES:
        info = status["categories"][category]
        if info["ready"]:
            lines.append(f"- **{category}**: ✅ 있음 (최종 갱신: {info['updatedAt']})")
        else:
            lines.append(f"- **{category}**: ❌ 없음")

    if status["allReady"]:
        lines.append("\n모든 데이터가 준비되어 있습니다. 바로 분석을 진행할 수 있습니다.")
    else:
        lines.append(
            "\n일부 데이터가 없습니다. `download_data` 도구로 다운로드하거나, "
            "사용자에게 다운로드 여부를 물어보세요."
        )
    return "\n".join(lines)
