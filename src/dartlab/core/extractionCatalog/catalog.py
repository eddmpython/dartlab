"""추출 concept manifest 조립, fail-fast index, immutable 조회 API."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TypedDict, overload

from dartlab.core.extractionCatalog.disclosureManifest import (
    CAPITAL,
    DEBT,
    FILING,
    GOVERNANCE,
    NARRATIVE,
    SEGMENT,
    WORKFORCE,
)
from dartlab.core.extractionCatalog.models import (
    CATEGORIES,
    DartSource,
    EdgarSource,
    ExtractionConcept,
    HonestNull,
)
from dartlab.core.extractionCatalog.noteManifest import (
    EDGAR_NOTE_TAGS,
    NOTES,
    STATEMENTS,
)

# providers.edgar.docs.sections.topics의 10-K/10-Q Item taxonomy mirror.
# L0가 L1을 import하지 않으므로 provider 순서에서 소비 방향을 수렴할 때까지 drift Guard로 보호한다.
_EDGAR_ITEM_CATEGORY: Mapping[str, str] = MappingProxyType(
    {
        "item1Business": "narrative",
        "item1ARiskFactors": "narrative",
        "item1BUnresolvedStaffComments": "filingMeta",
        "item1CCybersecurity": "narrative",
        "item1DExecutiveOfficers": "governance",
        "item2Properties": "narrative",
        "item3LegalProceedings": "narrative",
        "item4MineSafetyDisclosures": "filingMeta",
        "item4AExecutiveOfficersOfTheRegistrant": "governance",
        "item5MarketForCommonEquity": "capital",
        "item6Reserved": "financialStatement",
        "item7Mdna": "narrative",
        "item7AMarketRiskDisclosures": "narrative",
        "item8FinancialStatements": "financialStatement",
        "item9ChangesInAccountants": "governance",
        "item9AControlsAndProcedures": "governance",
        "item9BOtherInformation": "filingMeta",
        "item9CForeignJurisdictionDisclosures": "filingMeta",
        "item10DirectorsAndCorporateGovernance": "governance",
        "item11ExecutiveCompensation": "workforce",
        "item12SecurityOwnership": "governance",
        "item13RelatedTransactions": "governance",
        "item14PrincipalAccountantFees": "governance",
        "item15ExhibitsAndSchedules": "filingMeta",
        "item16Form10KSummary": "filingMeta",
        "item103EnvironmentalDisclosure": "narrative",
        "item405RegulationSKDisclosure": "governance",
        "item406RegulationSKCodeOfEthics": "governance",
        "partIItem1FinancialStatements": "financialStatement",
        "partIItem2Mdna": "narrative",
        "partIItem3MarketRisk": "narrative",
        "partIItem4ControlsAndProcedures": "governance",
        "partIIItem1LegalProceedings": "narrative",
        "partIIItem1ARiskFactors": "narrative",
        "partIIItem2UnregisteredSalesAndUseOfProceeds": "capital",
        "partIIItem3DefaultsUponSeniorSecurities": "debt",
        "partIIItem4MineSafetyDisclosures": "filingMeta",
        "partIIItem5OtherInformation": "filingMeta",
        "partIIItem6Exhibits": "filingMeta",
    }
)


def _edgarItem(conceptId: str, category: str, label: str, topicId: str, dartNull: str) -> ExtractionConcept:
    """DART에 구조적 대응이 없는 SEC Item concept를 만든다."""
    return ExtractionConcept(
        conceptId=conceptId,
        category=category,
        label=label,
        dart=HonestNull(dartNull),
        edgar=EdgarSource("item", (topicId,)),
        axisType="text",
        valueType="text",
    )


_EDGAR_ITEMS: tuple[ExtractionConcept, ...] = (
    _edgarItem(
        "edgar.unresolvedComments",
        "filingMeta",
        "SEC 미해소 지적사항",
        "item1BUnresolvedStaffComments",
        "DART 는 SEC comment-letter 절차 대응 공시 없음",
    ),
    _edgarItem(
        "edgar.cybersecurity",
        "narrative",
        "사이버보안(Item 1C)",
        "item1CCybersecurity",
        "DART 정형 사이버보안 섹션 부재(사업의 내용에 산발 기재)",
    ),
    _edgarItem(
        "edgar.mineSafety",
        "filingMeta",
        "광산안전 공시",
        "item4MineSafetyDisclosures",
        "DART 는 Dodd-Frank 광산안전 대응 공시 없음",
    ),
    _edgarItem(
        "edgar.otherInformation",
        "filingMeta",
        "기타정보(Item 9B)",
        "item9BOtherInformation",
        "DART 대응 catch-all 정형 섹션 부재",
    ),
    _edgarItem(
        "edgar.foreignJurisdiction",
        "filingMeta",
        "외국관할 검사방해 공시(HFCAA)",
        "item9CForeignJurisdictionDisclosures",
        "DART 는 HFCAA 대응 공시 없음",
    ),
    _edgarItem(
        "edgar.form10kSummary",
        "filingMeta",
        "10-K 요약(임의)",
        "item16Form10KSummary",
        "DART 대응 임의 요약 섹션 부재",
    ),
    _edgarItem(
        "edgar.section16Compliance",
        "governance",
        "내부자 신고 준수(Sec 16)",
        "item405RegulationSKDisclosure",
        "DART 는 Section 16 지연신고 정형 공시 없음",
    ),
    _edgarItem(
        "edgar.codeOfEthics",
        "governance",
        "윤리강령(Item 406)",
        "item406RegulationSKCodeOfEthics",
        "DART 정형 윤리강령 섹션 부재(지배구조에 산발 기재)",
    ),
)

_EDGAR_ITEM_PRIMARY: Mapping[str, str] = MappingProxyType(
    {
        "item1Business": "narrative.businessOverview",
        "item1ARiskFactors": "narrative.riskFactors",
        "item1CCybersecurity": "edgar.cybersecurity",
        "item1DExecutiveOfficers": "governance.executive",
        "item1BUnresolvedStaffComments": "edgar.unresolvedComments",
        "item2Properties": "narrative.rawMaterial",
        "item3LegalProceedings": "note.contingencies",
        "item4MineSafetyDisclosures": "edgar.mineSafety",
        "item4AExecutiveOfficersOfTheRegistrant": "governance.executive",
        "item5MarketForCommonEquity": "capital.dividend",
        "item6Reserved": "statement.ratios",
        "item7Mdna": "narrative.mdna",
        "item7AMarketRiskDisclosures": "note.financialRiskMgmt",
        "item8FinancialStatements": "statement.bs",
        "item9ChangesInAccountants": "governance.auditContract",
        "item9AControlsAndProcedures": "governance.auditOpinion",
        "item9BOtherInformation": "edgar.otherInformation",
        "item9CForeignJurisdictionDisclosures": "edgar.foreignJurisdiction",
        "item10DirectorsAndCorporateGovernance": "narrative.governanceText",
        "item11ExecutiveCompensation": "workforce.executivePayTotal",
        "item12SecurityOwnership": "governance.majorHolder",
        "item13RelatedTransactions": "note.relatedParty",
        "item14PrincipalAccountantFees": "governance.auditContract",
        "item15ExhibitsAndSchedules": "narrative.majorContracts",
        "item16Form10KSummary": "edgar.form10kSummary",
        "item103EnvironmentalDisclosure": "narrative.environment",
        "item405RegulationSKDisclosure": "edgar.section16Compliance",
        "item406RegulationSKCodeOfEthics": "edgar.codeOfEthics",
        "partIItem1FinancialStatements": "statement.bs",
        "partIItem2Mdna": "narrative.mdna",
        "partIItem3MarketRisk": "note.financialRiskMgmt",
        "partIIItem1ARiskFactors": "narrative.riskFactors",
        "partIIItem1LegalProceedings": "note.contingencies",
        "partIIItem2UnregisteredSalesAndUseOfProceeds": "capital.stockTotal",
        "partIItem4ControlsAndProcedures": "governance.auditOpinion",
        "partIIItem4MineSafetyDisclosures": "edgar.mineSafety",
        "partIIItem5OtherInformation": "edgar.otherInformation",
    }
)

_CONCEPTS: tuple[ExtractionConcept, ...] = (
    *STATEMENTS,
    *NOTES,
    *GOVERNANCE,
    *CAPITAL,
    *WORKFORCE,
    *DEBT,
    *SEGMENT,
    *NARRATIVE,
    *FILING,
    *_EDGAR_ITEMS,
)


def _buildIndex(concepts: tuple[ExtractionConcept, ...]) -> Mapping[str, ExtractionConcept]:
    """conceptId 중복을 silent last-write 없이 거부한다."""
    index: dict[str, ExtractionConcept] = {}
    for concept in concepts:
        if concept.conceptId in index:
            raise ValueError(f"중복 extraction conceptId: {concept.conceptId}")
        index[concept.conceptId] = concept
    return MappingProxyType(index)


def _buildNoteAliases(concepts: tuple[ExtractionConcept, ...]) -> Mapping[str, str]:
    """등록된 note alias만 만들고 concept 간 alias 재사용을 거부한다."""
    aliases: dict[str, str] = {}
    owners: dict[str, str] = {}
    for concept in concepts:
        if concept.category != "note" or not concept.registered or not isinstance(concept.dart, DartSource):
            continue
        for alias in (concept.conceptId, concept.conceptId.removeprefix("note."), concept.label):
            if alias in owners:
                raise ValueError(f"note alias 충돌: {alias!r} -> {owners[alias]!r}, {concept.conceptId!r}")
            aliases[alias] = concept.dart.key
            owners[alias] = concept.conceptId
    return MappingProxyType(aliases)


_INDEX = _buildIndex(_CONCEPTS)
_NOTE_ALIAS = _buildNoteAliases(_CONCEPTS)

_invalidItemCategories = sorted(set(_EDGAR_ITEM_CATEGORY.values()) - set(CATEGORIES))
if _invalidItemCategories:
    raise ValueError(f"미등록 EDGAR Item category: {_invalidItemCategories}")

_missingPrimaryConcepts = sorted(set(_EDGAR_ITEM_PRIMARY.values()) - set(_INDEX))
if _missingPrimaryConcepts:
    raise ValueError(f"EDGAR Item 대표 concept 부재: {_missingPrimaryConcepts}")

_byCategory: dict[str, list[ExtractionConcept]] = {category: [] for category in CATEGORIES}
_byParity: dict[str, list[ExtractionConcept]] = {
    "both": [],
    "dartOnly": [],
    "edgarOnly": [],
    "none": [],
}
for _concept in _CONCEPTS:
    _byCategory[_concept.category].append(_concept)
    _byParity[_concept.parity()].append(_concept)
_BY_CATEGORY: Mapping[str, tuple[ExtractionConcept, ...]] = MappingProxyType(
    {category: tuple(concepts) for category, concepts in _byCategory.items()}
)
_BY_PARITY: Mapping[str, tuple[ExtractionConcept, ...]] = MappingProxyType(
    {parity: tuple(concepts) for parity, concepts in _byParity.items()}
)


class EdgarItemCoverageSummary(TypedDict):
    """SEC Item catalog coverage projection."""

    present: int
    catalogued: int
    uncatalogued: list[tuple[str, int]]


class CatalogSummary(TypedDict):
    """추출 catalog의 provider 대칭 요약 projection."""

    total: int
    byCategory: dict[str, int]
    parity: dict[str, int]
    registeredNotes: list[str]
    honestNull: list[str]
    dartHonestNull: list[str]
    edgarHonestNull: list[str]


def resolveNoteKey(key: str) -> str | None:
    """등록된 note 이름을 canonical NT_ key로 해소한다.

    Args:
        key: conceptId, bare name 또는 한글 label.

    Returns:
        canonical NT_ key. 미등록 또는 미일치면 None.

    Requires:
        외부 의존성 없음. import 시점에 검증된 불변 alias index를 사용한다.

    Raises:
        없음.

    Example:
        >>> resolveNoteKey("note.tax")
        'NT_TAX'
    """
    return _NOTE_ALIAS.get(key)


def getExtractionConcepts(*, category: str | None = None) -> list[ExtractionConcept]:
    """정의 순서를 보존한 전체 또는 category별 concept snapshot을 반환한다.

    Args:
        category: CATEGORIES 중 하나. None이면 전체.

    Returns:
        호출자가 자유롭게 다룰 수 있는 새 list. 미등록 category는 빈 list.

    Requires:
        외부 의존성 없음. import 시점에 조립된 catalog를 사용한다.

    Raises:
        없음.

    Example:
        >>> getExtractionConcepts(category="note")[0].category
        'note'
    """
    if category is None:
        return list(_CONCEPTS)
    return list(_BY_CATEGORY.get(category, ()))


def getConcept(conceptId: str) -> ExtractionConcept | None:
    """안정 conceptId로 단일 concept를 조회한다.

    Args:
        conceptId: 예: ``note.tax``.

    Returns:
        불변 ExtractionConcept 또는 미등록이면 None.

    Requires:
        외부 의존성 없음. import 시점에 검증된 concept index를 사용한다.

    Raises:
        없음.

    Example:
        >>> getConcept("note.tax").conceptId
        'note.tax'
    """
    return _INDEX.get(conceptId)


def conceptsByCategory() -> dict[str, list[ExtractionConcept]]:
    """9개 category가 항상 존재하는 독립 list projection을 반환한다.

    Returns:
        ``{category: [ExtractionConcept, ...]}``.

    Requires:
        외부 의존성 없음. import 시점에 조립된 category index를 사용한다.

    Raises:
        없음.

    Example:
        >>> "note" in conceptsByCategory()
        True
    """
    return {category: list(_BY_CATEGORY[category]) for category in CATEGORIES}


def edgarTagsFor(category: str) -> tuple[str, ...]:
    """EDGAR note category의 us-gaap tag tuple을 반환한다.

    Args:
        category: inventory, borrowings 등 note category.

    Returns:
        불변 tag tuple. 미등록이면 빈 tuple.

    Requires:
        외부 의존성 없음. 정적 EDGAR tag manifest를 사용한다.

    Raises:
        없음.

    Example:
        >>> isinstance(edgarTagsFor("inventory"), tuple)
        True
    """
    return EDGAR_NOTE_TAGS.get(category, ())


@overload
def edgarItemCategory(topicId: None = None) -> dict[str, str]:
    """전체 SEC Item category mapping 조회 타입을 선언한다.

    Args:
        topicId: 전체 mapping을 뜻하는 None.

    Returns:
        호출자가 자유롭게 다룰 수 있는 ``{topicId: category}`` dict.

    Requires:
        외부 의존성 없음.

    Raises:
        없음.

    Example:
        >>> isinstance(edgarItemCategory(), dict)
        True
    """
    ...


@overload
def edgarItemCategory(topicId: str) -> str | None:
    """단일 SEC Item category 조회 타입을 선언한다.

    Args:
        topicId: SEC 10-K/10-Q normalized topicId.

    Returns:
        등록 category 또는 미등록이면 None.

    Requires:
        외부 의존성 없음.

    Raises:
        없음.

    Example:
        >>> edgarItemCategory("item1Business")
        'narrative'
    """
    ...


def edgarItemCategory(topicId: str | None = None) -> dict[str, str] | str | None:
    """SEC Item topicId를 catalog category로 해소한다.

    Args:
        topicId: 단일 topicId. None이면 전체 mapping을 요청한다.

    Returns:
        category, 미등록이면 None, 전체 요청이면 독립 dict.

    Requires:
        외부 의존성 없음. 검증된 SEC Item taxonomy mirror를 사용한다.

    Raises:
        없음.

    Example:
        >>> edgarItemCategory("item1Business")
        'narrative'
    """
    if topicId is None:
        return dict(_EDGAR_ITEM_CATEGORY)
    return _EDGAR_ITEM_CATEGORY.get(topicId)


def conceptForEdgarItem(topicId: str) -> ExtractionConcept | None:
    """SEC Item topicId의 대표 concept를 반환한다.

    Args:
        topicId: SEC 10-K/10-Q normalized topicId.

    Returns:
        대표 ExtractionConcept 또는 미등록이면 None.

    Requires:
        외부 의존성 없음. 검증된 SEC Item 대표 concept index를 사용한다.

    Raises:
        없음.

    Example:
        >>> conceptForEdgarItem("item1Business").conceptId
        'narrative.businessOverview'
    """
    conceptId = _EDGAR_ITEM_PRIMARY.get(topicId)
    return _INDEX.get(conceptId) if conceptId else None


def edgarItemToConcept() -> dict[str, str]:
    """SEC Item topicId에서 대표 conceptId로 가는 독립 mapping을 반환한다.

    Returns:
        호출자가 자유롭게 다룰 수 있는 ``{topicId: conceptId}`` dict.

    Requires:
        외부 의존성 없음. 검증된 SEC Item 대표 concept index를 사용한다.

    Raises:
        없음.

    Example:
        >>> edgarItemToConcept()["item1Business"]
        'narrative.businessOverview'
    """
    return dict(_EDGAR_ITEM_PRIMARY)


def edgarItemCoverage(presentItemIds: Mapping[str, int] | Iterable[str]) -> EdgarItemCoverageSummary:
    """실재 SEC Item 집합 대비 catalog coverage를 측정한다.

    Capabilities:
        관측된 SEC Item의 등록 수와 미등록 빈도를 한 번에 계산한다.

    AIContext:
        수집·추출 진단에서 taxonomy 누락을 근거와 함께 제시할 때 사용한다.

    Guide:
        중복 빈도가 있으면 mapping을, 단순 존재 집합이면 iterable을 전달한다.

    When:
        EDGAR 문서에서 관측한 Item과 L0 catalog의 coverage를 비교할 때 호출한다.

    How:
        입력을 빈도 mapping으로 정규화한 뒤 immutable category index와 대조한다.

    Args:
        presentItemIds: topicId iterable 또는 ``{topicId: 빈도}``.

    Returns:
        present, catalogued, uncatalogued 빈도 목록.

    Requires:
        외부 의존성 없음. import 시점에 검증된 SEC Item taxonomy를 사용한다.

    Raises:
        없음.

    Example:
        >>> edgarItemCoverage({"item1Business": 2})["catalogued"]
        1

    SeeAlso:
        edgarItemCategory, conceptForEdgarItem
    """
    if isinstance(presentItemIds, Mapping):
        frequencies = dict(presentItemIds)
    else:
        frequencies: dict[str, int] = {}
        for topicId in presentItemIds:
            frequencies[topicId] = frequencies.get(topicId, 0) + 1
    catalogued = [topicId for topicId in frequencies if topicId in _EDGAR_ITEM_CATEGORY]
    uncatalogued = sorted(
        ((topicId, frequency) for topicId, frequency in frequencies.items() if topicId not in _EDGAR_ITEM_CATEGORY),
        key=lambda item: -item[1],
    )
    return {
        "present": len(frequencies),
        "catalogued": len(catalogued),
        "uncatalogued": uncatalogued,
    }


def parityMatrix() -> dict[str, list[str]]:
    """provider parity 4상태별 conceptId list를 반환한다.

    Returns:
        both, dartOnly, edgarOnly, none별 독립 conceptId list.

    Requires:
        외부 의존성 없음. import 시점에 계산된 parity index를 사용한다.

    Raises:
        없음.

    Example:
        >>> set(parityMatrix()) == {"both", "dartOnly", "edgarOnly", "none"}
        True
    """
    return {
        parity: [concept.conceptId for concept in _BY_PARITY[parity]]
        for parity in ("both", "dartOnly", "edgarOnly", "none")
    }


def catalogSummary() -> CatalogSummary:
    """총계, category, parity, 등록 note, provider별 HonestNull을 요약한다.

    Capabilities:
        추출 catalog의 규모와 provider 대칭성을 단일 projection으로 제공한다.

    AIContext:
        릴리스 검토와 추출 coverage 설명에서 정량 근거를 만들 때 사용한다.

    Guide:
        반환 dict는 독립 snapshot이므로 호출자가 수정해도 catalog는 변하지 않는다.

    When:
        catalog 등록 상태와 구조적 provider 부재를 함께 점검할 때 호출한다.

    How:
        불변 category·parity index와 각 concept의 HonestNull source를 집계한다.

    Returns:
        총계, category/parity 수, 등록 note와 provider별 HonestNull 목록.

    Requires:
        외부 의존성 없음. import 시점에 검증된 전체 catalog를 사용한다.

    Raises:
        없음.

    Example:
        >>> catalogSummary()["total"]
        88

    SeeAlso:
        parityMatrix, getExtractionConcepts
    """
    dartNull = [concept.conceptId for concept in _CONCEPTS if isinstance(concept.dart, HonestNull)]
    edgarNull = [concept.conceptId for concept in _CONCEPTS if isinstance(concept.edgar, HonestNull)]
    honestNull = [
        concept.conceptId
        for concept in _CONCEPTS
        if isinstance(concept.dart, HonestNull) or isinstance(concept.edgar, HonestNull)
    ]
    return {
        "total": len(_CONCEPTS),
        "byCategory": {category: len(_BY_CATEGORY[category]) for category in CATEGORIES},
        "parity": {parity: len(_BY_PARITY[parity]) for parity in _BY_PARITY},
        "registeredNotes": [concept.conceptId for concept in _CONCEPTS if concept.registered],
        "honestNull": honestNull,
        "dartHonestNull": dartNull,
        "edgarHonestNull": edgarNull,
    }


__all__ = [
    "catalogSummary",
    "conceptForEdgarItem",
    "conceptsByCategory",
    "edgarItemCategory",
    "edgarItemCoverage",
    "edgarItemToConcept",
    "edgarTagsFor",
    "getConcept",
    "getExtractionConcepts",
    "parityMatrix",
    "resolveNoteKey",
]
