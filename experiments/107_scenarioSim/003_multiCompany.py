"""107-003 — 다중 기업 시나리오 시뮬레이터 검증.

002의 전체 ProForma + 이중 판정을 다양한 업종/상황의 기업에 적용.
사후 검증: 2023년 말 시점 시나리오 → 2024년 Q1~Q4 실적.

기업 선정 기준:
  - 다양한 업종 (반도체, 자동차, 금융, 바이오, 식품, 건설)
  - 다양한 상황 (성장, 안정, 하락, 턴어라운드)
  - 매출 1조+ (ProForma 안정성)

메모리 안전: Company 1개씩 순차 로드 → 분석 → 해제.

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/003_multiCompany.py
"""

from __future__ import annotations

import gc
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_RESULT_FILE = _ROOT / "multi_results.json"

# ---------------------------------------------------------------------------
# 기업 + 시나리오 정의
# ---------------------------------------------------------------------------
COMPANIES = [
    {
        "code": "005930", "name": "삼성전자", "sector": "반도체",
        "scenario": "반도체 회복", "growth": 15.0,
        "overrides": {},  # 기본 비율 사용
    },
    {
        "code": "000660", "name": "SK하이닉스", "sector": "반도체",
        "scenario": "HBM 수혜", "growth": 30.0,
        "overrides": {},
    },
    {
        "code": "005380", "name": "현대차", "sector": "자동차",
        "scenario": "글로벌 판매 호조", "growth": 8.0,
        "overrides": {},
    },
    {
        "code": "035420", "name": "NAVER", "sector": "플랫폼",
        "scenario": "AI 광고 성장", "growth": 12.0,
        "overrides": {},
    },
    {
        "code": "068270", "name": "셀트리온", "sector": "바이오",
        "scenario": "바이오시밀러 확대", "growth": 20.0,
        "overrides": {},
    },
    {
        "code": "004020", "name": "현대제철", "sector": "철강",
        "scenario": "건설 경기 둔화", "growth": -5.0,
        "overrides": {},
    },
    {
        "code": "030200", "name": "KT", "sector": "통신",
        "scenario": "안정 성장", "growth": 3.0,
        "overrides": {},
    },
    {
        "code": "034730", "name": "SK", "sector": "지주",
        "scenario": "자회사 실적 개선", "growth": 10.0,
        "overrides": {},
    },
]


# ---------------------------------------------------------------------------
# 공통 함수 (002에서 가져옴)
# ---------------------------------------------------------------------------
def _quarterlyValues(is_df, snakeId: str, year: str) -> list[float]:
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


# ---------------------------------------------------------------------------
# 단일 기업 분석
# ---------------------------------------------------------------------------
def _analyzeOne(compInfo: dict) -> dict | None:
    """기업 1개 분석 → 결과 dict."""
    from dartlab import Company
    from dartlab.core.finance.proforma import build_proforma

    code = compInfo["code"]
    try:
        c = Company(code)
        ts = c.finance.timeseries
        fullSeries = ts[0] if isinstance(ts, tuple) else ts
        periods = ts[1] if isinstance(ts, tuple) else []
        is_df = c.IS

        # 2023까지 필터
        cutoff = "2023-Q4"
        cutIdx = periods.index(cutoff) + 1 if cutoff in periods else len(periods)
        series = {}
        for stmt in ["IS", "BS", "CF"]:
            series[stmt] = {k: v[:cutIdx] for k, v in fullSeries[stmt].items()}

        # 실적 데이터
        rev2023 = _quarterlyValues(is_df, "sales", "2023")
        oi2023 = _quarterlyValues(is_df, "operating_profit", "2023")
        rev2024 = _quarterlyValues(is_df, "sales", "2024")
        oi2024 = _quarterlyValues(is_df, "operating_profit", "2024")

        if not rev2023 or not rev2024 or not oi2024:
            del c; gc.collect()
            return None

        # 시나리오 3개 (bull = growth×1.5, bear = growth×0.3)
        baseGrowth = compInfo["growth"]
        bullGrowth = baseGrowth * 1.5 if baseGrowth > 0 else baseGrowth * 0.5
        bearGrowth = baseGrowth * 0.3 if baseGrowth > 0 else baseGrowth * 1.5

        pfResults = {}
        for scName, growth in [("bull", bullGrowth), ("base", baseGrowth), ("bear", bearGrowth)]:
            try:
                pf = build_proforma(
                    series,
                    revenue_growth_path=[growth],
                    scenario_name=scName,
                    overrides=compInfo.get("overrides") or None,
                )
                if pf.projections:
                    pfResults[scName] = pf
            except (KeyError, ValueError, ZeroDivisionError, TypeError):
                pass

        if "base" not in pfResults:
            del c; gc.collect()
            return None

        # 계절성 분해
        revW = _seasonality(is_df, "sales", ["2021", "2022", "2023"])
        oiW = _seasonality(is_df, "operating_profit", ["2021", "2022", "2023"])

        # 분기 목표
        qRevTargets = {}
        qOiTargets = {}
        for sc in ["bull", "base", "bear"]:
            pf = pfResults.get(sc)
            if not pf:
                continue
            p = pf.projections[0]
            qRevTargets[sc] = [p.revenue * w for w in revW]
            qOiTargets[sc] = [p.operating_income * w for w in oiW]

        # 분기 판정
        judgments = []
        for q in range(4):
            actualRev = rev2024[q]
            actualOI = oi2024[q]

            revPath = _judge(
                actualRev,
                qRevTargets.get("bull", [0]*4)[q],
                qRevTargets["base"][q],
                qRevTargets.get("bear", [0]*4)[q],
            )
            oiPath = _judge(
                actualOI,
                qOiTargets.get("bull", [0]*4)[q],
                qOiTargets["base"][q],
                qOiTargets.get("bear", [0]*4)[q],
            )
            judgments.append({"q": f"Q{q+1}", "revPath": revPath, "oiPath": oiPath})

        # 연간 요약
        baseP = pfResults["base"].projections[0]
        actualAnnualRev = sum(rev2024)
        actualAnnualOI = sum(oi2024)
        baseAnnualRev = baseP.revenue
        baseAnnualOI = baseP.operating_income

        revDeviation = (actualAnnualRev - baseAnnualRev) / abs(baseAnnualRev) * 100 if baseAnnualRev else 0
        oiDeviation = (actualAnnualOI - baseAnnualOI) / abs(baseAnnualOI) * 100 if baseAnnualOI else 0

        result = {
            "code": code,
            "name": compInfo["name"],
            "sector": compInfo["sector"],
            "scenario": compInfo["scenario"],
            "growth": baseGrowth,
            "baseRevenue_조": round(baseAnnualRev / 1e12, 1),
            "actualRevenue_조": round(actualAnnualRev / 1e12, 1),
            "revDeviation": round(revDeviation, 1),
            "baseOI_조": round(baseAnnualOI / 1e12, 1),
            "actualOI_조": round(actualAnnualOI / 1e12, 1),
            "oiDeviation": round(oiDeviation, 1),
            "judgments": judgments,
            "finalRevPath": judgments[-1]["revPath"] if judgments else "unknown",
            "finalOiPath": judgments[-1]["oiPath"] if judgments else "unknown",
        }

        del c
        gc.collect()
        return result

    except Exception as e:
        print(f"    [ERR] {code}: {e}")
        gc.collect()
        return None


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("107 시나리오 시뮬레이터 — 003 다중 기업 검증")
    print("=" * 70)

    results = []
    for i, comp in enumerate(COMPANIES):
        print(f"\n[{i+1}/{len(COMPANIES)}] {comp['name']} ({comp['code']}) — {comp['scenario']}")
        r = _analyzeOne(comp)
        if r:
            results.append(r)
            print(f"  매출: base {r['baseRevenue_조']}조 vs 실제 {r['actualRevenue_조']}조 ({r['revDeviation']:+.1f}%)")
            print(f"  이익: base {r['baseOI_조']}조 vs 실제 {r['actualOI_조']}조 ({r['oiDeviation']:+.1f}%)")
            qSummary = " → ".join(f"{j['q']}:{j['revPath'][:3]}/{j['oiPath'][:3]}" for j in r["judgments"])
            print(f"  분기: {qSummary}")
        else:
            print(f"  분석 실패")

    # 요약 테이블
    print(f"\n{'='*70}")
    print(f"요약 ({len(results)}개 기업)")
    print(f"{'='*70}")
    print(f"{'기업':10s} {'시나리오':16s} {'매출편차':>8s} {'이익편차':>8s} {'매출최종':>12s} {'이익최종':>12s}")
    print("-" * 70)

    for r in results:
        print(f"{r['name']:10s} {r['scenario']:16s} {r['revDeviation']:>+7.1f}% {r['oiDeviation']:>+7.1f}% {r['finalRevPath']:>12s} {r['finalOiPath']:>12s}")

    # 시나리오 정확도
    print(f"\n--- 시나리오 정확도 ---")
    revOnTrack = sum(1 for r in results if abs(r["revDeviation"]) <= 10)
    oiOnTrack = sum(1 for r in results if abs(r["oiDeviation"]) <= 30)
    n = len(results)
    print(f"  매출 ±10% 이내: {revOnTrack}/{n} ({revOnTrack/n*100:.0f}%)")
    print(f"  이익 ±30% 이내: {oiOnTrack}/{n} ({oiOnTrack/n*100:.0f}%)")

    # 이중 판정의 가치
    print(f"\n--- 이중 판정 차이 (매출 vs 이익이 다른 판정) ---")
    for r in results:
        for j in r["judgments"]:
            if j["revPath"] != j["oiPath"]:
                print(f"  {r['name']} {j['q']}: 매출={j['revPath']:20s} 이익={j['oiPath']}")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "nCompanies": len(results),
        "results": results,
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
