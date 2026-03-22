"""실험 ID: 003
실험명: 키워드 선행 지표 — 트렌드 키워드 조기 언급 기업의 후속 성과

목적:
- "AI", "ESG", "메타버스" 등 트렌드 키워드를 조기 언급한 기업이 후속 매출 성장에서 우위인지 검증
- 키워드 조기 채택이 실제 사업 성과로 이어지는지 실증

가설:
1. 트렌드 키워드(AI, ESG 등) 조기 언급 기업 → 비언급 기업 대비 매출성장률 5%p+ 우위
2. 키워드별 예측력 차이가 존재 (모든 키워드가 동일하지 않음)

방법:
1. 48사 docs parquet에서 핵심 키워드별 최초 등장 연도 측정
2. 각 키워드에 대해 "조기 언급"(해당 연도 중앙값 이전) vs "후발/미언급" 그룹 분리
3. 그룹별 T+1, T+2년 매출성장률 비교
4. 성공 기준: 조기 언급 그룹 매출성장률 5%p+ 우위

결과:
- 대상: 48사, 7개 트렌드 키워드 카테고리
- 키워드별 조기 언급 vs 후발/미언급 매출성장률 비교:
  | 키워드        | 언급률 | 조기N | 후발N | 조기성장 | 후발성장 | 격차     |
  |-------------|-------|------|------|--------|--------|---------|
  | AI/인공지능    | 65%   | 14   | 20   | +20.4% | +51.4% | -31.0pp |
  | ESG         | 65%   | 13   | 21   | +21.8% | +41.4% | -19.6pp |
  | 메타버스/XR   | 46%   | 7    | 27   | +42.7% | +35.7% | +7.0pp ✓|
  | 전기차/배터리   | 60%   | 11   | 23   | +37.0% | +37.5% | -0.5pp  |
  | 디지털전환     | 56%   | 8    | 26   | +21.7% | +38.3% | -16.5pp |
  | 바이오        | 21%   | 6    | 29   | +46.0% | +35.6% | +10.4pp✓|
  | 반도체/HBM   | 19%   | 4    | 31   | +28.4% | +33.0% | -4.6pp  |
- 키워드 밀도 상위 기업: 현대차(AI 8172회), KB금융(ESG 4440회), 삼성바이오(바이오 8643회)
- 수행 시간: 160초

결론:
- 가설 1 부분 채택: 2개 키워드(메타버스+7.0pp, 바이오+10.4pp)에서 조기 언급 5%p+ 우위
  - 그러나 7개 중 5개에서 조기 언급이 오히려 열위 → "키워드 조기 언급 = 성과 우위" 일반화 불가
- 가설 2 채택: 키워드별 예측력 차이 극명
  - AI/인공지능: -31pp — 조기 언급 기업이 오히려 성장률 낮음
    → 대기업(현대차, 삼성전자) 중심으로 먼저 언급하지만, 이미 성숙 기업이라 성장률이 낮음
  - ESG: -19.6pp — 금융사(KB금융, 신한) 중심 언급. 금융은 매출 성장률 자체가 낮음
  - 바이오: +10.4pp — 전문 바이오 기업이 먼저 언급하고 실제로 성과도 좋음 (도메인 특화 키워드)
- 핵심 통찰: 범용 트렌드 키워드(AI, ESG, DX)는 대기업이 먼저 채택하므로 역의 인과
  - 도메인 특화 키워드(바이오, 메타버스)만 선행 신호 가치
  - 키워드 "양"이 아닌 "맥락"이 중요 — 단순 빈도 카운트의 한계
- 시그널 엔진 시사점:
  1. 범용 키워드는 선행 지표로 부적합 — 기업 규모 바이어스
  2. 도메인 특화 키워드 + 기업 규모 정규화가 필요
  3. 키워드 "신규 등장"보다 "밀도 변화"가 더 의미 있을 수 있음

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

# 트렌드 키워드 (한글 + 영문)
TREND_KEYWORDS = {
    "AI/인공지능": ["인공지능", "AI", "머신러닝", "딥러닝", "생성형"],
    "ESG": ["ESG", "탄소중립", "지속가능", "온실가스", "RE100"],
    "메타버스/XR": ["메타버스", "가상현실", "증강현실", "XR", "VR"],
    "전기차/배터리": ["전기차", "이차전지", "배터리", "EV", "전고체"],
    "디지털전환": ["디지털 전환", "DX", "클라우드", "디지털화"],
    "바이오": ["바이오시밀러", "바이오의약", "세포치료", "유전자치료", "mRNA"],
    "반도체/HBM": ["HBM", "고대역폭", "파운드리", "시스템반도체", "NPU"],
}


def _extractKeywordPresence(stockCode: str) -> dict[str, dict[int, int]]:
    """docs parquet에서 키워드별 연도별 언급 횟수."""
    from dartlab.core.dataLoader import loadData

    try:
        df = loadData(stockCode, category="docs",
                      columns=["section_content", "year"])

        filtered = df.filter(pl.col("section_content").is_not_null() & pl.col("year").is_not_null())
        if filtered.is_empty():
            return {}

        result: dict[str, dict[int, int]] = {}

        for category, keywords in TREND_KEYWORDS.items():
            yearCounts: dict[int, int] = {}

            for yr in filtered["year"].unique().to_list():
                if yr is None:
                    continue
                yrInt = int(yr) if isinstance(yr, (int, float, str)) else None
                if yrInt is None or yrInt < 2019:
                    continue

                ydf = filtered.filter(pl.col("year") == yr)
                allText = " ".join(str(c) for c in ydf["section_content"].to_list() if c is not None)

                count = 0
                for kw in keywords:
                    count += allText.count(kw)

                if count > 0:
                    yearCounts[yrInt] = count

            if yearCounts:
                result[category] = yearCounts

        return result

    except (FileNotFoundError, RuntimeError, OSError):
        return {}


def _extractRevenueGrowth(stockCode: str) -> dict[int, float]:
    """연도별 매출 성장률."""
    from dartlab.engines.dart.finance.pivot import buildTimeseries

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


def runKeywordLeadingIndicator(*, verbose: bool = True) -> pl.DataFrame:
    """키워드 선행 지표 실험."""
    # 수집
    companyData: list[dict] = []

    for stockCode, corpName, sector in ALL_COMPANIES:
        kwPresence = _extractKeywordPresence(stockCode)
        revGrowth = _extractRevenueGrowth(stockCode)

        entry = {
            "stockCode": stockCode, "corpName": corpName, "sector": sector,
            "revGrowth": revGrowth,
        }

        # 각 키워드 카테고리별 최초 등장 연도 + 누적 횟수
        for category in TREND_KEYWORDS:
            yearCounts = kwPresence.get(category, {})
            if yearCounts:
                entry[f"{category}_firstYear"] = min(yearCounts.keys())
                entry[f"{category}_totalCount"] = sum(yearCounts.values())
            else:
                entry[f"{category}_firstYear"] = None
                entry[f"{category}_totalCount"] = 0

        companyData.append(entry)

    # 분석: 키워드별 조기/후발 그룹 비교
    rows = []
    for category in TREND_KEYWORDS:
        firstYears = [d[f"{category}_firstYear"] for d in companyData if d[f"{category}_firstYear"] is not None]
        if len(firstYears) < 5:
            rows.append({
                "keyword": category, "earlyN": 0, "lateN": 0,
                "earlyAvgGrowth": None, "lateAvgGrowth": None,
                "gapPp": None, "mentionRate": len(firstYears) / len(companyData) * 100,
            })
            continue

        medianYear = sorted(firstYears)[len(firstYears) // 2]

        # 조기 언급 (중앙값 이전) vs 후발/미언급
        earlyGrowths = []
        lateGrowths = []

        for d in companyData:
            fy = d[f"{category}_firstYear"]
            revG = d["revGrowth"]

            # T+1, T+2년 평균 성장률
            futureGrowths = []
            if fy is not None:
                for offset in [1, 2]:
                    g = revG.get(fy + offset)
                    if g is not None:
                        futureGrowths.append(g)
            else:
                # 미언급 기업은 전체 평균 기간의 성장률
                for yr in range(2020, 2025):
                    g = revG.get(yr)
                    if g is not None:
                        futureGrowths.append(g)

            if not futureGrowths:
                continue

            avgG = sum(futureGrowths) / len(futureGrowths)

            if fy is not None and fy <= medianYear:
                earlyGrowths.append(avgG)
            else:
                lateGrowths.append(avgG)

        earlyAvg = sum(earlyGrowths) / len(earlyGrowths) if earlyGrowths else None
        lateAvg = sum(lateGrowths) / len(lateGrowths) if lateGrowths else None
        gap = (earlyAvg - lateAvg) if earlyAvg is not None and lateAvg is not None else None

        rows.append({
            "keyword": category,
            "earlyN": len(earlyGrowths),
            "lateN": len(lateGrowths),
            "earlyAvgGrowth": round(earlyAvg, 1) if earlyAvg is not None else None,
            "lateAvgGrowth": round(lateAvg, 1) if lateAvg is not None else None,
            "gapPp": round(gap, 1) if gap is not None else None,
            "mentionRate": len(firstYears) / len(companyData) * 100,
        })

    df = pl.DataFrame(rows)

    if verbose:
        _printResults(df, companyData)

    return df


def _printResults(df: pl.DataFrame, companyData: list[dict]) -> None:
    """결과 출력."""
    print(f"\n[키워드 선행 지표 분석] {len(companyData)}사 대상")

    print(f"\n{'키워드':16s} | {'언급률':>6s} | {'조기N':>5s} | {'후발N':>5s} | {'조기성장':>8s} | {'후발성장':>8s} | {'격차':>8s}")
    print("-" * 75)

    passCount = 0
    for i in range(len(df)):
        row = df.row(i, named=True)
        earlyStr = f"{row['earlyAvgGrowth']:+.1f}%" if row['earlyAvgGrowth'] is not None else "N/A"
        lateStr = f"{row['lateAvgGrowth']:+.1f}%" if row['lateAvgGrowth'] is not None else "N/A"
        gapStr = f"{row['gapPp']:+.1f}pp" if row['gapPp'] is not None else "N/A"
        marker = " ✓" if row['gapPp'] is not None and row['gapPp'] > 5 else ""
        if row['gapPp'] is not None and row['gapPp'] > 5:
            passCount += 1
        print(f"{row['keyword']:16s} | {row['mentionRate']:5.0f}% | {row['earlyN']:5d} | {row['lateN']:5d} | {earlyStr:>8s} | {lateStr:>8s} | {gapStr:>8s}{marker}")

    # 키워드 밀도 상위 기업
    print(f"\n[키워드별 가장 많이 언급한 기업 (상위 3)]")
    for category in TREND_KEYWORDS:
        top3 = sorted(
            [(d["corpName"], d[f"{category}_totalCount"]) for d in companyData if d[f"{category}_totalCount"] > 0],
            key=lambda x: x[1], reverse=True
        )[:3]
        if top3:
            topStr = ", ".join(f"{name}({cnt}회)" for name, cnt in top3)
            print(f"  {category:16s}: {topStr}")

    # GATE
    print(f"\n{'='*60}")
    print(f"가설 1 판정: {passCount}개 키워드에서 조기 언급 5%p+ 우위")
    print(f"  → {'✓ PASS (1개+)' if passCount >= 1 else '✗ FAIL (0개)'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("=" * 60)
    print("086-003: 키워드 선행 지표 (Phase 3)")
    print("=" * 60)

    start = time.time()
    resultDf = runKeywordLeadingIndicator()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "003_keywordLeadingIndicator.parquet")
    print(f"\n→ {DATA_DIR / '003_keywordLeadingIndicator.parquet'} ({elapsed:.1f}s)")
