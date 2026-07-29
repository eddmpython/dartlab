"""EDGAR profile namespace — docs spine + finance merge layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.core.memory import lookupCache

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


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
        """sections — docs + finance 통합 지도.

        Returns:
            ``chapter/topic/blockType/blockOrder/source/{period...}`` 컬럼 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._profileAccessor.sections

        SeeAlso:
            - ``Company.panel`` — public surface.
            - ``_DocsAccessor.sections`` — docs spine origin.

        Requires:
            - polars

        Capabilities:
            - docs.sections (spine) + finance topics (BS/IS/CF/CIS) merge — chapter × topic × source ×
              period 통합 보드. ratios 별도 column 통합.

        Guide:
            - 사용자 API 는 ``c.panel(...)`` / ``c.topics`` — 본 namespace 직접 호출 X.

        AIContext:
            internal merge accessor — AI 가 직접 호출 X. Company facade 가 본 함수 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 → None. caller None 분기 의무.
                - merge 결과의 source 컬럼 무시 X — docs vs finance origin 명시.
            OutputSchema:
                - pl.DataFrame [chapter, topic, blockType, blockOrder, source, period...] 또는 None.
            Prerequisites:
                - docs.sections + finance 시리즈.
            Freshness:
                - docs + finance 의 latest min.
            Dataflow:
                - docs.sections + finance topics → merge → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        cacheKey = "_sections"
        cacheHit, cached = lookupCache(self._company._cache, cacheKey)
        if cacheHit:
            return cached

        docsSec = self._company._docs.sections
        if docsSec is None or (isinstance(docsSec, pl.DataFrame) and docsSec.is_empty()):
            self._company._cache[cacheKey] = None
            return None

        periodCols = [c for c in docsSec.columns if _isPeriodColumn(c)]

        # source 컬럼 추가
        if "source" not in docsSec.columns:
            docsSec = docsSec.with_columns(pl.lit("docs").alias("source"))

        # finance topics 추가
        extraRows: list[dict[str, Any]] = []
        for ft in ("BS", "IS", "CF", "CIS"):
            df = getattr(self._company._finance, ft, None)
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
        if self._company._finance.ratioSeries is not None:
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

    @property
    def sharesOutstanding(self) -> int | None:
        """최신 발행주식수 (SEC DEI).

        Returns:
            발행주식수 int 또는 None.

        Raises:
            없음.

        Example:
            >>> c._profileAccessor.sharesOutstanding

        SeeAlso:
            - ``Company.panel`` — public surface.
            - ``_DocsAccessor.sections`` — docs spine origin.

        Requires:
            - polars

        Capabilities:
            - docs.sections (spine) + finance topics (BS/IS/CF/CIS) merge — chapter × topic × source ×
              period 통합 보드. ratios 별도 column 통합.

        Guide:
            - 사용자 API 는 ``c.panel(...)`` / ``c.topics`` — 본 namespace 직접 호출 X.

        AIContext:
            internal merge accessor — AI 가 직접 호출 X. Company facade 가 본 함수 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 → None. caller None 분기 의무.
                - merge 결과의 source 컬럼 무시 X — docs vs finance origin 명시.
            OutputSchema:
                - pl.DataFrame [chapter, topic, blockType, blockOrder, source, period...] 또는 None.
            Prerequisites:
                - docs.sections + finance 시리즈.
            Freshness:
                - docs + finance 의 latest min.
            Dataflow:
                - docs.sections + finance topics → merge → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        cacheKey = "_sharesOutstanding"
        cacheHit, cached = lookupCache(self._company._cache, cacheKey)
        if cacheHit:
            return cached

        from dartlab.providers.edgar.finance.pivot import getSharesOutstanding

        val = getSharesOutstanding(self._company.cik)
        self._company._cache[cacheKey] = val
        return val

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """source provenance — 해당 topic 이 어디서 왔는지.

        Args:
            topic: topic 이름.
            period: 단일 period (선택).

        Returns:
            ``{source, topic, period, ...}`` provenance dict 또는 None.

        Raises:
            없음.

        Example:
            >>> c._profileAccessor.trace("IS")

        LLM Specifications:
            AntiPatterns:
                - 결과 dict source 무시 X — docs/finance origin 명시 의무.
                - profile.trace 는 Company.trace 의 단순 위임 — 추가 가공 없음.
            OutputSchema:
                - dict {topic, source, period?, ...} 또는 None.
            Prerequisites:
                - Company.trace 가용.
            Freshness:
                - Company.trace 와 동일.
            Dataflow:
                - 본 namespace → Company.trace(topic, period).
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        return self._company.trace(topic, period=period)
