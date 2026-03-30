"""거시지표 시계열 정제 유틸 — ECOS/FRED 공통.

변화율 계산, 분기/연간 리샘플링, Parquet 영구 캐시.
analysis 계층에서 재무-거시 회귀 시 시간축 맞추기에 사용.
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

log = logging.getLogger(__name__)

# Parquet 영구 캐시 경로
_CACHE_DIR = Path.home() / ".dartlab" / "cache" / "macro"


# ── 변화율 계산 ──


def addChangeRate(df: pl.DataFrame, *, valueName: str = "value") -> pl.DataFrame:
    """시계열 DataFrame에 변화율 컬럼 추가.

    추가 컬럼:
        - change: 전기대비 변화량
        - changePct: 전기대비 변화율 (%)
        - yoyChange: 전년동기대비 변화량 (4기 lag, 분기 기준)
        - yoyChangePct: 전년동기대비 변화율 (%)

    Args:
        df: ``(date, value)`` 형태 DataFrame.
        valueName: 값 컬럼명.
    """
    if df.is_empty() or valueName not in df.columns:
        return df

    result = df.sort("date").with_columns(
        (pl.col(valueName) - pl.col(valueName).shift(1)).alias("change"),
        (
            (pl.col(valueName) - pl.col(valueName).shift(1))
            / pl.col(valueName).shift(1).abs()
            * 100
        ).alias("changePct"),
    )

    # YoY: 날짜 간격 추정으로 lag 결정
    if len(df) >= 8:
        dates = df.sort("date").get_column("date")
        avgGapDays = (dates[-1] - dates[0]).days / (len(dates) - 1)

        if avgGapDays < 45:
            # 월별 → 12기 lag
            yoyLag = 12
        elif avgGapDays < 120:
            # 분기별 → 4기 lag
            yoyLag = 4
        else:
            # 연간 → 1기 lag
            yoyLag = 1

        result = result.with_columns(
            (pl.col(valueName) - pl.col(valueName).shift(yoyLag)).alias("yoyChange"),
            (
                (pl.col(valueName) - pl.col(valueName).shift(yoyLag))
                / pl.col(valueName).shift(yoyLag).abs()
                * 100
            ).alias("yoyChangePct"),
        )

    return result


# ── 리샘플링 ──


def resampleToQuarterly(df: pl.DataFrame, *, valueName: str = "value", method: str = "last") -> pl.DataFrame:
    """시계열을 분기별로 리샘플링.

    Args:
        method: "last" (기말값), "mean" (평균), "sum" (합계).
    """
    if df.is_empty() or valueName not in df.columns:
        return df

    df = df.sort("date")

    agg_expr = {
        "last": pl.col(valueName).last(),
        "mean": pl.col(valueName).mean(),
        "sum": pl.col(valueName).sum(),
    }[method]

    return (
        df.with_columns(pl.col("date").cast(pl.Date))
        .group_by_dynamic("date", every="1q")
        .agg(agg_expr)
        .sort("date")
    )


def resampleToAnnual(df: pl.DataFrame, *, valueName: str = "value", method: str = "last") -> pl.DataFrame:
    """시계열을 연간으로 리샘플링.

    Args:
        method: "last" (기말값), "mean" (평균), "sum" (합계).
    """
    if df.is_empty() or valueName not in df.columns:
        return df

    df = df.sort("date")

    agg_expr = {
        "last": pl.col(valueName).last(),
        "mean": pl.col(valueName).mean(),
        "sum": pl.col(valueName).sum(),
    }[method]

    return (
        df.with_columns(pl.col("date").cast(pl.Date))
        .group_by_dynamic("date", every="1y")
        .agg(agg_expr)
        .sort("date")
    )


# ── Parquet 영구 캐시 ──


def saveMacroParquet(indicatorId: str, df: pl.DataFrame, *, source: str = "ecos") -> Path:
    """거시지표 시계열을 Parquet으로 영구 저장.

    Args:
        indicatorId: 지표 ID (예: "GDP", "CPI").
        source: "ecos" 또는 "fred".

    Returns:
        저장된 파일 경로.
    """
    dirPath = _CACHE_DIR / source
    dirPath.mkdir(parents=True, exist_ok=True)
    path = dirPath / f"{indicatorId}.parquet"
    df.write_parquet(path)
    log.debug("Parquet 저장: %s (%d rows)", path, len(df))
    return path


def loadMacroParquet(indicatorId: str, *, source: str = "ecos") -> pl.DataFrame | None:
    """Parquet 영구 캐시에서 거시지표 로드.

    Returns:
        DataFrame 또는 None (캐시 없음).
    """
    path = _CACHE_DIR / source / f"{indicatorId}.parquet"
    if not path.exists():
        return None
    try:
        return pl.read_parquet(path)
    except Exception:
        log.warning("Parquet 읽기 실패: %s", path)
        return None


def enrichAndCache(
    indicatorId: str,
    df: pl.DataFrame,
    *,
    source: str = "ecos",
    valueName: str = "value",
) -> pl.DataFrame:
    """변화율 추가 + Parquet 저장을 한 번에 처리.

    Args:
        indicatorId: 지표 ID.
        df: raw ``(date, value)`` DataFrame.
        source: "ecos" 또는 "fred".

    Returns:
        변화율이 추가된 DataFrame.
    """
    enriched = addChangeRate(df, valueName=valueName)
    saveMacroParquet(indicatorId, enriched, source=source)
    return enriched


# ── 복수 지표 정렬 (재무 시계열과 맞추기) ──


def alignToFinancialPeriods(
    macroDf: pl.DataFrame,
    periods: list[str],
    *,
    valueName: str = "value",
) -> pl.DataFrame:
    """거시지표 시계열을 재무 기간에 맞춰 정렬.

    재무 기간 "2024A" → 2024년 연간 평균/기말값으로 매핑.
    재무 기간 "2024Q3" → 해당 분기 평균/기말값으로 매핑.

    Args:
        macroDf: ``(date, value, ...)`` 거시지표 DataFrame.
        periods: 재무 기간 목록 (예: ["2024A", "2023A", "2022A"]).

    Returns:
        ``(period, value)`` DataFrame.
    """
    if macroDf.is_empty():
        return pl.DataFrame({"period": periods, "value": [None] * len(periods)})

    rows: list[dict] = []
    df = macroDf.sort("date")

    for period in periods:
        year = int(period[:4])

        if "Q" in period:
            q = int(period[-1])
            startMonth = (q - 1) * 3 + 1
            endMonth = q * 3
            from datetime import date

            startDate = date(year, startMonth, 1)
            if endMonth == 12:
                endDate = date(year, 12, 31)
            else:
                endDate = date(year, endMonth + 1, 1)

            mask = (pl.col("date") >= startDate) & (pl.col("date") < endDate)
        else:
            # 연간 ("2024A" 또는 "2024")
            from datetime import date

            startDate = date(year, 1, 1)
            endDate = date(year + 1, 1, 1)
            mask = (pl.col("date") >= startDate) & (pl.col("date") < endDate)

        subset = df.filter(mask)
        if subset.is_empty():
            rows.append({"period": period, "value": None})
        else:
            val = subset.get_column(valueName)[-1]  # 기말값
            rows.append({"period": period, "value": val})

    return pl.DataFrame(rows)
