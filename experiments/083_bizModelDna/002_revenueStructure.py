"""실험 ID: 002
실험명: 매출 구조 추출 — finance 비율 기반 vs Company.show 기반

목적:
- 사업모델 DNA의 첫 번째 축인 "매출 구조"를 자동 추출하는 방법론 비교
- 경량 접근(finance 비율만)과 정밀 접근(segments/salesOrder 토픽)의 정보량 차이 측정

가설:
1. finance 비율(grossMargin, sgaRatio, costOfSalesRatio)만으로 섹터 간 매출 구조 차이를 80%+ 구분 가능
2. Company.show("segments")에서 실제 사업부문 매출 비중(HHI) 추출이 가능한 기업이 50% 이상

방법:
1. 경량 접근: 50사의 finance 비율을 buildTimeseries + calcRatios로 수집
   - grossMargin, sgaRatio, costOfSalesRatio, operatingMargin, ebitdaMargin
   - 이 5개 비율로 섹터 간 분리도(F-statistic) 측정
2. 정밀 접근: 5사(섹터당 1사)에 대해 Company.show("segments") 로드
   - 부문별 매출 비중 추출 가능 여부 확인
   - HHI(허핀달-허쉬만 지수) 계산

결과 (실험 후 작성):
- PART 1: 경량 접근 (8.2s, 50사)
  - 섹터별 평균:
    | 섹터           | grossMargin | sgaRatio | costOfSales | opMargin | ebitda |
    |---------------|-------------|----------|-------------|----------|--------|
    | IT/반도체       | 34.1%       | 19.9%    | 65.9%       | 12.6%    | 22.2%  |
    | 산업재/자동차    | 37.6%       | 16.9%    | 175.6%      | 22.1%    | 25.5%  |
    | 건강관리/제약    | 150.1%      | 80.3%    | 105.9%      | 45.4%    | 54.7%  |
    | 금융           | N/A         | N/A      | N/A         | N/A      | N/A    |
    | 필수소비재/식품  | 26.6%       | 17.3%    | 67.5%       | 7.9%     | 10.7%  |
  - 금융 섹터: 모든 비율 N/A → 매출/원가 구조가 일반 기업과 다름
  - 건강관리/제약: grossMargin 150% → 재무제표 구조 차이 (매출원가 vs 영업비용 분류)
  - 산업재 costOfSalesRatio 175% → 일부 기업 데이터 이상값 존재
  - F-statistic: grossMargin 1.52, sgaRatio 1.54 → 분리도 낮음 (F > 2.5 필요)
    → 단일 비율로는 섹터 간 구분 불충분. 다차원 조합 필요.

- PART 2: 정밀 접근 (19.6s, 5사)
  - segments 가용: 0/5사 (삼성전자, 현대차, 셀트리온, KB금융, CJ제일제당)
  - 모든 기업에서 topics 목록에 "부문" 없음 (47~49개 토픽 존재)
  - 원인: sections 수평화에서 segments가 독립 토픽으로 추출되지 않음
    (사업보고서 K-IFRS 주석의 부문정보는 notes.segments 경로일 수 있음)

결론:
- 가설 1 기각: 단일 비율(grossMargin 등)의 F-statistic < 2로 섹터 간 80% 구분 불가
  → 다차원 특성 벡터(5~8개 비율 조합) + 클러스터링 필요 (007에서 검증)
- 가설 2 기각: segments 토픽 가용 0/5사 → Company.show("segments") 경로 불가
  → 사업모델 DNA의 "매출 구조" 축은 finance 비율 조합으로만 근사해야 함
  → 부문 매출 세분화(HHI)는 K-IFRS 주석(notes.segments) 또는 원본 텍스트 파싱 필요
- 금융 섹터: 모든 비율 N/A → 매출 구조 분류에서 별도 경로 필요
- 핵심 시사점: Phase 1 007_archetypeClassify에서 finance 비율 5~8개 조합 + PCA/클러스터링으로
  segments 없이도 사업모델 분류를 시도해야 함

실험일: 2026-03-22
"""

from __future__ import annotations

import sys
import time
from dataclasses import asdict
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# 001에서 검증된 50사 목록 (재사용)
SECTOR_COMPANIES = {
    "IT/반도체": [
        ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "NAVER"),
        ("035720", "카카오"), ("006400", "삼성SDI"), ("247540", "에코프로비엠"),
        ("373220", "LG에너지솔루션"), ("068270", "셀트리온"),
        ("207940", "삼성바이오로직스"), ("036570", "엔씨소프트"),
    ],
    "산업재/자동차": [
        ("005380", "현대차"), ("000270", "기아"), ("012330", "현대모비스"),
        ("010130", "고려아연"), ("051910", "LG화학"), ("011170", "롯데케미칼"),
        ("003550", "LG"), ("034730", "SK"), ("028260", "삼성물산"),
        ("009150", "삼성전기"),
    ],
    "건강관리/제약": [
        ("068270", "셀트리온"), ("207940", "삼성바이오로직스"), ("326030", "SK바이오팜"),
        ("128940", "한미약품"), ("006280", "녹십자"), ("000100", "유한양행"),
        ("185750", "종근당"), ("003060", "에이치엘비"), ("145720", "덴티움"),
        ("214150", "클래시스"),
    ],
    "금융": [
        ("105560", "KB금융"), ("055550", "신한지주"), ("086790", "하나금융지주"),
        ("316140", "우리금융지주"), ("024110", "기업은행"), ("138930", "BNK금융지주"),
        ("175330", "JB금융지주"), ("032830", "삼성생명"), ("000810", "삼성화재"),
        ("088350", "한화생명"),
    ],
    "필수소비재/식품": [
        ("097950", "CJ제일제당"), ("004370", "농심"), ("271560", "오리온"),
        ("280360", "롯데웰푸드"), ("005300", "롯데칠성"), ("007310", "오뚜기"),
        ("003230", "삼양식품"), ("002270", "롯데지주"), ("001040", "CJ"),
        ("282330", "BGF리테일"),
    ],
}

# 매출 구조 프록시 비율
REVENUE_RATIO_FIELDS = [
    "grossMargin", "sgaRatio", "costOfSalesRatio",
    "operatingMargin", "netMargin", "ebitdaMargin",
    "totalAssetTurnover", "revenueTTM",
]


def collectRevenueRatios(*, verbose: bool = True) -> pl.DataFrame:
    """50사 finance 비율 수집 (경량 접근)."""
    from dartlab.engines.common.finance.ratios import calcRatios
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

    rows = []
    for sector, companies in SECTOR_COMPANIES.items():
        for stockCode, corpName in companies:
            row: dict = {"stockCode": stockCode, "corpName": corpName, "sector": sector}

            try:
                result = buildTimeseries(stockCode)
                if result is None:
                    for f in REVENUE_RATIO_FIELDS:
                        row[f] = None
                    rows.append(row)
                    continue

                series, _periods = result
                ratios = calcRatios(series)
                rd = asdict(ratios)
                for f in REVENUE_RATIO_FIELDS:
                    row[f] = rd.get(f)

            except (FileNotFoundError, RuntimeError, OSError):
                for f in REVENUE_RATIO_FIELDS:
                    row[f] = None

            rows.append(row)

    df = pl.DataFrame(rows)

    if verbose:
        print("\n[매출 구조 비율 — 섹터별 평균]")
        print(f"{'섹터':20s} | {'grossMargin':>12s} | {'sgaRatio':>10s} | {'costOfSales':>12s} | {'opMargin':>10s} | {'ebitda':>8s}")
        print("-" * 90)

        for sector in SECTOR_COMPANIES:
            sdf = df.filter(pl.col("sector") == sector)
            gm = sdf["grossMargin"].drop_nulls().mean()
            sga = sdf["sgaRatio"].drop_nulls().mean()
            cos = sdf["costOfSalesRatio"].drop_nulls().mean()
            om = sdf["operatingMargin"].drop_nulls().mean()
            eb = sdf["ebitdaMargin"].drop_nulls().mean()
            print(f"{sector:20s} | {_fmt(gm):>12s} | {_fmt(sga):>10s} | {_fmt(cos):>12s} | {_fmt(om):>10s} | {_fmt(eb):>8s}")

        # F-statistic으로 섹터 간 분리도 측정 (간단 구현)
        print("\n[섹터 간 분리도 (F-statistic 근사)]")
        for ratio in ["grossMargin", "operatingMargin", "ebitdaMargin", "costOfSalesRatio", "sgaRatio"]:
            f_stat = _approxFStat(df, ratio, "sector")
            print(f"  {ratio:20s}: F ≈ {f_stat:.2f}" if f_stat is not None else f"  {ratio:20s}: 데이터 부족")

    return df


def _fmt(val) -> str:
    return f"{val:.1f}%" if val is not None else "N/A"


def _approxFStat(df: pl.DataFrame, col: str, groupCol: str) -> float | None:
    """간단 F-statistic 근사. ANOVA 대용."""
    valid = df.filter(pl.col(col).is_not_null())
    if len(valid) < 10:
        return None

    grandMean = valid[col].mean()
    groups = valid.group_by(groupCol).agg([
        pl.col(col).mean().alias("mean"),
        pl.col(col).len().alias("n"),
    ])

    # Between-group SS
    ssb = sum(
        row["n"] * (row["mean"] - grandMean) ** 2
        for row in groups.iter_rows(named=True)
        if row["mean"] is not None
    )

    # Within-group SS
    ssw = 0.0
    for row in groups.iter_rows(named=True):
        grpData = valid.filter(pl.col(groupCol) == row[groupCol])[col].to_list()
        ssw += sum((v - row["mean"]) ** 2 for v in grpData if v is not None)

    k = len(groups)  # 그룹 수
    n = len(valid)    # 전체 수

    if k <= 1 or n <= k or ssw == 0:
        return None

    msb = ssb / (k - 1)
    msw = ssw / (n - k)

    return msb / msw if msw > 0 else None


def checkSegmentsAvailability(*, verbose: bool = True) -> dict:
    """5사(섹터당 1사) Company.show("segments") 가용성 확인 (정밀 접근)."""
    import warnings

    import dartlab

    # 섹터당 1사 (대표 대형주)
    sampleCompanies = [
        ("005930", "삼성전자", "IT/반도체"),
        ("005380", "현대차", "산업재/자동차"),
        ("068270", "셀트리온", "건강관리/제약"),
        ("105560", "KB금융", "금융"),
        ("097950", "CJ제일제당", "필수소비재/식품"),
    ]

    results = {}
    for stockCode, corpName, sector in sampleCompanies:
        if verbose:
            print(f"\n{'─'*40}")
            print(f"{corpName} ({stockCode}) — {sector}")
            print(f"{'─'*40}")

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                c = dartlab.Company(stockCode)

            # topics 확인
            topics = c.topics if hasattr(c, "topics") else []
            segmentTopics = [t for t in topics if "부문" in str(t) or "segment" in str(t).lower()]

            if verbose:
                print(f"  전체 topics: {len(topics)}개")
                print(f"  부문 관련: {segmentTopics}")

            # show("segments") 시도
            segDf = None
            try:
                segDf = c.show("segments")
            except (ValueError, KeyError, AttributeError):
                pass

            if segDf is not None and isinstance(segDf, pl.DataFrame) and not segDf.is_empty():
                if verbose:
                    print(f"  segments: {segDf.shape}")
                    print(f"  컬럼: {segDf.columns[:8]}")
                results[stockCode] = {
                    "corpName": corpName, "sector": sector,
                    "hasSegments": True, "shape": segDf.shape,
                    "columns": segDf.columns,
                }
            else:
                if verbose:
                    print("  segments: None 또는 빈 DataFrame")
                results[stockCode] = {
                    "corpName": corpName, "sector": sector,
                    "hasSegments": False,
                }

            # 메모리 해제
            del c
        except (RuntimeError, OSError, FileNotFoundError) as e:
            if verbose:
                print(f"  로드 실패: {e}")
            results[stockCode] = {
                "corpName": corpName, "sector": sector,
                "hasSegments": False, "error": str(e),
            }

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("PART 1: 경량 접근 — finance 비율 기반 매출 구조")
    print("=" * 60)

    start = time.time()
    ratioDf = collectRevenueRatios()
    elapsed1 = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ratioDf.write_parquet(DATA_DIR / "002_revenueRatios.parquet")
    print(f"\n→ {DATA_DIR / '002_revenueRatios.parquet'} ({elapsed1:.1f}s)")

    print("\n" + "=" * 60)
    print("PART 2: 정밀 접근 — Company.show('segments') 가용성 (5사)")
    print("=" * 60)

    start = time.time()
    segResults = checkSegmentsAvailability()
    elapsed2 = time.time() - start

    print(f"\n[세그먼트 가용성 요약]")
    hasCount = sum(1 for v in segResults.values() if v.get("hasSegments"))
    print(f"  가용: {hasCount}/{len(segResults)}사")
    print(f"  소요: {elapsed2:.1f}s")
