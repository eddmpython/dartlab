"""실험 ID: 010
실험명: 시계열 이상 탐지

목적:
- 2,700사 finance 시계열에서 급변/추세 전환 자동 탐지
- "전년 대비 부채 2배 증가", "매출 반토막" 같은 이벤트 수집
- 시장 전체의 이상 이벤트 분포 파악

가설:
1. 연간 ratios의 전년비 변화율로 이상 이벤트를 자동 탐지할 수 있다
2. 이상 이벤트는 특정 연도(경기 변동)에 집중된다
3. 섹터별로 이상 이벤트 빈도가 다르다

방법:
1. 전체 종목 ratioSeries 수집 → 연도별 핵심 비율 시계열
2. 전년비 변화율 계산
3. Z-score 기반 이상치 탐지 (|Z| > 2)
4. 이벤트 연도/섹터 분포 분석

결과 (실험 후 작성):
- 수집: 20,884건 (2,505종목 × 9년), 123.7s
- 이상 이벤트: 44건 (|Z|>2), 43종목
- 메트릭별: debtRatio 43건 (98%), operatingMargin 1건
- 연도별: 2017 8건, 2021 8건 (경기 변동기에 집중 — 가설2 부분 확인)
- 섹터별: 건강관리 13건(30%), IT 12건(27%) — 변동성 높은 섹터 집중 (가설3 확인)
- Top 급변: 모아라이프플러스 2018 부채비율 +75,093% (Z=122), 애드바이오텍 2025 +28,081% (Z=46)
- ROE yoy 변화는 이상치가 0건 — 비율 변화율의 분포가 너무 넓어 Z>2에 걸리지 않음

결론:
- 채택: 자동 탐지 가능 (가설1), 섹터별 빈도 차이 확인 (가설3)
- 가설2(연도 집중) 부분 확인: 2017/2021에 약간 집중하나 강한 패턴은 아님
- debtRatio가 가장 극단적 변화 — 자본잠식 진입/탈출 기업
- 향후: 절대값 변화(매출 반토막 등)는 기업 규모 정규화 후 별도 탐지 필요

실험일: 2026-03-20
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# 탐지 대상 비율
WATCH_RATIOS = ["roe", "debtRatio", "operatingMargin", "revenueTTM", "totalAssets"]


def collectRatioTimeSeries(*, maxCompanies: int | None = None, verbose: bool = True) -> pl.DataFrame:
    """전체 종목의 연도별 핵심 비율 시계열 수집."""
    import dartlab
    from dartlab.engines.analysis.sector.classifier import classify
    from dartlab.engines.common.finance.ratios import calcRatios
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

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

    if maxCompanies:
        codes = codes[:maxCompanies]

    rows = []
    t0 = time.time()

    for i, code in enumerate(codes):
        if verbose and (i + 1) % 200 == 0:
            elapsed = time.time() - t0
            print(f"  [{i+1}/{len(codes)}] {elapsed:.0f}s")

        result = None
        try:
            result = buildTimeseries(code)
        except Exception:
            continue

        if result is None:
            continue

        ts, periods = result

        # sector
        corpName = names.get(code, "")
        try:
            sec = classify(corpName, industries.get(code, ""), products.get(code, ""))
            sector = sec.sector.value if sec and sec.sector else None
        except Exception:
            sector = None

        # 연도별 비율 계산 — periods에서 연도 추출
        # periods: ["2016-Q1", ..., "2024-Q4"]
        # 각 연도의 Q4(또는 마지막 분기)로 연간 비율 계산
        yearPeriods: dict[str, int] = {}  # year → 최대 period index
        for idx, p in enumerate(periods):
            year = p[:4]
            yearPeriods[year] = idx  # 마지막(최신) 분기 인덱스

        for year, lastIdx in sorted(yearPeriods.items()):
            row = {"stockCode": code, "corpName": corpName, "sector": sector, "year": year}
            for sjDiv, ratioMap in ts.items():
                for snakeId, values in ratioMap.items():
                    if lastIdx < len(values) and values[lastIdx] is not None:
                        # 핵심 비율만 추출
                        mapping = {
                            "sales": "revenueTTM",
                            "revenue": "revenueTTM",
                            "total_assets": "totalAssets",
                            "total_equity": "totalEquity",
                            "equity": "totalEquity",
                            "net_income": "netIncome",
                            "profit_loss": "netIncome",
                            "operating_income": "operatingIncome",
                            "operating_profit": "operatingIncome",
                            "total_liabilities": "totalLiabilities",
                            "liabilities": "totalLiabilities",
                        }
                        if snakeId in mapping:
                            key = mapping[snakeId]
                            if key not in row or row[key] is None:
                                row[key] = values[lastIdx]
            rows.append(row)

    elapsed = time.time() - t0
    if verbose:
        print(f"수집 완료: {len(rows)}건 ({elapsed:.1f}s)")

    return pl.DataFrame(rows)


def computeYoYChanges(df: pl.DataFrame) -> pl.DataFrame:
    """전년비 변화율 계산."""
    # 파생 비율 계산 (컬럼 존재 여부 체크)
    exprs = []
    if "totalLiabilities" in df.columns and "totalAssets" in df.columns:
        # equity = assets - liabilities
        df = df.with_columns(
            (pl.col("totalAssets") - pl.col("totalLiabilities")).alias("totalEquity")
        )
        exprs.append(
            pl.when(pl.col("totalEquity") != 0)
            .then(pl.col("netIncome") / pl.col("totalEquity") * 100)
            .otherwise(None)
            .alias("roe")
        )
        exprs.append(
            pl.when(pl.col("totalEquity") != 0)
            .then(pl.col("totalLiabilities") / pl.col("totalEquity") * 100)
            .otherwise(None)
            .alias("debtRatio")
        )
    if "revenueTTM" in df.columns:
        if "operatingIncome" in df.columns:
            exprs.append(
                pl.when(pl.col("revenueTTM") != 0)
                .then(pl.col("operatingIncome") / pl.col("revenueTTM") * 100)
                .otherwise(None)
                .alias("operatingMargin")
            )
    if exprs:
        df = df.with_columns(exprs)

    metrics = ["revenueTTM", "totalAssets", "roe", "debtRatio", "operatingMargin"]
    result = df.sort(["stockCode", "year"])

    for m in metrics:
        if m not in result.columns:
            continue
        result = result.with_columns(
            pl.col(m).shift(1).over("stockCode").alias(f"{m}_prev")
        )
        result = result.with_columns(
            ((pl.col(m) - pl.col(f"{m}_prev")) / pl.col(f"{m}_prev").abs() * 100)
            .alias(f"{m}_yoy")
        )

    return result


def detectAnomalies(df: pl.DataFrame, zThreshold: float = 2.0) -> pl.DataFrame:
    """Z-score 기반 이상치 탐지."""
    # 비율 변화만 탐지 (절대값은 스케일 차이로 Z-score 무의미)
    yoyCols = [c for c in df.columns if c.endswith("_yoy") and not c.startswith("revenue") and not c.startswith("totalAssets")]
    events = []

    for col in yoyCols:
        metric = col.replace("_yoy", "")
        vals = df[col].drop_nulls().cast(pl.Float64)
        if vals.len() < 10:
            continue
        mean = vals.mean()
        std = vals.std()
        if std == 0 or std is None:
            continue

        anomalies = df.filter(
            pl.col(col).is_not_null()
            & (((pl.col(col) - mean) / std).abs() > zThreshold)
        )

        for row in anomalies.select(
            ["stockCode", "corpName", "sector", "year", col,
             metric if metric in df.columns else col]
        ).iter_rows(named=True):
            zScore = (row[col] - mean) / std
            if zScore != zScore:  # NaN check
                continue
            events.append({
                "stockCode": row["stockCode"],
                "corpName": row["corpName"],
                "sector": row["sector"],
                "year": row["year"],
                "metric": metric,
                "yoyChange": row[col],
                "zScore": zScore,
                "direction": "급증" if zScore > 0 else "급감",
            })

    return pl.DataFrame(events).sort("zScore", descending=True) if events else pl.DataFrame()


if __name__ == "__main__":
    # 시계열 수집
    print("=== 시계열 수집 ===")
    tsDf = collectRatioTimeSeries()
    print(f"shape: {tsDf.shape}")
    print(f"종목: {tsDf['stockCode'].n_unique()}, 연도 범위: {tsDf['year'].min()} ~ {tsDf['year'].max()}")

    # YoY 변화율
    print(f"\n=== YoY 변화율 계산 ===")
    yoyDf = computeYoYChanges(tsDf)

    # 이상치 탐지
    print(f"\n{'='*70}")
    print("이상 이벤트 탐지 (|Z| > 2)")
    print("=" * 70)
    anomalies = detectAnomalies(yoyDf)
    if anomalies.is_empty():
        print("이상 이벤트 없음")
    else:
        print(f"총 이상 이벤트: {anomalies.shape[0]}건")
        print(f"종목: {anomalies['stockCode'].n_unique()}개")

        # 메트릭별 이벤트 수
        print(f"\n메트릭별 이벤트 수:")
        metricCounts = anomalies.group_by("metric").len().sort("len", descending=True)
        print(metricCounts)

        # 연도별 이벤트 수
        print(f"\n연도별 이벤트 수:")
        yearCounts = anomalies.group_by("year").len().sort("year")
        print(yearCounts)

        # 섹터별 이벤트 수
        print(f"\n섹터별 이벤트 수:")
        sectorCounts = anomalies.group_by("sector").len().sort("len", descending=True)
        print(sectorCounts)

        # Top 20 급변 이벤트
        print(f"\n급변 이벤트 Top 20 (|Z| 최대):")
        top = anomalies.sort(pl.col("zScore").abs(), descending=True).head(20)
        print(top.select(["corpName", "year", "metric", "yoyChange", "zScore", "direction"]))
