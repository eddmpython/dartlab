"""
실험 ID: 051-005
실험명: US 상장사 재무비율 커버율 (annual=True 모드, 최종)

목적:
- calcRatios(annual=True) + buildAnnual(불완전연도 제거) 후 커버율 재측정
- interest→finance alias 효과 확인
- 003 실험(수정 전)과 비교

방법:
1. tickers.parquet 상장사 중 finance parquet 보유 CIK
2. buildAnnual → calcRatios(annual=True)
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
    from dartlab.engines.edgar.finance.pivot import buildAnnual
    from dartlab.engines.common.finance.ratios import RatioResult, calcRatios

    edgarDir = Path(config.dataDir) / "edgar" / "finance"
    tickerPath = Path(config.dataDir) / "edgar" / "tickers.parquet"

    if not edgarDir.exists() or not tickerPath.exists():
        print("EDGAR 데이터 없음")
        return

    tdf = pl.read_parquet(tickerPath)
    tickerCiks = set(tdf["cik"].to_list())

    existingCiks = []
    for pq in edgarDir.glob("*.parquet"):
        cik = pq.stem
        if cik in tickerCiks:
            existingCiks.append(cik)

    total_listed = len(existingCiks)
    print(f"상장사 finance 보유: {total_listed}개", flush=True)

    random.seed(SEED)
    if len(existingCiks) > SAMPLE_SIZE:
        sample = random.sample(existingCiks, SAMPLE_SIZE)
    else:
        sample = existingCiks
    total = len(sample)
    print(f"샘플: {total}개", flush=True)

    ratioFields = [f.name for f in fields(RatioResult) if f.name != "warnings"]
    fieldCount = {name: 0 for name in ratioFields}
    successCount = 0
    noDataCount = 0
    failCount = 0
    errors: list[tuple[str, str]] = []

    t0 = time.time()

    for i, cik in enumerate(sample):
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate
            print(f"  [{i+1}/{total}] {elapsed:.0f}s, {rate:.0f}/s, ETA {eta:.0f}s", flush=True)

        try:
            annual = buildAnnual(cik)
            if annual is None:
                noDataCount += 1
                continue

            aSeries, _ = annual
            r = calcRatios(aSeries, annual=True)

            successCount += 1
            for name in ratioFields:
                if getattr(r, name) is not None:
                    fieldCount[name] += 1

        except Exception as e:
            failCount += 1
            errors.append((cik, str(e)[:80]))

    elapsed = time.time() - t0

    print(f"\n{'='*60}", flush=True)
    print(f"US 상장사 재무비율 커버율 - annual=True ({elapsed:.0f}s)")
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
    print(f"{'필드':<40} {'채워짐':>8} {'커버율':>8}  {'vs 003':>8}")
    print("-" * 68)
    prev = {
        "revenueTTM": 46.1, "operatingIncomeTTM": 51.9, "netIncomeTTM": 70.6,
        "operatingCashflowTTM": 63.3, "investingCashflowTTM": 56.3,
        "totalAssets": 80.7, "totalEquity": 80.5, "totalLiabilities": 80.5,
        "currentAssets": 65.7, "currentLiabilities": 64.9, "cash": 78.5,
        "shortTermBorrowings": 100, "longTermBorrowings": 100, "bonds": 100,
        "grossProfit": 31.3, "costOfSales": 30.0, "sga": 53.7,
        "inventories": 38.5, "receivables": 52.8, "payables": 54.3,
        "tangibleAssets": 66.4, "intangibleAssets": 45.2, "retainedEarnings": 76.2,
        "financeIncome": 0, "financeCosts": 0,
        "capex": 39.0, "dividendsPaid": 21.4,
        "noncurrentAssets": 65.9, "noncurrentLiabilities": 64.5, "netDebt": 100,
    }
    for name in inputFields:
        cnt = fieldCount[name]
        pct = cnt / base * 100
        p = prev.get(name, 0)
        diff = pct - p
        sign = "+" if diff > 0 else ""
        print(f"{name:<40} {cnt:>8} {pct:>7.1f}%  {sign}{diff:>6.1f}p")

    print()
    prev2 = {
        "roe": 54.6, "roa": 53.8, "operatingMargin": 38.2, "netMargin": 45.4,
        "grossMargin": 29.1, "ebitdaMargin": 38.2, "costOfSalesRatio": 27.3,
        "sgaRatio": 39.4, "debtRatio": 78.4, "currentRatio": 64.5,
        "quickRatio": 38.2, "equityRatio": 78.1, "interestCoverage": 0,
        "netDebtRatio": 79.6, "noncurrentRatio": 51.3,
        "revenueGrowth3Y": 55.0,
        "totalAssetTurnover": 43.9, "inventoryTurnover": 24.9,
        "receivablesTurnover": 34.9, "payablesTurnover": 25.1,
        "fcf": 63.3, "operatingCfMargin": 42.9, "operatingCfToNetIncome": 63.3,
        "capexRatio": 29.6, "dividendPayoutRatio": 18.2,
    }
    print("[ 계산 비율 필드 ]")
    print(f"{'필드':<40} {'채워짐':>8} {'커버율':>8}  {'vs 003':>8}")
    print("-" * 68)
    for name in ratioCalcFields:
        cnt = fieldCount[name]
        pct = cnt / base * 100
        p = prev2.get(name, 0)
        diff = pct - p
        sign = "+" if diff > 0 else ""
        print(f"{name:<40} {cnt:>8} {pct:>7.1f}%  {sign}{diff:>6.1f}p")

    if errors:
        print(f"\n[ 에러 종목 (처음 10개) ]")
        for cik, msg in errors[:10]:
            print(f"  {cik}: {msg}")


if __name__ == "__main__":
    main()
