"""
실험 ID: 051-004
실험명: US 상장사 재무비율 커버율 (timeseries 기반, 수정 후)

목적:
- USCompany.ratios가 timeseries(분기) 기반으로 변경된 후 커버율 재측정
- interest_expense→finance_costs, interest_income→finance_income alias 효과 확인
- 003 실험과 동일 조건(상장사, 1000 샘플)으로 비교

가설:
1. TTM 기반이므로 커버율 변동 있을 것 (올라갈 수도, 내려갈 수도)
2. finance_costs 커버율이 0%에서 상승

방법:
1. tickers.parquet 상장사 CIK 중 finance parquet 보유 종목
2. buildTimeseries → calcRatios (003은 buildAnnual → calcRatios였음)
3. 동일 SEED=42, 1000개 샘플

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
    import polars as pl
    from dartlab import config
    from dartlab.engines.company.edgar.finance.pivot import buildTimeseries
    from dartlab.engines.common.finance.ratios import RatioResult, calcRatios

    edgarDir = Path(config.dataDir) / "edgar" / "finance"
    tickerPath = Path(config.dataDir) / "edgar" / "tickers.parquet"

    if not edgarDir.exists() or not tickerPath.exists():
        print("EDGAR 데이터 없음")
        return

    tdf = pl.read_parquet(tickerPath)
    tickerCiks = set(tdf["cik"].to_list())
    print(f"tickers.parquet: {len(tickerCiks)}개 CIK (상장사)", flush=True)

    existingCiks = []
    for pq in edgarDir.glob("*.parquet"):
        cik = pq.stem
        if cik in tickerCiks:
            existingCiks.append(cik)

    print(f"finance parquet 보유 상장사: {len(existingCiks)}개", flush=True)

    random.seed(SEED)
    if len(existingCiks) > SAMPLE_SIZE:
        sample = random.sample(existingCiks, SAMPLE_SIZE)
    else:
        sample = existingCiks
    total = len(sample)
    print(f"샘플: {total}개", flush=True)

    ratioFields = [f.name for f in fields(RatioResult) if f.name != "warnings"]

    fieldCount = {name: 0 for name in ratioFields}
    warningCount: dict[str, int] = {}
    successCount = 0
    failCount = 0
    noDataCount = 0
    errors: list[tuple[str, str]] = []

    t0 = time.time()

    for i, cik in enumerate(sample):
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate
            print(f"  [{i+1}/{total}] {elapsed:.0f}s, {rate:.0f}/s, ETA {eta:.0f}s", flush=True)

        try:
            ts = buildTimeseries(cik)
            if ts is None:
                noDataCount += 1
                continue

            series, _ = ts
            r = calcRatios(series)
            if r is None:
                noDataCount += 1
                continue

            successCount += 1
            for name in ratioFields:
                if getattr(r, name) is not None:
                    fieldCount[name] += 1

            for w in r.warnings:
                warningCount[w] = warningCount.get(w, 0) + 1

        except Exception as e:
            failCount += 1
            errors.append((cik, str(e)[:80]))

    elapsed = time.time() - t0

    print(f"\n{'='*60}", flush=True)
    print(f"US 상장사 재무비율 커버율 - timeseries 기반 ({elapsed:.0f}s)")
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
    print(f"{'필드':<40} {'채워짐':>8} {'커버율':>8}")
    print("-" * 60)
    for name in inputFields:
        cnt = fieldCount[name]
        pct = cnt / base * 100
        mark = " ◀ LOW" if pct < 50 else ""
        print(f"{name:<40} {cnt:>8} {pct:>7.1f}%{mark}")

    print()
    print("[ 계산 비율 필드 ]")
    print(f"{'필드':<40} {'채워짐':>8} {'커버율':>8}")
    print("-" * 60)
    for name in ratioCalcFields:
        cnt = fieldCount[name]
        pct = cnt / base * 100
        mark = " ◀ LOW" if pct < 50 else ""
        print(f"{name:<40} {cnt:>8} {pct:>7.1f}%{mark}")

    if warningCount:
        print(f"\n[ 경고 분포 (상위 10개) ]")
        for w, cnt in sorted(warningCount.items(), key=lambda x: -x[1])[:10]:
            print(f"  {cnt:>5}건: {w}")

    if errors:
        print(f"\n[ 에러 종목 (처음 20개) ]")
        for cik, msg in errors[:20]:
            print(f"  {cik}: {msg}")
        if len(errors) > 20:
            print(f"  ... 외 {len(errors)-20}개")


if __name__ == "__main__":
    main()
