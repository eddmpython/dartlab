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

# 직원수 추출 패턴. providers(L1)가 파싱 SSOT. scan(L1.5) employeeBuild 가 downward import 로 공유한다.
# 구체 우선(approximately/had/total of...) 후 일반("NNN employees"). 첫 매칭 채택.
_EMPLOYEE_PATTERNS = [
    re.compile(r"approximately\s+([\d,]+)\s+(?:full[- ]?time\s+)?employees", re.IGNORECASE),
    re.compile(r"had\s+approximately\s+([\d,]+)\s+employees", re.IGNORECASE),
    re.compile(r"employed?\s+approximately\s+([\d,]+)\s+(?:people|personnel|workers)", re.IGNORECASE),
    re.compile(r"total\s+of\s+([\d,]+)\s+employees", re.IGNORECASE),
    re.compile(r"([\d,]+)\s+full[- ]?time\s+(?:equivalent\s+)?employees", re.IGNORECASE),
    re.compile(r"(?:we|the company)\s+had\s+([\d,]+)\s+employees", re.IGNORECASE),
    re.compile(r"workforce\s+of\s+approximately\s+([\d,]+)", re.IGNORECASE),
    re.compile(r"([\d,]+)\s+employees", re.IGNORECASE),
]


def parseEmployeeCount(text: str) -> int | None:
    """10-K 본문 텍스트에서 직원수 추출. 패턴 우선순위 + 상식 범위(10~5,000,000) 가드.

    구체 패턴(approximately/had/total of...)을 먼저 시도하고, 매칭 시 쉼표 제거 후 정수화한다. 상식
    범위를 벗어난 값(오탐. 연도·금액 등)은 거른다. scan ``employeeBuild`` 가 본 함수를 공유한다(파싱 SSOT).

    Args:
        text: 10-K Item1/Human Capital 등의 본문 텍스트.

    Returns:
        int | None. 직원수(10~5M). 패턴 미매칭 또는 범위 밖이면 None.

    Raises:
        없음.

    Example:
        >>> parseEmployeeCount("we had approximately 164,000 full-time employees")
        164000
    """
    for pattern in _EMPLOYEE_PATTERNS:
        match = pattern.search(text)
        if match:
            cleaned = match.group(1).replace(",", "").strip()
            try:
                val = int(cleaned)
            except ValueError:
                continue
            if 10 <= val <= 5_000_000:
                return val
    return None


def extractEmployee(company: "Company") -> pl.DataFrame | None:
    """직원 현황 추출.

    1순위: XBRL EntityNumberOfEmployees
    2순위: 10-K Item 1 텍스트 regex

    Args:
        company: EDGAR Company 인스턴스.

    Returns:
        ``period/headcount/source`` 컬럼 DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> extractEmployee(Company("AAPL"))
    """
    rows: list[dict] = []

    # 1순위: XBRL
    #
    # 예전에는 company.timeseries 가 있을 때만 아래로 갔다. 그 이름은 Company 표면에 없어
    # 매번 AttributeError 였고 except 가 그것을 지워, XBRL 경로가 한 번도 실행되지 않았다.
    # _getEmployeeFacts 는 cik 와 로컬 parquet 만 보므로 그 가드가 애초에 필요 없다.
    rows.extend(_getEmployeeFacts(company))

    # 2순위: 10-K 텍스트 파싱
    if not rows:
        sections = company._docs.sections
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
                    count = parseEmployeeCount(fullText)
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
            .collect(engine="streaming")
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
