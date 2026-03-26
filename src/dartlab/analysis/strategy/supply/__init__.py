"""공급망 분석 엔진 — 공시에서 고객/공급사 관계 추출 + 리스크 스코어링.

sections의 부문정보, 원재료, 관계자거래 등에서
규칙 기반으로 고객/공급사를 추출하고 공급망 리스크를 평가한다.

사용법::

    import dartlab

    c = dartlab.Company("005930")
    c.supply                    # 공급망 분석 결과
    c.supply.customers          # 주요 고객 목록
    c.supply.suppliers          # 주요 공급사 목록
    c.supply.riskScore          # 리스크 점수
"""

from dartlab.analysis.strategy.supply.extractor import extract_supply_links
from dartlab.analysis.strategy.supply.risk import analyze_supply_chain
from dartlab.analysis.strategy.supply.types import SupplyChainResult, SupplyLink

__all__ = [
    "analyze_supply_chain",
    "extract_supply_links",
    "SupplyChainResult",
    "SupplyLink",
]
