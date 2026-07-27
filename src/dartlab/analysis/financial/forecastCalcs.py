"""매출전망 축 -- forecast 엔진을 analysis 패턴으로 래핑 — facade.

본체: `_forecastCalcsInputs` / `_forecastCalcsRevenue` / `_forecastCalcsScenarios` / `_forecastCalcsMeta`.

calc 함수 8 개: 매출예측, 세그먼트전망, ProForma, 시나리오, 방법론, 과거비율, 플래그,
시나리오 시뮬레이션. 모든 함수는 ``(company) -> dict | None`` 시그니처.
"""

from __future__ import annotations

from dartlab.analysis.financial._forecastCalcsInputs import (
    _buildCompanyDataBundle,
    _getSectorParams,
    _getSeriesAndMeta,
    _getShares,
    _runForecastRevenue,
)
from dartlab.analysis.financial._forecastCalcsMeta import (
    calcCalibrationReport,
    calcForecastFlags,
    calcForecastMethodology,
    calcHistoricalRatios,
)
from dartlab.analysis.financial._forecastCalcsRevenue import (
    calcRevenueForecast,
    calcSegmentForecast,
)
from dartlab.analysis.financial._forecastCalcsScenarios import (
    calcProFormaHighlights,
    calcScenarioImpact,
    calcScenarioSimulation,
)

__all__ = [
    "_buildCompanyDataBundle",
    "_getSectorParams",
    "_getSeriesAndMeta",
    "_getShares",
    "_runForecastRevenue",
    "calcCalibrationReport",
    "calcForecastFlags",
    "calcForecastMethodology",
    "calcHistoricalRatios",
    "calcProFormaHighlights",
    "calcRevenueForecast",
    "calcScenarioImpact",
    "calcScenarioSimulation",
    "calcSegmentForecast",
]
