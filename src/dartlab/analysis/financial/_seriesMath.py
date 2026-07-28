"""재무 시계열 값 계산 primitive SSOT. 전기대비 증감률과 최신 유효값.

수익성·성장·안정성·효율·ROIC 다섯 축이 증감률 세 줄을 각자 갖고 있었고, insight 의
이상징후와 지배구조 신호가 최신 유효값 네 줄을 각자 갖고 있었다. 한쪽만 고치면 같은
재무 시계열을 읽는 두 축이 서로 다른 답을 냈다.

수치 규약:
- 증감률은 직전값이 None 또는 0 이면 None. 예외를 던지지 않는다.
- 직전값의 절대값으로 나눠 부호를 보존한다 (적자 축소가 음수 성장으로 뒤집히지 않는다).
- 소수 둘째 자리 반올림은 표시 단위가 % 라서 붙어 있다.

``dartlab.core.ratios._yoy`` 는 이름만 같은 다른 함수다. 그쪽은 시계열과 인덱스를 받아
``yoyPct`` 로 위임하며 부호 전환을 None 으로 막는다. 이쪽은 스칼라 둘만 받고 부호가
바뀌어도 그대로 계산한다. 둘을 합치면 값이 달라지므로 따로 둔다.
"""

from __future__ import annotations


def _yoy(cur, prev) -> float | None:
    """전기대비 증감률 계산.

    Returns
    -------
    float | None
        YoY 변화율 (%). 계산 불가 시 None.
    """
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _latestNotNone(values: list):
    """뒤에서부터 첫 non-None 값. 전부 결측이면 None.

    Parameters
    ----------
    values : list
        시계열 값 목록. 뒤쪽이 최신이다.

    Returns
    -------
    Any | None
        가장 최근 non-None 값.
    """
    for v in reversed(values):
        if v is not None:
            return v
    return None
