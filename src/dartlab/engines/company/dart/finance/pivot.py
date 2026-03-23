"""원본 finance parquet → 분기별 시계열 dict 피벗.

정규화 로직:
1. CFS 우선 선택 (행 단위 중복 제거)
2. IS/CIS/CF 누적 → standalone 변환
3. BS 그대로 (시점 잔액)
4. 분기별 period 컬럼 생성
5. SCE 연도별 매트릭스/시계열 피벗

결과 구조::

    {
        "BS":  {"total_assets": [v1, v2, ...], ...},
        "IS":  {"sales": [...], ...},
        "CF":  {"operating_cashflow": [...], ...},
    }

periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]

SCE 결과 구조::

    matrix[year][cause][detail] = 금액
    series["SCE"]["cause__detail"] = [v2016, v2017, ..., v2024]

snakeId는 standardAccounts.json 기준 그대로 사용.
"""

from __future__ import annotations

import logging
from typing import Optional

import polars as pl

from dartlab.engines.common.finance.ordering import sortSeries
from dartlab.engines.common.finance.period import extractYear, formatPeriod
from dartlab.engines.company.dart.finance.mapper import AccountMapper

_log = logging.getLogger(__name__)

QUARTER_ORDER = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}


def _preserveUnmapped(label: str, prefix: str) -> str:
    safe = (
        label.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "_")
    )
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in safe)
    safe = "_".join(part for part in safe.split("_") if part)
    return f"{prefix}_{safe or 'unknown'}"


def _loadAndNormalize(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[pl.DataFrame, list[str]]]:
    """finance parquet → 정규화된 DataFrame + periods (내부용)."""
    from dartlab.core.dataLoader import loadData

    _FINANCE_COLS = [
        "sj_div",
        "fs_div",
        "account_id",
        "account_nm",
        "bsns_year",
        "reprt_nm",
        "thstrm_amount",
        "thstrm_add_amount",
    ]
    df = loadData(stockCode, category="finance", columns=_FINANCE_COLS)
    if df is None or df.is_empty():
        return None

    if "sj_div" not in df.columns:
        return None

    df = df.filter(pl.col("sj_div").is_in(["BS", "IS", "CIS", "CF"]))
    if df.is_empty():
        return None

    # 2015년 제외 — Q4(사업보고서)만 존재하여 standalone 변환 불가
    df = df.filter(pl.col("bsns_year") != "2015")
    if df.is_empty():
        return None

    df = _applyCfsPriority(df, fsDivPref)
    df = _normalizeQ4(df)

    periods = _buildPeriods(df)
    return df, periods


def buildTimeseries(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """finance parquet → 분기별 standalone 시계열.

    Args:
            stockCode: 종목코드 (예: "005930")
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도). CFS 없으면 OFS fallback.

    Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]
    """
    result = _loadAndNormalize(stockCode, fsDivPref)
    if result is None:
        return None

    df, periods = result
    series = _pivotToSeries(df, periods)

    return series, periods


def buildAnnual(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """finance parquet → 연도별 시계열.

    IS/CF: 해당 연도 분기별 standalone 합산.
    BS: 해당 연도 마지막 분기(Q4 우선) 시점잔액.

    Args:
            stockCode: 종목코드 (예: "005930")
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

    Returns:
            (series, years) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            years = ["2016", "2017", ..., "2024"]
    """
    qResult = buildTimeseries(stockCode, fsDivPref)
    if qResult is None:
        return None

    qSeries, qPeriods = qResult
    return _aggregateAnnual(qSeries, qPeriods)


def buildCumulative(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """finance parquet → 분기별 누적 시계열.

    IS/CF: 해당 연도 시작부터 누적합 (Q1, Q1+Q2, Q1+Q2+Q3, Q1+Q2+Q3+Q4).
    BS: 시점잔액 그대로.

    Args:
            stockCode: 종목코드 (예: "005930")
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

    Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]
    """
    qResult = buildTimeseries(stockCode, fsDivPref)
    if qResult is None:
        return None

    qSeries, qPeriods = qResult
    return _aggregateCumulative(qSeries, qPeriods)


def _applyCfsPriority(df: pl.DataFrame, pref: str) -> pl.DataFrame:
    """시트(연도×분기×재무제표) 단위 CFS/OFS 선택. pref 우선.

    같은 시트에서 CFS가 1행이라도 있으면 CFS만 사용하고,
    CFS가 없는 시트는 OFS 전체로 폴백한다.
    행 단위 혼합은 합계 불일치를 유발하므로 금지한다.
    """
    if "fs_div" not in df.columns:
        return df

    available = set(df["fs_div"].drop_nulls().unique().to_list())
    if len(available) <= 1:
        return df

    # 시트별(연도, 분기, 재무제표) 소스 결정
    groupCols = ["bsns_year", "reprt_nm", "sj_div"]
    if not all(c in df.columns for c in groupCols):
        return df

    sheetSources = df.group_by(groupCols).agg(pl.col("fs_div").drop_nulls().unique().alias("_sources"))

    def _pickSource(sources: list[str]) -> str:
        """시트별 선택할 fs_div 결정."""
        sourceSet = set(sources)
        if pref in sourceSet:
            return pref
        fallback = "OFS" if pref == "CFS" else "CFS"
        if fallback in sourceSet:
            return fallback
        return sources[0]

    sheetSources = sheetSources.with_columns(
        pl.col("_sources").map_elements(_pickSource, return_dtype=pl.Utf8).alias("_targetFs")
    )

    df = df.join(sheetSources.select(groupCols + ["_targetFs"]), on=groupCols, how="left")
    df = df.filter(pl.col("fs_div") == pl.col("_targetFs"))
    df = df.drop("_targetFs")
    return df


def _normalizeQ4(df: pl.DataFrame) -> pl.DataFrame:
    """IS/CIS/CF 누적값 → standalone(분기 단독) 변환.

    DART 원본 데이터 구조:
    - thstrm_amount: 당기금액 (IS/CIS: 누적, CF: 누적, BS: 시점잔액)
    - thstrm_add_amount: 당기추가금액 (IS/CIS Q4 사업보고서 전용 — 연간 누적)

    Standalone 변환 로직:
    - BS: 시점 잔액이므로 thstrm_amount 그대로
    - CF: Q1은 그대로, Q2~Q4는 전분기 thstrm_amount 차분
    - IS/CIS:
      - Q1: thstrm_amount 그대로 (없으면 thstrm_add_amount fallback)
      - Q2~Q3: thstrm_add_amount - 전분기 thstrm_add_amount
        (thstrm_amount가 null이거나 thstrm_add_amount와 같으면 누적 기반)
      - Q4 특수: thstrm_add_amount가 없으면 thstrm_amount를 Q4 누적으로 간주
        → thstrm_amount - 전분기 thstrm_add_amount로 standalone 추출

    Fallback 경로:
    - thstrm_add_amount null + Q4 IS/CIS → thstrm_amount로 대체 후 차분
    - 전분기 값 null → None (standalone 계산 불가)
    """
    df = df.with_columns(pl.col("reprt_nm").replace(QUARTER_ORDER).cast(pl.Int32).alias("_qOrd"))

    # 문자열 금액 → Float64 변환 (빈 문자열, "-" → null)
    for col in ["thstrm_amount", "thstrm_add_amount"]:
        if col in df.columns:
            df = df.with_columns(
                pl.when(
                    pl.col(col).is_not_null()
                    & (pl.col(col).str.strip_chars() != "")
                    & (pl.col(col).str.strip_chars() != "-")
                )
                .then(pl.col(col).str.strip_chars().str.replace_all(",", "").cast(pl.Float64, strict=False))
                .otherwise(pl.lit(None).cast(pl.Float64))
                .alias(col)
            )
        else:
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias(col))

    groupKey = ["bsns_year", "sj_div", "account_id"]
    df = df.sort(groupKey + ["_qOrd"])

    df = df.with_columns(pl.col("thstrm_add_amount").shift(1).over(groupKey).alias("_prevAdd"))

    # Q4 IS/CIS: thstrm_add_amount가 null이면 thstrm_amount를 연간 누적으로 간주
    df = df.with_columns(
        pl.when(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("reprt_nm") == "4분기")
            & pl.col("thstrm_add_amount").is_null()
        )
        .then(pl.col("thstrm_amount"))
        .otherwise(pl.col("thstrm_add_amount"))
        .alias("thstrm_add_amount")
    )

    # prevAdd/prevAmount 재계산 (Q4 fallback 적용 후)
    df = df.with_columns(pl.col("thstrm_add_amount").shift(1).over(groupKey).alias("_prevAdd"))
    df = df.with_columns(pl.col("thstrm_amount").shift(1).over(groupKey).alias("_prevAmount"))

    df = df.with_columns(
        # BS: 시점 잔액 그대로
        pl.when(pl.col("sj_div") == "BS")
        .then(pl.col("thstrm_amount"))
        # CF: Q1 그대로, Q2~Q4 전분기 차분
        .when(pl.col("sj_div") == "CF")
        .then(
            pl.when(pl.col("_qOrd") == 1)
            .then(pl.col("thstrm_amount"))
            .when(pl.col("_prevAmount").is_null())
            .then(None)
            .otherwise(pl.col("thstrm_amount") - pl.col("_prevAmount"))
        )
        # IS/CIS Q1: thstrm_amount null이면 thstrm_add_amount fallback
        .when((pl.col("reprt_nm") == "1분기") & pl.col("thstrm_amount").is_null())
        .then(pl.col("thstrm_add_amount"))
        # IS/CIS Q2~Q4: 누적 기반 차분 (thstrm_amount가 null이거나 add와 같으면)
        .when(
            (pl.col("reprt_nm") != "1분기")
            & (pl.col("thstrm_amount").is_null() | (pl.col("thstrm_amount") == pl.col("thstrm_add_amount")))
        )
        .then(
            pl.when(pl.col("_prevAdd").is_null()).then(None).otherwise(pl.col("thstrm_add_amount") - pl.col("_prevAdd"))
        )
        # IS/CIS Q4: thstrm_add_amount null fallback — thstrm_amount에서 차분
        .when((pl.col("reprt_nm") == "4분기") & pl.col("thstrm_add_amount").is_null())
        .then(pl.when(pl.col("_prevAdd").is_null()).then(None).otherwise(pl.col("thstrm_amount") - pl.col("_prevAdd")))
        # 기본: thstrm_amount 사용 (IS/CIS Q1 정상 경로)
        .otherwise(pl.col("thstrm_amount"))
        .alias("_normalized_amount")
    )

    df = df.drop(["_prevAdd", "_prevAmount", "thstrm_add_amount", "_qOrd"])

    return df


def _buildPeriods(df: pl.DataFrame) -> list[str]:
    """분기별 period 리스트 생성."""
    pairs = df.select("bsns_year", "reprt_nm").unique()
    result = []
    for row in pairs.iter_rows(named=True):
        y = row["bsns_year"]
        q = row["reprt_nm"]
        qNum = QUARTER_ORDER.get(q, 0)
        if qNum == 0:
            continue
        result.append((y, qNum, formatPeriod(y, qNum)))

    result.sort(key=lambda x: (x[0], x[1]))
    return [r[2] for r in result]


def _pivotToSeries(
    df: pl.DataFrame,
    periods: list[str],
) -> dict[str, dict[str, list[Optional[float]]]]:
    """DataFrame → {sjDiv: {snakeId: [값...]}} 피벗."""
    mapper = AccountMapper.get()
    periodIdx = {p: i for i, p in enumerate(periods)}
    nPeriods = len(periods)

    result: dict[str, dict[str, list[Optional[float]]]] = {
        "BS": {},
        "IS": {},
        "CF": {},
    }

    totalRows = 0
    unmappedRows = 0
    unmappedAccounts: dict[str, int] = {}

    for row in df.iter_rows(named=True):
        sjDiv = row.get("sj_div", "")
        if sjDiv == "CIS":
            sjDiv = "IS"
        if sjDiv not in result:
            continue

        totalRows += 1
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        snakeId = mapper.map(accountId, accountNm)
        if snakeId is None:
            unmappedRows += 1
            key = f"{accountId}|{accountNm}"
            unmappedAccounts[key] = unmappedAccounts.get(key, 0) + 1
            _log.debug("미매핑 계정: id=%s nm=%s", accountId, accountNm)
            continue

        amount = row.get("_normalized_amount")

        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        pKey = formatPeriod(year, qNum)

        idx = periodIdx.get(pKey)
        if idx is None:
            continue

        target = result[sjDiv]
        if snakeId not in target:
            target[snakeId] = [None] * nPeriods

        if target[snakeId][idx] is None:
            target[snakeId][idx] = amount

    if unmappedAccounts:
        _log.info(
            "finance 매핑: %d/%d 행 매핑 완료, %d 행 미매핑 (%d 고유 계정)",
            totalRows - unmappedRows,
            totalRows,
            unmappedRows,
            len(unmappedAccounts),
        )
        for acct, cnt in sorted(unmappedAccounts.items(), key=lambda x: -x[1])[:5]:
            _log.debug("  미매핑 상위: %s (%d회)", acct, cnt)

    sortSeries(result)
    return result


def _aggregateAnnual(
    qSeries: dict[str, dict[str, list[Optional[float]]]],
    qPeriods: list[str],
) -> tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]:
    """분기별 standalone → 연도별 집계."""
    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(qPeriods):
        year = extractYear(p)
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


def _aggregateCumulative(
    qSeries: dict[str, dict[str, list[Optional[float]]]],
    qPeriods: list[str],
) -> tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]:
    """분기별 standalone → 분기별 누적."""
    yearStarts: dict[str, int] = {}
    for i, p in enumerate(qPeriods):
        year = extractYear(p)
        if year not in yearStarts:
            yearStarts[year] = i

    result: dict[str, dict[str, list[Optional[float]]]] = {"BS": {}, "IS": {}, "CF": {}}
    nPeriods = len(qPeriods)

    for sjDiv in qSeries:
        for snakeId, vals in qSeries[sjDiv].items():
            cum: list[Optional[float]] = [None] * nPeriods

            if sjDiv == "BS":
                cum = list(vals)
            else:
                for i, p in enumerate(qPeriods):
                    year = extractYear(p)
                    startIdx = yearStarts[year]
                    qVals = [vals[j] for j in range(startIdx, i + 1) if j < len(vals) and vals[j] is not None]
                    cum[i] = sum(qVals) if qVals else None

            result[sjDiv][snakeId] = cum

    return result, list(qPeriods)


def buildSceMatrix(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, dict[str, Optional[float]]]], list[str]]]:
    """SCE 원본 → 연도별 자본변동 매트릭스.

    각 연도에서 가장 높은 분기(maxQ)만 사용.

    Args:
            stockCode: 종목코드 (예: "005930")
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

    Returns:
            (matrix, years) 또는 None.
            matrix[year][cause_snakeId][detail_snakeId] = 금액
            years = ["2016", "2017", ..., "2024"]
    """
    from dartlab.core.dataLoader import loadData

    _SCE_COLS = [
        "sj_div",
        "fs_div",
        "account_id",
        "account_nm",
        "bsns_year",
        "reprt_nm",
        "thstrm_amount",
    ]
    df = loadData(stockCode, category="finance", columns=_SCE_COLS)
    if df is None or df.is_empty():
        return None

    return _buildSceMatrixFromDf(df, fsDivPref)


def _buildSceMatrixFromDf(
    df: pl.DataFrame,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, dict[str, Optional[float]]]], list[str]]]:
    """DataFrame에서 직접 SCE 매트릭스 피벗 (내부용)."""
    from dartlab.engines.company.dart.finance.sceMapper import normalizeCause, normalizeDetail

    if "sj_div" not in df.columns:
        return None

    sce = df.filter(pl.col("sj_div") == "SCE")
    if sce.is_empty():
        return None

    sce = _applyCfsPriority(sce, fsDivPref)

    if "thstrm_amount" in sce.columns:
        sce = sce.with_columns(
            pl.when(
                pl.col("thstrm_amount").is_not_null()
                & (pl.col("thstrm_amount").str.strip_chars() != "")
                & (pl.col("thstrm_amount").str.strip_chars() != "-")
            )
            .then(pl.col("thstrm_amount").str.strip_chars().str.replace_all(",", "").cast(pl.Float64, strict=False))
            .otherwise(pl.lit(None).cast(pl.Float64))
            .alias("thstrm_amount")
        )

    yearMaxQ: dict[str, int] = {}
    for row in sce.iter_rows(named=True):
        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        if qNum > 0:
            yearMaxQ[year] = max(yearMaxQ.get(year, 0), qNum)

    yearSet: set[str] = set()
    matrix: dict[str, dict[str, dict[str, Optional[float]]]] = {}

    for row in sce.iter_rows(named=True):
        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        if qNum == 0:
            continue

        maxQ = yearMaxQ.get(year, 4)
        if qNum != maxQ:
            continue

        nm = row.get("account_nm", "") or ""
        detail = row.get("account_detail", "") or ""
        amount = row.get("thstrm_amount")

        cause = normalizeCause(nm)
        component = normalizeDetail(detail)

        if cause.startswith("unmapped:"):
            cause = _preserveUnmapped(cause.split(":", 1)[1], "other")
        if component.startswith("unmapped:"):
            component = _preserveUnmapped(component.split(":", 1)[1], "detail")

        yearSet.add(year)
        if year not in matrix:
            matrix[year] = {}
        if cause not in matrix[year]:
            matrix[year][cause] = {}

        if amount is not None:
            matrix[year][cause][component] = amount

    years = sorted(yearSet)
    if not years:
        return None
    return matrix, years


def buildSceAnnual(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """SCE → 연도별 시계열 (BS/IS/CF와 유사한 출력 형태).

    Args:
            stockCode: 종목코드 (예: "005930")
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

    Returns:
            (series, years) 또는 None.
            series["SCE"]["cause__detail"] = [v2016, v2017, ..., v2024]
            years = ["2016", "2017", ..., "2024"]
    """
    result = buildSceMatrix(stockCode, fsDivPref)
    if result is None:
        return None

    return _sceMatrixToSeries(result)


def _sceMatrixToSeries(
    matrixResult: tuple[dict[str, dict[str, dict[str, Optional[float]]]], list[str]],
) -> tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]:
    """매트릭스 → 연도별 시계열 변환 (내부용)."""
    matrix, years = matrixResult
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    allKeys: set[tuple[str, str]] = set()
    for year in matrix:
        for cause in matrix[year]:
            for detail in matrix[year][cause]:
                allKeys.add((cause, detail))

    series: dict[str, list[Optional[float]]] = {}
    for cause, detail in sorted(allKeys):
        key = f"{cause}__{detail}"
        vals: list[Optional[float]] = [None] * nYears
        for year in matrix:
            idx = yearIdx[year]
            val = matrix[year].get(cause, {}).get(detail)
            vals[idx] = val
        series[key] = vals

    return {"SCE": series}, years
