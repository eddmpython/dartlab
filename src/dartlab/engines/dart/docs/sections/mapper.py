from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")
_MULTISPACE_RE = re.compile(r"\s+")
_LEAF_PREFIX_RE = re.compile(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+")
_TRAILING_PUNCT_RE = re.compile(r"[-–—:：;,]+$")
_PATTERN_MAPPINGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^지적재산권보유현황\(.+\)$"), "intellectualProperty"),
    (re.compile(r"^연구개발실적\(.+\)$"), "majorContractsAndRnd"),
    (re.compile(r"^주요지적재산권현황\(상세\)$"), "intellectualProperty"),
    (re.compile(r"^수주(?:상황|현황)\(상세\)$"), "salesOrder"),
    (re.compile(r"^경영상의주요계약(?:\(|\[)상세(?:\)|\])$"), "majorContractsAndRnd"),
    (re.compile(r"^투자매매업무-장내파생상품거래현황\(상세\)$"), "riskDerivative"),
    (re.compile(r"^\(.+\)신용파생상품상세명세(?:\(상세\))?$"), "riskDerivative"),
    (re.compile(r"^(?:투자매매업무-증권거래현황|투자중개업무-금융투자상품의위탁매매및수수료현황)\(상세\)$"), "productService"),
    (re.compile(r"^(?:\(.+\)(?:예금업무|대출업무|e-금융서비스|방카슈랑스|신용카드상품|대출상품|예금상품|외환/수출입서비스|기타업무-외환/수출입서비스|기타업무-e-금융서비스|상품및서비스개요|신탁업무)|투자일임업무-투자운용인력현황|투자운용인력현황)\(상세\)$"), "productService"),
    (re.compile(r"^(?:신탁업무-재무제표|신탁업무재무제표)\(상세\)$"), "financialNotes"),
    (re.compile(r"^기업집단에소속된회사\(상세\)$"), "affiliateGroupDetail"),
)


def _mappingPath() -> Path:
    return Path(__file__).resolve().parent / "mapperData" / "sectionMappings.json"


def stripSectionPrefix(title: str) -> str:
    return _LEAF_PREFIX_RE.sub("", title.strip())


def normalizeSectionTitle(title: str) -> str:
    text = stripSectionPrefix(title)
    text = _INDUSTRY_PREFIX_RE.sub("", text)
    text = stripSectionPrefix(text)
    text = text.replace("ㆍ", ",")
    text = text.replace("·", ",")
    text = _MULTISPACE_RE.sub("", text)
    text = _TRAILING_PUNCT_RE.sub("", text)
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
    mapped = loadSectionMappings().get(normalized)
    if mapped:
        return mapped
    for pattern, topic in _PATTERN_MAPPINGS:
        if pattern.match(normalized):
            return topic
    return normalized
