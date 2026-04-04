"""직원 현황 추출 — 10-K Item 1 텍스트 + XBRL.

10-K Item 1 (Business) 섹션에서 직원 수를 regex로 추출.
XBRL EntityNumberOfEmployees 태그가 있으면 우선 사용.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company

# 직원 수 추출 패턴
_EMPLOYEE_PATTERNS = [
    # "approximately 164,000 full-time employees"
    re.compile(r"approximately\s+([\d,]+)\s+(?:full[- ]?time\s+)?employees", re.IGNORECASE),
    # "had approximately 161,000 employees"
    re.compile(r"had\s+approximately\s+([\d,]+)\s+employees", re.IGNORECASE),
    # "employed approximately 228,000 people"
    re.compile(r"employed?\s+approximately\s+([\d,]+)\s+(?:people|personnel|workers)", re.IGNORECASE),
    # "total of 181,000 employees"
    re.compile(r"total\s+of\s+([\d,]+)\s+employees", re.IGNORECASE),
    # "181,000 full-time equivalent employees"
    re.compile(r"([\d,]+)\s+full[- ]?time\s+(?:equivalent\s+)?employees", re.IGNORECASE),
    # "We had 221,000 employees"
    re.compile(r"(?:we|the company)\s+had\s+([\d,]+)\s+employees", re.IGNORECASE),
    # "our workforce of approximately 150,000"
    re.compile(r"workforce\s+of\s+approximately\s+([\d,]+)", re.IGNORECASE),
    # 단순 "NNN,NNN employees"
    re.compile(r"([\d,]+)\s+employees", re.IGNORECASE),
]


def _parseNumber(text: str) -> int | None:
    """쉼표 제거 후 정수 변환."""
    cleaned = text.replace(",", "").strip()
    try:
        val = int(cleaned)
        # 상식적 범위: 10명 ~ 5,000,000명
        return val if 10 <= val <= 5_000_000 else None
    except ValueError:
        return None


def extractEmployee(company: "Company") -> pl.DataFrame | None:
    """직원 현황 추출.

    1순위: XBRL EntityNumberOfEmployees
    2순위: 10-K Item 1 텍스트 regex
    """
    rows: list[dict] = []

    # 1순위: XBRL
    try:
        ts, periods = company.timeseries or (None, None)
        if ts is not None and periods:
            # XBRL facts에서 직접 탐색
            facts = _getEmployeeFacts(company)
            if facts:
                for record in facts:
                    rows.append(record)
    except (AttributeError, TypeError):
        pass

    # 2순위: 10-K 텍스트 파싱
    if not rows:
        sections = company.docs.sections
        if sections is not None and not sections.is_empty():
            # Item 1 Business 섹션 찾기
            item1Topics = sections.filter(pl.col("topic").str.contains("(?i)item1Business|item1$"))
            if item1Topics.height > 0:
                periodCols = [
                    c
                    for c in item1Topics.columns
                    if c
                    not in (
                        "topic",
                        "blockType",
                        "blockOrder",
                        "textNodeType",
                        "textLevel",
                        "textPath",
                    )
                ]
                for pcol in periodCols:
                    texts = item1Topics[pcol].drop_nulls().to_list()
                    fullText = " ".join(str(t) for t in texts)
                    count = _extractEmployeeCount(fullText)
                    if count is not None:
                        rows.append({"period": pcol, "employeeCount": count, "source": "10-K_text"})

    return pl.DataFrame(rows) if rows else None


def _getEmployeeFacts(company: "Company") -> list[dict]:
    """XBRL facts에서 EntityNumberOfEmployees 추출."""
    from dartlab.providers.edgar.report import edgarFinancePath

    cik = getattr(company, "cik", None)
    if not cik:
        return []

    path = edgarFinancePath(cik)
    if not path.exists():
        return []

    try:
        df = (
            pl.scan_parquet(path)
            .filter(pl.col("tag").str.contains("(?i)NumberOfEmployees") & pl.col("form").is_in(["10-K", "20-F"]))
            .select("fy", "val", "filed")
            .collect()
        )

        if df.is_empty():
            return []

        # 연도별 최신값
        df = df.sort("filed", descending=True).unique(subset=["fy"], keep="first")
        records = []
        for row in df.iter_rows(named=True):
            fy = row.get("fy")
            val = row.get("val")
            if fy is not None and val is not None:
                records.append(
                    {
                        "period": str(fy),
                        "employeeCount": int(val),
                        "source": "XBRL",
                    }
                )
        return records
    except (pl.exceptions.ComputeError, OSError):
        return []


def _extractEmployeeCount(text: str) -> int | None:
    """텍스트에서 직원 수 추출."""
    for pattern in _EMPLOYEE_PATTERNS:
        match = pattern.search(text)
        if match:
            val = _parseNumber(match.group(1))
            if val is not None:
                return val
    return None
