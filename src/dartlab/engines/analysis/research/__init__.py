"""종합 기업분석 리포트 엔진.

종목코드 하나로 세계 수준의 equity research 리포트를 생성한다.

사용법::

    from dartlab.engines.analysis.research import generateResearch

    result = generateResearch(company)
    result.executive.opinion    # "강력매수"
    result.thesis.bullCase      # ["매출 +25.3% (고성장)", ...]
    result.valuationAnalysis    # DCF/DDM/상대가치 종합
    result.riskAnalysis         # distress + anomalies
"""

from dartlab.engines.analysis.research.orchestrator import generateResearch
from dartlab.engines.analysis.research.scoring import calcAllScores
from dartlab.engines.analysis.research.types import (
    AnomalySection,
    CompanyOverview,
    DistressSection,
    DuPontResult,
    EarningsQuality,
    ExecutiveSummary,
    FinancialAnalysis,
    ForecastData,
    InsightDetail,
    InvestmentThesis,
    LynchFairValue,
    MagicFormulaScore,
    MarketData,
    NarrativeAnalysis,
    NarrativeParagraph,
    PeerSection,
    PiotroskiScore,
    QmjScore,
    QuantScores,
    ResearchMeta,
    ResearchResult,
    RiskSection,
    SectorKpi,
    SectorKpis,
    ValuationSection,
)

__all__ = [
    "generateResearch",
    "calcAllScores",
    "AnomalySection",
    "CompanyOverview",
    "DistressSection",
    "DuPontResult",
    "EarningsQuality",
    "ExecutiveSummary",
    "FinancialAnalysis",
    "ForecastData",
    "InsightDetail",
    "InvestmentThesis",
    "LynchFairValue",
    "MagicFormulaScore",
    "MarketData",
    "NarrativeAnalysis",
    "NarrativeParagraph",
    "PeerSection",
    "PiotroskiScore",
    "QmjScore",
    "QuantScores",
    "ResearchMeta",
    "ResearchResult",
    "RiskSection",
    "SectorKpi",
    "SectorKpis",
    "ValuationSection",
]
