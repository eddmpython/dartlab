"""DART 정형공시와 narrative 추출 개념의 선언형 manifest."""

from __future__ import annotations

from dartlab.core.extractionCatalog.models import (
    DartSource,
    EdgarSource,
    ExtractionConcept,
    HonestNull,
)


def _report(
    conceptId: str,
    category: str,
    label: str,
    apiType: str,
    edgar: EdgarSource | HonestNull,
    *,
    axisType: str = "single",
    valueType: str = "amount",
) -> ExtractionConcept:
    """DART 정형공시 개념 한 행을 만든다."""
    return ExtractionConcept(
        conceptId=conceptId,
        category=category,
        label=label,
        dart=DartSource("report", apiType),
        edgar=edgar,
        axisType=axisType,
        valueType=valueType,
    )


def _narrative(
    conceptId: str,
    label: str,
    chapter: str,
    section: str,
    edgarItem: str | None,
    keyword: str,
    *,
    valueType: str = "text",
) -> ExtractionConcept:
    """SPINE anchor와 SEC Item을 연결한 narrative 개념 한 행을 만든다."""
    edgar: EdgarSource | HonestNull
    edgar = EdgarSource("item", (edgarItem,)) if edgarItem else HonestNull("대응 SEC Item 없음(P2 앵커추출)")
    return ExtractionConcept(
        conceptId=conceptId,
        category="narrative",
        label=label,
        dart=DartSource("narrative", section),
        edgar=edgar,
        axisType="text",
        valueType=valueType,
        narrativeAnchor=(chapter, keyword),
    )


GOVERNANCE: tuple[ExtractionConcept, ...] = (
    _report(
        "governance.majorHolder",
        "governance",
        "최대주주현황",
        "majorHolder",
        EdgarSource("proxy", ("BeneficialOwnership",)),
    ),
    _report(
        "governance.majorHolderChange",
        "governance",
        "최대주주변동",
        "majorHolderChange",
        HonestNull("US proxy 는 시점 보유만, 변동 이력 표 부재"),
    ),
    _report(
        "governance.minorityHolder",
        "governance",
        "소액주주현황",
        "minorityHolder",
        HonestNull("US 소액주주 분산 통계 공시 없음"),
    ),
    _report("governance.executive", "governance", "임원현황", "executive", EdgarSource("proxy", ("board",))),
    _report(
        "governance.outsideDirector",
        "governance",
        "사외이사현황",
        "outsideDirector",
        EdgarSource("proxy", ("board",)),
    ),
    _report(
        "governance.auditOpinion",
        "governance",
        "감사의견",
        "auditOpinion",
        EdgarSource("item", ("auditOpinion",)),
        valueType="text",
    ),
    _report(
        "governance.auditContract",
        "governance",
        "감사용역계약",
        "auditContract",
        EdgarSource("proxy", ("auditFees",)),
    ),
    _report(
        "governance.nonAuditContract",
        "governance",
        "비감사용역계약",
        "nonAuditContract",
        EdgarSource("proxy", ("auditFees",)),
    ),
)

CAPITAL: tuple[ExtractionConcept, ...] = (
    _report(
        "capital.dividend",
        "capital",
        "배당",
        "dividend",
        EdgarSource("xbrlTag", ("CommonStockDividendsPerShareDeclared", "PaymentsOfDividendsCommonStock")),
    ),
    _report(
        "capital.treasuryStock",
        "capital",
        "자기주식",
        "treasuryStock",
        EdgarSource("xbrlTag", ("TreasuryStockValue", "PaymentsForRepurchaseOfCommonStock")),
    ),
    _report(
        "capital.capitalChange",
        "capital",
        "증자감자현황",
        "capitalChange",
        EdgarSource("xbrlTag", ("StockIssuedDuringPeriodValueNewIssues", "StockRepurchasedDuringPeriodValue")),
    ),
    _report(
        "capital.stockTotal",
        "capital",
        "주식총수현황",
        "stockTotal",
        EdgarSource("xbrlTag", ("CommonStockSharesIssued", "CommonStockSharesOutstanding")),
    ),
)

WORKFORCE: tuple[ExtractionConcept, ...] = (
    _report(
        "workforce.employee",
        "workforce",
        "직원현황",
        "employee",
        EdgarSource("item", ("EntityNumberOfEmployees",)),
    ),
    _report(
        "workforce.executivePayTotal",
        "workforce",
        "임원보수총액",
        "executivePayAllTotal",
        EdgarSource("proxy", ("SCT",)),
    ),
    _report(
        "workforce.executivePayIndividual",
        "workforce",
        "임원보수개인별",
        "executivePayIndividual",
        EdgarSource("proxy", ("SCT",)),
    ),
    _report(
        "workforce.topPay",
        "workforce",
        "개인별보수(5억이상)",
        "topPay",
        HonestNull("US 는 named executive 5인만 공시, 일반 5억+ 개인 공시 없음"),
    ),
    _report(
        "workforce.unregisteredExecutivePay",
        "workforce",
        "미등기임원보수",
        "unregisteredExecutivePay",
        HonestNull("US 미등기임원 별도 공시 없음"),
    ),
    _report(
        "workforce.executivePayByType",
        "workforce",
        "임원보수유형별",
        "executivePayByType",
        EdgarSource("proxy", ("SCT",)),
    ),
    _report(
        "workforce.executivePayTotalApproved",
        "workforce",
        "임원보수총승인액",
        "executivePayTotal",
        HonestNull("US 는 주주 보수 승인총액 별도 공시 없음(say-on-pay 는 찬반 투표)"),
    ),
)

FILING: tuple[ExtractionConcept, ...] = (
    _report(
        "filing.publicOfferingUsage",
        "filingMeta",
        "공모자금사용내역",
        "publicOfferingUsage",
        HonestNull("US 는 S-1/424B use-of-proceeds 서술, DART 정형표 대응 부재"),
        valueType="text",
    ),
    _report(
        "filing.privateOfferingUsage",
        "filingMeta",
        "사모자금사용내역",
        "privateOfferingUsage",
        HonestNull("US 사모 자금사용 정형 공시 없음"),
        valueType="text",
    ),
)

DEBT: tuple[ExtractionConcept, ...] = (
    _report(
        "debt.corporateBond",
        "debt",
        "회사채미상환잔액",
        "corporateBond",
        EdgarSource(
            "xbrlTag",
            ("LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths", "DebtInstrumentFaceAmount"),
        ),
    ),
    _report(
        "debt.shortTermBond",
        "debt",
        "단기사채미상환잔액",
        "shortTermBond",
        EdgarSource("xbrlTag", ("ShortTermBorrowings",)),
    ),
    _report(
        "debt.commercialPaper",
        "debt",
        "기업어음미상환잔액",
        "commercialPaper",
        EdgarSource("xbrlTag", ("CommercialPaper",)),
    ),
    _report(
        "debt.hybridSecurities",
        "debt",
        "신종자본증권",
        "hybridSecurities",
        HonestNull("US 신종자본증권 별도 apiType 공시 없음"),
    ),
    _report(
        "debt.contingentCapital",
        "debt",
        "조건부자본증권",
        "contingentCapital",
        HonestNull("US 조건부자본증권 별도 공시 없음"),
    ),
    _report(
        "debt.debtSecurities",
        "debt",
        "채무증권발행실적",
        "debtSecurities",
        EdgarSource("xbrlTag", ("ProceedsFromIssuanceOfLongTermDebt",)),
    ),
)

SEGMENT: tuple[ExtractionConcept, ...] = (
    ExtractionConcept(
        "segment.salesByProduct",
        "segment",
        "제품별매출구성",
        DartSource("segmentTable", "salesByProduct"),
        EdgarSource("deraFacts", ("BusinessSegments",)),
        axisType="multiAxis",
    ),
    _report(
        "network.investedCompany",
        "segment",
        "타법인출자현황",
        "investedCompany",
        HonestNull("US EX-21 은 자회사 이름+관할만, 장부가/지분% 부재"),
    ),
)

NARRATIVE: tuple[ExtractionConcept, ...] = (
    _narrative("narrative.businessOverview", "사업의개요", "II", "businessOverview", "Item1Business", "사업의 개요"),
    _narrative(
        "narrative.salesOrder",
        "매출및수주상황",
        "II",
        "salesOrder",
        None,
        "매출 및 수주",
        valueType="amount",
    ),
    _narrative(
        "narrative.productionCapacity",
        "생산능력및가동률",
        "II",
        "productionCapacity",
        None,
        "생산설비",
        valueType="amount",
    ),
    _narrative(
        "narrative.rawMaterial",
        "원재료및생산설비",
        "II",
        "rawMaterial",
        None,
        "원재료",
        valueType="amount",
    ),
    _narrative(
        "narrative.riskFactors",
        "위험요소",
        "II",
        "riskFactors",
        "Item1ARiskFactors",
        "위험관리",
    ),
    _narrative("narrative.mdna", "경영진단및분석", "IV", "mdna", "Item7MDA", "경영진단"),
    _narrative("narrative.rnd", "연구개발활동", "II", "rnd", None, "연구개발"),
    _narrative("narrative.majorContracts", "주요계약", "II", "majorContracts", None, "주요계약"),
    _narrative(
        "narrative.governanceText",
        "지배구조서술",
        "VI",
        "governanceText",
        "Item10Governance",
        "이사회",
    ),
    _narrative("narrative.environment", "환경규제", "II", "environment", None, "환경"),
)

__all__ = [
    "CAPITAL",
    "DEBT",
    "FILING",
    "GOVERNANCE",
    "NARRATIVE",
    "SEGMENT",
    "WORKFORCE",
]
