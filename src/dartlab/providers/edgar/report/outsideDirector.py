"""사외이사 추출 — 10-K Item 10 텍스트 파싱.

DEF 14A proxy 없이도 10-K에서 이사회 구성을 추출할 수 있다.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company

_INDEPENDENT_PATTERN = re.compile(
    r"(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)"
    r".*?(?:independent|outside|non-executive)\s*(?:director|member)",
    re.IGNORECASE | re.DOTALL,
)


def extractOutsideDirector(company: "Company") -> pl.DataFrame | None:
    """사외이사 정보 추출.

    10-K Item 10 (Directors and Corporate Governance) 섹션에서
    independent director 언급을 파싱.
    """
    sections = company.docs.sections
    if sections is None or sections.is_empty():
        return None

    item10 = sections.filter(
        pl.col("topic").str.contains("(?i)item10|directors|corporateGovernance")
    )
    if item10.is_empty():
        return None

    periodCols = [c for c in item10.columns if c not in (
        "topic", "blockType", "blockOrder", "textNodeType",
        "textLevel", "textPath",
    )]
    if not periodCols:
        return None

    latestPeriod = periodCols[-1]
    texts = item10[latestPeriod].drop_nulls().to_list()
    fullText = " ".join(str(t) for t in texts)

    # independent director 수 추정
    independentCount = len(re.findall(r"(?i)independent\s+director", fullText))
    totalBoard = len(re.findall(r"(?i)(?:director|member\s+of\s+the\s+board)", fullText))

    if independentCount == 0 and totalBoard == 0:
        return None

    return pl.DataFrame([{
        "period": latestPeriod,
        "independentDirectors": independentCount if independentCount > 0 else None,
        "totalBoardMentions": totalBoard if totalBoard > 0 else None,
        "source": "10-K_text",
    }])
