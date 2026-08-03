"""P1a 밸류에이션 격상 게이트 — G1 단위 정합 + DCF de-gate (offline 결정론).

valuation uplift의 현재 실행 계약을 검증한다.
본 파일 = 순수/offline 게이트(네트워크·Company 로드 불요). G2 백테스트(historical price)·
full calcDFV sanity(credit/CHS)는 영속 이벤트루프 필요 → CI/통합에서 별도(requires_data).

검증 대상:
- G1 단위 항등: reinvestmentIdentity round-trip · ROIC→WACC fade 단조수렴 ·
  terminal 무료성장 차단 · reverse-DCF 항등(solve∘forward).
- DCF de-gate: 실 캡처데이터(005930 calcRoicTimeline)로 펀더멘털 anchor(g=reinvest×ROIC
  fade)가 naive 고성장 대비 과대평가를 교정(new<old) + 터미널 의존 감소(TVshare↓).
"""

from __future__ import annotations

from dartlab.analysis.valuation._dFVDrivers import _estimateReinvestRate
from dartlab.analysis.valuation.consistency import calcCashFlowConsistency
from dartlab.analysis.valuation.dcf import multiStageDcf
from dartlab.analysis.valuation.priceImplied import _bisectImpliedGrowth, _dcfFromGrowth
from dartlab.core.utils.calc import reinvestmentIdentity

# 005930 calcRoicTimeline 실출력 (newest→oldest, 원). 2026=당해 미완(roic/nopat None).
SAMSUNG_HIST = [
    {"period": "2026", "roic": None, "nopat": None, "investedCapital": 440276851000000.0},
    {"period": "2025", "roic": 9.9, "nopat": 39834389934609, "investedCapital": 402525590000000.0},
    {"period": "2024", "roic": 6.71, "nopat": 24544470750000, "investedCapital": 365609385000000.0},
    {"period": "2023", "roic": 1.61, "nopat": 4925232000000, "investedCapital": 305974041000000.0},
    {"period": "2022", "roic": 10.35, "nopat": 32532472500000, "investedCapital": 314312974000000.0},
]


def _fadePath(roic0: float, wacc: float, n: int, k: float = 1.0) -> list[float]:
    """ROIC_0 → WACC 수렴 경로 (buildReinvestmentPath 와 동일 수식)."""
    return [roic0 + (wacc - roic0) * (t / n) ** k for t in range(1, n + 1)]


# ── G1 단위 정합 ──


def test_g1_reinvestment_identity_roundtrip():
    ri = reinvestmentIdentity(growthRatePct=8.0, roicPct=16.0)
    assert ri is not None
    assert abs(ri["impliedReinvestRate"] - 0.5) < 1e-9
    assert abs(0.5 * 16.0 - 8.0) < 1e-9  # g = reinvest × ROIC


def test_g1_fade_converges_monotonically_to_wacc():
    path = _fadePath(20.0, 8.0, 5)
    assert all(path[i] >= path[i + 1] for i in range(len(path) - 1)), "fade 단조 감소"
    assert abs(path[-1] - 8.0) < 0.1, "마지막 ROIC == WACC"


def test_g1_terminal_no_free_growth():
    gInf, roicInf = 3.0, 10.0
    terminalReinvest = gInf / roicInf
    assert abs(terminalReinvest * roicInf - gInf) < 1e-9  # 무료성장 0


def test_g1_reverse_dcf_identity():
    baseRev, fcfMargin, wacc, tg, h = 1.0e13, 0.12, 0.09, 0.02, 3
    gTrue = 0.10
    ev = _dcfFromGrowth(baseRev, fcfMargin, gTrue, wacc, tg, h)
    gSolved = _bisectImpliedGrowth(
        ev=ev, baseRevenue=baseRev, fcfMargin=fcfMargin, wacc=wacc, terminalGrowth=tg, horizon=h
    )
    assert gSolved is not None
    assert abs(gSolved - gTrue) < 1e-3
    evRecheck = _dcfFromGrowth(baseRev, fcfMargin, gSolved, wacc, tg, h)
    assert abs(evRecheck / ev - 1) < 0.01


# ── 재투자율 추정 (실 캡처데이터) ──


def test_estimate_reinvest_rate_real_data():
    r = _estimateReinvestRate(SAMSUNG_HIST)
    assert r is not None
    assert 0.0 <= r <= 0.9


def test_estimate_reinvest_rate_skips_incomplete_year():
    # 2026 nopat None → 그 pair 제외, 그래도 유효 pair 로 산출.
    assert _estimateReinvestRate(SAMSUNG_HIST) is not None
    # 데이터 전무면 None.
    assert _estimateReinvestRate([{"roic": None, "nopat": None, "investedCapital": None}]) is None


# ── DCF de-gate: 과대평가 교정 ──


def test_dcf_degate_corrects_naive_overvaluation():
    """펀더멘털 anchor(g=reinvest×ROIC fade) < naive 고성장 → DCF 과대 교정 + TVshare 감소."""
    reinvest = _estimateReinvestRate(SAMSUNG_HIST)
    roic0 = next(h["roic"] for h in SAMSUNG_HIST if h["roic"] is not None)
    wacc, naive = 8.72, 12.0
    growth = [max(-5.0, min(reinvest * r, 25.0)) for r in _fadePath(roic0, wacc, 8)]
    fundG = reinvest * roic0
    assert fundG < naive, "펀더멘털 성장이 naive 외삽보다 보수적"

    baseFcf, netDebt, shares = 30e12, -30e12, 5.97e9
    old = multiStageDcf(
        baseFcf=baseFcf,
        growthYears=[5],
        growthRates=[naive],
        terminalGrowthRate=2.5,
        wacc=wacc,
        netDebt=netDebt,
        shares=shares,
    )
    new = multiStageDcf(
        baseFcf=baseFcf,
        growthYears=[1] * len(growth),
        growthRates=growth,
        terminalGrowthRate=2.5,
        wacc=wacc,
        netDebt=netDebt,
        shares=shares,
    )
    assert new["perShare"] < old["perShare"], "naive 과대평가 해소"
    assert new["tvShare"] < old["tvShare"], "터미널 의존 감소(fade 효과)"


# ── G3 민감도 그리드 (순수 multiStageDcf, offline) ──


def test_g3_sensitivity_grid_monotonic():
    """WACC×g 민감도 격자 — WACC↑→가치↓, g↑→가치↑ 단조성 + TVshare 폭주 차단."""
    baseFcf, netDebt, shares = 30e12, -30e12, 5.97e9

    def _ps(waccPct: float, gPct: float) -> float:
        r = multiStageDcf(
            baseFcf=baseFcf,
            growthYears=[8],
            growthRates=[gPct],
            terminalGrowthRate=2.5,
            wacc=waccPct,
            netDebt=netDebt,
            shares=shares,
        )
        return r["perShare"]

    waccs = [7.0, 8.0, 9.0, 10.0, 11.0]
    growths = [4.0, 6.0, 8.0, 10.0, 12.0]
    # WACC 단조 감소 (g 고정)
    for g in growths:
        col = [_ps(w, g) for w in waccs]
        assert all(col[i] > col[i + 1] for i in range(len(col) - 1)), f"WACC↑→가치↓ 위반 (g={g})"
    # g 단조 증가 (WACC 고정)
    for w in waccs:
        row = [_ps(w, g) for g in growths]
        assert all(row[i] < row[i + 1] for i in range(len(row) - 1)), f"g↑→가치↑ 위반 (WACC={w})"
    # TVshare 폭주 차단 — 중앙 가정에서 < 0.85
    mid = multiStageDcf(
        baseFcf=baseFcf,
        growthYears=[8],
        growthRates=[8.0],
        terminalGrowthRate=2.5,
        wacc=9.0,
        netDebt=netDebt,
        shares=shares,
    )
    assert mid["tvShare"] < 0.85, f"TVshare 과대 {mid['tvShare']:.2f}"


# ── G5 정합성 (순수 calcCashFlowConsistency, offline) ──


def test_g5_growth_equation_consistency():
    """g=reinvest×ROIC 정합 입력은 Growth Equation critical 0, 위반 입력은 flag."""
    reinvest = _estimateReinvestRate(SAMSUNG_HIST)
    roic0 = next(h["roic"] for h in SAMSUNG_HIST if h["roic"] is not None)
    fundG = reinvest * roic0  # 정합 성장

    okRes = calcCashFlowConsistency(
        roicPct=roic0,
        growthRatePct=fundG,
        reinvestmentRatePct=reinvest * 100,
        terminalGrowthPct=2.5,
        waccPct=8.72,
        primaryModel="dcf2stage",
        modelsUsed=3,
        country="KR",
    )
    assert okRes is not None and "score" in okRes
    gFlags = [f for f in okRes.get("flags", []) if "성장" in f.get("rule", "") or "growth" in f.get("rule", "").lower()]
    crit = [f for f in gFlags if f.get("severity") == "critical"]
    assert not crit, f"정합 성장인데 critical Growth Equation flag: {crit}"

    # 위반: 성장이 reinvest×ROIC 를 크게 초과
    badRes = calcCashFlowConsistency(
        roicPct=roic0,
        growthRatePct=roic0 * 2,  # reinvest>1 함의 — 불가능
        reinvestmentRatePct=reinvest * 100,
        terminalGrowthPct=2.5,
        waccPct=8.72,
        primaryModel="dcf2stage",
        modelsUsed=3,
        country="KR",
    )
    assert badRes["score"] <= okRes["score"], "위반 입력 score 가 정합보다 높음(검증 실패)"


# ── through-cycle ROIC 정규화 (사이클 peak 과대평가 차단) — 실 캡처 ROIC 이력 ──

HYNIX_ROIC = [31.08, 25.9, -10.4, 5.8, 14.82, 7.35, 4.63]  # 000660 — HBM peak + 2023 메모리 불황
SAMSUNG_ROIC = [9.9, 6.71, 1.61, 10.35, 13.69, 10.15, 8.21]  # 005930 — 안정


def test_through_cycle_roic_tames_cyclical_peak():
    """고-ROIC 사이클 peak(하이닉스 31%)을 through-cycle median(7.35)으로 정규화 → 성장 절반↓."""
    from dartlab.analysis.valuation._dFVDrivers import _growthPathFromRoics

    reinvest = 0.9
    hy = _growthPathFromRoics(HYNIX_ROIC, reinvest, 9.69, 8)
    assert hy is not None
    assert hy["roicAnchor"] == 7.35, "through-cycle median anchor (peak 31.08 아님)"
    fundGNorm = reinvest * hy["roicAnchor"]
    fundGPeak = reinvest * HYNIX_ROIC[0]  # 옛 latest-peak anchor
    assert fundGNorm < fundGPeak * 0.5, "peak 대비 절반 이하로 정규화"


def test_through_cycle_roic_leaves_stable_firm_unchanged():
    """안정 종목(삼성)은 median ≈ latest → 정규화 영향 거의 없음."""
    from dartlab.analysis.valuation._dFVDrivers import _growthPathFromRoics

    sam = _growthPathFromRoics(SAMSUNG_ROIC, 0.9, 8.72, 8)
    assert sam is not None
    assert abs(sam["roicAnchor"] - SAMSUNG_ROIC[0]) < 1.5, "median ≈ latest (무변)"


def test_through_cycle_roic_none_for_structural_loss():
    """through-cycle ROIC ≤ 0(구조적 적자) → None (성장 anchor 불가, 호출부 폴백)."""
    from dartlab.analysis.valuation._dFVDrivers import _growthPathFromRoics

    assert _growthPathFromRoics([-5.0, -2.0, -8.0, 1.0], 0.5, 9.0, 8) is None
