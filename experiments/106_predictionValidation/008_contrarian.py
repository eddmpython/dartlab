"""008 — 역발상(contrarian) 텍스트 신호 교차 검증.

007 발견: 축소 키워드 우세 기업이 오히려 매출 +16.9% (n=101).
가설:
  H1: "이전 하락 + 축소우세" → 반등(상승) 확률 > base rate
  H2: "이전 상승 + 확장우세" → 둔화/하락 확률 > base rate
  H3: 2개 연도에서 모두 작동 → 우연이 아님

2개 연도 검증:
  Period A: 2021→2022 문서 → 2023 매출
  Period B: 2022→2023 문서 → 2024 매출

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/008_contrarian.py
"""

from __future__ import annotations

import gc
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_RESULT_FILE = _ROOT / "contrarian_results.json"

EXPAND_KW = ["증가", "성장", "확대", "개선", "호조", "신규", "진출", "착공",
             "수주", "상승", "호전", "신설", "확장", "증대", "늘어"]
SHRINK_KW = ["감소", "하락", "축소", "악화", "둔화", "위축", "부진", "철수",
             "중단", "손실", "적자", "폐쇄", "매각", "저하", "줄어"]


def _countKw(text: str | None) -> tuple[int, int]:
    if not text:
        return 0, 0
    return (
        sum(text.count(kw) for kw in EXPAND_KW),
        sum(text.count(kw) for kw in SHRINK_KW),
    )


def _growth(val: float, prevVal: float) -> float:
    if prevVal == 0:
        return 0.0
    return max(-200, min(200, (val - prevVal) / abs(prevVal) * 100))


def _direction(g: float) -> str:
    if g > 1:
        return "up"
    elif g < -1:
        return "down"
    return "flat"


def _binomialTest(k: int, n: int, p0: float) -> float:
    """단순 정규 근사 이항 검정 (z-test). p-value 반환."""
    if n == 0:
        return 1.0
    pHat = k / n
    se = math.sqrt(p0 * (1 - p0) / n)
    if se == 0:
        return 1.0
    z = (pHat - p0) / se
    # 단측 검정 (pHat > p0)
    pValue = 0.5 * (1 + math.erf(-z / math.sqrt(2)))
    return pValue


def _loadRevenueSeries() -> dict[str, dict[str, float]]:
    from dartlab.scan import Scan
    scan = Scan()
    scanResult = scan("account", "매출액")
    revDf = scanResult.df if hasattr(scanResult, "df") else scanResult
    codeCol = "stockCode" if "stockCode" in revDf.columns else revDf.columns[0]
    skipCols = {codeCol, "companyName", "corpName", "종목코드", "회사명", "sector", "업종"}
    qCols = [c for c in revDf.columns if c not in skipCols and c[:1].isdigit()]
    yearSet = set()
    for c in qCols:
        yearSet.add(c[:4])
    years = sorted(yearSet)
    yearQCols = {}
    for y in years:
        yearQCols[y] = sorted([c for c in qCols if c.startswith(y)])
    result: dict[str, dict[str, float]] = {}
    for row in revDf.iter_rows(named=True):
        code = str(row.get(codeCol, ""))
        if not code:
            continue
        annuals = {}
        for y in years:
            qs = yearQCols[y]
            if len(qs) < 4:
                continue
            qvals = [row.get(q) for q in qs]
            if any(v is None for v in qvals):
                continue
            annuals[y] = sum(float(v) for v in qvals)
        if len(annuals) >= 3:
            result[code] = annuals
    del revDf, scanResult
    gc.collect()
    return result


def _analyzeOnePeriod(
    changes: pl.DataFrame,
    revSeries: dict[str, dict[str, float]],
    fromYear: str,
    toYear: str,
    testYear: str,
    prevYear: str,
) -> dict:
    """한 기간의 분석 실행."""

    docChanges = changes.filter(
        (pl.col("fromPeriod") == fromYear) &
        (pl.col("toPeriod") == toYear) &
        (pl.col("changeType") == "wording")
    )

    # 종목별 키워드 집계
    codeKw: dict[str, dict] = defaultdict(lambda: {"expand": 0, "shrink": 0})
    for row in docChanges.iter_rows(named=True):
        code = row["stockCode"]
        if code not in revSeries:
            continue
        preview = row.get("preview") or ""
        e, s = _countKw(preview)
        codeKw[code]["expand"] += e
        codeKw[code]["shrink"] += s

    # 결과 조합
    records = []
    for code, kw in codeKw.items():
        annuals = revSeries.get(code, {})
        if toYear not in annuals or testYear not in annuals or prevYear not in annuals:
            continue
        if abs(annuals[toYear]) < 10_000_000_000:
            continue

        total = kw["expand"] + kw["shrink"]
        if total == 0:
            continue
        expandRatio = kw["expand"] / total

        prevDir = _direction(_growth(annuals[toYear], annuals[prevYear]))
        actualDir = _direction(_growth(annuals[testYear], annuals[toYear]))
        actualGrowth = _growth(annuals[testYear], annuals[toYear])

        kwType = "shrink" if expandRatio < 0.4 else ("expand" if expandRatio > 0.6 else "neutral")

        records.append({
            "code": code,
            "expandRatio": expandRatio,
            "kwType": kwType,
            "prevDir": prevDir,
            "actualDir": actualDir,
            "actualGrowth": actualGrowth,
        })

    n = len(records)
    baseUpRate = sum(1 for r in records if r["actualDir"] == "up") / n if n > 0 else 0

    # H1: 이전 하락 + 축소우세 → 반등?
    h1 = [r for r in records if r["prevDir"] == "down" and r["kwType"] == "shrink"]
    h1_up = sum(1 for r in h1 if r["actualDir"] == "up")
    h1_rate = h1_up / len(h1) if h1 else 0
    h1_p = _binomialTest(h1_up, len(h1), baseUpRate) if h1 else 1.0

    # H2: 이전 상승 + 확장우세 → 하락?
    h2 = [r for r in records if r["prevDir"] == "up" and r["kwType"] == "expand"]
    h2_down = sum(1 for r in h2 if r["actualDir"] == "down")
    baseDownRate = sum(1 for r in records if r["actualDir"] == "down") / n if n > 0 else 0
    h2_rate = h2_down / len(h2) if h2 else 0
    h2_p = _binomialTest(h2_down, len(h2), baseDownRate) if h2 else 1.0

    # 모든 조합
    combos = {}
    for prevD in ["up", "down"]:
        for kwT in ["shrink", "neutral", "expand"]:
            subset = [r for r in records if r["prevDir"] == prevD and r["kwType"] == kwT]
            if not subset:
                continue
            sn = len(subset)
            upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn
            downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn
            avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
            combos[f"{prevD}+{kwT}"] = {
                "n": sn,
                "upRate": round(upRate * 100, 1),
                "downRate": round(downRate * 100, 1),
                "avgGrowth": round(avgGrowth, 1),
            }

    return {
        "period": f"{fromYear}→{toYear} 문서 → {testYear} 매출",
        "n": n,
        "baseUpRate": round(baseUpRate * 100, 1),
        "baseDownRate": round(baseDownRate * 100, 1),
        "H1": {
            "description": f"이전하락+축소우세 → 반등",
            "n": len(h1),
            "upRate": round(h1_rate * 100, 1),
            "pValue": round(h1_p, 4),
            "significant": h1_p < 0.05,
        },
        "H2": {
            "description": f"이전상승+확장우세 → 하락",
            "n": len(h2),
            "downRate": round(h2_rate * 100, 1),
            "pValue": round(h2_p, 4),
            "significant": h2_p < 0.05,
        },
        "combos": combos,
    }


def main():
    print("=" * 60)
    print("106 예측 검증 — 008 역발상 텍스트 신호 교차 검증")
    print("=" * 60)

    # 데이터 로드
    print("\n[1/3] 데이터 로드...")
    changes = pl.read_parquet(str(_DATA / "dart" / "scan" / "changes.parquet"))
    revSeries = _loadRevenueSeries()
    print(f"  changes: {changes.shape[0]:,} 행")
    print(f"  매출: {len(revSeries)} 종목")

    # 2개 연도 검증
    periods = [
        ("2021", "2022", "2023", "2021"),  # 2021→2022 문서 → 2023 매출 (이전=2021→2022)
        ("2022", "2023", "2024", "2022"),  # 2022→2023 문서 → 2024 매출 (이전=2022→2023)
    ]

    results = []
    for fromY, toY, testY, prevY in periods:
        print(f"\n[2/3] 분석: {fromY}→{toY} 문서 → {testY} 매출")
        r = _analyzeOnePeriod(changes, revSeries, fromY, toY, testY, prevY)
        results.append(r)

        print(f"  종목 수: {r['n']}")
        print(f"  Base rate: up={r['baseUpRate']}%, down={r['baseDownRate']}%")
        print(f"\n  H1 (이전하락+축소 → 반등): n={r['H1']['n']}, up={r['H1']['upRate']}%, p={r['H1']['pValue']:.4f} {'✅' if r['H1']['significant'] else '❌'}")
        print(f"  H2 (이전상승+확장 → 하락): n={r['H2']['n']}, down={r['H2']['downRate']}%, p={r['H2']['pValue']:.4f} {'✅' if r['H2']['significant'] else '❌'}")

        print(f"\n  --- 모든 조합 ---")
        print(f"  {'조합':<20s} {'n':>5s} {'up%':>6s} {'down%':>6s} {'평균':>8s}")
        for combo, info in sorted(r["combos"].items()):
            print(f"  {combo:<20s} {info['n']:>5d} {info['upRate']:>5.1f}% {info['downRate']:>5.1f}% {info['avgGrowth']:>+7.1f}%")

    # H3: 일관성 검증
    print(f"\n{'='*60}")
    print(f"[3/3] H3: 2개 연도 일관성 검증")
    print(f"{'='*60}")

    for h in ["H1", "H2"]:
        vals = [r[h] for r in results]
        print(f"\n  {h}: {vals[0]['description']}")
        for i, v in enumerate(vals):
            period = results[i]["period"]
            metric = "upRate" if h == "H1" else "downRate"
            base = results[i]["baseUpRate"] if h == "H1" else results[i]["baseDownRate"]
            print(f"    {period}: {v[metric]}% (base={base}%) n={v['n']} p={v['pValue']:.4f} {'✅' if v['significant'] else '❌'}")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "results": results,
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
