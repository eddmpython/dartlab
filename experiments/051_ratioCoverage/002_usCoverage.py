"""
실험 ID: 051-002
실험명: US 재무비율 커버율 측정 (1000개 랜덤 샘플)

목적:
- EDGAR CIK 데이터에 대해 ratios 계산이 정상 동작하는지 확인
- 각 비율 필드별 채워진 비율(커버율) 측정
- 에러 발생 종목 파악

가설:
1. 80% 이상에서 ratios 계산 성공
2. 핵심 비율(ROE, ROA, 영업이익률) 커버율 70% 이상

방법:
1. edgar/finance/ 디렉토리에서 1000개 랜덤 샘플링 (CIK당 ~0.5초, 전체 ~8분)
2. buildAnnual(cik) → calcRatios(series) 호출
3. 필드별 None/not-None 집계
4. 에러 종목 기록

결과 (실험 후 작성):

결론:

실험일: 2026-03-10
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import fields
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

SAMPLE_SIZE = 1000
SEED = 42


def main():
    from dartlab import config
    from dartlab.engines.common.finance.ratios import RatioResult, calcRatios
    from dartlab.engines.company.edgar.finance.pivot import buildAnnual

    edgarDir = Path(config.dataDir) / "edgar" / "finance"
    if not edgarDir.exists():
        print(f"EDGAR finance 디렉토리 없음: {edgarDir}")
        return

    allParquets = sorted(edgarDir.glob("*.parquet"))
    totalAll = len(allParquets)

    random.seed(SEED)
    parquets = random.sample(allParquets, min(SAMPLE_SIZE, totalAll))
    total = len(parquets)
    print(f"US EDGAR 전체: {totalAll}개, 샘플: {total}개", flush=True)

    ratioFields = [f.name for f in fields(RatioResult) if f.name != "warnings"]

    fieldCount = {name: 0 for name in ratioFields}
    successCount = 0
    failCount = 0
    noDataCount = 0
    errors: list[tuple[str, str]] = []

    t0 = time.time()

    for i, pq in enumerate(parquets):
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate
            print(f"  [{i+1}/{total}] {elapsed:.0f}s, {rate:.0f}/s, ETA {eta:.0f}s", flush=True)

        cik = pq.stem

        try:
            annual = buildAnnual(cik)
            if annual is None:
                noDataCount += 1
                continue

            aSeries, _ = annual
            r = calcRatios(aSeries)
            if r is None:
                noDataCount += 1
                continue

            successCount += 1
            for name in ratioFields:
                if getattr(r, name) is not None:
                    fieldCount[name] += 1

        except Exception as e:
            failCount += 1
            errors.append((cik, str(e)[:80]))

    elapsed = time.time() - t0

    print(f"\n{'='*60}", flush=True)
    print(f"US 재무비율 커버율 ({elapsed:.0f}s, 샘플 {total}/{totalAll})")
    print(f"{'='*60}")
    print(f"샘플: {total}, 성공: {successCount}, 데이터없음: {noDataCount}, 에러: {failCount}")
    print(f"ratios 계산률: {successCount/total*100:.1f}%")
    print()

    inputFields = []
    ratioCalcFields = []
    for name in ratioFields:
        if name.endswith("TTM") or name in (
            "totalAssets", "totalEquity", "totalLiabilities",
            "currentAssets", "currentLiabilities", "cash",
            "shortTermBorrowings", "longTermBorrowings", "bonds",
            "grossProfit", "costOfSales", "sga", "inventories",
            "receivables", "payables", "tangibleAssets", "intangibleAssets",
            "retainedEarnings", "financeIncome", "financeCosts",
            "capex", "dividendsPaid", "noncurrentAssets", "noncurrentLiabilities",
            "netDebt",
        ):
            inputFields.append(name)
        else:
            ratioCalcFields.append(name)

    base = successCount or 1

    print("[ 입력 데이터 필드 ]")
    print(f"{'필드':<35} {'채워짐':>8} {'커버율':>8}")
    print("-" * 55)
    for name in inputFields:
        cnt = fieldCount[name]
        pct = cnt / base * 100
        print(f"{name:<35} {cnt:>8} {pct:>7.1f}%")

    print()
    print("[ 계산 비율 필드 ]")
    print(f"{'필드':<35} {'채워짐':>8} {'커버율':>8}")
    print("-" * 55)
    for name in ratioCalcFields:
        cnt = fieldCount[name]
        pct = cnt / base * 100
        print(f"{name:<35} {cnt:>8} {pct:>7.1f}%")

    if errors:
        print(f"\n[ 에러 종목 (처음 20개) ]")
        for cik, msg in errors[:20]:
            print(f"  {cik}: {msg}")
        if len(errors) > 20:
            print(f"  ... 외 {len(errors)-20}개")


if __name__ == "__main__":
    main()
