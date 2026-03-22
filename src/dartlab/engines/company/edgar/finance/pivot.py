"""EDGAR companyfacts → 분기별/연도별 시계열 dict 피벗.

정규화 전략:
- IS: duration ≤100일 standalone 직접 선택, 없으면 YTD deaccumulate
- CF: 항상 YTD deaccumulate (Q2=Q2_YTD-Q1, Q3=Q3_YTD-Q2_YTD)
- BS: end 내림차순 최신값 선택
- Q4 = FY - Q1 - Q2 - Q3 역산 (BS 제외)

결과 구조 (DART와 동일)::

    {
        "BS":  {"total_assets": [v1, v2, ...], ...},
        "IS":  {"sales": [...], ...},
        "CF":  {"operating_cashflow": [...], ...},
        "CI":  {"comprehensive_income": [...], ...},
    }

periods = ["2020-Q1", "2020-Q2", ..., "2024-Q4"]
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import polars as pl

from dartlab.engines.common.finance.ordering import sortSeries
from dartlab.engines.common.finance.period import extractYear, formatPeriod, parsePeriod
from dartlab.engines.company.edgar.finance.mapper import EdgarMapper


def _getEdgarDir() -> Path:
    from dartlab.core.dataLoader import _dataDir

    return _dataDir("edgar")


def buildTimeseries(
    cik: str,
    *,
    edgarDir: Path | None = None,
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """EDGAR companyfacts → 분기별 standalone 시계열.

    Args:
        cik: SEC CIK 번호 (예: "0000320193").
        edgarDir: EDGAR 데이터 디렉토리 (None이면 config 기본값).

    Returns:
        (series, periods) 또는 None.
        series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}, "CI": {...}}
        periods = ["2020-Q1", "2020-Q2", ..., "2024-Q4"]
    """
    if edgarDir is None:
        edgarDir = _getEdgarDir()
    df = _loadFacts(edgarDir, cik)
    if df is None or df.height == 0:
        return None

    stmtTags = EdgarMapper.classifyTagsByStmt()

    allTags = df.select("tag").unique().to_series().to_list()
    tagToStmts: dict[str, set[str]] = {}
    for stmt, tags in stmtTags.items():
        for tag in tags:
            tagToStmts.setdefault(tag, set()).add(stmt)

    for tag in allTags:
        if tag not in tagToStmts:
            tagToStmts[tag] = {_guessStmt(tag)}

    stmtDfs: dict[str, pl.DataFrame] = {}
    for stmt in ["IS", "BS", "CF", "CI"]:
        stmtTagList = [t for t, stmts in tagToStmts.items() if stmt in stmts]
        if not stmtTagList:
            continue
        stmtDf = df.filter(pl.col("tag").is_in(stmtTagList))
        if stmtDf.height > 0:
            stmtDfs[stmt] = stmtDf

    series: dict[str, dict[str, dict[str, float]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}
    sidSource: dict[str, dict[str, dict[str, str]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}
    allPeriods: set[str] = set()

    for stmt, stmtDf in stmtDfs.items():
        selected = _selectStandalone(stmtDf, stmt)
        if selected.height == 0:
            continue

        pivoted = _pivotTimeseries(selected)
        pivoted = _computeQ4(pivoted, stmt)

        periodCols = [c for c in pivoted.columns if c != "tag"]

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
                    allPeriods.add(p)
                    if dartSid not in series[stmt]:
                        series[stmt][dartSid] = {}
                        sidSource[stmt][dartSid] = {}

                    prevSource = sidSource[stmt].get(dartSid, {}).get(p)
                    if prevSource is None:
                        series[stmt][dartSid][p] = val
                        sidSource[stmt].setdefault(dartSid, {})[p] = "common" if isCommon else "learned"
                    elif prevSource == "learned" and isCommon:
                        series[stmt][dartSid][p] = val
                        sidSource[stmt][dartSid][p] = "common"

    periods = _sortPeriods(allPeriods)
    nPeriods = len(periods)
    periodIdx = {p: i for i, p in enumerate(periods)}

    result: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}
    for stmt in series:
        for sid, pMap in series[stmt].items():
            vals: list[Optional[float]] = [None] * nPeriods
            for p, v in pMap.items():
                idx = periodIdx.get(p)
                if idx is not None:
                    vals[idx] = v
            result[stmt][sid] = vals

    _computeEquity(result, periods)
    _computeDerived(result, periods)
    sortSeries(result)

    return result, periods


def buildAnnual(
    cik: str,
    *,
    edgarDir: Path | None = None,
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """EDGAR companyfacts → 연도별 시계열.

    IS/CF: 해당 연도 분기별 standalone 합산.
    BS: 해당 연도 마지막 분기 시점잔액.

    Args:
        cik: SEC CIK 번호.
        edgarDir: EDGAR 데이터 디렉토리 (None이면 config 기본값).

    Returns:
        (series, years) 또는 None.
    """
    qResult = buildTimeseries(cik, edgarDir=edgarDir)
    if qResult is None:
        return None

    qSeries, qPeriods = qResult

    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(qPeriods):
        year = extractYear(p)
        yearSet.setdefault(year, []).append(i)

    years = sorted(yearSet.keys())
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    result: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}

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
                    if len(qIndices) < 4:
                        annual[yIdx] = None
                    else:
                        annual[yIdx] = sum(qVals) if qVals else None

            result[sjDiv][snakeId] = annual

    return result, years


def _loadFacts(edgarDir: Path, cik: str) -> Optional[pl.DataFrame]:
    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        path = _autoDownloadEdgarFinance(cik, path)
        if path is None:
            return None
    df = pl.read_parquet(path)
    return df.filter(pl.col("namespace") == "us-gaap")


def _autoDownloadEdgarFinance(cik: str, dest: Path) -> Optional[Path]:
    """SEC EDGAR companyfacts API에서 재무 데이터를 자동 다운로드."""
    from urllib.error import URLError

    print(f"[dartlab] {cik} (SEC EDGAR 재무 데이터) 로컬에 없음 → SEC API에서 다운로드 중...")
    try:
        from dartlab.engines.company.edgar.openapi.facts import (
            companyFactsToRows,
            getCompanyFactsJson,
        )

        payload = getCompanyFactsJson(cik)
        df = companyFactsToRows(payload)
        if df.is_empty():
            print(f"[dartlab] {cik} SEC API 응답이 비어있음 (데이터 없음)")
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(dest)
        print(f"[dartlab] 저장 완료: {dest}")
        return dest
    except (URLError, OSError, RuntimeError) as e:
        print(f"[dartlab] {cik} SEC API 다운로드 실패: {e}")
        return None


def _guessStmt(tag: str) -> str:
    tagLower = tag.lower()
    cfKeywords = [
        "cashflow",
        "cash_flow",
        "netcash",
        "payment",
        "proceeds",
        "repayment",
        "issuance",
        "capex",
        "dividend",
        "depreciation",
        "amortization",
        "stockcompensation",
    ]
    for kw in cfKeywords:
        if kw in tagLower:
            return "CF"

    bsKeywords = [
        "asset",
        "liabilit",
        "equity",
        "receivable",
        "payable",
        "inventory",
        "cash",
        "debt",
        "borrowing",
        "goodwill",
        "intangible",
        "property",
        "plant",
        "deferred",
    ]
    for kw in bsKeywords:
        if kw in tagLower:
            return "BS"

    return "IS"


def _selectStandalone(df: pl.DataFrame, stmtType: str) -> pl.DataFrame:
    if stmtType == "BS":
        tagDf = df.filter(pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]))
    else:
        tagDf = df.filter(pl.col("frame").is_null() & pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]))

    if tagDf.height == 0:
        return pl.DataFrame()

    tagDf = tagDf.with_columns((pl.col("fy").cast(pl.Utf8) + "-" + pl.col("fp")).alias("period"))

    if stmtType == "BS":
        return _selectBS(tagDf)
    elif stmtType == "CF":
        return _selectFlowYTD(tagDf)
    else:
        return _selectFlowDirect(tagDf)


def _selectBS(tagDf: pl.DataFrame) -> pl.DataFrame:
    """BS 시점잔액 선택.

    각 (tag, period)에서 가장 최근 end date의 값을 선택한다.
    SEC filing에서 Q1~Q3은 당기 시점잔액(frame 있음)과
    비교재무제표(frame 없음, 전년도 FY end)가 공존하는데,
    최대 end date가 당기 시점잔액이다.
    """
    if tagDf.height == 0:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})

    hasEnd = tagDf.filter(pl.col("end").is_not_null())
    if hasEnd.height == 0:
        return _selectByLatestPeriod(tagDf)

    return (
        hasEnd.sort(["end", "filed"], descending=[True, True])
        .group_by(["tag", "period"])
        .agg(pl.col("val").first().alias("val"))
    )


def _selectByLatestPeriod(df: pl.DataFrame) -> pl.DataFrame:
    if df.height == 0:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})

    hasEnd = df.filter(pl.col("end").is_not_null())
    if hasEnd.height > 0:
        return (
            hasEnd.sort(["end", "filed"], descending=[True, True])
            .group_by(["tag", "period"])
            .agg(pl.col("val").first().alias("val"))
        )

    return df.sort("filed", descending=True).group_by(["tag", "period"]).agg(pl.col("val").first().alias("val"))


def _computeDurationDays(tagDf: pl.DataFrame) -> pl.DataFrame:
    return tagDf.with_columns(
        pl.when(pl.col("start").is_not_null() & pl.col("end").is_not_null())
        .then((pl.col("end") - pl.col("start")).dt.total_days())
        .otherwise(pl.lit(None))
        .alias("duration_days")
    )


def _selectFlowDirect(tagDf: pl.DataFrame) -> pl.DataFrame:
    tagDf = _computeDurationDays(tagDf)

    fyRows = tagDf.filter(pl.col("fp") == "FY")
    fyResult = _selectByLatestPeriod(fyRows)

    q1Rows = tagDf.filter(pl.col("fp") == "Q1")
    q1Result = _selectByLatestPeriod(q1Rows)

    q2q3Standalone = tagDf.filter(
        pl.col("fp").is_in(["Q2", "Q3"]) & pl.col("duration_days").is_not_null() & (pl.col("duration_days") <= 100)
    )
    q2q3Result = _selectByLatestPeriod(q2q3Standalone)

    parts = [df for df in [fyResult, q1Result, q2q3Result] if df.height > 0]
    result = pl.concat(parts) if parts else pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})

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
        pl.col("fp").is_in(["Q2", "Q3"]) & pl.col("duration_days").is_not_null() & (pl.col("duration_days") > 100)
    )

    q2q3Result = (
        q2q3Ytd.sort(["end", "filed"], descending=[True, True])
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
    q1Map: dict[tuple[str, str], float] = {}
    for row in fyQ1Result.iter_rows(named=True):
        period = row["period"]
        if period.endswith("-Q1"):
            q1Map[(row["tag"], extractYear(period))] = row["val"]

    ytdMap: dict[tuple[str, str, str], float] = {}
    for row in q2q3Ytd.iter_rows(named=True):
        key = (row["tag"], str(row["fy"]), row["fp"])
        ytdMap[key] = row["ytd_val"]

    for (tag, fy, fp), ytdVal in ytdMap.items():
        if fp == "Q2":
            q1Val = q1Map.get((tag, fy))
            if q1Val is not None and ytdVal is not None:
                rows.append({"tag": tag, "period": formatPeriod(fy, 2), "val": ytdVal - q1Val})
        elif fp == "Q3":
            q2YtdVal = ytdMap.get((tag, fy, "Q2"))
            if q2YtdVal is not None and ytdVal is not None:
                rows.append({"tag": tag, "period": formatPeriod(fy, 3), "val": ytdVal - q2YtdVal})

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

    ytdRows = tagDf.filter(pl.col("duration_days").is_not_null() & (pl.col("duration_days") > 100))

    rows = []
    for mpRow in missingPeriods.iter_rows(named=True):
        tag, period = mpRow["tag"], mpRow["period"]
        fy = extractYear(period)
        fp = period.split("-")[1]

        candidates = ytdRows.filter((pl.col("tag") == tag) & (pl.col("fy") == int(fy)) & (pl.col("fp") == fp)).sort(
            ["end", "filed"], descending=[True, True]
        )

        if candidates.height == 0:
            continue

        ytdVal = candidates.row(0, named=True)["val"]

        if fp == "Q2":
            q1Rows = tagDf.filter((pl.col("tag") == tag) & (pl.col("fy") == int(fy)) & (pl.col("fp") == "Q1")).sort(
                "filed", descending=True
            )
            if q1Rows.height > 0:
                q1Val = q1Rows.row(0, named=True)["val"]
                if q1Val is not None and ytdVal is not None:
                    rows.append({"tag": tag, "period": period, "val": ytdVal - q1Val})

        elif fp == "Q3":
            q2YtdRows = ytdRows.filter(
                (pl.col("tag") == tag) & (pl.col("fy") == int(fy)) & (pl.col("fp") == "Q2")
            ).sort(["end", "filed"], descending=[True, True])
            if q2YtdRows.height > 0:
                q2YtdVal = q2YtdRows.row(0, named=True)["val"]
                if q2YtdVal is not None and ytdVal is not None:
                    rows.append({"tag": tag, "period": period, "val": ytdVal - q2YtdVal})

    if not rows:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})
    return pl.DataFrame(rows)


def _pivotTimeseries(selected: pl.DataFrame) -> pl.DataFrame:
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


def _computeQ4(pivoted: pl.DataFrame, stmtType: str) -> pl.DataFrame:
    periodCols = [c for c in pivoted.columns if c != "tag"]
    years = sorted({extractYear(c) for c in periodCols if "-" in c})

    newCols = {}
    for year in years:
        fyCol = f"{year}-FY"
        q4Col = formatPeriod(year, 4)

        if stmtType == "BS":
            if fyCol in pivoted.columns and q4Col not in pivoted.columns:
                newCols[q4Col] = pivoted[fyCol]
        else:
            q1Col = formatPeriod(year, 1)
            q2Col = formatPeriod(year, 2)
            q3Col = formatPeriod(year, 3)
            if all(c in pivoted.columns for c in [fyCol, q1Col, q2Col, q3Col]):
                newCols[q4Col] = pivoted[fyCol] - pivoted[q1Col] - pivoted[q2Col] - pivoted[q3Col]

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


def _sortPeriods(periods: set[str]) -> list[str]:
    def sortKey(p: str) -> tuple:
        try:
            year, q = parsePeriod(p)
            return (int(year), q)
        except (ValueError, IndexError):
            return (9999, 9)

    return sorted(periods, key=sortKey)


def _computeEquity(
    result: dict[str, dict[str, list[Optional[float]]]],
    periods: list[str],
) -> None:
    nci = result["BS"].get("noncontrolling_interests_equity")
    eqNci = result["BS"].get("total_stockholders_equity")
    teq = result["BS"].get("owners_of_parent_equity")
    redeemNci = result["BS"].get("redeemable_noncontrolling_interest")
    n = len(periods)

    if eqNci is None and teq is not None:
        eqNci = [None] * n
        result["BS"]["total_stockholders_equity"] = eqNci

    if teq is None and eqNci is not None:
        teq = [None] * n
        result["BS"]["owners_of_parent_equity"] = teq

    if eqNci is not None and teq is not None:
        for i in range(n):
            nciVal = (nci[i] or 0) if nci else 0
            if eqNci[i] is None and teq[i] is not None:
                eqNci[i] = teq[i] + nciVal
            if teq[i] is None and eqNci[i] is not None:
                teq[i] = eqNci[i] - nciVal

    assets = result["BS"].get("total_assets")
    if eqNci is not None and redeemNci is not None:
        for i in range(n):
            if eqNci[i] is not None and redeemNci[i] is not None:
                merged = eqNci[i] + redeemNci[i]
                if assets and assets[i] is not None and merged > assets[i]:
                    continue
                eqNci[i] = merged


_DERIVED_FORMULAS = [
    ("BS", "total_liabilities", "total_assets", "total_stockholders_equity", "subtract"),
    ("BS", "total_liabilities", "current_liabilities", "noncurrent_liabilities", "add"),
    ("IS", "gross_profit", "sales", "cost_of_sales", "subtract"),
    ("BS", "noncurrent_assets", "total_assets", "current_assets", "subtract"),
    ("BS", "noncurrent_liabilities", "total_liabilities", "current_liabilities", "subtract"),
]


def _computeDerived(
    result: dict[str, dict[str, list[Optional[float]]]],
    periods: list[str],
) -> None:
    n = len(periods)
    for stmt, target, srcA, srcB, op in _DERIVED_FORMULAS:
        existing = result[stmt].get(target)
        aVals = result[stmt].get(srcA)
        bVals = result[stmt].get(srcB)
        if aVals is None or bVals is None:
            continue

        derived = [None] * n
        filled = False
        for i in range(n):
            if existing is not None and existing[i] is not None:
                continue
            a = aVals[i]
            b = bVals[i]
            if a is None or b is None:
                continue
            derived[i] = (a + b) if op == "add" else (a - b)
            filled = True

        if not filled:
            continue

        if existing is None:
            result[stmt][target] = derived
        else:
            for i in range(n):
                if existing[i] is None and derived[i] is not None:
                    existing[i] = derived[i]


# ── SCE (자본변동표) ─────────────────────────────────────────────

# BS equity 컴포넌트 → SCE cause 매핑
_EQUITY_COMPONENTS: list[tuple[str, str]] = [
    ("common_stock", "Common Stock"),
    ("additional_paid_in_capital", "Additional Paid-in Capital"),
    ("retained_earnings", "Retained Earnings"),
    ("treasury_stock", "Treasury Stock"),
    ("accumulated_other_comprehensive_income", "Accumulated OCI"),
    ("noncontrolling_interests_equity", "Noncontrolling Interest"),
    ("owners_of_parent_equity", "Total Parent Equity"),
    ("total_stockholders_equity", "Total Equity"),
]

# CF equity 거래 → SCE 참고 항목
_EQUITY_TRANSACTIONS: list[tuple[str, str]] = [
    ("dividends_paid", "Dividends Paid"),
    ("stock_repurchase", "Share Repurchase"),
    ("stock_issuance", "Share Issuance"),
    ("stock_compensation", "Stock-Based Compensation"),
]


def buildSce(
    cik: str,
    *,
    edgarDir: Path | None = None,
) -> pl.DataFrame | None:
    """BS equity 컴포넌트 연간 변화 + CF equity 거래로 SCE 구성.

    Returns:
        DataFrame with columns: component, label, {year columns...}
        각 셀은 해당 연도의 변화량 (당기말 - 전기말). 첫 연도는 None.
    """
    annual = buildAnnual(cik, edgarDir=edgarDir)
    if annual is None:
        return None

    series, years = annual
    bs = series.get("BS", {})
    cf = series.get("CF", {})
    isStmt = series.get("IS", {})

    rows: list[dict] = []
    nYears = len(years)

    # 1. BS equity 컴포넌트 연간 변화량
    for snakeId, label in _EQUITY_COMPONENTS:
        vals = bs.get(snakeId)
        if vals is None:
            continue
        hasData = False
        row: dict = {"component": snakeId, "label": label}
        for i, year in enumerate(years):
            if i == 0:
                row[str(year)] = None
            else:
                prev = vals[i - 1]
                curr = vals[i]
                if prev is not None and curr is not None:
                    row[str(year)] = curr - prev
                    hasData = True
                else:
                    row[str(year)] = None
        if hasData:
            rows.append(row)

    # 2. Net Income (IS)
    netIncome = isStmt.get("net_profit") or isStmt.get("net_income")
    if netIncome is not None:
        row = {"component": "net_income", "label": "Net Income"}
        hasData = False
        for i, year in enumerate(years):
            val = netIncome[i]
            row[str(year)] = val
            if val is not None:
                hasData = True
        if hasData:
            rows.append(row)

    # 3. CF equity 거래
    for snakeId, label in _EQUITY_TRANSACTIONS:
        vals = cf.get(snakeId)
        if vals is None:
            continue
        hasData = False
        row = {"component": snakeId, "label": label}
        for i, year in enumerate(years):
            val = vals[i]
            row[str(year)] = val
            if val is not None:
                hasData = True
        if hasData:
            rows.append(row)

    # 4. OCI (CI statement)
    ci = series.get("CI", {})
    oci = ci.get("other_comprehensive_income") or ci.get("total_other_comprehensive_income")
    if oci is not None:
        row = {"component": "other_comprehensive_income", "label": "Other Comprehensive Income"}
        hasData = False
        for i, year in enumerate(years):
            val = oci[i]
            row[str(year)] = val
            if val is not None:
                hasData = True
        if hasData:
            rows.append(row)

    if not rows:
        return None

    df = pl.DataFrame(rows)
    # 기간 컬럼 역순 정렬 (최신 먼저)
    metaCols = ["component", "label"]
    periodCols = [c for c in df.columns if c not in metaCols]
    periodCols.sort(reverse=True)
    return df.select(metaCols + periodCols)
