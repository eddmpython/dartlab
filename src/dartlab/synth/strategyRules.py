"""40개 투자전략 룰엔진: 순수 판정 함수.

각 전략은 매크로 데이터로부터 "활성/비활성/해당없음"을 판별하는 순수 함수다.
L1.5 synth SSOT (macro/summary 가 소비).

구성은 3 층이다. 본 모듈의 ``evaluateStrategies`` 가 macroData 를 sub-dict 로 풀어
``strategyGroups`` 의 그룹 판정기를 순서대로 잇고, 그룹 판정기 열하나가 전략 1~40 을 나눠
가지며, ``strategyTypes`` 가 결과 타입과 되풀이되는 판정 모양을 담는다.
"""

from __future__ import annotations

from dartlab.synth.strategyGroups import (
    _capexPressureSignals,
    _creditCycleSignals,
    _currencyLinkedSignals,
    _cyclePhaseSignals,
    _dollarStrengthSignals,
    _financeSpreadSignals,
    _growthLinkageSignals,
    _ismLiquiditySignals,
    _leadingIndicatorSignals,
    _monetaryPolicySignals,
    _tradeConditionSignals,
)
from dartlab.synth.strategyTypes import StrategySignal

__all__ = ["StrategySignal", "evaluateStrategies"]


def evaluateStrategies(macroData: dict) -> list[StrategySignal]:
    """40개 투자전략 일괄 평가 → StrategySignal 리스트.

    Capabilities:
        macro/summary 의 9 축 결과 (cycle/rates/assets/sentiment/liquidity/
        forecast/crisis/inventory/trade) 를 받아 40 개 투자전략 룰을 한
        번에 평가. 각 전략은 active/direction/strength/confidence 4 필드로
        표현. macro/summary 의 strategy lens 가 본 결과를 그대로 노출.

    Args:
        macroData: summary 의 전체 dict.
            keys: ``cycle``, ``rates``, ``assets``, ``sentiment``,
            ``liquidity``, ``forecast``, ``crisis``, ``inventory``,
            ``trade``. 일부 키 누락 가능하며 해당 전략은 ``active=False``.

    Returns:
        list[StrategySignal] (길이 40, 순서 고정):
            - ``id`` (int): 1~40 전략 번호
            - ``name`` (str): 전략 한국어 라벨
            - ``active`` (bool|None): 평가 가능 여부
            - ``direction`` (str): ``"bullish"``/``"bearish"``/``"neutral"``/``"na"``
            - ``strength`` (float): 0.0~1.0
            - ``confidence`` (str): ``"high"``/``"medium"``/``"low"``
            - ``description`` (str): 현재 시그널 해석

    Raises:
        없음.

    Example:
        >>> from dartlab.macro.summary import summary
        >>> macro = summary()
        >>> signals = evaluateStrategies(macro)
        >>> [s for s in signals if s.active and s.direction == "bullish"]

    Guide:
        40 전략은 7 그룹으로 분류: A. 경기순환(1~9), B. 무역/환율(10~14),
        C. 금리(15~22), D. 달러/외환(23~27), E. 신용/설비(28~33),
        F. ISM/유동성(34~39), G. 금융업(40). 각 룰은 macroData 의 특정
        sub-dict 키 의존이라 키가 없으면 자동 inactive.

    SeeAlso:
        - ``dartlab.macro.summary.summary``
        - ``dartlab.synth.scenario`` (시나리오 매칭)

    Requires:
        macroData 가 macro/summary 출력 스키마. 빈 dict 호출 가능 (모든
        전략 inactive 로 반환).

    AIContext:
        결과 리스트를 UI 에 표시할 때 ``confidence="high"`` 만 필터링
        권장. low confidence 는 데이터 부재 또는 신호 약함을 의미하므로
        과해석 회피. 같은 시그널이 여러 전략에서 일관된 방향을 가리키면
        해당 macro 신호가 강한 증거가 됨.

    LLM Specifications:
        AntiPatterns:
            - 40 전략 결과 dict 를 곧바로 portfolio weight 로 변환 금지.
              본 함수는 macro lens 의 정성 판단이지 quant trade rule 이 아님.
            - direction 만 보고 매매 결정 금지. confidence + active + macro
              cross-check 셋 다 확인 필수.
        OutputSchema:
            list[StrategySignal] 길이 40 고정. 순서 보존.
            ``StrategySignal{id:int, name:str, active:bool|None, direction:str,
            strength:float, confidence:str, description:str}``.
        Prerequisites:
            macroData 가 macro/summary 스키마. 일부 키 미존재 허용.
        Freshness:
            macro/summary 의 freshness 에 따름.
        Dataflow:
            macroData → 9 sub-dict 추출 → 40 _sig() 호출 → list 반환.
        TargetMarkets: KR + Global. 일부 전략은 KR 특화 (예: 35, 27).
    """
    cycle = macroData.get("cycle") or {}
    rates = macroData.get("rates") or {}
    macroData.get("sentiment") or {}
    liquidity = macroData.get("liquidity") or {}
    forecast = macroData.get("forecast") or {}
    crisis = macroData.get("crisis") or {}
    inventory = macroData.get("inventory") or {}
    trade = macroData.get("trade") or {}
    assets = macroData.get("assets") or {}

    # 본 함수의 책임은 macroData 를 9 개 sub-dict 로 풀고 그룹 판정기를 정해진
    # 차례로 잇는 것뿐. 판정 규칙은 각 그룹 함수가 갖는다. 잇는 순서는 공개
    # 계약(id 1~40 고정 순서)이라 바꾸지 않는다.
    return [
        *_growthLinkageSignals(rates, forecast, trade),
        *_cyclePhaseSignals(cycle, inventory),
        *_tradeConditionSignals(trade, inventory),
        *_leadingIndicatorSignals(rates, forecast, trade),
        *_monetaryPolicySignals(rates, assets),
        *_dollarStrengthSignals(crisis),
        *_currencyLinkedSignals(rates, assets, trade),
        *_creditCycleSignals(cycle, rates, forecast),
        *_capexPressureSignals(crisis, inventory, trade),
        *_ismLiquiditySignals(cycle, rates, crisis, inventory, assets, liquidity),
        *_financeSpreadSignals(rates),
    ]
