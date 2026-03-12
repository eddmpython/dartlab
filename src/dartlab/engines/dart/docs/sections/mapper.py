from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")
_MULTISPACE_RE = re.compile(r"\s+")
_LEAF_PREFIX_RE = re.compile(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+")


def _mappingPath() -> Path:
    return Path(__file__).resolve().parent / "mapperData" / "sectionMappings.json"


def stripSectionPrefix(title: str) -> str:
    return _LEAF_PREFIX_RE.sub("", title.strip())


def normalizeSectionTitle(title: str) -> str:
    text = stripSectionPrefix(title)
    text = _INDUSTRY_PREFIX_RE.sub("", text)
    text = stripSectionPrefix(text)
    text = text.replace("ㆍ", ",")
    text = _MULTISPACE_RE.sub("", text)
    return text.strip()


@lru_cache(maxsize=1)
def loadSectionMappings() -> dict[str, str]:
    path = _mappingPath()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    expanded: dict[str, str] = {}
    for key, value in raw.items():
        expanded[normalizeSectionTitle(key)] = value
    return expanded


def mapSectionTitle(title: str) -> str:
    normalized = normalizeSectionTitle(title)
    return loadSectionMappings().get(normalized, normalized)
