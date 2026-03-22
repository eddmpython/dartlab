"""
실험 ID: 009
실험명: BS 전기비교값 혼입 분석 + _selectBS 개선

목적:
- D1(57.3%), D4(40.8%), R1(61.4%) 낮은 정확도의 근본 원인 정밀 분석
- BS에서 동일 (fy, fp)에 전기/당기 end date가 공존하는 패턴 정량화
- _selectByLatestPeriod() 개선안 도출 및 효과 측정

가설:
1. BS 전기비교값은 특정 태그에서만 발생 (instant vs duration 혼재)
2. end date 필터링으로 전기비교값을 제거하면 D1 정확도 80%+ 달성 가능
3. 해결 키: 각 (fy, fp)마다 "기대되는 end date" 계산 후 매칭

방법:
1. Phase 1: S&P 100에서 BS 전기비교값 패턴 정량 분석
   - 각 (tag, fy, fp)별 end date 분포
   - 전기비교값 비율 (end < 기대 end)
2. Phase 2: end date 필터링 전략 도출
   - 전략A: (fy, fp) → 기대 end date 매칭 (가장 많은 태그가 보고하는 end date)
   - 전략B: start=null (instant) 행만 사용
   - 전략C: fy의 fiscal year end date 기반 필터
3. Phase 3: 개선된 _selectBS로 007 재실행

결과 (2026-03-10):

Phase 1: BS 전기비교값 패턴
  - S&P 100, 총 38,070개 (tag, fy, fp) 조합
  - 단일 end date: 30,503 (80.1%)
  - 복수 end date: 7,567 (19.9%) — 전기비교값 행 추정 14,716개
  - 비회계연도(WMT/LOW/TGT/DE) 특히 심각 (200~313건)
  - StockholdersEquity 태그가 최대 5개 end date 공존 (AAPL 2022-Q2)

Phase 2: 전략 비교 (R1: Liabilities = Assets - Equity(NCI))
  | 전략          | 포인트 | ≤1%          | ≤5%          |
  |--------------|--------|-------------|-------------|
  | baseline     | 2,811  | 1,741(61.9%)| 2,474(88.0%)|
  | majorityEnd  | 2,811  | 2,666(94.8%)| 2,804(99.8%)|
  | instantOnly  | 2,811  | 1,741(61.9%)| 2,474(88.0%)|

Phase 3: majorityEnd 확장 검증
  | 전략/공식     | R1 ≤1% | R1 ≤5% | R4 ≤1% | R4 ≤5% |
  |-------------|--------|--------|--------|--------|
  | baseline    | 61.9%  | 88.0%  | 72.0%  | 75.2%  |
  | majorityEnd | 94.7%  | 99.7%  | 80.8%  | 80.8%  |

결론:
- 가설1 기각: BS 태그는 모두 instant (start=null), instantOnly 전략 무효
- 가설2 채택: majorityEnd로 R1 61.9%→94.8% (+32.9%p), 80%+ 달성
- 가설3 채택: 다수결 end date가 핵심 — 각 (fy, fp)에서 가장 많은 태그가 보고하는 end
- R4가 R1보다 낮은 건 AssetsNoncurrent 미보고 기업 존재 (coverage 한계)
- 다음 단계: pivot.py _selectBS()에 majorityEnd 전략 적용

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

_PROJECT_ROOT = Path(__file__).resolve().parents[7]
_EDGAR_FINANCE = _PROJECT_ROOT / "data" / "edgar" / "finance"
_TICKERS_PATH = _PROJECT_ROOT / "data" / "edgar" / "tickers.parquet"

SP100_TICKERS = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMT", "AMZN",
    "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK-B", "C", "CAT",
    "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS", "CVX",
    "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "EXC", "F", "FDX", "GD",
    "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM", "INTC",
    "INTU", "JNJ", "JPM", "KHC", "KO", "LIN", "LLY", "LMT", "LOW", "MA",
    "MCD", "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS", "MSFT",
    "NEE", "NFLX", "NKE", "NOW", "NVDA", "ORCL", "PEP", "PFE", "PG", "PM",
    "PYPL", "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT", "TMO",
    "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC",
    "WMT", "XOM",
]

BS_TAGS = [
    "Assets", "LiabilitiesAndStockholdersEquity",
    "AssetsCurrent", "AssetsNoncurrent",
    "Liabilities", "LiabilitiesCurrent", "LiabilitiesNoncurrent",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
]


def getTickerCikMap():
    if not _TICKERS_PATH.exists():
        return {}
    df = pl.read_parquet(_TICKERS_PATH)
    result = {}
    for row in df.iter_rows(named=True):
        ticker = row.get("ticker", "")
        cik = row.get("cik", "")
        if ticker and cik:
            result[ticker] = str(cik)
    return result


def loadParquet(cik: str):
    path = _EDGAR_FINANCE / f"{cik}.parquet"
    if not path.exists():
        return None
    return pl.read_parquet(path)


def phase1_analyzePriorPeriod():
    """BS 전기비교값 패턴 정량 분석"""
    print("=" * 70)
    print("Phase 1: BS 전기비교값 패턴 분석")
    print("=" * 70)

    tickerCik = getTickerCikMap()
    totalRows = 0
    priorRows = 0
    multiEndPeriods = 0
    singleEndPeriods = 0
    tickerIssues = Counter()
    endDateCounts = Counter()
    exampleIssues = []

    for ticker in SP100_TICKERS:
        cik = tickerCik.get(ticker)
        if not cik:
            continue
        df = loadParquet(cik)
        if df is None:
            continue

        bsDf = df.filter(
            (pl.col("namespace") == "us-gaap") &
            (pl.col("tag").is_in(BS_TAGS)) &
            (pl.col("frame").is_null()) &
            (pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]))
        )

        if bsDf.height == 0:
            continue

        grouped = bsDf.group_by(["tag", "fy", "fp"]).agg(
            pl.col("end").n_unique().alias("nEnds"),
            pl.col("end").max().alias("maxEnd"),
            pl.col("end").min().alias("minEnd"),
            pl.col("end").count().alias("nRows"),
        )

        for row in grouped.iter_rows(named=True):
            tag = row["tag"]
            fy = row["fy"]
            fp = row["fp"]
            nEnds = row["nEnds"]
            nRows = row["nRows"]
            totalRows += nRows

            if nEnds > 1:
                multiEndPeriods += 1
                priorRows += nRows - 1
                tickerIssues[ticker] += 1
                if len(exampleIssues) < 20:
                    exampleIssues.append({
                        "ticker": ticker, "tag": tag,
                        "fy": fy, "fp": fp,
                        "nEnds": nEnds,
                        "maxEnd": row["maxEnd"],
                        "minEnd": row["minEnd"],
                    })
            else:
                singleEndPeriods += 1

    total = multiEndPeriods + singleEndPeriods
    print(f"\n  총 (tag, fy, fp) 조합: {total}")
    print(f"  단일 end date: {singleEndPeriods} ({singleEndPeriods/total*100:.1f}%)")
    print(f"  복수 end date: {multiEndPeriods} ({multiEndPeriods/total*100:.1f}%)")
    print(f"  전기비교값 행 추정: {priorRows}")

    print(f"\n  기업별 복수 end date 건수 (상위 15):")
    for ticker, count in tickerIssues.most_common(15):
        print(f"    {ticker:<6s}: {count}")

    print(f"\n  예시:")
    for ex in exampleIssues[:10]:
        print(f"    {ex['ticker']:<6s} {ex['tag']:<55s} {ex['fy']}-{ex['fp']:<3s} "
              f"ends={ex['nEnds']} max={ex['maxEnd']} min={ex['minEnd']}")

    return multiEndPeriods


def phase2_endDateStrategy():
    """end date 필터링 전략별 효과 비교"""
    print("\n" + "=" * 70)
    print("Phase 2: end date 필터링 전략 비교")
    print("=" * 70)

    tickerCik = getTickerCikMap()

    formulaTargets = {
        "R1": {"result": "Liabilities", "srcA": "Assets", "srcB": "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "op": "subtract"},
    }

    strategies = {
        "baseline": "현재 방식 (end 내림차순 first)",
        "majorityEnd": "다수결 end date 매칭",
        "instantOnly": "start=null (instant) 행만 사용",
    }

    stratResults = {s: {"total": 0, "within1": 0, "within5": 0} for s in strategies}

    for ticker in SP100_TICKERS:
        cik = tickerCik.get(ticker)
        if not cik:
            continue
        df = loadParquet(cik)
        if df is None:
            continue

        bsDf = df.filter(
            (pl.col("namespace") == "us-gaap") &
            (pl.col("tag").is_in(BS_TAGS)) &
            (pl.col("frame").is_null()) &
            (pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]))
        ).with_columns(
            (pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period")
        )

        if bsDf.height == 0:
            continue

        periods = bsDf.select("period").unique().to_series().to_list()

        for period in periods:
            pDf = bsDf.filter(pl.col("period") == period)

            for stratName in strategies:
                tagVals = _applyStrategy(pDf, stratName)

                rTag = formulaTargets["R1"]["result"]
                aTag = formulaTargets["R1"]["srcA"]
                bTag = formulaTargets["R1"]["srcB"]

                reported = tagVals.get(rTag)
                aVal = tagVals.get(aTag)
                bVal = tagVals.get(bTag)

                if reported is None or aVal is None or bVal is None:
                    continue
                if abs(reported) < 1:
                    continue

                derived = aVal - bVal
                errorPct = abs(derived - reported) / abs(reported) * 100

                sr = stratResults[stratName]
                sr["total"] += 1
                if errorPct <= 1.0:
                    sr["within1"] += 1
                if errorPct <= 5.0:
                    sr["within5"] += 1

    print(f"\n  R1: Liabilities = Assets - StockholdersEquity(NCI)")
    print(f"  {'전략':<20s} {'포인트':>8s} {'≤1%':>8s} {'≤5%':>8s}")
    print(f"  {'-'*50}")
    for stratName, label in strategies.items():
        sr = stratResults[stratName]
        total = sr["total"]
        if total == 0:
            print(f"  {label:<20s} {'0':>8s}")
            continue
        w1 = sr["within1"]
        w5 = sr["within5"]
        print(f"  {stratName:<20s} {total:>8d} {w1:>5d} ({w1/total*100:.1f}%) {w5:>5d} ({w5/total*100:.1f}%)")


def _applyStrategy(pDf: pl.DataFrame, strategy: str) -> dict[str, float]:
    """period 내 태그별 값을 전략에 따라 선택"""
    tagVals = {}

    if strategy == "baseline":
        result = (
            pDf.sort(["end", "filed"], descending=[True, True])
            .group_by("tag")
            .agg(pl.col("val").first().alias("val"))
        )
        for row in result.iter_rows(named=True):
            tagVals[row["tag"]] = row["val"]

    elif strategy == "majorityEnd":
        endCounts = (
            pDf.group_by("end")
            .agg(pl.col("tag").n_unique().alias("nTags"))
            .sort("nTags", descending=True)
        )
        if endCounts.height == 0:
            return tagVals

        bestEnd = endCounts.row(0, named=True)["end"]

        matched = pDf.filter(pl.col("end") == bestEnd)
        for row in matched.group_by("tag").agg(pl.col("val").first()).iter_rows(named=True):
            tagVals[row["tag"]] = row["val"]

        unmatched = pDf.filter(~pl.col("tag").is_in(list(tagVals.keys())))
        if unmatched.height > 0:
            fallback = (
                unmatched.sort(["end", "filed"], descending=[True, True])
                .group_by("tag")
                .agg(pl.col("val").first().alias("val"))
            )
            for row in fallback.iter_rows(named=True):
                tagVals[row["tag"]] = row["val"]

    elif strategy == "instantOnly":
        instant = pDf.filter(pl.col("start").is_null())
        if instant.height == 0:
            instant = pDf

        result = (
            instant.sort(["end", "filed"], descending=[True, True])
            .group_by("tag")
            .agg(pl.col("val").first().alias("val"))
        )
        for row in result.iter_rows(named=True):
            tagVals[row["tag"]] = row["val"]

    return tagVals


def phase3_extendedValidation():
    """majorityEnd 전략으로 5개 공식 전체 재검증"""
    print("\n" + "=" * 70)
    print("Phase 3: majorityEnd 전략 전체 검증")
    print("=" * 70)

    tickerCik = getTickerCikMap()

    RAW_FORMULAS = [
        {"id": "R1", "label": "Liabilities = Assets - Equity(NCI)",
         "result": "Liabilities", "srcA": "Assets",
         "srcB": "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
         "op": "subtract"},
        {"id": "R4", "label": "NoncurrentAssets = Assets - CurrentAssets",
         "result": "AssetsNoncurrent", "srcA": "Assets",
         "srcB": "AssetsCurrent", "op": "subtract"},
    ]

    for strategy in ["baseline", "majorityEnd"]:
        print(f"\n  === {strategy} ===")
        for rf in RAW_FORMULAS:
            total = 0
            within1 = 0
            within5 = 0

            for ticker in SP100_TICKERS:
                cik = tickerCik.get(ticker)
                if not cik:
                    continue
                df = loadParquet(cik)
                if df is None:
                    continue

                bsDf = df.filter(
                    (pl.col("namespace") == "us-gaap") &
                    (pl.col("tag").is_in([rf["result"], rf["srcA"], rf["srcB"]])) &
                    (pl.col("frame").is_null()) &
                    (pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]))
                ).with_columns(
                    (pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period")
                )

                if bsDf.height == 0:
                    continue

                periods = bsDf.select("period").unique().to_series().to_list()

                for period in periods:
                    pDf = bsDf.filter(pl.col("period") == period)
                    tagVals = _applyStrategy(pDf, strategy)

                    reported = tagVals.get(rf["result"])
                    aVal = tagVals.get(rf["srcA"])
                    bVal = tagVals.get(rf["srcB"])

                    if reported is None or aVal is None or bVal is None:
                        continue
                    if abs(reported) < 1:
                        continue

                    derived = aVal - bVal
                    errorPct = abs(derived - reported) / abs(reported) * 100

                    total += 1
                    if errorPct <= 1.0:
                        within1 += 1
                    if errorPct <= 5.0:
                        within5 += 1

            if total > 0:
                print(f"  {rf['id']}: {rf['label']}")
                print(f"    {total} 포인트, ≤1%: {within1}/{total} ({within1/total*100:.1f}%), ≤5%: {within5}/{total} ({within5/total*100:.1f}%)")
            else:
                print(f"  {rf['id']}: 검증 포인트 없음")


if __name__ == "__main__":
    phase1_analyzePriorPeriod()
    phase2_endDateStrategy()
    phase3_extendedValidation()

    print("\n" + "=" * 70)
    print("완료.")
    print("=" * 70)
