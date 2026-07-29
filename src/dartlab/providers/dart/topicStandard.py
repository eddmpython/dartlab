"""DART 정기보고서 표준 — topic ↔ chapter ↔ 한글 label 단일 진실값.

본 모듈은 분산되어 있던 DART 표준 매핑 3 종을 SSOT 로 통합한다:

1. ``TOPIC_CANONICAL_CHAPTER`` — topic key → Roman chapter ("I" ~ "XII").
   분기보고서 stub 과 사업보고서 본문의 chapter 가 다를 때 표준 위치 강제.

2. ``TOPIC_DISPLAY_LABEL`` — topic key → DART 보고서 한글 label.
   사용자 노출용 (TOC / 뷰어 헤더).

3. ``CHAPTER_LABEL_KR`` — Roman chapter → DART 표준 한글 chapter 풀네임.

4. ``NOTES_SUB_SECTIONS`` — 재무제표 주석 31 표준 sub-section.
   notes 수평화 (financialNotes/consolidatedNotes 를 sub-leaf 로 분할) 용.

사용 예::

    from dartlab.providers.dart.topicStandard import (
        TOPIC_CANONICAL_CHAPTER,
        TOPIC_DISPLAY_LABEL,
        CHAPTER_LABEL_KR,
        NOTES_SUB_SECTIONS,
        chapterFor,
        labelFor,
    )

    chapterFor("dividend")          # "III"
    labelFor("dividend")            # "배당에 관한 사항"
    CHAPTER_LABEL_KR["III"]         # "III. 재무에 관한 사항"
"""

from __future__ import annotations

import re

# notes sub-topic key 패턴 — `{parent}_NN_slug` (NN = zero-padded 2 자리).
_NOTES_SUB_TOPIC_RE = re.compile(r"^(?:financialNotes|consolidatedNotes)_(?P<num>\d{2})_[A-Za-z]\w*$")

# Company topic 단축어 → provider canonical topic.
# 레지스트리 엔트리 alias와 달리 raw panel topic 및 notes dispatch까지 해소하므로
# DART topic owner가 소유한다.
TOPIC_ALIASES: dict[str, str] = {
    "articles": "articlesOfIncorporation",
    "board": "boardOfDirectors",
    "capital": "shareCapital",
    "cashflow": "CF",
    "cashflows": "CF",
    "cf": "CF",
    "comprehensiveincome": "CIS",
    "contingent": "contingentLiability",
    "control": "internalControl",
    "cost": "costByNature",
    "directors": "boardOfDirectors",
    "equitychanges": "SCE",
    "history": "companyHistory",
    "holder": "majorHolder",
    "holders": "holderOverview",
    "incomestatement": "IS",
    "investment": "investmentInOther",
    "is": "IS",
    "material": "rawMaterial",
    "meeting": "shareholderMeeting",
    "overview": "companyOverview",
    "pay": "executivePay",
    "pl": "IS",
    "product": "productService",
    "profitloss": "IS",
    "relatedParty": "relatedPartyTx",
    "risk": "riskDerivative",
    "sales": "salesOrder",
    "summary": "fsSummary",
    "tangible": "tangibleAsset",
    "bs": "BS",
    "balancesheet": "BS",
    "cis": "CIS",
    "sce": "SCE",
}

# ── chapter 1 ── topic → canonical chapter (Roman)
# DART 사업보고서 최신 표준 위치. 분기보고서가 stub 을 다른 chapter 에 두는 케이스가
# 있어 데이터 분포 (mode/first-seen) 추론 불가 — 명시 매핑이 단일 진실값.
TOPIC_CANONICAL_CHAPTER: dict[str, str] = {
    # I. 회사의 개요
    "companyOverview": "I",
    "companyHistory": "I",
    "capitalChange": "I",
    "shareCapital": "I",
    "articlesOfIncorporation": "I",
    # II. 사업의 내용 — 데이터 일관 (override 불요지만 명시)
    "businessOverview": "II",
    "productService": "II",
    "rawMaterial": "II",
    "salesOrder": "II",
    "riskDerivative": "II",
    "majorContractsAndRnd": "II",
    "otherReferences": "II",
    # III. 재무에 관한 사항
    "ratios": "III",
    "fsSummary": "III",
    "consolidatedStatements": "III",
    "consolidatedNotes": "III",
    "financialStatements": "III",
    "financialNotes": "III",
    "dividend": "III",
    "BS": "III",
    "IS": "III",
    "CIS": "III",
    "CF": "III",
    "SCE": "III",
    # IV. 이사의 경영진단 및 분석의견 등
    "cautionaryStatement": "IV",
    "mdnaOverview": "IV",
    "financialConditionAndResults": "IV",
    "liquidityAndCapitalResources": "IV",
    "otherFinance": "IV",
    # V. 회계감사인의 감사의견 등
    "audit": "V",
    "auditOpinion": "V",
    "auditContract": "V",
    "nonAuditContract": "V",
    "mdna": "V",
    "internalControl": "V",
    # VI. 이사회 등 회사의 기관에 관한 사항
    "boardOfDirectors": "VI",
    "auditSystem": "VI",
    "shareholderMeeting": "VI",
    "outsideDirector": "VI",
    # VII. 주주에 관한 사항
    "majorHolder": "VII",
    "majorHolderChange": "VII",
    "minorityHolder": "VII",
    "stockTotal": "VII",
    "treasuryStock": "VII",
    # VIII. 임원 및 직원 등에 관한 사항
    "employee": "VIII",
    "executive": "VIII",
    "executivePay": "VIII",
    "executivePayAllTotal": "VIII",
    "executivePayIndividual": "VIII",
    "topPay": "VIII",
    "unregisteredExecutivePay": "VIII",
    "executivePayByType": "VIII",
    "executivePayTotal": "VIII",
    # IX. 계열회사 등에 관한 사항
    "affiliateGroup": "IX",
    "investedCompany": "IX",
    # X. 대주주 등과의 거래내용
    "relatedPartyTx": "X",
    "commercialPaper": "X",
    "corporateBond": "X",
    "debtSecurities": "X",
    "privateOfferingUsage": "X",
    "publicOfferingUsage": "X",
    "shortTermBond": "X",
    # XI. 그 밖에 투자자 보호를 위하여 필요한 사항
    "investorProtection": "XI",
    "disclosureChanges": "XI",
    "contingentLiability": "XI",
    "sanction": "XI",
    "subsequentEvents": "XI",
    "expertConfirmation": "XI",
    # XII. 상세표 (별표 — 4 형제 detail 보고서)
    "affiliateGroupDetail": "XII",
    "appendixSchedule": "XII",
    "investmentInOtherDetail": "XII",
    "rndDetail": "XII",
    "subsidiaryDetail": "XII",
}


# ── chapter 2 ── topic → DART 보고서 한글 label (사용자 노출)
TOPIC_DISPLAY_LABEL: dict[str, str] = {
    # I. 회사의 개요
    "companyOverview": "회사의 개요",
    "companyHistory": "회사의 연혁",
    "capitalChange": "자본금 변동사항",
    "shareCapital": "주식의 총수 등",
    "articlesOfIncorporation": "정관에 관한 사항",
    # II. 사업의 내용
    "businessOverview": "사업의 개요",
    "productService": "주요 제품 및 서비스",
    "rawMaterial": "원재료 및 생산설비",
    "salesOrder": "매출 및 수주상황",
    "riskDerivative": "위험관리 및 파생거래",
    "majorContractsAndRnd": "주요계약 및 연구개발활동",
    "otherReferences": "기타 참고사항",
    # III. 재무에 관한 사항
    "ratios": "재무비율",
    "fsSummary": "요약재무정보",
    "consolidatedStatements": "연결재무제표",
    "consolidatedNotes": "연결재무제표 주석",
    "financialStatements": "재무제표",
    "financialNotes": "재무제표 주석",
    "dividend": "배당에 관한 사항",
    "BS": "재무상태표",
    "IS": "손익계산서",
    "CIS": "포괄손익계산서",
    "CF": "현금흐름표",
    "SCE": "자본변동표",
    # IV. 이사의 경영진단 및 분석의견 등
    "cautionaryStatement": "주의사항",
    "mdnaOverview": "이사의 경영진단 및 분석의견 개요",
    "financialConditionAndResults": "재무상태 및 영업실적",
    "liquidityAndCapitalResources": "유동성 및 자금조달",
    "otherFinance": "기타 재무사항",
    # V. 회계감사인의 감사의견 등
    "audit": "회계감사인의 감사의견",
    "auditOpinion": "회계감사인의 감사의견",
    "mdna": "경영진단 및 분석의견",
    "internalControl": "내부통제에 관한 사항",
    "auditContract": "감사용역 계약",
    "nonAuditContract": "비감사용역 계약",
    # VI. 이사회 등 회사의 기관에 관한 사항
    "boardOfDirectors": "이사회에 관한 사항",
    "auditSystem": "감사제도에 관한 사항",
    "shareholderMeeting": "주주의 의결권 행사에 관한 사항",
    "outsideDirector": "사외이사 및 변동현황",
    # VII. 주주에 관한 사항
    "majorHolder": "최대주주에 관한 사항",
    "majorHolderChange": "최대주주 변동현황",
    "minorityHolder": "소액주주 현황",
    "stockTotal": "주식의 분포",
    "treasuryStock": "자기주식 취득 및 처분",
    # VIII. 임원 및 직원 등에 관한 사항
    "executive": "임원 현황",
    "employee": "직원 등의 현황",
    "executivePay": "임원의 보수",
    "executivePayAllTotal": "임원 보수 총액",
    "executivePayIndividual": "개별 임원 보수",
    "topPay": "보수 상위 5 인",
    "unregisteredExecutivePay": "미등기임원 보수",
    "executivePayByType": "유형별 임원 보수",
    "executivePayTotal": "임원 보수 총계",
    # IX. 계열회사 등에 관한 사항
    "affiliateGroup": "계열회사 현황",
    "investedCompany": "타법인출자 현황",
    # X. 대주주 등과의 거래내용
    "relatedPartyTx": "대주주 등과의 거래내용",
    "commercialPaper": "기업어음증권 미상환잔액",
    "corporateBond": "회사채 미상환잔액",
    "debtSecurities": "채무증권 발행실적",
    "privateOfferingUsage": "사모자금 사용내역",
    "publicOfferingUsage": "공모자금 사용내역",
    "shortTermBond": "단기사채 미상환잔액",
    # XI. 그 밖에 투자자 보호를 위하여 필요한 사항
    "investorProtection": "투자자 보호",
    "disclosureChanges": "공시내용 변경",
    "contingentLiability": "우발부채",
    "sanction": "제재현황",
    "subsequentEvents": "후발사건",
    "expertConfirmation": "전문가 확인",
    # XII. 상세표
    "affiliateGroupDetail": "계열회사 상세",
    "appendixSchedule": "상세표",
    "investmentInOtherDetail": "타법인출자 상세",
    "rndDetail": "연구개발 상세",
    "subsidiaryDetail": "종속회사 상세",
}


def resolveTopicAlias(topic: str) -> str:
    """Company topic 단축어를 DART canonical topic으로 해소한다.

    Args:
        topic: 사용자가 전달한 canonical topic 또는 단축어.

    Returns:
        등록된 단축어면 canonical topic, 아니면 입력 그대로.

    Raises:
        없음.

    Example:
        >>> resolveTopicAlias("board")
        'boardOfDirectors'
    """
    return TOPIC_ALIASES.get(topic, topic)


# ── chapter 3 ── Roman chapter → DART 표준 한글 풀네임
CHAPTER_LABEL_KR: dict[str, str] = {
    "I": "I. 회사의 개요",
    "II": "II. 사업의 내용",
    "III": "III. 재무에 관한 사항",
    "IV": "IV. 이사의 경영진단 및 분석의견 등",
    "V": "V. 회계감사인의 감사의견 등",
    "VI": "VI. 이사회 등 회사의 기관에 관한 사항",
    "VII": "VII. 주주에 관한 사항",
    "VIII": "VIII. 임원 및 직원 등에 관한 사항",
    "IX": "IX. 계열회사 등에 관한 사항",
    "X": "X. 대주주 등과의 거래내용",
    "XI": "XI. 그 밖에 투자자 보호를 위하여 필요한 사항",
    "XII": "XII. 상세표",
}


# ── 주석 4 ── DART 재무제표 주석 31 표준 sub-section
# 사업보고서의 "5. 재무제표 주석" 안 N. 헤딩 표준 구조. backend pipeline 이 본문 첫 줄
# 의 ``N. xyz`` 패턴으로 sub-topic 분할할 때 ID/label 의 단일 진실값.
NOTES_SUB_SECTIONS: list[tuple[int, str, str]] = [
    # (번호, slug — sub-topic key suffix, 한글 label)
    (1, "general", "일반적 사항"),
    (2, "accountingPolicy", "중요한 회계처리방침"),
    (3, "estimates", "중요한 회계추정 및 가정"),
    (4, "financialInstruments", "범주별 금융상품"),
    (5, "financialAssetsTransfer", "금융자산의 양도"),
    (6, "fairValueAssets", "공정가치금융자산"),
    (7, "tradeReceivables", "매출채권 및 미수금"),
    (8, "inventories", "재고자산"),
    (9, "subsidiariesAndAssociates", "종속기업, 관계기업 및 공동기업 투자"),
    (10, "ppe", "유형자산"),
    (11, "intangibleAssets", "무형자산"),
    (12, "borrowings", "차입금"),
    (13, "bonds", "사채"),
    (14, "definedBenefit", "순확정급여부채(자산)"),
    (15, "provisions", "충당부채"),
    (16, "contingentAndCommitments", "우발부채와 약정사항"),
    (17, "contractLiabilities", "계약부채"),
    (18, "capitalStock", "자본금"),
    (19, "retainedEarnings", "이익잉여금"),
    (20, "otherCapital", "기타자본항목"),
    (21, "expensesByNature", "비용의 성격별 분류"),
    (22, "sga", "판매비와관리비"),
    (23, "otherIncomeExpense", "기타수익 및 기타비용"),
    (24, "financeIncomeExpense", "금융수익 및 금융비용"),
    (25, "incomeTax", "법인세비용"),
    (26, "eps", "주당이익"),
    (27, "cashflow", "현금흐름표"),
    (28, "riskManagement", "재무위험관리"),
    (29, "fairValue", "공정가치 측정"),
    (30, "segment", "부문별 보고"),
    (31, "relatedParty", "특수관계자와의 거래"),
    (32, "subsequentEvents", "보고기간후사건"),
]


# ── 주석 5 ── DART 사업보고서 chapter 별 표준 topic 순서 SSOT
# 각 chapter 의 topic 표준 순서. backend buildToc 가 본 layout 순서로 topic 정렬.
# layout 에 없는 topic 은 tail 에 alphabetical 로 append.
# chapter III 만 sub-topic grouping 추가 처리 (consolidatedNotes_NN_xxx → folder).
#
# 출처: DART 정기보고서 표준 양식 (대분류 11 + 별표 1).
CHAPTER_LAYOUT: dict[str, tuple[str, ...]] = {
    # I. 회사의 개요
    "I": (
        "companyOverview",
        "companyHistory",
        "capitalChange",
        "shareCapital",
        "articlesOfIncorporation",
    ),
    # II. 사업의 내용
    "II": (
        "businessOverview",
        "productService",
        "rawMaterial",
        "salesOrder",
        "riskDerivative",
        "majorContractsAndRnd",
        "otherReferences",
    ),
    # III. 재무에 관한 사항 (sub-topic grouping 별도 처리)
    "III": (
        "ratios",
        "fsSummary",
        "consolidatedStatements",
        "consolidatedNotes",
        "financialStatements",
        "financialNotes",
        "dividend",
    ),
    # IV. 이사의 경영진단 및 분석의견 등
    "IV": (
        "cautionaryStatement",
        "mdnaOverview",
        "financialConditionAndResults",
        "liquidityAndCapitalResources",
        "otherFinance",
    ),
    # V. 회계감사인의 감사의견 등
    "V": (
        "audit",
        "internalControl",
        "auditContract",
        "nonAuditContract",
        "mdna",
    ),
    # VI. 이사회 등 회사의 기관에 관한 사항
    "VI": (
        "boardOfDirectors",
        "auditSystem",
        "shareholderMeeting",
        "outsideDirector",
    ),
    # VII. 주주에 관한 사항
    "VII": (
        "majorHolder",
        "majorHolderChange",
        "minorityHolder",
        "stockTotal",
        "treasuryStock",
    ),
    # VIII. 임원 및 직원 등에 관한 사항
    "VIII": (
        "executive",
        "employee",
        "executivePay",
        "executivePayAllTotal",
        "executivePayIndividual",
        "executivePayByType",
        "executivePayTotal",
        "topPay",
        "unregisteredExecutivePay",
    ),
    # IX. 계열회사 등에 관한 사항
    "IX": (
        "affiliateGroup",
        "investedCompany",
    ),
    # X. 대주주 등과의 거래내용
    "X": (
        "relatedPartyTx",
        "corporateBond",
        "commercialPaper",
        "shortTermBond",
        "debtSecurities",
        "privateOfferingUsage",
        "publicOfferingUsage",
    ),
    # XI. 그 밖에 투자자 보호를 위하여 필요한 사항
    "XI": (
        "sanction",
        "contingentLiability",
        "disclosureChanges",
        "subsequentEvents",
        "expertConfirmation",
        "investorProtection",
    ),
    # XII. 상세표
    "XII": (
        "subsidiaryDetail",
        "affiliateGroupDetail",
        "investmentInOtherDetail",
        "rndDetail",
        "appendixSchedule",
    ),
}

# alias — 옛 코드 호환 (chapter III layout 만 별도 reference).
CHAPTER_III_LAYOUT: tuple[str, ...] = CHAPTER_LAYOUT["III"]

# financialStatements folder 의 자식 (DART 표준 5 표 순서).
FINANCIAL_STATEMENT_CHILDREN: tuple[str, ...] = ("BS", "IS", "CIS", "CF", "SCE")

# chapter III sub-topic → parent folder topic 매핑. None 이면 직속 leaf.
_NOTES_PARENT_RE = re.compile(r"^(?P<parent>financialNotes|consolidatedNotes)_\d{2}_")


def chapterIIIParent(topic: str) -> str | None:
    """chapter III sub-topic → parent folder topic. 직속이면 None.

    매핑:
        - ``BS/IS/CIS/CF/SCE`` → ``financialStatements``
        - ``financialNotes_NN_xxx`` → ``financialNotes``
        - ``consolidatedNotes_NN_xxx`` → ``consolidatedNotes``
        - 그 외 → None (직속)

    Args:
        topic: dartlab topic 키.

    Returns:
        parent topic key 또는 None.

    Raises:
        없음.

    Example:
        >>> chapterIIIParent("financialNotes_05_financialAssetsTransfer")
        'financialNotes'
        >>> chapterIIIParent("BS")
        'financialStatements'
        >>> chapterIIIParent("dividend") is None
        True
    """
    if topic in FINANCIAL_STATEMENT_CHILDREN:
        return "financialStatements"
    match = _NOTES_PARENT_RE.match(topic)
    if match:
        return match.group("parent")
    return None


def chapterIIIOrder(topic: str) -> int:
    """chapter III layout 안 topic 의 정렬 키. layout 에 없으면 999.

    Args:
        topic: dartlab topic 키.

    Returns:
        0-based index 또는 layout 부재 시 999.

    Raises:
        없음.

    Example:
        >>> chapterIIIOrder("consolidatedNotes")
        3
        >>> chapterIIIOrder("dividend")
        6
        >>> chapterIIIOrder("unknownTopic")
        999
    """
    try:
        return CHAPTER_III_LAYOUT.index(topic)
    except ValueError:
        return 999


def chapterTopicOrder(topic: str, chapter: str) -> int:
    """chapter 안 topic 의 DART 표준 정렬 키. layout 에 없으면 999.

    Args:
        topic: dartlab topic 키.
        chapter: Roman chapter ("I" ~ "XII").

    Returns:
        0-based index 또는 layout 부재 시 999.

    Raises:
        없음.

    Example:
        >>> chapterTopicOrder("companyOverview", "I")
        0
        >>> chapterTopicOrder("articlesOfIncorporation", "I")
        4
        >>> chapterTopicOrder("unknownTopic", "I")
        999
    """
    layout = CHAPTER_LAYOUT.get(chapter)
    if not layout:
        return 999
    try:
        return layout.index(topic)
    except ValueError:
        return 999


def chapterFor(topic: str) -> str | None:
    """topic key → canonical chapter ("I" ~ "XII") 또는 None.

    Args:
        topic: dartlab topic 키 (예 ``"dividend"``).

    Returns:
        Roman chapter 또는 매핑 부재 시 None.

    Raises:
        없음.

    Example:
        >>> chapterFor("dividend")
        'III'
    """
    return TOPIC_CANONICAL_CHAPTER.get(topic)


def labelFor(topic: str, fallback: str | None = None) -> str:
    """topic key → DART 표준 한글 label. 매핑 부재 시 fallback 또는 topic 그대로.

    notes sub-topic (``financialNotes_NN_slug`` 형식) 은 자동으로
    ``N. {한글}`` 반환 (NOTES_SUB_SECTIONS lookup).

    Args:
        topic: dartlab topic 키.
        fallback: 매핑 부재 시 반환할 값. None 이면 topic key 그대로.

    Returns:
        한글 label.

    Raises:
        없음.

    Example:
        >>> labelFor("dividend")
        '배당에 관한 사항'
        >>> labelFor("financialNotes_05_financialAssetsTransfer")
        '5. 금융자산의 양도'
    """
    label = TOPIC_DISPLAY_LABEL.get(topic)
    if label:
        return label
    # notes sub-topic 패턴 — `{parent}_NN_slug`.
    sub_match = _NOTES_SUB_TOPIC_RE.match(topic)
    if sub_match:
        number = int(sub_match.group("num"))
        for n, _slug, korean in NOTES_SUB_SECTIONS:
            if n == number:
                return notesSubTopicLabel(number, korean)
    return fallback if fallback is not None else topic


def chapterLabelKr(chapter: str) -> str:
    """chapter Roman (또는 풀네임) → DART 표준 한글 풀네임.

    이미 풀네임 (``"III. 재무에 관한 사항"``) 박혀있으면 그대로 반환 (idempotent).

    Args:
        chapter: Roman ("III") 또는 풀네임.

    Returns:
        한글 풀네임. 매핑 부재 시 입력 그대로.

    Raises:
        없음.

    Example:
        >>> chapterLabelKr("III")
        'III. 재무에 관한 사항'
    """
    if not isinstance(chapter, str):
        return str(chapter)
    raw = chapter.strip()
    if not raw:
        return raw
    if "." in raw and len(raw.split(".", 1)[-1].strip()) > 0:
        return raw  # 이미 풀네임
    prefix = raw.split(".")[0].strip()
    return CHAPTER_LABEL_KR.get(prefix, raw)


# 주석 sub-topic key 생성 — financialNotes_05_financialAssetsTransfer 식.
def notesSubTopicKey(parentTopic: str, number: int, slug: str) -> str:
    """주석 sub-topic key — `{parent}_{NN}_{slug}` 형식 (zero-padded 2 자리).

    Args:
        parentTopic: ``"financialNotes"`` 또는 ``"consolidatedNotes"``.
        number: 주석 번호 (1~32).
        slug: 영문 slug (``"general"`` 등).

    Returns:
        sub-topic key.

    Raises:
        없음.

    Example:
        >>> notesSubTopicKey("financialNotes", 5, "financialAssetsTransfer")
        'financialNotes_05_financialAssetsTransfer'
    """
    return f"{parentTopic}_{number:02d}_{slug}"


def notesSubTopicLabel(number: int, koreanName: str) -> str:
    """주석 sub-topic 한글 label — `{N}. {koreanName}` 형식.

    Args:
        number: 주석 번호.
        koreanName: 한글 sub-section 이름.

    Returns:
        한글 label.

    Raises:
        없음.

    Example:
        >>> notesSubTopicLabel(5, "금융자산의 양도")
        '5. 금융자산의 양도'
    """
    return f"{number}. {koreanName}"
