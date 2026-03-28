"""공급망 분석 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SupplyLink:
    """하나의 공급망 관계."""

    source: str  # 발주/구매 기업 (종목코드 또는 기업명)
    target: str  # 공급/고객 기업
    relation: str  # "customer", "supplier", "related_party"
    evidence: str  # 출처 텍스트 (topic + period)
    confidence: float  # 신뢰도 0~1


@dataclass
class SupplyChainResult:
    """기업의 공급망 분석 결과."""

    stockCode: str
    corpName: str | None

    customers: list[SupplyLink]  # 주요 고객 목록
    suppliers: list[SupplyLink]  # 주요 공급사 목록
    relatedParties: list[SupplyLink]  # 관계자거래

    concentration: float  # 매출 집중도 HHI (0~1)
    riskScore: float  # 공급망 리스크 점수 (0~100)
    riskFactors: list[str]  # 리스크 요인

    @property
    def totalLinks(self) -> int:
        """고객사+공급사+특수관계자 총 링크 수."""
        return len(self.customers) + len(self.suppliers) + len(self.relatedParties)
