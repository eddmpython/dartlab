"""스타일 빌드 공통 헬퍼 — OHLCV 페치 + 시장 분기 + length 정렬.

각 스타일 build 함수가 import 해서 보일러플레이트 없이 시작할 수 있게 하는
얇은 공용 모듈. 헬퍼 난립 금지 — 이 파일 외에 styles/ 안에 별도 utility 만들지 말 것.
"""

from __future__ import annotations

import numpy as np

from dartlab.core.market import resolveMarket
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.screen.dataAccess import fetchOhlcv, ohlcvToArrays


def getArrays(company, *, start: str | None = None) -> dict:
    """Company 객체에서 OHLCV → numpy dict 변환.

    Capabilities:
        - company.stockCode + 선택적 start → fetchOhlcv → ohlcvToArrays
        - company._strategy_start fallback 지원

    Args:
        company: dartlab Company 객체 또는 stockCode 속성 가진 stub.
        start: ``"2020-01-01"`` 같이 명시 시 장기 OHLCV.

    Returns:
        dict — ``{open, high, low, close, volume, date}`` 또는 빈 dict.

    Guide:
        모든 styles/*.build 함수의 첫 보일러플레이트. 다른 위치에 비슷한 helper 만들지 말 것.

    When:
        Strategy build 함수 시작 + AI 전략 평가 답변.

    How:
        stockCode 추출 → start fallback → fetchOhlcv → ohlcvToArrays.

    Requires:
        company.stockCode 속성.

    Raises:
        없음 — fetch 실패 시 빈 dict.

    Example:
        >>> arr = getArrays(company, start="2014-01-01")
        >>> arr["close"].shape
        (2789,)

    See Also:
        - safeQuantile : NaN safe 분위
        - screen.dataAccess.fetchOhlcv : 원본 fetcher

    AIContext:
        Strategy 평가 체인의 첫 단계. AI 가 백테스트 답변 시 invisible 호출.
    """
    code = getattr(company, "stockCode", None)
    if not code:
        return {}
    # company 객체에 _strategy_start 속성 있으면 그것도 사용 (옵션)
    s = start or getattr(company, "_strategy_start", None)
    df = fetchOhlcv(code, **({"start": s} if s else {}))
    if isEmptyDf(df):
        return {}
    return ohlcvToArrays(df)


def isKr(company) -> bool:
    """KR 시장 여부.

    Example:
        >>> isKr(company)
        True

    Requires:
        company 가 stockCode 속성 보유.

    Raises:
        없음.
    """
    code = getattr(company, "stockCode", "")
    return resolveMarket(code, "auto") == "KR"


def getStockCode(company) -> str:
    """Company 객체에서 종목코드 추출.

    Parameters
    ----------
    company : Company
        dartlab Company 객체 또는 stockCode 속성 가진 stub.

    Returns
    -------
    str
        종목코드 문자열. 속성 없으면 빈 문자열.

    Example:
        >>> getStockCode(company)
        '005930'

    Requires:
        company 가 stockCode 속성 보유.

    Raises:
        없음.
    """
    return getattr(company, "stockCode", "") or ""


def safeQuantile(arr: np.ndarray, q: float) -> float:
    """NaN-safe quantile.

    Capabilities:
        - NaN 제거 후 np.quantile + 표본 < 10 시 nan 안전 반환
        - 임계값 산출 시 분위 cutoff 표준

    Args:
        arr: 입력 array.
        q: 분위 (0~1).

    Returns:
        float — 분위값 또는 NaN.

    Guide:
        Strategy 임계값 계산용. 표본 ≥ 10 보장 + NaN drop.

    When:
        Strategy 임계 → entry 분위 cut + AI 분위 답변.

    How:
        ``arr[~np.isnan(arr)]`` → ``np.quantile``.

    Requires:
        arr 가 numpy array.

    Raises:
        없음.

    Example:
        >>> safeQuantile(np.array([1, 2, np.nan, 4]), 0.5)
        nan  # n<10

    See Also:
        - getArrays : OHLCV → numpy
        - synth.indicators.* : 분위 입력 indicator

    AIContext:
        Strategy threshold 답변 시 분위 cutoff 인용.
    """
    a = arr[~np.isnan(arr)]
    if len(a) < 10:
        return float("nan")
    return float(np.quantile(a, q))


# 0.10 BC 깸 — snake_case alias 제거.
