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


def _inferShares(company: Any) -> int | None:
    """기존 calcDcf 결과의 equityValue / perShareValue 로 주식수 역산.

    BS 에 outstanding_shares 가 없는 경우 대응 (KRX 메타 의존 회피).

    Returns
    -------
    int | None
        추정 발행주식수. 역산 실패 시 None.
    """
    try:
        from dartlab.analysis.financial.valuation import calcDcf

        r = calcDcf(company)
        if isinstance(r, dict):
            eq = r.get("equityValue")
            ps = r.get("perShareValue")
            if eq and ps and ps > 0:
                return int(eq / ps)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    return None


def _getCurrentPriceLight(company: Any) -> float | None:
    """현재 주가 추출. gather price 축의 종가 마지막 값.

    예전에는 ``company.currentPrice`` 를 먼저 봤는데 그 이름은 Company 표면에 없어 한 번도
    타지 않았다. 실제로 값을 내던 것은 아래 gather 경로 하나뿐이라 그것만 남겼다.

    Returns
    -------
    float | None
        현재 주가 (원). 조회 실패 시 None.
    """
    try:
        from dartlab.core.di import getMacroProvider

        g = getMacroProvider().getDefaultGather()
        p = g("price", getattr(company, "stockCode", ""))
        if p is not None and hasattr(p, "height") and p.height > 0:
            return float(p["close"][-1])
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
