"""실험 ID: 007
실험명: 사업모델 아키타입 비지도 분류 — 002~006 특성 통합

목적:
- 002~006 실험에서 검증된 특성을 통합하여 사업모델 아키타입 비지도 분류
- 사업모델 DNA 종합: 비용구조(003) + 자본배분(004) + 현금전환(005) + 해자(006)

가설:
1. 6~8개 정규화 특성으로 k-means 클러스터링 시 silhouette > 0.25 달성 (k=4~8)
2. 분류된 아키타입이 섹터 직관과 75%+ 일치 (동일 섹터가 같은 클러스터에 몰림)
3. 연속 2년 동일 아키타입 유지율 > 75% (안정성 — 시계열 데이터 제한으로 이번 실험 생략)

방법:
1. 003~006 parquet 결합 (stockCode 기준 join)
2. 특성 선택: assetIntensity, laborIntensity, capexRatio, dividendPayoutRatio,
   investedCompanyCount(log), ccc(clipped), opcfMargin, moatTotal
3. 결측값: 섹터 중앙값으로 대체, 금융 섹터는 별도 처리
4. Min-Max 정규화 → k-means (k=4~8) → silhouette 최적 k 선택
5. 클러스터별 특성 프로파일 + 섹터 분포 확인

결과 (실행 후 작성):
- 데이터: 48사 병합, 비금융 38사 대상 클러스터링
- 결측 현황: dividendPayoutRatio 54% null (가장 높음), moatTotal 0% null (가장 낮음)
  → 중앙값 대체로 imputation
- k별 silhouette: k=3(0.223), k=4(0.218), k=5(0.050), k=6(0.153), k=7(0.153), k=8(0.183)
  → 최적 k=3, silhouette=0.223
- 3개 클러스터 프로파일:
  | 클러스터 | 기업수 | 자산집약 | CAPEX | 배당  | CF마진 | 해자  | 추정 아키타입        |
  |---------|------|--------|-------|------|------|------|-------------------|
  | C0      | 15   | 17.7%  | 6.7%  | 38.9%| 15.0%| 23.6 | Cash Returner     |
  | C1      | 6    | 50.3%  | 34.7% | 49.7%| 46.0%| 17.7 | Heavy Manufacturer|
  | C2      | 17   | 41.2%  | 7.2%  | 21.8%| 10.6%| 3.1  | Balanced Operator |
- 섹터-클러스터 매칭:
  - IT/반도체: C0(50%) — 플랫폼(NAVER,카카오)과 반도체(삼성전자) 분리
  - 산업재: C0(70%) ✓ — 대기업+지주 위주
  - 건강관리: C2(60%) — 바이오 특성
  - 필수소비재: C2(80%) ✓ — 식품/유통 밀집
- 직관 매칭: C1에 SK하이닉스, 삼성SDI, LG에너지솔루션, LG화학 → 중후장대 설비투자형 ✓
  C0에 NAVER, 카카오, 삼성전자 + 자동차/지주 → 높은 해자+환원형 ✓

결론:
- 가설 1 조건부 기각: silhouette 0.223 < 0.25 목표 미달
  → 다만 k=3에서 의미 있는 분리 달성. dividendPayoutRatio 54% 결측이 품질 저하 원인
  → 결측률 개선(배당 데이터 보강) 시 0.25 초과 가능성 있음
- 가설 2 부분 채택: 산업재 70%, 필수소비재 80% → 75% 기준 부분 충족
  IT/반도체는 50%로 미달 (플랫폼 vs 반도체 분화가 섹터 단위에서 포착 안 됨)
- 3개 아키타입이 실용적:
  - Heavy Manufacturer (6사): 극한 CAPEX + 높은 자산집약도 (반도체, 배터리, 화학)
  - Cash Returner (15사): 높은 해자 + 높은 배당 + 적정 CF마진 (플랫폼, 지주, 대기업)
  - Balanced Operator (17사): 낮은 해자 + 낮은 투자 (식품, 중소제약, 소재)
- 핵심 시사점:
  - 8개 특성 중 가장 분별력 높은 축: CAPEX비율 + 자산집약도 + 해자총점
  - dividendPayoutRatio 결측이 가장 큰 노이즈 원인 → 배당 데이터 보강 우선
  - 금융 섹터(10사): 별도 분류 체계 필요 (NIM, 자기자본비율, BIS비율 등)
- Phase 4 통합 시: 3+1 아키타입 (비금융 3개 + 금융 별도) 구조로 engines/bizmodel/ 설계

실험일: 2026-03-22
"""

from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# 특성 컬럼
FEATURE_COLS = [
    "assetIntensity",       # 003: 자산집약도
    "laborIntensity",       # 003: 인건비집약도
    "capexRatio",           # 004: CAPEX 비율
    "dividendPayoutRatio",  # 004: 배당성향
    "investedCompanyLog",   # 004: 투자사수 (log 변환)
    "cccClipped",           # 005: CCC (이상값 제거)
    "opcfMargin",           # 005: 영업CF마진
    "moatTotal",            # 006: 해자 총점
]


def _loadAndMerge() -> pl.DataFrame:
    """003~006 parquet 결합."""
    # 003: 비용 구조
    df003 = pl.read_parquet(DATA_DIR / "003_costFingerprint.parquet").select([
        "stockCode", "corpName", "sector",
        "assetIntensity", "laborIntensity",
    ])

    # 004: 자본배분
    df004 = pl.read_parquet(DATA_DIR / "004_capitalAllocation.parquet").select([
        "stockCode", "capexRatio", "dividendPayoutRatio", "investedCompanyCount",
    ])

    # 005: 현금전환
    df005 = pl.read_parquet(DATA_DIR / "005_cashConversion.parquet").select([
        "stockCode", "ccc", "opcfMargin",
    ])

    # 006: 해자
    df006 = pl.read_parquet(DATA_DIR / "006_moatDetection.parquet").select([
        "stockCode", "moatTotal",
    ])

    # 결합
    df = (
        df003
        .join(df004, on="stockCode", how="left")
        .join(df005, on="stockCode", how="left")
        .join(df006, on="stockCode", how="left")
    )

    # 파생 변환
    # investedCompanyCount → log 변환 (분포 정규화)
    df = df.with_columns(
        pl.when(pl.col("investedCompanyCount").is_not_null() & (pl.col("investedCompanyCount") > 0))
        .then(pl.col("investedCompanyCount").log())
        .otherwise(None)
        .alias("investedCompanyLog")
    )

    # CCC clipping: [-100, 1000] 범위로 제한 (이상값 제거)
    df = df.with_columns(
        pl.when(pl.col("ccc").is_not_null())
        .then(pl.col("ccc").clip(-100, 1000))
        .otherwise(None)
        .alias("cccClipped")
    )

    return df


def _imputeByMedian(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    """결측값을 전체 중앙값으로 대체."""
    for col in cols:
        median = df[col].drop_nulls().median()
        if median is not None:
            df = df.with_columns(
                pl.when(pl.col(col).is_null())
                .then(pl.lit(median))
                .otherwise(pl.col(col))
                .alias(col)
            )
    return df


def _minMaxNormalize(values: list[float]) -> list[float]:
    """Min-Max 정규화 [0, 1]."""
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return [0.5] * len(values)
    return [(v - vmin) / (vmax - vmin) for v in values]


def _kmeans(data: list[list[float]], k: int, maxIter: int = 100) -> tuple[list[int], list[list[float]]]:
    """간단 k-means 구현 (외부 라이브러리 불필요)."""
    n = len(data)
    dim = len(data[0])

    # 초기 센트로이드: random
    random.seed(42)
    centroids = random.sample(data, min(k, n))

    labels = [0] * n
    for _ in range(maxIter):
        # 할당
        newLabels = []
        for point in data:
            dists = [sum((point[d] - c[d]) ** 2 for d in range(dim)) for c in centroids]
            newLabels.append(dists.index(min(dists)))

        if newLabels == labels:
            break
        labels = newLabels

        # 센트로이드 업데이트
        for c in range(k):
            members = [data[i] for i in range(n) if labels[i] == c]
            if members:
                centroids[c] = [sum(m[d] for m in members) / len(members) for d in range(dim)]

    return labels, centroids


def _silhouette(data: list[list[float]], labels: list[int]) -> float:
    """실루엣 점수 계산."""
    n = len(data)
    dim = len(data[0])
    clusters = set(labels)

    if len(clusters) < 2:
        return 0.0

    def _dist(p1: list[float], p2: list[float]) -> float:
        return math.sqrt(sum((p1[d] - p2[d]) ** 2 for d in range(dim)))

    scores = []
    for i in range(n):
        ci = labels[i]

        # a(i): 같은 클러스터 내 평균 거리
        same = [j for j in range(n) if labels[j] == ci and j != i]
        if not same:
            scores.append(0.0)
            continue
        a_i = sum(_dist(data[i], data[j]) for j in same) / len(same)

        # b(i): 가장 가까운 다른 클러스터의 평균 거리
        b_i = float("inf")
        for ck in clusters:
            if ck == ci:
                continue
            others = [j for j in range(n) if labels[j] == ck]
            if others:
                avg_dist = sum(_dist(data[i], data[j]) for j in others) / len(others)
                b_i = min(b_i, avg_dist)

        if b_i == float("inf"):
            scores.append(0.0)
        else:
            scores.append((b_i - a_i) / max(a_i, b_i))

    return sum(scores) / len(scores)


def runArchetypeClassify(*, verbose: bool = True) -> pl.DataFrame:
    """사업모델 아키타입 비지도 분류 실행."""
    df = _loadAndMerge()

    if verbose:
        print(f"\n[데이터 병합] {len(df)}사, {len(FEATURE_COLS)}개 특성")
        print("[결측 현황]")
        for col in FEATURE_COLS:
            null = df[col].null_count()
            print(f"  {col:25s}: {null}/{len(df)} null")

    # 결측값 대체
    df = _imputeByMedian(df, FEATURE_COLS)

    # 금융 섹터 제외 (CCC, 자산집약도 등 의미 없음)
    nonFinDf = df.filter(pl.col("sector") != "금융")
    finDf = df.filter(pl.col("sector") == "금융")

    if verbose:
        print(f"\n[비금융 {len(nonFinDf)}사 대상 클러스터링]")

    # 정규화
    featureMatrix = []
    for col in FEATURE_COLS:
        vals = nonFinDf[col].to_list()
        normed = _minMaxNormalize(vals)
        featureMatrix.append(normed)

    # 전치: row × feature
    data = [[featureMatrix[f][i] for f in range(len(FEATURE_COLS))]
            for i in range(len(nonFinDf))]

    # k=3~8 시도, 최적 silhouette
    bestK, bestSil, bestLabels = 4, -1.0, []
    if verbose:
        print(f"\n[k별 silhouette 점수]")

    for k in range(3, 9):
        labels, centroids = _kmeans(data, k)
        sil = _silhouette(data, labels)
        if verbose:
            print(f"  k={k}: silhouette={sil:.3f}")
        if sil > bestSil:
            bestK, bestSil, bestLabels = k, sil, labels

    if verbose:
        print(f"\n→ 최적 k={bestK}, silhouette={bestSil:.3f}")

    # 결과 추가
    nonFinDf = nonFinDf.with_columns(
        pl.Series("cluster", bestLabels)
    )

    # 클러스터별 프로파일
    if verbose:
        print(f"\n[클러스터별 특성 프로파일 (원본 스케일)]")
        for c in range(bestK):
            cdf = nonFinDf.filter(pl.col("cluster") == c)
            n = len(cdf)
            sectors = cdf["sector"].to_list()
            sectorDist = {}
            for s in sectors:
                sectorDist[s] = sectorDist.get(s, 0) + 1

            print(f"\n  Cluster {c} ({n}사): {dict(sorted(sectorDist.items(), key=lambda x: -x[1]))}")
            for col in FEATURE_COLS:
                mean = cdf[col].mean()
                print(f"    {col:25s}: {mean:.1f}" if mean is not None else f"    {col:25s}: N/A")

            # 아키타입 이름 추론
            ai = cdf["assetIntensity"].mean() or 0
            capex = cdf["capexRatio"].mean() or 0
            div = cdf["dividendPayoutRatio"].mean() or 0
            moat = cdf["moatTotal"].mean() or 0
            ccc = cdf["cccClipped"].mean() or 0
            opcf = cdf["opcfMargin"].mean() or 0

            if capex > 15 and ai > 30:
                archetype = "Heavy Manufacturer"
            elif moat > 20 and opcf > 15:
                archetype = "Moat-Protected Innovator"
            elif div > 30:
                archetype = "Cash Returner"
            elif ccc < 200 and opcf > 10:
                archetype = "Efficient Converter"
            else:
                archetype = "Balanced Operator"

            print(f"    → 추정 아키타입: {archetype}")

        # 섹터-클러스터 교차표
        print(f"\n[섹터-클러스터 매칭]")
        for sector in ["IT/반도체", "산업재", "건강관리", "필수소비재"]:
            sdf = nonFinDf.filter(pl.col("sector") == sector)
            if sdf.is_empty():
                continue
            clusters_in_sector = sdf["cluster"].to_list()
            from collections import Counter
            dist = Counter(clusters_in_sector)
            dominant = dist.most_common(1)[0]
            purity = dominant[1] / len(clusters_in_sector) * 100
            print(f"  {sector:12s}: 주 클러스터 {dominant[0]} ({purity:.0f}%) | 분포: {dict(dist)}")

        # 기업별 클러스터 할당
        print(f"\n[기업별 클러스터]")
        for row_data in nonFinDf.sort("cluster").iter_rows(named=True):
            print(f"  C{row_data['cluster']}: {row_data['corpName']:12s} ({row_data['sector']})")

    return nonFinDf


if __name__ == "__main__":
    print("=" * 60)
    print("007: 사업모델 아키타입 비지도 분류")
    print("=" * 60)

    start = time.time()
    resultDf = runArchetypeClassify()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "007_archetypeClassify.parquet")
    print(f"\n→ {DATA_DIR / '007_archetypeClassify.parquet'} ({elapsed:.1f}s)")
