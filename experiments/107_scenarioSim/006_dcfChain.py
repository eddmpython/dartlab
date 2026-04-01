"""107-006 — DCF 3년 체인 + 역전 방지 (P3).

문제: 002에서 Bull(CapEx↑) FCF < Bear(CapEx↓) → 적정가 역전.
해결: 3년 ProForma FCF 명시적 할인 + Terminal에서 CapEx = 감가상각 정규화.

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/006_dcfChain.py
"""

from __future__ import annotations

import gc
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


def _qvals(is_df, sid: str, year: str) -> list[float]:
    row = is_df.filter(is_df["snakeId"] == sid)
    if row.height == 0:
        return []
    vals = []
    for q in range(1, 5):
        col = f"{year}Q{q}"
        if col in row.columns:
            v = row[col].to_list()[0]
            vals.append(float(v) if v is not None else 0)
    return vals if len(vals) == 4 else []


def scenarioDCF(projections, wacc_pct: float, terminalGrowth: float = 0.02,
                netDebt: float = 0, shares: int = 1) -> dict:
    """3년 ProForma → DCF 적정가.

    Terminal FCF = OCF - 감가상각 (유지 CapEx = 감가상각 수준으로 정규화).
    """
    wacc = wacc_pct / 100
    if wacc <= terminalGrowth:
        wacc = terminalGrowth + 0.05

    # 명시적 3년 FCF 할인
    pvFcf = 0
    for i, p in enumerate(projections):
        pvFcf += p.fcf / (1 + wacc) ** (i + 1)

    # Terminal: 마지막 연도에서 CapEx = Depreciation으로 정규화
    lastP = projections[-1]
    normalizedCapex = lastP.depreciation  # 유지 CapEx = 감가상각
    normalizedFcf = lastP.ocf - normalizedCapex
    if normalizedFcf <= 0:
        normalizedFcf = lastP.ocf * 0.3  # 안전장치

    tv = normalizedFcf * (1 + terminalGrowth) / (wacc - terminalGrowth)
    pvTv = tv / (1 + wacc) ** len(projections)

    ev = pvFcf + pvTv
    equityValue = ev - netDebt
    perShare = int(equityValue / shares) if shares > 0 else 0

    return {
        "pvFcf": pvFcf,
        "pvTv": pvTv,
        "ev": ev,
        "equityValue": equityValue,
        "perShare": perShare,
        "normalizedFcf": normalizedFcf,
        "terminalValue": tv,
    }


def main():
    print("=" * 70)
    print("107-006 DCF 3년 체인 + 역전 방지")
    print("=" * 70)

    from dartlab import Company
    from dartlab.core.finance.proforma import build_proforma, extract_historical_ratios

    c = Company("005930")
    ts = c.finance.timeseries
    fullSeries = ts[0] if isinstance(ts, tuple) else ts
    periods = ts[1] if isinstance(ts, tuple) else []
    is_df = c.IS

    cutIdx = periods.index("2023-Q4") + 1
    series = {stmt: {k: v[:cutIdx] for k, v in fullSeries[stmt].items()} for stmt in ["IS", "BS", "CF"]}

    ratios = extract_historical_ratios(series)
    rev23 = sum(_qvals(is_df, "sales", "2023"))
    gp23 = sum(_qvals(is_df, "gross_profit", "2023"))
    baseGM = gp23 / rev23 * 100 if rev23 else 0

    # 발행주식수
    shares = 5969782550  # 삼성전자 보통주

    # 3개 시나리오 × 3년 ProForma
    scenarios = [
        ("Bull: 초회복", [22.0, 15.0, 10.0], 0.7),  # 성장 수렴
        ("Base: 회복",   [15.0, 10.0, 7.0],  0.5),
        ("Bear: 지연",   [5.0, 3.0, 2.0],    0.3),
    ]

    print(f"\n  과거 GM: {ratios.gross_margin:.1f}%, 기준연도 GM: {baseGM:.1f}%")

    # ── 002 방식 (1년 FCF) vs 006 방식 (3년 체인) ──
    print(f"\n{'='*70}")
    print(f"  {'시나리오':16s} | {'1년DCF(002)':>12s} | {'3년DCF(006)':>12s} | {'차이':>8s}")
    print(f"  {'-'*56}")

    for label, growthPath, histWeight in scenarios:
        blendedGM = baseGM * (1 - histWeight) + ratios.gross_margin * histWeight

        # 3년 ProForma
        pf3 = build_proforma(
            series,
            revenue_growth_path=growthPath,
            scenario_name=label,
            overrides={"gross_margin": blendedGM},
        )

        # 1년 ProForma (002 방식)
        pf1 = build_proforma(
            series,
            revenue_growth_path=[growthPath[0]],
            scenario_name=label,
            overrides={"gross_margin": blendedGM},
        )

        if not pf3.projections or not pf1.projections:
            print(f"  {label:16s} | ProForma 실패")
            continue

        # 순부채
        p1 = pf1.projections[0]
        netDebt = (p1.short_term_debt + p1.long_term_debt) - p1.cash

        # 002 방식: 1년 FCF → Terminal
        wacc = pf1.wacc
        waccD = wacc / 100
        if waccD <= 0.02:
            waccD = 0.07
        fcf1 = p1.fcf
        tv1 = fcf1 * 1.02 / (waccD - 0.02) if waccD > 0.02 else 0
        ev1 = fcf1 / (1 + waccD) + tv1 / (1 + waccD)
        perShare1 = int((ev1 - netDebt) / shares) if shares > 0 else 0

        # 006 방식: 3년 체인
        dcf3 = scenarioDCF(pf3.projections, wacc, shares=shares, netDebt=netDebt)

        diff = dcf3["perShare"] - perShare1

        print(f"  {label:16s} | {perShare1:>10,}원 | {dcf3['perShare']:>10,}원 | {diff:>+7,}원")

    # 역전 확인
    print(f"\n  --- 역전 여부 확인 ---")
    dcfResults = {}
    for label, growthPath, histWeight in scenarios:
        blendedGM = baseGM * (1 - histWeight) + ratios.gross_margin * histWeight
        pf = build_proforma(series, revenue_growth_path=growthPath, scenario_name=label, overrides={"gross_margin": blendedGM})
        if pf.projections:
            p1 = pf.projections[0]
            netDebt = (p1.short_term_debt + p1.long_term_debt) - p1.cash
            dcf = scenarioDCF(pf.projections, pf.wacc, shares=shares, netDebt=netDebt)
            dcfResults[label] = dcf["perShare"]

            # 상세
            print(f"\n  [{label}]")
            for i, p in enumerate(pf.projections):
                print(f"    +{i+1}년: 매출 {p.revenue/1e12:.1f}조, OI {p.operating_income/1e12:.1f}조, FCF {p.fcf/1e12:.1f}조, D&A {p.depreciation/1e12:.1f}조, CapEx {p.capex/1e12:.1f}조")
            print(f"    정규화 FCF: {dcf['normalizedFcf']/1e12:.1f}조 (OCF - D&A)")
            print(f"    적정가: {dcf['perShare']:,}원")

    # 역전 체크
    vals = list(dcfResults.values())
    labels = list(dcfResults.keys())
    if len(vals) == 3:
        if vals[0] >= vals[1] >= vals[2]:
            print(f"\n  ✅ 역전 없음: {labels[0]}({vals[0]:,}) ≥ {labels[1]}({vals[1]:,}) ≥ {labels[2]}({vals[2]:,})")
        else:
            print(f"\n  ❌ 역전 발생: {' vs '.join(f'{l}({v:,})' for l, v in dcfResults.items())}")

    del c; gc.collect()


if __name__ == "__main__":
    main()
