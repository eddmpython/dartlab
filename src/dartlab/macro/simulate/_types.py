"""거시 시뮬레이션 엔진 자료형. frozen dataclass SSOT.

BVAR 적합과 시뮬레이션 결과 컨테이너다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

# 변수 변환 코드 → Minnesota prior 자기1차계수 δ.
# 'level'      : 원값(금리·스프레드 — 지속). δ=0.8.
# 'logdiff100' : 100·Δlog(지수 → 월간 % 성장). δ=0(성장률 ≈ 백색).
DELTA_BY_TRANSFORM = {"level": 0.8, "logdiff100": 0.0}


@dataclass(frozen=True)
class VarSpec:
    """BVAR 단일 변수 사양.

    Args:
        seriesId: FRED/ECOS 시리즈 id.
        label: 표시 라벨(한국어).
        transform: 'level' | 'logdiff100'.
    """

    seriesId: str
    label: str
    transform: str


@dataclass(frozen=True)
class BvarFit:
    """자연켤레 Minnesota BVAR 사후 적합.

    bPost      : (k, n) 사후 계수 평균. k = n·p + 1(절편 마지막 열).
    sPost      : (n, n) 역위샤트 척도행렬.
    nuPost     : 역위샤트 자유도.
    xtxInv     : (k, k) 행렬정규 좌측 (X*'X*)^{-1}.
    sigmaHat   : (n, n) 사후평균 잔차공분산 = sPost / (nuPost - n - 1).
    p, n       : lag 차수·변수 수.
    specs      : 변수 사양(순서 = 행렬 변수축).
    lastLevels : (n,) 추정 끝 원시 레벨(logdiff 누적 환산용).
    endYm      : 추정 마지막 관측 'YYYY-MM'.
    nObs       : 추정 표본 수(변환 후 행).
    """

    bPost: np.ndarray
    sPost: np.ndarray
    nuPost: float
    xtxInv: np.ndarray
    sigmaHat: np.ndarray
    p: int
    n: int
    specs: tuple[VarSpec, ...]
    lastLevels: np.ndarray
    endYm: str
    nObs: int


@dataclass(frozen=True)
class MacroSimResult:
    """거시 forward 시뮬 결과 — JSON 직렬화(macro/sim/{market}.json) 원천.

    status='ok' 외에는 fan/irf/regimePath 가 빈 dict 이고 missing 에 사유.
    """

    market: str
    status: str
    asOf: str
    horizon: int
    model: dict[str, Any]
    fan: dict[str, Any]
    irf: dict[str, Any]
    regimePath: dict[str, Any]
    missing: list[dict[str, Any]] = field(default_factory=list)
    scenarios: list[dict[str, Any]] = field(default_factory=list)

    def toPayload(self) -> dict[str, Any]:
        """JSON 친화 dict(numpy 제거)."""
        return {
            "market": self.market,
            "status": self.status,
            "asOf": self.asOf,
            "horizon": self.horizon,
            "model": self.model,
            "fan": self.fan,
            "irf": self.irf,
            "regimePath": self.regimePath,
            "scenarios": self.scenarios,
            "missing": self.missing,
        }
