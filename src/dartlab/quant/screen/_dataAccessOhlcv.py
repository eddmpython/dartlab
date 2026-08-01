"""quant 공용 헬퍼: OHLCV fetch + numpy 변환 + 신호 시리즈 어댑터."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    import polars as pl

from dartlab.core.polarsUtil import isEmptyDf
from dartlab.synth.marketDataAccess import fetchOhlcv as fetchOhlcvShared

log = logging.getLogger(__name__)


def fetchOhlcv(stockCode: str, **kwargs: Any) -> "pl.DataFrame | None":
    """gather("price")로 OHLCV 수집: 실패 시 None.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: "005930", "AAPL").
    **kwargs
        GatherEntry 전달 인자 (start, market 등).

    Returns
    -------
    pl.DataFrame | None
        date : date: 거래일
        open : float: 시가 (원)
        high : float: 고가 (원)
        low : float: 저가 (원)
        close : float: 종가 (원)
        volume : int: 거래량 (주)
        수집 실패 시 None.

    Requires:
        L1 gather provider (KR KRX 또는 US Yahoo Finance) 활성.

    Raises:
        없음. 모든 실패는 None 반환 + warning 로그.
    """
    # 수집 자체는 L1.5 `synth.marketDataAccess` 가 정본이다. 예전에는 같은 여섯 줄을
    # 여기서도 갖고 있어서, 한쪽만 예외를 더 잡으면 같은 종목이 엔진에 따라 다르게 비었다.
    return fetchOhlcvShared(stockCode, **kwargs)


def fetchBenchmark(market: str = "KR", **kwargs: Any) -> "pl.DataFrame | None":
    """벤치마크 OHLCV 수집: KR=KRX 지수, US=S&P500.

    Parameters
    ----------
    market : str
        "KR" / "KOSPI" / "KOSDAQ" 또는 "US".
    **kwargs
        ``stockCode``, ``benchmark``, ``start``, ``end`` 등.

    Returns
    -------
    pl.DataFrame | None
        date : date: 거래일
        open : float: 시가
        high : float: 고가
        low : float: 저가
        close : float: 종가
        volume : int: 거래량
        수집 실패 시 None.

    Example:
        >>> df = fetchBenchmark("KR")
        >>> df.columns
        ['date', 'open', 'high', 'low', 'close', 'volume']

    Requires:
        gather provider 활성 + 벤치마크 시리즈 등록.

    Raises:
        없음. 실패는 None.
    """
    try:
        from dartlab.quant.benchmark.data import fetchBenchmarkOhlcv

        stockCode = kwargs.pop("stockCode", None)
        benchmark = kwargs.pop("benchmark", None)
        benchmarkMode = kwargs.pop("benchmarkMode", "market")
        return fetchBenchmarkOhlcv(
            stockCode,
            market=market,
            benchmark=benchmark,
            benchmarkMode=benchmarkMode,
            **kwargs,
        )
    except (ImportError, ValueError, TypeError, RuntimeError):
        log.warning("벤치마크 fetch 실패: %s", market)
        return None


def ohlcvToArrays(df) -> dict:
    """Polars OHLCV DataFrame → numpy 배열 dict.

    Capabilities:
        - date 오름차순 정렬로 시계열 형성 순서 보장
        - open/high/low/close/volume 컬럼을 float64 numpy 변환
        - date 컬럼은 list 로 보존 (날짜 객체 형식 유지)

    Args:
        df: pl.DataFrame: OHLCV (date/open/high/low/close/volume).

    Returns:
        dict: keys ``open/high/low/close/volume/date``. 빈 df 시 ``{}``.

    Guide:
        Quant signal/regime 모듈 (technical indicators, chartPatterns) 의 표준 입력 변환.

    When:
        Numpy 기반 indicator 계산 + AI technical 답변.

    How:
        ``isEmptyDf`` skip → date 정렬 → 각 컬럼 ``to_numpy().astype(np.float64)``.

    Requires:
        df 가 polars DataFrame.

    Raises:
        없음. 누락 컬럼 자동 skip.

    Example:
        >>> arr = ohlcvToArrays(df)
        >>> arr["close"].shape
        (252,)

    See Also:
        - fetchOhlcv : 원본 DataFrame 소스
        - detectChartPatterns : numpy 소비자

    AIContext:
        Technical signal 계산 직전 변환. AI quant axis 답변 체인의 표준 단계.
    """
    import numpy as np

    if isEmptyDf(df):
        return {}

    if "date" in df.columns:
        df = df.sort("date")

    result = {}
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            result[col] = df.get_column(col).to_numpy().astype(np.float64)

    if "date" in df.columns:
        result["date"] = df.get_column("date").to_list()

    return result


def tomMask(dates) -> "Any":
    """Turn-of-the-Month boolean mask: KR 캘린더 시즌신호.

    KOSDAQ 에서 학술 검증된 월말 3거래일 + 월초 3거래일 효과를 boolean 시계열로 반환.
    학술 근거: Lakonishok-Smidt 1988, Korean Journal of Finance (KOSDAQ TOM, 2018+).

    seasonalKR 스타일 외에 다른 곳에서 만들지 말 것 (SSOT).

    Capabilities:
        - 일자 시퀀스 → ``day ≤ 3 or day ≥ 25`` boolean ndarray
        - TOM 효과 (월말·월초 abnormal return) 진입 마스크

    Args:
        dates: ``list[date]`` 또는 polars Date Series: OHLCV 의 date 컬럼.

    Returns:
        numpy.ndarray[bool]: 길이 N. 월말 3 일 / 월초 3 일 True.

    Guide:
        seasonalKR 스타일의 진입 게이트. 다른 위치에서 재구현 금지 (SSOT).

    When:
        시즌 alpha + AI calendar effect 답변.

    How:
        list comprehension ``d.day ≤ 3 or d.day ≥ 25`` → np.bool_ array.

    Requires:
        dates 의 각 원소가 ``.day`` 속성 보유 (date/datetime).

    Raises:
        없음. 빈 입력 시 빈 array.

    Example:
        >>> from datetime import date
        >>> tomMask([date(2026, 1, 1), date(2026, 1, 15), date(2026, 1, 28)])
        array([ True, False,  True])

    See Also:
        - strategy.styles.seasonalKR : 본 mask 의 유일 호출자
        - extractSignalSeries : 호환 signal wrapper

    AIContext:
        시즌 alpha 답변 시 TOM 효과 활성 일자 인용.
    """
    import numpy as np

    days = [d.day for d in dates]
    return np.array([(d <= 3 or d >= 25) for d in days], dtype=np.bool_)


def extractSignalSeries(arr: dict, fn, *, key: str | None = None, **kwargs) -> "np.ndarray | None":
    """벡터 신호 함수를 OHLCV 배열에 적용해 시계열 반환 (SSOT).

    Strategy DSL 이 dict-only analyze_xxx 함수의 시계열 분기 안에서 호출하는 단일
    공용 헬퍼. 다른 위치에 비슷한 wrapper 만들지 말 것.

    Capabilities:
        - inspect 로 ``fn`` 의 시그니처 자동 분석 + arr/kwargs 에서 대응 입력 매칭
        - 결과를 ``{key or fn.__name__: NDArray}`` 단일 컬럼 dict 로 정규화

    Args:
        arr: ``ohlcvToArrays`` 결과 dict (close/high/low/volume/date).
        fn: ``signals.py`` / ``indicators.py`` 의 v* 함수 (시그니처 자동 감지).
        key: 결과 컬럼 명. None 이면 ``fn.__name__``.
        **kwargs: fn 에 전달할 추가 인자.

    Returns:
        dict ``{key: NDArray}``: 길이 보존.

    Guide:
        Strategy DSL 의 v*-함수 시계열 분기 단일 SSOT. 다른 위치에 비슷한 wrapper 금지.

    When:
        Strategy DSL 의 시계열 신호 합성 + AI 백테스트 답변.

    How:
        ``inspect.signature(fn).parameters`` 순회 → arr[param] 또는 kwargs[param] 매칭
        → 나머지 kwargs 전달.

    Requires:
        arr 에 close 컬럼 + fn 이 callable + 시그니처 readable.

    Raises:
        없음. close 부재 또는 빈 arr 시 ``{}``.

    Example:
        >>> def vsma(close, n=20): ...
        >>> out = extractSignalSeries(arr, vsma, n=50)
        >>> out["vsma"].shape
        (252,)

    See Also:
        - strategy.signal : 신호 함수 모음
        - ohlcvToArrays : arr 생성

    AIContext:
        DSL 답변 시 v*-함수 결과 시계열 인용 → 백테스트 시뮬레이션 체인.
    """
    import inspect

    if not arr or "close" not in arr:
        return {}
    sig_params = list(inspect.signature(fn).parameters.keys())
    inputs = []
    for p in sig_params:
        if p in arr:
            inputs.append(arr[p])
        elif p in kwargs:
            inputs.append(kwargs.pop(p))
        else:
            break
    out = fn(*inputs, **kwargs)
    return {key or fn.__name__: out}
