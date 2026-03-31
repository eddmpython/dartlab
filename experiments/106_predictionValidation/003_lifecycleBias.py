"""003 — 생애주기별 방향 보정 + 평균회귀 검증.

001 기준선 발견:
  - 모멘텀 13.5% (역지표!) → 평균회귀가 지배적
  - OLS 47.2% (랜덤 근접) → 하락 예측 34.4%가 취약
  - decline 기업 37.4% → 핵심 약점

검증할 개선안:
  A. 역모멘텀: 모멘텀의 반대 방향으로 예측
  B. 횡단면 전이확률: 연도 N의 방향 → 연도 N+1 실제 방향의 전이 확률 학습
  C. OLS + 전이확률 결합: OLS 방향을 전이확률로 보정

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/003_lifecycleBias.py
"""

from __future__ import annotations

import gc
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_RESULT_FILE = _ROOT / "lifecycle_results.json"


# ---------------------------------------------------------------------------
# OLS (001에서 복사)
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
# 데이터 로드 (001에서 복사)
# ---------------------------------------------------------------------------
def _loadAccountSeries(accountName: str) -> tuple[list[str], dict[str, list[float | None]]]:
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

    yearSet: set[str] = set()
    for c in qCols:
        yearSet.add(c[:4])
    years = sorted(yearSet, reverse=True)

    yearQCols: dict[str, list[str]] = {}
    for y in years:
        qs = sorted([c for c in qCols if c.startswith(y)])
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


# ---------------------------------------------------------------------------
# 방향 판정
# ---------------------------------------------------------------------------
def _direction(val: float, prevVal: float) -> str:
    if prevVal == 0:
        return "flat"
    growth = (val - prevVal) / abs(prevVal) * 100
    if growth > 1:
        return "up"
    elif growth < -1:
        return "down"
    return "flat"


def _growth(val: float, prevVal: float) -> float:
    if prevVal == 0:
        return 0.0
    g = (val - prevVal) / abs(prevVal) * 100
    return max(-200, min(200, g))


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("106 예측 검증 — 003 생애주기별 방향 보정")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n[1/5] 데이터 로드...")
    years, revSeries = _loadAccountSeries("매출액")
    _, oiSeries = _loadAccountSeries("영업이익")
    print(f"  기간: {years}, 매출 {len(revSeries)}개, 영업이익 {len(oiSeries)}개")

    # 2025 제외
    years = [y for y in years if y != "2025"]
    if len(years) < 3:
        print("[ERROR] 연도 부족")
        sys.exit(1)

    # years = ['2024', '2023', '2022', '2021'] (최신 먼저)
    # 학습: 2022→2023 전이확률 학습
    # 테스트: 2023→2024 전이확률로 예측

    trainFrom, trainTo = years[2], years[1]  # 2022→2023
    testFrom, testTo = years[1], years[0]    # 2023→2024

    print(f"\n[2/5] 전이확률 학습: {trainFrom}→{trainTo}")
    print(f"       테스트:       {testFrom}→{testTo}")

    # ---------------------------------------------------------------------------
    # 3. 전이확률 학습 (횡단면)
    # ---------------------------------------------------------------------------
    # direction_from → direction_to 전이 빈도 카운트
    transition: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    # metric별 분리
    metricTransition: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )

    for metric, series, minSize in [
        ("revenue", revSeries, 10_000_000_000),
        ("operatingIncome", oiSeries, 1_000_000_000),
    ]:
        # years 인덱스에서 찾기
        fromIdx = years.index(trainFrom)  # 2022의 인덱스
        toIdx = years.index(trainTo)      # 2023의 인덱스
        # 그 전 해 (2021)
        prevIdx = fromIdx + 1 if fromIdx + 1 < len(years) else None

        for code, vals in series.items():
            # trainFrom(2022) 값과 trainTo(2023) 값이 필요
            vFrom = vals[fromIdx]
            vTo = vals[toIdx]
            if vFrom is None or vTo is None:
                continue

            vFrom, vTo = float(vFrom), float(vTo)
            if abs(vFrom) < minSize:
                continue

            # trainFrom의 이전 해 값으로 trainFrom 방향 판정
            if prevIdx is not None and vals[prevIdx] is not None:
                vPrev = float(vals[prevIdx])
                if abs(vPrev) < minSize:
                    continue
                dirFrom = _direction(vFrom, vPrev)
            else:
                continue

            dirTo = _direction(vTo, vFrom)
            transition[dirFrom][dirTo] += 1
            metricTransition[metric][dirFrom][dirTo] += 1

    # 전이확률 계산
    print("\n[3/5] 전이확률 (횡단면):")
    transProb: dict[str, dict[str, float]] = {}
    for fromDir in ["up", "down", "flat"]:
        counts = transition[fromDir]
        total = sum(counts.values())
        if total == 0:
            continue
        probs = {d: counts[d] / total for d in ["up", "down", "flat"]}
        transProb[fromDir] = probs
        print(f"  {fromDir:6s} → up={probs.get('up',0):.1%}  down={probs.get('down',0):.1%}  flat={probs.get('flat',0):.1%}  (n={total})")

    # 메트릭별 전이확률
    metricTransProb: dict[str, dict[str, dict[str, float]]] = {}
    for m in ["revenue", "operatingIncome"]:
        metricTransProb[m] = {}
        for fromDir in ["up", "down", "flat"]:
            counts = metricTransition[m][fromDir]
            total = sum(counts.values())
            if total > 0:
                metricTransProb[m][fromDir] = {d: counts[d] / total for d in ["up", "down", "flat"]}

    # ---------------------------------------------------------------------------
    # 4. 테스트: 다양한 전략 비교
    # ---------------------------------------------------------------------------
    print(f"\n[4/5] 테스트 실행 ({testFrom}→{testTo})...")

    results = []
    for metric, series, minSize in [
        ("revenue", revSeries, 10_000_000_000),
        ("operatingIncome", oiSeries, 1_000_000_000),
    ]:
        fromIdx = years.index(testFrom)  # 2023
        toIdx = years.index(testTo)      # 2024
        prevIdx = fromIdx + 1 if fromIdx + 1 < len(years) else None  # 2022

        for code, vals in series.items():
            vFrom = vals[fromIdx]
            vTo = vals[toIdx]
            if vFrom is None or vTo is None:
                continue
            vFrom, vTo = float(vFrom), float(vTo)
            if abs(vFrom) < minSize:
                continue

            if prevIdx is None or vals[prevIdx] is None:
                continue
            vPrev = float(vals[prevIdx])
            if abs(vPrev) < minSize:
                continue

            dirCurrent = _direction(vFrom, vPrev)  # 2023의 방향 (2022→2023)
            actualDir = _direction(vTo, vFrom)      # 실제 2024 방향
            actualGrowth = _growth(vTo, vFrom)

            # --- 전략 1: 모멘텀 (현재 방향 유지) ---
            momDir = dirCurrent

            # --- 전략 2: 역모멘텀 (반대 방향) ---
            antiMomDir = {"up": "down", "down": "up", "flat": "flat"}[dirCurrent]

            # --- 전략 3: 전이확률 (가장 높은 확률 방향) ---
            tp = transProb.get(dirCurrent, {"up": 0.33, "down": 0.33, "flat": 0.33})
            transDir = max(tp, key=tp.get)

            # --- 전략 4: 메트릭별 전이확률 ---
            mtp = metricTransProb.get(metric, {}).get(dirCurrent)
            if mtp:
                metricTransDir = max(mtp, key=mtp.get)
            else:
                metricTransDir = transDir

            # --- 전략 5: OLS 추세 ---
            trainVals = []
            for i in range(fromIdx, len(years)):
                v = vals[i]
                if v is not None:
                    trainVals.append(float(v))
            trainVals.reverse()  # 오래된→최신

            if len(trainVals) >= 2:
                x = list(range(len(trainVals)))
                slope, intercept, r2 = _ols(x, trainVals)
                predicted = slope * len(trainVals) + intercept
                olsGrowth = _growth(predicted, trainVals[-1])
                if olsGrowth > 1:
                    olsDir = "up"
                elif olsGrowth < -1:
                    olsDir = "down"
                else:
                    olsDir = "flat"
            else:
                olsDir = "flat"
                olsGrowth = 0.0
                r2 = 0.0

            # --- 전략 6: OLS + 전이확률 결합 ---
            # OLS 방향과 전이확률 방향이 일치하면 채택, 불일치하면 전이확률 우선
            if olsDir == transDir:
                combinedDir = olsDir  # 합의
            else:
                # 전이확률의 가장 높은 확률이 50% 이상이면 전이 우선
                maxTransProb = max(tp.values()) if tp else 0
                if maxTransProb >= 0.5:
                    combinedDir = transDir
                else:
                    combinedDir = olsDir  # 불확실하면 OLS 유지

            results.append({
                "stockCode": code,
                "metric": metric,
                "dirCurrent": dirCurrent,
                "actualDir": actualDir,
                "momDir": momDir,
                "antiMomDir": antiMomDir,
                "transDir": transDir,
                "metricTransDir": metricTransDir,
                "olsDir": olsDir,
                "combinedDir": combinedDir,
                "momCorrect": momDir == actualDir,
                "antiMomCorrect": antiMomDir == actualDir,
                "transCorrect": transDir == actualDir,
                "metricTransCorrect": metricTransDir == actualDir,
                "olsCorrect": olsDir == actualDir,
                "combinedCorrect": combinedDir == actualDir,
            })

    gc.collect()

    if not results:
        print("[ERROR] 결과 없음")
        sys.exit(1)

    # ---------------------------------------------------------------------------
    # 5. 결과 집계
    # ---------------------------------------------------------------------------
    n = len(results)
    strategies = ["mom", "antiMom", "trans", "metricTrans", "ols", "combined"]
    stratNames = {
        "mom": "모멘텀",
        "antiMom": "역모멘텀",
        "trans": "전이확률",
        "metricTrans": "메트릭전이",
        "ols": "OLS",
        "combined": "OLS+전이",
    }

    print(f"\n{'='*60}")
    print(f"전체 관측치: {n}")
    print(f"\n{'전략':<12s} {'정확도':>8s} {'맞음':>6s}")
    print("-" * 30)

    summaryAccs = {}
    for s in strategies:
        correct = sum(1 for r in results if r[f"{s}Correct"])
        acc = correct / n * 100
        summaryAccs[s] = round(acc, 1)
        print(f"  {stratNames[s]:<10s} {acc:>7.1f}% {correct:>5d}/{n}")

    # 방향별 breakdown
    print(f"\n--- 실제 방향별 정확도 ---")
    for d in ["up", "down", "flat"]:
        subset = [r for r in results if r["actualDir"] == d]
        if not subset:
            continue
        print(f"\n  [{d}] n={len(subset)}")
        for s in strategies:
            correct = sum(1 for r in subset if r[f"{s}Correct"])
            acc = correct / len(subset) * 100
            print(f"    {stratNames[s]:<10s} {acc:>7.1f}%")

    # 메트릭별
    print(f"\n--- 메트릭별 정확도 ---")
    for m in ["revenue", "operatingIncome"]:
        subset = [r for r in results if r["metric"] == m]
        if not subset:
            continue
        print(f"\n  [{m}] n={len(subset)}")
        for s in strategies:
            correct = sum(1 for r in subset if r[f"{s}Correct"])
            acc = correct / len(subset) * 100
            print(f"    {stratNames[s]:<10s} {acc:>7.1f}%")

    # 현재 방향별 (어떤 상태에서 출발했는가)
    print(f"\n--- 출발 방향별 정확도 ---")
    for d in ["up", "down", "flat"]:
        subset = [r for r in results if r["dirCurrent"] == d]
        if not subset:
            continue
        print(f"\n  [{d}에서 출발] n={len(subset)}")
        for s in strategies:
            correct = sum(1 for r in subset if r[f"{s}Correct"])
            acc = correct / len(subset) * 100
            print(f"    {stratNames[s]:<10s} {acc:>7.1f}%")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "trainPeriod": f"{trainFrom}→{trainTo}",
        "testPeriod": f"{testFrom}→{testTo}",
        "total": n,
        "accuracy": summaryAccs,
        "transitionProb": {
            k: {k2: round(v2, 3) for k2, v2 in v.items()}
            for k, v in transProb.items()
        },
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
