"""Company 객체에서 계산 입력을 안전하게 꺼내는 접근 primitive SSOT.

L1.5 synth 본체. L2 분석 엔진 다섯(analysis · credit · macro · quant · industry)은 서로
import 하지 못하므로, 둘 이상이 같은 모양으로 쓰는 접근 코드는 여기로 내려온다.
재무비율 스냅샷을 꺼내는 같은 세 줄이 analysis 의 자본구조 축과 credit 의 지표 산술에
따로 있었고, 한쪽만 고치면 같은 회사의 같은 비율을 두 엔진이 다르게 읽었다.

접근 규약: Company 를 import 하지 않고 duck typing 으로만 읽는다. synth 는 provider 를
모르는 자리라 타입을 붙일 수 없고, 붙이면 L1.5 가 L1 구현에 묶인다. `macroCompanyContext`
와 같은 방식이다.

실패 규약: 값이 없거나 계산이 안 되면 예외 대신 None. 비율은 재무제표가 모자라면 아예
만들어지지 않으므로, 부재와 실패를 구분할 방법이 원래부터 없다.
"""

from __future__ import annotations

from typing import Any


def ratiosOf(company: Any):
    """Company 의 재무비율 스냅샷을 꺼낸다. 데이터가 모자라면 None.

    Args:
        company: `_finance.ratios` 를 가진 Company 객체.

    Returns:
        RatioResult 객체. 재무제표가 없거나 비율 계산이 실패하면 None.
    """
    try:
        return company._finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None
