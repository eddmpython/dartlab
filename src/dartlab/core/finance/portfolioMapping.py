"""매크로 regime → 자산배분 가중치 매핑.

순수 판정 함수. core/ 계층 소속 — macro/summary에서 소비.

학술 근거:
- Ilmanen (2011): "Expected Returns" — regime-based allocation
- Bridgewater: All-Weather + Pure Alpha regime decomposition
- CFA Institute (2025): "Mind the Cycle: From Macro Shifts to Portfolio Plays"
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AllocationResult:
    """자산배분 가중치 결과."""

    equity: int  # 주식 (%)
    bond: int  # 채권 (%)
    gold: int  # 금 (%)
    cash: int  # 현금 (%)
    regime: str  # 적용된 regime
    rationale: list[str]  # 배분 근거


# ── 기본 배분 테이블 (regime × phase) ──

_BASE_ALLOCATION = {
    # (overall, phase) → (equity, bond, gold, cash)
    ("favorable", "expansion"): (70, 20, 5, 5),
    ("favorable", "recovery"): (60, 25, 5, 10),
    ("favorable", ""): (60, 25, 5, 10),
    ("neutral", "expansion"): (55, 25, 10, 10),
    ("neutral", "recovery"): (50, 30, 10, 10),
    ("neutral", "slowdown"): (40, 35, 15, 10),
    ("neutral", ""): (50, 30, 10, 10),
    ("unfavorable", "slowdown"): (30, 40, 15, 15),
    ("unfavorable", "contraction"): (20, 40, 20, 20),
    ("unfavorable", ""): (25, 40, 20, 15),
}


def regimeToAllocation(macroResult: dict) -> AllocationResult:
    """종합 매크로 결과 → 자산배분 가중치.

    Args:
        macroResult: summary 축의 전체 결과 dict.
            필수 키: overall, cycle.phase
            선택 키: sentiment.fearGreed.score, liquidity.fci, inventory.ismAllocation

    Returns:
        AllocationResult: equity/bond/gold/cash % + 근거
    """
    overall = macroResult.get("overall", "neutral")
    cycle = macroResult.get("cycle") or {}
    phase = cycle.get("phase", "")
    rationale: list[str] = []

    # 기본 배분
    key = (overall, phase)
    if key not in _BASE_ALLOCATION:
        key = (overall, "")
    base = _BASE_ALLOCATION.get(key, (50, 30, 10, 10))
    equity, bond, gold, cash = base
    rationale.append(f"기본: {overall}/{phase or '?'} → 주식{equity}/채권{bond}/금{gold}/현금{cash}")

    # ── 미세 조정 ──

    # 심리: 극단공포 → 주식 비중 상향 (역투자), 극단탐욕 → 주식 하향
    fg = (macroResult.get("sentiment") or {}).get("fearGreed") or {}
    fg_score = fg.get("score")
    if fg_score is not None:
        if fg_score < 20:
            equity = min(equity + 10, 80)
            cash = max(cash - 10, 0)
            rationale.append(f"극단공포({fg_score:.0f}) → 주식 +10%p (역투자)")
        elif fg_score > 80:
            equity = max(equity - 10, 10)
            cash = min(cash + 10, 40)
            rationale.append(f"극단탐욕({fg_score:.0f}) → 주식 -10%p (경계)")

    # FCI: 긴축이면 채권 비중 상향
    fci = (macroResult.get("liquidity") or {}).get("fci") or {}
    fci_regime = fci.get("regime")
    if fci_regime == "tight":
        bond = min(bond + 5, 60)
        equity = max(equity - 5, 10)
        rationale.append("FCI 긴축 → 채권 +5%p")
    elif fci_regime == "loose":
        equity = min(equity + 5, 80)
        bond = max(bond - 5, 10)
        rationale.append("FCI 완화 → 주식 +5%p")

    # 위기 상태: Minsky 과열이면 금 비중 상향
    crisis = macroResult.get("crisis") or {}
    minsky = crisis.get("minskyPhase") or {}
    if minsky.get("phase") in ("overtrading", "discredit"):
        gold = min(gold + 5, 30)
        equity = max(equity - 5, 10)
        rationale.append(f"Minsky {minsky.get('phaseLabel', '')} → 금 +5%p")

    # 정규화 (합계 100%)
    total = equity + bond + gold + cash
    if total != 100:
        diff = 100 - total
        cash = max(cash + diff, 0)

    regime_label = f"{overall}/{phase}" if phase else overall

    return AllocationResult(
        equity=equity,
        bond=bond,
        gold=gold,
        cash=cash,
        regime=regime_label,
        rationale=rationale,
    )
