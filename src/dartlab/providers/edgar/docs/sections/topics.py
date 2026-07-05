"""EDGAR docs topic 택소노미 SSOT (chapter/label 매핑).

sections 파이프라인이 emit 하는 topic(``form_type::itemId``, 예 ``10-K::item1Business``)을
(chapter, label) 로 해소하는 단일 진실의 원천. 옛 ``providers.edgar.company`` 안에 흩어져 있던 라벨
dict(_FINANCE_LABELS·_10K_ITEM_LABELS·_10Q_ITEM_LABELS)과 해소기(_topicChapterLabel·_itemIdToLabel)를
여기로 올려, company facade·docs 열거기(`enumerate`)·인벤토리가 한 곳을 재사용한다(중복 제거).

**계층**: providers/edgar/docs/sections (L1). 외부 dartlab import 0(순수 데이터 + 문자열 가공)이라 같은
provider 상위(company facade)도, frame(L1.5) 열거기도 순환 없이 소비한다. core(L0) 카탈로그는 계층상
providers 를 import 못 하므로 별도 mirror(`_EDGAR_ITEM_LABELS`)를 두고 drift 가드로 본 SSOT 와 일치 강제.
"""

from __future__ import annotations

import re

# 재무 5표 topic → (chapter, label)
_FINANCE_LABELS: dict[str, tuple[str, str]] = {
    "BS": ("Financial Statements", "Balance Sheet"),
    "IS": ("Financial Statements", "Income Statement"),
    "CF": ("Financial Statements", "Cash Flow"),
    "CIS": ("Financial Statements", "Comprehensive Income"),
    "ratios": ("Financial Statements", "Financial Ratios"),
}

# 10-K Item → (chapter, label)
_10K_ITEM_LABELS: dict[str, tuple[str, str]] = {
    "item1Business": ("Part I", "Business"),
    "item1ARiskFactors": ("Part I", "Risk Factors"),
    "item1BUnresolvedStaffComments": ("Part I", "Unresolved Staff Comments"),
    "item1CCybersecurity": ("Part I", "Cybersecurity"),
    "item1DExecutiveOfficers": ("Part I", "Executive Officers"),
    "item2Properties": ("Part I", "Properties"),
    "item3LegalProceedings": ("Part I", "Legal Proceedings"),
    "item4MineSafetyDisclosures": ("Part I", "Mine Safety Disclosures"),
    "item4AExecutiveOfficersOfTheRegistrant": ("Part I", "Executive Officers"),
    "item5MarketForCommonEquity": ("Part II", "Market for Common Equity"),
    "item6Reserved": ("Part II", "Reserved"),
    "item7Mdna": ("Part II", "MD&A"),
    "item7AMarketRiskDisclosures": ("Part II", "Market Risk Disclosures"),
    "item8FinancialStatements": ("Part II", "Financial Statements"),
    "item9ChangesInAccountants": ("Part III", "Changes in Accountants"),
    "item9AControlsAndProcedures": ("Part III", "Controls and Procedures"),
    "item9BOtherInformation": ("Part III", "Other Information"),
    "item9CForeignJurisdictionDisclosures": ("Part III", "Foreign Jurisdiction Disclosures"),
    "item10DirectorsAndCorporateGovernance": ("Part III", "Directors & Corporate Governance"),
    "item11ExecutiveCompensation": ("Part III", "Executive Compensation"),
    "item12SecurityOwnership": ("Part III", "Security Ownership"),
    "item13RelatedTransactions": ("Part III", "Related Transactions"),
    "item14PrincipalAccountantFees": ("Part III", "Principal Accountant Fees"),
    "item15ExhibitsAndSchedules": ("Part IV", "Exhibits & Schedules"),
    "item16Form10KSummary": ("Part IV", "Form 10-K Summary"),
    "item103EnvironmentalDisclosure": ("Regulation S-K", "Environmental Disclosure"),
    "item405RegulationSKDisclosure": ("Regulation S-K", "Regulation S-K Disclosure"),
    "item406RegulationSKCodeOfEthics": ("Regulation S-K", "Code of Ethics"),
}

# 10-Q Part/Item → (chapter, label)
_10Q_ITEM_LABELS: dict[str, tuple[str, str]] = {
    "partIItem1FinancialStatements": ("Part I", "Financial Statements"),
    "partIItem2Mdna": ("Part I", "MD&A"),
    "partIItem3MarketRisk": ("Part I", "Market Risk Disclosures"),
    "partIItem4ControlsAndProcedures": ("Part I", "Controls and Procedures"),
    "partIIItem1LegalProceedings": ("Part II", "Legal Proceedings"),
    "partIIItem1ARiskFactors": ("Part II", "Risk Factors"),
    "partIIItem2UnregisteredSalesAndUseOfProceeds": ("Part II", "Unregistered Sales"),
    "partIIItem3DefaultsUponSeniorSecurities": ("Part II", "Defaults Upon Senior Securities"),
    "partIIItem4MineSafetyDisclosures": ("Part II", "Mine Safety Disclosures"),
    "partIIItem5OtherInformation": ("Part II", "Other Information"),
    "partIIItem6Exhibits": ("Part II", "Exhibits"),
}


def _itemIdToLabel(itemId: str) -> str:
    """camelCase itemId 를 읽기 쉬운 label 로 변환한다.

    Args:
        itemId: ``"item5AOperatingResults"`` 같은 camelCase topic id.

    Returns:
        공백 분리된 label(예 "Operating Results"). 파싱 불가 시 itemId 원문.

    Raises:
        없음.

    Example:
        >>> _itemIdToLabel("item5AOperatingResults")
        'Operating Results'
    """
    m = re.match(r"^(?:partI{1,2})?[Ii]tem(\d+)([A-Z]?)(.*)$", itemId)
    if not m:
        return itemId
    subLetter = m.group(2)
    rest = m.group(3)
    if subLetter and rest and rest[0].isupper():
        pass
    elif subLetter:
        rest = subLetter + rest
    if not rest:
        return itemId
    label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", rest)
    label = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", label)
    return label


def _topicChapterLabel(topic: str) -> tuple[str, str]:
    """topic(``form::itemId`` 또는 재무키)에서 (chapter, label)을 해소한다.

    Args:
        topic: ``"10-K::item1Business"`` / ``"BS"`` 등.

    Returns:
        (chapter, label) 튜플. 미매핑 20-F/기타는 (formType, itemIdToLabel).

    Raises:
        없음.

    Example:
        >>> _topicChapterLabel("10-K::item1Business")
        ('Part I', 'Business')
    """
    if topic in _FINANCE_LABELS:
        return _FINANCE_LABELS[topic]
    if "::" in topic:
        formType, itemId = topic.split("::", 1)
        if formType == "10-K" and itemId in _10K_ITEM_LABELS:
            return _10K_ITEM_LABELS[itemId]
        if formType == "10-Q" and itemId in _10Q_ITEM_LABELS:
            return _10Q_ITEM_LABELS[itemId]
        return (formType, _itemIdToLabel(itemId))
    return ("", topic)


def topicChapterLabel(topic: str) -> tuple[str, str]:
    """topic 에서 (chapter, label)을 해소한다 (public alias of `_topicChapterLabel`).

    Args:
        topic: ``"10-K::item1Business"`` / ``"BS"`` 등 sections topic.

    Returns:
        (chapter, label) 튜플.

    Raises:
        없음.

    Example:
        >>> topicChapterLabel("10-K::item7Mdna")
        ('Part II', 'MD&A')

    Capabilities:
        - sections topic 을 사람이 읽는 (chapter, label)로 해소하는 단일 진입점.

    Guide:
        - 인벤토리/열거기가 topic unit 의 title·chapter 를 붙일 때 호출.

    AIContext:
        US 보고서 단위 라벨링. DART chapter(로마자)와 구조 통일(Part I/II/III/IV).

    Requires:
        - 외부 의존 0 (순수 문자열 매핑).
    """
    return _topicChapterLabel(topic)
