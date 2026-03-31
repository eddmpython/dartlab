"""001 — 전종목 예측 기준선 측정.

현재 dartlab 예측 파이프라인의 핵심 로직을 Scan 데이터만으로 재현하고,
전 종목에 대해 방향 정확도 + MAE를 측정한다.

예측 방법:
  1. 모멘텀 (기존): 최근 2년 연속 방향 → 다음 해 방향 예측
  2. OLS 추세: 연도별 OLS 기울기로 다음 해 값 예측 → 방향 + 오차 측정

측정 기간:
  - Test A: train ≤2022 → predict 2023 vs actual 2023
  - Test B: train ≤2023 → predict 2024 vs actual 2024

메모리 안전: Company 미로드, Scan ratio만 사용.

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/001_baseline.py
    uv run python -X utf8 experiments/106_predictionValidation/001_baseline.py --pilot 100
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_RESULT_FILE = _ROOT / "baseline_results.json"


# ---------------------------------------------------------------------------
# OLS (core/finance/ols.py에서 직접 복사 — import 없이 독립 실행 보장)
# ---------------------------------------------------------------------------
def _ols(x: list[float], y: list[float]) -> tuple[float, float, float]:
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)
    denom = n * sum_x2 - sum_x**2
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, max(0.0, r_squared)


# ---------------------------------------------------------------------------
# Scan 데이터 로드
# ---------------------------------------------------------------------------
def _loadAccountSeries(accountName: str) -> tuple[list[str], dict[str, list[float | None]]]:
    """scan("account", name)으로 전종목 시계열 로드 → 연간 합산.

    분기 데이터(2024Q1~Q4)를 연간 합산하여 반환.
    Q1~Q4 중 하나라도 None이면 해당 연도는 None.

    Returns:
        (years, {stockCode: [val_for_each_year]})
        years[0] = 최신 연도, years[-1] = 가장 오래된 연도
    """
    from dartlab.scan import Scan

    scan = Scan()
    scanResult = scan("account", accountName)
    if scanResult is None:
        return [], {}
    df = scanResult.df if hasattr(scanResult, "df") else scanResult
    if df is None or df.height == 0:
        return [], {}

    codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
    skipCols = {codeCol, "companyName", "corpName", "종목코드", "회사명", "sector", "업종"}
    qCols = [c for c in df.columns if c not in skipCols and c[:1].isdigit()]
    if not qCols:
        return [], {}

    # 연도 추출 (2024Q4 → 2024)
    yearSet: set[str] = set()
    for c in qCols:
        yearSet.add(c[:4])
    years = sorted(yearSet, reverse=True)  # 최신 먼저

    # 연도별 분기 컬럼 매핑
    yearQCols: dict[str, list[str]] = {}
    for y in years:
        qs = sorted([c for c in qCols if c.startswith(y)])  # Q1, Q2, Q3, Q4
        yearQCols[y] = qs

    result: dict[str, list[float | None]] = {}
    for row in df.iter_rows(named=True):
        code = str(row.get(codeCol, ""))
        if not code:
            continue
        annualVals: list[float | None] = []
        for y in years:
            qs = yearQCols[y]
            if len(qs) < 4:
                annualVals.append(None)
                continue
            qvals = [row.get(q) for q in qs]
            if any(v is None for v in qvals):
                annualVals.append(None)
                continue
            annualVals.append(sum(float(v) for v in qvals))
        result[code] = annualVals
    return years, result


def _getValidSeries(
    series: dict[str, list[float | None]],
    periodCols: list[str],
    targetYear: str,
    minTrainYears: int = 3,
) -> dict[str, dict]:
    """targetYear을 테스트로 분리하고, 학습 데이터가 충분한 종목만 반환.

    Returns:
        {stockCode: {"trainYears": [...], "trainVals": [...], "actual": float}}
    """
    if targetYear not in periodCols:
        return {}

    targetIdx = periodCols.index(targetYear)
    result = {}

    for code, vals in series.items():
        actual = vals[targetIdx]
        if actual is None:
            continue
        actual = float(actual)

        # targetYear 이후 (더 오래된) 기간이 학습 데이터
        trainPairs = []
        for i in range(targetIdx + 1, len(periodCols)):
            v = vals[i]
            if v is not None:
                trainPairs.append((periodCols[i], float(v)))

        if len(trainPairs) < minTrainYears:
            continue

        # 시간 순서 정렬 (오래된 → 최신)
        trainPairs.sort(key=lambda p: p[0])
        trainYears = [p[0] for p in trainPairs]
        trainVals = [p[1] for p in trainPairs]

        # 이전 해 값 (targetYear 직전)
        prevVal = None
        if targetIdx + 1 < len(periodCols):
            pv = vals[targetIdx + 1]
            if pv is not None:
                prevVal = float(pv)

        result[code] = {
            "trainYears": trainYears,
            "trainVals": trainVals,
            "actual": actual,
            "prevVal": prevVal,
        }
    return result


# ---------------------------------------------------------------------------
# 생애주기 판정
# ---------------------------------------------------------------------------
def _classifyLifecycle(trainVals: list[float]) -> str:
    """최근 3개 값으로 생애주기 판정."""
    if len(trainVals) < 3:
        return "unknown"
    recent3 = trainVals[-3:]  # 시간순 (오래된→최신)
    g1 = (recent3[1] - recent3[0]) / abs(recent3[0]) if recent3[0] != 0 else 0
    g2 = (recent3[2] - recent3[1]) / abs(recent3[1]) if recent3[1] != 0 else 0

    if g1 > 0.1 and g2 > 0.1:
        return "high_growth"
    elif g1 < -0.05 and g2 < -0.05:
        return "decline"
    elif abs(g1) < 0.05 and abs(g2) < 0.05:
        return "mature"
    else:
        return "transition"


# ---------------------------------------------------------------------------
# 예측 방법들
# ---------------------------------------------------------------------------
def _predictMomentum(trainVals: list[float]) -> str:
    """모멘텀 예측: 최근 2기 연속 방향으로 예측."""
    if len(trainVals) < 3:
        return "flat"
    d1 = trainVals[-1] - trainVals[-2]
    d2 = trainVals[-2] - trainVals[-3]
    if d1 > 0 and d2 > 0:
        return "up"
    elif d1 < 0 and d2 < 0:
        return "down"
    return "flat"


def _predictOls(trainVals: list[float]) -> tuple[str, float, float]:
    """OLS 추세 예측.

    Returns:
        (direction, predictedGrowth%, rSquared)
    """
    n = len(trainVals)
    x = list(range(n))
    slope, intercept, r2 = _ols(x, trainVals)

    # 다음 해 예측값
    predicted = slope * n + intercept
    lastVal = trainVals[-1]

    if lastVal == 0:
        growth = 0.0
    else:
        growth = (predicted - lastVal) / abs(lastVal) * 100
        growth = max(-200, min(200, growth))  # 캡

    if growth > 1:
        direction = "up"
    elif growth < -1:
        direction = "down"
    else:
        direction = "flat"

    return direction, growth, r2


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=int, default=0)
    args = parser.parse_args()

    print("=" * 60)
    print("106 예측 검증 — 001 기준선 측정")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n[1/5] 매출액 시계열 로드...")
    periodCols, revSeries = _loadAccountSeries("매출액")
    print(f"  기간: {periodCols}")
    print(f"  종목 수: {len(revSeries)}")

    if not periodCols or len(periodCols) < 4:
        print("[ERROR] 기간 데이터 부족")
        sys.exit(1)

    print("\n[2/5] 영업이익 시계열 로드...")
    _, oiSeries = _loadAccountSeries("영업이익")
    print(f"  종목 수: {len(oiSeries)}")

    # 2. 테스트 기간 결정
    # 2025년은 미완료 → 제외. 2024, 2023을 테스트 연도로 사용
    testYears = [y for y in periodCols if y in ("2024", "2023")]
    if not testYears:
        # fallback: 최신 완료 연도 2개
        completedYears = [y for y in periodCols if y != periodCols[0]]
        testYears = completedYears[:2]
    print(f"\n[3/5] 테스트 기간: {testYears}")

    # 3. 백테스트 실행
    allResults = []
    lifecycleCounts: dict[str, int] = defaultdict(int)
    lifecycleCorrect: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for metric, series, metricName in [
        ("revenue", revSeries, "매출"),
        ("operatingIncome", oiSeries, "영업이익"),
    ]:
        for testYear in testYears:
            valid = _getValidSeries(series, periodCols, testYear, minTrainYears=2)

            codes = sorted(valid.keys())
            if args.pilot > 0:
                codes = codes[:args.pilot]

            for code in codes:
                info = valid[code]
                trainVals = info["trainVals"]
                actual = info["actual"]
                prevVal = info["prevVal"]

                if prevVal is None or prevVal == 0:
                    continue

                # 소액 필터: 매출 100억 미만 or 영업이익 10억 미만 → 성장률 왜곡
                if metric == "revenue" and abs(prevVal) < 10_000_000_000:
                    continue
                if metric == "operatingIncome" and abs(prevVal) < 1_000_000_000:
                    continue

                # 실제 성장률 및 방향 (±200% 캡)
                actualGrowth = (actual - prevVal) / abs(prevVal) * 100
                actualGrowth = max(-200, min(200, actualGrowth))
                if actualGrowth > 1:
                    actualDir = "up"
                elif actualGrowth < -1:
                    actualDir = "down"
                else:
                    actualDir = "flat"

                # 생애주기
                lifecycle = _classifyLifecycle(trainVals)
                lifecycleCounts[lifecycle] += 1

                # 방법 1: 모멘텀
                momDir = _predictMomentum(trainVals)
                momCorrect = momDir == actualDir

                # 방법 2: OLS 추세
                olsDir, olsGrowth, olsR2 = _predictOls(trainVals)
                olsCorrect = olsDir == actualDir
                olsMae = abs(olsGrowth - actualGrowth)

                if momCorrect:
                    lifecycleCorrect[lifecycle]["momentum"] += 1
                if olsCorrect:
                    lifecycleCorrect[lifecycle]["ols"] += 1

                allResults.append({
                    "stockCode": code,
                    "metric": metric,
                    "testYear": testYear,
                    "lifecycle": lifecycle,
                    "actualGrowth": round(actualGrowth, 2),
                    "actualDir": actualDir,
                    "momDir": momDir,
                    "momCorrect": momCorrect,
                    "olsDir": olsDir,
                    "olsGrowth": round(olsGrowth, 2),
                    "olsR2": round(olsR2, 4),
                    "olsCorrect": olsCorrect,
                    "olsMae": round(olsMae, 2),
                })

    gc.collect()

    if not allResults:
        print("[ERROR] 결과 없음")
        sys.exit(1)

    # 4. 결과 집계
    print(f"\n[4/5] 결과 집계 ({len(allResults)} 관측치)")

    total = len(allResults)
    momTotal = sum(1 for r in allResults if r["momCorrect"])
    olsTotal = sum(1 for r in allResults if r["olsCorrect"])
    olsMaeAvg = sum(r["olsMae"] for r in allResults) / total

    # 방향별
    dirBreakdown: dict[str, dict] = {}
    for d in ["up", "down", "flat"]:
        subset = [r for r in allResults if r["actualDir"] == d]
        if subset:
            dirBreakdown[d] = {
                "count": len(subset),
                "momAcc": round(sum(1 for r in subset if r["momCorrect"]) / len(subset) * 100, 1),
                "olsAcc": round(sum(1 for r in subset if r["olsCorrect"]) / len(subset) * 100, 1),
                "olsMae": round(sum(r["olsMae"] for r in subset) / len(subset), 2),
            }

    # 메트릭별
    metricBreakdown: dict[str, dict] = {}
    for m in ["revenue", "operatingIncome"]:
        subset = [r for r in allResults if r["metric"] == m]
        if subset:
            metricBreakdown[m] = {
                "count": len(subset),
                "momAcc": round(sum(1 for r in subset if r["momCorrect"]) / len(subset) * 100, 1),
                "olsAcc": round(sum(1 for r in subset if r["olsCorrect"]) / len(subset) * 100, 1),
                "olsMae": round(sum(r["olsMae"] for r in subset) / len(subset), 2),
            }

    # 생애주기별
    lifecycleBreakdown: dict[str, dict] = {}
    for lc in ["high_growth", "mature", "transition", "decline", "unknown"]:
        subset = [r for r in allResults if r["lifecycle"] == lc]
        if subset:
            lifecycleBreakdown[lc] = {
                "count": len(subset),
                "momAcc": round(sum(1 for r in subset if r["momCorrect"]) / len(subset) * 100, 1),
                "olsAcc": round(sum(1 for r in subset if r["olsCorrect"]) / len(subset) * 100, 1),
                "olsMae": round(sum(r["olsMae"] for r in subset) / len(subset), 2),
            }

    # 테스트 연도별
    yearBreakdown: dict[str, dict] = {}
    for y in testYears:
        subset = [r for r in allResults if r["testYear"] == y]
        if subset:
            yearBreakdown[y] = {
                "count": len(subset),
                "momAcc": round(sum(1 for r in subset if r["momCorrect"]) / len(subset) * 100, 1),
                "olsAcc": round(sum(1 for r in subset if r["olsCorrect"]) / len(subset) * 100, 1),
                "olsMae": round(sum(r["olsMae"] for r in subset) / len(subset), 2),
            }

    # 5. 출력
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total": total,
        "momentum": {
            "accuracy": round(momTotal / total * 100, 1),
            "correct": momTotal,
        },
        "ols": {
            "accuracy": round(olsTotal / total * 100, 1),
            "correct": olsTotal,
            "maeAvg": round(olsMaeAvg, 2),
        },
        "byDirection": dirBreakdown,
        "byMetric": metricBreakdown,
        "byLifecycle": lifecycleBreakdown,
        "byYear": yearBreakdown,
    }

    print(f"\n{'='*60}")
    print(f"전체 관측치: {total}")
    print(f"\n모멘텀  방향 정확도: {summary['momentum']['accuracy']}%")
    print(f"OLS     방향 정확도: {summary['ols']['accuracy']}%")
    print(f"OLS     MAE 평균:    {summary['ols']['maeAvg']}%p")

    print(f"\n--- 실제 방향별 ---")
    for d, info in dirBreakdown.items():
        print(f"  {d:6s}: n={info['count']:5d}  mom={info['momAcc']:5.1f}%  ols={info['olsAcc']:5.1f}%  mae={info['olsMae']:.1f}%p")

    print(f"\n--- 메트릭별 ---")
    for m, info in metricBreakdown.items():
        print(f"  {m:20s}: n={info['count']:5d}  mom={info['momAcc']:5.1f}%  ols={info['olsAcc']:5.1f}%  mae={info['olsMae']:.1f}%p")

    print(f"\n--- 생애주기별 ---")
    for lc, info in lifecycleBreakdown.items():
        print(f"  {lc:15s}: n={info['count']:5d}  mom={info['momAcc']:5.1f}%  ols={info['olsAcc']:5.1f}%  mae={info['olsMae']:.1f}%p")

    print(f"\n--- 테스트 연도별 ---")
    for y, info in yearBreakdown.items():
        print(f"  {y}: n={info['count']:5d}  mom={info['momAcc']:5.1f}%  ols={info['olsAcc']:5.1f}%  mae={info['olsMae']:.1f}%p")

    # 저장
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
