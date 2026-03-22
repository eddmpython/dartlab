"""EDINET 유가증券보고서 section title → topicId 매핑.

DART/EDGAR sections mapper와 동일한 패턴:
1. normalizeSectionTitle() — 전각→반각, 공백, 번호 패턴 정규화
2. mapSectionTitle() — sectionMappings.json 조회 → topicId

유가증券보고서 구조:
  第一部 企業情報
    第1 企業の概況 (회사 개요)
    第2 事業の状況 (사업 현황)
    第3 設備の状況 (설비 현황)
    第4 提出会社の状況 (제출회사 현황)
    第5 経理の状況 (재무 현황)
  第二部 提出会社の保証会社等の情報
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "mapperData"

# ── 정규화 패턴 ──

# 전각 숫자/영문 → 반각
_FULLWIDTH_OFFSET = 0xFEE0

# 번호 패턴: "第1", "第２", "1.", "１．", "(1)", "（１）"
_SECTION_NUM_RE = re.compile(
    r"^(?:第[一二三四五六七八九十\d１２３４５６７８９０]+\s*|"
    r"\d+[.．]\s*|"
    r"[（(]\d+[)）]\s*|"
    r"[①②③④⑤⑥⑦⑧⑨⑩]\s*)"
)

# 다중 공백 → 단일
_MULTISPACE_RE = re.compile(r"\s+")

# 【】 제거
_BRACKET_RE = re.compile(r"[【】]")


def _toHalfWidth(text: str) -> str:
    """전각 영숫자/기호 → 반각."""
    result: list[str] = []
    for ch in text:
        cp = ord(ch)
        if 0xFF01 <= cp <= 0xFF5E:
            result.append(chr(cp - _FULLWIDTH_OFFSET))
        elif cp == 0x3000:
            result.append(" ")
        else:
            result.append(ch)
    return "".join(result)


def normalizeSectionTitle(title: str) -> str:
    """section title 정규화.

    전각→반각, 번호 제거, 공백 정규화, 앞뒤 공백 제거.

    Args:
        title: 원본 section title.

    Returns:
        정규화된 title.
    """
    if not title:
        return ""

    text = _toHalfWidth(title)
    text = _BRACKET_RE.sub("", text)
    text = _MULTISPACE_RE.sub(" ", text).strip()

    # 선행 번호 제거
    text = _SECTION_NUM_RE.sub("", text).strip()

    return text


# ── 매핑 ──


@lru_cache(maxsize=1)
def _loadMappings() -> dict[str, str]:
    path = _DATA_DIR / "sectionMappings.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mapSectionTitle(title: str) -> str | None:
    """section title → topicId 매핑.

    Args:
        title: 원본 또는 정규화된 section title.

    Returns:
        topicId (camelCase) 또는 None.
    """
    mappings = _loadMappings()

    # 원본으로 먼저 시도
    if title in mappings:
        return mappings[title]

    # 정규화 후 시도
    normalized = normalizeSectionTitle(title)
    if normalized in mappings:
        return mappings[normalized]

    # 부분 매칭 (핵심 키워드 포함 여부)
    normalizedLower = normalized.lower()
    for key, topicId in mappings.items():
        if key in normalized or normalized in key:
            return topicId

    return None
