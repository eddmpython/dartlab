"""실험 ID: 001
실험명: 공시 텍스트 변화 → 실적 상관 — Phase 3 관문 실험

목적:
- 공시 문서의 텍스트 변화율이 다음해 실적 변동을 예측하는지 검증
- dartlab만의 핵심 해자: "공시 텍스트 구조 변화를 시계열 시그널로 사용"

가설:
1. 공시 텍스트 변화율(YoY 텍스트 길이 변화) > 50% → 다음해 실적 변동 상관 > 0.15 (Spearman)
2. "사업의 내용" 섹션 변화율이 가장 높은 예측력

방법:
1. 48사 docs parquet에서 "사업의 내용" 관련 섹션의 연도별 텍스트 길이 측정
2. 텍스트 변화율 = abs(len(year) - len(year-1)) / len(year-1) × 100
3. finance에서 연도별 매출성장률, 영업이익성장률 추출
4. 텍스트 변화율(T년) vs 실적 변동(T+1년) Spearman 상관 측정
5. 성공 기준: Spearman > 0.15 (p < 0.05)

결과:
- 대상: 146 관측치 (48사 × 연도), 유효 쌍(bizChangeRate + nextYrRevGrowth) N=82
- 사업의내용 변화율 vs T+1 매출성장률: Spearman ρ=0.068 ✗ FAIL (기준 >0.15)
- 리스크 섹션 변화율 vs T+1 매출성장률: N=51, ρ=-0.105
- 변화율 크기별 T+1 매출성장률:
  | 변화율 구간 | N   | 평균성장률 | 표준편차 |
  |-----------|-----|---------|--------|
  | 소(~10%)   | 44  | +16.9%  | 31.4%  |
  | 중(10~50%) | 28  | +20.4%  | 56.3%  |
  | 대(50%+)   | 10  | +14.8%  | 19.0%  |
- 섹터별 상관:
  | 섹터       | N  | ρ      |
  |-----------|----| -------|
  | IT/반도체   | 33 | -0.092 |
  | 산업재      | 15 | +0.411 |
  | 건강관리     | 24 | +0.109 |
  | 금융       | <5 | 데이터 부족 |
  | 필수소비재    | 10 | -0.212 |
- 수행 시간: 229초

결론:
- 가설 1 기각: 사업의내용 텍스트 변화율 vs T+1 매출성장률 ρ=0.068 — 기준 0.15에 크게 미달
- 가설 2 기각: 사업의내용(ρ=0.068)이 리스크(ρ=-0.105)보다 절대값이 작음. 어느 섹션도 유의미하지 않음
- 변화율 크기별로도 T+1 성과 차이 없음: 소(+16.9%), 중(+20.4%), 대(+14.8%) — 단조 관계 없음
- 섹터별 유일한 양성: 산업재 ρ=0.411 (N=15로 소표본이나 의미 있는 수준)
  - IT/반도체 ρ=-0.092, 필수소비재 ρ=-0.212: 텍스트 변화가 실적과 무관하거나 역방향
- Phase 3 GATE: ✗ FAIL (|ρ|=0.068 ≤ 0.15)
  - 텍스트 길이 변화율이라는 조잡한 프록시로는 선행 신호 추출 불가
  - 근본 한계: 텍스트 "양"의 변화 ≠ 텍스트 "의미"의 변화
  - 산업재에서만 양성인 이유: 경기 민감 업종은 사업보고서 기술 변화가 실적 변동과 동행하는 경향
- 향후 방향: Phase 3은 키워드 기반 접근(003_keywordLeadingIndicator, 006_riskEscalation)으로 축소
  - 002_topicPredictivePower: 토픽별 세분화로 재시도 가치 있음
  - 의미 기반(semantic shift)은 embedding 필요 → 현 실험 범위 밖

실험일: 2026-03-22
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

ALL_COMPANIES = [
    ("005930", "삼성전자", "IT/반도체"), ("000660", "SK하이닉스", "IT/반도체"),
    ("035420", "NAVER", "IT/반도체"), ("035720", "카카오", "IT/반도체"),
    ("006400", "삼성SDI", "IT/반도체"), ("247540", "에코프로비엠", "IT/반도체"),
    ("373220", "LG에너지솔루션", "IT/반도체"), ("036570", "엔씨소프트", "IT/반도체"),
    ("005380", "현대차", "산업재"), ("000270", "기아", "산업재"),
    ("012330", "현대모비스", "산업재"), ("010130", "고려아연", "산업재"),
    ("051910", "LG화학", "산업재"), ("011170", "롯데케미칼", "산업재"),
    ("003550", "LG", "산업재"), ("034730", "SK", "산업재"),
    ("028260", "삼성물산", "산업재"), ("009150", "삼성전기", "산업재"),
    ("068270", "셀트리온", "건강관리"), ("207940", "삼성바이오로직스", "건강관리"),
    ("326030", "SK바이오팜", "건강관리"), ("128940", "한미약품", "건강관리"),
    ("006280", "녹십자", "건강관리"), ("000100", "유한양행", "건강관리"),
    ("185750", "종근당", "건강관리"), ("003060", "에이치엘비", "건강관리"),
    ("145720", "덴티움", "건강관리"), ("214150", "클래시스", "건강관리"),
    ("105560", "KB금융", "금융"), ("055550", "신한지주", "금융"),
    ("086790", "하나금융지주", "금융"), ("316140", "우리금융지주", "금융"),
    ("024110", "기업은행", "금융"), ("138930", "BNK금융지주", "금융"),
    ("175330", "JB금융지주", "금융"), ("032830", "삼성생명", "금융"),
    ("000810", "삼성화재", "금융"), ("088350", "한화생명", "금융"),
    ("097950", "CJ제일제당", "필수소비재"), ("004370", "농심", "필수소비재"),
    ("271560", "오리온", "필수소비재"), ("280360", "롯데웰푸드", "필수소비재"),
    ("005300", "롯데칠성", "필수소비재"), ("007310", "오뚜기", "필수소비재"),
    ("003230", "삼양식품", "필수소비재"), ("002270", "롯데지주", "필수소비재"),
    ("001040", "CJ", "필수소비재"), ("282330", "BGF리테일", "필수소비재"),
]

# 관심 섹션 키워드
BIZ_SECTIONS = ["사업의 내용", "사업개요", "사업의 개요", "주요 사업", "주요사업"]
RISK_SECTIONS = ["위험", "리스크", "경영위험"]


def _extractTextLengthByYear(stockCode: str, sectionKeywords: list[str]) -> dict[int, int]:
    """docs parquet에서 관련 섹션의 연도별 텍스트 길이."""
    from dartlab.core.dataLoader import loadData

    try:
        df = loadData(stockCode, category="docs",
                      columns=["section_title", "section_content", "year"])

        # 키워드 필터
        cond = pl.lit(False)
        for kw in sectionKeywords:
            cond = cond | pl.col("section_title").str.contains(kw)
        filtered = df.filter(pl.col("section_title").is_not_null() & cond)

        if filtered.is_empty():
            return {}

        yearLen: dict[int, int] = {}
        for yr in filtered["year"].unique().to_list():
            if yr is None:
                continue
            yrInt = int(yr) if isinstance(yr, (int, float, str)) else None
            if yrInt is None or yrInt < 2019:
                continue
            ydf = filtered.filter(pl.col("year") == yr)
            totalLen = sum(len(str(c)) for c in ydf["section_content"].to_list() if c is not None)
            if totalLen > 0:
                yearLen[yrInt] = totalLen

        return yearLen

    except (FileNotFoundError, RuntimeError, OSError):
        return {}


def _extractRevenueGrowth(stockCode: str) -> dict[int, float]:
    """연도별 매출 성장률."""
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

    try:
        result = buildTimeseries(stockCode)
        if result is None:
            return {}
        series, periods = result
        isSeries = series.get("IS", {})

        revVals = []
        for key in ["revenue", "sales"]:
            if key in isSeries and any(v is not None for v in isSeries[key]):
                revVals = isSeries[key]
                break
        if not revVals:
            return {}

        yearRev: dict[int, float] = {}
        for i, period in enumerate(periods):
            if i >= len(revVals) or revVals[i] is None:
                continue
            yr = None
            if isinstance(period, (int, float)):
                yr = int(period)
            elif isinstance(period, str):
                try:
                    yr = int(period[:4])
                except (ValueError, IndexError):
                    continue
            elif isinstance(period, (tuple, list)):
                try:
                    yr = int(period[0])
                except (ValueError, IndexError, TypeError):
                    continue
            if yr and 2019 <= yr <= 2025:
                if yr not in yearRev or revVals[i] > yearRev[yr]:
                    yearRev[yr] = revVals[i]

        # YoY 성장률
        growth: dict[int, float] = {}
        sortedYears = sorted(yearRev.keys())
        for i in range(1, len(sortedYears)):
            y = sortedYears[i]
            py = sortedYears[i - 1]
            if py == y - 1 and yearRev[py] > 0:
                growth[y] = (yearRev[y] / yearRev[py] - 1) * 100
        return growth

    except (FileNotFoundError, RuntimeError, OSError):
        return {}


def _spearmanCorr(x: list[float], y: list[float]) -> float:
    """Spearman 순위상관."""
    n = len(x)
    if n < 3:
        return 0.0

    def _rank(vals: list) -> list[float]:
        indexed = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        for rank, (idx, _) in enumerate(indexed, 1):
            ranks[idx] = float(rank)
        return ranks

    rx = _rank(x)
    ry = _rank(y)
    d_sq = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    return 1 - (6 * d_sq) / (n * (n ** 2 - 1))


def runDiffToPerformance(*, verbose: bool = True) -> pl.DataFrame:
    """공시 변화 → 실적 상관 실행."""
    rows = []

    for stockCode, corpName, sector in ALL_COMPANIES:
        # 텍스트 변화율
        bizLen = _extractTextLengthByYear(stockCode, BIZ_SECTIONS)
        riskLen = _extractTextLengthByYear(stockCode, RISK_SECTIONS)

        # 매출 성장률
        revGrowth = _extractRevenueGrowth(stockCode)

        # 텍스트 변화율 계산
        sortedYears = sorted(bizLen.keys())
        for i in range(1, len(sortedYears)):
            yr = sortedYears[i]
            prevYr = sortedYears[i - 1]

            if prevYr != yr - 1 or bizLen[prevYr] == 0:
                continue

            bizChangeRate = abs(bizLen[yr] - bizLen[prevYr]) / bizLen[prevYr] * 100
            riskChangeRate = None
            if yr in riskLen and prevYr in riskLen and riskLen[prevYr] > 0:
                riskChangeRate = abs(riskLen[yr] - riskLen[prevYr]) / riskLen[prevYr] * 100

            # T+1년 실적
            nextYrGrowth = revGrowth.get(yr + 1)

            rows.append({
                "stockCode": stockCode, "corpName": corpName, "sector": sector,
                "textYear": yr, "bizChangeRate": round(bizChangeRate, 1),
                "riskChangeRate": round(riskChangeRate, 1) if riskChangeRate is not None else None,
                "nextYrRevGrowth": round(nextYrGrowth, 1) if nextYrGrowth is not None else None,
                "bizTextLen": bizLen[yr],
            })

    df = pl.DataFrame(rows)

    if verbose:
        _printResults(df)

    return df


def _printResults(df: pl.DataFrame) -> None:
    """결과 출력."""
    print(f"\n[데이터 현황] {len(df)} 관측치 (기업×연도)")

    # 사업의 내용 변화율 vs T+1 매출성장률
    validDf = df.filter(
        pl.col("bizChangeRate").is_not_null() & pl.col("nextYrRevGrowth").is_not_null()
    )

    if len(validDf) >= 5:
        biz = validDf["bizChangeRate"].to_list()
        rev = validDf["nextYrRevGrowth"].to_list()
        rho = _spearmanCorr(biz, rev)

        print(f"\n[핵심 결과: 사업의내용 변화율 vs T+1 매출성장률]")
        print(f"  N={len(validDf)}, Spearman ρ={rho:.3f}")
        print(f"  판정: {'✓ PASS (>0.15)' if abs(rho) > 0.15 else '✗ FAIL (|ρ| ≤ 0.15)'}")

        # 변화율 크기별 그룹 분석
        print(f"\n[변화율 크기별 T+1 매출성장률]")
        for label, lo, hi in [("소(~10%)", 0, 10), ("중(10~50%)", 10, 50), ("대(50%+)", 50, 10000)]:
            grp = validDf.filter(
                (pl.col("bizChangeRate") >= lo) & (pl.col("bizChangeRate") < hi)
            )
            if len(grp) >= 3:
                avgG = grp["nextYrRevGrowth"].mean()
                stdG = grp["nextYrRevGrowth"].std()
                print(f"  {label:12s}: N={len(grp):3d}, 평균={avgG:+6.1f}%, 표준편차={stdG:6.1f}%")

    # 리스크 섹션 변화율
    riskDf = df.filter(
        pl.col("riskChangeRate").is_not_null() & pl.col("nextYrRevGrowth").is_not_null()
    )
    if len(riskDf) >= 5:
        risk = riskDf["riskChangeRate"].to_list()
        rev2 = riskDf["nextYrRevGrowth"].to_list()
        rho2 = _spearmanCorr(risk, rev2)
        print(f"\n[리스크 섹션 변화율 vs T+1 매출성장률]")
        print(f"  N={len(riskDf)}, Spearman ρ={rho2:.3f}")

    # 섹터별
    print(f"\n[섹터별 상관]")
    for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
        sdf = validDf.filter(pl.col("sector") == sector) if len(validDf) > 0 else pl.DataFrame()
        if len(sdf) >= 5:
            b = sdf["bizChangeRate"].to_list()
            r = sdf["nextYrRevGrowth"].to_list()
            rho_s = _spearmanCorr(b, r)
            print(f"  {sector:12s}: N={len(sdf):3d}, ρ={rho_s:.3f}")
        else:
            print(f"  {sector:12s}: N<5 (데이터 부족)")

    # GATE 판정
    if len(validDf) >= 5:
        biz = validDf["bizChangeRate"].to_list()
        rev = validDf["nextYrRevGrowth"].to_list()
        rho = _spearmanCorr(biz, rev)
        print(f"\n{'='*50}")
        gatePass = abs(rho) > 0.15
        print(f"Phase 3 GATE 판정: {'✓ PASS' if gatePass else '✗ FAIL'}")
        print(f"  |ρ|={abs(rho):.3f} {'>' if gatePass else '<='} 0.15")
        if abs(rho) < 0.10:
            print(f"  → 공시 텍스트 선행 신호 가설 기각")
        print(f"{'='*50}")


if __name__ == "__main__":
    print("=" * 60)
    print("086-001: 공시 텍스트 변화 → 실적 상관 (Phase 3 GATE)")
    print("=" * 60)

    start = time.time()
    resultDf = runDiffToPerformance()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "001_diffToPerformance.parquet")
    print(f"\n→ {DATA_DIR / '001_diffToPerformance.parquet'} ({elapsed:.1f}s)")
