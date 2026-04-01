"""107-008 — 저마진/적자 기업 블렌딩 보정 검증.

007 문제: 하이닉스(이익+1563%), NAVER(+373%), KT(+174%) —
기준연도 이익률이 매우 낮을 때 50:50 블렌딩이 음수/비현실적 이익 생성.

해결: 기준연도 이익률에 따라 과거 비율 가중치 자동 조정.
  이익률 < 2%: 과거 80% (적자→회복 전제)
  이익률 < 5%: 과거 70%
  이익률 ≥ 5%: 50:50

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/008_lowMarginFix.py
"""

from __future__ import annotations

import gc
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


def _qvals(is_df, sid, year):
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


def _blendWeight(baseOpMargin: float) -> float:
    """기준연도 영업이익률에 따라 과거 비율 가중치 결정."""
    if baseOpMargin < 2.0:
        return 0.8
    elif baseOpMargin < 5.0:
        return 0.7
    else:
        return 0.5


def main():
    print("=" * 70)
    print("107-008 저마진/적자 기업 블렌딩 보정")
    print("=" * 70)

    from dartlab import Company
    from dartlab.core.finance.proforma import build_proforma, extract_historical_ratios

    targets = [
        {"code": "000660", "name": "SK하이닉스", "growth": [30.0, 20.0, 12.0]},
        {"code": "035420", "name": "NAVER", "growth": [12.0, 10.0, 8.0]},
        {"code": "030200", "name": "KT", "growth": [3.0, 2.0, 2.0]},
    ]

    for comp in targets:
        print(f"\n{'='*70}")
        print(f"  {comp['name']} ({comp['code']})")
        print(f"{'='*70}")

        c = Company(comp["code"])
        ts = c.finance.timeseries
        fullSeries = ts[0] if isinstance(ts, tuple) else ts
        periods = ts[1] if isinstance(ts, tuple) else []
        is_df = c.IS

        cutIdx = periods.index("2023-Q4") + 1
        series = {stmt: {k: v[:cutIdx] for k, v in fullSeries[stmt].items()} for stmt in ["IS", "BS", "CF"]}

        ratios = extract_historical_ratios(series)
        rev23 = sum(_qvals(is_df, "sales", "2023"))
        gp23 = sum(_qvals(is_df, "gross_profit", "2023"))
        oi23 = sum(_qvals(is_df, "operating_profit", "2023"))

        baseGM = gp23 / rev23 * 100 if rev23 else 0
        baseOpMargin = oi23 / rev23 * 100 if rev23 else 0

        # 실제 2024
        rev24 = sum(_qvals(is_df, "sales", "2024"))
        oi24 = sum(_qvals(is_df, "operating_profit", "2024"))
        actualOpMargin = oi24 / rev24 * 100 if rev24 else 0

        print(f"  2023: GM={baseGM:.1f}%, OP margin={baseOpMargin:.1f}%")
        print(f"  과거: GM={ratios.gross_margin:.1f}%, SGA={ratios.sga_ratio:.1f}%")
        print(f"  2024 실제: 매출 {rev24/1e12:.1f}조, OI {oi24/1e12:.1f}조 (margin {actualOpMargin:.1f}%)")

        # 자동 보정 가중치
        hw = _blendWeight(baseOpMargin)
        print(f"  → 자동 보정: 이익률 {baseOpMargin:.1f}% → 과거 가중 {hw:.0%}")

        # 3가지 방식 비교
        methods = [
            ("007(50:50 고정)", 0.5),
            ("008(자동보정)", hw),
            ("참고(과거100%)", 1.0),
        ]

        growthPath = comp["growth"]

        for label, histW in methods:
            blendedGM = baseGM * (1 - histW) + ratios.gross_margin * histW

            try:
                pf = build_proforma(
                    series,
                    revenue_growth_path=growthPath,
                    scenario_name="base",
                    overrides={"gross_margin": blendedGM},
                )
                if pf.projections:
                    p = pf.projections[0]
                    pfMargin = p.operating_income / p.revenue * 100 if p.revenue else 0
                    oiDev = (oi24 - p.operating_income) / abs(p.operating_income) * 100 if p.operating_income and p.operating_income != 0 else float('inf')
                    print(f"  {label:20s}: GM={blendedGM:.1f}% → OI {p.operating_income/1e12:.1f}조 (margin {pfMargin:.1f}%) | 편차 {oiDev:+.0f}%")
                else:
                    print(f"  {label:20s}: ProForma 실패")
            except (KeyError, ValueError, ZeroDivisionError, TypeError) as e:
                print(f"  {label:20s}: 오류 {e}")

        del c
        gc.collect()


if __name__ == "__main__":
    main()
