"""DART Company 의 show/select 보조 utility.

Company.panel / select 가 호출하는 stateless utility 헬퍼 — facade 의 책임 분산
1차 (show/select 본체 분리는 Stage 2-4b 이후 단계).

Module-level helpers:
    cleanFinanceDataFrame  — BS/IS/CF/CIS/SCE 후처리 (all-null 행 제거, 중복 병합)
    transposeToVertical    — wide → long 변환 (delegate to dartlab.providers._common.show)
    warnUnknownTopic       — 미등록 topic 경고 (유사 topic 제안)
    applyPeriodFilter      — period 컬럼 필터링 (exact / Q4 fallback / period column)
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab.providers.dart.checks import _isPeriodColumn


def cleanFinanceDataFrame(df: pl.DataFrame, sjDiv: str) -> pl.DataFrame:
    """재무제표 DataFrame 후처리 — all-null 행 제거, CF 고유 정리, 중복행 병합.

    - CF 고유: ``"당기순이익"`` 제거 (standalone 차분 오류), 영문 항목 제거.
    - 공통: 모든 기간이 null 인 행 제거.
    - 공통: 같은 ``항목`` 중복행 병합 (mapper 의 한국어 → snakeId 1:N 충돌 해결).

    Args:
        df: 후처리 대상 DataFrame.
        sjDiv: BS/IS/CF/CIS/SCE 중 하나.

    Returns:
        후처리된 DataFrame.

    Raises:
        없음.

    Example:
        >>> cleanFinanceDataFrame(df, "CF")

    SeeAlso:
        - ``dataDispatcher`` — 본 모듈 호출자.
        - ``Company.panel`` / ``Company.select`` — public surface.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/show 후처리 stateless utility (cleanFinanceDataFrame / transposeToVertical /
          warnUnknownTopic / applyPeriodFilter).

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal show helper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
        OutputSchema:
            - pl.DataFrame / None — 함수별.
        Prerequisites:
            - 본 회사 finance/docs 데이터.
        Freshness:
            - 데이터 갱신 시점.
        Dataflow:
            - DataFrame 입력 → stateless 변환 → 본 함수.
        TargetMarkets:
            - KR (DART) show 보조.
    """
    periodCols = [c for c in df.columns if _isPeriodColumn(c)]
    if not periodCols:
        return df
    labelCol = "항목"
    # CF 고유: 당기순이익 제거 (standalone 차분 오류), 영문 항목 제거
    if sjDiv == "CF":
        df = df.filter(~pl.col(labelCol).is_in(["당기순이익", "법인세비용차감전순이익"]))
        df = df.filter(~pl.col(labelCol).str.contains(r"^[a-z_]+$"))
    # 공통: all-null 행 제거 (모든 기간이 null 인 행)
    notAllNull = pl.any_horizontal([pl.col(c).is_not_null() for c in periodCols])
    df = df.filter(notAllNull)
    # 공통: 같은 항목 중복행 병합 — mapper 의 한국어 → 여러 snakeId (1:N) 충돌 해결.
    if df[labelCol].n_unique() < df.height:
        hasSnakeId = "snakeId" in df.columns
        aggCols = list(periodCols)
        extraAgg = [pl.col("snakeId").first().alias("snakeId")] if hasSnakeId else []
        merged = df.group_by(labelCol, maintain_order=True).agg(
            extraAgg + [pl.col(c).drop_nulls().first().alias(c) for c in aggCols]
        )
        df = merged.select([c for c in df.columns if c in merged.columns])
    return df


def transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
    """wide → long 변환. ``dartlab.providers._common.show.transposeToVertical`` 위임.

    Args:
        wide: 행=계정/열=period wide DataFrame.
        periods: 변환 대상 period 컬럼 리스트.

    Returns:
        long DataFrame 또는 None (변환 실패).

    Raises:
        없음.

    Example:
        >>> transposeToVertical(wide_df, ["2024Q4", "2024Q3"])

    SeeAlso:
        - ``dataDispatcher`` — 본 모듈 호출자.
        - ``Company.panel`` / ``Company.select`` — public surface.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/show 후처리 stateless utility (cleanFinanceDataFrame / transposeToVertical /
          warnUnknownTopic / applyPeriodFilter).

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal show helper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
        OutputSchema:
            - pl.DataFrame / None — 함수별.
        Prerequisites:
            - 본 회사 finance/docs 데이터.
        Freshness:
            - 데이터 갱신 시점.
        Dataflow:
            - DataFrame 입력 → stateless 변환 → 본 함수.
        TargetMarkets:
            - KR (DART) show 보조.
    """
    from dartlab.providers._common.show import transposeToVertical as _coreTransposeToVertical

    return _coreTransposeToVertical(wide, periods)


def warnUnknownTopic(topic: str, sec: pl.DataFrame) -> None:
    """미등록 topic 경고 — 유사 topic 제안 + ``c.topics`` 안내.

    difflib 의 ``get_close_matches`` 로 상위 3 개 유사 topic 추출.

    Args:
        topic: 미등록 topic 이름.
        sec: sections DataFrame (``topic`` 컬럼에서 후보 풀 추출).

    Returns:
        None (warning 만 발생).

    Raises:
        없음 (warnings.warn 호출만).

    Example:
        >>> warnUnknownTopic("majorShareholders", sections_df)  # majorHolder 제안

    SeeAlso:
        - ``dataDispatcher`` — 본 모듈 호출자.
        - ``Company.panel`` / ``Company.select`` — public surface.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/show 후처리 stateless utility (cleanFinanceDataFrame / transposeToVertical /
          warnUnknownTopic / applyPeriodFilter).

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal show helper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
        OutputSchema:
            - pl.DataFrame / None — 함수별.
        Prerequisites:
            - 본 회사 finance/docs 데이터.
        Freshness:
            - 데이터 갱신 시점.
        Dataflow:
            - DataFrame 입력 → stateless 변환 → 본 함수.
        TargetMarkets:
            - KR (DART) show 보조.
    """
    import difflib
    import warnings

    all_topics = sec["topic"].unique().sort().to_list() if "topic" in sec.columns else []
    similar = difflib.get_close_matches(topic, all_topics, n=3, cutoff=0.4)
    if similar:
        warnings.warn(
            f"'{topic}' topic을 찾을 수 없습니다. "
            f"유사한 topic: {', '.join(similar)}. "
            f"전체 목록은 c.topics로 확인하세요.",
            stacklevel=3,
        )
    else:
        warnings.warn(
            f"'{topic}' topic을 찾을 수 없습니다. 전체 목록은 c.topics 또는 c.index로 확인하세요.",
            stacklevel=3,
        )


def applyPeriodFilter(payload: Any, period: str | None) -> Any:
    """period 컬럼 필터링 — exact / Q4 fallback / period 컬럼 매칭.

    매칭 우선순위: ``rawPeriod`` 정규화 → exact → ``"2024"`` → ``"2024Q4"`` 확장.

    Args:
        payload: DataFrame 또는 임의 payload (DataFrame 아니면 그대로 반환).
        period: 필터 period (``"2024"`` / ``"2024Q4"`` / None).

    Returns:
        필터된 DataFrame 또는 원본 payload (period 미지정 시). 요청 기간이 wide 표에 없으면
        None.

    Raises:
        없음.

    Example:
        >>> applyPeriodFilter(df, "2024Q4")

    SeeAlso:
        - ``dataDispatcher`` — 본 모듈 호출자.
        - ``Company.panel`` / ``Company.select`` — public surface.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/show 후처리 stateless utility (cleanFinanceDataFrame / transposeToVertical /
          warnUnknownTopic / applyPeriodFilter).

    Guide:
        - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

    AIContext:
        internal show helper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 본 모듈 직접 호출 X — Company facade 위임.
        OutputSchema:
            - pl.DataFrame / None — 함수별.
        Prerequisites:
            - 본 회사 finance/docs 데이터.
        Freshness:
            - 데이터 갱신 시점.
        Dataflow:
            - DataFrame 입력 → stateless 변환 → 본 함수.
        TargetMarkets:
            - KR (DART) show 보조.
    """
    if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
        return payload
    from dartlab.providers.dart.sectionPeriod import rawPeriod

    requestedPeriod = str(period)
    normalizedPeriod = rawPeriod(period)

    # exact match first, then normalized (Q4 → annual alias), then Q4 expansion
    q4Fallback = f"{requestedPeriod}Q4" if "Q" not in requestedPeriod else None
    exactPeriod = (
        normalizedPeriod
        if normalizedPeriod in payload.columns
        else (
            requestedPeriod
            if requestedPeriod in payload.columns
            else (q4Fallback if q4Fallback and q4Fallback in payload.columns else None)
        )
    )
    if exactPeriod is not None:
        keepCols = [c for c in payload.columns if not _isPeriodColumn(c)]
        keepCols.append(exactPeriod)
        result = payload.select(keepCols)
        if exactPeriod != requestedPeriod:
            result = result.rename({exactPeriod: requestedPeriod})
        return result

    if "period" in payload.columns:
        result = payload.filter(pl.col("period") == normalizedPeriod)
        if result.is_empty() and "Q" not in normalizedPeriod:
            result = payload.filter(pl.col("period") == f"{normalizedPeriod}Q4")
        return result
    if "year" in payload.columns:
        return payload.filter(pl.col("year").cast(pl.Utf8) == normalizedPeriod)
    return None
