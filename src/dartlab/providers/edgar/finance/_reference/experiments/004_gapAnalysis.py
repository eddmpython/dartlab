"""
실험 ID: 004
실험명: total_liabilities 갭 원인 분석 + 수정 검증 + 파생 계정 실배치 설계

목적:
- AMZN/WMT에서 total_liabilities가 누락되는 근본 원인 규명
- 003에서 적용한 284개 오매핑 수정의 품질 검증
- 파생 계정(gross_profit, non_current_assets 등) pivot.py 실배치 설계 확정

가설:
1. total_liabilities 누락은 매핑 문제가 아닌 pivot.py의 stmt 분류 문제
   (Liabilities 태그가 BS가 아닌 다른 stmt로 분류될 가능성)
2. 284개 수정 중 10% 이상이 과도한 재분류 (키워드 오매칭)
3. 파생 계정 3개(gross_profit, non_current_assets, non_current_liabilities) 추가 시
   10사 공통 핵심계정 13/21 → 16/21 달성

방법:
1. AMZN/WMT parquet에서 Liabilities 관련 태그 직접 추적
2. mapper → pivot 전 과정에서 어디서 탈락하는지 확인
3. 284개 수정 목록을 패턴별 분류 → 오분류 후보 식별
4. 파생 계정 계산 → 공통 핵심계정 수 변화 측정

결과 (2026-03-10):

[Phase 1] total_liabilities 갭 추적
  ★ AMZN/WMT는 "Liabilities" 태그 자체를 SEC에 보고하지 않음!
  - AMZN: LiabilitiesCurrent(134행), LiabilitiesNoncurrent(14행) 있음 → Liabilities 없음
  - WMT: LiabilitiesCurrent(185행) 있음, LiabilitiesNoncurrent 없음 → Liabilities 없음
  - 매핑 문제가 아닌 기업 보고 방식 차이
  - 해결: total_liabilities = current_liabilities + non_current_liabilities 파생 계산

  ★ _guessStmt는 Liabilities 관련 태그를 모두 BS로 올바르게 분류 → stmt 분류 문제 아님

  ★ DeferredTaxAssetsLiabilitiesNet → total_liabilities로 잘못 매핑 (003 수정 오류)
    AMZN: 이 태그가 21행(FY만), WMT: 8행(FY만)으로 total_liabilities 오매핑 확인

[Phase 2] 284개 수정 품질 검증
  카테고리별: non_current_assets(160), total_liabilities(98), operating_income(11),
             cost_of_sales(9), current_assets(5), gross_profit(1)
  의심스러운 수정: 71개 (25%)
  주요 오류 패턴:
    1. liability→asset 전환 (37개): "noncurrent" 키워드가 non_current_assets 패턴에 매칭
       예: otherliabilitiesnoncurrent → non_current_assets (❌ 부채인데 자산으로)
       예: pensionandotherpostretirementbenefitplansliabilitiesnoncurrent → non_current_assets (❌)
    2. 세부항목→합계 승격 (12개): accruedliabilities → total_liabilities (❌)
    3. asset→liability 전환 (22개): DeferredTaxAssetsLiabilitiesNet → total_liabilities (❌)
  ★ 003 실험 phase2의 coreRelated 패턴 매칭이 너무 공격적
    "noncurrent" 패턴이 liability 태그에도 매칭 → non_current_assets로 잘못 분류

[Phase 3] 파생 계정 추가 시 커버리지 변화
  GOOG: gross_profit 파생(33Q)
  AMZN: non_current_assets 파생(50Q) — total_liabilities 여전히 누락
  META: gross_profit 파생(50Q)
  XOM: non_current_liabilities 파생(50Q) — cost_of_sales/gross_profit/operating_income 여전히 누락
  WMT: gross_profit(62Q) + non_current_assets(49Q) 파생 — total_liabilities/non_current_liabilities 누락
  10사 공통: 40개, 공통 핵심: 13/21 (변동 없음)

[Phase 4] _guessStmt 분류 디버그
  모든 Liabilities 관련 태그 → BS로 올바르게 분류 (정상)
  TotalLiabilities → 미매핑 (us-gaap 태그가 아니라 비표준)
  OtherLiabilities → total_liabilities로 매핑 (003 수정에 의해)

결론:
- 가설1 채택: total_liabilities 누락은 매핑/stmt 문제 아닌 "보고 안 함"
  → 해결: total_liabilities = current_liabilities + non_current_liabilities 파생
  → WMT는 non_current_liabilities도 없어서 추가 파생 필요
- 가설2 채택: 284개 중 71개(25%) 과도한 재분류 → 즉시 롤백 필요
  → 003의 "noncurrent" 패턴 매칭이 liability 태그를 asset으로 잘못 전환
  → 세부항목을 합계(total_liabilities)로 승격시킨 것도 부적절
- 가설3 부분 채택: 파생 추가해도 13/21 유지 (AMZN/WMT/JPM/XOM 업종 한계)

다음 작업:
1. 71개 오수정 롤백 (이전 값으로 복원 또는 삭제)
2. total_liabilities 파생 계산 추가 (pivot.py _computeDerived)
3. WMT non_current_liabilities 파생: 별도 계산 로직 필요

실험일: 2026-03-10
"""

import sys
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl
from dartlab.providers.edgar.finance.mapper import EdgarMapper
from dartlab.providers.edgar.finance.pivot import buildTimeseries

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"
MAPPER_DATA = PROJECT_ROOT / "src" / "dartlab" / "engines" / "edgar" / "finance" / "mapperData"
REF_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = REF_DIR / "learningLogs"

TICKERS = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "NVDA": "0001045810",
    "META": "0001326801",
    "JPM": "0000019617",
    "JNJ": "0000200406",
    "XOM": "0000034088",
    "WMT": "0000104169",
}

CORE_ACCOUNTS = [
    "revenue", "cost_of_sales", "gross_profit", "operating_income", "net_income",
    "total_assets", "current_assets", "non_current_assets",
    "cash_and_equivalents", "inventories",
    "total_liabilities", "current_liabilities", "non_current_liabilities",
    "total_equity", "equity_including_nci",
    "operating_cashflow", "investing_cashflow", "financing_cashflow",
    "trade_receivables", "ppe",
    "profit_before_tax",
]


def phase1_traceLiabilities():
    """Phase 1: AMZN/WMT에서 Liabilities 태그 추적."""
    print("\n[Phase 1] total_liabilities 갭 추적")
    print("=" * 60)

    targets = {"AMZN": "0001018724", "WMT": "0000104169"}

    for ticker, cik in targets.items():
        print(f"\n  --- {ticker} (CIK: {cik}) ---")

        path = EDGAR_DIR / f"{cik}.parquet"
        if not path.exists():
            print(f"  파일 없음: {path}")
            continue

        df = pl.read_parquet(path)
        df = df.filter(pl.col("namespace") == "us-gaap")

        liabTags = df.filter(
            pl.col("tag").str.to_lowercase().str.contains("liabilit")
        ).select("tag").unique().to_series().to_list()

        print(f"  'liabilit' 포함 태그: {len(liabTags)}개")

        for tag in sorted(liabTags):
            sid = EdgarMapper.mapToDart(tag)
            sidStr = sid if sid else "(미매핑)"

            tagRows = df.filter(pl.col("tag") == tag)
            fpValues = tagRows.select("fp").unique().to_series().to_list()
            rowCount = tagRows.height

            marker = "***" if sid == "total_liabilities" else "   "
            print(f"    {marker} {tag:<50s} → {sidStr:<30s} [{rowCount}행, fp={fpValues}]")

        liabTag = "Liabilities"
        liabRows = df.filter(pl.col("tag") == liabTag)
        if liabRows.height > 0:
            print(f"\n  [Liabilities 태그 상세]")
            print(f"    행수: {liabRows.height}")
            print(f"    fp: {liabRows.select('fp').unique().to_series().to_list()}")
            print(f"    fy: {sorted(liabRows.select('fy').unique().to_series().to_list())}")

            stmtTags = EdgarMapper.classifyTagsByStmt()
            inBS = "Liabilities" in stmtTags.get("BS", set())
            inIS = "Liabilities" in stmtTags.get("IS", set())
            inCF = "Liabilities" in stmtTags.get("CF", set())
            print(f"    classifyTagsByStmt: BS={inBS}, IS={inIS}, CF={inCF}")

            sid = EdgarMapper.mapToDart("Liabilities", "BS")
            print(f"    mapToDart('Liabilities', 'BS') → {sid}")
            sid2 = EdgarMapper.mapToDart("Liabilities", "")
            print(f"    mapToDart('Liabilities', '') → {sid2}")

            sample = liabRows.head(5)
            for row in sample.iter_rows(named=True):
                print(f"    예시: fy={row['fy']}, fp={row['fp']}, val={row['val']}, "
                      f"start={row.get('start')}, end={row.get('end')}, filed={row.get('filed')}")
        else:
            print(f"\n  [Liabilities 태그 없음!]")

            altTags = [t for t in liabTags if t.lower() in [
                "liabilities", "liabilitiesandstockholdersequity",
                "totalliabilities",
            ]]
            print(f"  대안 태그: {altTags}")

        result = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        if result:
            series, periods = result
            bsSids = list(series.get("BS", {}).keys())
            hasTotalLiab = "total_liabilities" in bsSids
            print(f"\n  buildTimeseries 결과:")
            print(f"    BS snakeId 수: {len(bsSids)}")
            print(f"    total_liabilities 존재: {hasTotalLiab}")

            if not hasTotalLiab:
                liabRelated = [sid for sid in bsSids if "liab" in sid]
                print(f"    liab 관련 snakeId: {liabRelated}")

                isSids = list(series.get("IS", {}).keys())
                cfSids = list(series.get("CF", {}).keys())
                isLiab = [sid for sid in isSids if "liab" in sid]
                cfLiab = [sid for sid in cfSids if "liab" in sid]
                if isLiab:
                    print(f"    IS에 liab 관련: {isLiab}")
                if cfLiab:
                    print(f"    CF에 liab 관련: {cfLiab}")


def phase2_verifyFixes():
    """Phase 2: 003 실험에서 적용한 수정 검증."""
    print("\n[Phase 2] 284개 수정 품질 검증")
    print("=" * 60)

    logFiles = sorted(LOG_DIR.glob("*fix_mismappings*.json"))
    if not logFiles:
        print("  수정 로그 파일 없음")
        return

    with open(logFiles[-1], encoding="utf-8") as f:
        logData = json.load(f)

    fixes = logData.get("fixes", {})
    print(f"  수정 로그: {logFiles[-1].name}")
    print(f"  총 수정: {len(fixes)}개")

    categories = {
        "non_current_assets": [],
        "current_liabilities": [],
        "non_current_liabilities": [],
        "current_assets": [],
        "total_liabilities": [],
        "gross_profit": [],
        "operating_income": [],
        "cost_of_sales": [],
        "기타": [],
    }

    suspicious = []

    for tag, info in fixes.items():
        fromSid = info["from"]
        toSid = info["to"]

        categorized = False
        for cat in categories:
            if cat != "기타" and toSid == cat:
                categories[cat].append((tag, fromSid, toSid))
                categorized = True
                break
        if not categorized:
            categories["기타"].append((tag, fromSid, toSid))

        if "liabilit" in tag and toSid in ["non_current_assets", "current_assets", "total_assets"]:
            suspicious.append((tag, fromSid, toSid, "liability→asset 전환"))
        elif "asset" in tag and toSid in ["total_liabilities", "current_liabilities", "non_current_liabilities"]:
            suspicious.append((tag, fromSid, toSid, "asset→liability 전환"))
        elif "other" in fromSid and toSid.startswith("other_"):
            suspicious.append((tag, fromSid, toSid, "other→other 순환"))
        elif "accrued" in tag and toSid == "total_liabilities":
            suspicious.append((tag, fromSid, toSid, "세부항목→합계 승격"))

    print(f"\n  [카테고리별 분류]")
    for cat, items in categories.items():
        if items:
            print(f"    {cat}: {len(items)}개")

    if suspicious:
        print(f"\n  [의심스러운 수정: {len(suspicious)}개]")
        for tag, fromSid, toSid, reason in suspicious:
            print(f"    {tag:<50s} {fromSid:<30s} → {toSid:<25s} ({reason})")

    return suspicious


def phase3_derivedAccountsCoverage():
    """Phase 3: 파생 계정 추가 시 공통 핵심계정 변화."""
    print("\n[Phase 3] 파생 계정 추가 시 커버리지 변화")
    print("=" * 60)

    derivable = {
        "gross_profit": ("IS", "revenue", "IS", "cost_of_sales", "subtract"),
        "non_current_assets": ("BS", "total_assets", "BS", "current_assets", "subtract"),
        "non_current_liabilities": ("BS", "total_liabilities", "BS", "current_liabilities", "subtract"),
    }

    allSnakeIdSets = {}
    derivedUsed = {}

    for ticker, cik in TICKERS.items():
        result = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        if result is None:
            continue

        series, periods = result
        allSids = set()
        for stmt in series:
            allSids.update(series[stmt].keys())

        derivedList = []
        for targetSid, (aStmt, aSid, bStmt, bSid, op) in derivable.items():
            if targetSid not in allSids:
                aVals = series.get(aStmt, {}).get(aSid)
                bVals = series.get(bStmt, {}).get(bSid)
                if aVals and bVals:
                    nonNull = sum(1 for a, b in zip(aVals, bVals) if a is not None and b is not None)
                    if nonNull > 0:
                        allSids.add(targetSid)
                        derivedList.append(f"{targetSid}({nonNull}Q)")

        allSnakeIdSets[ticker] = allSids
        if derivedList:
            derivedUsed[ticker] = derivedList

        coreHits = sum(1 for sid in CORE_ACCOUNTS if sid in allSids)
        missing = [sid for sid in CORE_ACCOUNTS if sid not in allSids]
        missingStr = ", ".join(missing) if missing else "없음"
        derivedStr = " + ".join(derivedList) if derivedList else ""
        print(f"  {ticker}: {coreHits}/{len(CORE_ACCOUNTS)} ({coreHits/len(CORE_ACCOUNTS)*100:.0f}%) "
              f"누락: {missingStr}")
        if derivedStr:
            print(f"         파생: {derivedStr}")

    tickers = list(allSnakeIdSets.keys())
    if len(tickers) >= 2:
        commonAll = allSnakeIdSets[tickers[0]]
        for t in tickers[1:]:
            commonAll = commonAll & allSnakeIdSets[t]

        print(f"\n  10사 공통 snakeId: {len(commonAll)}개")

        coreInCommon = [sid for sid in CORE_ACCOUNTS if sid in commonAll]
        print(f"  공통 핵심계정: {len(coreInCommon)}/{len(CORE_ACCOUNTS)}")
        for sid in CORE_ACCOUNTS:
            marker = "O" if sid in commonAll else "X"
            coverage = sum(1 for t in tickers if sid in allSnakeIdSets[t])
            print(f"    [{marker}] {sid:<30s} ({coverage}/{len(tickers)}사)")


def phase4_stmtClassificationDebug():
    """Phase 4: _guessStmt가 Liabilities를 잘못 분류하는지 확인."""
    print("\n[Phase 4] _guessStmt 분류 디버그")
    print("=" * 60)

    from dartlab.providers.edgar.finance.pivot import _guessStmt

    testTags = [
        "Liabilities",
        "LiabilitiesCurrent",
        "LiabilitiesNoncurrent",
        "LiabilitiesAndStockholdersEquity",
        "TotalLiabilities",
        "OtherLiabilities",
        "OtherLiabilitiesCurrent",
        "OtherLiabilitiesNoncurrent",
        "AccruedLiabilitiesCurrent",
    ]

    stmtTags = EdgarMapper.classifyTagsByStmt()
    allStmtTags = set()
    for stmtSet in stmtTags.values():
        allStmtTags.update(stmtSet)

    for tag in testTags:
        guessedStmt = _guessStmt(tag)
        inCommonTags = tag in allStmtTags
        sid = EdgarMapper.mapToDart(tag)
        sidStr = sid if sid else "(미매핑)"

        expectedStmt = "BS"
        marker = "OK" if guessedStmt == expectedStmt else "!!"
        commonMarker = "CT" if inCommonTags else "  "

        print(f"  [{marker}] [{commonMarker}] {tag:<45s} → stmt={guessedStmt:<4s} sid={sidStr}")

    amznPath = EDGAR_DIR / "0001018724.parquet"
    if amznPath.exists():
        df = pl.read_parquet(amznPath)
        df = df.filter((pl.col("namespace") == "us-gaap") & (pl.col("tag") == "Liabilities"))
        if df.height > 0:
            print(f"\n  [AMZN Liabilities 원본 데이터]")
            print(f"    행수: {df.height}")
            fps = df.select("fp").unique().to_series().to_list()
            print(f"    fp: {fps}")

            for fp in sorted(fps):
                fpRows = df.filter(pl.col("fp") == fp)
                print(f"\n    fp={fp}: {fpRows.height}행")
                for row in fpRows.sort("fy").head(3).iter_rows(named=True):
                    print(f"      fy={row['fy']}, val={row['val']}, "
                          f"start={row.get('start')}, end={row.get('end')}")


def main():
    print("=" * 70)
    print("EDGAR 갭 분석 + 수정 검증 + 파생 계정 설계")
    print("=" * 70)

    phase1_traceLiabilities()
    phase2_verifyFixes()
    phase4_stmtClassificationDebug()
    phase3_derivedAccountsCoverage()


if __name__ == "__main__":
    main()
