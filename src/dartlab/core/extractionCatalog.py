"""추출 개념 카탈로그 SSOT (L0 정적 매니페스트).

provider panel/report 에서 빼먹을 수 있는 모든 정보를 EDGAR·DART 동급으로 한 곳에 카테고리화한다.
흩어진 레지스트리(core/_entries notes 12 + report 28 apiType + edgar `_CATEGORY_TAGS` 12)를 참조하고
EDGAR 열 + parity 판정 + narrativeAnchor 를 ADD 한 단일 진실의 원천이다.

**계층 정합 (L0)**: 순수 데이터(dataclass + 문자열 상수)만 보유하고 provider import 가 0 이라 core(L0)에
잔류한다. frame(조립 L1.5)·providers(추출 L1)·scan(횡단 L1.5)·L2 분석엔진 모두 합법 소비 가능. 카탈로그를
reference(L1.5)에 두면 frame 이 `frame ↛ reference` 4형제 cross 금지로 읽지 못하므로 L0 가 유일 정답이다.

**성공 정의 (엔진차원 TODO)**: `tests/audit/extractionCoverageCensus.py` 가 본 매니페스트 vs 실제 추출을
전종목·양 provider 로 대조해 개념별 원장을 만든다. 성공 = 전 개념이 (추출됨) 또는 (기록된 정직-null).

**무bake**: 카탈로그는 정적 상수. 추출은 런타임이 SSOT(panel/report/finance)에서 직독한다.

SeeAlso:
    - `dartlab.providers.dart.notes` (DART 노트 dispatch, registry 구동).
    - `dartlab.providers.edgar.docs.notesParsers._CATEGORY_TAGS` (EDGAR 노트 태그 정본, 본 모듈이 미러·수렴).
    - `mainPlan/panel-extraction-workbench-ssot/00-prd.md` (설계 정본).
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES: tuple[str, ...] = (
    "financialStatement",
    "note",
    "governance",
    "capital",
    "workforce",
    "debt",
    "segment",
    "narrative",
    "filingMeta",
)

# 축유형 / 값유형 어휘 (카탈로그 불변식 검증에 사용).
AXIS_TYPES: tuple[str, ...] = ("single", "multiAxis", "movement", "text")
VALUE_TYPES: tuple[str, ...] = ("amount", "rate", "text")


@dataclass(frozen=True)
class DartSource:
    """DART 추출 표면 참조.

    surface 는 note(NT_ canonicalKey) · report(apiType) · statement(재무 5표 논리키) ·
    narrative(SPINE 앵커 섹션) · segmentTable 중 하나. key 는 그 표면의 식별자.
    """

    surface: str
    key: str
    dispatch: tuple[str, str] | None = None


@dataclass(frozen=True)
class EdgarSource:
    """EDGAR 추출 표면 참조.

    surface 는 xbrlTag(us-gaap fact) · deraFacts(DERA num+dim) · proxy(DEF 14A 파싱) ·
    item(SEC Item 택소노미) · statement 중 하나. keys 는 us-gaap 태그 후보 또는 Item id 튜플.
    """

    surface: str
    keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class HonestNull:
    """구조적 부재의 정직 기록. 능력부족 포장이 아니라 원천 공시에 존재하지 않음을 사유와 함께 명시."""

    reason: str


@dataclass(frozen=True)
class ExtractionConcept:
    """추출가능 개념 1건 (카탈로그 최소 단위).

    conceptId 는 안정 식별자, category 는 9 대분류, dart/edgar 는 양 provider 표면 또는 부재.
    axisType 는 single|multiAxis|movement|text, valueType 는 amount|rate|text.
    narrativeAnchor 는 (chapterCanonical, sectionCore) 로 narrative 개념만 보유.
    registered 는 first-class 이름 접근 가능 여부(노트 개념만 의미). 레거시 core/_entries notes 12 또는
    catalog 라우팅(`resolveNoteKey` -> panel canonicalKey 폴백)으로 `c.panel(이름)` 도달 가능하면 True.
    """

    conceptId: str
    category: str
    label: str
    dart: DartSource | None
    edgar: EdgarSource | HonestNull | None
    axisType: str = "single"
    valueType: str = "amount"
    narrativeAnchor: tuple[str, str] | None = None
    registered: bool = False

    def parity(self) -> str:
        """이 개념의 DART/EDGAR parity 상태 문자열을 반환한다.

        Returns:
            "both"(양 provider 추출경로) · "dartOnly"(EDGAR 구조부재) · "edgarOnly" ·
            "narrative"(SPINE 앵커 정성) · "none".
        """
        hasDart = isinstance(self.dart, DartSource)
        hasEdgar = isinstance(self.edgar, EdgarSource)
        edgarNull = isinstance(self.edgar, HonestNull)
        if self.category == "narrative":
            return "narrative"
        if hasDart and hasEdgar:
            return "both"
        if hasDart and (edgarNull or self.edgar is None):
            return "dartOnly"
        if hasEdgar and not hasDart:
            return "edgarOnly"
        return "none"

    def toDict(self) -> dict:
        """직렬화용 dict 로 변환한다 (census/tests JSON 출력).

        Returns:
            conceptId·category·label·axisType·valueType·registered·parity + dart/edgar 요약 dict.
        """
        return {
            "conceptId": self.conceptId,
            "category": self.category,
            "label": self.label,
            "axisType": self.axisType,
            "valueType": self.valueType,
            "registered": self.registered,
            "narrativeAnchor": list(self.narrativeAnchor) if self.narrativeAnchor else None,
            "parity": self.parity(),
            "dart": None if self.dart is None else {"surface": self.dart.surface, "key": self.dart.key},
            "edgar": _edgarToDict(self.edgar),
        }


def _edgarToDict(edgar: EdgarSource | HonestNull | None) -> dict | None:
    """EdgarSource/HonestNull 을 직렬화 dict 로."""
    if isinstance(edgar, EdgarSource):
        return {"surface": edgar.surface, "keys": list(edgar.keys)}
    if isinstance(edgar, HonestNull):
        return {"surface": "honestNull", "reason": edgar.reason}
    return None


# EDGAR 노트 태그 SSOT. providers/edgar/docs/notesParsers._CATEGORY_TAGS 정본 미러.
# 12 등록 카테고리는 정본을 충실히 복사(추출 무회귀). test_extractionCatalog 의 드리프트 가드가
# 정본과 동일함을 강제(양쪽 수렴). 신규 10 노트는 본 카탈로그가 SSOT.
_EDGAR_NOTE_TAGS: dict[str, tuple[str, ...]] = {
    "inventory": (
        "InventoryFinishedGoods",
        "InventoryWorkInProcess",
        "InventoryRawMaterials",
        "InventoryNet",
        "InventoryGross",
        "InventoryAdjustments",
        "InventoryValuationReserves",
    ),
    "borrowings": (
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermDebtCurrent",
        "ShortTermBorrowings",
        "LinesOfCreditCurrent",
        "CommercialPaper",
        "NotesPayable",
        "SecuredDebt",
        "UnsecuredDebt",
    ),
    "tangibleAsset": (
        "PropertyPlantAndEquipmentGross",
        "PropertyPlantAndEquipmentNet",
        "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
        "Land",
        "BuildingsAndImprovementsGross",
        "MachineryAndEquipmentGross",
        "ConstructionInProgressGross",
        "LeaseholdImprovementsGross",
    ),
    "intangibleAsset": (
        "Goodwill",
        "IntangibleAssetsNetExcludingGoodwill",
        "FiniteLivedIntangibleAssetsGross",
        "FiniteLivedIntangibleAssetsAccumulatedAmortization",
        "FiniteLivedIntangibleAssetsNet",
        "IndefiniteLivedIntangibleAssetsExcludingGoodwill",
        "CapitalizedComputerSoftwareGross",
        "CapitalizedComputerSoftwareNet",
    ),
    "receivables": (
        "AccountsReceivableNetCurrent",
        "AccountsReceivableGrossCurrent",
        "AllowanceForDoubtfulAccountsReceivableCurrent",
        "NotesReceivableNet",
        "ReceivablesNetCurrent",
    ),
    "provisions": (
        "ProductWarrantyAccrual",
        "LossContingencyAccrualAtCarryingValue",
        "RestructuringReserve",
        "EnvironmentalLossContingencyStatementOfFinancialPositionAccrual",
        "LitigationReserve",
        "AccruedLiabilitiesCurrent",
    ),
    "eps": (
        "EarningsPerShareBasic",
        "EarningsPerShareDiluted",
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount",
    ),
    "segments": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SegmentReportingInformationOperatingIncomeLoss",
        "SegmentReportingInformationRevenue",
    ),
    "costByNature": (
        "CostOfGoodsAndServicesSold",
        "SellingGeneralAndAdministrativeExpense",
        "ResearchAndDevelopmentExpense",
        "DepreciationAndAmortization",
        "LaborAndRelatedExpense",
        "AdvertisingExpense",
    ),
    "lease": (
        "OperatingLeaseRightOfUseAsset",
        "OperatingLeaseLiability",
        "FinanceLeaseRightOfUseAsset",
        "FinanceLeaseLiability",
        "OperatingLeasePayments",
        "OperatingLeaseCost",
    ),
    "affiliates": (
        "InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures",
        "EquityMethodInvestments",
        "EquityMethodInvestmentRealizedGainLossOnDisposal",
        "IncomeLossFromEquityMethodInvestments",
        "EquityMethodInvestmentDividendsOrDistributions",
        "EquityMethodInvestmentOwnershipPercentage",
        "PaymentsToAcquireEquityMethodInvestments",
        "PaymentsToAcquireBusinessesAndInterestInAffiliates",
        "EquityMethodInvestmentOtherThanTemporaryImpairment",
    ),
    "investmentProperty": (
        "RealEstateInvestmentPropertyNet",
        "RealEstateInvestmentPropertyAtCost",
        "RealEstateInvestmentPropertyAccumulatedDepreciation",
        "RealEstateInvestmentPropertyAtFairValue",
        "RealEstateHeldsale",
    ),
}


def _note(
    conceptId: str,
    label: str,
    dartKey: str,
    edgarTags: tuple[str, ...],
    *,
    axisType: str = "multiAxis",
    valueType: str = "amount",
    registered: bool = False,
    edgarNull: str | None = None,
) -> ExtractionConcept:
    """K-IFRS note 개념 생성 헬퍼 (내부)."""
    edgar: EdgarSource | HonestNull
    edgar = HonestNull(reason=edgarNull) if edgarNull is not None else EdgarSource("xbrlTag", edgarTags)
    return ExtractionConcept(
        conceptId=conceptId,
        category="note",
        label=label,
        dart=DartSource("note", dartKey),
        edgar=edgar,
        axisType=axisType,
        valueType=valueType,
        registered=registered,
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
    """DART 정형공시(apiType) 개념 생성 헬퍼 (내부)."""
    return ExtractionConcept(
        conceptId=conceptId,
        category=category,
        label=label,
        dart=DartSource("report", apiType),
        edgar=edgar,
        axisType=axisType,
        valueType=valueType,
    )


def _narr(
    conceptId: str,
    label: str,
    chapter: str,
    section: str,
    edgarItem: str | None,
    keyword: str,
    *,
    valueType: str = "text",
) -> ExtractionConcept:
    """narrative 개념 생성 헬퍼 (SPINE 앵커 + EDGAR Item, 내부).

    narrativeAnchor = (chapterRoman, sectionLeaf 한글 키워드). keyword 는 panel sectionLeaf 실측
    매처(era/회사 무관 견고). frame.narrative.extractNarrative 가 이 앵커로 단일 메커니즘 추출.
    """
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


_STATEMENTS: list[ExtractionConcept] = [
    ExtractionConcept(
        "statement.is",
        "financialStatement",
        "손익계산서",
        DartSource("statement", "is"),
        EdgarSource("statement", ("Revenues", "NetIncomeLoss", "OperatingIncomeLoss")),
    ),
    ExtractionConcept(
        "statement.bs",
        "financialStatement",
        "재무상태표",
        DartSource("statement", "bs"),
        EdgarSource("statement", ("Assets", "Liabilities", "StockholdersEquity")),
    ),
    ExtractionConcept(
        "statement.cf",
        "financialStatement",
        "현금흐름표",
        DartSource("statement", "cf"),
        EdgarSource("statement", ("NetCashProvidedByUsedInOperatingActivities",)),
    ),
    ExtractionConcept(
        "statement.cis",
        "financialStatement",
        "포괄손익계산서",
        DartSource("statement", "cis"),
        EdgarSource("statement", ("ComprehensiveIncomeNetOfTax",)),
    ),
    ExtractionConcept(
        "statement.sce",
        "financialStatement",
        "자본변동표",
        DartSource("statement", "sce"),
        EdgarSource("statement", ("StockholdersEquity",)),
    ),
    ExtractionConcept(
        "statement.ratios",
        "financialStatement",
        "재무비율",
        DartSource("statement", "ratios"),
        EdgarSource("statement", ("Revenues", "Assets", "StockholdersEquity")),
        valueType="rate",
    ),
]

_NOTES: list[ExtractionConcept] = [
    # registered 12 (core/_entries/notes.py). EDGAR 태그는 _EDGAR_NOTE_TAGS 정본.
    _note("note.inventory", "재고자산", "NT_D826380", _EDGAR_NOTE_TAGS["inventory"], registered=True),
    _note("note.receivables", "매출채권", "NT_D822420", _EDGAR_NOTE_TAGS["receivables"], registered=True),
    _note(
        "note.tangibleAsset",
        "유형자산",
        "NT_D822100",
        _EDGAR_NOTE_TAGS["tangibleAsset"],
        axisType="movement",
        registered=True,
    ),
    _note("note.intangibleAsset", "무형자산", "NT_D823180", _EDGAR_NOTE_TAGS["intangibleAsset"], registered=True),
    _note(
        "note.investmentProperty", "투자부동산", "NT_D825900", _EDGAR_NOTE_TAGS["investmentProperty"], registered=True
    ),
    _note(
        "note.affiliates",
        "관계기업",
        "NT_D825700",
        _EDGAR_NOTE_TAGS["affiliates"],
        axisType="movement",
        registered=True,
    ),
    _note("note.borrowings", "차입금", "NT_D822400", _EDGAR_NOTE_TAGS["borrowings"], registered=True),
    _note("note.provisions", "충당부채", "NT_D827570", _EDGAR_NOTE_TAGS["provisions"], registered=True),
    _note("note.eps", "주당이익", "NT_D838000", _EDGAR_NOTE_TAGS["eps"], registered=True),
    _note("note.lease", "리스", "NT_D832610", _EDGAR_NOTE_TAGS["lease"], registered=True),
    _note("note.segments", "영업부문(주석)", "NT_D871100", _EDGAR_NOTE_TAGS["segments"], registered=True),
    _note("note.costByNature", "비용의성격별분류", "NT_D834300", _EDGAR_NOTE_TAGS["costByNature"], registered=True),
    # high-value 10 (P1 등록: 실측 확인 Samsung panel NT_ 실재 + canonicalKey 추출 검증). 본 카탈로그가 SSOT.
    _note(
        "note.regionalRevenue",
        "지역별매출",
        "NT_D831150",
        ("RevenueFromContractWithCustomerExcludingAssessedTax",),
        registered=True,
    ),
    _note(
        "note.sgAndA",
        "판매비와관리비",
        "NT_D834310",
        ("SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"),
        registered=True,
    ),
    _note(
        "note.employeeBenefits",
        "종업원급여",
        "NT_D834480",
        ("DefinedBenefitPlanBenefitObligation", "DefinedBenefitPlanFairValueOfPlanAssets", "LaborAndRelatedExpense"),
        registered=True,
    ),
    _note(
        "note.financialIncomeExpense",
        "금융수익금융비용",
        "NT_D834330",
        ("InterestExpense", "InvestmentIncomeInterest", "InterestIncomeExpenseNet"),
        registered=True,
    ),
    _note(
        "note.relatedParty",
        "특수관계자거래",
        "NT_D818000",
        ("RelatedPartyTransactionAmountsOfTransaction", "RelatedPartyTransactionDueFromToRelatedPartyCurrent"),
        registered=True,
    ),
    _note(
        "note.tax",
        "법인세",
        "NT_D835110",
        ("IncomeTaxExpenseBenefit", "DeferredTaxAssetsNet", "CurrentIncomeTaxExpenseBenefit"),
        registered=True,
    ),
    _note(
        "note.contingencies",
        "우발부채약정",
        "NT_D827580",
        ("LossContingencyEstimateOfPossibleLoss", "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount"),
        valueType="text",
        registered=True,
    ),
    _note(
        "note.financialInstruments",
        "금융상품범주별",
        "NT_D822430",
        ("FinancialInstrumentsOwnedAtFairValue", "AvailableForSaleSecurities"),
        registered=True,
    ),
    _note(
        "note.capitalReserves",
        "자본및자본잉여금",
        "NT_D861200",
        ("AdditionalPaidInCapital", "CommonStockValue"),
        axisType="movement",
        registered=True,
    ),
    _note(
        "note.retainedEarnings",
        "이익잉여금",
        "NT_D861300",
        ("RetainedEarningsAccumulatedDeficit",),
        axisType="movement",
        registered=True,
    ),
    # 미등록 유지: dart 표본 커버리지 sparse(NT_D834120 비표준 배치). 정직 보류.
    _note(
        "note.shareBasedComp",
        "주식기준보상",
        "NT_D834120",
        ("ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"),
    ),
    # 완전성 충전 배치 2 (census 미카탈로그 탐지 -> 실측 라벨링, 표본 다빈도 고가치 IFRS 노트).
    _note(
        "note.financialRiskMgmt",
        "재무위험관리",
        "NT_D822390",
        (),
        valueType="text",
        edgarNull="US 는 파생상품·공정가치 노트로 분산, 단일 재무위험관리 fact 부재",
        registered=True,
    ),
    _note(
        "note.cashAndEquivalents",
        "현금및현금성자산",
        "NT_D822410",
        ("CashAndCashEquivalentsAtCarryingValue", "RestrictedCashAndCashEquivalents"),
        registered=True,
    ),
    _note(
        "note.otherIncomeExpense",
        "기타수익및기타비용",
        "NT_D834320",
        ("OtherNonoperatingIncomeExpense", "OtherOperatingIncomeExpenseNet"),
        registered=True,
    ),
    _note(
        "note.businessCombination",
        "사업결합",
        "NT_D817000",
        (
            "BusinessCombinationRecognizedIdentifiableAssetsAcquiredAndLiabilitiesAssumedNet",
            "BusinessCombinationConsiderationTransferred1",
        ),
        registered=True,
    ),
    _note(
        "note.subsequentEvents",
        "보고기간후사건",
        "NT_D815000",
        (),
        valueType="text",
        edgarNull="US SubsequentEvents 는 서술 TextBlock(수치 fact 부재)",
        registered=True,
    ),
    _note(
        "note.otherEquity",
        "기타자본항목",
        "NT_D861400",
        ("AccumulatedOtherComprehensiveIncomeLossNetOfTax",),
        axisType="movement",
        registered=True,
    ),
    _note(
        "note.restrictedFinancial",
        "사용제한금융상품",
        "NT_D822470",
        ("RestrictedCashAndCashEquivalents", "RestrictedCash"),
        registered=True,
    ),
    _note(
        "note.otherAssets",
        "기타유동및비유동자산",
        "NT_D822300",
        ("OtherAssetsCurrent", "OtherAssetsNoncurrent"),
        registered=True,
    ),
    _note(
        "note.otherLiabilities",
        "기타유동및비유동부채",
        "NT_D822310",
        ("OtherLiabilitiesCurrent", "OtherLiabilitiesNoncurrent"),
        registered=True,
    ),
    _note(
        "note.accountingPolicies",
        "유의적회계정책",
        "NT_D810000",
        (),
        valueType="text",
        edgarNull="US SignificantAccountingPolicies 는 서술 TextBlock(수치 fact 부재)",
        registered=True,
    ),
]

_GOVERNANCE: list[ExtractionConcept] = [
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
        "governance.outsideDirector", "governance", "사외이사현황", "outsideDirector", EdgarSource("proxy", ("board",))
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
        "governance.auditContract", "governance", "감사용역계약", "auditContract", EdgarSource("proxy", ("auditFees",))
    ),
    _report(
        "governance.nonAuditContract",
        "governance",
        "비감사용역계약",
        "nonAuditContract",
        EdgarSource("proxy", ("auditFees",)),
    ),
]

_CAPITAL: list[ExtractionConcept] = [
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
]

_WORKFORCE: list[ExtractionConcept] = [
    _report(
        "workforce.employee", "workforce", "직원현황", "employee", EdgarSource("item", ("EntityNumberOfEmployees",))
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
]

# filingMeta (공시 이벤트/자금사용). census 미카탈로그 탐지가 드러낸 apiType 충전.
_FILING: list[ExtractionConcept] = [
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
]

_DEBT: list[ExtractionConcept] = [
    _report(
        "debt.corporateBond",
        "debt",
        "회사채미상환잔액",
        "corporateBond",
        EdgarSource(
            "xbrlTag", ("LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths", "DebtInstrumentFaceAmount")
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
]

_SEGMENT: list[ExtractionConcept] = [
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
]

_NARRATIVE: list[ExtractionConcept] = [
    _narr("narrative.businessOverview", "사업의개요", "II", "businessOverview", "Item1Business", "사업의 개요"),
    _narr("narrative.salesOrder", "매출및수주상황", "II", "salesOrder", None, "매출 및 수주", valueType="amount"),
    _narr(
        "narrative.productionCapacity",
        "생산능력및가동률",
        "II",
        "productionCapacity",
        None,
        "생산설비",
        valueType="amount",
    ),
    _narr("narrative.rawMaterial", "원재료및생산설비", "II", "rawMaterial", None, "원재료", valueType="amount"),
    _narr("narrative.riskFactors", "위험요소", "II", "riskFactors", "Item1ARiskFactors", "위험관리"),
    _narr("narrative.mdna", "경영진단및분석", "IV", "mdna", "Item7MDA", "경영진단"),
    _narr("narrative.rnd", "연구개발활동", "II", "rnd", None, "연구개발"),
    _narr("narrative.majorContracts", "주요계약", "II", "majorContracts", None, "주요계약"),
    _narr("narrative.governanceText", "지배구조서술", "VI", "governanceText", "Item10Governance", "이사회"),
    _narr("narrative.environment", "환경규제", "II", "environment", None, "환경"),
]

_CONCEPTS: list[ExtractionConcept] = (
    _STATEMENTS + _NOTES + _GOVERNANCE + _CAPITAL + _WORKFORCE + _DEBT + _SEGMENT + _NARRATIVE + _FILING
)
_INDEX: dict[str, ExtractionConcept] = {c.conceptId: c for c in _CONCEPTS}

# 노트 별칭 -> canonicalKey(NT_) 역인덱스. conceptId · bareName · 한글 label 3 형태를 받는다.
# 견고한 접근 경로(panel 폴백)가 소비: 사용자가 NT_ 코드를 몰라도 이름으로 노트 도달.
_NOTE_ALIAS: dict[str, str] = {}
for _c in _CONCEPTS:
    if _c.category == "note" and isinstance(_c.dart, DartSource):
        _NOTE_ALIAS[_c.conceptId] = _c.dart.key
        _NOTE_ALIAS[_c.conceptId.removeprefix("note.")] = _c.dart.key
        _NOTE_ALIAS[_c.label] = _c.dart.key


def resolveNoteKey(key: str) -> str | None:
    """노트 conceptId/bareName/한글라벨 을 canonicalKey(NT_) 로 해소한다.

    panel 표면이 견고한 이름 접근(사용자가 NT_ 코드 미상)을 위해 폴백으로 소비한다.

    Args:
        key: "note.regionalRevenue" · "regionalRevenue" · "지역별매출" 중 하나.

    Returns:
        canonicalKey("NT_D831150") 또는 None(미매칭).

    Raises:
        없음.

    Example:
        >>> resolveNoteKey("지역별매출")
        'NT_D831150'
        >>> resolveNoteKey("note.tax")
        'NT_D835110'
    """
    return _NOTE_ALIAS.get(key)


def getExtractionConcepts(*, category: str | None = None) -> list[ExtractionConcept]:
    """추출 개념 전체(또는 카테고리별)를 반환한다.

    Args:
        category: 9 대분류 중 하나로 필터(None 이면 전체).

    Returns:
        ExtractionConcept 리스트(정의 순서 보존).

    Raises:
        없음. 미등록 category 는 빈 리스트.

    Example:
        >>> from dartlab.core.extractionCatalog import getExtractionConcepts
        >>> len(getExtractionConcepts(category="note")) >= 22
        True

    Capabilities:
        - 카탈로그 SSOT 조회 단일 진입점. census·workbench·parity 판정이 소비.

    Guide:
        - "노트 개념 목록" 은 ``getExtractionConcepts(category="note")``.
        - "전 개념" 은 ``getExtractionConcepts()``.

    AIContext:
        데이터 워크벤치가 "이 회사에서 뭘 뽑을 수 있나" 카탈로그를 제시할 때 호출.

    Requires:
        - 외부 의존 0 (L0 정적 데이터).
    """
    if category is None:
        return list(_CONCEPTS)
    return [c for c in _CONCEPTS if c.category == category]


def getConcept(conceptId: str) -> ExtractionConcept | None:
    """conceptId 로 단일 개념을 조회한다.

    Args:
        conceptId: 안정 식별자(예 "note.regionalRevenue").

    Returns:
        ExtractionConcept 또는 None(미등록).

    Raises:
        없음.

    Example:
        >>> getConcept("note.tax").label
        '법인세'
    """
    return _INDEX.get(conceptId)


def conceptsByCategory() -> dict[str, list[ExtractionConcept]]:
    """카테고리별 개념 그룹 dict 를 반환한다.

    Returns:
        {category: [ExtractionConcept, ...]} (9 카테고리 키 상주).

    Raises:
        없음.

    Example:
        >>> conceptsByCategory()["financialStatement"][0].conceptId
        'statement.is'
    """
    out: dict[str, list[ExtractionConcept]] = {c: [] for c in CATEGORIES}
    for c in _CONCEPTS:
        out.setdefault(c.category, []).append(c)
    return out


def edgarTagsFor(category: str) -> tuple[str, ...]:
    """12 등록 노트 카테고리의 EDGAR us-gaap 태그 정본을 반환한다.

    providers/edgar/docs/notesParsers 가 본 함수로 수렴해 `_CATEGORY_TAGS` 중복을 제거하는 SSOT 진입점.

    Args:
        category: 노트 카테고리(inventory·borrowings 등 12 종).

    Returns:
        us-gaap 태그 튜플(미등록 카테고리는 빈 튜플).

    Raises:
        없음.

    Example:
        >>> "InventoryNet" in edgarTagsFor("inventory")
        True
    """
    return _EDGAR_NOTE_TAGS.get(category, ())


def parityMatrix() -> dict[str, list[str]]:
    """parity 상태별 conceptId 목록을 반환한다 (both/dartOnly/edgarOnly/narrative/none).

    Returns:
        {parityStatus: [conceptId, ...]}.

    Raises:
        없음.

    Example:
        >>> "statement.is" in parityMatrix()["both"]
        True
    """
    out: dict[str, list[str]] = {}
    for c in _CONCEPTS:
        out.setdefault(c.parity(), []).append(c.conceptId)
    return out


def catalogSummary() -> dict:
    """카탈로그 요약 통계(총계·카테고리별·parity 분해)를 반환한다.

    Returns:
        total·byCategory·parity·registeredNotes·honestNull 키를 가진 dict.

    Raises:
        없음.

    Example:
        >>> catalogSummary()["total"] >= 60
        True
    """
    byCat = {k: len(v) for k, v in conceptsByCategory().items()}
    par = {k: len(v) for k, v in parityMatrix().items()}
    registered = [c.conceptId for c in _CONCEPTS if c.registered]
    honestNull = [c.conceptId for c in _CONCEPTS if isinstance(c.edgar, HonestNull)]
    return {
        "total": len(_CONCEPTS),
        "byCategory": byCat,
        "parity": par,
        "registeredNotes": registered,
        "honestNull": honestNull,
    }
