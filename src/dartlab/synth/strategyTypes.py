"""전략 판정 결과 타입과 여러 전략이 되풀이하는 판정 모양.

40 전략 중 열셋이 "필드가 A 면 강세, B 면 약세, 아니면 중립" 이라는 똑같은 모양이었고,
둘은 수출 채산성 신호를 접두어로 읽는 다섯 줄을 글자 그대로 나눠 갖고 있었다. 그 모양을
여기 한 번만 적어 둔다.

임계값 비교처럼 모양이 다른 판정에는 일부러 적용하지 않았다. 비슷해 보인다고 억지로 한
함수에 밀어 넣으면 조건이 바뀔 때 그 함수가 특수 경우를 모으는 자리가 된다.

`strategyRules` 와 `strategyGroups` 가 함께 쓰는 잎 모듈이라 둘 사이 순환이 생기지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySignal:
    """투자전략 판정 결과."""

    id: int  # 전략 번호 (1-40)
    name: str  # 전략 이름
    active: bool | None  # True=활성, False=비활성, None=판별불가
    direction: str  # "bullish" | "bearish" | "neutral" | "na"
    strength: float  # 0.0~1.0 (신호 강도)
    confidence: str  # "high" | "medium" | "low"
    description: str  # 현재 상황 해석


def _sig(
    id: int,
    name: str,
    active: bool | None,
    direction: str,
    description: str,
    *,
    strength: float = 0.5,
    confidence: str = "medium",
) -> StrategySignal:
    """전략 신호 생성 헬퍼."""
    if active is None or active is False:
        strength = 0.0
        confidence = "low"
    return StrategySignal(id, name, active, direction, round(strength, 2), confidence, description)


def _matchDirection(value: object, *, bullish: tuple, bearish: tuple) -> str:
    """라벨 값 하나를 강세/약세 집합에 대조해 direction 으로 옮긴다.

    40 전략 중 13 개가 "이 필드가 A 면 강세, B 면 약세, 아니면 중립" 이라는 똑같은
    모양을 쓴다. 같은 삼항식을 열세 번 늘어놓으면 라벨이 하나 늘 때마다 열세 곳을
    같이 고쳐야 해서, 규칙의 모양 자체에 이름을 붙여 뽑았다. 임계값 비교나 접두사
    매칭처럼 모양이 다른 전략은 여기 얹지 않고 제자리에 둔다.
    """
    if value in bullish:
        return "bullish"
    if value in bearish:
        return "bearish"
    return "neutral"


def _exportProfitDirection(exportProfit: dict) -> str:
    """수출 채산성 신호 문자열을 direction 으로 옮긴다.

    전략 10 과 31 이 같은 exportProfit.signal 을 글자 하나 다르지 않은 규칙으로
    읽어 판정식이 두 곳에 복제돼 있었다. 접두사 매칭이라 라벨 집합 대조
    (_matchDirection)로는 대체되지 않아 전용 판정기로 모은다.
    """
    signal = exportProfit.get("signal", "")
    if signal.startswith("positive") or signal.startswith("strong_positive"):
        return "bullish"
    if "negative" in signal:
        return "bearish"
    return "neutral"
