"""Excel 내보내기 템플릿 — 시트 구성 정의.

템플릿은 여러 SheetSpec으로 구성되며, 각 SheetSpec은
데이터 소스(source), 표시할 컬럼, 연도 범위, 정렬을 정의한다.

사용법::

    from dartlab.export.template import ExcelTemplate, SheetSpec, PRESETS

    t = ExcelTemplate(name="나만의 양식", sheets=[
        SheetSpec(source="IS", label="손익계산서"),
        SheetSpec(source="BS", label="재무상태표", columns=["sales", "net_profit"]),
        SheetSpec(source="dividend", label="배당"),
    ])

    # 프리셋 사용
    full = PRESETS["full"]
    summary = PRESETS["summary"]
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SheetSpec:
    """단일 시트 명세."""

    source: str
    label: str = ""
    columns: list[str] = field(default_factory=list)
    years: list[str] = field(default_factory=list)
    sortBy: str = ""
    maxRows: int = 0

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.source


@dataclass
class ExcelTemplate:
    """Excel 내보내기 템플릿."""

    name: str
    sheets: list[SheetSpec] = field(default_factory=list)
    description: str = ""
    createdAt: float = field(default_factory=time.time)
    updatedAt: float = field(default_factory=time.time)
    templateId: str = ""

    def __post_init__(self) -> None:
        if not self.templateId:
            self.templateId = f"t_{int(self.createdAt * 1000)}"

    def addSheet(self, spec: SheetSpec) -> None:
        """시트 추가."""
        self.sheets.append(spec)
        self.updatedAt = time.time()

    def removeSheet(self, index: int) -> None:
        """인덱스로 시트 제거."""
        if 0 <= index < len(self.sheets):
            self.sheets.pop(index)
            self.updatedAt = time.time()

    def moveSheet(self, fromIdx: int, toIdx: int) -> None:
        """시트 순서 이동."""
        if 0 <= fromIdx < len(self.sheets) and 0 <= toIdx < len(self.sheets):
            sheet = self.sheets.pop(fromIdx)
            self.sheets.insert(toIdx, sheet)
            self.updatedAt = time.time()

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화용 dict."""
        return asdict(self)

    def toJson(self) -> str:
        """JSON 문자열."""
        return json.dumps(self.toDict(), ensure_ascii=False, indent=2)

    @classmethod
    def fromDict(cls, d: dict[str, Any]) -> ExcelTemplate:
        """dict에서 복원."""
        sheets = [SheetSpec(**s) for s in d.get("sheets", [])]
        return cls(
            name=d["name"],
            sheets=sheets,
            description=d.get("description", ""),
            createdAt=d.get("createdAt", time.time()),
            updatedAt=d.get("updatedAt", time.time()),
            templateId=d.get("templateId", ""),
        )

    @classmethod
    def fromJson(cls, s: str) -> ExcelTemplate:
        """JSON 문자열에서 복원."""
        return cls.fromDict(json.loads(s))


def _buildFullPreset() -> ExcelTemplate:
    """전체 데이터 프리셋 — 모든 시트 포함."""
    return ExcelTemplate(
        name="전체",
        templateId="preset_full",
        description="모든 데이터 소스를 포함하는 전체 내보내기.",
        sheets=[
            SheetSpec(source="IS", label="손익계산서"),
            SheetSpec(source="BS", label="재무상태표"),
            SheetSpec(source="CF", label="현금흐름표"),
            SheetSpec(source="ratios", label="재무비율"),
            SheetSpec(source="fsSummary", label="요약재무정보"),
            SheetSpec(source="dividend", label="배당"),
            SheetSpec(source="majorHolder", label="최대주주"),
            SheetSpec(source="employee", label="직원현황"),
            SheetSpec(source="executive", label="임원현황"),
            SheetSpec(source="executivePay", label="임원보수"),
            SheetSpec(source="audit", label="감사의견"),
            SheetSpec(source="boardOfDirectors", label="이사회"),
            SheetSpec(source="shareCapital", label="주식현황"),
            SheetSpec(source="rnd", label="R&D"),
            SheetSpec(source="segments", label="부문정보"),
            SheetSpec(source="productService", label="주요제품"),
            SheetSpec(source="subsidiary", label="자회사투자"),
            SheetSpec(source="affiliate", label="관계기업투자"),
            SheetSpec(source="bond", label="채무증권"),
            SheetSpec(source="contingentLiability", label="우발부채"),
            SheetSpec(source="capitalChange", label="자본변동"),
            SheetSpec(source="fundraising", label="증자감자"),
            SheetSpec(source="relatedPartyTx", label="관계자거래"),
            SheetSpec(source="tangibleAsset", label="유형자산"),
            SheetSpec(source="costByNature", label="비용성격별분류"),
            SheetSpec(source="riskDerivative", label="위험관리"),
            SheetSpec(source="sanction", label="제재현황"),
            SheetSpec(source="affiliateGroup", label="계열사"),
            SheetSpec(source="internalControl", label="내부통제"),
            SheetSpec(source="salesOrder", label="매출수주"),
            SheetSpec(source="otherFinance", label="기타재무"),
            SheetSpec(source="companyHistory", label="연혁"),
        ],
    )


def _buildSummaryPreset() -> ExcelTemplate:
    """요약 프리셋 — 핵심 시트만."""
    return ExcelTemplate(
        name="요약",
        templateId="preset_summary",
        description="핵심 재무 데이터만 포함하는 요약 내보내기.",
        sheets=[
            SheetSpec(source="IS", label="손익계산서"),
            SheetSpec(source="BS", label="재무상태표"),
            SheetSpec(source="CF", label="현금흐름표"),
            SheetSpec(source="ratios", label="재무비율"),
            SheetSpec(source="dividend", label="배당"),
            SheetSpec(source="majorHolder", label="최대주주"),
        ],
    )


def _buildGovernancePreset() -> ExcelTemplate:
    """지배구조 프리셋."""
    return ExcelTemplate(
        name="지배구조",
        templateId="preset_governance",
        description="지배구조 관련 데이터 모음.",
        sheets=[
            SheetSpec(source="majorHolder", label="최대주주"),
            SheetSpec(source="executive", label="임원현황"),
            SheetSpec(source="executivePay", label="임원보수"),
            SheetSpec(source="boardOfDirectors", label="이사회"),
            SheetSpec(source="audit", label="감사의견"),
            SheetSpec(source="internalControl", label="내부통제"),
            SheetSpec(source="shareholderMeeting", label="주주총회"),
        ],
    )


PRESETS: dict[str, ExcelTemplate] = {
    "full": _buildFullPreset(),
    "summary": _buildSummaryPreset(),
    "governance": _buildGovernancePreset(),
}
