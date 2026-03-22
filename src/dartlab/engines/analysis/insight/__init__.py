"""인사이트 분석 엔진.

7영역 등급 분석 + 이상치 탐지 + 종합 요약.

사용법::

    from dartlab.engines.analysis.insight import analyze

    result = analyze("005930")
    result.grades()        # {'performance': 'A', 'profitability': 'B', ...}
    result.anomalies       # [Anomaly(...), ...]
    result.summary         # "삼성전자는 실적, 재무건전성 등..."
    result.profile         # "premium"
"""

from dartlab.engines.analysis.insight.pipeline import analyze
from dartlab.engines.analysis.insight.types import (
    AnalysisResult,
    Anomaly,
    AuditDataForAnomaly,
    DistressAxis,
    DistressResult,
    Flag,
    InsightResult,
    MarketDataForDistress,
    ModelScore,
)

__all__ = [
    "analyze",
    "AnalysisResult",
    "Anomaly",
    "AuditDataForAnomaly",
    "DistressAxis",
    "DistressResult",
    "Flag",
    "InsightResult",
    "MarketDataForDistress",
    "ModelScore",
]
