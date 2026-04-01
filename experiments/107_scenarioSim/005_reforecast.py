"""107-005 — 분기 재예측 (P2).

핵심: Q1 실적 발표 후 연간 착지 예상을 업데이트한다.
방법 2가지 비교:
  1. 단순: 남은 분기 원래 목표 유지
  2. 추세: YTD 편차를 남은 분기에 부분 반영 (50%)

삼성전자 2024 Q1→Q2→Q3→Q4 순차 재예측.

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/005_reforecast.py
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


def _seasonality(is_df, sid: str, years: list[str]) -> list[float]:
    all_w = []
    for y in years:
        qv = _qvals(is_df, sid, y)
        if len(qv) == 4:
            t = sum(abs(v) for v in qv)
            if t > 0:
                all_w.append([abs(v)/t for v in qv])
    if not all_w:
        return [0.25]*4
    n = len(all_w)
    avg = [sum(w[q] for w in all_w)/n for q in range(4)]
    s = sum(avg)
    return [w/s for w in avg] if s > 0 else [0.25]*4


def _reforecast(
    annualTarget: float,
    qTargets: list[float],
    actuals: list[float],     # Q1부터 현재까지 실적
    trendFactor: float = 0.5,
) -> tuple[float, float]:
    """분기 재예측 → (단순 착지, 추세 착지).

    단순: actualYTD + 남은 분기 원래 목표
    추세: 남은 분기에 YTD 편차 × trendFactor 반영
    """
    nActual = len(actuals)
    ytdActual = sum(actuals)
    ytdTarget = sum(qTargets[:nActual])

    remainingTargets = qTargets[nActual:]
    remainingSum = sum(remainingTargets)

    # 단순
    simple = ytdActual + remainingSum

    # 추세
    if ytdTarget > 0:
        deviation = (ytdActual / ytdTarget) - 1
        adjustedRemaining = remainingSum * (1 + deviation * trendFactor)
    else:
        adjustedRemaining = remainingSum
    trend = ytdActual + adjustedRemaining

    return simple, trend


def main():
    print("=" * 70)
    print("107-005 분기 재예측")
    print("=" * 70)

    from dartlab import Company
    from dartlab.core.finance.proforma import build_proforma, extract_historical_ratios

    c = Company("005930")
    ts = c.finance.timeseries
    fullSeries = ts[0] if isinstance(ts, tuple) else ts
    periods = ts[1] if isinstance(ts, tuple) else []
    is_df = c.IS

    # 2023까지 필터
    cutIdx = periods.index("2023-Q4") + 1
    series = {stmt: {k: v[:cutIdx] for k, v in fullSeries[stmt].items()} for stmt in ["IS", "BS", "CF"]}

    # 기준연도 비율
    ratios = extract_historical_ratios(series)
    rev23 = sum(_qvals(is_df, "sales", "2023"))
    gp23 = sum(_qvals(is_df, "gross_profit", "2023"))
    baseGM = gp23 / rev23 * 100 if rev23 else 0
    blendedGM = baseGM * 0.5 + ratios.gross_margin * 0.5

    # Base 시나리오 ProForma (004 블렌딩 적용)
    pf = build_proforma(series, revenue_growth_path=[15.0], scenario_name="base", overrides={"gross_margin": blendedGM})
    p = pf.projections[0]

    # 분기 목표
    revW = _seasonality(is_df, "sales", ["2021", "2022", "2023"])
    oiW = _seasonality(is_df, "operating_profit", ["2021", "2022", "2023"])
    qRevTargets = [p.revenue * w for w in revW]
    qOiTargets = [p.operating_income * w for w in oiW]

    # 실적
    rev24Q = _qvals(is_df, "sales", "2024")
    oi24Q = _qvals(is_df, "operating_profit", "2024")
    annualRevActual = sum(rev24Q)
    annualOiActual = sum(oi24Q)

    print(f"\n  Base 시나리오: 연간 매출 {p.revenue/1e12:.1f}조, 영업이익 {p.operating_income/1e12:.1f}조")
    print(f"  실제 연간:    매출 {annualRevActual/1e12:.1f}조, 영업이익 {annualOiActual/1e12:.1f}조")

    # 분기별 순차 재예측
    print(f"\n{'='*70}")
    print(f"  분기별 재예측 (Q1→Q4 순차)")
    print(f"{'='*70}")

    print(f"\n  {'시점':6s} | {'단순착지':>8s} {'추세착지':>8s} {'실제':>8s} | {'단순오차':>7s} {'추세오차':>7s} | {'이익단순':>8s} {'이익추세':>8s} {'이익실제':>8s} | {'이익단순오차':>8s} {'이익추세오차':>8s}")
    print(f"  {'-'*120}")

    for q in range(1, 5):
        revActuals = rev24Q[:q]
        oiActuals = oi24Q[:q]

        revSimple, revTrend = _reforecast(p.revenue, qRevTargets, revActuals)
        oiSimple, oiTrend = _reforecast(p.operating_income, qOiTargets, oiActuals)

        revSimpleErr = (revSimple - annualRevActual) / annualRevActual * 100
        revTrendErr = (revTrend - annualRevActual) / annualRevActual * 100
        oiSimpleErr = (oiSimple - annualOiActual) / annualOiActual * 100
        oiTrendErr = (oiTrend - annualOiActual) / annualOiActual * 100

        print(f"  Q{q}까지 | {revSimple/1e12:>7.1f}조 {revTrend/1e12:>7.1f}조 {annualRevActual/1e12:>7.1f}조 | {revSimpleErr:>+6.1f}% {revTrendErr:>+6.1f}% | {oiSimple/1e12:>7.1f}조 {oiTrend/1e12:>7.1f}조 {annualOiActual/1e12:>7.1f}조 | {oiSimpleErr:>+7.1f}% {oiTrendErr:>+7.1f}%")

    # 요약
    print(f"\n{'='*70}")
    print(f"  재예측 정확도 추이 (매출 기준)")
    print(f"{'='*70}")

    for q in range(1, 5):
        _, revTrend = _reforecast(p.revenue, qRevTargets, rev24Q[:q])
        err = abs(revTrend - annualRevActual) / annualRevActual * 100
        bar = "█" * int(err * 2) + "░" * (20 - int(err * 2))
        print(f"  Q{q} 시점 오차: {err:5.1f}% |{bar}|")

    del c; gc.collect()


if __name__ == "__main__":
    main()
