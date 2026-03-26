"""sections 패키지 공용 상수와 유틸리티."""

from __future__ import annotations

import re

import polars as pl

REPORT_KINDS: list[tuple[str, str]] = [
    ("annual", ""),
    ("Q1", "Q1"),
    ("semi", "Q2"),
    ("Q3", "Q3"),
]

RE_SPLIT_SUFFIX = re.compile(r" \[\d+/\d+\]$")
RE_PERIOD = re.compile(r"^\d{4}(Q[1-4])?$")
RE_ANNUAL_Q4_ALIAS = re.compile(r"^(\d{4})Q4$")


def detectContentCol(df: pl.DataFrame) -> str:
    if "section_content" in df.columns:
        return "section_content"
    return "content"


def periodSortKey(period: str) -> tuple[int, int]:
    value = str(period)
    if "Q" in value:
        return int(value[:4]), int(value[-1])
    return int(value), 4


def sortPeriods(periods: list[str], *, descending: bool = False) -> list[str]:
    return sorted(periods, key=periodSortKey, reverse=descending)


def periodOrderValue(period: str) -> int:
    year, slot = periodSortKey(period)
    return year * 10 + slot


def basePath(path: str) -> str:
    return RE_SPLIT_SUFFIX.sub("", path)


def rawPeriod(period: str) -> str:
    value = str(period).strip()
    match = RE_ANNUAL_Q4_ALIAS.fullmatch(value)
    if match:
        return match.group(1)
    return value


def displayPeriod(period: str, *, annualAsQ4: bool = False) -> str:
    value = rawPeriod(period)
    if annualAsQ4 and RE_PERIOD.fullmatch(value) and "Q" not in value:
        return f"{value}Q4"
    return value


def periodColumns(
    columns: list[str],
    *,
    descending: bool = False,
    annualAsQ4: bool = False,
) -> list[str]:
    ordered = sortPeriods([str(col) for col in columns if RE_PERIOD.fullmatch(str(col))], descending=descending)
    return [displayPeriod(period, annualAsQ4=annualAsQ4) for period in ordered]


def formatPeriodRange(
    periods: list[str],
    *,
    descending: bool = False,
    annualAsQ4: bool = False,
) -> str:
    ordered = sortPeriods([rawPeriod(period) for period in periods], descending=descending)
    if not ordered:
        return "-"
    labels = [displayPeriod(period, annualAsQ4=annualAsQ4) for period in ordered]
    return f"{labels[0]}..{labels[-1]}" if len(labels) > 1 else labels[0]


def reorderPeriodColumns(
    df: pl.DataFrame,
    *,
    descending: bool = False,
    annualAsQ4: bool = False,
) -> pl.DataFrame:
    periodCols = [str(col) for col in df.columns if RE_PERIOD.fullmatch(str(col))]
    if not periodCols:
        return df

    orderedPeriods = sortPeriods(periodCols, descending=descending)
    metaCols = [col for col in df.columns if col not in periodCols]
    result = df.select(metaCols + orderedPeriods)
    if not annualAsQ4:
        return result

    existing = set(result.columns)
    renameMap: dict[str, str] = {}
    for period in orderedPeriods:
        label = displayPeriod(period, annualAsQ4=True)
        if label == period:
            continue
        if label in existing and label != period:
            continue
        renameMap[period] = label
    return result.rename(renameMap) if renameMap else result
