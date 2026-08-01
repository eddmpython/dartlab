"""macro 엔진 공통 헬퍼."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import polars as pl

log = logging.getLogger(__name__)


def recentTimeseries(df, months: int = 6, valueCol: str = "value") -> list[dict] | None:
    """gather DataFrame에서 최근 N개월분 시계열 추출.

    Capabilities:
        gather.macro() polars DataFrame 에서 최근 N 개월 시계열을 추출해 JSON 친화적
        [{date, value}] 리스트로 변환. UI 차트 / Story narrative 시계열 직렬화 헬퍼.

    Parameters
    ----------
    df : pl.DataFrame | None
        gather.macro() 결과 (date, value 컬럼).
    months : int
        추출 기간 (개월).
    value_col : str
        값 컬럼명.

    Returns
    -------
    list[dict] | None
        [{date: str — "YYYY-MM-DD", value: float}] 리스트. 데이터 없으면 None.

    Raises:
        없음 — 파싱 실패 시 None.

    Example:
        >>> from dartlab.macro.seriesFetch import recentTimeseries
        >>> recentTimeseries(df, months=3)[0]
        {'date': '2026-02-15', 'value': 5.4}

    Guide:
        반환 리스트는 시간 오름차순. JSON 직렬화 가능.

    When:
        UI 차트 직렬화 / analyzeCrisis timeseries 키 생성 시.

    How:
        cutoff = now - months × 30 days → filter → date/value 컬럼 추출 → dict 변환.

    See Also:
        - ``dartlab.macro.seriesFetch.collectTimeseries`` : 다중 시리즈 일괄

    Requires:
        - polars DataFrame (date / value 컬럼).

    AIContext:
        AI 직접 호출 없음 (내부 헬퍼). 결과는 UI / JSON 직렬화에 그대로 사용.
    """
    if df is None or len(df) == 0:
        return None
    try:
        cutoff = datetime.now() - timedelta(days=months * 30)
        filtered = df.filter(df["date"] >= cutoff).sort("date")
        if len(filtered) == 0:
            return None
        dates = filtered.get_column("date").to_list()
        vals = filtered.get_column(valueCol).to_list()
        return [
            {"date": str(d)[:10], "value": float(v) if v is not None else None}
            for d, v in zip(dates, vals)
            if v is not None
        ]
    except (KeyError, ValueError, TypeError):
        return None


def applyAsOf(df, asOf: str | None) -> "pl.DataFrame | None":
    """관측일 기준 cutoff 필터. 빈티지·공표시점 보장은 하지 않는다.

    Capabilities:
        최신 수정치 시계열에서 관측일이 as_of 이후인 행을 제거한다. 이 함수만으로는
        데이터 빈티지나 공표 지연을 재현할 수 없으므로 point-in-time 백테스트에 사용할 수 없다.

    Parameters
    ----------
    df : pl.DataFrame | None
        date 컬럼을 포함한 시계열 DataFrame.
    as_of : str | None
        기준 날짜 ("YYYY-MM-DD"). None이면 필터 없이 원본 반환.

    Returns
    -------
    pl.DataFrame | None
        as_of 이하 행만 남긴 DataFrame. df가 None이면 None.

    Raises:
        ValueError: asOf가 YYYY-MM-DD 형식이 아닐 때.
        TypeError: asOf가 문자열이 아닐 때.

    Example:
        >>> from dartlab.macro.seriesFetch import applyAsOf
        >>> applyAsOf(df, "2024-12-31")

    Guide:
        ``getGather(asOf)`` 가 본 함수를 자동 적용. 직접 호출은 드물다.

    When:
        최신 수정치 자료의 관측일 cutoff가 필요할 때. 성과 백테스트에는 사용 금지.

    How:
        asOf 파싱 → df.filter(date <= cutoff).

    See Also:
        - ``dartlab.macro.seriesFetch.getGather`` : as_of 자동 적용 wrapper

    Requires:
        - polars DataFrame (date 컬럼) 또는 None.

    AIContext:
        AI 직접 호출 없음 (백테스트 내부 헬퍼).
    """
    if asOf is None:
        return df
    if not isinstance(asOf, str):
        raise TypeError("asOf는 YYYY-MM-DD 형식의 문자열이어야 합니다.")
    try:
        cutoff = datetime.strptime(asOf, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("asOf는 유효한 YYYY-MM-DD 형식이어야 합니다.") from exc
    if df is None or len(df) == 0:
        return df
    return df.filter(df["date"] <= cutoff)


def applyOverrides(data: dict, overrides: dict | None) -> dict:
    """overrides dict를 data에 병합 — 시나리오 시뮬레이션용.

    Capabilities:
        AI / 사용자 시나리오 가정 dict 를 원본 data 에 in-place 병합. analyzeCrisis 등 매크로
        엔진의 overrides 진입점.

    Parameters
    ----------
    data : dict
        원본 데이터 dict.
    overrides : dict | None
        덮어쓸 키-값 쌍. None이면 원본 그대로.

    Returns
    -------
    dict
        overrides가 병합된 data (in-place 수정).

    Raises:
        없음.

    Example:
        >>> from dartlab.macro.seriesFetch import applyOverrides
        >>> applyOverrides({"vix": 15}, {"vix": 40})
        {'vix': 40}

    Guide:
        in-place 수정 — 호출자가 원본 보존하려면 사전 copy 필요.

    When:
        analyzeCrisis / analyzeCycle 의 overrides 파라미터가 본 함수 사용.

    How:
        overrides 가 None 이 아니면 data.update(overrides) 호출.

    See Also:
        - ``dartlab.macro.crisis.crisis.analyzeCrisis`` : 본 함수 사용자

    Requires:
        - dict 데이터 + overrides dict (None 허용).

    AIContext:
        AI 가 시나리오 분기 답변 시 overrides dict 직접 구성. 본 함수는 내부 병합 헬퍼.
    """
    if overrides:
        data.update(overrides)
    return data


# ══════════════════════════════════════
# 공통 fetch 헬퍼 — 90회 중복 제거
# ══════════════════════════════════════


def getGather(asOf: str | None = None) -> "Any":
    """gather 인스턴스 생성 — as_of 있으면 자동 필터링 래핑.

    Capabilities:
        DI 의 macroProvider → default gather 추출 후 asOf 가 있으면 macro 메서드를 ``applyAsOf``
        wrapper 로 교체한 사본 반환. L2 macro 모듈의 단일 gather 진입점.

    모든 L2 모듈의 _fetch_* 함수에서 이것을 사용.

    Parameters
    ----------
    as_of : str | None
        관측일 cutoff 날짜 ("YYYY-MM-DD"). None이면 원본 gather. 최신 수정치에
        적용되므로 빈티지·공표시점 기준의 point-in-time 데이터가 아니다.

    Returns
    -------
    Gather
        macro() 호출 시 as_of 필터가 적용된 gather 인스턴스.

    Raises:
        없음 — DI 미초기화 시 di 모듈이 raise.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather
        >>> g = getGather("2024-12-31")
        >>> g.macro("UNRATE")

    Guide:
        asOf는 시점 표시용 관측일 cutoff다. 성과 백테스트의 PIT 근거로 사용하지 않는다.

    When:
        모든 L2 macro 모듈의 _fetch_* 함수에서 진입점. AI 직접 호출 드물다.

    How:
        getMacroProvider → gather → asOf None 이면 그대로 / 있으면 copy 후 macro 메서드 wrap.

    See Also:
        - ``dartlab.macro.seriesFetch.applyAsOf`` : 본 함수가 사용
        - ``dartlab.core.di.getMacroProvider`` : provider DI

    Requires:
        - DI 초기화 (``getMacroProvider`` 가 default gather 보유)

    AIContext:
        AI 직접 호출 없음 (L2 macro 내부 진입점).
    """
    from dartlab.core.di import getMacroProvider

    g = getMacroProvider().getDefaultGather()
    if asOf is None:
        return g

    _orig = g.macro

    def _filtered(sid):
        return applyAsOf(_orig(sid), asOf)

    import copy

    gc = copy.copy(g)
    gc.macro = _filtered  # type: ignore
    return gc


def fetchLatest(g, seriesId: str) -> float | None:
    """시리즈의 최신값 1개 조회.

    Capabilities:
        gather.macro(seriesId) 결과의 마지막 non-null 관측값 1 개 반환. 가장 자주 쓰는 헬퍼 —
        90+ 호출처.

    Parameters
    ----------
    g : Gather
        gather 인스턴스 (get_gather() 결과).
    series_id : str
        FRED/ECOS 시리즈 ID (예: "GDP", "UNRATE").

    Returns
    -------
    float | None
        최신 관측값. 실패 시 None (debug 로깅).

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchLatest
        >>> fetchLatest(getGather(), "UNRATE")
        4.1

    Guide:
        실패 (KeyError/ValueError) 는 debug 로그만 — 호출자가 None 체크 의무.

    When:
        L2 macro 모듈의 단일 최신값 fetch 시.

    How:
        g.macro(seriesId) → drop_nulls → vals[-1].

    See Also:
        - ``dartlab.macro.seriesFetch.fetchLatestWithPrev`` : 최신 + 직전

    Raises:
        없음 — fetch 실패는 debug log + None.

    Requires:
        - gather 인스턴스 (``getGather`` 결과) + seriesId 매핑.
    """
    try:
        df = g.macro(seriesId)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) > 0:
                return float(vals[-1])
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_latest(%s) 실패: %s", seriesId, e)
    return None


def fetchLatestWithPrev(g, seriesId: str) -> tuple[float | None, float | None]:
    """최신값 + 직전값 조회 — 모멘텀 계산용.

    Capabilities:
        gather.macro(seriesId) 결과의 마지막 2 개 non-null 값 반환. 단순 모멘텀 (delta) 계산에
        사용.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_id : str
        시리즈 ID.

    Returns
    -------
    tuple[float | None, float | None]
        (최신값, 직전값). 데이터 부족 시 (None, None).

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchLatestWithPrev
        >>> fetchLatestWithPrev(getGather(), "UNRATE")
        (4.1, 4.0)

    Guide:
        값 1 개만 있으면 (val, None) 반환 — 호출자 안전 패턴.

    When:
        모멘텀 / 1 기간 delta 답변 시.

    How:
        drop_nulls → 마지막 2 개 추출.

    See Also:
        - ``dartlab.macro.seriesFetch.fetchYoy`` : 12 기간 YoY

    Raises:
        없음 — fetch 실패는 debug log + (None, None).

    Requires:
        - gather 인스턴스 + seriesId.
    """
    try:
        df = g.macro(seriesId)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) >= 2:
                return float(vals[-1]), float(vals[-2])
            if len(vals) == 1:
                return float(vals[-1]), None
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_latest_with_prev(%s) 실패: %s", seriesId, e)
    return None, None


def fetchSeriesList(g, seriesId: str) -> list[float] | None:
    """전체 시계열을 float 리스트로 조회.

    Capabilities:
        gather.macro(seriesId) 결과 전체를 float 리스트로 변환. Hamilton recession probability /
        Sahm rule / FCI 등 시계열 알고리즘 입력.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_id : str
        시리즈 ID.

    Returns
    -------
    list[float] | None
        시간순 값 리스트. Hamilton/Sahm/FCI 등 시계열 알고리즘에 사용.
        데이터 없으면 None.

    Raises:
        없음 — fetch 실패 시 None.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchSeriesList
        >>> fetchSeriesList(getGather(), "UNRATE")[-3:]

    Guide:
        시간 오름차순 보존. 시계열 알고리즘 표준 입력 형태.

    When:
        ``creditToGDPGap`` / Sahm rule / FCI 계산 등 시계열 알고리즘 호출 전.

    How:
        g.macro(seriesId) → drop_nulls → to_list.

    See Also:
        - ``dartlab.macro.crisis.detectors.creditToGDPGap`` : 본 함수 결과 소비자

    Requires:
        - gather 인스턴스 + seriesId.
    """
    try:
        df = g.macro(seriesId)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls().to_list()
            if vals:
                return [float(v) for v in vals]
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_series_list(%s) 실패: %s", seriesId, e)
    return None


def fetchYoy(g, seriesId: str) -> float | None:
    """12개월 전 대비 YoY 변화율.

    Capabilities:
        월간 시계열 가정 — 마지막 관측치와 12 개월 전 관측치 비율 (%). 관측 < 13 이면 None.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_id : str
        시리즈 ID.

    Returns
    -------
    float | None
        전년동월대비 변화율 (%). 관측치 13개 미만이면 None.

    Raises:
        없음.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchYoy
        >>> fetchYoy(getGather(), "CPIAUCSL")
        3.2

    Guide:
        월간 시계열 가정. 분기 시리즈는 ``fetchChangePct(g, sid, lookback=4)`` 사용.

    When:
        월간 macro 지표 (CPI/PCE/실업률) 의 YoY 답변.

    How:
        drop_nulls → vals[-1] vs vals[-13] 비율 × 100.

    See Also:
        - ``dartlab.macro.seriesFetch.fetchChangePct`` : 임의 lookback

    Requires:
        - gather 인스턴스 + 월간 시리즈 (관측 ≥ 13).
    """
    try:
        df = g.macro(seriesId)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) >= 13:
                current = float(vals[-1])
                prev = float(vals[-13])
                if prev != 0:
                    return ((current - prev) / abs(prev)) * 100
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_yoy(%s) 실패: %s", seriesId, e)
    return None


def fetchChangePct(g, seriesId: str, lookback: int = 63) -> float | None:
    """lookback 관측치 전 대비 변화율.

    Capabilities:
        가변 lookback (관측 수) 변화율 헬퍼. 일간 시계열 63 일 ≈ 3 개월, 252 ≈ 1 년 표준.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_id : str
        시리즈 ID.
    lookback : int
        비교 기준 관측치 수. 기본 63 ≈ 3개월(일간 데이터).

    Returns
    -------
    float | None
        변화율 (%). 데이터 부족 시 None.

    Raises:
        없음.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchChangePct
        >>> fetchChangePct(getGather(), "DTWEXBGS", lookback=63)
        2.5

    Guide:
        일간 시리즈에서 63 일 (3 개월 영업일) 기본. 호출자가 lookback 명시 권장.

    When:
        DXY / VIX / HY spread 등 일간 시리즈의 단기 변화율 답변.

    How:
        drop_nulls → vals[-1] vs vals[-lookback] 비율 × 100.

    See Also:
        - ``dartlab.macro.seriesFetch.fetchYoy`` : 12 기간 (월간) YoY

    Requires:
        - gather 인스턴스 + 시리즈 (관측 > lookback).
    """
    try:
        df = g.macro(seriesId)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) > lookback:
                current = float(vals[-1])
                old = float(vals[-lookback])
                if old != 0:
                    return ((current - old) / abs(old)) * 100
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_change_pct(%s) 실패: %s", seriesId, e)
    return None


def fetchWithHistory(g, seriesId: str) -> dict[str, float | None]:
    """최신 + 직전 + 6개월전 값을 한 번에 조회.

    Capabilities:
        하나의 fetch 로 current/prev/6m 3 시점 값 dict 반환. 단기 (1 기간) + 중기 (6 기간) 변화
        동시 답변에 효율적.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_id : str
        시리즈 ID.

    Returns
    -------
    dict[str, float | None]
        current : float | None — 최신값
        prev : float | None — 직전값
        6m : float | None — 6개월전 값

    Raises:
        없음.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchWithHistory
        >>> fetchWithHistory(getGather(), "UNRATE")
        {'current': 4.1, 'prev': 4.0, '6m': 3.8}

    Guide:
        월간 시리즈 권장. 분기 시리즈에서 "6m" 은 약 2 분기 전.

    When:
        AI 답변 "현재 X, 전월 Y, 6 개월 전 Z" 1 회 fetch 시.

    How:
        drop_nulls → 마지막 / 마지막-1 / 마지막-6 추출.

    See Also:
        - ``dartlab.macro.seriesFetch.fetchLatestWithPrev`` : 2 시점만 필요할 때

    Requires:
        - gather 인스턴스 + 시리즈 (관측 ≥ 7 권장).

    AIContext:
        AI 답변 시 "최신, 전월, 6개월 전" 3 시점 답변에 본 함수 결과 dict 그대로 사용.
    """
    result: dict[str, float | None] = {}
    try:
        df = g.macro(seriesId)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls().to_list()
            if vals:
                result["current"] = float(vals[-1])
                if len(vals) > 1:
                    result["prev"] = float(vals[-2])
                if len(vals) > 6:
                    result["6m"] = float(vals[-7])
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_with_history(%s) 실패: %s", seriesId, e)
    return result


def fetchMonthlyDict(g, seriesId: str) -> dict[str, float] | None:
    """시리즈를 월간 dict로 변환 — 역사적 분석용.

    Capabilities:
        시계열을 {"YYYY-MM": value} 월간 dict 로 직렬화 — 같은 달 중복은 마지막 값. 역사 이벤트
        매칭 (Dalio 48 / 2008 / 2020) 에서 시점 룩업.

    같은 달에 여러 값이면 마지막 값.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_id : str
        시리즈 ID.

    Returns
    -------
    dict[str, float] | None
        {"YYYY-MM": value} 매핑. 데이터 없으면 None.

    Raises:
        없음.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, fetchMonthlyDict
        >>> d = fetchMonthlyDict(getGather(), "UNRATE")
        >>> d["2008-10"]
        6.5

    Guide:
        역사 시점 룩업 (2008-09 등) 에 적합. 시계열 알고리즘은 ``fetchSeriesList`` 사용.

    When:
        ``matchHistoricalEvents`` 같은 시점 매칭 함수 입력 생성 시.

    How:
        date 컬럼 → "YYYY-MM" 키 → value 매핑 dict.

    See Also:
        - ``dartlab.macro.corporate.historicalContext.matchHistoricalEvents`` : 본 함수 사용자

    Requires:
        - gather 인스턴스 + 시리즈.
    """
    try:
        df = g.macro(seriesId)
        if df is None or len(df) == 0:
            return None
        dates = df.get_column("date").to_list()
        values = df.get_column("value").to_list()
        monthly: dict[str, float] = {}
        for d, v in zip(dates, values):
            if v is not None:
                monthly[str(d)[:7]] = float(v)
        return monthly if monthly else None
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        log.debug("fetch_monthly_dict(%s) 실패: %s", seriesId, e)
        return None


def collectTimeseries(g, seriesMap: dict[str, str]) -> dict[str, list[dict] | None]:
    """여러 시리즈의 최근 시계열을 일괄 수집.

    Capabilities:
        다중 시리즈 (label → seriesId) 를 한 번의 호출로 ``recentTimeseries`` 형태로 수집. UI
        차트 / Story 시계열 dict 합성에 사용.

    Parameters
    ----------
    g : Gather
        gather 인스턴스.
    series_map : dict[str, str]
        {라벨: 시리즈ID} 매핑 (예: {"GDP": "GDP", "실업률": "UNRATE"}).

    Returns
    -------
    dict[str, list[dict] | None]
        {라벨: [{date: str, value: float}] | None} — 실패한 시리즈는 None.

    Example:
        >>> from dartlab.macro.seriesFetch import getGather, collectTimeseries
        >>> ts = collectTimeseries(getGather(), {"GDP": "GDP", "실업률": "UNRATE"})

    Guide:
        실패한 시리즈는 None 으로 분리 — 호출자가 dict 값 None 체크.

    When:
        ``analyzeCrisis`` 가 timeseries 키 합성 시 본 함수 호출.

    How:
        seriesMap 루프 → ``recentTimeseries(g.macro(sid))`` → dict[label] = result.

    See Also:
        - ``dartlab.macro.seriesFetch.recentTimeseries`` : 개별 시리즈

    Raises:
        없음 — 개별 시리즈 실패 시 dict[label]=None.

    Requires:
        - gather 인스턴스 + seriesMap dict.

    AIContext:
        AI 답변 차트 데이터 dict 직접 인용 가능. 실패 (None) 라벨은 답변에 "데이터 부재" 단서.
    """
    ts: dict[str, list[dict] | None] = {}
    for label, sid in seriesMap.items():
        try:
            ts[label] = recentTimeseries(g.macro(sid))
        except (KeyError, ValueError, TypeError, AttributeError):
            ts[label] = None
    return ts
