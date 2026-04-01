"""107-001 — 시나리오 시뮬레이터 프로토타입.

삼성전자로 사후 검증:
  - 2023년 말 시점에서 "2024년 반도체 회복" 시나리오 설정
  - 과거 계절성으로 Q1~Q4 분기 목표 분해
  - 실제 2024년 Q1~Q4 실적과 비교 → 분기별 판정 + 행동

Company 1개만 로드. 메모리 안전.

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/001_prototype.py
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
_RESULT_FILE = _ROOT / "prototype_results.json"


# ---------------------------------------------------------------------------
# 데이터 구조
# ---------------------------------------------------------------------------
@dataclass
class QuarterTarget:
    quarter: str      # "2024Q1"
    bull: float
    base: float
    bear: float


@dataclass
class QuarterJudgment:
    quarter: str
    actual: float
    target_base: float
    target_bull: float
    target_bear: float
    deviation_pct: float        # (actual - base) / base × 100
    path: str                   # on_track / outperform / underperform / broken
    action: str
    reason: str
    cumulative_actual: float    # YTD 누적 실적
    cumulative_base: float      # YTD 누적 base 목표


@dataclass
class ScenarioSimulation:
    stockCode: str
    companyName: str
    scenarioName: str
    baseYear: str               # 시나리오 기준 연도 (이 해 데이터로 설정)
    targetYear: str             # 검증 대상 연도

    # 시나리오 가정
    revenueGrowth: float        # 연간 매출 성장률 %
    marginAssumption: str       # "개선" / "유지" / "악화"

    # 연간 목표
    annualRevenue: dict         # {"bull": X, "base": Y, "bear": Z}
    annualOI: dict              # 영업이익

    # 분기 목표
    quarterlyTargets: list      # [QuarterTarget × 4]

    # 분기별 판정
    judgments: list = field(default_factory=list)

    # 최종 상태
    finalPath: str = ""
    finalAction: str = ""


# ---------------------------------------------------------------------------
# 계절성 분해
# ---------------------------------------------------------------------------
def _extractQuarterlyValues(is_df, snakeId: str, year: str) -> list[float]:
    """IS DataFrame에서 특정 연도의 Q1~Q4 값을 추출."""
    row = is_df.filter(is_df["snakeId"] == snakeId)
    if row.height == 0:
        return []
    vals = []
    for q in range(1, 5):
        col = f"{year}Q{q}"
        if col in row.columns:
            v = row[col].to_list()[0]
            if v is not None:
                vals.append(float(v))
    return vals


def _computeSeasonality(is_df, snakeId: str, years: list[str]) -> list[float]:
    """과거 N년의 Q1~Q4 비중 평균 → [w1, w2, w3, w4], 합=1.0."""
    all_weights = []
    for year in years:
        qvals = _extractQuarterlyValues(is_df, snakeId, year)
        if len(qvals) == 4:
            total = sum(abs(v) for v in qvals)
            if total > 0:
                weights = [abs(v) / total for v in qvals]
                all_weights.append(weights)

    if not all_weights:
        return [0.25, 0.25, 0.25, 0.25]  # 균등 분배

    # 평균
    n = len(all_weights)
    avg = [sum(w[q] for w in all_weights) / n for q in range(4)]
    # 정규화
    s = sum(avg)
    return [w / s for w in avg] if s > 0 else [0.25] * 4


# ---------------------------------------------------------------------------
# 시나리오 생성
# ---------------------------------------------------------------------------
def createSimulation(
    company,
    scenarioName: str,
    revenueGrowth: float,       # 연간 매출 성장률 %
    marginAssumption: str = "유지",  # "개선" / "유지" / "악화"
    baseYear: str = "2023",
    targetYear: str = "2024",
    bullSpread: float = 1.5,    # base 대비 ×1.5 성장
    bearSpread: float = 0.3,    # base 대비 ×0.3 성장
) -> ScenarioSimulation:
    """시나리오 시뮬레이션 생성."""
    is_df = company.IS

    # base year 연간 매출/영업이익 (Q1~Q4 합산)
    baseRevQ = _extractQuarterlyValues(is_df, "sales", baseYear)
    baseOIQ = _extractQuarterlyValues(is_df, "operating_profit", baseYear)

    if not baseRevQ or not baseOIQ:
        raise ValueError(f"{baseYear} 분기 데이터 부족")

    baseRevAnnual = sum(baseRevQ)
    baseOIAnnual = sum(baseOIQ)
    baseMargin = baseOIAnnual / baseRevAnnual * 100 if baseRevAnnual else 0

    # 3개 시나리오 연간 목표
    baseGrowth = revenueGrowth / 100
    bullGrowth = baseGrowth * bullSpread
    bearGrowth = baseGrowth * bearSpread

    scenarios = {
        "bull": {"revGrowth": bullGrowth},
        "base": {"revGrowth": baseGrowth},
        "bear": {"revGrowth": bearGrowth},
    }

    # 마진 조정
    marginDelta = {"개선": 2.0, "유지": 0.0, "악화": -2.0}[marginAssumption]

    annualRevenue = {}
    annualOI = {}
    for sc, params in scenarios.items():
        rev = baseRevAnnual * (1 + params["revGrowth"])
        margin = baseMargin + marginDelta * (1 if sc == "bull" else 0 if sc == "base" else -1)
        oi = rev * margin / 100
        annualRevenue[sc] = rev
        annualOI[sc] = oi

    # 계절성 분해 (과거 3년)
    seasonYears = [str(int(baseYear) - i) for i in range(3) if int(baseYear) - i >= 2020]
    seasonWeights = _computeSeasonality(is_df, "sales", seasonYears)

    print(f"  계절성 비중: Q1={seasonWeights[0]:.1%} Q2={seasonWeights[1]:.1%} Q3={seasonWeights[2]:.1%} Q4={seasonWeights[3]:.1%}")

    # 분기 목표
    quarterlyTargets = []
    for q in range(4):
        qLabel = f"{targetYear}Q{q+1}"
        qt = QuarterTarget(
            quarter=qLabel,
            bull=annualRevenue["bull"] * seasonWeights[q],
            base=annualRevenue["base"] * seasonWeights[q],
            bear=annualRevenue["bear"] * seasonWeights[q],
        )
        quarterlyTargets.append(qt)

    return ScenarioSimulation(
        stockCode=company.stockCode,
        companyName=getattr(company, "name", company.stockCode),
        scenarioName=scenarioName,
        baseYear=baseYear,
        targetYear=targetYear,
        revenueGrowth=revenueGrowth,
        marginAssumption=marginAssumption,
        annualRevenue={k: round(v) for k, v in annualRevenue.items()},
        annualOI={k: round(v) for k, v in annualOI.items()},
        quarterlyTargets=quarterlyTargets,
    )


# ---------------------------------------------------------------------------
# 분기 판정
# ---------------------------------------------------------------------------
def judgeQuarter(
    sim: ScenarioSimulation,
    quarter: str,
    actual: float,
    tolerance: float = 0.05,
) -> QuarterJudgment:
    """분기 실적 판정."""
    target = next((t for t in sim.quarterlyTargets if t.quarter == quarter), None)
    if target is None:
        raise ValueError(f"{quarter} 목표 없음")

    deviation = (actual - target.base) / abs(target.base) * 100 if target.base else 0

    # 판정
    if abs(deviation) <= tolerance * 100:
        path = "on_track"
    elif actual >= target.bull:
        path = "outperform"
    elif actual <= target.bear:
        path = "underperform_severe"
    elif deviation > 0:
        path = "outperform_mild"
    else:
        path = "underperform"

    # YTD 누적
    qIdx = int(quarter[-1]) - 1
    cumActual = actual
    cumBase = target.base
    for prev in sim.judgments:
        cumActual += prev.actual
        cumBase += prev.target_base

    # 행동 결정
    action, reason = _decideAction(path, sim.judgments)

    judgment = QuarterJudgment(
        quarter=quarter,
        actual=round(actual),
        target_base=round(target.base),
        target_bull=round(target.bull),
        target_bear=round(target.bear),
        deviation_pct=round(deviation, 1),
        path=path,
        action=action,
        reason=reason,
        cumulative_actual=round(cumActual),
        cumulative_base=round(cumBase),
    )

    sim.judgments.append(judgment)
    sim.finalPath = path
    sim.finalAction = action

    return judgment


def _decideAction(currentPath: str, history: list[QuarterJudgment]) -> tuple[str, str]:
    """판정 이력 → 행동 추천."""
    prevPaths = [j.path for j in history]

    if currentPath == "on_track":
        return "보유", "시나리오 경로 내 진행 중"

    elif currentPath in ("outperform", "outperform_mild"):
        consecutiveOut = 0
        for p in reversed(prevPaths):
            if "outperform" in p:
                consecutiveOut += 1
            else:
                break
        if consecutiveOut >= 1:  # 이전에도 outperform → 2분기 연속
            return "비중확대 검토", f"{'outperform' if currentPath == 'outperform' else '소폭 상회'} {consecutiveOut+1}분기 연속"
        return "보유 (긍정 관찰)", "1분기 상회, 추세 확인 필요"

    elif currentPath == "underperform":
        consecutiveUnder = 0
        for p in reversed(prevPaths):
            if "underperform" in p:
                consecutiveUnder += 1
            else:
                break
        if consecutiveUnder >= 1:
            return "비중축소 검토", f"underperform {consecutiveUnder+1}분기 연속"
        return "보유 (경계)", "1분기 하회, 일시적 이탈 가능"

    elif currentPath == "underperform_severe":
        return "비중축소 검토", "Bear 시나리오 이탈 — 시나리오 전제 재검토 필요"

    return "시나리오 재설정", "예측 범위 밖"


# ---------------------------------------------------------------------------
# 메인: 삼성전자 사후 검증
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("107 시나리오 시뮬레이터 — 001 프로토타입")
    print("=" * 60)

    from dartlab import Company

    print("\n[1/4] 삼성전자 로드...")
    c = Company("005930")
    is_df = c.IS

    # 2023 실적 확인
    rev2023 = _extractQuarterlyValues(is_df, "sales", "2023")
    oi2023 = _extractQuarterlyValues(is_df, "operating_profit", "2023")
    print(f"  2023 매출: {sum(rev2023)/1e12:.1f}조 ({[round(v/1e12, 1) for v in rev2023]})")
    print(f"  2023 영업이익: {sum(oi2023)/1e12:.1f}조 ({[round(v/1e12, 1) for v in oi2023]})")

    # 2024 실적 (검증용)
    rev2024 = _extractQuarterlyValues(is_df, "sales", "2024")
    oi2024 = _extractQuarterlyValues(is_df, "operating_profit", "2024")
    print(f"  2024 실제 매출: {sum(rev2024)/1e12:.1f}조 ({[round(v/1e12, 1) for v in rev2024]})")
    print(f"  2024 실제 영업이익: {sum(oi2024)/1e12:.1f}조")

    actualYoY = (sum(rev2024) - sum(rev2023)) / sum(rev2023) * 100
    print(f"  실제 YoY: {actualYoY:+.1f}%")

    # [2] 시나리오 설정: "2024 반도체 회복"
    print(f"\n[2/4] 시나리오 설정: '반도체 회복'")
    print(f"  가정: 매출 +15%, 마진 개선")

    sim = createSimulation(
        company=c,
        scenarioName="반도체 회복",
        revenueGrowth=15.0,     # base: +15%
        marginAssumption="개선",
        baseYear="2023",
        targetYear="2024",
        bullSpread=1.5,         # bull: +22.5%
        bearSpread=0.3,         # bear: +4.5%
    )

    print(f"\n  연간 목표:")
    for sc in ["bull", "base", "bear"]:
        rev = sim.annualRevenue[sc]
        print(f"    {sc:5s}: 매출 {rev/1e12:.1f}조")

    print(f"\n  분기 목표 (base):")
    for qt in sim.quarterlyTargets:
        print(f"    {qt.quarter}: bull={qt.bull/1e12:.1f}조 base={qt.base/1e12:.1f}조 bear={qt.bear/1e12:.1f}조")

    # [3] 분기별 판정
    print(f"\n[3/4] 분기별 판정 (실제 실적 vs 시나리오)")
    print(f"{'='*70}")

    for q in range(4):
        qLabel = f"2024Q{q+1}"
        actual = rev2024[q]

        judgment = judgeQuarter(sim, qLabel, actual)

        devSymbol = "▲" if judgment.deviation_pct > 0 else "▼" if judgment.deviation_pct < 0 else "─"
        print(f"\n  {qLabel}: 실적 {actual/1e12:.1f}조 | 목표 {judgment.target_base/1e12:.1f}조 | {devSymbol} {judgment.deviation_pct:+.1f}%")
        print(f"         판정: {judgment.path}")
        print(f"         행동: {judgment.action} — {judgment.reason}")
        print(f"         YTD: 실적 {judgment.cumulative_actual/1e12:.1f}조 vs 목표 {judgment.cumulative_base/1e12:.1f}조")

    # [4] 최종 요약
    print(f"\n{'='*70}")
    print(f"[4/4] 최종 요약")
    print(f"{'='*70}")
    print(f"  시나리오: {sim.scenarioName} (매출 +{sim.revenueGrowth}%)")
    print(f"  실제 YoY: {actualYoY:+.1f}%")
    print(f"  최종 판정: {sim.finalPath}")
    print(f"  최종 행동: {sim.finalAction}")

    # 분기별 판정 요약
    print(f"\n  분기별 경로:")
    for j in sim.judgments:
        print(f"    {j.quarter}: {j.path:20s} → {j.action}")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stockCode": sim.stockCode,
        "scenario": sim.scenarioName,
        "revenueGrowth": sim.revenueGrowth,
        "actualYoY": round(actualYoY, 1),
        "judgments": [
            {
                "quarter": j.quarter,
                "actual_조": round(j.actual / 1e12, 1),
                "base_조": round(j.target_base / 1e12, 1),
                "deviation": j.deviation_pct,
                "path": j.path,
                "action": j.action,
            }
            for j in sim.judgments
        ],
        "finalPath": sim.finalPath,
        "finalAction": sim.finalAction,
    }

    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    del c
    gc.collect()


if __name__ == "__main__":
    main()
