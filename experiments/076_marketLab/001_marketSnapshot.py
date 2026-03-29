"""실험 ID: 001
실험명: 시장 전체 재무 스냅샷 수집

목적:
- 2,700+사의 핵심 재무 비율을 하나의 DataFrame으로 집계
- 시장 전체 분석의 기반 데이터 생성
- 수집 시간, 실패율, 누락 비율 측정

가설:
1. 10분 이내에 2,700사 ratios를 수집하고 parquet로 캐시 가능
2. 실패율 10% 미만 (데이터 없는 종목 제외)
3. 핵심 비율(ROE, 부채비율 등) 커버리지 80%+

방법:
1. dartlab.listing() → 전체 종목 코드 수집
2. finance parquet 직접 로드 → buildTimeseries → calcRatios (Company 미사용, docs 다운로드 방지)
3. sector 분류 별도 추가
4. parquet로 캐시

결과 (실험 후 작성):
- 수집 시간: 128.5s (2,661사, 20.7 co/s)
- 실패: 5건 (0.2%) — 신규 상장 등 finance parquet 미존재
- finance 없음: 151건 (5.7%) — buildTimeseries 결과 None
- 비율별 커버리지:
  - ROE: 86.1%, 부채비율: 83.4%, 영업이익률: 81.3%
  - 총자산: 94.1%, 매출TTM: 88.6%
  - revenueGrowth: 0% (calcRatios 단일 시점에 미포함)
  - PER/PBR: 0% (시가총액 미제공)
- 섹터 분류: 11개 섹터, IT 574 / 산업재 487 / 소재 474 / 건강관리 363
- 기초통계:
  - ROE 중앙값 3.45%, 부채비율 중앙값 64.69%
  - 이상치 존재: ROE -466~365, 부채비율 -5214~4456

결론:
- 채택: 2분 내 2,661사 재무 스냅샷 수집 가능 — 시장 분석 기반으로 충분
- revenueGrowth는 ratioSeries(시계열)에서 추출 필요 → 007에서 처리
- PER/PBR은 시가총액 데이터 별도 수집 필요
- 이상치 클렌징은 002에서 처리

실험일: 2026-03-20
"""

from __future__ import annotations

import sys
import time
from dataclasses import asdict
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# 수집할 비율 필드
RATIO_FIELDS = [
    # 절대값
    "revenueTTM", "operatingIncomeTTM", "netIncomeTTM", "totalAssets", "totalEquity",
    # 수익성
    "roe", "roa", "operatingMargin", "netMargin", "grossMargin", "ebitdaMargin",
    "costOfSalesRatio", "sgaRatio",
    # 안정성
    "debtRatio", "currentRatio", "quickRatio", "equityRatio", "interestCoverage",
    "netDebtRatio", "noncurrentRatio",
    # 성장성
    "revenueGrowth", "operatingProfitGrowth", "netProfitGrowth", "assetGrowth",
    "equityGrowthRate", "revenueGrowth3Y",
    # 효율성
    "totalAssetTurnover", "inventoryTurnover", "receivablesTurnover", "payablesTurnover",
    # 현금흐름
    "fcf", "operatingCfMargin", "operatingCfToNetIncome", "capexRatio", "dividendPayoutRatio",
    # 밸류에이션
    "per", "pbr", "psr", "evEbitda",
]


def collectMarketSnapshot(*, maxCompanies: int | None = None, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사의 재무 비율 + 섹터 정보를 수집하여 DataFrame 반환.

    finance parquet를 직접 로드하여 Company 생성 오버헤드(docs 다운로드)를 회피.
    """
    import dartlab
    from dartlab.core.sector.classifier import classify
    from dartlab.core.finance.ratios import calcRatios
    from dartlab.providers.dart.finance.pivot import buildTimeseries

    kindDf = dartlab.listing()
    codes = kindDf["종목코드"].to_list()
    names = dict(zip(kindDf["종목코드"].to_list(), kindDf["회사명"].to_list()))
    industries = dict(zip(
        kindDf["종목코드"].to_list(),
        kindDf["업종"].to_list() if "업종" in kindDf.columns else [""] * len(codes),
    ))
    products = dict(zip(
        kindDf["종목코드"].to_list(),
        kindDf["주요제품"].to_list() if "주요제품" in kindDf.columns else [""] * len(codes),
    ))

    if maxCompanies is not None:
        codes = codes[:maxCompanies]

    rows: list[dict] = []
    failed: list[str] = []
    noFinance: list[str] = []
    t0 = time.time()

    for i, code in enumerate(codes):
        if verbose and (i + 1) % 200 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(codes) - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{len(codes)}] {elapsed:.0f}s, {rate:.1f} co/s, ETA {eta:.0f}s")

        row: dict = {"stockCode": code, "corpName": names.get(code, "")}

        # sector 분류 (lightweight — KIND 데이터만 사용)
        corpName = names.get(code, "")
        kindIndustry = industries.get(code, "")
        mainProducts = products.get(code, "")
        try:
            sec = classify(corpName, kindIndustry, mainProducts)
            row["sector"] = sec.sector.value if sec and sec.sector else None
            row["industryGroup"] = sec.industryGroup.value if sec and sec.industryGroup else None
        except Exception:
            row["sector"] = None
            row["industryGroup"] = None

        # finance 직접 로드 (buildTimeseries는 stockCode로 parquet 직접 로드)
        try:
            result = buildTimeseries(code)
            if result is None:
                noFinance.append(code)
                for f in RATIO_FIELDS:
                    row[f] = None
                rows.append(row)
                continue

            ts, periods = result
            ratioResult = calcRatios(ts)

            rd = asdict(ratioResult)
            for f in RATIO_FIELDS:
                row[f] = rd.get(f)

        except FileNotFoundError:
            noFinance.append(code)
            for f in RATIO_FIELDS:
                row[f] = None
        except Exception as e:
            failed.append(code)
            for f in RATIO_FIELDS:
                row[f] = None
            if verbose and len(failed) <= 10:
                print(f"  FAIL {code} ({corpName}): {type(e).__name__}: {e}")

        rows.append(row)

    elapsed = time.time() - t0

    df = pl.DataFrame(rows)

    if verbose:
        print(f"\n{'='*60}")
        print(f"수집 완료: {len(rows)}/{len(codes)} ({elapsed:.1f}s, {len(codes)/elapsed:.1f} co/s)")
        print(f"실패: {len(failed)} ({len(failed)/len(codes)*100:.1f}%)")
        print(f"finance 없음: {len(noFinance)} ({len(noFinance)/len(codes)*100:.1f}%)")

        # 비율별 커버리지
        print(f"\n비율별 커버리지 (non-null %):")
        for f in ["roe", "debtRatio", "operatingMargin", "revenueGrowth", "currentRatio",
                   "fcf", "totalAssetTurnover", "per", "grossMargin", "netMargin",
                   "revenueTTM", "totalAssets"]:
            if f in df.columns:
                nonNull = df[f].drop_nulls().len()
                pct = nonNull / len(df) * 100
                print(f"  {f:30s} {nonNull:>5d} / {len(df)} ({pct:.1f}%)")

    return df


def saveSnapshot(df: pl.DataFrame) -> Path:
    """parquet로 저장."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "market_ratios.parquet"
    df.write_parquet(str(path))
    print(f"\n저장: {path} ({df.shape[0]} rows × {df.shape[1]} cols)")
    return path


def loadSnapshot() -> pl.DataFrame | None:
    """캐시된 parquet 로드."""
    path = DATA_DIR / "market_ratios.parquet"
    if not path.exists():
        return None
    return pl.read_parquet(str(path))


if __name__ == "__main__":
    # 소규모 테스트 (20개)
    print("=== 소규모 테스트 (20사) ===")
    testDf = collectMarketSnapshot(maxCompanies=20)
    print(f"\n테스트 shape: {testDf.shape}")
    print(testDf.select(["stockCode", "corpName", "sector", "roe", "debtRatio", "operatingMargin"]))

    # 전체 수집
    print(f"\n{'='*60}")
    print("=== 전체 수집 시작 ===")
    df = collectMarketSnapshot()
    path = saveSnapshot(df)

    # 요약 통계
    print(f"\n=== 요약 통계 ===")
    print(f"총 종목: {df.shape[0]}")
    print(f"총 컬럼: {df.shape[1]}")

    # 섹터별 종목 수
    if "sector" in df.columns:
        sectorCounts = df.group_by("sector").len().sort("len", descending=True)
        print(f"\n섹터별 종목 수:")
        print(sectorCounts)

    # 핵심 비율 기초통계
    print(f"\n핵심 비율 기초통계:")
    for f in ["roe", "debtRatio", "operatingMargin", "revenueGrowth", "currentRatio"]:
        if f in df.columns:
            col = df[f].drop_nulls()
            if col.len() > 0:
                print(f"  {f:25s} mean={col.mean():.2f}  median={col.median():.2f}  "
                      f"std={col.std():.2f}  min={col.min():.2f}  max={col.max():.2f}")
