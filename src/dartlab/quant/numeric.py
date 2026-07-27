"""quant 수치 강제변환 SSOT. parseNumber.

화면 필터, 프리셋 문자열, scan 행이 섞여 들어오는 자리에서 "숫자면 그대로, 문자열이면
한국식 표기까지 풀어서" 라는 같은 규칙을 세 모듈이 각자 갖고 있었다. 한쪽만 고치면 같은
값이 랭킹과 프리셋과 신호에서 다르게 읽힌다.

문자열 해석 자체는 `core.utils.helpers.parseNumStr` 가 정본이다. 콤마, 회계 괄호 음수,
퍼센트, 세모 표기를 그쪽이 안다. 여기가 더하는 것은 이미 숫자인 값을 문자열로 돌리지 않고
바로 통과시키는 것 하나뿐이다. 그래서 `True` 는 1.0 이 되고, 문자열 "True" 는 None 이다.
"""

from __future__ import annotations

from typing import Any


def parseNumber(value: Any) -> float | None:
    """숫자면 그대로 float, 문자열이면 한국식 표기까지 풀어서 float. 실패는 None.

    Args:
        value: 숫자, 숫자 문자열, None 중 하나.

    Returns:
        float. 읽을 수 없으면 None.
    """
    if isinstance(value, (int, float)):
        return float(value)
    from dartlab.core.utils.helpers import parseNumStr

    return parseNumStr(value)
