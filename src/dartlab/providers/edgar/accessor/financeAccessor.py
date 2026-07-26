"""EDGAR finance namespace — XBRL 정규화 재무 데이터."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.core.logger import getLogger
from dartlab.core.memory import _CACHE_MISSING
from dartlab.core.ratios import calcRatios, calcRatioSeries, toSeriesDict

_log = getLogger(__name__)

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


class _FinanceAccessor:
    """EDGAR finance namespace. XBRL 정규화 재무 데이터."""

    def __init__(self, company: Company):
        self._company = company

    def _stmtDf(self, stmtKey: str, *, freq: str = "Q") -> pl.DataFrame | None:
        """재무제표 DataFrame. ``freq="Q"`` (분기, 기본) 또는 ``"Y"`` (연간).

        Args:
            stmtKey: BS/IS/CF/CI 중 하나.
            freq: ``"Q"``/``"Y"``.

        Returns:
            ``snakeId/항목/period...`` 컬럼 wide DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance._stmtDf("BS")
        """
        cacheKey = f"_finance_{stmtKey}_{freq}"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        if sys.platform == "emscripten":
            result = self._stmtDfFromPublishedArtifact(stmtKey, freq=freq)
            if result is not None:
                self._company._cache[cacheKey] = result
                return result

        result = self._company._buildFinanceSeries(freq=freq)
        if result is None:
            self._company._cache[cacheKey] = None
            return None

        series, years = result
        stmtData = series.get(stmtKey)
        if not stmtData:
            self._company._cache[cacheKey] = None
            return None

        from dartlab.core.utils.labels import getKoreanLabels
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        krLabels = getKoreanLabels()
        lineOrder = EdgarMapper.getLineOrder()  # snakeId → line 번호

        # standardAccounts line 순서로 정렬 (매핑 없으면 맨 뒤)
        sortedItems = sorted(stmtData.items(), key=lambda kv: lineOrder.get(kv[0], 9999))
        rows = []
        for snakeId, values in sortedItems:
            label = krLabels.get(snakeId, snakeId)  # 한국어 매핑 없으면 snakeId 그대로
            # 컬럼명 표준: "항목" (sections 사상)
            row: dict[str, Any] = {
                "snakeId": snakeId,
                "항목": label,
            }
            for i, year in enumerate(years):
                row[str(year)] = values[i] if i < len(values) else None
            rows.append(row)

        if not rows:
            self._company._cache[cacheKey] = None
            return None

        result = pl.DataFrame(rows)
        # 기간 컬럼: "2025-Q4" → "2025Q4" (DART 형식 통일) + 역순 정렬
        periodCols = [c for c in result.columns if c not in ("snakeId", "항목")]
        renameMap = {c: c.replace("-", "") for c in periodCols if "-" in c}
        if renameMap:
            result = result.rename(renameMap)
            periodCols = [renameMap.get(c, c) for c in periodCols]
        # 전부 null인 빈 컬럼 제거
        nonEmpty = [c for c in periodCols if result[c].null_count() < result.height]
        result = result.select(["snakeId", "항목"] + nonEmpty[::-1])
        self._company._cache[cacheKey] = result
        return result

    def _stmtDfFromPublishedArtifact(self, stmtKey: str, *, freq: str = "Q") -> pl.DataFrame | None:
        """Pyodide 브라우저용 공개 ``edgarFinanceStmt`` artifact 를 wide panel 로 변환."""
        try:
            from dartlab.core.dataLoader import loadData

            df = loadData(self._company.ticker, category="edgarFinanceStmt")
        except Exception as exc:  # noqa: BLE001
            _log.warning("발행 재무 artifact 로드 실패로 None 반환: %s: %s", type(exc).__name__, exc)
            return None
        if df is None or df.is_empty() or "sj_div" not in df.columns:
            return None

        valueCol = "thstrm_amount" if "thstrm_amount" in df.columns else None
        if valueCol is None:
            return None

        stmt = df.filter(pl.col("sj_div") == stmtKey)
        if stmt.is_empty():
            return None

        freqKey = str(freq or "Q").upper()
        if freqKey == "Y":
            stmt = stmt.filter(pl.col("reprt_code") == "11011").with_columns(pl.col("bsns_year").alias("period"))
        else:
            quarterMap = {"11013": "Q1", "11012": "Q2", "11014": "Q3", "11011": "Q4"}
            stmt = (
                stmt.filter(pl.col("reprt_code").is_in(list(quarterMap)))
                .with_columns(pl.col("reprt_code").replace(quarterMap).alias("__quarter"))
                .with_columns((pl.col("bsns_year") + pl.col("__quarter")).alias("period"))
            )
        if stmt.is_empty():
            return None

        stmt = stmt.with_columns(
            pl.when(pl.col("account_id").is_not_null() & (pl.col("account_id").cast(pl.Utf8).str.len_chars() > 0))
            .then(pl.col("account_id").cast(pl.Utf8))
            .otherwise(pl.col("account_nm").cast(pl.Utf8))
            .alias("snakeId"),
            pl.col("account_nm").cast(pl.Utf8).alias("항목"),
        )
        order = stmt.group_by(["snakeId", "항목"]).agg(pl.col("ord").min().alias("__ord"))
        wide = stmt.select(["snakeId", "항목", "period", valueCol]).pivot(
            on="period",
            index=["snakeId", "항목"],
            values=valueCol,
            aggregate_function="first",
        )
        if wide.is_empty():
            return None

        wide = order.join(wide, on=["snakeId", "항목"], how="right").sort("__ord").drop("__ord")
        periodCols = sorted([c for c in wide.columns if c not in ("snakeId", "항목")], reverse=True)
        if not periodCols:
            return None
        return wide.select(["snakeId", "항목"] + periodCols)

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표 (Balance Sheet) — XBRL companyfacts 기반.

        Returns:
            wide DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.BS  # 내부 — 사용자는 c.panel("BS")

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        return self._stmtDf("BS")

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서 (Income Statement) — XBRL companyfacts 기반.

        Returns:
            wide DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.IS  # 내부 — 사용자는 c.panel("IS")

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        return self._stmtDf("IS")

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표 (Cash Flow) — XBRL companyfacts 기반.

        Returns:
            wide DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.CF  # 내부 — 사용자는 c.panel("CF")

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        return self._stmtDf("CF")

    @property
    def CIS(self) -> pl.DataFrame | None:
        """포괄손익계산서 (Comprehensive IS) — IS + OCI.

        Returns:
            wide DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.CIS  # 내부 — 사용자는 c.panel("CIS")

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        return self._stmtDf("CI")

    @property
    def ratios(self):
        """재무비율 snapshot — 연간 base.

        Returns:
            ``RatioResult`` dataclass 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.ratios  # 내부 — 사용자는 c.panel("ratios")

        SeeAlso:
            - ``_stmtDf`` — 본 property 의 backend.
            - ``Company.panel("ratios")`` / ``Company.panel("BS"/"IS"/"CF"/"CIS")`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 4 재무제표 (BS/IS/CF/CIS) + ratios 의 _FinanceAccessor namespace. XBRL companyfacts 정규화
              결과를 snakeId × period wide DataFrame 으로 노출. cache 통합.

        Guide:
            - 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X.
        """
        val = self._company._cache.get("_ratios", _CACHE_MISSING)
        if val is _CACHE_MISSING:
            annual = self._company._buildFinanceSeries(freq="Y")
            if annual is None:
                val = None
            else:
                aSeries, _ = annual
                val = calcRatios(aSeries, annual=True)
            self._company._cache["_ratios"] = val
        return val

    @property
    def ratioSeries(self):
        """재무비율 시계열 — 연간 series.

        Returns:
            ``{ratio: [년도별 값...], ...}`` dict 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.ratioSeries  # 내부 — 사용자는 c.panel("ratioSeries")

        SeeAlso:
            - ``_stmtDf`` — 본 property 의 backend.
            - ``Company.panel("ratios")`` / ``Company.panel("BS"/"IS"/"CF"/"CIS")`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 4 재무제표 (BS/IS/CF/CIS) + ratios 의 _FinanceAccessor namespace. XBRL companyfacts 정규화
              결과를 snakeId × period wide DataFrame 으로 노출. cache 통합.

        Guide:
            - 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X.
        """
        cacheKey = "_ratioSeries"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]
        annual = self._company._buildFinanceSeries(freq="Y")
        if annual is None:
            return None
        aSeries, years = annual
        rs = calcRatioSeries(aSeries, years)
        result = toSeriesDict(rs)
        self._company._cache[cacheKey] = result
        return result

    @property
    def SCE(self) -> pl.DataFrame | None:
        """자본변동표 (Statement of Changes in Equity).

        Returns:
            wide DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.SCE  # 내부 — 사용자는 c.panel("SCE")

        SeeAlso:
            - ``_stmtDf`` — 본 property 의 backend.
            - ``Company.panel("ratios")`` / ``Company.panel("BS"/"IS"/"CF"/"CIS")`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 4 재무제표 (BS/IS/CF/CIS) + ratios 의 _FinanceAccessor namespace. XBRL companyfacts 정규화
              결과를 snakeId × period wide DataFrame 으로 노출. cache 통합.

        Guide:
            - 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        cacheKey = "_finance_SCE"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]
        from dartlab.providers.edgar.finance.pivot import buildSce

        result = buildSce(self._company.cik)
        self._company._cache[cacheKey] = result
        return result

    def explore(self, query: str) -> pl.DataFrame | None:
        """XBRL 태그 검색 — 전 기간 값 탐색.

        Args:
            query: 태그 패턴 (정규식 또는 substring).

        Returns:
            매칭 행 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.explore("Revenue")

        SeeAlso:
            - ``_stmtDf`` — 본 property 의 backend.
            - ``Company.panel("ratios")`` / ``Company.panel("BS"/"IS"/"CF"/"CIS")`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 4 재무제표 (BS/IS/CF/CIS) + ratios 의 _FinanceAccessor namespace. XBRL companyfacts 정규화
              결과를 snakeId × period wide DataFrame 으로 노출. cache 통합.

        Guide:
            - 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        from dartlab.providers.edgar.finance.explore import explore

        return explore(self._company.cik, query)

    def listTags(self, *, limit: int | None = None) -> pl.DataFrame | None:
        """보고된 모든 us-gaap 태그 목록.

        Args:
            limit: 최대 행 수. None 이면 무제한.

        Returns:
            태그 목록 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._finance.listTags(limit=50)

        SeeAlso:
            - ``_stmtDf`` — 본 property 의 backend.
            - ``Company.panel("ratios")`` / ``Company.panel("BS"/"IS"/"CF"/"CIS")`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 4 재무제표 (BS/IS/CF/CIS) + ratios 의 _FinanceAccessor namespace. XBRL companyfacts 정규화
              결과를 snakeId × period wide DataFrame 으로 노출. cache 통합.

        Guide:
            - 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        from dartlab.providers.edgar.finance.explore import listTags

        return listTags(self._company.cik, limit=limit)

    def iterTags(self, *, limit: int | None = None):
        """``listTags`` 의 iterator pair (룰 10).

        Args:
            limit: 최대 행 수. None 이면 무제한.

        Yields:
            태그 row dict.

        Raises:
            없음.

        Example:
            >>> for row in c._finance.iterTags(limit=20):
            ...     print(row["tag"], row["count"])

        SeeAlso:
            - ``_stmtDf`` — 본 property 의 backend.
            - ``Company.panel("ratios")`` / ``Company.panel("BS"/"IS"/"CF"/"CIS")`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 4 재무제표 (BS/IS/CF/CIS) + ratios 의 _FinanceAccessor namespace. XBRL companyfacts 정규화
              결과를 snakeId × period wide DataFrame 으로 노출. cache 통합.

        Guide:
            - 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - finance 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("BS"/"IS"/"CF"/"CIS"/"ratios")``.
            OutputSchema:
                - pl.DataFrame [snakeId, 항목, period...] 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet 보유.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → buildFinanceSeries → EdgarMapper → snakeId/한국어 라벨화 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL) 한정.
        """
        df = self.listTags(limit=limit)
        if df is None:
            return
        yield from df.iter_rows(named=True)
