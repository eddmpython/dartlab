"""금융환경지수(Financial Conditions Index) — GS 방식 5변수 z-score.

순수 데이터 + 판정 함수. numpy만 사용.
core/ 계층 소속 — macro/liquidity에서 소비.

학술 근거:
- Hatzius et al. (2010): "Financial Conditions Indexes: A Fresh Look"
- Goldman Sachs FCI: 5변수 GDP 임팩트 가중치
- Chicago Fed NFCI: 105변수 DFM (FRED에서 직접 소비 가능)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FCIResult:
    """금융환경지수 결과."""

    value: float  # FCI 값 (양수=긴축, 음수=완화. NFCI와 동일 부호)
    regime: str  # "tight" | "neutral" | "loose"
    regimeLabel: str  # "긴축" | "중립" | "완화"
    components: dict[str, float]  # 개별 변수 z-score
    description: str


# GS FCI 방식 가중치 (GDP 1년 임팩트 기반 근사)
_WEIGHTS_US = {
    "policy_rate": 0.35,
    "long_rate": 0.15,
    "credit_spread": 0.25,
    "equity": 0.15,  # 역수: 주가 하락 = 긴축
    "fx": 0.10,  # 달러 강세 = 긴축
}

_WEIGHTS_KR = {
    "policy_rate": 0.30,
    "long_rate": 0.20,
    "credit_spread": 0.25,
    "equity": 0.15,
    "fx": 0.10,
}


def calcFCI(
    variables: dict[str, list[float]],
    *,
    market: str = "US",
) -> FCIResult:
    """금융환경지수 계산 — 5변수 z-score 가중 합산.

    Args:
        variables: 각 변수의 시계열 (최근 24개월+ 권장)
            - policy_rate: 정책금리 시계열
            - long_rate: 장기금리(10Y) 시계열
            - credit_spread: HY 스프레드 시계열
            - equity: 주가지수 YoY% 시계열 (양수=상승)
            - fx: 달러인덱스(또는 USDKRW) 시계열
        market: "US" | "KR"

    Returns:
        FCIResult: FCI 값 + 구간 + 구성요소
    """
    weights = _WEIGHTS_US if market.upper() == "US" else _WEIGHTS_KR
    components: dict[str, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for key, weight in weights.items():
        series = variables.get(key)
        if series is None or len(series) < 6:
            continue

        arr = np.array(series, dtype=np.float64)
        arr = arr[~np.isnan(arr)]
        if len(arr) < 6:
            continue

        mean = float(np.mean(arr))
        std = float(np.std(arr))
        if std < 1e-10:
            continue

        current = float(arr[-1])
        z = (current - mean) / std

        # 주가는 역수: 주가 하락 = 긴축(양수)
        if key == "equity":
            z = -z

        components[key] = round(z, 3)
        weighted_sum += z * weight
        total_weight += weight

    if total_weight == 0:
        return FCIResult(0.0, "neutral", "데이터부족", {}, "FCI 계산 불가")

    fci = weighted_sum / total_weight

    if fci > 0.5:
        regime, label = "tight", "긴축"
        desc = f"FCI {fci:+.2f} — 금융환경 긴축"
    elif fci < -0.5:
        regime, label = "loose", "완화"
        desc = f"FCI {fci:+.2f} — 금융환경 완화"
    else:
        regime, label = "neutral", "중립"
        desc = f"FCI {fci:+.2f} — 금융환경 중립"

    return FCIResult(
        value=round(fci, 3),
        regime=regime,
        regimeLabel=label,
        components=components,
        description=desc,
    )
