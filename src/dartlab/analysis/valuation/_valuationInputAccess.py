"""밸류에이션 입력 확보 primitive SSOT. 주식수 역산 · 현재 주가 · BS 다중 키 값.

``_dFVCalcs`` 와 ``controlSynergy`` 가 주식수 역산 열한 줄을, ``bankDFV`` 와 ``sotp``
가 현재 주가 조회 열두 줄을, ``_dFVTsd`` 와 ``controlSynergy`` 가 BS 값 추출 다섯 줄을
각자 갖고 있었다. 한쪽만 고치면 같은 회사의 같은 순차입금을 두 모델이 다르게 읽는다.

실패 규약: 셋 다 예외를 밖으로 던지지 않는다. 주식수와 주가는 못 구하면 None, BS 값은
못 구하면 0.0 이다. 0.0 은 "차입금 항목이 없다" 는 뜻이라 합산에 그대로 얹힌다.

dartlab 모듈 import 는 전부 함수 안이다. 최상단으로 올리면 ``valuation`` · ``core.di``
와 순환이 되고, 주가 조회 하나 때문에 gather 배선이 무조건 끌려온다.
"""

from __future__ import annotations

from typing import Any


def _inferSharesInput(company: Any, basePeriod: str | None = None) -> dict | None:
    """공시 주식수를 우선하고 최신 계산에서만 DCF 역산을 허용한다."""
    try:
        from dartlab.analysis.financial._companyLookup import _getSharesOutstandingInput

        reported = _getSharesOutstandingInput(company, basePeriod=basePeriod)
        if reported:
            return reported
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    # 과거 기준 계산은 최신 시가총액이나 최신 profile 주식수로 대체하지 않는다.
    if basePeriod is not None:
        return None
    try:
        from dartlab.analysis.financial.valuation import calcDcf

        r = calcDcf(company)
        if isinstance(r, dict):
            eq = r.get("equityValue")
            ps = r.get("perShareValue")
            if eq and ps and ps > 0:
                return {"value": int(eq / ps), "period": None, "source": "calcDcf.latest"}
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    return None


def _inferShares(company: Any, basePeriod: str | None = None) -> int | None:
    """공시 주식수를 얻고 최신 계산에 한해 calcDcf 역산으로 보완한다.

    ``basePeriod`` 가 있으면 그 기간까지 공시된 값만 허용한다. 과거 값이 없을 때
    최신 시가총액 기반 주식수로 대체하지 않는다.

    Returns
    -------
    int | None
        발행주식수. 기간 일치 값을 얻지 못하면 None.
    """
    resolved = _inferSharesInput(company, basePeriod=basePeriod)
    return resolved["value"] if resolved else None


def _getCurrentPriceLight(company: Any) -> float | None:
    """현재 주가 추출. 단일 종목 스냅샷만 조회한다.

    전 종목 1년 가격 패널을 읽으면 투자 브리프 하나가 수 GB를 적재한다. 재무 가치평가가
    공유하는 ``_priceContext``를 사용해 같은 Company 세션에서 단일 종목 API를 한 번만 호출한다.

    Returns
    -------
    float | None
        현재 주가 (원). 조회 실패 시 None.
    """
    try:
        from dartlab.analysis.financial._valuationInputs import _fetchPriceContext

        price = _fetchPriceContext(company)
        if price and price.get("currentPrice") is not None:
            return float(price["currentPrice"])
    except (ImportError, AttributeError, ValueError, TypeError, KeyError):
        pass
    return None


def _balanceValue(data: dict, latest: str, *keys: str) -> float:
    """BS 다중 키에서 최신 기간의 첫 유효 값 추출 (없거나 0 이면 0.0).

    같은 계정을 provider 마다 ``shortterm_borrowings`` · ``short_term_borrowings`` ·
    ``short_term_debt`` 처럼 다르게 부르므로 키를 우선순위 순서로 받는다. 원래는 두
    모듈의 중첩 함수라 ``data`` 와 ``latest`` 를 클로저로 잡았고, 여기서는 인자로 받는다.

    Parameters
    ----------
    data : dict
        snakeId 별 ``{기간: 값}`` 매핑.
    latest : str
        읽을 기간 라벨.
    keys : str
        우선순위 순서의 계정 snakeId 들.

    Returns
    -------
    float
        처음 만난 truthy 값. 전부 없으면 0.0.
    """
    for k in keys:
        v = (data.get(k) or {}).get(latest)
        if v:
            return float(v)
    return 0.0
