"""finance pivot SCE (자본변동표) — pivot.py 분할 (규칙 3 LoC).

`pivot.py` 939 LoC 가 규칙 3 임계 (>800) 위반. SCE 관련 함수 (~170 줄) 를 본
모듈로 분리. 호출자 호환 — pivot.py 가 재내보내기.
"""

from __future__ import annotations

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.polarsUtil import isEmptyDf


def buildSceMatrix(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> tuple[dict[str, dict[str, dict[str, float | None]]], list[str]] | None:
    """SCE 원본 → 연도별 자본변동 매트릭스.

    각 연도에서 가장 높은 분기 (maxQ) 만 사용 — 누적 보고 인정.

    Args:
        stockCode: 종목코드 (예: ``"005930"``).
        fsDivPref: ``"CFS"`` (연결) 또는 ``"OFS"`` (별도).

    Returns:
        ``(matrix, years)`` 또는 None.

        - ``matrix[year][cause_snakeId][detail_snakeId] = 금액``
        - ``years = ["2016", "2017", ..., "2024"]``

    Raises:
        없음 (데이터 부재 시 None 반환).

    Example:
        >>> matrix, years = buildSceMatrix("005930")
    """

    _SCE_COLS = [
        "sj_div",
        "fs_div",
        "account_id",
        "account_nm",
        "account_detail",
        "bsns_year",
        "reprt_nm",
        "thstrm_amount",
    ]
    df = loadData(stockCode, category="finance", columns=_SCE_COLS)
    if isEmptyDf(df):
        return None

    return _buildSceMatrixFromDf(df, fsDivPref)


def _buildSceMatrixFromDf(
    df: pl.DataFrame,
    fsDivPref: str = "CFS",
) -> tuple[dict[str, dict[str, dict[str, float | None]]], list[str]] | None:
    """DataFrame에서 직접 SCE 매트릭스 피벗 (내부용)."""
    from dartlab.providers.dart.finance.sceMapper import normalizeCause, normalizeDetail

    if "sj_div" not in df.columns:
        return None

    sce = df.filter(pl.col("sj_div") == "SCE")
    if sce.is_empty():
        return None

    from dartlab.providers.dart.finance.pivot import _applyCfsPriority

    sce = _applyCfsPriority(sce, fsDivPref)

    if "thstrm_amount" in sce.columns:
        from dartlab.providers.dart.parse.amount import parseAmountExpr

        sce = sce.with_columns(parseAmountExpr("thstrm_amount").alias("thstrm_amount"))

    from dartlab.providers.dart.finance.pivot import QUARTER_ORDER, _preserveUnmapped

    yearMaxQ: dict[str, int] = {}
    for row in sce.iter_rows(named=True):
        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        if qNum > 0:
            yearMaxQ[year] = max(yearMaxQ.get(year, 0), qNum)

    yearSet: set[str] = set()
    matrix: dict[str, dict[str, dict[str, float | None]]] = {}

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
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    """SCE → 연도별 시계열 (BS/IS/CF 와 유사한 출력 형태).

    Args:
        stockCode: 종목코드 (예: ``"005930"``).
        fsDivPref: ``"CFS"`` (연결) 또는 ``"OFS"`` (별도).

    Returns:
        ``(series, years)`` 또는 None.

        - ``series["SCE"]["cause__detail"] = [v2016, v2017, ..., v2024]``
        - ``years = ["2016", "2017", ..., "2024"]``

    Raises:
        없음 (데이터 부재 시 None 반환).

    Example:
        >>> series, years = buildSceAnnual("005930")
    """
    result = buildSceMatrix(stockCode, fsDivPref)
    if result is None:
        return None

    return _sceMatrixToSeries(result)


def _sceMatrixToSeries(
    matrixResult: tuple[dict[str, dict[str, dict[str, float | None]]], list[str]],
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]]:
    """매트릭스 → 연도별 시계열 변환 (내부용)."""
    matrix, years = matrixResult
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    allKeys: set[tuple[str, str]] = set()
    for year in matrix:
        for cause in matrix[year]:
            for detail in matrix[year][cause]:
                allKeys.add((cause, detail))

    series: dict[str, list[float | None]] = {}
    for cause, detail in sorted(allKeys):
        key = f"{cause}__{detail}"
        vals: list[float | None] = [None] * nYears
        for year in matrix:
            idx = yearIdx[year]
            val = matrix[year].get(cause, {}).get(detail)
            vals[idx] = val
        series[key] = vals

    return {"SCE": series}, years
