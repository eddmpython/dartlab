"""
실험 ID: 010
실험명: D4 오차 원인 정밀 분석 + non_current_assets 매핑 개선

목적:
- D4(42.9%) 낮은 정확도의 구체적 원인 파악
- CSCO(873%), ABBV(2308%) 등 대형 오차 기업의 원본 XBRL 분석
- non_current_assets 매핑 문제인지, BS 값 선택 문제인지 판별
- 개선안 도출

가설:
1. non_current_assets 보고값이 실제로는 다른 의미의 태그에서 오매핑되었을 가능성
2. AssetsNoncurrent 태그 자체의 end date 불일치 (majorityEnd로도 해결 안 됨)
3. 일부 기업은 AssetsNoncurrent를 보고하지 않고 세부 항목만 보고

방법:
1. Phase 1: D4 오차 >5% 기업 전수 조사 — 어떤 태그가 non_current_assets로 매핑되는지
2. Phase 2: 원본 XBRL에서 Assets, AssetsCurrent, AssetsNoncurrent 직접 비교
3. Phase 3: 오매핑 태그 식별 + 제거/수정안 도출

결과 (2026-03-10):

Phase 1: non_current_assets 매핑 소스 태그 분석
  - D4 오차 상위 10개 기업 중 AssetsNoncurrent 직접 보고: 0개
  - 대신 세부 태그(noncurrent suffix)가 non_current_assets로 오매핑:
    - CSCO: 6개 (NotesAndLoansReceivableNetNoncurrent 등)
    - DIS: 8개 (AccountsReceivableGrossNoncurrent, DeferredRevenueAndCreditsNoncurrent 등)
    - TSLA: 8개 (CryptoAssetFairValueNoncurrent, RestrictedCashAndCashEquivalentsNoncurrent 등)
  - 008과 동일 패턴이나 non_current_assets는 level=2라 008 필터 통과

Phase 2: 원본 XBRL 비교
  - 전 기업 AssetsNoncurrent = None (미보고)
  - Assets, AssetsCurrent는 정상 보고

Phase 3: buildTimeseries 비교
  - 오매핑된 세부 태그 합산값이 non_current_assets로 잡혀 실제 값의 1/50~1/100 수준

010b: 오매핑 제거
  - learnedSynonyms에서 non_current_assets 세부 태그 119개 제거 (10,799 → 10,680)
  - NoncurrentAssets 1개만 남김
  - 007 재검증:
    - D4: 42.9%(27사) → 62.3%(13사) (+19.4%p)
    - D4 커버리지: 보고 81→14%, 파생가능 83% → 파생으로 +70% 커버리지

결론:
- 가설1 채택: 세부 태그(noncurrent suffix)가 합산계정으로 오매핑
- 가설3 채택: 대부분 기업이 AssetsNoncurrent 미보고, 세부 항목만 보고
- 교훈: level=2 합산계정도 세부 태그 유입 가능 — suffix 기반 학습의 체계적 한계
- D4 남은 오차(62.3%): NEE/PYPL/SO 등의 BS 전기비교값 잔여 문제 (특수 entity 구조)

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dartlab.engines.edgar.finance.mapper import EdgarMapper
from dartlab.engines.edgar.finance.pivot import buildTimeseries

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"
TICKERS_PATH = PROJECT_ROOT / "data" / "edgar" / "tickers.parquet"

D4_ERROR_TICKERS = {
    "CSCO": "0000858877",
    "ABBV": "0001551152",
    "TSLA": "0001318605",
    "AVGO": "0001730168",
    "CVS": "0000064803",
    "T": "0000732717",
    "CMCSA": "0001166691",
    "DIS": "0001744489",
    "LOW": "0000060667",
    "KHC": "0001637459",
}


def phase1_tagSource():
    """D4 오차 기업에서 non_current_assets로 매핑되는 태그 확인."""
    print("=" * 70)
    print("Phase 1: non_current_assets 매핑 소스 태그 분석")
    print("=" * 70)

    for ticker, cik in sorted(D4_ERROR_TICKERS.items()):
        path = EDGAR_DIR / f"{cik}.parquet"
        if not path.exists():
            print(f"\n  {ticker}: 파일 없음")
            continue

        df = pl.read_parquet(path)
        df = df.filter(pl.col("namespace") == "us-gaap")

        tags = df.select("tag").unique().to_series().to_list()

        ncaTags = []
        for tag in tags:
            sid = EdgarMapper.mapToDart(tag, "BS")
            if sid == "non_current_assets":
                ncaTags.append(tag)

        print(f"\n  {ticker} ({cik}):")
        print(f"    non_current_assets로 매핑되는 태그 ({len(ncaTags)}개):")
        for tag in sorted(ncaTags):
            rawSid = EdgarMapper.map(tag, "BS")
            isCommon = EdgarMapper.isCommonTag(tag)
            source = "commonTag" if isCommon else "learned"
            count = df.filter(pl.col("tag") == tag).height
            print(f"      {tag:<60s} → {rawSid:<25s} [{source}] ({count}행)")

        assetsNoncurrent = df.filter(pl.col("tag") == "AssetsNoncurrent")
        if assetsNoncurrent.height > 0:
            print(f"    AssetsNoncurrent 직접 존재: {assetsNoncurrent.height}행")
        else:
            print(f"    AssetsNoncurrent 직접 보고 없음")

        assets = df.filter(pl.col("tag") == "Assets")
        assetsCurrent = df.filter(pl.col("tag") == "AssetsCurrent")
        print(f"    Assets: {assets.height}행, AssetsCurrent: {assetsCurrent.height}행")


def phase2_rawComparison():
    """원본 XBRL에서 Assets - AssetsCurrent vs AssetsNoncurrent 직접 비교."""
    print("\n" + "=" * 70)
    print("Phase 2: 원본 XBRL 직접 비교 (D4 오차 기업)")
    print("=" * 70)

    for ticker, cik in sorted(D4_ERROR_TICKERS.items()):
        path = EDGAR_DIR / f"{cik}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(path)
        df = df.filter(
            (pl.col("namespace") == "us-gaap") &
            pl.col("frame").is_null() &
            pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]) &
            pl.col("tag").is_in(["Assets", "AssetsCurrent", "AssetsNoncurrent"])
        ).with_columns(
            (pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period")
        )

        if df.height == 0:
            print(f"\n  {ticker}: 관련 태그 없음")
            continue

        majorityEnd = (
            df.filter(pl.col("end").is_not_null())
            .group_by(["period", "end"])
            .agg(pl.col("tag").n_unique().alias("nTags"))
            .sort(["period", "nTags"], descending=[False, True])
            .group_by("period")
            .agg(pl.col("end").first().alias("bestEnd"))
        )

        matched = df.join(majorityEnd, on="period").filter(
            pl.col("end") == pl.col("bestEnd")
        )
        tagPeriodVals = {}
        for row in matched.sort("filed", descending=True).group_by(["tag", "period"]).agg(
            pl.col("val").first()
        ).iter_rows(named=True):
            tagPeriodVals.setdefault(row["tag"], {})[row["period"]] = row["val"]

        periods = sorted(set(p for tv in tagPeriodVals.values() for p in tv.keys()))

        print(f"\n  {ticker} ({cik}) — 최근 8개 period:")
        recentPeriods = [p for p in periods if not p.endswith("-FY")][-8:]
        errorCount = 0
        totalCount = 0
        for p in recentPeriods:
            a = tagPeriodVals.get("Assets", {}).get(p)
            ac = tagPeriodVals.get("AssetsCurrent", {}).get(p)
            anc = tagPeriodVals.get("AssetsNoncurrent", {}).get(p)

            derived = (a - ac) if (a is not None and ac is not None) else None

            if anc is not None and derived is not None and abs(anc) > 0:
                err = abs(derived - anc) / abs(anc) * 100
                totalCount += 1
                if err > 1.0:
                    errorCount += 1
                errStr = f"  err={err:.1f}%"
            else:
                errStr = ""

            aStr = f"{a:>15,.0f}" if a is not None else f"{'None':>15s}"
            acStr = f"{ac:>15,.0f}" if ac is not None else f"{'None':>15s}"
            ancStr = f"{anc:>15,.0f}" if anc is not None else f"{'None':>15s}"
            dStr = f"{derived:>15,.0f}" if derived is not None else f"{'None':>15s}"

            print(f"    {p:<9s}  Assets={aStr}  Current={acStr}  Noncurrent={ancStr}  Derived={dStr}{errStr}")

        if totalCount > 0:
            print(f"    오차>1%: {errorCount}/{totalCount}")


def phase3_buildTsComparison():
    """buildTimeseries 결과에서 D4 관련 값 직접 확인."""
    print("\n" + "=" * 70)
    print("Phase 3: buildTimeseries 결과 D4 비교")
    print("=" * 70)

    for ticker, cik in sorted(D4_ERROR_TICKERS.items()):
        ts = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        if ts is None:
            print(f"\n  {ticker}: buildTimeseries 실패")
            continue

        series, periods = ts
        bs = series.get("BS", {})

        totalAssets = bs.get("total_assets")
        currentAssets = bs.get("current_assets")
        nca = bs.get("non_current_assets")

        if totalAssets is None:
            print(f"\n  {ticker}: total_assets 없음")
            continue

        recentPeriods = periods[-8:]
        recentIndices = list(range(len(periods) - 8, len(periods)))

        print(f"\n  {ticker}:")
        errorCount = 0
        totalCount = 0
        for idx, p in zip(recentIndices, recentPeriods):
            if idx < 0:
                continue
            ta = totalAssets[idx] if totalAssets else None
            ca = currentAssets[idx] if currentAssets else None
            ncaVal = nca[idx] if nca else None

            derived = (ta - ca) if (ta is not None and ca is not None) else None

            if ncaVal is not None and derived is not None and abs(ncaVal) > 0:
                err = abs(derived - ncaVal) / abs(ncaVal) * 100
                totalCount += 1
                if err > 1.0:
                    errorCount += 1
                errStr = f"  err={err:.1f}%"
            else:
                errStr = ""

            taStr = f"{ta:>15,.0f}" if ta is not None else f"{'None':>15s}"
            caStr = f"{ca:>15,.0f}" if ca is not None else f"{'None':>15s}"
            ncaStr = f"{ncaVal:>15,.0f}" if ncaVal is not None else f"{'None':>15s}"
            dStr = f"{derived:>15,.0f}" if derived is not None else f"{'None':>15s}"

            print(f"    {p:<9s}  total_assets={taStr}  current={caStr}  noncurrent={ncaStr}  derived={dStr}{errStr}")

        if totalCount > 0:
            print(f"    오차>1%: {errorCount}/{totalCount}")


if __name__ == "__main__":
    phase1_tagSource()
    phase2_rawComparison()
    phase3_buildTsComparison()

    print("\n" + "=" * 70)
    print("완료.")
    print("=" * 70)
