"""
실험 ID: 011
실험명: 오차 기업 1:1 정밀 진단

목적:
- D1/D4에서 오차 >5%인 기업을 하나하나 원본 parquet로 확인
- 오차 원인을 4개 카테고리로 분류:
  A) 매핑 오류 — learnedSynonyms 수정으로 해결 가능
  B) BS 전기비교값 잔여 — majorityEnd 알고리즘 개선 필요
  C) 연결/별도 혼재 — entity 필터링 필요
  D) 원본 데이터 이상 — 해결 불가, 스킵 대상
- 각 기업에 대해 정확한 원인 + 해결책 도출

가설:
1. 대부분 B(전기비교값) 또는 C(연결/별도 혼재)일 것
2. A(매핑 오류)는 008/010에서 대부분 해결됨
3. 기업별 맞춤 처리보다 알고리즘 개선이 효율적

방법:
1. 007 Phase 2에서 오차 >5%인 기업 목록 추출
2. 각 기업 parquet에서 관련 태그의 (fy, fp, end, val) 직접 출력
3. majorityEnd가 올바른 end를 선택했는지 확인
4. 원인 분류 + 해결안 기록

결과 (실험 후 작성):
- D1 오차 기업 12개 + D4 오차 기업 4개 진단 완료
- 근본 원인 3가지 발견:
  1. StockholdersEquity(parent) vs StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest(NCI포함)
     두 태그 모두 total_equity → equity_including_nci로 매핑되어 충돌
     NEE: 8-10%, KHC: 0.4%, TSLA: 1.6-3.3% D1 오차
  2. NoncurrentAssets가 전체 비유동이 아닌 부분 소계인 기업
     META: 36.9%, TSLA: 56.3%, GOOG: 55.2% D4 오차
  3. TemporaryEquity/RedeemableNCI가 BS 등식에서 누락
     NEE: 401M(0.2%), KHC: 6M(0.01%), TSLA: 63M(0.05%)
- majorityEnd 이후 해결된 기업: BKNG, DHR, DUK, EMR, INTU, PYPL, SO (모두 0%)

결론:
- 가설 1 부분 채택: B(전기비교값)는 009에서 해결, 남은 오차는 새 원인 E(equity 충돌)
- 가설 2 기각: 매핑 오류가 아니라 SE/SE_NCI 동일 매핑이 근본 원인
- 가설 3 채택: standardAccounts.json 수정으로 알고리즘 개선 가능
- 해결안 → 012 실험에서 equity 분리 매핑 적용

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dartlab.providers.edgar.finance.mapper import EdgarMapper
from dartlab.providers.edgar.finance.pivot import buildTimeseries

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"

D1_ERROR_TICKERS = {
    "KHC": "0001637459",
    "BKNG": "0001075531",
    "LIN": "0001707925",
    "NEE": "0000753308",
    "EMR": "0000032604",
    "SO": "0000092122",
    "DHR": "0000313616",
    "PYPL": "0001633917",
    "INTU": "0000896878",
    "META": "0001326801",
    "DUK": "0001326160",
}

D4_ERROR_TICKERS = {
    "NEE": "0000753308",
    "PYPL": "0001633917",
    "SO": "0000092122",
    "TSLA": "0001318605",
}

BS_DIAG_TAGS = [
    "Assets",
    "AssetsCurrent",
    "AssetsNoncurrent",
    "NoncurrentAssets",
    "Liabilities",
    "LiabilitiesCurrent",
    "LiabilitiesNoncurrent",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "LiabilitiesAndStockholdersEquity",
]


def diagnoseCompany(ticker: str, cik: str, focusPeriods: list[str] | None = None):
    """한 기업의 BS 태그를 period/end별로 상세 출력."""
    print(f"\n{'='*70}")
    print(f"  {ticker} ({cik})")
    print(f"{'='*70}")

    path = EDGAR_DIR / f"{cik}.parquet"
    if not path.exists():
        print("  파일 없음")
        return

    df = pl.read_parquet(path)
    df = df.filter(
        (pl.col("namespace") == "us-gaap") &
        pl.col("frame").is_null() &
        pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]) &
        pl.col("tag").is_in(BS_DIAG_TAGS)
    ).with_columns(
        (pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period")
    )

    if df.height == 0:
        print("  관련 태그 없음")
        return

    periods = sorted(df.select("period").unique().to_series().to_list())
    if focusPeriods:
        periods = [p for p in periods if p in focusPeriods]
    else:
        periods = periods[-12:]

    for period in periods:
        pDf = df.filter(pl.col("period") == period)
        if pDf.height == 0:
            continue

        endCounts = (
            pDf.group_by("end")
            .agg(pl.col("tag").n_unique().alias("nTags"))
            .sort("nTags", descending=True)
        )
        bestEnd = endCounts.row(0, named=True)["end"]
        nEnds = endCounts.height

        print(f"\n  [{period}] ends={nEnds}, bestEnd={bestEnd}")

        if nEnds > 1:
            for row in endCounts.iter_rows(named=True):
                endDate = row["end"]
                nTags = row["nTags"]
                tags = pDf.filter(pl.col("end") == endDate).select("tag").to_series().to_list()
                marker = " ★" if endDate == bestEnd else ""
                print(f"    end={endDate} ({nTags} tags){marker}: {', '.join(sorted(tags))}")
        else:
            print(f"    end={bestEnd} (전체 일치)")

        for tag in BS_DIAG_TAGS:
            tagRows = pDf.filter(pl.col("tag") == tag)
            if tagRows.height == 0:
                continue
            for row in tagRows.sort("end", descending=True).iter_rows(named=True):
                endDate = row["end"]
                val = row["val"]
                isBest = "★" if endDate == bestEnd else " "
                print(f"    {isBest} {tag:<65s} end={endDate}  val={val:>18,.0f}")


def diagnoseBuildTs(ticker: str, cik: str):
    """buildTimeseries 결과에서 D1/D4 관련 값 확인."""
    ts = buildTimeseries(cik, edgarDir=EDGAR_DIR)
    if ts is None:
        print(f"  buildTimeseries 실패")
        return

    series, periods = ts
    bs = series.get("BS", {})

    ta = bs.get("total_assets")
    eq = bs.get("equity_including_nci")
    tl = bs.get("total_liabilities")
    ca = bs.get("current_assets")
    nca = bs.get("non_current_assets")

    recentPeriods = periods[-8:]
    startIdx = len(periods) - 8

    print(f"\n  buildTimeseries 결과 (최근 8분기):")
    print(f"  {'period':<10s} {'total_assets':>16s} {'equity_nci':>16s} {'total_liab':>16s} {'D1_derived':>16s} {'D1_err':>8s}")
    for i, p in enumerate(recentPeriods):
        j = startIdx + i
        if j < 0:
            continue
        taVal = ta[j] if ta else None
        eqVal = eq[j] if eq else None
        tlVal = tl[j] if tl else None

        d1 = (taVal - eqVal) if (taVal is not None and eqVal is not None) else None

        errStr = ""
        if tlVal is not None and d1 is not None and abs(tlVal) > 0:
            err = abs(d1 - tlVal) / abs(tlVal) * 100
            errStr = f"{err:.1f}%"

        taStr = f"{taVal:>16,.0f}" if taVal is not None else f"{'None':>16s}"
        eqStr = f"{eqVal:>16,.0f}" if eqVal is not None else f"{'None':>16s}"
        tlStr = f"{tlVal:>16,.0f}" if tlVal is not None else f"{'None':>16s}"
        d1Str = f"{d1:>16,.0f}" if d1 is not None else f"{'None':>16s}"

        print(f"  {p:<10s} {taStr} {eqStr} {tlStr} {d1Str} {errStr:>8s}")


def phase1_d1Diagnosis():
    """D1 오차 >5% 기업 진단."""
    print("\n" + "#" * 70)
    print("  Phase 1: D1 오차 기업 정밀 진단")
    print("#" * 70)

    for ticker, cik in sorted(D1_ERROR_TICKERS.items()):
        diagnoseCompany(ticker, cik)
        diagnoseBuildTs(ticker, cik)


def phase2_d4Diagnosis():
    """D4 오차 >5% 기업 진단."""
    print("\n" + "#" * 70)
    print("  Phase 2: D4 오차 기업 정밀 진단")
    print("#" * 70)

    for ticker, cik in sorted(D4_ERROR_TICKERS.items()):
        diagnoseCompany(ticker, cik)
        diagnoseBuildTs(ticker, cik)


if __name__ == "__main__":
    phase1_d1Diagnosis()
    phase2_d4Diagnosis()

    print("\n" + "=" * 70)
    print("완료.")
    print("=" * 70)
