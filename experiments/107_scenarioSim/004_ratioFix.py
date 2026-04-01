"""107-004 — 마진 비율 정규화 (P1).

문제: ProForma가 과거 5년 가중 평균 비율을 사용하므로,
비정상 연도(2023 삼성전자 영업이익률 2.5%)가 기준이면 이익 목표가 비현실적.

해결: 기준연도 비율과 과거 비율을 시나리오별로 블렌딩.
- Bull: 과거 비율 70% (마진 회복 낙관)
- Base: 50:50
- Bear: 기준연도 70% (현재 상태 지속)

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/004_ratioFix.py
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


def main():
    print("=" * 70)
    print("107-004 마진 비율 정규화")
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

    # 과거 비율
    ratios = extract_historical_ratios(series)
    histGM = ratios.gross_margin
    histSGA = ratios.sga_ratio
    histOpMargin = histGM - histSGA  # 과거 영업이익률 근사

    # 기준연도(2023) 실제 비율
    rev23 = sum(_qvals(is_df, "sales", "2023"))
    gp23 = sum(_qvals(is_df, "gross_profit", "2023"))
    oi23 = sum(_qvals(is_df, "operating_profit", "2023"))
    baseGM = gp23 / rev23 * 100 if rev23 else 0
    baseOpMargin = oi23 / rev23 * 100 if rev23 else 0

    print(f"\n  과거 5년 가중: GM={histGM:.1f}%, SGA={histSGA:.1f}%, OP margin≈{histOpMargin:.1f}%")
    print(f"  2023 기준연도:  GM={baseGM:.1f}%, OP margin={baseOpMargin:.1f}%")

    # 2024 실제
    rev24 = sum(_qvals(is_df, "sales", "2024"))
    oi24 = sum(_qvals(is_df, "operating_profit", "2024"))
    actualOpMargin = oi24 / rev24 * 100 if rev24 else 0
    print(f"  2024 실제:     매출 {rev24/1e12:.1f}조, OP margin={actualOpMargin:.1f}%")

    # 시나리오별 블렌딩
    blends = {
        "bull":  {"histWeight": 0.7, "growth": 22.0, "label": "Bull(과거70%)"},
        "base":  {"histWeight": 0.5, "growth": 15.0, "label": "Base(50:50)"},
        "bear":  {"histWeight": 0.3, "growth": 5.0,  "label": "Bear(기준70%)"},
    }

    print(f"\n{'='*70}")
    print(f"  시나리오별 마진 블렌딩 → ProForma → 이익 비교")
    print(f"{'='*70}")

    # 계절성
    oiW = _seasonality(is_df, "operating_profit", ["2021", "2022", "2023"])
    oi24Q = _qvals(is_df, "operating_profit", "2024")

    for scName, cfg in blends.items():
        hw = cfg["histWeight"]
        blendedGM = baseGM * (1 - hw) + histGM * hw
        # SGA는 과거 비율 유지 (비용 구조는 안정적)
        overrides = {"gross_margin": blendedGM}

        pf = build_proforma(
            series,
            revenue_growth_path=[cfg["growth"]],
            scenario_name=scName,
            overrides=overrides,
        )
        if not pf.projections:
            print(f"  [{cfg['label']}] ProForma 실패")
            continue

        p = pf.projections[0]
        pfOpMargin = p.operating_income / p.revenue * 100 if p.revenue else 0

        # 003 방식 (override 없음)
        pfNoFix = build_proforma(series, revenue_growth_path=[cfg["growth"]], scenario_name=f"{scName}_nofix")
        pNoFix = pfNoFix.projections[0] if pfNoFix.projections else None
        nofixOI = pNoFix.operating_income if pNoFix else 0
        nofixMargin = nofixOI / pNoFix.revenue * 100 if pNoFix and pNoFix.revenue else 0

        # 분기별 이익 판정 비교
        qOiTargets = [p.operating_income * w for w in oiW]
        qOiNoFix = [nofixOI * w for w in oiW] if pNoFix else [0]*4

        print(f"\n  [{cfg['label']}] GM 블렌딩: {blendedGM:.1f}% (기준{baseGM:.1f}% × {1-hw:.0%} + 과거{histGM:.1f}% × {hw:.0%})")
        print(f"    수정 후: 매출 {p.revenue/1e12:.1f}조, 영업이익 {p.operating_income/1e12:.1f}조 (margin {pfOpMargin:.1f}%)")
        print(f"    수정 전: 매출 {pNoFix.revenue/1e12:.1f}조, 영업이익 {nofixOI/1e12:.1f}조 (margin {nofixMargin:.1f}%)")
        print(f"    실  제: 매출 {rev24/1e12:.1f}조, 영업이익 {oi24/1e12:.1f}조 (margin {actualOpMargin:.1f}%)")

        # 이익 편차 비교
        fixedDev = (oi24 - p.operating_income) / abs(p.operating_income) * 100 if p.operating_income else 0
        nofixDev = (oi24 - nofixOI) / abs(nofixOI) * 100 if nofixOI else 0
        print(f"    이익 편차: 수정 후 {fixedDev:+.1f}% | 수정 전 {nofixDev:+.1f}%")

        # 분기별 판정 비교 (base 시나리오만)
        if scName == "base":
            print(f"\n    --- Base 분기별 이익 판정 비교 ---")
            for q in range(4):
                actual = oi24Q[q] if q < len(oi24Q) else 0
                target_fix = qOiTargets[q]
                target_nofix = qOiNoFix[q]
                dev_fix = (actual - target_fix) / abs(target_fix) * 100 if target_fix else 0
                dev_nofix = (actual - target_nofix) / abs(target_nofix) * 100 if target_nofix else 0
                print(f"      Q{q+1}: 실적 {actual/1e12:.1f}조 | 수정목표 {target_fix/1e12:.1f}조 ({dev_fix:+.0f}%) | 기존목표 {target_nofix/1e12:.1f}조 ({dev_nofix:+.0f}%)")

    del c; gc.collect()


if __name__ == "__main__":
    main()
