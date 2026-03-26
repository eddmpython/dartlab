"""ESG 공시 분석 엔진 — 환경(E), 사회(S), 지배구조(G) 3축 평가.

sections 텍스트 + 기존 scan 결과에서 ESG 메트릭을 추출하고,
K-ESG/GRI/TCFD 표준에 매핑하여 종합 등급을 부여한다.

사용법::

    import dartlab

    c = dartlab.Company("005930")
    c.esg                       # ESG 종합 (E/S/G 각 등급)
    c.esg.environment           # 환경 pillar 상세
    c.esg.social                # 사회 pillar 상세
    c.esg.governance            # 지배구조 pillar 상세
"""

from dartlab.analysis.strategy.esg.extractor import analyze_esg, esg_to_dataframe
from dartlab.analysis.strategy.esg.timeline import esg_timeline
from dartlab.analysis.strategy.esg.types import EsgPillar, EsgResult

__all__ = [
    "analyze_esg",
    "esg_to_dataframe",
    "esg_timeline",
    "EsgPillar",
    "EsgResult",
]
