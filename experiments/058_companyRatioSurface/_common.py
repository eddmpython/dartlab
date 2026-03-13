from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


FINANCIAL_KEYWORDS: tuple[str, ...] = (
    "금융",
    "은행",
    "보험",
    "증권",
    "저축",
    "신탁",
    "투자업",
    "캐피탈",
)


def isFinancialIndustry(industry: str | None) -> bool:
    if not industry:
        return False
    return any(keyword in industry for keyword in FINANCIAL_KEYWORDS)


def kindMeta() -> dict[str, dict[str, Any]]:
    from dartlab.core.kindList import getKindList

    kind = getKindList()
    codeCol, nameCol, marketCol, industryCol, listedCol = (
        kind.columns[2],
        kind.columns[0],
        kind.columns[1],
        kind.columns[3],
        kind.columns[5],
    )
    return {
        row[codeCol]: {
            "corpName": row[nameCol],
            "market": row[marketCol],
            "industry": row[industryCol],
            "listedAt": row[listedCol],
        }
        for row in kind.iter_rows(named=True)
    }


def localFinanceCodes(limit: int | None = None) -> list[str]:
    from dartlab.core.dataLoader import _dataDir

    files = sorted(Path(_dataDir("finance")).glob("*.parquet"))
    codes = [f.stem for f in files]
    return codes if limit is None else codes[:limit]


def ratioSurfaceFrame(code: str) -> tuple[pl.DataFrame | None, int | None]:
    from dartlab.engines.common.finance.ratios import calcRatioSeries, toSeriesDict
    from dartlab.engines.dart.company import _ratioSeriesToDataFrame
    from dartlab.engines.dart.finance.pivot import buildAnnual

    annual = buildAnnual(code)
    if annual is None:
        return None, None

    annualSeries, years = annual
    rs = calcRatioSeries(annualSeries, years)
    series, years = toSeriesDict(rs)
    df = _ratioSeriesToDataFrame(series, years)
    return df, len(years)


def classifyStatus(
    *,
    rowCount: int | None,
    yearCount: int | None,
    industry: str | None,
    listedAt: str | None,
    corpName: str | None,
) -> str:
    if rowCount is None:
        if listedAt:
            year = int(str(listedAt)[:4])
            if year >= 2024:
                return "원천공백-신규상장"
        if corpName is None:
            return "원천공백-메타부재"
        return "원천공백"

    if yearCount is not None and yearCount < 5:
        if rowCount < 10 and isFinancialIndustry(industry):
            return "금융업 정상 축소"
        return "연도부족"

    if rowCount < 10:
        if isFinancialIndustry(industry):
            return "금융업 정상 축소"
        return "비금융 이상축소"

    return "정상"
