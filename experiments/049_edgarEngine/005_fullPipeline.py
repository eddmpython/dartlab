"""
실험 ID: 005
실험명: EDGAR 전체 파이프라인 통합 프로토타입

목적:
- 003(피벗) + 004(매핑) 결과를 통합하여 패키지 배치 전 전체 파이프라인 검증
- DART와 동일한 인터페이스 제공: buildTimeseries → buildAnnual → calcRatios
- EDGAR→DART canonical snakeId 변환으로 L2 엔진 호환성 검증
- IS/CF NetIncomeLoss 충돌 해결 (stmt 기반 매핑)
- AAPL/MSFT/NVDA 3사로 E2E 검증

가설:
1. stmt 기반 매핑으로 IS net_income / CF net_income_cf 분리 가능
2. DART와 동일한 인터페이스로 buildTimeseries + calcRatios 동작
3. L2 insight에서 사용하는 29개 snakeId 중 24개 이상 커버

방법:
1. EdgarMapper: standardAccounts.json + learnedSynonyms.json 로딩, stmt 기반 매핑
2. pivot: 003 로직 (selectStandalone, computeQ4) → DART 형식 시계열 dict 변환
3. EDGAR→DART alias 적용 (004에서 도출한 13개 + equity 수정)
4. extract + ratios는 DART 것을 그대로 사용 (인터페이스 동일)
5. AAPL/MSFT/NVDA로 매핑 + 피벗 + 비율 계산 통합 검증

결과:
  [Part 1: Revenue/Net Income 분기 검증 — 24/24 OK]
  AAPL FY2024: Revenue Q1~Q4 + Net Income Q1~Q4 모두 0.00%
  MSFT FY2024: Revenue Q1~Q4 + Net Income Q1~Q4 모두 0.00%
  NVDA FY2025: Revenue Q1~Q4 + Net Income Q1~Q4 모두 0.00%

  [Part 2: L2 커버리지 — 26/29 (90%)]
  미커버 3개 (US-GAAP 구조적 차이):
  - bonds: US-GAAP에 '사채' 개념 없음 (long_term_debt에 포함)
  - equity_nci: 3사 모두 NCI=0 (비지배지분 없는 기업)
  - issued_capital: US-GAAP은 common_stock + APIC 분리

  [Part 3: buildAnnual FY 합계 — 6/6 OK]
  AAPL FY2024: Revenue 391.035B, NI 93.736B 정확 일치
  MSFT FY2024: Revenue 245.122B, NI 88.136B 정확 일치
  NVDA FY2025: Revenue 130.497B, NI 72.880B 정확 일치

  [Part 4: calcRatios — DART 인터페이스 완전 호환]
  NVDA 예시: ROE 175.1%, ROA 124.5%, Op Margin 56.2%, Debt Ratio 40.7%
  AAPL/MSFT: 진행 중 FY(partial year)가 마지막이라 일부 비율 N/A
  → 완료된 FY 기준으로 사용하면 정상 동작

  [Part 5: IS/CF net_income 분리 — 성공]
  STMT_OVERRIDES로 NetIncomeLoss를 IS→net_income, CF→net_income_cf로 분리
  AAPL: IS=84.544B, CF=84.544B (NCI=0이라 동일)

  [핵심 발견]
  1. commonTag 우선 필수: learnedSynonyms 오매핑(CapitalLeases→total_equity 등)이
     BS equity를 오염시킴 → commonTag 값으로 덮어쓰기 전략 적용
  2. partial year 문제: 진행 중 FY가 마지막에 위치 → getLatest가 불완전 데이터 선택
     → DART와 동일한 구조적 한계, 실무에서는 완료 FY 기준 사용
  3. EDGAR→DART alias 14개 + STMT_OVERRIDES 2개 = 16개 변환 규칙

결론:
  가설 1 채택: STMT_OVERRIDES로 IS/CF net_income 분리 성공
  가설 2 채택: DART와 동일한 buildTimeseries/buildAnnual/calcRatios 인터페이스 동작
  가설 3 채택: 26/29 (90%) L2 커버리지. 미커버 3개는 US-GAAP 구조적 차이

  패키지 배치 준비 완료. 핵심 구현 요소:
  1. EdgarMapper: commonTags(344) + learnedSynonyms(11,375) 병합, stmt 기반 매핑
  2. pivot: IS(standalone 직접) + CF(YTD deaccumulate) + BS + Q4 역산
  3. EDGAR→DART alias 14개 + STMT_OVERRIDES 2개
  4. commonTag 우선 전략 (오매핑 방어)
  5. _computeEquity: equity_including_nci - equity_nci = total_equity 역산

실험일: 2026-03-10
"""

import json
import sys
from pathlib import Path
from typing import Optional

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
    "total_equity": "equity_including_nci",
}

STMT_OVERRIDES: dict[tuple[str, str], str] = {
    ("NetIncomeLoss", "IS"): "net_income",
    ("NetIncomeLoss", "CF"): "net_income_cf",
}

TICKER_CIK = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
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


def _getEdgarDir() -> Path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from dartlab import config
    return Path(config.dataDir) / "edgarData"


class EdgarMapper:
    _tagMap: Optional[dict[str, str]] = None
    _stmtTagMap: Optional[dict[str, dict[str, str]]] = None
    _accounts: Optional[list[dict]] = None

    _commonTags: Optional[set[str]] = None

    @classmethod
    def _ensureLoaded(cls):
        if cls._tagMap is not None:
            return

        stdPath = EDDM_FINANCE_DIR / "standardAccounts.json"
        with open(stdPath, encoding="utf-8") as f:
            stdData = json.load(f)

        cls._accounts = stdData["accounts"]

        cls._stmtTagMap = {}
        cls._commonTags = set()
        commonTagMap = {}
        for acct in cls._accounts:
            sid = acct["snakeId"]
            stmt = acct["stmt"]
            for tag in acct.get("commonTags", []):
                commonTagMap[tag.lower()] = sid
                cls._commonTags.add(tag.lower())
                cls._stmtTagMap.setdefault(tag.lower(), {})[stmt] = sid

        learnedPath = EDDM_FINANCE_DIR / "learnedSynonyms.json"
        with open(learnedPath, encoding="utf-8") as f:
            learnedData = json.load(f)

        cls._tagMap = {}
        for tag, sid in learnedData.get("tagMappings", {}).items():
            cls._tagMap[tag.lower()] = sid

        for tag, sid in commonTagMap.items():
            cls._tagMap[tag.lower()] = sid

    @classmethod
    def isCommonTag(cls, tag: str) -> bool:
        cls._ensureLoaded()
        return tag.lower() in cls._commonTags

    @classmethod
    def map(cls, tag: str, stmtType: str = "") -> Optional[str]:
        cls._ensureLoaded()

        overrideKey = (tag, stmtType)
        if overrideKey in STMT_OVERRIDES:
            return STMT_OVERRIDES[overrideKey]

        tagLower = tag.lower()

        if stmtType and tagLower in cls._stmtTagMap:
            stmtMap = cls._stmtTagMap[tagLower]
            if stmtType in stmtMap:
                return stmtMap[stmtType]

        edgarSid = cls._tagMap.get(tagLower)
        if edgarSid is None:
            return None

        return EDGAR_TO_DART_ALIASES.get(edgarSid, edgarSid)

    @classmethod
    def mapToDart(cls, tag: str, stmtType: str = "") -> Optional[str]:
        sid = cls.map(tag, stmtType)
        if sid is None:
            return None
        return EDGAR_TO_DART_ALIASES.get(sid, sid)


def loadFacts(edgarDir: Path, cik: str) -> pl.DataFrame:
    path = edgarDir / "finance" / f"{cik}.parquet"
    df = pl.read_parquet(path)
    return df.filter(pl.col("namespace") == "us-gaap")


def _computeDurationDays(tagDf: pl.DataFrame) -> pl.DataFrame:
    return tagDf.with_columns(
        pl.when(
            pl.col("start").is_not_null() & pl.col("end").is_not_null()
        )
        .then((pl.col("end") - pl.col("start")).dt.total_days())
        .otherwise(pl.lit(None))
        .alias("duration_days")
    )


def _selectByLatestPeriod(df: pl.DataFrame) -> pl.DataFrame:
    if df.height == 0:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})

    hasEnd = df.filter(pl.col("end").is_not_null())
    if hasEnd.height > 0:
        return (
            hasEnd
            .sort(["end", "filed"], descending=[True, True])
            .group_by(["tag", "period"])
            .agg(pl.col("val").first().alias("val"))
        )

    return (
        df
        .sort("filed", descending=True)
        .group_by(["tag", "period"])
        .agg(pl.col("val").first().alias("val"))
    )


def _selectBS(tagDf: pl.DataFrame) -> pl.DataFrame:
    return _selectByLatestPeriod(tagDf)


def _selectFlowDirect(tagDf: pl.DataFrame) -> pl.DataFrame:
    tagDf = _computeDurationDays(tagDf)

    fyRows = tagDf.filter(pl.col("fp") == "FY")
    fyResult = _selectByLatestPeriod(fyRows)

    q1Rows = tagDf.filter(pl.col("fp") == "Q1")
    q1Result = _selectByLatestPeriod(q1Rows)

    q2q3Standalone = tagDf.filter(
        pl.col("fp").is_in(["Q2", "Q3"]) &
        pl.col("duration_days").is_not_null() &
        (pl.col("duration_days") <= 100)
    )
    q2q3Result = _selectByLatestPeriod(q2q3Standalone)

    parts = [df for df in [fyResult, q1Result, q2q3Result] if df.height > 0]
    result = pl.concat(parts) if parts else pl.DataFrame(
        schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64}
    )

    missingPeriods = _findMissingQuarters(tagDf, result)
    if missingPeriods.height > 0:
        ytdFallback = _ytdDeaccumulate(tagDf, missingPeriods)
        if ytdFallback.height > 0:
            result = pl.concat([result, ytdFallback])

    return result


def _selectFlowYTD(tagDf: pl.DataFrame) -> pl.DataFrame:
    tagDf = _computeDurationDays(tagDf)

    fyQ1 = tagDf.filter(pl.col("fp").is_in(["FY", "Q1"]))
    fyQ1Result = _selectByLatestPeriod(fyQ1)

    q2q3Ytd = tagDf.filter(
        pl.col("fp").is_in(["Q2", "Q3"]) &
        pl.col("duration_days").is_not_null() &
        (pl.col("duration_days") > 100)
    )

    q2q3Result = (
        q2q3Ytd
        .sort(["end", "filed"], descending=[True, True])
        .group_by(["tag", "fy", "fp"])
        .agg(pl.col("val").first().alias("ytd_val"))
    )

    deaccumulated = _deaccumulateCF(fyQ1Result, q2q3Result)
    return pl.concat([fyQ1Result, deaccumulated])


def _deaccumulateCF(
    fyQ1Result: pl.DataFrame,
    q2q3Ytd: pl.DataFrame,
) -> pl.DataFrame:
    rows = []
    q1Map = {}
    for row in fyQ1Result.iter_rows(named=True):
        period = row["period"]
        if period.endswith("-Q1"):
            q1Map[(row["tag"], period.split("-")[0])] = row["val"]

    ytdMap = {}
    for row in q2q3Ytd.iter_rows(named=True):
        key = (row["tag"], str(row["fy"]), row["fp"])
        ytdMap[key] = row["ytd_val"]

    for (tag, fy, fp), ytdVal in ytdMap.items():
        if fp == "Q2":
            q1Val = q1Map.get((tag, fy))
            if q1Val is not None and ytdVal is not None:
                rows.append({"tag": tag, "period": f"{fy}-Q2", "val": ytdVal - q1Val})
        elif fp == "Q3":
            q2YtdVal = ytdMap.get((tag, fy, "Q2"))
            if q2YtdVal is not None and ytdVal is not None:
                rows.append({"tag": tag, "period": f"{fy}-Q3", "val": ytdVal - q2YtdVal})

    if not rows:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})
    return pl.DataFrame(rows)


def _findMissingQuarters(tagDf: pl.DataFrame, result: pl.DataFrame) -> pl.DataFrame:
    allPeriods = tagDf.select("tag", "period").unique()
    existingPeriods = result.select("tag", "period").unique()
    missing = allPeriods.join(existingPeriods, on=["tag", "period"], how="anti")
    return missing.filter(pl.col("period").str.contains("Q[23]"))


def _ytdDeaccumulate(tagDf: pl.DataFrame, missingPeriods: pl.DataFrame) -> pl.DataFrame:
    tagDf = _computeDurationDays(tagDf) if "duration_days" not in tagDf.columns else tagDf

    ytdRows = tagDf.filter(
        pl.col("duration_days").is_not_null() &
        (pl.col("duration_days") > 100)
    )

    rows = []
    for mpRow in missingPeriods.iter_rows(named=True):
        tag, period = mpRow["tag"], mpRow["period"]
        fy, fp = period.split("-")

        candidates = ytdRows.filter(
            (pl.col("tag") == tag) &
            (pl.col("fy") == int(fy)) &
            (pl.col("fp") == fp)
        ).sort(["end", "filed"], descending=[True, True])

        if candidates.height == 0:
            continue

        ytdVal = candidates.row(0, named=True)["val"]

        if fp == "Q2":
            q1Rows = tagDf.filter(
                (pl.col("tag") == tag) &
                (pl.col("fy") == int(fy)) &
                (pl.col("fp") == "Q1")
            ).sort("filed", descending=True)
            if q1Rows.height > 0:
                q1Val = q1Rows.row(0, named=True)["val"]
                if q1Val is not None and ytdVal is not None:
                    rows.append({"tag": tag, "period": period, "val": ytdVal - q1Val})

        elif fp == "Q3":
            q2YtdRows = ytdRows.filter(
                (pl.col("tag") == tag) &
                (pl.col("fy") == int(fy)) &
                (pl.col("fp") == "Q2")
            ).sort(["end", "filed"], descending=[True, True])
            if q2YtdRows.height > 0:
                q2YtdVal = q2YtdRows.row(0, named=True)["val"]
                if q2YtdVal is not None and ytdVal is not None:
                    rows.append({"tag": tag, "period": period, "val": ytdVal - q2YtdVal})

    if not rows:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})
    return pl.DataFrame(rows)


def selectStandalone(df: pl.DataFrame, stmtType: str) -> pl.DataFrame:
    tagDf = df.filter(
        pl.col("frame").is_null() &
        pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"])
    )

    if tagDf.height == 0:
        return pl.DataFrame()

    tagDf = tagDf.with_columns(
        (pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period")
    )

    if stmtType == "BS":
        return _selectBS(tagDf)
    elif stmtType == "CF":
        return _selectFlowYTD(tagDf)
    else:
        return _selectFlowDirect(tagDf)


def pivotTimeseries(selected: pl.DataFrame) -> pl.DataFrame:
    if selected.height == 0:
        return pl.DataFrame()

    pivoted = selected.pivot(
        on="period",
        index="tag",
        values="val",
        aggregate_function="first",
    )

    periodCols = [c for c in pivoted.columns if c != "tag"]

    def sortKey(col: str) -> tuple:
        parts = col.split("-")
        if len(parts) == 2:
            fy = int(parts[0])
            fpOrder = {"Q1": 1, "Q2": 2, "Q3": 3, "FY": 5}
            return (fy, fpOrder.get(parts[1], 9))
        return (9999, 9)

    sortedCols = sorted(periodCols, key=sortKey)
    return pivoted.select(["tag"] + sortedCols)


def computeQ4(pivoted: pl.DataFrame, stmtType: str) -> pl.DataFrame:
    if stmtType == "BS":
        return pivoted

    periodCols = [c for c in pivoted.columns if c != "tag"]
    years = sorted({c.split("-")[0] for c in periodCols if "-" in c})

    newCols = {}
    for year in years:
        fyCol = f"{year}-FY"
        q1Col = f"{year}-Q1"
        q2Col = f"{year}-Q2"
        q3Col = f"{year}-Q3"
        q4Col = f"{year}-Q4"

        hasFy = fyCol in pivoted.columns
        hasQ1 = q1Col in pivoted.columns
        hasQ2 = q2Col in pivoted.columns
        hasQ3 = q3Col in pivoted.columns

        if hasFy and hasQ1 and hasQ2 and hasQ3:
            q4Vals = (
                pivoted[fyCol] - pivoted[q1Col] - pivoted[q2Col] - pivoted[q3Col]
            )
            newCols[q4Col] = q4Vals

    if not newCols:
        return pivoted

    for colName, colData in newCols.items():
        pivoted = pivoted.with_columns(colData.alias(colName))

    allCols = [c for c in pivoted.columns if c != "tag"]

    def sortKey(col: str) -> tuple:
        parts = col.split("-")
        if len(parts) == 2:
            fy = int(parts[0])
            fpOrder = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "FY": 5}
            return (fy, fpOrder.get(parts[1], 9))
        return (9999, 9)

    sortedCols = sorted(allCols, key=sortKey)
    return pivoted.select(["tag"] + sortedCols)


STMT_TAG_SETS = {
    "IS": None,
    "BS": None,
    "CF": None,
}


def _classifyTagsByStmt() -> dict[str, set[str]]:
    EdgarMapper._ensureLoaded()
    stmtTags: dict[str, set[str]] = {"IS": set(), "BS": set(), "CF": set()}
    for acct in EdgarMapper._accounts:
        stmt = acct["stmt"]
        if stmt in stmtTags:
            for tag in acct.get("commonTags", []):
                stmtTags[stmt].add(tag)
    return stmtTags


def buildTimeseries(
    edgarDir: Path,
    cik: str,
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    df = loadFacts(edgarDir, cik)
    if df.height == 0:
        return None

    allTags = df.select("tag").unique().to_series().to_list()

    stmtTags = _classifyTagsByStmt()

    tagToStmts: dict[str, set[str]] = {}
    for stmt, tags in stmtTags.items():
        for tag in tags:
            tagToStmts.setdefault(tag, set()).add(stmt)

    for tag in allTags:
        if tag not in tagToStmts:
            tagToStmts[tag] = {_guessStmt(tag)}

    stmtDfs = {}
    for stmt in ["IS", "BS", "CF"]:
        stmtTagList = [t for t, stmts in tagToStmts.items() if stmt in stmts]
        if not stmtTagList:
            continue
        stmtDf = df.filter(pl.col("tag").is_in(stmtTagList))
        if stmtDf.height > 0:
            stmtDfs[stmt] = stmtDf

    series: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}}
    allPeriods: set[str] = set()

    for stmt, stmtDf in stmtDfs.items():
        selected = selectStandalone(stmtDf, stmt)
        if selected.height == 0:
            continue

        pivoted = pivotTimeseries(selected)
        pivoted = computeQ4(pivoted, stmt)

        periodCols = [c for c in pivoted.columns if c != "tag"]
        for p in periodCols:
            if "-FY" not in p:
                allPeriods.add(p)

        sidSource: dict[str, dict[str, str]] = {}

        for row in pivoted.iter_rows(named=True):
            tag = row["tag"]
            dartSid = EdgarMapper.mapToDart(tag, stmt)
            if dartSid is None:
                continue

            isCommon = EdgarMapper.isCommonTag(tag)

            for p in periodCols:
                if "-FY" in p:
                    continue
                val = row.get(p)
                if val is not None:
                    if dartSid not in series[stmt]:
                        series[stmt][dartSid] = {}
                        sidSource[dartSid] = {}

                    prevSource = sidSource.get(dartSid, {}).get(p)
                    if prevSource is None:
                        series[stmt][dartSid][p] = val
                        sidSource.setdefault(dartSid, {})[p] = "common" if isCommon else "learned"
                    elif prevSource == "learned" and isCommon:
                        series[stmt][dartSid][p] = val
                        sidSource[dartSid][p] = "common"

    periods = _sortPeriods(allPeriods)
    nPeriods = len(periods)
    periodIdx = {p: i for i, p in enumerate(periods)}

    result: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}}
    for stmt in series:
        for sid, pMap in series[stmt].items():
            vals: list[Optional[float]] = [None] * nPeriods
            for p, v in pMap.items():
                idx = periodIdx.get(p)
                if idx is not None:
                    vals[idx] = v
            result[stmt][sid] = vals

    _computeEquity(result, periods)

    return result, periods


def _guessStmt(tag: str) -> str:
    tagLower = tag.lower()
    cfKeywords = [
        "cashflow", "cash_flow", "netcash", "payment", "proceeds",
        "repayment", "issuance", "capex", "dividend",
        "depreciation", "amortization", "stockcompensation",
    ]
    for kw in cfKeywords:
        if kw in tagLower:
            return "CF"

    bsKeywords = [
        "asset", "liabilit", "equity", "receivable", "payable",
        "inventory", "cash", "debt", "borrowing", "goodwill",
        "intangible", "property", "plant", "deferred",
    ]
    for kw in bsKeywords:
        if kw in tagLower:
            return "BS"

    return "IS"


def _sortPeriods(periods: set[str]) -> list[str]:
    def sortKey(p: str) -> tuple:
        parts = p.split("-")
        if len(parts) == 2:
            fy = int(parts[0])
            fpOrder = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
            return (fy, fpOrder.get(parts[1], 9))
        return (9999, 9)

    return sorted(periods, key=sortKey)


def _computeEquity(
    result: dict[str, dict[str, list[Optional[float]]]],
    periods: list[str],
) -> None:
    nci = result["BS"].get("equity_nci")
    total = result["BS"].get("equity_including_nci")

    if total is not None and nci is not None:
        totalEquity = [None] * len(periods)
        for i in range(len(periods)):
            t = total[i]
            n = nci[i]
            if t is not None:
                totalEquity[i] = t - (n or 0)
        result["BS"]["total_equity"] = totalEquity
    elif total is not None:
        result["BS"]["total_equity"] = list(total)


def buildAnnual(
    edgarDir: Path,
    cik: str,
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    qResult = buildTimeseries(edgarDir, cik)
    if qResult is None:
        return None

    qSeries, qPeriods = qResult

    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(qPeriods):
        year = p.split("-")[0]
        yearSet.setdefault(year, []).append(i)

    years = sorted(yearSet.keys())
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    result: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}}

    for sjDiv in qSeries:
        for snakeId, vals in qSeries[sjDiv].items():
            annual: list[Optional[float]] = [None] * nYears

            for year, qIndices in yearSet.items():
                yIdx = yearIdx[year]

                if sjDiv == "BS":
                    lastIdx = max(qIndices)
                    annual[yIdx] = vals[lastIdx] if lastIdx < len(vals) else None
                else:
                    qVals = [vals[qi] for qi in qIndices if qi < len(vals) and vals[qi] is not None]
                    annual[yIdx] = sum(qVals) if qVals else None

            result[sjDiv][snakeId] = annual

    return result, years


def _verifyTimeseries(edgarDir: Path):
    print(f"\n{'='*70}")
    print(f"  Part 1: buildTimeseries 검증")
    print(f"{'='*70}")

    VERIFY = {
        "AAPL": {
            "cik": TICKER_CIK["AAPL"],
            "revenue": {
                "2024-Q1": 119_575_000_000,
                "2024-Q2": 90_753_000_000,
                "2024-Q3": 85_777_000_000,
                "2024-Q4": 94_930_000_000,
            },
            "net_income": {
                "2024-Q1": 33_916_000_000,
                "2024-Q2": 23_636_000_000,
                "2024-Q3": 21_448_000_000,
                "2024-Q4": 14_736_000_000,
            },
        },
        "MSFT": {
            "cik": TICKER_CIK["MSFT"],
            "revenue": {
                "2024-Q1": 56_517_000_000,
                "2024-Q2": 62_020_000_000,
                "2024-Q3": 61_858_000_000,
                "2024-Q4": 64_727_000_000,
            },
            "net_income": {
                "2024-Q1": 22_291_000_000,
                "2024-Q2": 21_870_000_000,
                "2024-Q3": 21_939_000_000,
                "2024-Q4": 22_036_000_000,
            },
        },
        "NVDA": {
            "cik": TICKER_CIK["NVDA"],
            "revenue": {
                "2025-Q1": 26_044_000_000,
                "2025-Q2": 30_040_000_000,
                "2025-Q3": 35_082_000_000,
                "2025-Q4": 39_331_000_000,
            },
            "net_income": {
                "2025-Q1": 14_881_000_000,
                "2025-Q2": 16_599_000_000,
                "2025-Q3": 19_309_000_000,
                "2025-Q4": 22_091_000_000,
            },
        },
    }

    for ticker, data in VERIFY.items():
        print(f"\n  --- {ticker} ---")
        result = buildTimeseries(edgarDir, data["cik"])
        if result is None:
            print(f"  ERROR: buildTimeseries returned None")
            continue

        series, periods = result

        for metric in ["revenue", "net_income"]:
            official = data[metric]
            vals = series.get("IS", {}).get(metric)
            if vals is None:
                print(f"  {metric}: NOT FOUND in series")
                continue

            periodIdx = {p: i for i, p in enumerate(periods)}
            print(f"  {metric}:")
            for period, officialVal in sorted(official.items()):
                idx = periodIdx.get(period)
                extracted = vals[idx] if idx is not None and idx < len(vals) else None
                if extracted is not None:
                    diff = (extracted - officialVal) / officialVal * 100
                    status = "OK" if abs(diff) < 0.01 else f"DIFF {diff:+.2f}%"
                    print(f"    {period}: {extracted/1e9:.3f}B vs {officialVal/1e9:.3f}B → {status}")
                else:
                    print(f"    {period}: N/A vs {officialVal/1e9:.3f}B → MISSING")


def _verifyL2Coverage(edgarDir: Path):
    print(f"\n{'='*70}")
    print(f"  Part 2: L2 snakeId 커버리지 (3사)")
    print(f"{'='*70}")

    for ticker, cik in TICKER_CIK.items():
        result = buildTimeseries(edgarDir, cik)
        if result is None:
            print(f"  {ticker}: buildTimeseries returned None")
            continue

        series, periods = result

        allSids = set()
        for stmt in series:
            allSids.update(series[stmt].keys())

        covered = allSids & L2_INSIGHT_USED
        missing = L2_INSIGHT_USED - allSids

        print(f"\n  {ticker}: {len(covered)}/{len(L2_INSIGHT_USED)} ({len(covered)/len(L2_INSIGHT_USED)*100:.0f}%)")
        if missing:
            print(f"  미커버: {sorted(missing)}")


def _verifyAnnual(edgarDir: Path):
    print(f"\n{'='*70}")
    print(f"  Part 3: buildAnnual 검증")
    print(f"{'='*70}")

    VERIFY_ANNUAL = {
        "AAPL": {"cik": TICKER_CIK["AAPL"], "fy": "2024", "revFY": 391_035_000_000, "niFY": 93_736_000_000},
        "MSFT": {"cik": TICKER_CIK["MSFT"], "fy": "2024", "revFY": 245_122_000_000, "niFY": 88_136_000_000},
        "NVDA": {"cik": TICKER_CIK["NVDA"], "fy": "2025", "revFY": 130_497_000_000, "niFY": 72_880_000_000},
    }

    for ticker, data in VERIFY_ANNUAL.items():
        result = buildAnnual(edgarDir, data["cik"])
        if result is None:
            print(f"  {ticker}: buildAnnual returned None")
            continue

        series, years = result
        fy = data["fy"]
        yearIdx = years.index(fy) if fy in years else None

        if yearIdx is None:
            print(f"  {ticker}: year {fy} not in years={years}")
            continue

        rev = series.get("IS", {}).get("revenue", [None] * len(years))[yearIdx]
        ni = series.get("IS", {}).get("net_income", [None] * len(years))[yearIdx]

        revDiff = (rev - data["revFY"]) / data["revFY"] * 100 if rev else None
        niDiff = (ni - data["niFY"]) / data["niFY"] * 100 if ni else None

        print(f"  {ticker} FY{fy}:")
        if rev is not None:
            revStatus = "OK" if revDiff is not None and abs(revDiff) < 0.01 else f"{revDiff:+.2f}%" if revDiff is not None else "N/A"
            print(f"    Revenue: {rev/1e9:.3f}B vs {data['revFY']/1e9:.3f}B → {revStatus}")
        else:
            print(f"    Revenue: N/A vs {data['revFY']/1e9:.3f}B")
        if ni is not None:
            niStatus = "OK" if niDiff is not None and abs(niDiff) < 0.01 else f"{niDiff:+.2f}%" if niDiff is not None else "N/A"
            print(f"    Net Inc: {ni/1e9:.3f}B vs {data['niFY']/1e9:.3f}B → {niStatus}")
        else:
            print(f"    Net Inc: N/A vs {data['niFY']/1e9:.3f}B")


def _verifyRatios(edgarDir: Path):
    print(f"\n{'='*70}")
    print(f"  Part 4: calcRatios 검증 (연간 데이터 + DART 인터페이스 호환)")
    print(f"{'='*70}")

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from dartlab.engines.company.dart.finance.ratios import calcRatios
    from dartlab.engines.company.dart.finance.extract import getLatest

    for ticker, cik in TICKER_CIK.items():
        aResult = buildAnnual(edgarDir, cik)
        if aResult is None:
            print(f"  {ticker}: buildAnnual returned None")
            continue

        series, years = aResult
        ratios = calcRatios(series)

        print(f"\n  {ticker} ({len(years)} years: {years[0]}~{years[-1]})")
        print(f"    Revenue (latest): {getLatest(series, 'IS', 'revenue')/1e9:.1f}B" if getLatest(series, "IS", "revenue") else "    Revenue: N/A")
        print(f"    Net Income (latest): {getLatest(series, 'IS', 'net_income')/1e9:.1f}B" if getLatest(series, "IS", "net_income") else "    Net Income: N/A")
        print(f"    OpCF (latest): {getLatest(series, 'CF', 'operating_cashflow')/1e9:.1f}B" if getLatest(series, "CF", "operating_cashflow") else "    OpCF: N/A")
        print(f"    Total Assets: {ratios.totalAssets/1e9:.1f}B" if ratios.totalAssets else "    Total Assets: N/A")
        print(f"    Total Equity: {ratios.totalEquity/1e9:.1f}B" if ratios.totalEquity else "    Total Equity: N/A")
        print(f"    ROE: {ratios.roe:.1f}%" if ratios.roe is not None else "    ROE: N/A")
        print(f"    ROA: {ratios.roa:.1f}%" if ratios.roa is not None else "    ROA: N/A")
        print(f"    Op Margin: {ratios.operatingMargin:.1f}%" if ratios.operatingMargin is not None else "    Op Margin: N/A")
        print(f"    Net Margin: {ratios.netMargin:.1f}%" if ratios.netMargin is not None else "    Net Margin: N/A")
        print(f"    Debt Ratio: {ratios.debtRatio:.1f}%" if ratios.debtRatio is not None else "    Debt Ratio: N/A")
        print(f"    Current Ratio: {ratios.currentRatio:.1f}%" if ratios.currentRatio is not None else "    Current Ratio: N/A")
        print(f"    FCF: {ratios.fcf/1e9:.1f}B" if ratios.fcf is not None else "    FCF: N/A")
        print(f"    Rev Growth 3Y: {ratios.revenueGrowth3Y:.1f}%" if ratios.revenueGrowth3Y is not None else "    Rev Growth 3Y: N/A")
        print(f"    --- snakeId 목록 ({len(series['BS'])} BS, {len(series['IS'])} IS, {len(series['CF'])} CF) ---")


def _verifySeries(edgarDir: Path):
    print(f"\n{'='*70}")
    print(f"  Part 5: IS/CF net_income 분리 검증")
    print(f"{'='*70}")

    for ticker, cik in TICKER_CIK.items():
        result = buildAnnual(edgarDir, cik)
        if result is None:
            print(f"  {ticker}: buildAnnual returned None")
            continue

        series, years = result

        isNi = series.get("IS", {}).get("net_income")
        cfNi = series.get("CF", {}).get("net_income_cf")

        lastIdx = len(years) - 1
        print(f"\n  {ticker} ({years[-1]}):")
        if isNi and isNi[lastIdx] is not None:
            print(f"    IS net_income: {isNi[lastIdx]/1e9:.3f}B")
        else:
            print(f"    IS net_income: {'없음' if not isNi else 'None'}")
        if cfNi and cfNi[lastIdx] is not None:
            print(f"    CF net_income_cf: {cfNi[lastIdx]/1e9:.3f}B")
        else:
            print(f"    CF net_income_cf: {'없음' if not cfNi else 'None'}")

        if isNi and cfNi and isNi[lastIdx] and cfNi[lastIdx]:
            print(f"    동일값? {isNi[lastIdx] == cfNi[lastIdx]}")


def main():
    edgarDir = _getEdgarDir()
    print(f"[EDGAR] 데이터 경로: {edgarDir}")

    _verifyTimeseries(edgarDir)
    _verifyL2Coverage(edgarDir)
    _verifyAnnual(edgarDir)
    _verifyRatios(edgarDir)
    _verifySeries(edgarDir)


if __name__ == "__main__":
    main()
