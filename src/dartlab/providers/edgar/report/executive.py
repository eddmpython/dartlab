"""임원 현황 추출 — 10-K Item 10/XBRL officer 정보."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company

_OFFICER_PATTERN = re.compile(
    r"(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)"
    r"\s*[,\-–—]\s*"
    r"((?:Chief|President|Vice|Senior|Executive|General|Director|Secretary|Treasurer|Controller|Officer)[\w\s,]*)",
    re.MULTILINE,
)


def extractExecutive(company: "Company") -> pl.DataFrame | None:
    """임원 목록 추출.

    1순위: 10-K Item 10 섹션 텍스트 파싱
    2순위: XBRL에서 officer 관련 태그 (제한적)
    """
    sections = company.docs.sections
    if sections is None or sections.is_empty():
        return None

    # Item 10 Directors & Officers 섹션
    item10 = sections.filter(
        pl.col("topic").str.contains("(?i)item10|executiveOfficers|directors")
    )
    if item10.is_empty():
        # Item 1에 Executive Officers 포함된 경우도 있음
        item10 = sections.filter(
            pl.col("topic").str.contains("(?i)item1Business")
        )

    if item10.is_empty():
        return None

    # 가장 최신 기간
    periodCols = [c for c in item10.columns if c not in (
        "topic", "blockType", "blockOrder", "textNodeType",
        "textLevel", "textPath",
    )]
    if not periodCols:
        return None

    latestPeriod = periodCols[-1]
    texts = item10[latestPeriod].drop_nulls().to_list()
    fullText = " ".join(str(t) for t in texts)

    officers = _parseOfficers(fullText)
    if not officers:
        return None

    return pl.DataFrame([
        {"name": name, "title": title, "period": latestPeriod}
        for name, title in officers
    ])


def _parseOfficers(text: str) -> list[tuple[str, str]]:
    """텍스트에서 임원 이름+직책 쌍 추출."""
    matches = _OFFICER_PATTERN.findall(text)
    seen = set()
    results = []
    for name, title in matches:
        name = name.strip()
        title = title.strip().rstrip(",. ")
        key = name.lower()
        if key not in seen and len(name) > 3:
            seen.add(key)
            results.append((name, title))
    return results[:50]  # 상한
