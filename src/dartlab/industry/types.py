"""산업 매퍼엔진 데이터 모델.

taxonomy.json, nodes.json, edges.json의 행 단위 타입.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StageInfo:
    """taxonomy.json의 한 공정 단계."""

    key: str
    name: str
    role: str  # 제조 / 도매 / 소매 / 연구 / 서비스
    stream: str  # upstream / midstream / downstream
    keywords: list[str]


@dataclass
class IndustryDef:
    """taxonomy.json의 한 산업 정의."""

    industryId: str
    name: str
    ksicCodes: list[str]
    stages: list[StageInfo]

    def stageByKey(self, key: str) -> StageInfo | None:
        """stage key 로 StageInfo 조회. 없으면 None.

        Raises:
            없음.

        Example:
            >>> from dartlab.industry.taxonomy import getIndustry
            >>> getIndustry("semiconductor").stageByKey("memory").name
            '메모리'

        Requires:
            - 외부 의존 없음 (in-memory 리스트 룩업).
        """
        for s in self.stages:
            if s.key == key:
                return s
        return None

    def allKeywords(self) -> dict[str, list[str]]:
        """stage key → keywords 매핑.

        Raises:
            없음.

        Example:
            >>> from dartlab.industry.taxonomy import getIndustry
            >>> getIndustry("semiconductor").allKeywords().get("memory")[:3]

        Requires:
            - 외부 의존 없음.
        """
        return {s.key: s.keywords for s in self.stages}


@dataclass
class IndustryNode:
    """nodes.json의 한 행 — 회사의 산업 내 위치."""

    stockCode: str
    corpName: str
    industry: str  # taxonomy의 industry ID
    stage: str  # taxonomy의 stage key
    role: str = ""
    stream: str = ""
    confidence: float = 0.0
    source: str = ""  # kindlist / product / docs / ai / manual
    primary: bool = True
    updatedAt: str = ""
    revenue: float | None = None  # 매출액 (원)
    revenuePeriod: str | None = None  # 매출액의 회계연도 (YYYY)
    # 비상장 매입처 leaf supply fact (레버 A) — 그래프 노드 미승격, buyer 속성으로 보존.
    # 각 항목: {"supplier": str, "amount": float|None(억원), "ratio": float|None(%)}
    supplyFacts: list[dict] = field(default_factory=list)

    def toDict(self) -> dict:
        """dataclass → nodes.json 행 dict 직렬화.

        Raises:
            없음.

        Example:
            >>> IndustryNode("005930", "삼성전자", "semiconductor", "memory").toDict()["industry"]
            'semiconductor'

        Requires:
            - 외부 의존 없음.
        """
        return {
            "stockCode": self.stockCode,
            "corpName": self.corpName,
            "industry": self.industry,
            "stage": self.stage,
            "role": self.role,
            "stream": self.stream,
            "confidence": self.confidence,
            "source": self.source,
            "primary": self.primary,
            "updatedAt": self.updatedAt,
            "revenue": self.revenue,
            "revenuePeriod": self.revenuePeriod,
            # 빈 리스트는 직렬화 생략 (nodes.json 비대화 방지 — ~23%사만 보유)
            **({"supplyFacts": self.supplyFacts} if self.supplyFacts else {}),
        }

    @staticmethod
    def fromDict(d: dict) -> IndustryNode:
        """nodes.json 행 dict → IndustryNode 역직렬화.

        Raises:
            없음 — 누락 키는 기본값으로 폴백.

        Example:
            >>> IndustryNode.fromDict({"stockCode": "005930"}).stockCode
            '005930'

        Requires:
            - 외부 의존 없음.
        """
        return IndustryNode(
            stockCode=d.get("stockCode", ""),
            corpName=d.get("corpName", ""),
            industry=d.get("industry", ""),
            stage=d.get("stage", ""),
            role=d.get("role", ""),
            stream=d.get("stream", ""),
            confidence=d.get("confidence", 0.0),
            source=d.get("source", ""),
            primary=d.get("primary", True),
            updatedAt=d.get("updatedAt", ""),
            revenue=d.get("revenue"),
            revenuePeriod=d.get("revenuePeriod"),
            supplyFacts=d.get("supplyFacts", []),
        )


@dataclass
class IndustryEdge:
    """edges.json의 한 행 — 공급-수요 관계."""

    fromCode: str
    fromName: str
    toCode: str
    toName: str
    edgeType: str  # supplier / customer / affiliate / competitor
    industry: str
    confidence: float = 0.0
    source: str = ""  # docs / network / ai / manual
    evidence: str = ""
    product: str = ""  # 거래 품목 (supplier/customer)
    amount: float | None = None  # 거래 금액 (억원)
    ratio: float | None = None  # 매입비중 (%)

    def toDict(self) -> dict:
        """IndustryEdge → edges.json 행 dict 직렬화.

        Raises:
            없음.

        Example:
            >>> IndustryEdge("006400", "삼성SDI", "005930", "삼성전자", "supplier", "battery").toDict()["type"]
            'supplier'

        Requires:
            - 외부 의존 없음.
        """
        return {
            "fromCode": self.fromCode,
            "fromName": self.fromName,
            "toCode": self.toCode,
            "toName": self.toName,
            "type": self.edgeType,
            "industry": self.industry,
            "confidence": self.confidence,
            "source": self.source,
            "evidence": self.evidence,
            "product": self.product,
            "amount": self.amount,
            "ratio": self.ratio,
        }

    @staticmethod
    def fromDict(d: dict) -> IndustryEdge:
        """edges.json 행 dict → IndustryEdge 역직렬화.

        Raises:
            없음 — 누락 키는 기본값으로 폴백.

        Example:
            >>> IndustryEdge.fromDict({"fromCode": "006400", "toCode": "005930", "type": "supplier"}).edgeType
            'supplier'

        Requires:
            - 외부 의존 없음.
        """
        return IndustryEdge(
            fromCode=d.get("fromCode", ""),
            fromName=d.get("fromName", ""),
            toCode=d.get("toCode", ""),
            toName=d.get("toName", ""),
            edgeType=d.get("type", ""),
            industry=d.get("industry", ""),
            confidence=d.get("confidence", 0.0),
            source=d.get("source", ""),
            evidence=d.get("evidence", ""),
            product=d.get("product", ""),
            amount=d.get("amount"),
            ratio=d.get("ratio"),
        )
