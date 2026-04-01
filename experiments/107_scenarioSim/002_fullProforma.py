"""107-002 — ProForma 3-statement + DCF + 분기 판정.

001은 매출 1개 변수만 분해했다. 이번엔:
- build_proforma()로 IS→BS→CF 전체 시나리오 생성 (bull/base/bear)
- 과거 계절성으로 매출 + 영업이익 분기 분해
- dcfValuation()으로 시나리오별 적정가치
- 분기별 매출 + 영업이익 이중 판정
- DCF 근거 포함 행동 추천

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/002_fullProforma.py
"""

from __future__ import annotations

import gc
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_RESULT_FILE = _ROOT / "fullproforma_results.json"


# ---------------------------------------------------------------------------
# 분기 데이터 추출
# ---------------------------------------------------------------------------
def _quarterlyValues(is_df, snakeId: str, year: str) -> list[float]:
    """IS DataFrame에서 특정 연도의 Q1~Q4 값 추출."""
    row = is_df.filter(is_df["snakeId"] == snakeId)
    if row.height == 0:
        return []
    vals = []
    for q in range(1, 5):
        col = f"{year}Q{q}"
        if col in row.columns:
            v = row[col].to_list()[0]
            vals.append(float(v) if v is not None else 0)
    return vals if len(vals) == 4 else []


def _seasonality(is_df, snakeId: str, years: list[str]) -> list[float]:
    """과거 N년 Q1~Q4 비중 평균."""
    all_w = []
    for y in years:
        qv = _quarterlyValues(is_df, snakeId, y)
        if len(qv) == 4:
            total = sum(abs(v) for v in qv)
            if total > 0:
                all_w.append([abs(v) / total for v in qv])
    if not all_w:
        return [0.25] * 4
    n = len(all_w)
    avg = [sum(w[q] for w in all_w) / n for q in range(4)]
    s = sum(avg)
    return [w / s for w in avg] if s > 0 else [0.25] * 4


# ---------------------------------------------------------------------------
# 시나리오 정의
# ---------------------------------------------------------------------------
@dataclass
class ScenarioDef:
    name: str
    label: str
    revenue_growth: float       # %
    overrides: dict = field(default_factory=dict)  # ProForma overrides


# ---------------------------------------------------------------------------
# 판정
# ---------------------------------------------------------------------------
def _judge(actual: float, bull: float, base: float, bear: float, tol: float = 0.05) -> str:
    if base == 0:
        return "unknown"
    dev = (actual - base) / abs(base)
    if abs(dev) <= tol:
        return "on_track"
    elif actual >= bull:
        return "outperform"
    elif actual <= bear:
        return "underperform_severe"
    elif dev > 0:
        return "outperform_mild"
    else:
        return "underperform"


def _action(revPath: str, oiPath: str, history: list[dict]) -> tuple[str, str]:
    """매출 + 영업이익 이중 판정 → 행동."""
    # 최악 경로 기준
    severity = {"outperform": 2, "outperform_mild": 1, "on_track": 0,
                "underperform": -1, "underperform_severe": -2, "unknown": 0}
    revScore = severity.get(revPath, 0)
    oiScore = severity.get(oiPath, 0)
    combined = (revScore + oiScore) / 2

    # 연속성 체크
    prevScores = []
    for h in history[-2:]:
        ps = (severity.get(h.get("revPath", ""), 0) + severity.get(h.get("oiPath", ""), 0)) / 2
        prevScores.append(ps)

    consecutiveNeg = all(s < 0 for s in prevScores) if prevScores else False

    if combined >= 1.5:
        return "비중확대 검토", "매출+이익 모두 Bull 이상"
    elif combined >= 0.5:
        if len(prevScores) >= 1 and prevScores[-1] >= 0.5:
            return "비중확대 검토", "2분기 연속 상회"
        return "보유 (긍정)", "상회 관찰 중"
    elif combined >= -0.5:
        return "보유", "시나리오 경로 내"
    elif combined >= -1.5:
        if consecutiveNeg:
            return "비중축소 검토", "2분기 연속 하회"
        if oiPath == "underperform_severe" and revPath != "underperform_severe":
            return "비중축소 검토", "매출은 괜찮으나 마진 붕괴"
        return "보유 (경계)", "1분기 하회, 추세 확인 필요"
    else:
        return "비중축소 검토", "Bear 시나리오 이탈"


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("107 시나리오 시뮬레이터 — 002 전체 ProForma")
    print("=" * 70)

    from dartlab import Company
    from dartlab.core.finance.proforma import build_proforma
    from dartlab.core.finance.dcf import dcfValuation

    print("\n[1/5] 삼성전자 로드...")
    c = Company("005930")

    # series 추출 + 2023년까지만 필터 (사후 검증이므로)
    ts = c.finance.timeseries
    fullSeries = ts[0] if isinstance(ts, tuple) else ts
    periods = ts[1] if isinstance(ts, tuple) else []

    BASE_YEAR = "2023"
    TARGET_YEAR = "2024"
    cutoff = f"{BASE_YEAR}-Q4"
    cutIdx = periods.index(cutoff) + 1 if cutoff in periods else len(periods)
    series = {}
    for stmt in ["IS", "BS", "CF"]:
        series[stmt] = {}
        for key, vals in fullSeries[stmt].items():
            series[stmt][key] = vals[:cutIdx]
    print(f"  series 필터: ~{cutoff} ({cutIdx}분기)")

    shares = None
    profile = getattr(c, "profile", None)
    if profile:
        sv = getattr(profile, "sharesOutstanding", None)
        if sv:
            shares = int(sv)

    is_df = c.IS

    # 2023 실적
    rev2023 = _quarterlyValues(is_df, "sales", "2023")
    oi2023 = _quarterlyValues(is_df, "operating_profit", "2023")
    rev2024 = _quarterlyValues(is_df, "sales", "2024")
    oi2024 = _quarterlyValues(is_df, "operating_profit", "2024")

    print(f"  2023: 매출 {sum(rev2023)/1e12:.1f}조, 영업이익 {sum(oi2023)/1e12:.1f}조")
    print(f"  2024 실제: 매출 {sum(rev2024)/1e12:.1f}조, 영업이익 {sum(oi2024)/1e12:.1f}조")

    # 과거 비율 확인
    from dartlab.core.finance.proforma import extract_historical_ratios
    ratios = extract_historical_ratios(series)
    print(f"\n  과거 비율:")
    print(f"    매출총이익률: {ratios.gross_margin:.1f}%")
    print(f"    판관비율: {ratios.sga_ratio:.1f}%")
    print(f"    CAPEX/매출: {ratios.capex_to_revenue:.1f}%")
    print(f"    유효세율: {ratios.effective_tax_rate:.1f}%")

    # [2] 3개 시나리오
    print(f"\n[2/5] 3개 시나리오 ProForma 생성...")

    scenarios = [
        ScenarioDef("bull", "반도체 초회복", 22.0, {
            "gross_margin": ratios.gross_margin + 3.0,
            "capex_to_revenue": ratios.capex_to_revenue + 2.0,
        }),
        ScenarioDef("base", "반도체 회복", 15.0, {
            "gross_margin": ratios.gross_margin + 1.0,
        }),
        ScenarioDef("bear", "회복 지연", 5.0, {
            "gross_margin": ratios.gross_margin - 1.0,
        }),
    ]

    pfResults = {}
    for sc in scenarios:
        try:
            pf = build_proforma(
                series,
                revenue_growth_path=[sc.revenue_growth],
                shares=shares,
                scenario_name=sc.name,
                overrides=sc.overrides if sc.overrides else None,
            )
            pfResults[sc.name] = pf
            p = pf.projections[0] if pf.projections else None
            if p:
                print(f"\n  [{sc.label}] +1년:")
                print(f"    매출: {p.revenue/1e12:.1f}조  영업이익: {p.operating_income/1e12:.1f}조  순이익: {p.net_income/1e12:.1f}조")
                print(f"    FCF: {p.fcf/1e12:.1f}조  총자산: {p.total_assets/1e12:.1f}조  부채비율: {p.total_liabilities/p.total_equity*100:.0f}%")
        except Exception as e:
            print(f"  [{sc.label}] ProForma 실패: {e}")

    # [3] 시나리오별 간이 DCF (ProForma FCF 직접 사용)
    print(f"\n[3/5] 시나리오별 적정가치 (ProForma FCF 기반)...")
    dcfValues = {}
    for sc in scenarios:
        pf = pfResults.get(sc.name)
        if not pf or not pf.projections:
            continue
        p = pf.projections[0]
        wacc = pf.wacc / 100  # % → 소수
        terminalGrowth = 0.02  # 2%
        if wacc <= terminalGrowth:
            wacc = terminalGrowth + 0.05

        # 1년 FCF + Terminal Value (Gordon Growth)
        fcf1 = p.fcf
        tv = fcf1 * (1 + terminalGrowth) / (wacc - terminalGrowth)
        ev = fcf1 / (1 + wacc) + tv / (1 + wacc)

        # 순부채 차감
        netDebt = (p.short_term_debt + p.long_term_debt) - p.cash
        equityValue = ev - netDebt

        perShare = int(equityValue / shares) if shares and shares > 0 else 0
        dcfValues[sc.name] = perShare
        print(f"  {sc.label}: {perShare:,}원 (FCF {fcf1/1e12:.1f}조, WACC {pf.wacc:.1f}%, EV {ev/1e12:.0f}조)")

    # [4] 분기 분해 + 판정
    print(f"\n[4/5] 분기 분해 + 판정")

    seasonYears = ["2021", "2022", "2023"]
    revWeights = _seasonality(is_df, "sales", seasonYears)
    oiWeights = _seasonality(is_df, "operating_profit", seasonYears)
    print(f"  매출 계절성: {['Q'+str(i+1)+'='+f'{w:.0%}' for i,w in enumerate(revWeights)]}")
    print(f"  영업이익 계절성: {['Q'+str(i+1)+'='+f'{w:.0%}' for i,w in enumerate(oiWeights)]}")

    # 분기 목표 생성
    qTargets = {"revenue": {}, "oi": {}}
    for sc in scenarios:
        pf = pfResults.get(sc.name)
        if not pf or not pf.projections:
            continue
        p = pf.projections[0]
        qTargets["revenue"][sc.name] = [p.revenue * w for w in revWeights]
        qTargets["oi"][sc.name] = [p.operating_income * w for w in oiWeights]

    # 판정
    print(f"\n{'='*70}")
    print(f"  분기별 판정 (2024 Q1~Q4)")
    print(f"{'='*70}")

    history = []
    for q in range(4):
        qLabel = f"Q{q+1}"
        actualRev = rev2024[q]
        actualOI = oi2024[q]

        bullRev = qTargets["revenue"]["bull"][q]
        baseRev = qTargets["revenue"]["base"][q]
        bearRev = qTargets["revenue"]["bear"][q]

        bullOI = qTargets["oi"]["bull"][q]
        baseOI = qTargets["oi"]["base"][q]
        bearOI = qTargets["oi"]["bear"][q]

        revPath = _judge(actualRev, bullRev, baseRev, bearRev)
        oiPath = _judge(actualOI, bullOI, baseOI, bearOI)

        revDev = (actualRev - baseRev) / abs(baseRev) * 100 if baseRev else 0
        oiDev = (actualOI - baseOI) / abs(baseOI) * 100 if baseOI else 0

        action, reason = _action(revPath, oiPath, history)

        # YTD 누적
        ytdActualRev = sum(rev2024[:q+1])
        ytdBaseRev = sum(qTargets["revenue"]["base"][:q+1])
        ytdDev = (ytdActualRev - ytdBaseRev) / abs(ytdBaseRev) * 100 if ytdBaseRev else 0

        history.append({"revPath": revPath, "oiPath": oiPath})

        print(f"\n  ── 2024 {qLabel} ──")
        print(f"  매출:   실적 {actualRev/1e12:.1f}조 | 목표 {baseRev/1e12:.1f}조 | {'▲' if revDev > 0 else '▼'}{revDev:+.1f}% → {revPath}")
        print(f"  영업이익: 실적 {actualOI/1e12:.1f}조 | 목표 {baseOI/1e12:.1f}조 | {'▲' if oiDev > 0 else '▼'}{oiDev:+.1f}% → {oiPath}")
        print(f"  YTD:   {ytdActualRev/1e12:.1f}조 vs {ytdBaseRev/1e12:.1f}조 ({ytdDev:+.1f}%)")
        print(f"  행동:   {action} — {reason}")

    # [5] 최종 요약
    print(f"\n{'='*70}")
    print(f"[5/5] 최종 요약")
    print(f"{'='*70}")

    actualAnnualRev = sum(rev2024)
    actualAnnualOI = sum(oi2024)
    baseAnnualRev = sum(qTargets["revenue"]["base"])
    baseAnnualOI = sum(qTargets["oi"]["base"])

    print(f"  실제 연간: 매출 {actualAnnualRev/1e12:.1f}조, 영업이익 {actualAnnualOI/1e12:.1f}조")
    print(f"  Base 목표: 매출 {baseAnnualRev/1e12:.1f}조, 영업이익 {baseAnnualOI/1e12:.1f}조")
    print(f"  편차: 매출 {(actualAnnualRev-baseAnnualRev)/baseAnnualRev*100:+.1f}%, 영업이익 {(actualAnnualOI-baseAnnualOI)/baseAnnualOI*100:+.1f}%")

    if dcfValues:
        print(f"\n  DCF 적정가치:")
        for sc in scenarios:
            v = dcfValues.get(sc.name, 0)
            print(f"    {sc.label}: {v:,}원")

    print(f"\n  분기별 행동 흐름:")
    for q, h in enumerate(history):
        aLabel = f"Q{q+1}"
        print(f"    {aLabel}: 매출={h['revPath']:20s} 이익={h['oiPath']:20s}")

    # 저장
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "stock": "005930"}, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    del c
    gc.collect()


if __name__ == "__main__":
    main()
