from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_MULTISPACE_RE = re.compile(r"\s+")
_ITEM_RE = re.compile(r"^Item\s+(\d+[A-Z]?)\.\s*(.*)$", re.IGNORECASE)
_REG_S_K_RE = re.compile(r"^Item 405\. of Regulation S-K.*$", re.IGNORECASE)
_ITEM_601_RE = re.compile(r"^Item 601\. of Regulation S-K.*$", re.IGNORECASE)
_ITEM_406_RE = re.compile(r"^Item 406\. of Regulation S-K.*$", re.IGNORECASE)


def _mappingPath() -> Path:
    return Path(__file__).resolve().parent / "mapperData" / "sectionMappings.json"


def normalizeSectionTitle(title: str) -> str:
    text = _MULTISPACE_RE.sub(" ", title.strip())
    text = text.replace("§", "section")
    if _REG_S_K_RE.match(text):
        return "Item 405. of Regulation S-K"
    if _ITEM_406_RE.match(text):
        return "Item 406. of Regulation S-K"
    if _ITEM_601_RE.match(text):
        return "Item 15. Exhibits & Schedules"
    itemMatch = _ITEM_RE.match(text)
    if not itemMatch:
        return text

    itemNum = itemMatch.group(1).upper()
    itemLabel = _MULTISPACE_RE.sub(" ", itemMatch.group(2).strip())
    if itemNum == "4A":
        upperLabel = itemLabel.upper()
        if (
            not itemLabel
            or upperLabel == "ITEM 4A"
            or upperLabel.startswith("|")
            or "EXECUTIVE OFFICERS OF THE" in upperLabel
        ):
            itemLabel = "Executive Officers of the Registrant"
    if itemNum in {"8A", "8B"} and "SUPPLEMENTARY DATA OF AMERICAN AIRLINES" in itemLabel.upper():
        itemLabel = "Supplemental Financial Information"
    if itemNum in {"8A", "8B"} and itemLabel.lower() == "supplemental financial information (unaudited)":
        itemLabel = "Supplemental Financial Information"
    if itemNum in {"8A", "8B"} and itemLabel in {"", f"Item {itemNum}", f"Item {itemNum}"}:
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
