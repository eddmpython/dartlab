"""
실험 ID: 007
실험명: 파생 계정 정확도 검증 (S&P 100 대형주)

목적:
- 파생 계정 5개 공식의 실제 정확도를 S&P 100 대형주에서 검증
- "보고값이 있는 종목"에서 파생값 vs 보고값 오차율 측정
- 금융 vs 비금융 업종 분리 분석
- _computeDerived() 프로덕션 배치 전 정확도 근거 확보

가설:
1. 비금융 대형주에서 파생값 오차율 1% 이내가 95%+
2. total_liabilities = total_assets - equity_including_nci 정확도 99%+
3. 금융업종(JPM, GS, BAC 등)은 비금융 대비 오차율 높을 수 있음
4. 파생 순서(total_liabilities 먼저 → non_current_liabilities)가 정확도에 영향

방법:
1. S&P 100 (고유 100 CIK) buildTimeseries 실행
2. 각 종목에서 파생 대상 5개 계정의 보고값 존재 여부 확인
3. 보고값이 있는 종목에 한해 파생값 계산 후 오차 측정
4. 오차율 = |파생값 - 보고값| / |보고값| × 100
5. 분기별 오차 분포 (최대/평균/중앙값)
6. 금융 vs 비금융 분리 비교

결과 (2026-03-10):

[Phase 2-5] buildTimeseries 기반 검증 (매핑된 snakeId)
  ★ 핵심 발견: 오차의 대부분은 파생 공식 오류가 아니라 **매핑 오류**
  - total_liabilities: DeferredTaxLiabilitiesTaxDeferredIncome, DerivativeLiabilities 등
    세부 항목이 total_liabilities로 오매핑 → 보고값 자체가 왜곡
  - non_current_assets, non_current_liabilities도 동일 패턴
  - 오매핑 제외 후에도 잔여 오차 존재 (BS 전기비교값 혼입)

  D1 (total_liab = assets - equity): 3,100 포인트, ≤1% 57.8%, ≤5% 84.8%
    비금융 54.4%, 금융 69.5% (금융이 더 양호 — 직접 보고 비율 높음)
  D2 (total_liab = cur + noncur): 235 포인트, ≤1% 34.0% (검증가능 18사)
  D3 (gross_profit = rev - cogs): 1,462 포인트, ≤1% 80.7% (Q4 역산 오차 주원인)
  D4 (noncur_assets = total - cur): 786 포인트, ≤1% 29.0% (오매핑 557건 제외 후)
  D5 (noncur_liab = total - cur): 175 포인트, ≤1% 45.7%

  ★ 낮은 정확도의 원인 분석:
  1. **오매핑**: 세부 항목 태그가 합산 계정(total_liabilities, non_current_assets 등)으로
     잘못 학습됨 → learnedSynonyms.json 오학습
  2. **Q4 역산**: IS/CF에서 Q4 = FY - Q1 - Q2 - Q3 역산 시
     전기비교값이 혼입되면 대규모 오차 발생
  3. **BS 전기비교값**: 동일 (fy, fp) 조합에 전기/당기 값이 공존,
     end 정렬로 당기를 선택하나 간혹 전기 선택

[Phase 5] 커버리지 증가 효과 (S&P 100 기준)
  D1: total_liabilities 84% → 100% (+16)
  D2: total_liabilities 84% → 92% (+8, D1과 중복)
  D3: gross_profit 34% → 72% (+38) ★ 최대 효과
  D4: non_current_assets 90% → 99% (+9)
  D5: non_current_liabilities 30% → 77% (+47) ★ 최대 효과

[Phase 6] XBRL 원본 태그 기반 검증 (매핑 우회)
  매핑 오류를 배제하고 원본 XBRL 태그로 직접 검증.
  R1 (Liabilities = Assets - Equity): 3,638 포인트, ≤1% 61.4%
    비금융 57.1%, 금융 75.0%
    → 전기비교값 혼입이 주원인 (META 2017-Q3 등)
  R2 (Liabilities = Current + Noncurrent): 117 포인트, ≤1% 91.5% (7사)
    → PG FY에서만 오차 (10건), Q 분기는 100% 정확
  R3 (GrossProfit = Revenue - CostOfRevenue): 670 포인트, ≤1% 50.7%
    → Q4 역산 + 전기비교값 혼입
  R4 (NoncurrentAssets = Assets - CurrentAssets): 669 포인트, ≤1% 45.7%
    → TSLA 스케일 문제 (2012 초기), 전기비교 혼입
  R5 (NoncurrentLiab = Liab - CurrentLiab): 117 포인트, ≤1% 91.5% (7사)
    → R2와 동일, PG FY에서만 오차

[Phase 4] 파생 체인 (D1→D5) 검증
  319 포인트 중 ≤1%: 52.0%
  → total_liabilities 오매핑 → non_current_liabilities 연쇄 오차

결론:
- 가설1 기각: 비금융 ≤1% 정확도는 57% 수준 (95% 미달)
  BUT 원인은 **파생 공식 오류가 아니라 데이터/매핑 품질 문제**
- 가설2 기각: R1(원본 태그) 61.4% — 전기비교값 혼입이 주원인
  BUT R2/R5(동일 stmt 태그) 91.5%로 직접 합산은 정확
- 가설3 부분 기각: 금융이 비금융보다 오히려 양호 (75% vs 57%)
  금융업은 Liabilities 태그를 직접 보고하는 비율이 높기 때문
- 가설4 확인: D1 오류 → D5 연쇄 전파 존재 (52%)

★ 프로덕션 배치 판단:
  1. _computeDerived() 공식 자체는 수학적으로 정확
  2. 정확도 병목은 **파생이 아니라 BS 기간 선택/오매핑**
  3. 배치 조건:
     a) total_liabilities/non_current_liabilities: 보고값 없을 때만 파생 → 안전
     b) gross_profit: 보고값 없을 때만 파생 → 안전
     c) non_current_assets: 보고값 없을 때만 파생 → 안전
     d) 파생값이 기존 보고값을 **덮어쓰지 않는** 한 부작용 없음
  4. ★ 별도 과제: learnedSynonyms.json 오매핑 정리 (008?)

실험일: 2026-03-10
"""

import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dartlab.engines.edgar.finance.pivot import buildTimeseries

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"

SP100 = {
    "AAPL": "0000320193", "ABBV": "0001551152", "ABT": "0000001800",
    "ACN": "0001467373", "ADBE": "0000796343", "AIG": "0000005272",
    "AMD": "0000002488", "AMGN": "0000318154", "AMZN": "0001018724",
    "AVGO": "0001730168", "AXP": "0000004962", "BA": "0000012927",
    "BAC": "0000070858", "BK": "0001390777", "BKNG": "0001075531",
    "BLK": "0002012383", "BMY": "0000014272", "BRK-B": "0001067983",
    "C": "0000831001", "CAT": "0000018230", "CHTR": "0001091667",
    "CL": "0000021665", "CMCSA": "0001166691", "COF": "0000927628",
    "COP": "0001163165", "COST": "0000909832", "CRM": "0001108524",
    "CSCO": "0000858877", "CVS": "0000064803", "CVX": "0000093410",
    "DE": "0000315189", "DHR": "0000313616", "DIS": "0001744489",
    "DOW": "0001751788", "DUK": "0001326160", "EMR": "0000032604",
    "EXC": "0001109357", "F": "0000037996", "FDX": "0001048911",
    "GD": "0000040533", "GE": "0000040545", "GILD": "0000882095",
    "GM": "0001467858", "GOOG": "0001652044", "GS": "0000886982",
    "HD": "0000354950", "HON": "0000773840", "IBM": "0000051143",
    "INTC": "0000050863", "INTU": "0000896878", "JNJ": "0000200406",
    "JPM": "0000019617", "KHC": "0001637459", "KO": "0000021344",
    "LIN": "0001707925", "LLY": "0000059478", "LMT": "0000936468",
    "LOW": "0000060667", "MA": "0001141391", "MCD": "0000063908",
    "MDLZ": "0001103982", "MDT": "0001613103", "MET": "0001099219",
    "META": "0001326801", "MMM": "0000066740", "MO": "0000764180",
    "MRK": "0000310158", "MS": "0000895421", "MSFT": "0000789019",
    "NEE": "0000753308", "NFLX": "0001065280", "NKE": "0000320187",
    "NVDA": "0001045810", "ORCL": "0001341439", "PEP": "0000077476",
    "PFE": "0000078003", "PG": "0000080424", "PM": "0001413329",
    "PYPL": "0001633917", "QCOM": "0000804328", "RTX": "0000101829",
    "SBUX": "0000829224", "SCHW": "0000316709", "SO": "0000092122",
    "SPG": "0001063761", "T": "0000732717", "TGT": "0000027419",
    "TMO": "0000097745", "TMUS": "0001283699", "TSLA": "0001318605",
    "TXN": "0000097476", "UNH": "0000731766", "UNP": "0000100885",
    "UPS": "0001090727", "USB": "0000036104", "V": "0001403161",
    "VZ": "0000732712", "WFC": "0000072971", "WMT": "0000104169",
    "XOM": "0000034088",
}

FINANCIAL_TICKERS = {"AIG", "AXP", "BAC", "BK", "BLK", "BRK-B", "C", "COF", "GS", "JPM", "MET", "MS", "SCHW", "USB", "WFC"}

DERIVED_FORMULAS = [
    {
        "id": "D1",
        "target": "total_liabilities",
        "stmt": "BS",
        "formula": "total_assets - equity_including_nci",
        "sources": ["total_assets", "equity_including_nci"],
        "op": "subtract",
    },
    {
        "id": "D2",
        "target": "total_liabilities",
        "stmt": "BS",
        "formula": "current_liabilities + non_current_liabilities",
        "sources": ["current_liabilities", "non_current_liabilities"],
        "op": "add",
    },
    {
        "id": "D3",
        "target": "gross_profit",
        "stmt": "IS",
        "formula": "revenue - cost_of_sales",
        "sources": ["revenue", "cost_of_sales"],
        "op": "subtract",
    },
    {
        "id": "D4",
        "target": "non_current_assets",
        "stmt": "BS",
        "formula": "total_assets - current_assets",
        "sources": ["total_assets", "current_assets"],
        "op": "subtract",
    },
    {
        "id": "D5",
        "target": "non_current_liabilities",
        "stmt": "BS",
        "formula": "total_liabilities - current_liabilities",
        "sources": ["total_liabilities", "current_liabilities"],
        "op": "subtract",
    },
]


def loadAllTimeseries():
    """S&P 100 전체 buildTimeseries 실행."""
    print("[Phase 1] S&P 100 buildTimeseries 로드")
    print("=" * 60)

    results = {}
    errors = []
    seen = set()

    for ticker, cik in sorted(SP100.items()):
        if cik in seen:
            continue
        seen.add(cik)

        ts = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        if ts is None:
            errors.append(ticker)
            continue
        results[ticker] = ts

    print(f"  로드 성공: {len(results)}개")
    if errors:
        print(f"  로드 실패: {errors}")
    return results


def validateFormula(formula, series, periods):
    """단일 종목 + 단일 공식의 분기별 오차 측정.

    Returns:
        list of (period, reported, derived, errorPct) 또는 None (검증 불가)
    """
    stmt = formula["stmt"]
    target = formula["target"]
    sources = formula["sources"]
    op = formula["op"]

    stmtData = series.get(stmt, {})
    targetVals = stmtData.get(target)
    if targetVals is None:
        return None

    sourceVals = []
    for src in sources:
        vals = stmtData.get(src)
        if vals is None:
            return None
        sourceVals.append(vals)

    results = []
    skipped = 0
    for i, period in enumerate(periods):
        reported = targetVals[i]
        if reported is None or reported == 0:
            continue

        srcVals = [sv[i] for sv in sourceVals]
        if any(v is None for v in srcVals):
            continue

        if op == "subtract":
            derived = srcVals[0] - srcVals[1]
        elif op == "add":
            derived = srcVals[0] + srcVals[1]
        else:
            continue

        maxSrc = max(abs(v) for v in srcVals)
        if maxSrc > 0 and abs(reported) / maxSrc < 0.01:
            skipped += 1
            continue

        if abs(derived) > 0 and abs(reported) > 0:
            ratio = max(abs(derived), abs(reported)) / min(abs(derived), abs(reported))
            if ratio > 10:
                skipped += 1
                continue

        errorPct = abs(derived - reported) / abs(reported) * 100
        results.append((period, reported, derived, errorPct))

    return (results, skipped) if results else None


def phase2_validateAll(allData):
    """Phase 2: 전체 종목 × 전체 공식 검증."""
    print("\n[Phase 2] 파생 공식 정확도 검증")
    print("=" * 60)

    formulaResults = defaultdict(lambda: {"total": 0, "under1pct": 0, "under5pct": 0, "errors": [], "tickers": [], "financial": defaultdict(list), "skipped": 0})

    for ticker, (series, periods) in sorted(allData.items()):
        isFinancial = ticker in FINANCIAL_TICKERS

        for formula in DERIVED_FORMULAS:
            fid = formula["id"]
            result = validateFormula(formula, series, periods)
            if result is None:
                continue

            validations, skipped = result
            fr = formulaResults[fid]
            fr["tickers"].append(ticker)
            fr["skipped"] += skipped

            for period, reported, derived, errorPct in validations:
                fr["total"] += 1
                if errorPct <= 1.0:
                    fr["under1pct"] += 1
                if errorPct <= 5.0:
                    fr["under5pct"] += 1
                if errorPct > 1.0:
                    fr["errors"].append({
                        "ticker": ticker,
                        "period": period,
                        "reported": reported,
                        "derived": derived,
                        "errorPct": errorPct,
                        "isFinancial": isFinancial,
                    })

                sector = "financial" if isFinancial else "nonFinancial"
                fr["financial"][sector].append(errorPct)

    return formulaResults


def phase3_printResults(formulaResults):
    """Phase 3: 결과 출력."""
    print("\n[Phase 3] 공식별 결과 요약")
    print("=" * 60)

    for formula in DERIVED_FORMULAS:
        fid = formula["id"]
        fr = formulaResults.get(fid)
        if fr is None:
            print(f"\n  {fid}: {formula['formula']} → 검증 불가 (데이터 없음)")
            continue

        total = fr["total"]
        u1 = fr["under1pct"]
        u5 = fr["under5pct"]
        tickerCount = len(fr["tickers"])
        skipped = fr["skipped"]

        print(f"\n  {fid}: {formula['target']} = {formula['formula']}")
        print(f"  검증 종목: {tickerCount}개, 분기-포인트: {total}개" + (f" (오매핑 제외: {skipped}건)" if skipped else ""))
        if total > 0:
            print(f"  오차 ≤1%: {u1}/{total} ({u1/total*100:.1f}%)")
            print(f"  오차 ≤5%: {u5}/{total} ({u5/total*100:.1f}%)")

        for sector in ["nonFinancial", "financial"]:
            errs = fr["financial"].get(sector, [])
            if not errs:
                continue
            avgErr = sum(errs) / len(errs)
            maxErr = max(errs)
            within1 = sum(1 for e in errs if e <= 1.0)
            label = "비금융" if sector == "nonFinancial" else "금융"
            print(f"    [{label}] {len(errs)} 포인트, 평균 {avgErr:.2f}%, 최대 {maxErr:.1f}%, ≤1%: {within1}/{len(errs)} ({within1/len(errs)*100:.1f}%)")

        bigErrors = [e for e in fr["errors"] if e["errorPct"] > 5.0]
        if bigErrors:
            print(f"  *** 오차 >5% ({len(bigErrors)}건):")
            bigErrors.sort(key=lambda x: -x["errorPct"])
            for e in bigErrors[:10]:
                fLabel = "[금융]" if e["isFinancial"] else ""
                print(f"      {e['ticker']:<6s} {e['period']:<9s} 보고={e['reported']:>15,.0f}  파생={e['derived']:>15,.0f}  오차={e['errorPct']:.1f}% {fLabel}")


def phase4_dependencyChain(allData):
    """Phase 4: 파생 순서 의존성 검증.

    D5(non_current_liabilities = total_liabilities - current_liabilities)는
    total_liabilities가 보고되지 않은 경우 D1로 먼저 파생해야 함.
    이 체인 파생의 정확도를 별도 측정.
    """
    print("\n[Phase 4] 파생 체인 의존성 검증")
    print("=" * 60)
    print("  D5 = total_liabilities - current_liabilities")
    print("  total_liabilities가 미보고 → D1(total_assets - equity) 선파생 필요\n")

    chainCount = 0
    chainErrors = []

    for ticker, (series, periods) in sorted(allData.items()):
        bs = series.get("BS", {})

        totalLiab = bs.get("total_liabilities")
        totalAssets = bs.get("total_assets")
        equity = bs.get("equity_including_nci")
        currentLiab = bs.get("current_liabilities")
        nonCurrentLiab = bs.get("non_current_liabilities")

        if nonCurrentLiab is None or currentLiab is None or totalAssets is None or equity is None:
            continue

        for i, period in enumerate(periods):
            ncl_reported = nonCurrentLiab[i]
            if ncl_reported is None or ncl_reported == 0:
                continue

            tl_reported = totalLiab[i] if totalLiab else None
            ta = totalAssets[i]
            eq = equity[i]
            cl = currentLiab[i]

            if ta is None or eq is None or cl is None:
                continue

            if tl_reported is not None:
                continue

            tl_derived = ta - eq
            ncl_derived = tl_derived - cl

            errorPct = abs(ncl_derived - ncl_reported) / abs(ncl_reported) * 100
            chainCount += 1
            if errorPct > 1.0:
                chainErrors.append({
                    "ticker": ticker,
                    "period": period,
                    "reported": ncl_reported,
                    "derived": ncl_derived,
                    "errorPct": errorPct,
                })

    if chainCount == 0:
        print("  체인 파생 대상 0건 (모든 종목이 total_liabilities 직접 보고)")
    else:
        within1 = chainCount - len(chainErrors)
        print(f"  체인 파생 포인트: {chainCount}개")
        print(f"  오차 ≤1%: {within1}/{chainCount} ({within1/chainCount*100:.1f}%)")
        if chainErrors:
            print(f"  오차 >1% ({len(chainErrors)}건):")
            for e in sorted(chainErrors, key=lambda x: -x["errorPct"])[:10]:
                print(f"    {e['ticker']:<6s} {e['period']:<9s} 보고={e['reported']:>15,.0f}  파생={e['derived']:>15,.0f}  오차={e['errorPct']:.1f}%")


def phase5_coverageGain(allData):
    """Phase 5: 파생으로 얻는 추가 커버리지."""
    print("\n[Phase 5] 파생 계정 커버리지 증가 효과")
    print("=" * 60)

    for formula in DERIVED_FORMULAS:
        fid = formula["id"]
        target = formula["target"]
        stmt = formula["stmt"]
        sources = formula["sources"]

        hasReported = 0
        canDerive = 0
        newCoverage = 0

        for ticker, (series, periods) in allData.items():
            stmtData = series.get(stmt, {})
            targetVals = stmtData.get(target)
            hasTarget = targetVals is not None and any(v is not None for v in targetVals)

            canDeriveThis = all(
                stmtData.get(src) is not None and any(v is not None for v in stmtData.get(src, []))
                for src in sources
            )

            if hasTarget:
                hasReported += 1
            if canDeriveThis:
                canDerive += 1
            if canDeriveThis and not hasTarget:
                newCoverage += 1

        total = len(allData)
        print(f"  {fid}: {target} = {formula['formula']}")
        print(f"    보고: {hasReported}/{total} ({hasReported/total*100:.0f}%)")
        print(f"    파생 가능: {canDerive}/{total} ({canDerive/total*100:.0f}%)")
        print(f"    신규 커버: +{newCoverage} ({newCoverage/total*100:.0f}%)")
        print()


def phase6_rawTagValidation():
    """Phase 6: XBRL 원본 태그 기반 파생 검증 (매핑 우회).

    buildTimeseries 결과가 아닌, 원본 parquet에서 직접 XBRL 태그를 읽어
    파생 공식의 수학적 정확도를 검증. 매핑 오류 영향 배제.
    """
    import polars as pl

    print("\n[Phase 6] XBRL 원본 태그 기반 파생 검증 (매핑 우회)")
    print("=" * 60)

    RAW_FORMULAS = [
        {
            "id": "R1",
            "label": "Liabilities = Assets - StockholdersEquity(NCI)",
            "target": "Liabilities",
            "sourceA": "Assets",
            "sourceB": ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "StockholdersEquity"],
            "op": "subtract",
        },
        {
            "id": "R2",
            "label": "Liabilities = LiabilitiesCurrent + LiabilitiesNoncurrent",
            "target": "Liabilities",
            "sourceA": "LiabilitiesCurrent",
            "sourceB": ["LiabilitiesNoncurrent"],
            "op": "add",
        },
        {
            "id": "R3",
            "label": "GrossProfit = Revenue - CostOfRevenue",
            "target": "GrossProfit",
            "sourceA": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
            "sourceB": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"],
            "op": "subtract",
        },
        {
            "id": "R4",
            "label": "AssetsNoncurrent = Assets - AssetsCurrent",
            "target": ["AssetsNoncurrent", "NoncurrentAssets"],
            "sourceA": "Assets",
            "sourceB": ["AssetsCurrent"],
            "op": "subtract",
        },
        {
            "id": "R5",
            "label": "LiabilitiesNoncurrent = Liabilities - LiabilitiesCurrent",
            "target": ["LiabilitiesNoncurrent", "NoncurrentLiabilities"],
            "sourceA": "Liabilities",
            "sourceB": ["LiabilitiesCurrent"],
            "op": "subtract",
        },
    ]

    seen = set()
    totalResults = {}
    for rf in RAW_FORMULAS:
        totalResults[rf["id"]] = {"total": 0, "within1": 0, "within5": 0, "errors": [], "tickers": 0, "financial": {"financial": [], "nonFinancial": []}}

    for ticker, cik in sorted(SP100.items()):
        if cik in seen:
            continue
        seen.add(cik)

        path = EDGAR_DIR / f"{cik}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(path)
        df = df.filter(
            (pl.col("namespace") == "us-gaap") &
            pl.col("frame").is_null() &
            pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"])
        )

        if df.height == 0:
            continue

        df = df.with_columns(
            (pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period")
        )

        tagPeriodVals = {}
        deduped = (
            df.filter(pl.col("end").is_not_null())
            .sort(["end", "filed"], descending=[True, True])
            .group_by(["tag", "period"])
            .agg(pl.col("val").first(), pl.col("end").first())
        )

        for row in deduped.iter_rows(named=True):
            tagPeriodVals.setdefault(row["tag"], {})[row["period"]] = row["val"]

        isFinancial = ticker in FINANCIAL_TICKERS

        for rf in RAW_FORMULAS:
            rid = rf["id"]
            targets = rf["target"] if isinstance(rf["target"], list) else [rf["target"]]
            sourceAs = rf["sourceA"] if isinstance(rf["sourceA"], list) else [rf["sourceA"]]
            sourceBs = rf["sourceB"] if isinstance(rf["sourceB"], list) else [rf["sourceB"]]

            targetData = None
            for t in targets:
                if t in tagPeriodVals:
                    targetData = tagPeriodVals[t]
                    break
            if targetData is None:
                continue

            srcAData = None
            for a in sourceAs:
                if a in tagPeriodVals:
                    srcAData = tagPeriodVals[a]
                    break
            if srcAData is None:
                continue

            srcBData = None
            for b in sourceBs:
                if b in tagPeriodVals:
                    srcBData = tagPeriodVals[b]
                    break
            if srcBData is None:
                continue

            fr = totalResults[rid]
            fr["tickers"] += 1
            sector = "financial" if isFinancial else "nonFinancial"

            for period, reported in targetData.items():
                if reported is None or reported == 0:
                    continue
                aVal = srcAData.get(period)
                bVal = srcBData.get(period)
                if aVal is None or bVal is None:
                    continue

                if rf["op"] == "subtract":
                    derived = aVal - bVal
                else:
                    derived = aVal + bVal

                errorPct = abs(derived - reported) / abs(reported) * 100
                fr["total"] += 1
                if errorPct <= 1.0:
                    fr["within1"] += 1
                if errorPct <= 5.0:
                    fr["within5"] += 1
                fr["financial"][sector].append(errorPct)
                if errorPct > 1.0:
                    fr["errors"].append({"ticker": ticker, "period": period, "reported": reported, "derived": derived, "errorPct": errorPct})

    for rf in RAW_FORMULAS:
        rid = rf["id"]
        fr = totalResults[rid]
        total = fr["total"]
        print(f"\n  {rid}: {rf['label']}")
        print(f"  검증 종목: {fr['tickers']}개, 분기-포인트: {total}개")
        if total > 0:
            print(f"  오차 ≤1%: {fr['within1']}/{total} ({fr['within1']/total*100:.1f}%)")
            print(f"  오차 ≤5%: {fr['within5']}/{total} ({fr['within5']/total*100:.1f}%)")

            for sector in ["nonFinancial", "financial"]:
                errs = fr["financial"][sector]
                if not errs:
                    continue
                avgErr = sum(errs) / len(errs)
                maxErr = max(errs)
                within1 = sum(1 for e in errs if e <= 1.0)
                label = "비금융" if sector == "nonFinancial" else "금융"
                print(f"    [{label}] {len(errs)} 포인트, 평균 {avgErr:.4f}%, 최대 {maxErr:.2f}%, ≤1%: {within1}/{len(errs)} ({within1/len(errs)*100:.1f}%)")

            bigErrors = [e for e in fr["errors"] if e["errorPct"] > 5.0]
            if bigErrors:
                print(f"  *** 오차 >5% ({len(bigErrors)}건):")
                for e in sorted(bigErrors, key=lambda x: -x["errorPct"])[:5]:
                    print(f"      {e['ticker']:<6s} {e['period']:<9s} 보고={e['reported']:>15,.0f}  파생={e['derived']:>15,.0f}  오차={e['errorPct']:.2f}%")


def main():
    print("=" * 70)
    print("007: 파생 계정 정확도 검증 (S&P 100)")
    print("=" * 70)

    allData = loadAllTimeseries()

    formulaResults = phase2_validateAll(allData)

    phase3_printResults(formulaResults)

    phase4_dependencyChain(allData)

    phase5_coverageGain(allData)

    phase6_rawTagValidation()


if __name__ == "__main__":
    main()
