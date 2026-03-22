"""
실험 ID: 004
실험명: EDGAR us-gaap 태그 → DART canonical snakeId 통합 매핑

목적:
- eddmpython standardAccounts.json의 commonTags → snakeId 매핑 활용
- EDGAR snakeId → DART canonical 변환 (002에서 도출한 alias 13개)
- AAPL/MSFT/NVDA 실제 태그로 매핑률 측정
- L2 엔진 호환성 검증 (소스 무관 동작 가능한지)

가설:
1. standardAccounts의 344개 commonTags로 핵심 재무 태그 80%+ 커버
2. learnedSynonyms 11,375개 추가 시 95%+ 커버
3. EDGAR→DART alias 13개로 L2 호환 100% 달성

방법:
1. standardAccounts.json에서 commonTags → snakeId 매핑 추출 (344개)
2. learnedSynonyms.json에서 tagMappings 추출 (11,375개)
3. 두 매핑 병합 (commonTags 우선)
4. EDGAR→DART alias 적용하여 DART canonical로 변환
5. AAPL/MSFT/NVDA 3사 태그에 매핑 적용, 매핑률 측정
6. L2 insight에서 사용하는 29개 snakeId 커버 여부 검증

결과:
  [매핑 데이터 규모]
  - commonTags 직접 매핑: 344 tags → 175 snakeIds
  - learnedSynonyms: 11,375 tags
  - 병합 후 전체: 11,713 tags (commonTags 우선)

  [태그 매핑률 (3사)]
               태그수  매핑됨  매핑률  행가중
  AAPL        503    463    92.0%  96.7%
  MSFT        543    506    93.2%  97.0%
  NVDA        625    581    93.0%  96.4%

  commonTags만 사용 시 24~29% → learnedSynonyms가 60%p 이상 기여

  [L2 호환성: 24/29 = 83%]
  미커버 5개 원인 분석:
  1. net_income → IS/CF 동일 태그 충돌 (NetIncomeLoss → net_income_cf 덮어쓰기)
  2. equity_including_nci → EDGAR total_equity가 DART equity_including_nci에 해당
  3. equity_nci → 3사 모두 MinorityInterest=0 (비지배지분 없는 기업)
  4. bonds → US-GAAP에 '사채' 개념 없음 (long_term_debt에 포함)
  5. issued_capital → US-GAAP은 common_stock + APIC 분리

  [자본 구조 차이 (IFRS vs US-GAAP)]
  - EDGAR total_equity = StockholdersEquity (NCI 포함 자본총계)
  - DART equity_including_nci = 자본총계 (NCI 포함)
  - DART total_equity = 지배기업 귀속 자본 (US-GAAP에 대응 태그 없음)
  - 해결: EDGAR total_equity → DART equity_including_nci로 매핑
         equity_including_nci - equity_nci = total_equity 역산

  [미매핑 태그 특성]
  - 대부분 주석공시 세부항목 (UnrecognizedTaxBenefits, FiniteLivedIntangibleAssets 등)
  - L2 분석에 불필요한 세부 계정 → 무시 가능

결론:
  가설 1 기각: commonTags만으로는 24~29% (80% 미달)
    → learnedSynonyms 필수, 병합 시 92~93% 달성
  가설 2 채택: 병합 후 행 가중 매핑률 96.4~97.0% (95%+ 달성)
  가설 3 부분 채택: alias 13개로 83% → 추가 조치 필요

  [패키지 배치 시 핵심 과제]
  1. stmt 기반 매핑: 동일 태그(NetIncomeLoss)가 IS와 CF에서 다른 snakeId
     → 매핑 시 sj_div(재무제표 구분) 정보 활용 필수
  2. EDGAR→DART alias 확장:
     - total_equity → equity_including_nci (기존 13개 + 1)
     - bonds/issued_capital은 US-GAAP에 없음 → L2에서 None 허용
  3. 매핑 JSON 독립 관리: standardAccounts + learnedSynonyms를
     dartlab의 mapperData/에 EDGAR 전용으로 배치

실험일: 2026-03-10
"""

import json
import sys
from pathlib import Path

import polars as pl

EDDM_FINANCE_DIR = Path(
    "C:/Users/MSI/OneDrive/Desktop/sideProject/nicegui/eddmpython"
    "/core/edgar/searchEdgar/finance"
)

EDGAR_TO_DART_ALIASES: dict[str, str] = {
    "operating_cash_flow": "operating_cashflow",
    "investing_cash_flow": "investing_cashflow",
    "financing_cash_flow": "financing_cashflow",
    "noncurrent_assets": "non_current_assets",
    "noncurrent_liabilities": "non_current_liabilities",
    "cost_of_revenue": "cost_of_sales",
    "inventory": "inventories",
    "property_plant_equipment": "ppe",
    "income_before_tax": "profit_before_tax",
    "short_term_debt": "short_term_borrowings",
    "long_term_debt": "long_term_borrowings",
    "accounts_receivable": "trade_receivables",
    "noncontrolling_interest": "equity_nci",
}

L2_INSIGHT_USED = {
    "revenue", "operating_income", "net_income", "total_assets",
    "current_assets", "non_current_assets", "total_liabilities",
    "current_liabilities", "non_current_liabilities", "total_equity",
    "equity_including_nci", "cash_and_equivalents", "inventories",
    "trade_receivables", "short_term_borrowings", "long_term_borrowings",
    "bonds", "operating_cashflow", "investing_cashflow", "financing_cashflow",
    "cost_of_sales", "gross_profit", "profit_before_tax",
    "income_tax_expense", "basic_eps", "diluted_eps", "ppe",
    "issued_capital", "equity_nci",
}

TICKER_CIK = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
}


def _getEdgarDir() -> Path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from dartlab import config
    return Path(config.dataDir) / "edgarData"


def buildCommonTagsMap() -> dict[str, str]:
    path = EDDM_FINANCE_DIR / "standardAccounts.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    tagMap = {}
    for acct in data["accounts"]:
        sid = acct["snakeId"]
        for tag in acct.get("commonTags", []):
            tagMap[tag] = sid
    return tagMap


def buildLearnedMap() -> dict[str, str]:
    path = EDDM_FINANCE_DIR / "learnedSynonyms.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tagMappings", {})


def buildFullMap() -> dict[str, str]:
    commonMap = buildCommonTagsMap()
    learnedMap = buildLearnedMap()

    fullMap = {}
    for tag, sid in learnedMap.items():
        fullMap[tag.lower()] = sid

    for tag, sid in commonMap.items():
        fullMap[tag.lower()] = sid

    return fullMap


def toDartCanonical(edgarSnakeId: str) -> str:
    return EDGAR_TO_DART_ALIASES.get(edgarSnakeId, edgarSnakeId)


def measureMappingRate(edgarDir: Path, fullMap: dict[str, str]):
    print(f"\n{'='*70}")
    print(f"  매핑 데이터 규모")
    print(f"{'='*70}")

    commonMap = buildCommonTagsMap()
    learnedMap = buildLearnedMap()
    print(f"  commonTags 직접 매핑: {len(commonMap)} tags → {len(set(commonMap.values()))} snakeIds")
    print(f"  learnedSynonyms 매핑: {len(learnedMap)} tags")
    print(f"  병합 후 전체 매핑: {len(fullMap)} tags (commonTags 우선)")

    for ticker, cik in TICKER_CIK.items():
        print(f"\n{'='*70}")
        print(f"  {ticker} (CIK={cik}) 매핑률 분석")
        print(f"{'='*70}")

        df = pl.read_parquet(edgarDir / "finance" / f"{cik}.parquet")
        usGaap = df.filter(pl.col("namespace") == "us-gaap")
        allTags = usGaap.select("tag").unique().to_series().to_list()

        mapped = {}
        unmapped = []
        for tag in allTags:
            sid = fullMap.get(tag.lower())
            if sid:
                mapped[tag] = sid
            else:
                unmapped.append(tag)

        total = len(allTags)
        nMapped = len(mapped)
        pct = nMapped / total * 100 if total > 0 else 0
        print(f"  총 태그: {total}, 매핑됨: {nMapped} ({pct:.1f}%), 미매핑: {len(unmapped)}")

        commonOnly = sum(1 for t in allTags if t.lower() in {k.lower() for k in buildCommonTagsMap()})
        print(f"  commonTags만: {commonOnly}/{total} ({commonOnly/total*100:.1f}%)")

        dartSnakeIds = set()
        for tag in allTags:
            sid = fullMap.get(tag.lower())
            if sid:
                dartSnakeIds.add(toDartCanonical(sid))

        l2Covered = dartSnakeIds & L2_INSIGHT_USED
        l2Missing = L2_INSIGHT_USED - dartSnakeIds
        print(f"\n  L2 snakeId 커버: {len(l2Covered)}/{len(L2_INSIGHT_USED)} ({len(l2Covered)/len(L2_INSIGHT_USED)*100:.0f}%)")

        if l2Missing:
            print(f"  L2 미커버:")
            for sid in sorted(l2Missing):
                print(f"    {sid}")

        rowWeighted = _measureRowWeighted(usGaap, fullMap)
        print(f"\n  행 가중 매핑률: {rowWeighted:.1f}%")

        if unmapped:
            unmappedCounts = {}
            for tag in unmapped:
                cnt = usGaap.filter(pl.col("tag") == tag).height
                unmappedCounts[tag] = cnt
            topUnmapped = sorted(unmappedCounts.items(), key=lambda x: -x[1])[:15]
            print(f"\n  미매핑 상위 15 (행 수 기준):")
            for tag, cnt in topUnmapped:
                print(f"    {tag:60} {cnt:>5} rows")


def _measureRowWeighted(usGaap: pl.DataFrame, fullMap: dict[str, str]) -> float:
    totalRows = usGaap.height
    if totalRows == 0:
        return 0.0

    mappedRows = 0
    tagCounts = usGaap.group_by("tag").len().to_dicts()
    for row in tagCounts:
        tag = row["tag"]
        cnt = row["len"]
        if tag.lower() in fullMap:
            mappedRows += cnt

    return mappedRows / totalRows * 100


def analyzeEquityMapping(edgarDir: Path, fullMap: dict[str, str]):
    print(f"\n{'='*70}")
    print(f"  자본 구조 매핑 분석 (IFRS vs US-GAAP)")
    print(f"{'='*70}")

    equityTags = [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "MinorityInterest",
        "CommonStockValue",
        "RetainedEarningsAccumulatedDeficit",
        "AdditionalPaidInCapital",
        "TreasuryStockValue",
        "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
    ]

    print(f"\n  {'US-GAAP 태그':65} → {'EDGAR snakeId':40} → {'DART canonical'}")
    print(f"  {'-'*65}-+-{'-'*40}-+-{'-'*25}")
    for tag in equityTags:
        edgarSid = fullMap.get(tag.lower(), "(unmapped)")
        dartSid = toDartCanonical(edgarSid) if edgarSid != "(unmapped)" else "(unmapped)"
        print(f"  {tag:65} → {edgarSid:40} → {dartSid}")

    print(f"""
  [자본 구조 핵심 차이]
  - EDGAR total_equity = StockholdersEquity (NCI 포함 가능)
    → DART에서는 이것이 equity_including_nci에 해당
  - EDGAR total_equity ≠ DART total_equity (지배기업 귀속만)
  - DART total_equity = EquityAttributableToOwnersOfParent (IFRS)
    → US-GAAP에는 이 태그가 없음
  - 해결: StockholdersEquity → equity_including_nci로 매핑
         StockholdersEquityIncluding... → equity_including_nci
         MinorityInterest → equity_nci
         equity_including_nci - equity_nci = total_equity (역산)
""")


def verifyWithPivot(edgarDir: Path, fullMap: dict[str, str]):
    print(f"\n{'='*70}")
    print(f"  003 피벗 결과 + 매핑 통합 검증 (AAPL)")
    print(f"{'='*70}")

    from importlib.util import module_from_spec, spec_from_file_location
    pivotPath = str(Path(__file__).parent / "003_pivotNormalize.py")
    spec = spec_from_file_location("pivot", pivotPath)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)

    cik = TICKER_CIK["AAPL"]
    df = pl.read_parquet(edgarDir / "finance" / f"{cik}.parquet")
    df = df.filter(pl.col("namespace") == "us-gaap")

    for stmtType, tags in mod.KEY_TAGS.items():
        selected = mod.selectStandalone(df, tags, stmtType)
        if selected.height == 0:
            continue

        pivoted = mod.pivotTimeseries(selected)
        pivoted = mod.computeQ4(pivoted, stmtType)

        print(f"\n  --- {stmtType} (tag → DART snakeId) ---")
        periodCols = [c for c in pivoted.columns if c != "tag"]
        showCols = periodCols[-5:]

        for row in pivoted.iter_rows(named=True):
            tag = row["tag"]
            edgarSid = fullMap.get(tag.lower(), "???")
            dartSid = toDartCanonical(edgarSid)
            vals = [f"{row.get(c, 0)/1e9:.1f}B" if row.get(c) else "—" for c in showCols]
            inL2 = "L2" if dartSid in L2_INSIGHT_USED else "  "
            print(f"  [{inL2}] {dartSid:35} {' | '.join(f'{v:>8}' for v in vals)}")

        hdr = f"  {'':41} {' | '.join(f'{c:>8}' for c in showCols)}"
        print(f"  {hdr}")


def main():
    edgarDir = _getEdgarDir()
    print(f"[EDGAR] 데이터 경로: {edgarDir}")

    fullMap = buildFullMap()
    measureMappingRate(edgarDir, fullMap)
    analyzeEquityMapping(edgarDir, fullMap)
    verifyWithPivot(edgarDir, fullMap)


if __name__ == "__main__":
    main()
