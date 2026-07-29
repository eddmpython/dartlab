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

from dartlab.core.memory import withMemoryBudget
from dartlab.core.utils.ordering import sortSeries
from dartlab.core.utils.period import (
    buildFiscalToCalendarMap,
    extractYear,
    formatPeriod,
    parsePeriod,
)
from dartlab.providers.edgar.finance.mapper import EdgarMapper


def _getEdgarDir() -> Path:
    from dartlab.core.dataLoader import _dataDir

    return _dataDir("edgar")


@withMemoryBudget(limitMb=500)
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

    Raises:
        없음.

    Example:
        >>> buildTimeseries("0000320193")
    """
    if edgarDir is None:
        edgarDir = _getEdgarDir()
    df = _loadFacts(edgarDir, cik)
    if df is None or df.height == 0:
        return None

    return _buildTimeseriesFromFacts(df)


def _buildTimeseriesFromFacts(
    df: pl.DataFrame,
    *,
    calendarize: bool = True,
) -> tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]:
    df = _selectFinanceNamespace(df)
    namespace = _financeNamespace(df)
    stmtDfs = _splitStmtFacts(df)

    # period 라벨 = end_date 기반 캘린더 앵커링 (Capital IQ 규칙).
    # `core/finance/period.py::buildFiscalToCalendarMap` SSOT 적용.
    # 12월 결산 기업(MNST/INTC/CPNG/OKLO 등) 은 identity — 효과 없음.
    # 비-12월 결산(UAA 3월·NKE 5월·AAPL 9월) 은 fy/fp → end-month CY 매핑.
    # 4 비교 가능성 (회사간 비교) 의 근본 — DART(Dec) ↔ EDGAR cross-company join 가능.
    fiscalToCal = buildFiscalToCalendarMap(df) if calendarize else {}

    series: dict[str, dict[str, dict[str, float]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}
    sidSource: dict[str, dict[str, dict[str, str]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}
    allPeriods: set[str] = set()

    for stmt, stmtDf in stmtDfs.items():
        selected = _selectStandalone(stmtDf, stmt)
        if selected.height == 0:
            continue

        pivoted = _pivotTimeseries(selected)
        pivoted = _computeQ4(pivoted, stmt)
        # 분기 공개 panel은 달력 분기로 비교 가능하게 만든다. 모든 fiscal 열을
        # 동시에 변환해야 2024-Q1 -> 2023-Q4 같은 연쇄 rename이 빠지지 않는다.
        if fiscalToCal:
            pivoted = _calendarizePeriodColumns(pivoted, fiscalToCal)

        periodCols = [c for c in pivoted.columns if c != "tag"]

        for row in pivoted.iter_rows(named=True):
            tag = row["tag"]
            dartSid = _mapFactTag(tag, stmt, namespace)
            if dartSid is None:
                continue

            # NT(주석) 상세 항목은 IS/BS/CF 본문에서 제외
            if dartSid.endswith("_detail") or dartSid.endswith("_note"):
                continue

            # snakeId의 정식 stmt와 현재 stmt가 다르면 제외 (BS 항목이 IS에 섞이는 것 방지)
            # 단, _change 접미사(운전자본 변동)는 CF에서 정당하므로 예외
            if not dartSid.endswith("_change"):
                canonStmt = EdgarMapper.getAccountStmt(dartSid)
                if canonStmt and canonStmt in ("BS", "IS", "CF", "CI", "EQ", "NT") and canonStmt != stmt:
                    continue

            isCommon = _isCommonFactTag(tag, namespace)

            for p in periodCols:
                if "-FY" in p:
                    continue
                val = row.get(p)
                if val is not None:
                    allPeriods.add(p)
                    _storeMappedValue(series[stmt], sidSource[stmt], dartSid, p, val, isCommon)

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

    # SNAKEID_ALIASES 양방향 확장 — canonical · alias 둘 다 series 에 노출.
    # `core/finance/helpers.py::toDictBySnakeId` 의 fixpoint 루프와 동일 패턴 (SSOT).
    # 예: mapper 가 "Assets" → "assets" 로 normalize 해도 소비자 (story · test) 가
    # "total_assets" 로 접근 가능하도록 복제.
    from dartlab.core.utils.labels import SNAKEID_ALIASES

    for stmtMap in result.values():
        for _ in range(4):  # transitive chain (A→B→C) 해소용 fixpoint
            changed = False
            for alias, canonical in SNAKEID_ALIASES.items():
                canonRow = stmtMap.get(canonical)
                aliasRow = stmtMap.get(alias)
                if canonRow is not None and aliasRow is None:
                    stmtMap[alias] = canonRow
                    changed = True
                elif aliasRow is not None and canonRow is None:
                    stmtMap[canonical] = aliasRow
                    changed = True
            if not changed:
                break

    sortSeries(result)

    return result, periods


def buildAnnual(
    cik: str,
    *,
    edgarDir: Path | None = None,
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """EDGAR companyfacts → 연도별 시계열.

    IS/CF: 해당 연도 분기별 standalone 합산 (4분기 필수).
           4분기 미만이면 FY 직접값 폴백.
    BS: 해당 연도 Q4 시점잔액. Q4가 없으면 연간값을 만들지 않음.

    Args:
        cik: SEC CIK 번호.
        edgarDir: EDGAR 데이터 디렉토리 (None이면 config 기본값).

    Returns:
        (series, years) 또는 None.

    Raises:
        없음.

    Example:
        >>> buildAnnual("0000320193")
    """
    if edgarDir is None:
        edgarDir = _getEdgarDir()
    df = _loadFacts(edgarDir, cik)
    if df is None or df.height == 0:
        return None

    # annual은 SEC의 fiscal year 계약이다. quarterly 공개 panel의 calendar
    # label을 여기 재사용하면 비12월 결산 기업의 네 분기가 두 연도에 갈라진다.
    qResult = _buildTimeseriesFromFacts(df, calendarize=False)
    qSeries, qPeriods = qResult

    # FY 직접값 맵 구축 (분기 합산 실패 시 폴백)
    fyMap = _buildFyMap(df)

    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(qPeriods):
        year = extractYear(p)
        yearSet.setdefault(year, []).append(i)
    for stmtMap in fyMap.values():
        for yearMap in stmtMap.values():
            for year in yearMap:
                yearSet.setdefault(year, [])

    years = sorted(yearSet.keys())
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    result: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}, "CI": {}}

    for sjDiv in result:
        snakeIds = set(qSeries.get(sjDiv, {}).keys())
        snakeIds.update(fyMap.get(sjDiv, {}).keys())

        for snakeId in snakeIds:
            # _detail/_note는 IS/BS/CF 본문에서 제외
            if snakeId.endswith("_detail") or snakeId.endswith("_note"):
                continue
            # canonStmt 검증 — BS 항목이 IS에 섞이는 것 방지
            if not snakeId.endswith("_change"):
                canonStmt = EdgarMapper.getAccountStmt(snakeId)
                if canonStmt and canonStmt in ("BS", "IS", "CF", "CI", "EQ", "NT") and canonStmt != sjDiv:
                    continue
            vals = qSeries.get(sjDiv, {}).get(snakeId, [])
            annual: list[Optional[float]] = [None] * nYears

            for year, qIndices in yearSet.items():
                yIdx = yearIdx[year]

                if sjDiv == "BS":
                    q4Indices = [index for index in qIndices if qPeriods[index].endswith("-Q4")]
                    if q4Indices:
                        q4Index = q4Indices[0]
                        annual[yIdx] = vals[q4Index] if q4Index < len(vals) else None
                else:
                    qVals: dict[str, float] = {}
                    for index in qIndices:
                        if index >= len(vals):
                            continue
                        value = vals[index]
                        if value is not None:
                            qVals[qPeriods[index].rsplit("-Q", 1)[-1]] = value
                    if set(qVals) == {"1", "2", "3", "4"}:
                        annual[yIdx] = sum(qVals.values())
                    else:
                        # FY 직접값 폴백
                        fyVal = fyMap.get(sjDiv, {}).get(snakeId, {}).get(year)
                        annual[yIdx] = fyVal

            result[sjDiv][snakeId] = annual

    return result, years


def _buildFyMap(
    df: pl.DataFrame,
) -> dict[str, dict[str, dict[str, float]]]:
    """raw companyfacts에서 FY 직접값을 annual 폴백 맵으로 구축."""
    df = _selectFinanceNamespace(df)
    namespace = _financeNamespace(df)
    stmtDfs = _splitStmtFacts(df)
    fyMap: dict[str, dict[str, dict[str, float]]] = {"IS": {}, "CF": {}, "CI": {}}
    sidSource: dict[str, dict[str, dict[str, str]]] = {"IS": {}, "CF": {}, "CI": {}}

    for stmt in ["IS", "CF", "CI"]:
        stmtDf = stmtDfs.get(stmt)
        if stmtDf is None or stmtDf.height == 0:
            continue

        selected = _selectStandalone(stmtDf, stmt)
        if selected.height == 0:
            continue
        annualRows = selected.filter(pl.col("period").str.ends_with("-FY"))
        if annualRows.height == 0:
            continue

        for row in annualRows.iter_rows(named=True):
            tag = row["tag"]
            dartSid = _mapFactTag(tag, stmt, namespace)
            if dartSid is None:
                continue
            period = row["period"]
            year = extractYear(period)
            val = row["val"]
            if val is None:
                continue
            _storeMappedValue(
                fyMap[stmt],
                sidSource[stmt],
                dartSid,
                year,
                val,
                _isCommonFactTag(tag, namespace),
            )

    return fyMap


def _selectStandalone(df: pl.DataFrame, stmtType: str) -> pl.DataFrame:
    # frame.is_null() 필터 제거 — downstream(_selectFlowDirect 등)이
    # duration_days 기반으로 standalone/YTD를 정확히 구분한다.
    # frame이 있는 행(CY2025, CY2025Q2 등)도 standalone일 수 있으므로
    # 여기서 미리 제거하면 Q2/Q3/FY 데이터가 누락된다.
    tagDf = df.filter(pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"]))

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

    각 (tag, period)에서 해당 fiscal period에 맞는 end date 값을 선택.
    multiEnd 혼합 방지: 같은 (tag, fy, fp)에 end가 여러 개면
    fp의 기대 월(Q1→3월, Q2→6월, Q3→9월, FY→12월)에 가장 가까운 end를 선택.
    """
    if tagDf.height == 0:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})

    hasEnd = tagDf.filter(pl.col("end").is_not_null())
    if hasEnd.height == 0:
        return _selectByLatestPeriod(tagDf)

    # frame이 있으면 우선 (정확한 기간 데이터)
    hasFrame = hasEnd.filter(pl.col("frame").is_not_null())
    noFrame = hasEnd.filter(pl.col("frame").is_null())

    if hasFrame.height > 0:
        # frame 있는 것 우선, 없으면 frame 없는 것으로 보충
        frameResult = (
            hasFrame.sort(["end", "filed"], descending=[True, True])
            .group_by(["tag", "period"])
            .agg(pl.col("val").first().alias("val"))
        )
        if noFrame.height > 0:
            noFrameResult = (
                noFrame.sort(["end", "filed"], descending=[True, True])
                .group_by(["tag", "period"])
                .agg(pl.col("val").first().alias("val"))
            )
            # frame 결과에 없는 (tag, period)만 보충
            supplement = noFrameResult.join(frameResult, on=["tag", "period"], how="anti")
            if supplement.height > 0:
                return pl.concat([frameResult, supplement])
        return frameResult

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

    # FY: 연간(300d+)만 선택 — 10-K 비교재무제표에 포함된 90일 standalone 제외
    fyRows = tagDf.filter(
        (pl.col("fp") == "FY") & pl.col("duration_days").is_not_null() & (pl.col("duration_days") > 300)
    )
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

    # FY: 연간(300d+)만, Q1: duration 무관 (항상 ~90d)
    fyRows = tagDf.filter(
        (pl.col("fp") == "FY") & pl.col("duration_days").is_not_null() & (pl.col("duration_days") > 300)
    )
    q1Rows = tagDf.filter(pl.col("fp") == "Q1")
    fyQ1 = (
        pl.concat([fyRows, q1Rows])
        if fyRows.height > 0 or q1Rows.height > 0
        else tagDf.filter(pl.col("fp").is_in(["FY", "Q1"]))
    )
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

    revTags = EdgarMapper.getTagsForSnakeIds(["sales", "revenue"])
    for (tag, fy, fp), ytdVal in ytdMap.items():
        if fp == "Q2":
            q1Val = q1Map.get((tag, fy))
            if q1Val is not None and ytdVal is not None:
                standalone = ytdVal - q1Val
                if standalone < 0 and tag in revTags:
                    continue
                rows.append({"tag": tag, "period": formatPeriod(fy, 2), "val": standalone})
        elif fp == "Q3":
            q2YtdVal = ytdMap.get((tag, fy, "Q2"))
            if q2YtdVal is not None and ytdVal is not None:
                standalone = ytdVal - q2YtdVal
                if standalone < 0 and tag in revTags:
                    continue
                rows.append({"tag": tag, "period": formatPeriod(fy, 3), "val": standalone})

    if not rows:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})
    return pl.DataFrame(rows)


def _findMissingQuarters(tagDf: pl.DataFrame, result: pl.DataFrame) -> pl.DataFrame:
    """Q1~Q3 중 기대되지만 result 에 없는 period 탐색.

    Q1 이 raw 에도 없는 YTD-전용 기업(Google 등) 대응:
    동일 (tag, fy) 에 Q2/Q3/FY 중 하나라도 있으면 Q1/Q2/Q3 모두 기대한다.
    """
    # raw 에 포함된 (tag, period) 조합
    rawPeriods = tagDf.select("tag", "period").unique()

    # (tag, fy) 단위로 Q2/Q3/FY 존재 여부 기반 기대 집합 생성
    tagFy = tagDf.select("tag", "fy").unique()
    # Q2/Q3/FY 중 하나라도 있는 (tag, fy) 만 기대 대상
    seenFp = tagDf.filter(pl.col("fp").is_in(["Q2", "Q3", "FY"])).select("tag", "fy").unique()
    expected = tagFy.join(seenFp, on=["tag", "fy"], how="semi")
    expectedPeriods = pl.concat(
        [
            expected.with_columns((pl.col("fy").cast(pl.Utf8) + pl.lit(f"-{q}")).alias("period")).select(
                "tag", "period"
            )
            for q in ("Q1", "Q2", "Q3")
        ]
    ).unique()

    allPeriods = pl.concat([rawPeriods, expectedPeriods]).unique()
    existingPeriods = result.select("tag", "period").unique()
    missing = allPeriods.join(existingPeriods, on=["tag", "period"], how="anti")
    return missing.filter(pl.col("period").str.contains("Q[123]"))


def _ytdDeaccumulate(tagDf: pl.DataFrame, missingPeriods: pl.DataFrame) -> pl.DataFrame:
    """YTD(누적) 데이터로 standalone 분기값 역산.

    Q1 누락 + Q2/Q3 standalone + Q3_YTD 보유 경우 (Google 같은 YTD-전용 보고 기업):
        Q1 = Q3_YTD - Q2_standalone - Q3_standalone
    Q1 누락 + Q2 standalone + Q2_YTD 경우:
        Q1 = Q2_YTD - Q2_standalone
    Q2 누락 + Q1 standalone + Q2_YTD 경우 (기존):
        Q2 = Q2_YTD - Q1_standalone
    Q3 누락 + Q2_YTD + Q3_YTD 경우 (기존):
        Q3 = Q3_YTD - Q2_YTD
    """
    tagDf = _computeDurationDays(tagDf) if "duration_days" not in tagDf.columns else tagDf

    ytdRows = tagDf.filter(pl.col("duration_days").is_not_null() & (pl.col("duration_days") > 100))
    standaloneRows = tagDf.filter(pl.col("duration_days").is_not_null() & (pl.col("duration_days") <= 100))

    revTags = EdgarMapper.getTagsForSnakeIds(["sales", "revenue"])
    rows = []
    for mpRow in missingPeriods.iter_rows(named=True):
        tag, period = mpRow["tag"], mpRow["period"]
        fy = extractYear(period)
        fp = period.split("-")[1]
        fyInt = int(fy)

        def _firstVal(df: pl.DataFrame) -> float | None:
            if df.height == 0:
                return None
            return df.sort(["end", "filed"], descending=[True, True]).row(0, named=True)["val"]

        if fp == "Q1":
            # 우선 Q2_YTD - Q2_standalone
            q2Ytd = _firstVal(ytdRows.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == "Q2")))
            q2Stand = _firstVal(
                standaloneRows.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == "Q2"))
            )
            standalone: float | None = None
            if q2Ytd is not None and q2Stand is not None:
                standalone = q2Ytd - q2Stand
            else:
                # fallback: Q3_YTD - Q2_standalone - Q3_standalone (GOOGL 케이스)
                q3Ytd = _firstVal(
                    ytdRows.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == "Q3"))
                )
                q3Stand = _firstVal(
                    standaloneRows.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == "Q3"))
                )
                if q3Ytd is not None and q2Stand is not None and q3Stand is not None:
                    standalone = q3Ytd - q2Stand - q3Stand
            if standalone is not None:
                if standalone < 0 and tag in revTags:
                    continue
                rows.append({"tag": tag, "period": period, "val": standalone})
            continue

        candidates = ytdRows.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == fp)).sort(
            ["end", "filed"], descending=[True, True]
        )
        if candidates.height == 0:
            continue
        ytdVal = candidates.row(0, named=True)["val"]

        if fp == "Q2":
            q1Rows = tagDf.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == "Q1")).sort(
                "filed", descending=True
            )
            if q1Rows.height > 0:
                q1Val = q1Rows.row(0, named=True)["val"]
                if q1Val is not None and ytdVal is not None:
                    standalone = float(ytdVal) - float(q1Val)
                    if standalone < 0 and tag in revTags:
                        continue
                    rows.append({"tag": tag, "period": period, "val": standalone})

        elif fp == "Q3":
            q2YtdRows = ytdRows.filter((pl.col("tag") == tag) & (pl.col("fy") == fyInt) & (pl.col("fp") == "Q2")).sort(
                ["end", "filed"], descending=[True, True]
            )
            if q2YtdRows.height > 0:
                q2YtdVal = q2YtdRows.row(0, named=True)["val"]
                if q2YtdVal is not None and ytdVal is not None:
                    standalone = float(ytdVal) - float(q2YtdVal)
                    if standalone < 0 and tag in revTags:
                        continue
                    rows.append({"tag": tag, "period": period, "val": standalone})

    if not rows:
        return pl.DataFrame(schema={"tag": pl.Utf8, "period": pl.Utf8, "val": pl.Float64})
    return pl.DataFrame(rows)


# ── 재내보내기 (분리: pivotFactsLoad.py · pivotPost.py) ──────────
from dartlab.providers.edgar.finance.pivotFactsLoad import (  # noqa: E402  re-export
    _autoDownloadEdgarFinance,
    _financeNamespace,
    _guessStmt,
    _isCommonFactTag,
    _loadFacts,
    _mapFactTag,
    _selectFinanceNamespace,
    _splitStmtFacts,
    _storeMappedValue,
)
from dartlab.providers.edgar.finance.pivotPost import (  # noqa: E402  re-export
    _calendarizePeriodColumns,
    _computeDerived,
    _computeEquity,
    _computeQ4,
    _pivotTimeseries,
    _sanitizeQ4,
    _sortPeriods,
    buildSce,
    getSharesOutstanding,
)
