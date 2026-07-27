from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_MULTISPACE_RE = re.compile(r"\s+")
_PIPE_RE = re.compile(r"\|")
_DASH_CHARS_RE = re.compile(r"[\x96\x97\u2013\u2014]")
_ITEM_RE = re.compile(r"^Item\s+(\d+[A-Z]?)\.\s*(.*)$", re.IGNORECASE)
_PART_ITEM_RE = re.compile(
    r"^Part\s+(I{1,2})\s*-\s*Item\s+(\d+[A-Z]?)\.\s*(.*)$",
    re.IGNORECASE,
)
# Part I - {label} (Item 없이 label만)
_PART_NOLABEL_RE = re.compile(
    r"^Part\s+(I{1,2})\s*-\s*(.+)$",
    re.IGNORECASE,
)
_REG_S_K_RE = re.compile(
    r"^Item\s+(?:405|103)\.\s+of\s+(?:SEC\s+)?Regulation\s+S-K.*$",
    re.IGNORECASE,
)
_ITEM_601_RE = re.compile(r"^Item 601\..*Regulation S-K.*$", re.IGNORECASE)
_ITEM_406_RE = re.compile(r"^Item 406\. of Regulation S-K.*$", re.IGNORECASE)
# 3자리+ Regulation S-K/AB 항목 → 일괄 흡수
_REG_3DIGIT_RE = re.compile(
    r"^Item\s+(\d{3,})\.\s+(?:of\s+)?(?:SEC\s+)?(?:Regulation\s+(?:S-K|AB)|SK-\d+|"
    r"under\s+Regulation).*$",
    re.IGNORECASE,
)
# "IT EM 1A" / "I tem 1A" 오타 보정 (정상 "Item"은 제외)
_BROKEN_ITEM_RE = re.compile(
    r"^(?:IT\s+EM|I\s+tem)\s+(\d+[A-Z]?)\.\s*(.*)$",
    re.IGNORECASE,
)
# "Item 4B. Item 4B" / "Item 12D. ITEM 12D" 중복 label 제거
_DUPE_LABEL_RE = re.compile(
    r"^(Item\s+\d+[A-Z]?)\.\s*(?:ITEM\s+\d+[A-Z]?\s*\.?\s*)?(.*)$",
    re.IGNORECASE,
)
# "of Regulation S-K ..." — Item prefix 없이 시작하는 Reg S-K 본문
_LOOSE_REG_RE = re.compile(
    r"^of\s+(?:SEC\s+)?Regulation\s+(?:S-K|AB)",
    re.IGNORECASE,
)
# "and the registrant, at the time of filing..."
_LOOSE_405_RE = re.compile(
    r"^and\s+the\s+registrant",
    re.IGNORECASE,
)
# "under Regulation S-K..."
_UNDER_REG_RE = re.compile(
    r"^under\s+Regulation\s+(?:S-K|AB)",
    re.IGNORECASE,
)
# "of SK-1300..."
_OF_SK_RE = re.compile(r"^of\s+SK-\d+", re.IGNORECASE)


def _mappingPath() -> Path:
    return Path(__file__).resolve().parent / "mapperData" / "sectionMappings.json"


def _cleanPipes(text: str) -> str:
    if "|" not in text:
        return text
    cleaned = _PIPE_RE.sub(" ", text)
    return _MULTISPACE_RE.sub(" ", cleaned).strip()


# 10-Q "Part I" 비Item label → canonical 매핑
_PART_LABEL_CANON: dict[tuple[str, str], str] = {
    # Risk Factors 변형
    ("I", "RISK FACTORS"): "Part II - Item 1A. Risk Factors",
    ("I", "RISK FACTORS."): "Part II - Item 1A. Risk Factors",
    # Other Information
    ("I", "OTHER INFORMATION"): "Part II - Item 5. Other Information",
    ("I", "OTHER INFORMATIO N"): "Part II - Item 5. Other Information",
    ("I", "OTHER MATTERS"): "Part II - Item 5. Other Information",
    # Exhibits
    ("I", "EXHIBITS AND REPORTS ON FORM 8-K."): "Part II - Item 6. Exhibits",
    ("I", "EXHIBITS AND REPORTS ON FORM 8-K"): "Part II - Item 6. Exhibits",
    ("I", "EXHIBIT S"): "Part II - Item 6. Exhibits",
    ("I", "EXHIBITS"): "Part II - Item 6. Exhibits",
    # Financial Statements
    ("I", "CONDENSED CONSOLIDATED FINANCIAL STATEMENTS. 3"): "Part I - Item 1. Financial Statements",
    ("I", "CONDENSED CONSOLIDATED FINANCIAL STATEMENTS"): "Part I - Item 1. Financial Statements",
    # MD&A
    (
        "I",
        "MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS",
    ): "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations",
    (
        "I",
        "MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERAT",
    ): "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations",
    # Unregistered Sales
    (
        "I",
        "UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS.",
    ): "Part II - Item 2. Unregistered Sales of Equity Securities and Use of Proceeds",
    (
        "I",
        "UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS",
    ): "Part II - Item 2. Unregistered Sales of Equity Securities and Use of Proceeds",
    # Page (table of contents)
    ("I", "PAGE"): "Part I - Item 1. Financial Statements",
    # Other
    ("I", "- OTHER INFORMATION"): "Part II - Item 5. Other Information",
}


def _normalizePartItem(text: str) -> str:
    partMatch = _PART_ITEM_RE.match(text)
    if partMatch:
        partNum = partMatch.group(1).upper()
        itemNum = partMatch.group(2).upper()
        itemLabel = _MULTISPACE_RE.sub(" ", partMatch.group(3).strip())
        itemLabel = _cleanPipes(itemLabel)
        itemLabelInner = re.sub(
            r"^Item\s+\d+[A-Z]?\.\s*",
            "",
            itemLabel,
            flags=re.IGNORECASE,
        ).strip()
        if itemLabelInner:
            itemLabel = itemLabelInner
        itemLabel = itemLabel.rstrip(".")

        if itemNum in {"5", "5A", "6", "7", "8"} and partNum == "I":
            partNum = "II"
        if itemNum == "1A" and partNum == "I":
            upperItemLabel = itemLabel.upper().replace("  ", " ")
            if upperItemLabel == "RISK FACTORS":
                partNum = "II"
            elif "UNAUDITED SUPPLEMENTAL" in upperItemLabel or "NAUDITED SUPPLEMENTAL" in upperItemLabel:
                return "Item 8A. Supplemental Financial Information"
        if itemNum == "1B" and partNum == "II":
            partNum = "I"

        canonLabels = {
            ("I", "1"): "Financial Statements",
            ("I", "2"): "Management's Discussion and Analysis of Financial Condition and Results of Operations",
            ("I", "3"): "Quantitative and Qualitative Disclosures About Market Risk",
            ("I", "4"): "Controls and Procedures",
            ("II", "1"): "Legal Proceedings",
            ("II", "1A"): "Risk Factors",
            ("II", "2"): "Unregistered Sales of Equity Securities and Use of Proceeds",
            ("II", "3"): "Defaults Upon Senior Securities",
            ("II", "4"): "Mine Safety Disclosures",
            ("II", "5"): "Other Information",
            ("II", "5A"): "Other Information",
            ("II", "6"): "Exhibits",
            ("II", "7"): "Signatures",
            ("II", "8"): "Management's Discussion and Analysis of Financial Condition and Results of Operations",
        }
        canon = canonLabels.get((partNum, itemNum))
        if canon:
            itemLabel = canon

        return f"Part {partNum} - Item {itemNum}. {itemLabel}"

    # "Part I - Risk Factors" (Item 없이)
    noItemMatch = _PART_NOLABEL_RE.match(text)
    if noItemMatch:
        partNum = noItemMatch.group(1).upper()
        label = noItemMatch.group(2).strip().rstrip(".")
        canonKey = (partNum, label.upper())
        canon = _PART_LABEL_CANON.get(canonKey)
        if canon:
            return canon
        # 추가 fuzzy: 앞부분 30자까지 매치
        truncLabel = label.upper()[:30]
        for (pn, cl), cv in _PART_LABEL_CANON.items():
            if pn == partNum and cl.startswith(truncLabel):
                return cv

    return text


def _nonItemTitle(text: str) -> str:
    """Item 접두어가 없는 제목을 정본 Item 으로 옮긴다. 못 옮기면 원문 그대로.

    회사마다 같은 절을 자기 말로 적는다. "EXECUTIVE OFFICERS OF THE REGISTRANT" 와
    "Executive" 가 같은 Item 4A 다. 순서가 뜻을 만든다. 넓게 잡는 규칙이 앞에 오면 좁은
    규칙이 영영 안 걸리므로 원래 순서를 그대로 지킨다.
    """
    upper = text.upper().strip()
    if "EXECUTIVE OFFICERS" in upper or upper == "EXECUTIVE":
        return "Item 4A. Executive Officers of the Registrant"
    if upper == "CONTROLS AND PROCEDURES":
        return "Item 9A. Controls and Procedures"
    if "CONSOLIDATED FINANCIAL STATEMENTS AND SUPPLEMENTARY" in upper:
        return "Item 8. Financial Statements"
    if "CONSOLIDATED FINANCIAL STATEMENTS AND OTHER" in upper:
        return "Item 8. Financial Statements"
    if upper.startswith("UNAUDITED SUPPLEMENTAL PRESENTATION"):
        return "Item 8A. Supplemental Financial Information"
    if upper.startswith("SUPPLEMENTAL FINANCIAL INFORMATION"):
        return "Item 8A. Supplemental Financial Information"
    if upper == "ANNUAL REPORT TO SECURITY HOLDERS":
        return "Item 10J. Annual Report to Security Holders"
    if "DISCLOSURE OF A REGISTRANT" in upper and "RECOVER" in upper:
        return "Recovery Of Erroneously Awarded Compensation"
    return text


_ITEM_405_LOOSE_RE = re.compile(r"^Item\s+405\.\s+and\s+the\s+registrant", re.IGNORECASE)
_PART_REG_RE = re.compile(r"^Part\s+\S+\s*-\s*Item\s+\d{3,}\.\s*(?:of\s+)?(?:SEC\s+)?Regulation", re.IGNORECASE)


def _regulationSkTitle(text: str) -> str | None:
    """Regulation S-K 참조를 정본 Item 제목으로 수렴시킨다. 해당 없으면 None.

    SEC 제출서류는 같은 조항을 열 가지 넘는 표기로 적는다. Item 접두어가 없는 것, 조문
    번호만 있는 것, Part-Item 안에 세 자리 조항이 박힌 것까지. 전부 한 제목으로 모아야
    문서 목차가 회사마다 갈라지지 않는다.
    """
    # Item 접두어 없이 시작하는 Reg S-K 표기.
    if _LOOSE_REG_RE.match(text) or _UNDER_REG_RE.match(text) or _OF_SK_RE.match(text):
        return "Item 405. of Regulation S-K"
    # "and the registrant, at the time of filing..." 로 시작하는 405 변형.
    if _LOOSE_405_RE.match(text):
        return "Item 405. of Regulation S-K"
    if _REG_S_K_RE.match(text):
        return "Item 405. of Regulation S-K"
    if _ITEM_406_RE.match(text):
        return "Item 406. of Regulation S-K"
    if _ITEM_601_RE.match(text):
        return "Item 15. Exhibits & Schedules"
    regMatch = _REG_3DIGIT_RE.match(text)
    if regMatch:
        return f"Item {regMatch.group(1)}. of Regulation S-K"
    if _ITEM_405_LOOSE_RE.match(text) or _PART_REG_RE.match(text):
        return "Item 405. of Regulation S-K"
    return None


def _isExecutiveOfficerLabel(itemNum: str, itemLabel: str, upperLabel: str) -> bool:
    """임원 정보 절인지 본다. 10-K 는 4A, 새 서식은 1D 로 같은 절을 적는다.

    번호마다 인정 문구가 다르다. 4A 는 목차에 "Part I 참조" 만 적힌 경우까지 받고,
    1D 는 EXECUTIVE 가 들어가면 받는다. 그 차이가 서식 차이라 한 조건으로 합치지 않는다.
    """
    if itemNum == "1D":
        return "EXECUTIVE" in upperLabel or not itemLabel
    return (
        not itemLabel
        or upperLabel == "ITEM 4A"
        or "EXECUTIVE OFFICERS" in upperLabel
        or upperLabel == "EXECUTIVE"
        or "INFORMATION ABOUT OUR EXECUTIVE" in upperLabel
        or "IN PART I OF THIS ANNUAL" in upperLabel
    )


def _isSupplementalLabel(itemNum: str, itemLabel: str, upperLabel: str) -> bool:
    """보충 재무정보 절인지 본다. 회사마다 여섯 가지 문구로 적는다."""
    return (
        "CONSOLIDATED FINANCIAL STATEMENTS" in upperLabel
        or "SUPPLEMENTARY DATA" in upperLabel
        or "SUPPLEMENTAL FINANCIAL" in upperLabel
        or "UNAUDITED SUPPLEMENTAL" in upperLabel
        or "SUPPLEMENTAL PRESENTATION" in upperLabel
        or upperLabel == f"ITEM {itemNum}"
        or not itemLabel
    )


def _refineItemLabel(itemNum: str, itemLabel: str) -> tuple[str, str | None]:
    """Item 번호별로 라벨을 정본 표기로 다듬는다.

    같은 절이 서식(10-K, 10-Q, 20-F)마다 다른 번호와 다른 문구로 온다. 번호를 알면
    라벨을 정할 수 있는 자리라 번호별로 모아 둔다.

    Returns:
        ``(라벨, 완결제목)``. 완결제목이 있으면 호출자는 그것을 그대로 돌려준다.
        번호까지 바뀌는 경우가 있어서 라벨만으로는 표현할 수 없다.
    """
    upperLabel = itemLabel.upper()
    # Item 1A in 10-Q: "UNAUDITED SUPPLEMENTAL" → Supplemental Financial
    if itemNum == "1A" and "UNAUDITED SUPPLEMENTAL" in upperLabel:
        return itemLabel, "Item 8A. Supplemental Financial Information"

    if itemNum in {"4A", "1D"} and _isExecutiveOfficerLabel(itemNum, itemLabel, upperLabel):
        itemLabel = "Executive Officers of the Registrant"

    # Item 8A/8B: Supplemental Financial 또는 Controls
    if itemNum in {"8A", "8B"}:
        if _isSupplementalLabel(itemNum, itemLabel, upperLabel):
            itemLabel = "Supplemental Financial Information"
        elif "OTHER INFORMATION" in upperLabel:
            return itemLabel, "Item 9B. Other Information"
        elif "CONTROLS AND PROCEDURES" in upperLabel:
            return itemLabel, "Item 9A. Controls and Procedures"

    # Item 15A: Financial Statements (alias of Item 15)
    if itemNum == "15A":
        if not itemLabel or "FINANCIAL" in upperLabel or upperLabel == f"ITEM {itemNum}":
            return itemLabel, "Item 15. Exhibits & Schedules"

    # Item 4B: Mine Safety Disclosures (오타 포함)
    if itemNum == "4B":
        if "MINE" in upperLabel and "SAFETY" in upperLabel:
            return itemLabel, "Item 4B. Mine Safety Disclosures"

    # Item 5A (20-F): "of this report" 변형
    if itemNum == "5A":
        if "OF THIS REPORT" in upperLabel or not itemLabel:
            itemLabel = "Operating and Financial Review and Prospects"

    # Item 3D (20-F): "Risk Factors on pages..." 변형
    if itemNum == "3D":
        if "RISK FACTORS" in upperLabel:
            itemLabel = "Risk Factors"

    return itemLabel, None


def normalizeSectionTitle(title: str) -> str:
    """SEC filing section title 을 정규화 (오타 보정, Part-Item 통합, Regulation S-K 수렴).

    Args:
        title: 원본 section title.

    Returns:
        정규화된 ``"Item NN. Label"`` 형식 문자열.

    Raises:
        없음.

    Example:
        >>> normalizeSectionTitle("ITEM 1A. RISK FACTORS")
        'Item 1A. Risk Factors'
    """
    text = _MULTISPACE_RE.sub(" ", title.strip())
    text = text.replace("§", "section")
    text = _DASH_CHARS_RE.sub("-", text)
    # curly quotes → straight quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = _cleanPipes(text)

    # 오타 보정: "IT EM 1A." / "I tem 1A." → "Item 1A."
    brokenMatch = _BROKEN_ITEM_RE.match(text)
    if brokenMatch:
        text = f"Item {brokenMatch.group(1)}. {brokenMatch.group(2)}"
        text = _MULTISPACE_RE.sub(" ", text).strip()

    # "Part I - Item 1A. IT EM 1A. RISK FACTORS" → 내부 오타 보정
    innerBroken = re.sub(
        r"(?:IT\s+EM|I\s+tem)\s+\d+[A-Z]?\.\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    if innerBroken != text:
        text = _MULTISPACE_RE.sub(" ", innerBroken).strip()

    regulationTitle = _regulationSkTitle(text)
    if regulationTitle is not None:
        return regulationTitle

    partResult = _normalizePartItem(text)
    if partResult != text:
        return partResult

    # "ITEM 4A" (마침표 없음) → "Item 4A." 로 보정 후 재시도
    noDotsMatch = re.match(r"^(?:ITEM|Item|item)\s+(\d+[A-Z]?)\s*$", text)
    if noDotsMatch:
        text = f"Item {noDotsMatch.group(1).upper()}."

    itemMatch = _ITEM_RE.match(text)
    if not itemMatch:
        return _nonItemTitle(text)

    itemNum = itemMatch.group(1).upper()
    itemLabel = _MULTISPACE_RE.sub(" ", itemMatch.group(2).strip())

    # 중복 label 제거: "Item 12D. ITEM 12D" → "Item 12D."
    dupeMatch = _DUPE_LABEL_RE.match(f"Item {itemNum}. {itemLabel}")
    if dupeMatch:
        innerLabel = dupeMatch.group(2).strip()
        if innerLabel:
            itemLabel = innerLabel
        else:
            itemLabel = ""

    itemLabel = itemLabel.rstrip(".")
    upperLabel = itemLabel.upper()

    itemLabel, finalTitle = _refineItemLabel(itemNum, itemLabel)
    if finalTitle is not None:
        return finalTitle

    return f"Item {itemNum}. {itemLabel}".strip()


@lru_cache(maxsize=1)
def loadSectionMappings() -> dict[str, str]:
    """sectionMappings.json 을 로드하여 정규화된 키-값 매핑 dict 를 반환.

    2026-04-19 계열 사고 방지 — wheel 누락 시 silent ``{}`` 대신 loud-fail.

    Returns:
        ``{normalizedTitle: topicId}`` dict.

    Raises:
        FileNotFoundError: 번들 리소스 부재.

    Example:
        >>> loadSectionMappings()["Item 1A. Risk Factors"]
    """
    path = _mappingPath()
    if not path.exists():
        raise FileNotFoundError(f"필수 번들 리소스 누락: {path}\n  → pip install -U --force-reinstall dartlab")

    raw = json.loads(path.read_text(encoding="utf-8"))
    expanded: dict[str, str] = {}
    for key, value in raw.items():
        normalizedKey = normalizeSectionTitle(key)
        expanded[normalizedKey] = value
    return expanded


@lru_cache(maxsize=1)
def _lowercaseMappings() -> dict[str, str]:
    """case-insensitive fallback용 소문자 키 매핑."""
    return {k.lower(): v for k, v in loadSectionMappings().items()}


def mapSectionTitle(formType: str, title: str) -> str:
    """section title 을 정규화하고 매핑을 적용하여 ``"formType::topic"`` 형태로 반환.

    Args:
        formType: ``"10-K"``/``"10-Q"``/``"20-F"`` 등.
        title: 원본 section title.

    Returns:
        ``"10-K::item1ARiskFactors"`` 형식 문자열.

    Raises:
        FileNotFoundError: 번들 리소스 부재.

    Example:
        >>> mapSectionTitle("10-K", "ITEM 1A. RISK FACTORS")
        '10-K::item1ARiskFactors'
    """
    normalized = normalizeSectionTitle(title)
    mappings = loadSectionMappings()
    mapped = mappings.get(normalized)
    if mapped is None:
        mapped = _lowercaseMappings().get(normalized.lower(), normalized)
    return f"{formType}::{mapped}"
