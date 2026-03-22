"""ESG 진전도 타임라인.

sections의 기간별 ESG 키워드 존재 여부를 추적하여
연도별 ESG 공시 진전도를 평가한다.
"""

from __future__ import annotations

import re

import polars as pl

from dartlab.engines.esg.taxonomy import (
    ENVIRONMENT_KEYWORDS,
    SOCIAL_KEYWORDS,
    TOPIC_TO_PILLAR,
)

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def esg_timeline(sections: pl.DataFrame | None) -> pl.DataFrame:
    """기간별 ESG 키워드 커버리지 타임라인.

    Args:
        sections: topic × period DataFrame.

    Returns:
        period, E_coverage, S_coverage, G_coverage, total_keywords 컬럼의 DataFrame.
    """
    if sections is None:
        return pl.DataFrame(
            schema={
                "period": pl.Utf8,
                "E_keywords": pl.Int64,
                "S_keywords": pl.Int64,
                "G_topics": pl.Int64,
                "total": pl.Int64,
            }
        )

    periods = [c for c in sections.columns if _PERIOD_RE.fullmatch(c)]
    if not periods:
        return pl.DataFrame(
            schema={
                "period": pl.Utf8,
                "E_keywords": pl.Int64,
                "S_keywords": pl.Int64,
                "G_topics": pl.Int64,
                "total": pl.Int64,
            }
        )

    has_topic = "topic" in sections.columns
    rows = []

    for period in periods:
        # 기간별 텍스트 합침
        all_text = ""
        g_topics = 0

        for row in sections.iter_rows(named=True):
            cell = str(row.get(period) or "")
            if cell:
                all_text += " " + cell

            # G 관련 topic 카운트
            if has_topic and cell:
                topic = row.get("topic", "")
                if TOPIC_TO_PILLAR.get(topic) == "G":
                    g_topics += 1

        # E 키워드 카운트
        e_count = 0
        for kw_list in ENVIRONMENT_KEYWORDS.values():
            e_count += sum(1 for kw in kw_list if kw in all_text)

        # S 키워드 카운트
        s_count = 0
        for kw_list in SOCIAL_KEYWORDS.values():
            s_count += sum(1 for kw in kw_list if kw in all_text)

        rows.append(
            {
                "period": period,
                "E_keywords": e_count,
                "S_keywords": s_count,
                "G_topics": g_topics,
                "total": e_count + s_count + g_topics,
            }
        )

    return pl.DataFrame(rows).sort("period", descending=True)
