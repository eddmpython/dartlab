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
