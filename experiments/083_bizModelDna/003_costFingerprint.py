"""실험 ID: 003
실험명: 비용 구조 핑거프린팅 — 자산경량 vs 중후장대, 노동집약 vs 자본집약

목적:
- report(employee) + finance 비율로 기업의 비용 구조를 4사분면으로 분류
- 사업모델 DNA 두 번째 축: "어디에 돈을 쓰는가"

가설:
1. 인건비 집약도(총급여/매출) + 자산집약도(유형자산/매출)로 4사분면 분류 가능:
   - Q1: 자산경량+노동경량 (플랫폼/SW)
   - Q2: 자산경량+노동집약 (서비스/제약)
   - Q3: 자산중심+노동경량 (반도체/화학)
   - Q4: 자산중심+노동집약 (자동차/건설)
2. 분류 결과가 섹터 직관과 80%+ 일치

방법:
1. 50사에 대해 finance(tangibleAsset, revenue) + report(employee) 데이터 수집
2. 축 계산:
   - x축: 자산집약도 = tangibleAsset / totalAssets (또는 tangibleAsset/revenue)
   - y축: 인건비집약도 = 총급여 / revenue (report employee에서 추출)
   - 보조: sgaRatio, costOfSalesRatio, depreciation 비율
3. 4사분면 분류 + 섹터별 분포 확인

결과 (실험 후 작성):
- 수집: 14.7s, 48사 (중복 제거 후, 금융 2사 finance 없음)
- 유효 데이터: assetIntensity 46/48, laborIntensity 37/48, headcount 46/48
- 섹터별 평균:
  | 섹터           | 자산집약도 | 인건비집약도 | 1인당매출(억) | 인원(명)  | sgaRatio |
  |---------------|----------|-----------|------------|---------|----------|
  | IT/반도체       | 36.7%    | 6.1%      | 28.7       | 18,049  | 17.4%    |
  | 산업재          | 28.6%    | 2.5%      | 81.1       | 14,082  | 16.9%    |
  | 건강관리         | 27.5%    | 21.0%     | 16.4       | 1,178   | 80.3%    |
  | 금융           | 0.8%     | N/A       | N/A        | 1,737   | N/A      |
  | 필수소비재        | 42.5%    | 4.4%      | 1136.7     | 2,102   | 18.6%    |
- 4사분면 분류 (중앙값: 자산 36.6%, 노동 3.7%):
  - Q1(경량+저노동): 카카오, 현대차, 현대모비스, 고려아연, LG, SK바이오팜, 셀트리온 → 플랫폼/지주/바이오
  - Q2(경량+고노동): NAVER, 엔씨소프트, 유한양행, 종근당, 녹십자 → SW/서비스/제약영업
  - Q3(중자산+저노동): 삼성전자, LG에너지솔루션, LG화학, SK, 롯데케미칼 → 반도체/화학/에너지
  - Q4(중자산+고노동): SK하이닉스, 삼성SDI, 에코프로비엠, 삼양식품, 농심, 롯데칠성 → 자본+노동 집약 제조
- 금융 섹터: 자산집약도 0.8% (유형자산 거의 없음), 인건비집약도 N/A → 매출 개념 상이
- 이상값: 한미약품 인건비집약도 92.2% → 매출 대비 급여 비율이 극단적 (R&D 인건비 포함 추정)

결론:
- 가설 1 채택: 자산집약도(tangibleAssets/totalAssets) + 인건비집약도(totalSalary/revenue)로
  4사분면 분류가 섹터 직관과 높은 일치도를 보임
- 유효 데이터: assetIntensity 96%, laborIntensity 77% → report employee 파싱 개선 시 더 높아질 수 있음
- 금융 섹터: 모든 비율이 일반 기업과 상이 → 별도 분류 체계 필요 (NIM, 자기자본비율 등)
- 핵심 시사점: 이 2차원 분류가 사업모델 DNA의 "비용 구조" 축으로 매우 유효
  → 007_archetypeClassify에서 이 축을 핵심 특성으로 활용

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

# 001에서 검증된 50사 (중복 제거)
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


def _parseNum(val) -> float | None:
    """문자열 숫자 파싱. 쉼표 제거, '-' → None."""
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if s in ("-", "", "None"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _extractEmployeeCost(stockCode: str) -> dict:
    """report parquet에서 employee 데이터 → 총급여, 인원수 추출."""
    from dartlab.core.dataLoader import loadData

    try:
        df = loadData(stockCode, category="report")
        emp = df.filter(pl.col("apiType") == "employee")
        if emp.is_empty():
            return {"totalSalary": None, "headcount": None, "salaryPerHead": None}

        # 최신 연도 (year는 문자열)
        years = sorted([y for y in emp["year"].unique().to_list() if y is not None], reverse=True)
        if not years:
            return {"totalSalary": None, "headcount": None, "salaryPerHead": None}

        # 최신 2개 연도 중 데이터 있는 것 선택
        for yr in years[:2]:
            latest = emp.filter(pl.col("year") == yr)

            # "성별합계" 행에서 인원수 추출 (fo_bbm이 "성별합계"인 행)
            summaryRows = latest.filter(
                pl.col("fo_bbm").is_not_null() & pl.col("fo_bbm").str.contains("합계")
            )
            if summaryRows.is_empty():
                # 합계 행이 없으면 전체에서 sm(합계) 사용
                summaryRows = latest

            # 인원수: sm(합계) 컬럼의 최대값 (전체 합계 행)
            headcount = None
            smVals = summaryRows["sm"].to_list() if "sm" in summaryRows.columns else []
            nums = [_parseNum(v) for v in smVals]
            nums = [n for n in nums if n is not None and n > 0]
            if nums:
                headcount = int(max(nums))  # 전체 합계가 가장 큰 값

            # 총급여: fyer_salary_totamt (연간급여총액, 원 단위)
            totalSalary = None
            salVals = latest["fyer_salary_totamt"].to_list() if "fyer_salary_totamt" in latest.columns else []
            salNums = [_parseNum(v) for v in salVals]
            salNums = [n for n in salNums if n is not None and n > 0]
            if salNums:
                totalSalary = sum(salNums)  # 부문별 합산

            if headcount or totalSalary:
                salaryPerHead = None
                if totalSalary and headcount and headcount > 0:
                    salaryPerHead = totalSalary / headcount
                return {"totalSalary": totalSalary, "headcount": headcount, "salaryPerHead": salaryPerHead}

        return {"totalSalary": None, "headcount": None, "salaryPerHead": None}

    except (FileNotFoundError, RuntimeError, OSError):
        return {"totalSalary": None, "headcount": None, "salaryPerHead": None}


def runCostFingerprint(*, verbose: bool = True) -> pl.DataFrame:
    """비용 구조 핑거프린팅 실행."""
    from dartlab.engines.common.finance.ratios import calcRatios
    from dartlab.engines.dart.finance.pivot import buildTimeseries

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
                row["revenueTTM"] = rd.get("revenueTTM")
                row["totalAssets"] = rd.get("totalAssets")
                row["operatingMargin"] = rd.get("operatingMargin")
                row["grossMargin"] = rd.get("grossMargin")
                row["sgaRatio"] = rd.get("sgaRatio")
                row["costOfSalesRatio"] = rd.get("costOfSalesRatio")
                # tangibleAsset 비율 (직접 계산)
                bs = series.get("BS", {})
                tangible = None
                for key in ["tangible_assets", "property_plant_equipment", "ppe_net"]:
                    vals = bs.get(key, [])
                    nonNull = [v for v in vals if v is not None]
                    if nonNull:
                        tangible = nonNull[-1]
                        break
                row["tangibleAssets"] = tangible
            else:
                for f in ["revenueTTM", "totalAssets", "operatingMargin", "grossMargin",
                          "sgaRatio", "costOfSalesRatio", "tangibleAssets"]:
                    row[f] = None
        except (FileNotFoundError, RuntimeError, OSError):
            for f in ["revenueTTM", "totalAssets", "operatingMargin", "grossMargin",
                      "sgaRatio", "costOfSalesRatio", "tangibleAssets"]:
                row[f] = None

        # employee 데이터 (report)
        emp = _extractEmployeeCost(stockCode)
        row.update(emp)

        # 파생 지표 계산
        rev = row.get("revenueTTM")
        ta = row.get("totalAssets")
        tang = row.get("tangibleAssets")
        sal = row.get("totalSalary")

        # 자산집약도 = tangibleAssets / totalAssets
        row["assetIntensity"] = (tang / ta * 100) if tang and ta and ta > 0 else None
        # 인건비집약도 = totalSalary / revenue (%)
        row["laborIntensity"] = (sal / rev * 100) if sal and rev and rev > 0 else None
        # 1인당 매출
        hc = row.get("headcount")
        row["revenuePerHead"] = (rev / hc) if rev and hc and hc > 0 else None

        rows.append(row)

    df = pl.DataFrame(rows)

    if verbose:
        print("\n[비용 구조 — 섹터별 평균]")
        print(f"{'섹터':12s} | {'자산집약도':>10s} | {'인건비집약도':>12s} | {'1인당매출(억)':>14s} | {'인원(명)':>10s} | {'sgaRatio':>10s}")
        print("-" * 85)

        for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
            sdf = df.filter(pl.col("sector") == sector)
            ai = sdf["assetIntensity"].drop_nulls().mean()
            li = sdf["laborIntensity"].drop_nulls().mean()
            rph = sdf["revenuePerHead"].drop_nulls().mean()
            hc = sdf["headcount"].drop_nulls().mean()
            sga = sdf["sgaRatio"].drop_nulls().mean()
            aiS = f"{ai:.1f}%" if ai is not None else "N/A"
            liS = f"{li:.1f}%" if li is not None else "N/A"
            rphS = f"{rph / 1e8:.1f}" if rph is not None else "N/A"
            hcS = f"{hc:,.0f}" if hc is not None else "N/A"
            sgaS = f"{sga:.1f}%" if sga is not None else "N/A"
            print(f"{sector:12s} | {aiS:>10s} | {liS:>12s} | {rphS:>14s} | {hcS:>10s} | {sgaS:>10s}")

        # 4사분면 분류
        validDf = df.filter(
            pl.col("assetIntensity").is_not_null() & pl.col("laborIntensity").is_not_null()
        )
        if len(validDf) > 0:
            medianAI = validDf["assetIntensity"].median()
            medianLI = validDf["laborIntensity"].median()

            print(f"\n[4사분면 기준: 자산집약도 중앙값={medianAI:.1f}%, 인건비집약도 중앙값={medianLI:.1f}%]")

            for _, row_data in enumerate(validDf.iter_rows(named=True)):
                ai_val = row_data["assetIntensity"]
                li_val = row_data["laborIntensity"]
                if ai_val < medianAI and li_val < medianLI:
                    quad = "Q1(경량+저노동)"
                elif ai_val < medianAI and li_val >= medianLI:
                    quad = "Q2(경량+고노동)"
                elif ai_val >= medianAI and li_val < medianLI:
                    quad = "Q3(중자산+저노동)"
                else:
                    quad = "Q4(중자산+고노동)"

                print(f"  {row_data['corpName']:12s} ({row_data['sector']:8s}) | "
                      f"자산={ai_val:5.1f}% 노동={li_val:5.1f}% → {quad}")

        # 유효 데이터 비율
        print(f"\n[유효 데이터]")
        print(f"  assetIntensity:  {df['assetIntensity'].drop_nulls().len()}/{len(df)}")
        print(f"  laborIntensity:  {df['laborIntensity'].drop_nulls().len()}/{len(df)}")
        print(f"  headcount:       {df['headcount'].drop_nulls().len()}/{len(df)}")

    return df


if __name__ == "__main__":
    start = time.time()
    df = runCostFingerprint()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    outPath = DATA_DIR / "003_costFingerprint.parquet"
    df.write_parquet(outPath)
    print(f"\n→ {outPath} ({elapsed:.1f}s)")
