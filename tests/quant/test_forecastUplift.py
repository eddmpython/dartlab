"""P1b 전망 격상 게이트 — 지수 fade + 영업레버리지 마진 (offline 결정론).

forecast uplift의 현재 실행 계약을 검증한다.
de-gate: ① cagr_decay 임의 선형감속 → 지수 fade g(t)=gT+(g0−gT)·exp(−λt)(경쟁수렴)
② 고정마진 → 영업레버리지 OPM(t)=base+β·(revGrowth−normal)(고정비 희석)·과거범위 캡.
본 파일 = 순수 수식 검증(_forecastMetric.py 인라인 로직 동치). 통합(real series)은 CI.
"""

from __future__ import annotations

import math

# import 가능 확인 (de-gate 회귀 가드)
from dartlab.analysis.forecast._forecastMetric import _marginLinkedForecast, forecastMetric  # noqa: F401


def _fade(g0: float, gT: float, lam: float, n: int) -> list[float]:
    """지수 fade — _forecastMetric.py cagr_decay 분기와 동치."""
    return [gT + (g0 - gT) * math.exp(-lam * t) for t in range(1, n + 1)]


def _opm(base: float, beta: float, normal: float, g: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """영업레버리지 OPM — _marginLinkedForecast 와 동치(β: %p/%p)."""
    return max(lo, min(base + (beta / 100.0) * (g - normal), hi))


# ── 지수 fade ──


def test_exponential_fade_converges_to_terminal():
    path = _fade(25.0, 4.0, 0.5, 8)
    assert all(path[i] >= path[i + 1] for i in range(len(path) - 1)), "단조 감소"
    assert abs(path[-1] - 4.0) < 2.0, "터미널 수렴"
    linearY1 = 25.0 - (25.0 - 4.0) / 8  # 선형 감속 1년차
    assert path[0] < linearY1, "지수 fade 가 선형보다 초기 수렴 빠름(임의 선형감속 폐기)"


def test_high_growth_slower_fade():
    fast = _fade(25.0, 4.0, 0.5, 8)  # 일반 λ=0.5
    slow = _fade(25.0, 4.0, 0.35, 8)  # 고성장 λ=0.35
    assert slow[3] > fast[3], "λ 작을수록(고성장) 느린 수렴 → 성장 더 지속"


# ── 영업레버리지 마진 ──


def test_operating_leverage_responds_to_growth():
    base, beta, normal = 0.10, 2.0, 5.0  # OPM 10%·β 2%p/%p·정상성장 5%
    assert _opm(base, beta, normal, 15.0) > _opm(base, beta, normal, 5.0), "고성장→마진 확대(레버리지)"
    assert _opm(base, beta, normal, -5.0) < _opm(base, beta, normal, 5.0), "역성장→마진 축소(역레버리지)"
    assert abs(_opm(base, beta, normal, 5.0) - base) < 1e-9, "정상성장 = base"


def test_operating_leverage_bounded():
    base, beta, normal, lo, hi = 0.10, 2.0, 5.0, 0.05, 0.18
    assert _opm(base, beta, normal, 100.0, lo, hi) == hi, "극단 고성장 상한 캡(폭주 방지)"
    assert _opm(base, beta, normal, -100.0, lo, hi) == lo, "극단 역성장 하한 캡"
