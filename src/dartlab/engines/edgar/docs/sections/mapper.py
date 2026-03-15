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
_ITEM_601_RE = re.compile(r"^Item 601\. of Regulation S-K.*$", re.IGNORECASE)
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
        if itemNum == "1A" and partNum == "I" and itemLabel.upper() == "RISK FACTORS":
            partNum = "II"
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


def normalizeSectionTitle(title: str) -> str:
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

    # "of Regulation S-K ..." — Item prefix 없이 시작 → 일괄 Reg S-K disclosure
    if _LOOSE_REG_RE.match(text) or _UNDER_REG_RE.match(text) or _OF_SK_RE.match(text):
        return "Item 405. of Regulation S-K"

    # "and the registrant, at the time of filing..." → Item 405 변형
    if _LOOSE_405_RE.match(text):
        return "Item 405. of Regulation S-K"

    # Regulation S-K 계열 일괄 처리
    if _REG_S_K_RE.match(text):
        return "Item 405. of Regulation S-K"
    if _ITEM_406_RE.match(text):
        return "Item 406. of Regulation S-K"
    if _ITEM_601_RE.match(text):
        return "Item 15. Exhibits & Schedules"
    regMatch = _REG_3DIGIT_RE.match(text)
    if regMatch:
        regNum = regMatch.group(1)
        return f"Item {regNum}. of Regulation S-K"

    # "Item 405. and the registrant..." 형태
    item405Loose = re.match(
        r"^Item\s+405\.\s+and\s+the\s+registrant",
        text,
        re.IGNORECASE,
    )
    if item405Loose:
        return "Item 405. of Regulation S-K"

    partResult = _normalizePartItem(text)
    if partResult != text:
        return partResult

    # "ITEM 4A" (마침표 없음) → "Item 4A." 로 보정 후 재시도
    noDotsMatch = re.match(r"^(?:ITEM|Item|item)\s+(\d+[A-Z]?)\s*$", text)
    if noDotsMatch:
        text = f"Item {noDotsMatch.group(1).upper()}."

    itemMatch = _ITEM_RE.match(text)
    if not itemMatch:
        # Non-Item titles: "EXECUTIVE OFFICERS OF THE REGISTRANT" 등
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

    # 10-K Item 4A: Executive Officers
    if itemNum == "4A":
        if (
            not itemLabel
            or upperLabel == "ITEM 4A"
            or "EXECUTIVE OFFICERS" in upperLabel
            or "EXECUTIVE" == upperLabel
            or "INFORMATION ABOUT OUR EXECUTIVE" in upperLabel
            or "IN PART I OF THIS ANNUAL" in upperLabel
        ):
            itemLabel = "Executive Officers of the Registrant"

    # 10-K Item 1D: Executive Officers (newer 10-K format)
    if itemNum == "1D":
        if "EXECUTIVE" in upperLabel or not itemLabel:
            itemLabel = "Executive Officers of the Registrant"

    # Item 8A/8B: Supplemental Financial 또는 Controls
    if itemNum in {"8A", "8B"}:
        if (
            "CONSOLIDATED FINANCIAL STATEMENTS" in upperLabel
            or "SUPPLEMENTARY DATA" in upperLabel
            or "SUPPLEMENTAL FINANCIAL" in upperLabel
            or "UNAUDITED SUPPLEMENTAL" in upperLabel
            or "SUPPLEMENTAL PRESENTATION" in upperLabel
            or upperLabel == f"ITEM {itemNum}"
            or not itemLabel
        ):
            itemLabel = "Supplemental Financial Information"
        elif "OTHER INFORMATION" in upperLabel:
            return "Item 9B. Other Information"
        elif "CONTROLS AND PROCEDURES" in upperLabel:
            return "Item 9A. Controls and Procedures"

    # Item 15A: Financial Statements (alias of Item 15)
    if itemNum == "15A":
        if not itemLabel or "FINANCIAL" in upperLabel or upperLabel == f"ITEM {itemNum}":
            return "Item 15. Exhibits & Schedules"

    return f"Item {itemNum}. {itemLabel}".strip()


@lru_cache(maxsize=1)
def loadSectionMappings() -> dict[str, str]:
    path = _mappingPath()
    if not path.exists():
        return {}

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
    normalized = normalizeSectionTitle(title)
    mappings = loadSectionMappings()
    mapped = mappings.get(normalized)
    if mapped is None:
        mapped = _lowercaseMappings().get(normalized.lower(), normalized)
    return f"{formType}::{mapped}"
