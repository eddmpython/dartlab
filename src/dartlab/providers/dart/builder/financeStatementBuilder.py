"""DART Company finance 빌더 helpers. facade thin delegate.

panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 진입점이 위임하는 backing 함수.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from dartlab.core.memory import lookupCache
from dartlab.core.ratios import calcRatioSeries, toSeriesDict
from dartlab.providers.dart.checks import _isPeriodColumn
from dartlab.providers.dart.financeMappers import (
    _financeCisAnnual,
    _financeCisQuarterly,
    _financeToDataFrame,
    _ratioArchetypeOverrideForIndustryGroup,
    _ratioSeriesToDataFrame,
    _sceToDataFrame,
)

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company


import re

_QUARTER_COL_RE = re.compile(r"^(\d{4})Q[1-4]$")


# ── SCE ──────────────────────────────────────────────────────────


def sceMatrix(company: Company):
    """SCE 3 차원 매트릭스 — ``buildSceMatrix`` 위임 + 캐시.

    Args:
        company: Company 인스턴스.

    Returns:
        ``(matrix, years)`` 또는 None (finance 부재).

    Raises:
        없음.

    Example:
        >>> sceMatrix(c)

    SeeAlso:
        - ``Company.panel`` ("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") — public surface.
        - ``financeMappers`` — XBRL → snakeId 변환.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance topic (BS/IS/CF/CIS/SCE/ratios) 빌드 + 연간/분기 series-tuple.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal finance builder — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company.panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 위임.
            - finance 부재 → None.
        OutputSchema:
            - pl.DataFrame / tuple[dict, list[str]] — series-tuple.
        Prerequisites:
            - 본 회사 finance parquet.
        Freshness:
            - finance 갱신 시점 (분기 마감 후 45 일).
        Dataflow:
            - finance parquet → series-tuple → mapper → DataFrame.
        TargetMarkets:
            - KR (DART XBRL).
    """
    if not company._hasFinance:
        return None
    cacheKey = "_sceMatrix_CFS"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    from dartlab.providers.dart.finance.pivot import buildSceMatrix

    result = buildSceMatrix(company.stockCode)
    company._cache[cacheKey] = result
    return result


def sceSeriesAnnual(company: Company):
    """SCE 연간 시계열 — ``buildSceAnnual`` 위임 + 캐시.

    Args:
        company: Company 인스턴스.

    Returns:
        ``(series, years)`` 또는 None (finance 부재).

    Raises:
        없음.

    Example:
        >>> sceSeriesAnnual(c)

    SeeAlso:
        - ``Company.panel`` ("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") — public surface.
        - ``financeMappers`` — XBRL → snakeId 변환.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance topic (BS/IS/CF/CIS/SCE/ratios) 빌드 + 연간/분기 series-tuple.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal finance builder — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company.panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 위임.
            - finance 부재 → None.
        OutputSchema:
            - pl.DataFrame / tuple[dict, list[str]] — series-tuple.
        Prerequisites:
            - 본 회사 finance parquet.
        Freshness:
            - finance 갱신 시점 (분기 마감 후 45 일).
        Dataflow:
            - finance parquet → series-tuple → mapper → DataFrame.
        TargetMarkets:
            - KR (DART XBRL).
    """
    if not company._hasFinance:
        return None
    cacheKey = "_sceAnnual_CFS"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    from dartlab.providers.dart.finance.pivot import buildSceAnnual

    result = buildSceAnnual(company.stockCode)
    company._cache[cacheKey] = result
    return result


def sce(company: Company) -> pl.DataFrame | None:
    """SCE (자본변동표) DataFrame — meta 컬럼 + 연도 역순 정렬.

    Capabilities:
        - ``sceSeriesAnnual(company)`` 결과를 ``_sceToDataFrame`` 으로 wide 변환.
        - 4 자리 연도 컬럼만 역순 정렬, meta 컬럼은 앞쪽 보존.
        - IS/BS/CF 와 컬럼 정렬 일관성 (사용자 비교 편의).
        - cacheKey = ``"_sceDataFrame_CFS"``.

    Args:
        company: Company 인스턴스.

    Returns:
        pl.DataFrame | None — SCE wide DataFrame. finance 미수집 시 None.

    Example:
        >>> # df = sce(c)
        >>> # df.select(["항목", "2024", "2023"])

    Guide:
        - "삼성전자 자본 변동 (이익잉여금/자본금)" → ``c.panel("SCE")`` → 본 함수.
        - "BS 와 비교" → ``c.panel("BS")`` 후 동일 연도 col 선택.

    SeeAlso:
        - ``sceMatrix`` / ``sceSeriesAnnual`` — 본 함수의 raw input.
        - ``_sceToDataFrame`` (financeMappers) — 변환 단계.
        - ``Company.panel("SCE")`` — 사용자 entry.

    Requires:
        - polars — DataFrame.
        - dartlab.providers.dart.financeMappers._sceToDataFrame.

    AIContext:
        SCE 는 자본 항목 (자본금/이익잉여금/기타포괄손익) 추이 — IS 의 당기순이익과 BS 자본
        의 다리. AI 가 "이익잉여금 증가" 류 질문 처리 시 본 함수 결과 활용.

    LLM Specifications:
        AntiPatterns:
            - 일부 회사가 SCE 미작성 (소규모) → None.
            - cache 의 _CFS 만 (separate scope X) — 별도 SCE 는 미지원.
        OutputSchema:
            - wide DataFrame — meta + 연도 역순.
        Prerequisites:
            - finance parquet 의 SCE 항목 존재.
        Freshness:
            - finance 수집 시점 + cache.
        Dataflow:
            - finance → sceSeriesAnnual → 본 함수 → c.panel("SCE").
        TargetMarkets:
            - KR (DART) 한정. EDGAR 의 statement of equity 는 별도.

    Raises:
        없음.
    """
    cacheKey = "_sceDataFrame_CFS"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    result = sceSeriesAnnual(company)
    if result is None:
        company._cache[cacheKey] = None
        return None
    series, years = result
    df = _sceToDataFrame(series, years)
    if df is not None:
        # 컬럼 정렬: 메타 컬럼 + 연도 역순 (최신 → 과거) — IS/BS/CF 와 일관성
        metaCols = [c for c in df.columns if not (c.isdigit() and len(c) == 4)]
        yearCols = sorted([c for c in df.columns if c.isdigit() and len(c) == 4], reverse=True)
        df = df.select(metaCols + yearCols)
    company._cache[cacheKey] = df
    return df


# ── CIS ──────────────────────────────────────────────────────────


def financeCisAnnual(company: Company):
    """CIS 연간 series — ``_financeCisAnnual`` 위임 + 캐시.

    Args:
        company: Company 인스턴스.

    Returns:
        ``(series, years)`` 또는 None.

    Raises:
        없음.

    Example:
        >>> financeCisAnnual(c)

    SeeAlso:
        - ``Company.panel`` ("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") — public surface.
        - ``financeMappers`` — XBRL → snakeId 변환.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance topic (BS/IS/CF/CIS/SCE/ratios) 빌드 + 연간/분기 series-tuple.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal finance builder — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company.panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 위임.
            - finance 부재 → None.
        OutputSchema:
            - pl.DataFrame / tuple[dict, list[str]] — series-tuple.
        Prerequisites:
            - 본 회사 finance parquet.
        Freshness:
            - finance 갱신 시점 (분기 마감 후 45 일).
        Dataflow:
            - finance parquet → series-tuple → mapper → DataFrame.
        TargetMarkets:
            - KR (DART XBRL).
    """
    if not company._hasFinance:
        return None
    cacheKey = "_financeCISAnnual_CFS"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    result = _financeCisAnnual(company.stockCode, "CFS")
    company._cache[cacheKey] = result
    return result


def financeCisQuarterly(company: Company):
    """CIS 분기별 시계열 (연간 합산 없이).

    Args:
        company: Company 인스턴스.

    Returns:
        ``(series, periods)`` 또는 None.

    Raises:
        없음.

    Example:
        >>> financeCisQuarterly(c)

    SeeAlso:
        - ``Company.panel`` ("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") — public surface.
        - ``financeMappers`` — XBRL → snakeId 변환.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance topic (BS/IS/CF/CIS/SCE/ratios) 빌드 + 연간/분기 series-tuple.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal finance builder — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company.panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 위임.
            - finance 부재 → None.
        OutputSchema:
            - pl.DataFrame / tuple[dict, list[str]] — series-tuple.
        Prerequisites:
            - 본 회사 finance parquet.
        Freshness:
            - finance 갱신 시점 (분기 마감 후 45 일).
        Dataflow:
            - finance parquet → series-tuple → mapper → DataFrame.
        TargetMarkets:
            - KR (DART XBRL).
    """
    if not company._hasFinance:
        return None
    cacheKey = "_financeCISQuarterly_CFS"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    result = _financeCisQuarterly(company.stockCode, "CFS")
    company._cache[cacheKey] = result
    return result


def aggregateCisAnnual(qDf: pl.DataFrame) -> pl.DataFrame | None:
    """CIS 분기 DataFrame → 연간 (4 분기 합, strict).

    4 분기 모두 있는 연도만 합산. 일부 분기 부재 연도는 결과에서 제외.

    Args:
        qDf: CIS 분기 wide DataFrame.

    Returns:
        연간 wide DataFrame 또는 None (분기 컬럼 부재).

    Raises:
        없음.

    Example:
        >>> aggregateCisAnnual(cis_quarterly_df)

    SeeAlso:
        - ``Company.panel`` ("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") — public surface.
        - ``financeMappers`` — XBRL → snakeId 변환.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance topic (BS/IS/CF/CIS/SCE/ratios) 빌드 + 연간/분기 series-tuple.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal finance builder — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company.panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 위임.
            - finance 부재 → None.
        OutputSchema:
            - pl.DataFrame / tuple[dict, list[str]] — series-tuple.
        Prerequisites:
            - 본 회사 finance parquet.
        Freshness:
            - finance 갱신 시점 (분기 마감 후 45 일).
        Dataflow:
            - finance parquet → series-tuple → mapper → DataFrame.
        TargetMarkets:
            - KR (DART XBRL).
    """
    yearGroups: dict[str, list[str]] = {}
    for col in qDf.columns:
        m = _QUARTER_COL_RE.match(col)
        if m:
            yearGroups.setdefault(m.group(1), []).append(col)
    if not yearGroups:
        return None
    # 4분기 모두 있는 연도만 합산 (strict)
    years = sorted([y for y, qs in yearGroups.items() if len(qs) == 4], reverse=True)
    if not years:
        return None
    metaCols = [c for c in qDf.columns if not _QUARTER_COL_RE.match(c)]
    exprs = [pl.col(c) for c in metaCols]
    for year in years:
        qs = sorted(yearGroups[year])
        exprs.append(pl.sum_horizontal([pl.col(q) for q in qs]).alias(year))
    return qDf.select(exprs)


# ── Ratios ───────────────────────────────────────────────────────


def ratioSeries(company: Company):
    """비율 분기 series + 연간 fallback — ``calcRatioSeries`` 위임 + 캐시.

    industry group 별 archetype override 적용. ``yoyLag=4`` (분기 단위 YoY).

    Args:
        company: Company 인스턴스.

    Returns:
        ``(series, periods)`` 또는 None.

    Raises:
        없음.

    Example:
        >>> ratioSeries(c)

    SeeAlso:
        - ``Company.panel`` ("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") — public surface.
        - ``financeMappers`` — XBRL → snakeId 변환.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance topic (BS/IS/CF/CIS/SCE/ratios) 빌드 + 연간/분기 series-tuple.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal finance builder — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company.panel("BS"/"IS"/"CF"/"CIS"/"SCE"/"ratios") 위임.
            - finance 부재 → None.
        OutputSchema:
            - pl.DataFrame / tuple[dict, list[str]] — series-tuple.
        Prerequisites:
            - 본 회사 finance parquet.
        Freshness:
            - finance 갱신 시점 (분기 마감 후 45 일).
        Dataflow:
            - finance parquet → series-tuple → mapper → DataFrame.
        TargetMarkets:
            - KR (DART XBRL).
    """
    if not company._hasFinance:
        return None
    cacheKey = "_ratioSeries_Q_CFS"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    qResult = buildFinanceSeries(company, freq="Q")
    if qResult is None:
        return None
    qSeries, periods = qResult
    # 2016-Q1 → 2016Q1 포맷 통일
    normalizedPeriods = [p.replace("-", "") for p in periods]
    archetypeOverride = _ratioArchetypeOverrideForIndustryGroup(getattr(company.sector, "industryGroup", None))
    rs = calcRatioSeries(qSeries, normalizedPeriods, annual=False, archetypeOverride=archetypeOverride, yoyLag=4)
    result = toSeriesDict(rs)
    company._cache[cacheKey] = result
    return result


def buildRatios(company: Company) -> pl.DataFrame | None:
    """[INTERNAL] 재무비율 DataFrame 빌더 — period 컬럼 역순 정렬 wide format.

    Capabilities:
        - ``ratioSeries(company)`` 결과를 받아 ``_ratioSeriesToDataFrame`` 으로 wide 변환.
        - period 컬럼 (예 "2024Q1") 만 정렬 — meta 컬럼은 앞쪽 보존.
        - 정렬 키 = (year:int, quarter:int) 내림차순.
        - ratioSeries None → 본 함수 None.

    Args:
        company: Company 인스턴스.

    Returns:
        pl.DataFrame | None — 비율 wide DataFrame. 컬럼 = meta + period N (역순). None 시 finance/
        ratios 미수집.

    Example:
        >>> # buildRatios(c)  # 내부 — 사용자는 c.panel("ratios")

    Guide:
        - "사용자는 ``c.panel('ratios')`` 호출" — 본 함수는 dispatch 내부.
        - "분기별 ROE 추세" → c.panel("ratios").filter(pl.col("항목")=="ROE").
        - "industryGroup override" → ``ratioSeries`` 에서 자동 적용 (본 함수 무관).

    SeeAlso:
        - ``ratioSeries`` — 본 함수의 (series, periods) source.
        - ``_ratioSeriesToDataFrame`` (financeMappers) — 본 함수 변환 단계.
        - ``Company.panel("ratios")`` — 사용자 entry.

    Requires:
        - polars — DataFrame.
        - dartlab.providers.dart.financeMappers — _ratioSeriesToDataFrame.
        - dartlab.providers.dart.checks — _isPeriodColumn.

    AIContext:
        AI 가 "삼성전자 ROE 추세" 류 질문 받으면 c.panel("ratios") 호출 → 본 함수 dispatch.
        결과 DataFrame 에서 항목 row + period 컬럼 lookup → 자연어 답변.

    LLM Specifications:
        AntiPatterns:
            - ratioSeries 가 finance 미수집 → 본 함수 None.
            - period 컬럼 형식 가정 (year + quarter) — 다른 형식 (예 월별) 은 _isPeriodColumn 미매칭.
        OutputSchema:
            - wide DataFrame — meta + period (역순).
        Prerequisites:
            - finance parquet + ratios 계산 가능 (Series 충분).
        Freshness:
            - ratioSeries / finance 의존.
        Dataflow:
            - finance → buildFinanceSeries → ratioSeries → 본 함수 → c.panel("ratios").
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    rs = ratioSeries(company)
    if rs is None:
        return None
    series, periods = rs
    df = _ratioSeriesToDataFrame(series, periods)
    if df is not None:
        metaCols = [c for c in df.columns if not _isPeriodColumn(c)]
        periodCols = [c for c in df.columns if _isPeriodColumn(c)]
        periodCols.sort(key=lambda p: (int(p[:4]), int(p[-1])), reverse=True)
        df = df.select(metaCols + periodCols)
    return df


# ── Statement (BS/IS/CF/CIS) build/dispatch ──────────────────────


def financeStmt(company: Company, sjDiv: str, *, freq: str = "Q", scope: str = "consolidated") -> pl.DataFrame | None:
    """finance 시계열에서 ``sjDiv`` DataFrame 빌드 — Q/Y/YTD × CFS/OFS 조합 (캐싱).

    Capabilities:
        - ``buildFinanceSeries(freq, scope)`` 호출 → (series, periods) 튜플 받아 wide DataFrame 변환.
        - period 포맷 정규화 ("2016-Q1" → "2016Q1").
        - cacheKey = ``"_financeStmt_{sjDiv}_{freq}_{scope}"``.
        - 5 sjDiv 지원: BS (재무상태) / IS (손익) / CF (현금흐름) / CIS (포괄손익) / SCE (자본변동).

    Args:
        company: Company 인스턴스.
        sjDiv: ``"BS"``/``"IS"``/``"CF"``/``"CIS"``/``"SCE"``.
        freq: ``"Q"`` (분기) / ``"Y"`` (연간) / ``"YTD"`` (누적). 기본 ``"Q"``.
        scope: ``"consolidated"`` (CFS) / ``"separate"`` (OFS). 기본 ``"consolidated"``.

    Returns:
        pl.DataFrame | None — wide format ("항목" + period 컬럼 N 개). finance 미수집 또는
        series 빈 결과 → None.

    Example:
        >>> # df = financeStmt(c, "IS", freq="Y")
        >>> # df.select(["항목", "2024", "2023"])

    Guide:
        - "삼성전자 IS 연간" → ``c.panel("IS", freq="Y")`` → ``financeStmt(c, "IS", freq="Y")``.
        - "별도 BS 분기" → ``c.panel("BS", scope="separate")``.
        - docs fallback 까지 → ``financeOrDocsStatement``.

    SeeAlso:
        - ``financeOrDocsStatement`` — 본 함수 None 시 docs fallback 까지 시도.
        - ``buildFinanceSeries`` — 본 함수의 (series, periods) source.
        - ``Company.panel("IS", freq=, scope=)`` — 사용자 entry.
        - ``dartlab.providers.dart.financeMappers._financeToDataFrame`` — 변환 단계.

    Requires:
        - polars — DataFrame.
        - dartlab.providers.dart.financeMappers — _financeToDataFrame.

    AIContext:
        Workbench 재무 토픽 가장 빈번한 backend. AI 가 c.panel("IS") 호출 → 본 함수 → DataFrame.
        None 반환 = finance parquet 미수집 → caller 는 docs fallback (``financeOrDocsStatement``)
        또는 미수집 안내.

    LLM Specifications:
        AntiPatterns:
            - sjDiv 가 5 종 외 (예 "PNL") → ``_financeToDataFrame`` 내부에서 빈 결과 또는 KeyError.
            - cache hit → series rebuild 안 됨 (freshness 가 cache TTL 의존).
            - freq="YTD" 인데 데이터 부재 → None.
        OutputSchema:
            - wide DataFrame — "항목" + 연도/분기 컬럼.
            - 정렬: caller (``buildFinanceSeries``) 의 periods 순.
        Prerequisites:
            - finance parquet 가 stockCode 에 수집됨 (``_hasFinance=True``).
        Freshness:
            - finance 수집 시점 + cache TTL.
        Dataflow:
            - finance parquet → buildFinanceSeries → 본 함수 → AI 답변.
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    cacheKey = f"_financeStmt_{sjDiv}_{freq}_{scope}"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached
    qResult = buildFinanceSeries(company, freq=freq, scope=scope)
    if qResult is None:
        return None
    series, periods = qResult
    # 2016-Q1 → 2016Q1 포맷 통일
    normalizedPeriods = [str(p).replace("-", "") for p in periods]
    df = _financeToDataFrame(series, normalizedPeriods, sjDiv)
    company._cache[cacheKey] = df
    return df


def financeOrDocsStatement(
    company: Company, sjDiv: str, *, freq: str = "Q", scope: str = "consolidated"
) -> pl.DataFrame | None:
    """finance 우선 + docs fallback dispatch — finance 미수집 회사도 docs 로 폴백.

    Capabilities:
        - CIS + consolidated → ``financeCisQuarterly`` 우선 (별도 캐시 경로). ``freq="Y"``
          이면 ``aggregateCisAnnual`` 적용 (4 분기 합).
        - 그 외 → ``financeStmt(sjDiv, freq, scope)`` 우선 시도.
        - 위 모두 None + ``freq="Q"`` + ``scope="consolidated"`` → docs fallback
          (``company._callModule("statements")``) 에서 sjDiv 추출.
        - docs fallback 은 분기 연결만 (다른 조합은 None).

    Args:
        company: Company 인스턴스.
        sjDiv: ``"BS"``/``"IS"``/``"CF"``/``"CIS"``/``"SCE"``.
        freq: ``"Q"``/``"Y"``/``"YTD"``.
        scope: ``"consolidated"``/``"separate"``.

    Returns:
        pl.DataFrame | None — wide DataFrame. 모든 경로 실패 시 None.

    Example:
        >>> # df = financeOrDocsStatement(c, "BS")  # finance 없으면 docs.statements

    Guide:
        - "finance / docs 어느 쪽이든" → 본 함수.
        - "finance only" → ``financeStmt``.
        - "docs only" → ``c.panel("statements")`` (Plan v10 단일 진입).

    SeeAlso:
        - ``financeStmt`` — 본 함수의 1 차 시도.
        - ``financeCisQuarterly`` / ``aggregateCisAnnual`` — CIS 경로.
        - ``Company._callModule("statements")`` — docs fallback source.
        - ``Company.panel("IS")`` — 사용자 entry.

    Requires:
        - polars — DataFrame.
        - 다른 builder/docs 모듈에 의존 (lazy import).

    AIContext:
        finance parquet 미수집 회사 (예 비상장/이상한 형태) 도 docs 로 대답 가능하게 하는
        safety net. AI 가 cross-company 비교 시 결과 비균질 (어떤 회사는 finance, 어떤 회사는
        docs) 가능 — caller 는 데이터 출처 명시 권장.

    LLM Specifications:
        AntiPatterns:
            - sjDiv 가 5 종 외 → 모든 경로 None.
            - docs fallback 의 분기 연결 한정 → docs.statements 결과의 sjDiv attr 가 None 일 수 있음.
            - CIS+consolidated 경로의 aggregateCisAnnual 은 4 분기 모두 있는 연도만 (strict).
        OutputSchema:
            - financeStmt 와 동일 (wide DataFrame).
        Prerequisites:
            - finance parquet 또는 docs.statements 중 하나 이상 존재.
        Freshness:
            - 각 backend 의 freshness 의존.
        Dataflow:
            - financeStmt → 본 함수 → docs.statements (fallback).
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    # CIS 는 별도 quarterly 캐시 — annual 은 4분기 합산 합성
    if sjDiv == "CIS" and scope == "consolidated":
        cisQ = financeCisQuarterly(company) if company._hasFinance else None
        if cisQ is not None:
            series, periods = cisQ
            normalizedPeriods = [p.replace("-", "") for p in periods]
            df = _financeToDataFrame(series, normalizedPeriods, "CIS")
            if df is not None and freq == "Y":
                df = aggregateCisAnnual(df)
            if df is not None:
                return df
    df = financeStmt(company, sjDiv, freq=freq, scope=scope) if company._hasFinance else None
    if df is not None:
        return df
    # docs fallback 은 분기 연결만 지원
    if freq == "Q" and scope == "consolidated":
        r = company._callModule("statements")
        return getattr(r, sjDiv, None) if r else None
    return None


def buildFinanceSeries(company: Company, *, freq: str = "Q", scope: str = "consolidated"):
    """[INTERNAL] finance series-tuple 빌더 — analysis/forecast/credit/story 의 raw input.

    Capabilities:
        - ``company._getFinanceBuild(periodKey, scopeKey)`` 위임 (Company facade).
        - freq → periodKey 매핑: Q→q / Y→y / YTD→cum.
        - scope → scopeKey: consolidated→CFS / separate→OFS.
        - 시그니처 검증 — freq/scope 허용 값 외 → ValueError.
        - ``_hasFinance=False`` → None (silent).
        - 사용자 직접 호출 X (api-contract). c.panel / c.select / analysis 모듈만 사용.

    Args:
        company: Company 인스턴스.
        freq: ``"Q"`` (분기, 기본) / ``"Y"`` (연간) / ``"YTD"`` (누적).
        scope: ``"consolidated"`` (CFS, 기본) / ``"separate"`` (OFS).

    Returns:
        tuple[dict, list[str]] | None — ``(series, periods)``. series 는 항목명 → 값 매핑 dict,
        periods 는 정렬된 period list.

    Raises:
        ValueError: freq 가 ``"Q"``/``"Y"``/``"YTD"`` 외, 또는 scope 가 ``"consolidated"``/
            ``"separate"`` 외.

    Example:
        >>> # series, periods = buildFinanceSeries(c, freq="Y", scope="separate")
        >>> # periods  # ["2024", "2023", ...]

    Guide:
        - "사용자는 직접 호출 X" — c.panel / c.select / analysis 모듈만.
        - "DataFrame 형태 필요" → ``financeStmt`` 또는 ``c.panel``.
        - "ratios 계산 input" → 본 함수 → ``calcRatioSeries``.

    SeeAlso:
        - ``financeStmt`` — 본 함수 결과를 DataFrame 으로 변환.
        - ``ratioSeries`` — 본 함수 결과를 비율 계산에 사용.
        - ``Company._getFinanceBuild`` — 본 함수 본체 (facade).
        - operation.apiContract — 사용자 entry 규약 SSOT.

    Requires:
        - polars (간접) — periods/series 의 source 가 finance parquet.
        - dartlab.providers.dart.company.Company — _getFinanceBuild 메서드.

    AIContext:
        AI 가 직접 호출 X. analysis / forecast / credit / story 등 calc 엔진이 series 형태
        필요할 때 사용. caller 는 본 함수 None 결과를 "finance 미수집" 으로 처리.

    LLM Specifications:
        AntiPatterns:
            - freq/scope 형식 오류 → ValueError (raise). caller 는 try/except 없으면 panic.
            - cache 미적용 — 매번 _getFinanceBuild 호출. caller 가 caching 책임.
        OutputSchema:
            - (series: dict[str, dict|list], periods: list[str]).
        Prerequisites:
            - _hasFinance=True.
        Freshness:
            - finance parquet 수집 시점.
        Dataflow:
            - finance parquet → _getFinanceBuild → 본 함수 → calc 엔진.
        TargetMarkets:
            - KR (DART) 한정.
    """
    if freq not in ("Q", "Y", "YTD"):
        raise ValueError(f"freq 는 'Q' / 'Y' / 'YTD' 중 하나여야 합니다 (받음: {freq!r})")
    if scope not in ("consolidated", "separate"):
        raise ValueError(f"scope 는 'consolidated' / 'separate' 중 하나여야 합니다 (받음: {scope!r})")
    if not company._hasFinance:
        return None
    _periodMap = {"Q": "q", "Y": "y", "YTD": "cum"}
    _scopeMap = {"consolidated": "CFS", "separate": "OFS"}
    return company._getFinanceBuild(_periodMap[freq], _scopeMap[scope])
