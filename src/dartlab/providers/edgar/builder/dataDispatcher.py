"""EDGAR Company 의 show dispatch + finance/ratio builders + period helpers.

Company facade 의 show 본체와 finance 빌더, period filter, preview helper 를
같이 옮긴다. Company facade 는 thin delegate.

Module-level functions:
    showImpl              — c.panel(topic, ...) 사용자 진입점 본체
    buildFinanceSeries    — finance series-tuple 빌더 (Q/Y/YTD)
    buildRatios           — 재무비율 DataFrame
    applyPeriodFilter     — period 필터 (Q4 fallback 포함)
    transposeToVertical   — wide → long (period 리스트)
    buildBlockIndex       — topic blockOrder 목차
    shapeStr / periodsStr / previewFinance / previewDocsCell — preview helpers
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.core.memory import lookupCache
from dartlab.core.polarsUtil import isEmptyDf

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company

import re

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _isPeriodColumn(col: str) -> bool:
    return bool(_PERIOD_COLUMN_RE.fullmatch(col))


# ── finance builders ───────────────────────────────────────────────


def buildFinanceSeries(company: Company, *, freq: str = "Q", scope: str = "consolidated"):
    """[INTERNAL] EDGAR finance series-tuple 빌더.

    사용자 진입점은 ``c.panel("IS", freq=, scope=)`` 만이다 (api-contract).
    EDGAR 는 ``scope="separate"`` 미지원 (SEC 는 연결만 보고).
    ``freq="YTD"`` 도 미지원 — annual 로 fallback.

    Args:
        company: EDGAR Company 인스턴스.
        freq: ``"Q"`` (분기, 기본) / ``"Y"`` (연간) / ``"YTD"`` (annual fallback).
        scope: ``"consolidated"`` (기본) — separate 는 raise.

    Returns:
        ``(series, periods)`` tuple 또는 None.

    Raises:
        ValueError: 미지원 freq/scope.

    Example:
        >>> buildFinanceSeries(c, freq="Q")

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    if freq not in ("Q", "Y", "YTD"):
        raise ValueError(f"freq 는 'Q' / 'Y' / 'YTD' 중 하나 (받음: {freq!r})")
    if scope == "separate":
        raise ValueError("EDGAR 는 scope='separate' 미지원 — SEC 는 연결만 보고")
    if scope != "consolidated":
        raise ValueError(f"scope 는 'consolidated' / 'separate' 중 하나 (받음: {scope!r})")
    # EDGAR _FinanceAccessor 는 freq 옵션 직접 지원.
    # atomic lazy build (cache.get + 로컬 var) — set 직후 EMERGENCY clear 가 evict 해도
    # 로컬 var 는 영향 없음. R9 audit 의 race window fix.
    if freq == "Q":
        cacheHit, val = lookupCache(company._cache, "_ts")
        if not cacheHit:
            from dartlab.providers.edgar.finance.pivot import buildTimeseries

            val = buildTimeseries(company.cik)
            company._cache["_ts"] = val
        return val
    # Y / YTD → annual
    cacheHit, val = lookupCache(company._cache, "_annual")
    if not cacheHit:
        from dartlab.providers.edgar.finance.pivot import buildAnnual

        val = buildAnnual(company.cik)
        company._cache["_annual"] = val
    return val


def buildRatios(company: Company) -> pl.DataFrame | None:
    """[INTERNAL] EDGAR 재무비율 DataFrame 빌더 — show("ratios") 가 호출.

    Args:
        company: EDGAR Company 인스턴스.

    Returns:
        분류/항목/연도 컬럼 wide DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> buildRatios(c)

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    from dartlab.providers.edgar.company import _ratioSeriesToDataFrame

    rs = company._finance.ratioSeries
    if rs is None:
        return None
    series, years = rs
    df = _ratioSeriesToDataFrame(series, years)
    if df is not None:
        metaCols = [c for c in df.columns if not _isPeriodColumn(c)]
        periodCols = [c for c in df.columns if _isPeriodColumn(c)]
        periodCols.sort(reverse=True)
        df = df.select(metaCols + periodCols)
    return df


# ── period filter / transpose / block index ────────────────────────


def applyPeriodFilter(payload: Any, period: str | None) -> Any:
    """period 단일 지정 시 해당 period 컬럼만 select (Q4 fallback 포함).

    Args:
        payload: 원본 DataFrame.
        period: 단일 period (예: ``"2024"``, ``"2024Q3"``). None 이면 noop.

    Returns:
        period 단일 컬럼만 남은 DataFrame, 또는 원본 그대로.

    Raises:
        없음.

    Example:
        >>> applyPeriodFilter(df, "2024")

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
        return payload
    requestedPeriod = str(period)
    q4Fallback = f"{requestedPeriod}Q4" if "Q" not in requestedPeriod else None
    exactPeriod = (
        requestedPeriod
        if requestedPeriod in payload.columns
        else (q4Fallback if q4Fallback and q4Fallback in payload.columns else None)
    )
    if exactPeriod is not None:
        keepCols = [c for c in payload.columns if not _isPeriodColumn(c)]
        keepCols.append(exactPeriod)
        result = payload.select(keepCols)
        if exactPeriod != requestedPeriod:
            result = result.rename({exactPeriod: requestedPeriod})
        return result
    return payload


def transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
    """wide 보드를 vertical (period × 항목) 으로 transpose.

    Args:
        wide: 원본 wide DataFrame.
        periods: 추출 대상 period 리스트.

    Returns:
        vertical DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> transposeToVertical(df, ["2024", "2023"])

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    from dartlab.providers._common.show import transposeToVertical as _coreTranspose

    return _coreTranspose(wide, periods)


def buildBlockIndex(topicRows: pl.DataFrame) -> pl.DataFrame:
    """topic 의 블록 목차 DataFrame.

    Args:
        topicRows: 특정 topic 의 sections 행.

    Returns:
        ``block/blockType/preview`` 컬럼 목차 DataFrame.

    Raises:
        없음.

    Example:
        >>> buildBlockIndex(sec.filter(pl.col("topic") == "10-K::item7Mdna"))

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    from dartlab.providers._common.show import buildBlockIndex as _coreBuildBlockIndex

    return _coreBuildBlockIndex(topicRows)


# ── preview helpers ────────────────────────────────────────────────


def shapeStr(df: pl.DataFrame | None) -> str:
    """DataFrame 모양을 ``"HxW"`` 문자열로.

    Args:
        df: 원본 DataFrame.

    Returns:
        ``"5x10"`` 형식 문자열 (None 이면 ``"-"``).

    Raises:
        없음.

    Example:
        >>> shapeStr(df)

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    if df is None:
        return "-"
    return f"{df.height}x{df.width}"


def periodsStr(df: pl.DataFrame | None) -> str:
    """DataFrame period 컬럼 범위를 ``"first..last"`` 문자열로.

    Args:
        df: 원본 DataFrame.

    Returns:
        ``"2020..2024"`` 형식 문자열 (없으면 ``"-"``).

    Raises:
        없음.

    Example:
        >>> periodsStr(df)

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    if df is None:
        return "-"
    periodCols = [c for c in df.columns if _PERIOD_COLUMN_RE.fullmatch(c)]
    if not periodCols:
        return "-"
    return f"{periodCols[0]}..{periodCols[-1]}" if len(periodCols) > 1 else periodCols[0]


def previewFinance(df: pl.DataFrame | None) -> str:
    """finance DataFrame 의 account 수 preview 문자열.

    Args:
        df: 원본 finance DataFrame.

    Returns:
        ``"N accounts"`` 형식 (없으면 ``"-"``).

    Raises:
        없음.

    Example:
        >>> previewFinance(df)

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    if isEmptyDf(df):
        return "-"
    return f"{df.height} accounts"


def previewDocsCell(topicRows: pl.DataFrame, periodCols: list[str]) -> str:
    """docs topic 첫 셀의 preview 문자열.

    Args:
        topicRows: 특정 topic 의 sections 행.
        periodCols: period 컬럼 리스트.

    Returns:
        ``"<period>: <text...>"`` 형식 (없으면 ``"-"``).

    Raises:
        없음.

    Example:
        >>> previewDocsCell(topicRows, ["2024", "2023"])

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    for row in topicRows.iter_rows(named=True):
        for col in periodCols:
            val = row.get(col)
            if val is not None:
                text = str(val).strip().replace("\n", " ")
                return f"{col}: {text[:100]}" if len(text) > 100 else f"{col}: {text[:80]}"
    return "-"


# ── show 진입점 ────────────────────────────────────────────────────


_SHOW_FINANCE_TOPICS = frozenset({"IS", "BS", "CF", "CIS", "SCE", "RATIOS"})


def isStrongTopic(topic: str) -> bool:
    """topic 이 finance 강한 소스(companyfacts)인지 — ``c.panel`` facade 라우팅 SSOT.

    EDGAR 도 DART 와 같이 소문자 is/bs/cf/ratios 는 native 다. 본 함수는 대문자
    IS/BS/CF/CIS/SCE/RATIOS finance 호출만 ``c.show``(companyfacts) 위임 대상으로 본다. 그 외
    item 섹션명·자유 텍스트는 raw panel 보드 행 검색(False). ``providers.dart.builder.dataDispatcher.isStrongTopic``
    의 EDGAR analog — panel facade 가 본 판정을 ``_strongFn`` 주입으로 받아 라우팅한다.

    Args:
        topic: 토픽 이름 (IS/BS/CF/CIS/SCE/ratios 또는 item 섹션명/자유 텍스트).

    Returns:
        True 면 finance 강한 소스(c.show 위임), False 면 raw 공시 보드 검색.

    Raises:
        없음.

    Example:
        >>> isStrongTopic("IS"), isStrongTopic("is"), isStrongTopic("RATIOS")
        (True, False, True)
        >>> isStrongTopic("Risk"), isStrongTopic("item1Business"), isStrongTopic("")
        (False, False, False)

    SeeAlso:
        - ``showImpl`` — 강한 소스 실제 dispatch (finance/sections).
        - ``providers.dart.panel.Panel.__call__`` — 본 판정을 facade 주입으로 받아 라우팅.

    Requires:
        - 없음 (순수 문자열 판정).

    Capabilities:
        - panel facade 의 finance(companyfacts) vs raw 보드 검색 분류 SSOT. 소문자 native 는
          Panel.__call__ 이 본 함수보다 먼저 처리한다.

    Guide:
        - ``Company.panel`` 이 ``p._strongFn = isStrongTopic`` 주입. 직접 호출 안전(순수).

    AIContext:
        - EDGAR 소문자 is/bs/cf/ratios 는 panel 단일 artifact native. 대문자만 companyfacts.

    When:
        - panel ``c.panel(key)`` 가 finance 위임 vs 보드 검색을 가를 때.

    How:
        - topic ∈ _SHOW_FINANCE_TOPICS → True. 대소문자 자동 승격 금지.

    LLM Specifications:
        AntiPatterns:
            - item 섹션명/자유 텍스트를 강함으로 분류 금지 — 보드(False)에서 검색.
        OutputSchema:
            - ``bool``.
        Prerequisites:
            - 없음.
        Freshness:
            - 순수 판정.
        Dataflow:
            - topic → finance set 매칭 → bool.
        TargetMarkets:
            - US (EDGAR).
    """
    if not topic:
        return False
    return topic in _SHOW_FINANCE_TOPICS


def showImpl(
    company: Company,
    topic: str,
    block: int | None = None,
    *,
    period: str | list[str] | None = None,
    raw: bool = False,
    **_kw: Any,
) -> pl.DataFrame | None:
    """topic 데이터 조회 — c.show 의 내부 구현 본체.

    Args:
        company: EDGAR Company 인스턴스.
        topic: topic 이름 (finance: BS/IS/CF/CIS/SCE/ratios 또는 docs item).
        block: 특정 block 인덱스 (None 이면 블록 목차).
        period: 단일 period (str) 또는 vertical view (list).
        raw: raw 패스스루 flag (현재 미사용).
        **_kw: 추가 keyword (freq 등).

    Returns:
        topic DataFrame 또는 None.

    Raises:
        ValueError: sections 부재 또는 topic 미존재.

    Example:
        >>> showImpl(c, "IS", freq="Y")

    SeeAlso:
        - ``EdgarCompany.panel`` — public surface.
        - ``buildFinanceSeries`` / ``buildRatios`` / ``applyPeriodFilter`` — 본 모듈.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - EDGAR Company.panel dispatch + finance series-tuple + ratios + period filter + preview.

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal dispatcher — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
            - topic 미정의 → None. caller None 분기.
        OutputSchema:
            - pl.DataFrame / tuple / dict / None — 함수별.
        Prerequisites:
            - 본 회사 SEC companyfacts/sections 데이터.
        Freshness:
            - SEC EDGAR 갱신 시점.
        Dataflow:
            - topic → finance/sections 분기 → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) show dispatch.
    """
    from dartlab.providers.edgar.company import _TOPIC_ALIASES

    # alias 해석 (riskFactors → item1ARiskFactors 등)
    topic = _TOPIC_ALIASES.get(topic, topic)

    # period가 리스트면 세로 뷰
    if isinstance(period, list):
        wide = company._showImpl(topic, block)
        if wide is None or not isinstance(wide, pl.DataFrame):
            return None
        return transposeToVertical(wide, period)

    # Finance topic(IS/BS/CF/CIS/SCE/ratios) — sections 거치지 않고 직접
    if topic in _SHOW_FINANCE_TOPICS:
        freq = _kw.get("freq", "Q")
        if topic == "ratios":
            df = buildRatios(company)
        elif topic == "SCE":
            df = company._finance.SCE
        else:
            df = company._finance._stmtDf(topic, freq=freq)
        return applyPeriodFilter(df, period) if df is not None else None

    # Notes 12 항목 — DART panel("inventory") 와 동일 패턴 (XBRL 수치 태그 기반)
    try:
        from dartlab.providers.edgar.docs.notesParsers import availableCategories

        if topic in availableCategories():
            return company._docs.notesByCategory(topic)
    except (ImportError, AttributeError):
        pass

    sec = company._docs.sections
    if sec is None:
        # silent None 대신 명시적 ValueError 로 안내
        raise ValueError(
            f"sections 데이터를 가져올 수 없습니다 (ticker={getattr(company, 'ticker', '?')}). "
            f"네트워크 또는 SEC EDGAR API 상태를 확인하세요."
        )

    topicRows = sec.filter(pl.col("topic") == topic)
    if topicRows.is_empty():
        # 가용 topic 일부 안내 (silent None 차단)
        try:
            available = sec["topic"].unique().to_list()[:20]
        except (AttributeError, KeyError):
            available = []
        hint = f"\n  사용 가능한 topic 일부: {', '.join(available)}" if available else ""
        raise ValueError(
            f"'{topic}' topic 을 찾을 수 없습니다 (EDGAR).{hint}\n  전체 목록: c.topics 또는 c.index 로 확인하세요."
        )

    if block is None:
        blockIndex = buildBlockIndex(topicRows)
        if blockIndex.height == 1:
            return company._showImpl(topic, blockIndex["block"][0], period=period)
        return blockIndex

    # 특정 block의 실제 데이터
    source = "docs"
    if "source" in topicRows.columns:
        srcRows = topicRows.filter(pl.col("blockOrder") == block) if "blockOrder" in topicRows.columns else topicRows
        if not srcRows.is_empty():
            source = srcRows["source"][0]

    if source == "finance":
        freq = _kw.get("freq", "Q")
        if topic == "ratios":
            df = buildRatios(company)
            return applyPeriodFilter(df, period) if df is not None else None
        if topic == "SCE":
            df = company._finance.SCE
            return applyPeriodFilter(df, period) if df is not None else None
        df = company._finance._stmtDf(topic, freq=freq)
        return applyPeriodFilter(df, period) if df is not None else None

    # docs — blockType에 따라 text/table 반환
    periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]
    if "blockType" in topicRows.columns:
        # blockOrder로 필터 (None이면 blockType으로 대체)
        bt = "text"
        if "blockOrder" in topicRows.columns:
            boFiltered = topicRows.filter(pl.col("blockOrder") == block)
            if not boFiltered.is_empty():
                bt = boFiltered["blockType"][0]
            else:
                # blockOrder가 None인 경우 — 인덱스로 접근
                btList = topicRows["blockType"].to_list()
                bt = btList[block] if block < len(btList) else "text"

        if bt == "text":
            textRows = topicRows.filter(pl.col("blockType") == "text")
            if textRows.is_empty():
                return None
            nonNullCols = [c for c in periodCols if textRows[c].null_count() < textRows.height]
            if not nonNullCols:
                return None
            return applyPeriodFilter(textRows.select(nonNullCols), period)
        else:
            tableRows = topicRows.filter(pl.col("blockType") == "table")
            if tableRows.is_empty():
                return None
            nonNullCols = [c for c in periodCols if tableRows[c].null_count() < tableRows.height]
            if not nonNullCols:
                return None
            return applyPeriodFilter(tableRows.select(nonNullCols), period)

    return applyPeriodFilter(topicRows, period)
