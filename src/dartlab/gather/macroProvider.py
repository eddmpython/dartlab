"""DefaultMacroProvider — F3 Protocol DIP 의 macro 측 구현체.

macro 엔진이 직접 gather 를 import 하지 않도록 추상화.
"""

from __future__ import annotations

from typing import Any

import polars as pl


def _latestValue(dataFrame: pl.DataFrame | None) -> float | None:
    if dataFrame is None or len(dataFrame) == 0:
        return None
    vals = dataFrame.get_column("value").drop_nulls()
    if len(vals) == 0:
        return None
    return float(vals[-1])


def _yoyValue(dataFrame: pl.DataFrame | None) -> float | None:
    if dataFrame is None or len(dataFrame) == 0:
        return None
    vals = dataFrame.get_column("value").drop_nulls()
    if len(vals) < 13:
        return None
    current = float(vals[-1])
    prev = float(vals[-13])
    if prev == 0:
        return None
    return ((current - prev) / abs(prev)) * 100


class DefaultMacroProvider:
    """MacroDataProvider 기본 구현 — gather/entry + macro/seriesFetch 우회."""

    def getDefaultGather(self) -> Any:
        """``.macro()`` 메서드를 가진 Gather 싱글턴.

        Capabilities: MacroDataProvider Protocol — engine Gather 싱글턴 lazy 반환.
        AIContext: macro engine 이 gather 본체 직접 의존 회피 — F3 Protocol DIP 의 macro 측 본체.
        Guide: 반환 객체는 ``.macro(seriesId)`` 메서드 계약 (L2 macro seriesFetch 전제).
            ⚠ GatherEntry(축 callable)로 바꾸면 ``.macro`` 부재 AttributeError 가 L2 전역의
            예외 흡수에 삼켜져 cycle/quadrant 가 조용히 열화된다 (2026-06-12 실측 회귀).
        When: macro engine 이 시리즈 fetch 위해 gather 필요 시.
        How: ``entry.providerAdapter.getDefaultGather()`` 위임 — engine.Gather 싱글턴
            (캐시·HTTP 클라이언트 재사용).

        Returns:
            engine.Gather 싱글턴 — ``.macro(seriesId)`` 시계열 fetch 에 사용.

        Raises:
            ImportError: gather import 실패.

        Requires:
            ``dartlab.gather.entry.providerAdapter`` import 가능.

        Example:
            >>> p = DefaultMacroProvider()
            >>> g = p.getDefaultGather()
            >>> df = g.macro("CPI")

        See Also:
            entry.providerAdapter.getDefaultGather : 위임 대상 singleton.
            core.macroProvider.MacroDataProvider : 본 메서드의 Protocol 정의.
        """
        from dartlab.gather.entry.providerAdapter import getDefaultGather

        return getDefaultGather()

    def applyAsOf(self, dataFrame: pl.DataFrame, asOf: str) -> pl.DataFrame:
        """as-of 필터링 — ``date <= asOf`` 행만 유지.

        Capabilities: ``date`` 컬럼 cutoff 필터 — look-ahead bias 차단.
        AIContext: macro 회귀 분석 시 분석 시점 이후 데이터 누출 방지.
        Guide: ISO 형식 (YYYY-MM-DD) 권장. date 컬럼은 필수다.
        When: 백테스트 / pseudo-prophet 분석 시.
        How: ``df.filter(pl.col('date') <= asOf)``.

        Args:
            dataFrame: 입력 DataFrame.
            asOf: 컷오프 날짜 (ISO 형식).

        Returns:
            컷오프를 적용한 새 DataFrame.

        Raises:
            KeyError: ``date`` 컬럼이 없을 때.

        Requires:
            dataFrame 의 ``date`` 컬럼 (있을 때만 적용).

        Example:
            >>> p = DefaultMacroProvider()
            >>> p.applyAsOf(df, "2024-12-31")

        See Also:
            fetchSeriesLatest · fetchSeriesYoy : asOf 미적용 단건 fetch.
        """
        if "date" not in dataFrame.columns:
            raise KeyError("macro as-of 필터에 필요한 'date' 컬럼이 없습니다.")
        return dataFrame.filter(pl.col("date") <= asOf)

    def fetchSeriesLatest(self, seriesId: str, *, limit: int | None = None) -> float | None:
        """seriesId 의 최신 값.

        Capabilities: gather.macro 시계열에서 최신 non-null value 추출.
        AIContext: 단건 매크로 값 표시 (UI tile, narrative 단순 인용).
        Guide: 실패 시 None — caller 가 None check.
        When: 단일 시점 매크로 값 표시 / KPI 대시보드 / narrative 인용 시.
        How: ``getDefaultGather().macro(seriesId)`` + 마지막 non-null value 추출.

        Args:
            seriesId: macro 시리즈 ID (예: "GDP").
            limit: 단건 float 반환 함수라 무시된다. 인터페이스 호환 목적.

        Returns:
            최신 관측치 (float). 유효 관측치가 없으면 None.

        Raises:
            Exception: gather/provider 호출 실패와 잘못된 schema를 원인 그대로 전달.

        Requires:
            GatherEntry.macro(seriesId)가 ``value`` 컬럼을 가진 DataFrame 반환.

        Example:
            >>> p = DefaultMacroProvider()
            >>> latest = p.fetchSeriesLatest("GDP")

        See Also:
            fetchSeriesYoy : 동행 YoY 단건.
            applyAsOf : 시계열 cutoff.
        """
        del limit

        return _latestValue(self.getDefaultGather().macro(seriesId))

    def fetchSeriesYoy(self, seriesId: str, *, limit: int | None = None) -> float | None:
        """seriesId 의 YoY 변화율.

        Capabilities: gather.macro 시계열에서 12개월 전 대비 YoY 계산.
        AIContext: 인플레이션/생산 YoY 비교 분석 진입 (CPI/IPI/PPI 등).
        Guide: 단건 float — 시계열 필요 시 macro entry.
        When: 단일 YoY 값 표시 / regime classifier 입력 시.
        How: ``getDefaultGather().macro(seriesId)`` + 마지막 값과 13번째 이전 값 비교.

        Args:
            seriesId: macro 시리즈 ID (예: "CPI").
            limit: 단건 float 반환 함수라 무시된다. 인터페이스 호환 목적.

        Returns:
            전년 동기 대비 변화율 (%, float). 관측치가 부족하거나 기준값이 0이면 None.

        Raises:
            Exception: gather/provider 호출 실패와 잘못된 schema를 원인 그대로 전달.

        Requires:
            GatherEntry.macro(seriesId)가 ``value`` 컬럼을 가진 DataFrame 반환.

        Example:
            >>> p = DefaultMacroProvider()
            >>> yoy = p.fetchSeriesYoy("CPI")

        See Also:
            fetchSeriesLatest : 동행 단건 latest.
        """
        del limit

        return _yoyValue(self.getDefaultGather().macro(seriesId))
