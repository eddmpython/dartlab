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
    r"^Part\s+(I{1,2})\s*-\s*Item\s+(\d+[A-Z]?)\.\s*(.*)$", re.IGNORECASE,
)
_REG_S_K_RE = re.compile(r"^Item\s+(?:405|103)\.\s+of\s+(?:SEC\s+)?Regulation\s+S-K.*$", re.IGNORECASE)
_ITEM_601_RE = re.compile(r"^Item 601\. of Regulation S-K.*$", re.IGNORECASE)
_ITEM_406_RE = re.compile(r"^Item 406\. of Regulation S-K.*$", re.IGNORECASE)


def _mappingPath() -> Path:
    return Path(__file__).resolve().parent / "mapperData" / "sectionMappings.json"


def _cleanPipes(text: str) -> str:
    if "|" not in text:
        return text
    cleaned = _PIPE_RE.sub(" ", text)
    return _MULTISPACE_RE.sub(" ", cleaned).strip()


def _normalizePartItem(text: str) -> str:
    partMatch = _PART_ITEM_RE.match(text)
    if not partMatch:
        return text
    partNum = partMatch.group(1).upper()
    itemNum = partMatch.group(2).upper()
    itemLabel = _MULTISPACE_RE.sub(" ", partMatch.group(3).strip())
    itemLabel = _cleanPipes(itemLabel)
    itemLabelInner = re.sub(r"^Item\s+\d+[A-Z]?\.\s*", "", itemLabel, flags=re.IGNORECASE).strip()
    if itemLabelInner:
        itemLabel = itemLabelInner
    itemLabel = itemLabel.rstrip(".")

    if itemNum in {"5", "6"} and partNum == "I":
        partNum = "II"
    if itemNum == "1A" and partNum == "I" and itemLabel.upper() == "RISK FACTORS":
        partNum = "II"

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
        ("II", "6"): "Exhibits",
    }
    canon = canonLabels.get((partNum, itemNum))
    if canon:
        itemLabel = canon

    return f"Part {partNum} - Item {itemNum}. {itemLabel}"


def normalizeSectionTitle(title: str) -> str:
    text = _MULTISPACE_RE.sub(" ", title.strip())
    text = text.replace("§", "section")
    text = _DASH_CHARS_RE.sub("-", text)
    text = _cleanPipes(text)
    if _REG_S_K_RE.match(text):
        return "Item 405. of Regulation S-K"
    if _ITEM_406_RE.match(text):
        return "Item 406. of Regulation S-K"
    if _ITEM_601_RE.match(text):
        return "Item 15. Exhibits & Schedules"

    partResult = _normalizePartItem(text)
    if partResult != text:
        return partResult

    itemMatch = _ITEM_RE.match(text)
    if not itemMatch:
        return text

    itemNum = itemMatch.group(1).upper()
    itemLabel = _MULTISPACE_RE.sub(" ", itemMatch.group(2).strip())
    itemLabel = itemLabel.rstrip(".")
    upperLabel = itemLabel.upper()
    if itemNum == "4A":
        if (
            not itemLabel
            or upperLabel == "ITEM 4A"
            or "EXECUTIVE OFFICERS OF THE" in upperLabel
        ):
            itemLabel = "Executive Officers of the Registrant"
    if itemNum in {"8A", "8B"}:
        if (
            "CONSOLIDATED FINANCIAL STATEMENTS" in upperLabel
            or "SUPPLEMENTARY DATA" in upperLabel
            or "SUPPLEMENTAL FINANCIAL" in upperLabel
            or upperLabel == f"ITEM {itemNum}"
            or not itemLabel
        ):
            itemLabel = "Supplemental Financial Information"
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


def mapSectionTitle(formType: str, title: str) -> str:
    normalized = normalizeSectionTitle(title)
    mapped = loadSectionMappings().get(normalized, normalized)
    return f"{formType}::{mapped}"
