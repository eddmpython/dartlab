"""edgar pivot 후처리 — pivot.py 분할 (규칙 3 LoC).

_pivotTimeseries / _computeQ4 / _sanitizeQ4 / _sortPeriods / _computeEquity /
_computeDerived / buildSce / getSharesOutstanding — XBRL fact long → wide pivot
이후의 Q4 역산, equity 시계열, SCE, 발행주식수 헬퍼.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import polars as pl

from dartlab.core.utils.ordering import sortSeries
from dartlab.core.utils.period import extractYear, formatPeriod, parsePeriod
from dartlab.providers.edgar.finance.mapper import EdgarMapper


def _calendarizePeriodColumns(pivoted: pl.DataFrame, fiscalToCalendar: dict[str, str]) -> pl.DataFrame:
    """Fiscal period 열을 한 번에 calendar period 열로 변환한다.

    순차 ``rename``은 목표 이름이 아직 원본 열로 존재할 때 변환을 건너뛴다.
    예를 들어 AAPL의 ``2024-Q1 -> 2023-Q4``는 ``2023-Q4`` 원본 열 때문에
    실패한다. select alias는 모든 열 이름을 동시에 바꾼다.

    결산월 전환으로 여러 fiscal 열이 같은 calendar quarter를 가리키면 더
    최근 fiscal label의 non-null 값을 우선하고 나머지는 결손 보충에만 쓴다.
    """
    if pivoted.is_empty() or not fiscalToCalendar:
        return pivoted

    targetSources: dict[str, list[str]] = {}
    for source in pivoted.columns:
        if source == "tag":
            continue
        target = fiscalToCalendar.get(source, source)
        targetSources.setdefault(target, []).append(source)

    expressions: list[pl.Expr] = [pl.col("tag")]
    for target, sources in targetSources.items():
        ordered = sorted(sources, reverse=True)
        if len(ordered) == 1:
            expressions.append(pl.col(ordered[0]).alias(target))
        else:
            expressions.append(pl.coalesce([pl.col(source) for source in ordered]).alias(target))
    return pivoted.select(expressions)


def _pivotTimeseries(selected: pl.DataFrame) -> pl.DataFrame:
    if selected.height == 0:
        return pl.DataFrame()

    pivoted = selected.pivot(  # polars-streaming-unsupported: pivot
        on="period",
        index="tag",
        values="val",
        aggregate_function="first",
    )

    periodCols = [c for c in pivoted.columns if c != "tag"]

    def _sortKey(col: str) -> tuple:
        parts = col.split("-")
        if len(parts) == 2:
            fy = int(parts[0])
            fpOrder = {"Q1": 1, "Q2": 2, "Q3": 3, "FY": 5}
            return (fy, fpOrder.get(parts[1], 9))
        return (9999, 9)

    sortedCols = sorted(periodCols, key=_sortKey)
    return pivoted.select(["tag"] + sortedCols)


def _computeQ4(pivoted: pl.DataFrame, stmtType: str) -> pl.DataFrame:
    """Q4 = FY - Q1 - Q2 - Q3 역산. BS는 FY 복사."""
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
                q4Raw = pivoted[fyCol] - pivoted[q1Col] - pivoted[q2Col] - pivoted[q3Col]
                newCols[q4Col] = q4Raw

    if not newCols:
        return pivoted

    for colName, colData in newCols.items():
        pivoted = pivoted.with_columns(colData.alias(colName))

    # Q4 sanity check: revenue/sales 태그에서 음수 Q4 → None 처리
    pivoted = _sanitizeQ4(pivoted, years)

    allCols = [c for c in pivoted.columns if c != "tag"]

    def _sortKey(col: str) -> tuple:
        parts = col.split("-")
        if len(parts) == 2:
            fy = int(parts[0])
            fpOrder = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "FY": 5}
            return (fy, fpOrder.get(parts[1], 9))
        return (9999, 9)

    sortedCols = sorted(allCols, key=_sortKey)
    return pivoted.select(["tag"] + sortedCols)


def _sanitizeQ4(pivoted: pl.DataFrame, years: list[str]) -> pl.DataFrame:
    """역산된 Q4 sanity check — 같은 연도 Q1~Q3 합 대비 비정상 Q4 제거.

    조건: Q4 < 0이고 |Q4| > Q1~Q3 평균의 2배 → Q4=None (YTD 오염 가능성).
    revenue 계열 태그가 음수면 무조건 None.
    """
    _REVENUE_TAGS = EdgarMapper.getTagsForSnakeIds(["sales", "revenue"])

    tags = pivoted["tag"].to_list()

    for year in years:
        q4Col = formatPeriod(year, 4)
        if q4Col not in pivoted.columns:
            continue
        q1Col = formatPeriod(year, 1)
        q2Col = formatPeriod(year, 2)
        q3Col = formatPeriod(year, 3)

        q4Vals = pivoted[q4Col].to_list()
        hasQ1 = q1Col in pivoted.columns
        hasQ2 = q2Col in pivoted.columns
        hasQ3 = q3Col in pivoted.columns

        nullMask = []
        for i, (tag, q4) in enumerate(zip(tags, q4Vals)):
            shouldNull = False
            if q4 is not None and q4 < 0:
                # revenue 계열은 음수 Q4 무조건 제거
                if tag in _REVENUE_TAGS:
                    shouldNull = True
                else:
                    # 다른 태그: Q1~Q3 평균 대비 비정상 검사
                    qVals = []
                    if hasQ1:
                        v = pivoted[q1Col][i]
                        if v is not None:
                            qVals.append(abs(v))
                    if hasQ2:
                        v = pivoted[q2Col][i]
                        if v is not None:
                            qVals.append(abs(v))
                    if hasQ3:
                        v = pivoted[q3Col][i]
                        if v is not None:
                            qVals.append(abs(v))
                    if qVals:
                        avgQ = sum(qVals) / len(qVals)
                        if avgQ > 0 and abs(q4) > avgQ * 2:
                            shouldNull = True
            nullMask.append(shouldNull)

        if any(nullMask):
            newVals = [None if nullMask[i] else q4Vals[i] for i in range(len(q4Vals))]
            pivoted = pivoted.with_columns(pl.Series(q4Col, newVals))

    return pivoted


def _sortPeriods(periods: set[str]) -> list[str]:
    def _sortKey(p: str) -> tuple:
        try:
            year, q = parsePeriod(p)
            return (int(year), q)
        except (ValueError, IndexError):
            return (9999, 9)

    return sorted(periods, key=_sortKey)


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
                if eqNci[i] != 0 and abs(merged) > abs(eqNci[i]) * 2:
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

    Args:
        cik: SEC CIK 번호.
        edgarDir: EDGAR 데이터 디렉토리 (None 이면 config 기본).

    Returns:
        DataFrame with columns: component, label, {year columns...}
        각 셀은 해당 연도의 변화량 (당기말 - 전기말). 첫 연도는 None.

    Raises:
        없음.

    Example:
        >>> buildSce("0000320193")
    """
    from dartlab.providers.edgar.finance.pivot import buildAnnual

    annual = buildAnnual(cik, edgarDir=edgarDir)
    if annual is None:
        return None

    series, years = annual
    bs = series.get("BS", {})
    cf = series.get("CF", {})
    isStmt = series.get("IS", {})

    rows: list[dict] = []
    len(years)

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


# ── Shares Outstanding ──────────────────────────────────────────


def getSharesOutstanding(cik: str, *, edgarDir: Path | None = None) -> Optional[int]:
    """SEC DEI 에서 최신 발행주식수 추출.

    Args:
        cik: SEC CIK 번호.
        edgarDir: EDGAR 데이터 디렉토리 (None 이면 config 기본).

    Returns:
        발행주식수 int 또는 None.

    Raises:
        없음.

    Example:
        >>> getSharesOutstanding("0000320193")
    """
    if edgarDir is None:
        from dartlab.providers.edgar.finance.pivot import _getEdgarDir

        edgarDir = _getEdgarDir()
    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        return None
    df = pl.read_parquet(path)
    dei = df.filter((pl.col("namespace") == "dei") & (pl.col("tag") == "EntityCommonStockSharesOutstanding"))
    if dei.height == 0:
        return None
    latest = dei.sort("end", descending=True).row(0, named=True)
    val = latest.get("val")
    return int(val) if val is not None else None
