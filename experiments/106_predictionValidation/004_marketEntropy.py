"""004 — 시장 엔트로피 기반 예측 보정 검증.

003 발견: 전이확률이 시장 base rate(~55% up)로 퇴화.
가설: 시장 전체의 성장률 분포 엔트로피가 낮으면(한 방향 집중),
      base rate 방향으로 예측 신뢰도가 올라가고,
      엔트로피가 높으면 개별 OLS를 따르는 것이 나을 수 있다.

검증 방법:
  - 2022년 전 종목 성장률 분포의 엔트로피 계산
  - 엔트로피 수준에 따라 OLS vs base-rate 전략 분기
  - 2023→2024 테스트

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/004_marketEntropy.py
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
_RESULT_FILE = _ROOT / "entropy_results.json"


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


def _shannonEntropy(values: list[float], nBins: int = 20) -> float:
    """이산화된 값의 Shannon 엔트로피 (bits)."""
    if not values:
        return 0.0
    vMin, vMax = min(values), max(values)
    if vMax == vMin:
        return 0.0
    binWidth = (vMax - vMin) / nBins
    counts = [0] * nBins
    for v in values:
        idx = min(int((v - vMin) / binWidth), nBins - 1)
        counts[idx] += 1
    total = len(values)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return entropy


def _growth(val: float, prevVal: float) -> float:
    if prevVal == 0:
        return 0.0
    g = (val - prevVal) / abs(prevVal) * 100
    return max(-200, min(200, g))


def _direction(growth: float) -> str:
    if growth > 1:
        return "up"
    elif growth < -1:
        return "down"
    return "flat"


def main():
    print("=" * 60)
    print("106 예측 검증 — 004 시장 엔트로피")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n[1/4] 데이터 로드...")
    years, revSeries = _loadAccountSeries("매출액")
    _, oiSeries = _loadAccountSeries("영업이익")
    years = [y for y in years if y != "2025"]
    print(f"  기간: {years}")

    # years = ['2024', '2023', '2022', '2021']
    # 2021→2022 성장률 분포로 엔트로피 계산
    # 2022→2023 성장률 분포로 엔트로피 계산
    # 테스트: 2023→2024

    # 2. 연도별 성장률 분포 + 엔트로피 계산
    print("\n[2/4] 연도별 시장 엔트로피 계산...")

    yearEntropy: dict[str, dict] = {}
    for yIdx in range(len(years) - 1):
        yTo, yFrom = years[yIdx], years[yIdx + 1]
        toIdx, fromIdx = yIdx, yIdx + 1

        growths = []
        upCount = 0
        for series in [revSeries, oiSeries]:
            for code, vals in series.items():
                vTo = vals[toIdx]
                vFrom = vals[fromIdx]
                if vTo is None or vFrom is None:
                    continue
                vTo, vFrom = float(vTo), float(vFrom)
                if abs(vFrom) < 1_000_000_000:
                    continue
                g = _growth(vTo, vFrom)
                growths.append(g)
                if g > 1:
                    upCount += 1

        if not growths:
            continue

        H = _shannonEntropy(growths)
        H_max = math.log2(20)
        H_norm = H / H_max if H_max > 0 else 0
        upRate = upCount / len(growths)
        median = sorted(growths)[len(growths) // 2]

        yearEntropy[f"{yFrom}→{yTo}"] = {
            "entropy": round(H, 3),
            "entropyNorm": round(H_norm, 3),
            "nObs": len(growths),
            "upRate": round(upRate, 3),
            "median": round(median, 1),
            "mean": round(sum(growths) / len(growths), 1),
        }
        print(f"  {yFrom}→{yTo}: H={H:.3f} H_norm={H_norm:.3f} up={upRate:.1%} median={median:.1f}% n={len(growths)}")

    # 3. 엔트로피 기반 전략 테스트 (2023→2024)
    print("\n[3/4] 테스트: 2023→2024")

    # 2022→2023의 엔트로피와 base rate를 사전 정보로 사용
    prior = yearEntropy.get("2022→2023", {})
    priorUpRate = prior.get("upRate", 0.5)
    priorHnorm = prior.get("entropyNorm", 0.5)
    print(f"  사전 정보 (2022→2023): H_norm={priorHnorm:.3f}, upRate={priorUpRate:.1%}")

    testTo, testFrom = years[0], years[1]  # 2024, 2023
    prevYear = years[2]  # 2022
    toIdx, fromIdx, prevIdx = 0, 1, 2

    results = []
    for metric, series, minSize in [
        ("revenue", revSeries, 10_000_000_000),
        ("operatingIncome", oiSeries, 1_000_000_000),
    ]:
        for code, vals in series.items():
            vTo = vals[toIdx]
            vFrom = vals[fromIdx]
            vPrev = vals[prevIdx] if prevIdx < len(vals) else None

            if vTo is None or vFrom is None:
                continue
            vTo, vFrom = float(vTo), float(vFrom)
            if abs(vFrom) < minSize:
                continue

            actualGrowth = _growth(vTo, vFrom)
            actualDir = _direction(actualGrowth)

            # OLS (2021~2023 → predict 2024)
            trainVals = []
            for i in range(fromIdx, len(years)):
                v = vals[i]
                if v is not None:
                    trainVals.append(float(v))
            trainVals.reverse()

            if len(trainVals) >= 2:
                x = list(range(len(trainVals)))
                slope, intercept, r2 = _ols(x, trainVals)
                predicted = slope * len(trainVals) + intercept
                olsGrowth = _growth(predicted, trainVals[-1])
                olsDir = _direction(olsGrowth)
            else:
                olsDir = "flat"
                olsGrowth = 0.0

            # 전략 1: 순수 OLS
            # 전략 2: base rate (항상 up, 가장 빈번한 방향)
            baseDir = "up" if priorUpRate > 0.5 else "down"

            # 전략 3: 엔트로피 적응 전략
            # H_norm 높으면(시장 분산) → OLS 따르기 (개별 기업 특성 중요)
            # H_norm 낮으면(시장 집중) → base rate 따르기
            if priorHnorm > 0.75:
                adaptiveDir = olsDir
            else:
                # base rate가 강하면 base rate, 아니면 OLS
                if abs(priorUpRate - 0.5) > 0.1:
                    adaptiveDir = baseDir
                else:
                    adaptiveDir = olsDir

            # 전략 4: 개별 기업 최근 방향 + 시장 base rate 결합
            if vPrev is not None:
                vPrev = float(vPrev)
                if abs(vPrev) >= minSize:
                    recentGrowth = _growth(vFrom, vPrev)
                    recentDir = _direction(recentGrowth)
                    # 기업 방향과 시장 방향이 일치하면 확신, 불일치하면 시장 우선
                    if recentDir == baseDir:
                        consensusDir = baseDir
                    else:
                        consensusDir = baseDir  # 시장 base rate 우선
                else:
                    consensusDir = baseDir
            else:
                consensusDir = baseDir

            results.append({
                "stockCode": code,
                "metric": metric,
                "actualDir": actualDir,
                "olsDir": olsDir,
                "baseDir": baseDir,
                "adaptiveDir": adaptiveDir,
                "consensusDir": consensusDir,
                "olsCorrect": olsDir == actualDir,
                "baseCorrect": baseDir == actualDir,
                "adaptiveCorrect": adaptiveDir == actualDir,
                "consensusCorrect": consensusDir == actualDir,
            })

    gc.collect()

    # 4. 결과
    n = len(results)
    print(f"\n{'='*60}")
    print(f"전체 관측치: {n}")
    print(f"\n{'전략':<16s} {'정확도':>8s}")
    print("-" * 30)

    strategies = [
        ("ols", "OLS"),
        ("base", "Base Rate(항상up)"),
        ("adaptive", "엔트로피 적응"),
        ("consensus", "시장+기업 결합"),
    ]

    accs = {}
    for key, name in strategies:
        correct = sum(1 for r in results if r[f"{key}Correct"])
        acc = correct / n * 100
        accs[key] = round(acc, 1)
        print(f"  {name:<14s} {acc:>7.1f}%  ({correct}/{n})")

    # 실제 방향별
    print(f"\n--- 실제 방향별 ---")
    for d in ["up", "down", "flat"]:
        subset = [r for r in results if r["actualDir"] == d]
        if not subset:
            continue
        sn = len(subset)
        print(f"  [{d}] n={sn}")
        for key, name in strategies:
            correct = sum(1 for r in subset if r[f"{key}Correct"])
            print(f"    {name:<14s} {correct/sn*100:>7.1f}%")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total": n,
        "accuracy": accs,
        "yearEntropy": yearEntropy,
        "priorUsed": {"Hnorm": priorHnorm, "upRate": priorUpRate},
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")


if __name__ == "__main__":
    main()
