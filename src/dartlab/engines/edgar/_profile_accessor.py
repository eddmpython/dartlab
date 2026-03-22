"""EDGAR profile namespace — docs spine + finance merge layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.engines.edgar.company import Company


def _isPeriodColumn(col: str) -> bool:
    import re

    return bool(re.fullmatch(r"\d{4}(Q[1-4])?", col))


class _ProfileAccessor:
    """EDGAR profile namespace — docs spine + finance/report merge layer.

    DART Company.profile과 동일한 사상:
    - docs.sections가 구조적 뼈대
    - finance가 숫자 authoritative → docs 요약재무 대체
    - 서술형/정성 정보는 docs authoritative
    """

    def __init__(self, company: Company):
        self._company = company

    @property
    def sections(self) -> pl.DataFrame | None:
        """sections — docs + finance 통합 지도."""
        cacheKey = "_sections"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        docsSec = self._company.docs.sections
        if docsSec is None:
            self._company._cache[cacheKey] = None
            return None

        periodCols = [c for c in docsSec.columns if _isPeriodColumn(c)]

        # source 컬럼 추가
        if "source" not in docsSec.columns:
            docsSec = docsSec.with_columns(pl.lit("docs").alias("source"))

        # finance topics 추가
        extraRows: list[dict[str, Any]] = []
        for ft in ("BS", "IS", "CF", "CIS"):
            df = getattr(self._company.finance, ft, None)
            if df is not None:
                extraRows.append(
                    {
                        "chapter": "Financial Statements",
                        "topic": ft,
                        "blockType": "table",
                        "blockOrder": 0,
                        "source": "finance",
                        **{p: None for p in periodCols},
                    }
                )
        if self._company.finance.ratioSeries is not None:
            extraRows.append(
                {
                    "chapter": "Financial Statements",
                    "topic": "ratios",
                    "blockType": "table",
                    "blockOrder": 0,
                    "source": "finance",
                    **{p: None for p in periodCols},
                }
            )

        if not extraRows:
            self._company._cache[cacheKey] = docsSec
            return docsSec

        extraDf = pl.DataFrame(
            extraRows,
            schema={
                "chapter": pl.Utf8,
                "topic": pl.Utf8,
                "blockType": pl.Utf8,
                "blockOrder": pl.Int64,
                "source": pl.Utf8,
                **{p: pl.Utf8 for p in periodCols},
            },
        )

        merged = pl.concat([docsSec, extraDf], how="diagonal_relaxed")
        self._company._cache[cacheKey] = merged
        return merged

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """source provenance — 해당 topic이 어디서 왔는지."""
        return self._company.trace(topic, period=period)
