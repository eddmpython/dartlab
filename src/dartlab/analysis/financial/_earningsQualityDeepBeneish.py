"""Beneish M-Score 시계열 호환 진입점."""

from __future__ import annotations

from dartlab.analysis.financial._earningsQualityCalcs import _beneishUnavailable
from dartlab.core.memory import memoizedCalc


@memoizedCalc
def calcBeneishTimeline(company, *, basePeriod: str | None = None) -> dict:
    """원식 입력 계약이 갖춰질 때까지 시계열 점수를 비발행한다.

    과거 구현은 DEPI를 항상 1로 두고, 결측 계정을 0 또는 중립값으로 대체하며,
    TATA와 LVGI에 다른 대용식을 사용했다. 축은 호환성을 위해 남기되 빈 history와
    구조화된 사유를 반환한다.
    """
    _ = company, basePeriod
    result = _beneishUnavailable()
    result.update(
        {
            "history": [],
            "threshold": None,
            "diagnosticMeta": {
                "reference": "Beneish(1999), 8-variable model",
                "canonical": False,
                "reasonCode": result["reasonCode"],
                "sampleBase": None,
                "precision": None,
                "falsePositiveRate": None,
            },
        }
    )
    return result
