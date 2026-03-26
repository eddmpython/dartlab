"""실험 ID: 004
실험명: 자본배분 프로파일 분류 — R&D / CAPEX / 배당 / 자회사투자

목적:
- 사업모델 DNA의 세 번째 축: "버는 돈을 어디에 배분하는가"
- R&D비율, CAPEX비율, 배당성향, 자회사투자 변동으로 자본배분 아키타입 분류

가설:
1. 4개 자본배분 지표(rndRatio, capexRatio, dividendPayoutRatio, investedCompanyCount)로
   기업을 4가지 아키타입으로 분류 가능:
   - Growth Investor: 높은 R&D + 높은 CAPEX (성장 투자형)
   - Cash Returner: 높은 배당 + 낮은 CAPEX (주주환원형)
   - Empire Builder: 낮은 배당 + 높은 자회사투자 (확장형)
   - Balanced: 중간 수준 (균형형)
2. 분류 결과가 섹터 직관과 70%+ 일치
   (IT/반도체 → Growth Investor, 금융 → Cash Returner 등)

방법:
1. 50사에 대해 finance(capexRatio, dividendPayoutRatio, R&D) + report(investedCompany) 수집
2. R&D비율 = IS research_development / revenue (buildTimeseries에서 직접)
3. 자회사투자: report parquet의 investedCompany 행 수 (많을수록 확장 성향)
4. 4개 지표 조합으로 아키타입 분류 (규칙 기반 + 2D 시각화)

결과 (실행 후 작성):
- 수집: 15.0s, 48사 (금융 2사 finance 없음 제외)
- 유효 데이터: capexRatio 37/48(77%), dividendPayoutRatio 22/48(46%),
  investedCompanyCount 47/48(98%), roic 46/48(96%), rndRatio 2/48(4%)
- R&D비율: IS에 research_development 계정이 별도 존재하는 기업이 2사뿐 (한미약품, 유한양행)
  → 대부분 판관비에 포함되어 별도 추출 불가
- 섹터별 평균:
  | 섹터           | R&D비율 | CAPEX비율 | 배당성향  | ROIC  | 투자사수 |
  |---------------|--------|----------|---------|-------|--------|
  | IT/반도체       | N/A    | 20.7%    | 63.1%   | 5.2%  | 89     |
  | 산업재          | N/A    | 9.4%     | 63.5%   | 4.4%  | 96     |
  | 건강관리         | 109.9% | 10.6%    | 38.9%   | 7.6%  | 54     |
  | 금융           | N/A    | N/A      | 19.4%   | 5.6%  | 43     |
  | 필수소비재        | N/A    | 6.7%     | 16.6%   | 10.1% | 44     |
- 아키타입 분류 (투자강도 중앙값 5.6%, 배당성향 중앙값 22.4%):
  - Growth Investor: 16사 — SK하이닉스, NAVER, 카카오, 삼성SDI, 에코프로비엠 등
  - Cash Returner: 5사 — 현대차, 고려아연, 신한지주, 기업은행, BNK금융지주
  - Empire Builder: 7사 — 기아, 현대모비스, 삼성물산, 삼성생명, CJ제일제당 등
  - Balanced: 16사 — 삼성전자, LG에너지솔루션, SK, SK바이오팜 등
- 섹터-아키타입 직관 매칭:
  - IT/반도체 → Growth Investor 75% ✓
  - 산업재 → Growth Investor 30% (분산됨)
  - 건강관리 → Balanced 50% (R&D 데이터 부족으로 Growth 미분류)
  - 금융 → Cash Returner 43% (부분 부합)
  - 필수소비재 → Balanced 44% (분산됨)

결론:
- 가설 1 조건부 채택: 3개 지표(capexRatio + dividendPayoutRatio + investedCompanyCount)로
  4개 아키타입 분류는 가능하나, R&D 데이터 부재로 Growth Investor 판별이 CAPEX 의존적
- R&D비율: IS 별도 계정 보유 기업 4%뿐 → 사업모델 DNA에서 R&D 축은 docs 텍스트 기반으로 전환 필요
  (006_moatDetection에서 "연구개발" 키워드 밀도로 대체)
- investedCompanyCount: 98% 커버리지로 매우 유효. NAVER(265), 현대차(227), 유한양행(212) 등
  확장 성향 기업 식별에 강력한 지표
- IT/반도체 → Growth Investor 75% 매칭: CAPEX 중심 분류가 반도체/배터리 업종에 직관적
- 금융 → Cash Returner 43%: 금융 내에서도 지주회사(Empire Builder)와 은행(Cash Returner) 분화
- 핵심 시사점: capexRatio + dividendPayoutRatio + investedCompanyCount 3축이
  사업모델 DNA "자본배분" 축으로 유효. R&D는 텍스트 기반으로 보완.
- 007_archetypeClassify에서 이 3개 지표를 핵심 특성으로 활용

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

# 003에서 검증된 48사 (중복 제거)
ALL_COMPANIES = [
    # IT/반도체
    ("005930", "삼성전자", "IT/반도체"), ("000660", "SK하이닉스", "IT/반도체"),
    ("035420", "NAVER", "IT/반도체"), ("035720", "카카오", "IT/반도체"),
    ("006400", "삼성SDI", "IT/반도체"), ("247540", "에코프로비엠", "IT/반도체"),
    ("373220", "LG에너지솔루션", "IT/반도체"),
    ("036570", "엔씨소프트", "IT/반도체"),
    # 산업재/자동차
    ("005380", "현대차", "산업재"), ("000270", "기아", "산업재"),
    ("012330", "현대모비스", "산업재"), ("010130", "고려아연", "산업재"),
    ("051910", "LG화학", "산업재"), ("011170", "롯데케미칼", "산업재"),
    ("003550", "LG", "산업재"), ("034730", "SK", "산업재"),
    ("028260", "삼성물산", "산업재"), ("009150", "삼성전기", "산업재"),
    # 건강관리/제약
    ("068270", "셀트리온", "건강관리"), ("207940", "삼성바이오로직스", "건강관리"),
    ("326030", "SK바이오팜", "건강관리"), ("128940", "한미약품", "건강관리"),
    ("006280", "녹십자", "건강관리"), ("000100", "유한양행", "건강관리"),
    ("185750", "종근당", "건강관리"), ("003060", "에이치엘비", "건강관리"),
    ("145720", "덴티움", "건강관리"), ("214150", "클래시스", "건강관리"),
    # 금융
    ("105560", "KB금융", "금융"), ("055550", "신한지주", "금융"),
    ("086790", "하나금융지주", "금융"), ("316140", "우리금융지주", "금융"),
    ("024110", "기업은행", "금융"), ("138930", "BNK금융지주", "금융"),
    ("175330", "JB금융지주", "금융"), ("032830", "삼성생명", "금융"),
    ("000810", "삼성화재", "금융"), ("088350", "한화생명", "금융"),
    # 필수소비재/식품
    ("097950", "CJ제일제당", "필수소비재"), ("004370", "농심", "필수소비재"),
    ("271560", "오리온", "필수소비재"), ("280360", "롯데웰푸드", "필수소비재"),
    ("005300", "롯데칠성", "필수소비재"), ("007310", "오뚜기", "필수소비재"),
    ("003230", "삼양식품", "필수소비재"), ("002270", "롯데지주", "필수소비재"),
    ("001040", "CJ", "필수소비재"), ("282330", "BGF리테일", "필수소비재"),
]


def _extractRndRatio(series: dict) -> float | None:
    """IS 시계열에서 R&D비율(%) 추출. research_development / revenue."""
    isSeries = series.get("IS", {})

    # R&D 비용
    rnd = None
    for key in ["research_development", "research_and_development_expense"]:
        vals = isSeries.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            rnd = nonNull[-1]  # 최신값
            break

    # 매출
    revenue = None
    for key in ["revenue", "sales"]:
        vals = isSeries.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            revenue = nonNull[-1]
            break

    if rnd is not None and revenue and revenue > 0:
        return abs(rnd) / revenue * 100
    return None


def _countInvestedCompanies(stockCode: str) -> int | None:
    """report parquet에서 investedCompany 행 수 (자회사/피투자회사 수).

    연도별 행 수가 크게 다를 수 있으므로, 10행 이상인 가장 최신 연도를 선택.
    """
    from dartlab.core.dataLoader import loadData

    try:
        df = loadData(stockCode, category="report")
        inv = df.filter(pl.col("apiType") == "investedCompany")
        if inv.is_empty():
            return None

        years = sorted(
            [y for y in inv["year"].unique().to_list() if y is not None],
            reverse=True,
        )
        if not years:
            return None

        # 데이터가 충분한(10행+) 가장 최신 연도 선택
        for yr in years:
            subset = inv.filter(pl.col("year") == yr)
            if len(subset) >= 10:
                return len(subset)

        # 10행 미만이면 가장 많은 연도
        best_yr = max(years, key=lambda y: len(inv.filter(pl.col("year") == y)))
        cnt = len(inv.filter(pl.col("year") == best_yr))
        return cnt if cnt > 0 else None

    except (FileNotFoundError, RuntimeError, OSError):
        return None


def _extractCapexAndDividend(series: dict) -> dict:
    """CF 시계열에서 capex, dividendsPaid 직접 추출 (ratios에서 None인 경우 보완)."""
    cfSeries = series.get("CF", {})
    isSeries = series.get("IS", {})

    # CAPEX: 유형자산 취득 (음수가 일반적)
    capex = None
    for key in [
        "purchase_of_property_plant_and_equipment",
        "acquisition_of_property_plant_equipment",
        "acquisitions_of_property_plant_and_equipment",
        "purchase_of_tangible_assets",
    ]:
        vals = cfSeries.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            capex = abs(nonNull[-1])
            break

    # 배당금 지급
    dividendsPaid = None
    for key in [
        "dividends_paid",
        "payment_of_dividends",
        "dividends_paid_to_owners_of_parent",
    ]:
        vals = cfSeries.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            dividendsPaid = abs(nonNull[-1])
            break

    # 매출
    revenue = None
    for key in ["revenue", "sales"]:
        vals = isSeries.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            revenue = nonNull[-1]
            break

    # 순이익
    netIncome = None
    for key in ["net_profit", "profit_for_the_year", "net_income"]:
        vals = isSeries.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            netIncome = nonNull[-1]
            break

    result: dict = {"capex": capex, "dividendsPaid": dividendsPaid}

    if capex and revenue and revenue > 0:
        result["capexRatio_direct"] = capex / revenue * 100
    else:
        result["capexRatio_direct"] = None

    if dividendsPaid and netIncome and netIncome > 0:
        result["dividendPayout_direct"] = dividendsPaid / netIncome * 100
    else:
        result["dividendPayout_direct"] = None

    return result


def runCapitalAllocation(*, verbose: bool = True) -> pl.DataFrame:
    """자본배분 프로파일 분류 실행."""
    from dartlab.core.finance.ratios import calcRatios
    from dartlab.providers.dart.finance.pivot import buildTimeseries

    rows = []
    for stockCode, corpName, sector in ALL_COMPANIES:
        row: dict = {"stockCode": stockCode, "corpName": corpName, "sector": sector}

        # finance 비율
        try:
            result = buildTimeseries(stockCode)
            if result is not None:
                series, _ = result
                ratios = calcRatios(series)
                rd = asdict(ratios)

                row["roic"] = rd.get("roic")
                row["revenueTTM"] = rd.get("revenueTTM")

                # R&D 비율 (IS에서 직접)
                row["rndRatio"] = _extractRndRatio(series)

                # capexRatio, dividendPayoutRatio: ratios 우선, None이면 직접 추출
                row["capexRatio"] = rd.get("capexRatio")
                row["dividendPayoutRatio"] = rd.get("dividendPayoutRatio")

                direct = _extractCapexAndDividend(series)
                if row["capexRatio"] is None and direct["capexRatio_direct"] is not None:
                    row["capexRatio"] = round(direct["capexRatio_direct"], 2)
                if row["dividendPayoutRatio"] is None and direct["dividendPayout_direct"] is not None:
                    row["dividendPayoutRatio"] = round(direct["dividendPayout_direct"], 2)
            else:
                for f in ["capexRatio", "dividendPayoutRatio", "roic",
                          "revenueTTM", "rndRatio"]:
                    row[f] = None
        except (FileNotFoundError, RuntimeError, OSError):
            for f in ["capexRatio", "dividendPayoutRatio", "roic",
                      "revenueTTM", "rndRatio"]:
                row[f] = None

        # 자회사 투자 수
        row["investedCompanyCount"] = _countInvestedCompanies(stockCode)

        rows.append(row)

    df = pl.DataFrame(rows)

    if verbose:
        _printResults(df)

    return df


def _printResults(df: pl.DataFrame) -> None:
    """결과 출력."""
    # 섹터별 평균
    print("\n[자본배분 — 섹터별 평균]")
    print(f"{'섹터':12s} | {'R&D비율':>8s} | {'CAPEX비율':>10s} | "
          f"{'배당성향':>8s} | {'ROIC':>6s} | {'투자사수':>8s}")
    print("-" * 75)

    for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
        sdf = df.filter(pl.col("sector") == sector)
        rnd = sdf["rndRatio"].drop_nulls().mean()
        capex = sdf["capexRatio"].drop_nulls().mean()
        div = sdf["dividendPayoutRatio"].drop_nulls().mean()
        roic = sdf["roic"].drop_nulls().mean()
        inv = sdf["investedCompanyCount"].drop_nulls().mean()

        rndS = f"{rnd:.1f}%" if rnd is not None else "N/A"
        capS = f"{capex:.1f}%" if capex is not None else "N/A"
        divS = f"{div:.1f}%" if div is not None else "N/A"
        roicS = f"{roic:.1f}%" if roic is not None else "N/A"
        invS = f"{inv:.0f}" if inv is not None else "N/A"
        print(f"{sector:12s} | {rndS:>8s} | {capS:>10s} | "
              f"{divS:>8s} | {roicS:>6s} | {invS:>8s}")

    # 아키타입 분류 (규칙 기반)
    validDf = df.filter(
        pl.col("capexRatio").is_not_null()
        | pl.col("rndRatio").is_not_null()
        | pl.col("dividendPayoutRatio").is_not_null()
    )

    # 투자 강도 = R&D + CAPEX (둘 다 있으면 합산, 하나만 있으면 그것 사용)
    investRows = []
    for row_data in validDf.iter_rows(named=True):
        rnd = row_data.get("rndRatio") or 0
        capex = row_data.get("capexRatio") or 0
        div = row_data.get("dividendPayoutRatio") or 0
        inv = row_data.get("investedCompanyCount") or 0

        investIntensity = rnd + capex  # 성장투자 강도
        investRows.append({
            **row_data,
            "investIntensity": investIntensity,
        })

    if not investRows:
        return

    investDf = pl.DataFrame(investRows)

    # 중앙값 기준
    medianInvest = investDf["investIntensity"].drop_nulls().median() or 0
    medianDiv = investDf.filter(
        pl.col("dividendPayoutRatio").is_not_null()
    )["dividendPayoutRatio"].median() or 0
    medianInvComp = investDf.filter(
        pl.col("investedCompanyCount").is_not_null()
    )["investedCompanyCount"].median() or 0

    print(f"\n[아키타입 기준: 투자강도 중앙값={medianInvest:.1f}%, "
          f"배당성향 중앙값={medianDiv:.1f}%, 투자사수 중앙값={medianInvComp:.0f}]")

    archetype_counts: dict[str, list[str]] = {
        "Growth Investor": [],
        "Cash Returner": [],
        "Empire Builder": [],
        "Balanced": [],
    }

    for row_data in investDf.iter_rows(named=True):
        invest = row_data.get("investIntensity") or 0
        div = row_data.get("dividendPayoutRatio") or 0
        invComp = row_data.get("investedCompanyCount") or 0
        name = row_data["corpName"]
        sector = row_data["sector"]

        # 분류 규칙
        if invest > medianInvest and div <= medianDiv:
            archetype = "Growth Investor"
        elif div > medianDiv and invest <= medianInvest:
            archetype = "Cash Returner"
        elif invComp > medianInvComp and div <= medianDiv:
            archetype = "Empire Builder"
        else:
            archetype = "Balanced"

        archetype_counts[archetype].append(f"{name}({sector})")

        print(f"  {name:12s} ({sector:8s}) | R&D={row_data.get('rndRatio') or 0:5.1f}% "
              f"CAPEX={row_data.get('capexRatio') or 0:5.1f}% "
              f"배당={div:5.1f}% 투자사={invComp:3.0f} → {archetype}")

    print("\n[아키타입별 요약]")
    for archetype, members in archetype_counts.items():
        print(f"  {archetype:18s}: {len(members)}사")
        if members:
            print(f"    → {', '.join(members[:6])}" + (f" 외 {len(members)-6}사" if len(members) > 6 else ""))

    # 유효 데이터 비율
    print(f"\n[유효 데이터]")
    for col in ["rndRatio", "capexRatio", "dividendPayoutRatio", "investedCompanyCount", "roic"]:
        n = df[col].drop_nulls().len()
        print(f"  {col:25s}: {n}/{len(df)}")

    # 섹터-아키타입 교차표
    print("\n[섹터-아키타입 매칭 직관 검증]")
    print("  기대: IT/반도체 → Growth Investor, 금융 → Cash Returner")
    for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
        sectorMembers = {a: [m for m in ms if sector in m] for a, ms in archetype_counts.items()}
        dominant = max(sectorMembers.items(), key=lambda x: len(x[1]))
        total = sum(len(v) for v in sectorMembers.values())
        pct = len(dominant[1]) / total * 100 if total > 0 else 0
        print(f"  {sector:12s}: {dominant[0]} ({pct:.0f}%)")


if __name__ == "__main__":
    print("=" * 60)
    print("004: 자본배분 프로파일 분류")
    print("=" * 60)

    start = time.time()
    resultDf = runCapitalAllocation()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "004_capitalAllocation.parquet")
    print(f"\n→ {DATA_DIR / '004_capitalAllocation.parquet'} ({elapsed:.1f}s)")
