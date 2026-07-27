"""재무비율 4 그룹 — 수익성/안정성/효율성/성장성."""

from __future__ import annotations

import polars as pl

from dartlab.synth.rowAccess import safeDiv
from dartlab.viz.display.finance.accounts import extractSeries
from dartlab.viz.display.finance.periods import lastNPeriods
from dartlab.viz.display.finance.schema import PeriodKind


def _pct(x: float | None) -> float | None:
    """× 100 None-safe."""
    return x * 100 if x is not None else None


def profitability(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """ROE / ROA / GPM / OPM / NPM."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    rev = extractSeries(norm, "revenue", periods)
    gp = extractSeries(norm, "grossProfit", periods)
    cos = extractSeries(norm, "costOfSales", periods)
    op = extractSeries(norm, "operatingIncome", periods)
    ni = extractSeries(norm, "netIncome", periods)
    assets = extractSeries(norm, "assets", periods)
    eq = extractSeries(norm, "equity", periods)

    def _gpAt(i: int) -> float | None:
        """매출총이익 보정."""
        if gp[i] is not None:
            return gp[i]
        if rev[i] is not None and cos[i] is not None:
            return rev[i] - cos[i]
        return None

    return {
        "periods": periods,
        "roe": [_pct(safeDiv(ni[i], eq[i])) for i in range(len(periods))],
        "roa": [_pct(safeDiv(ni[i], assets[i])) for i in range(len(periods))],
        "gpm": [_pct(safeDiv(_gpAt(i), rev[i])) for i in range(len(periods))],
        "opm": [_pct(safeDiv(op[i], rev[i])) for i in range(len(periods))],
        "npm": [_pct(safeDiv(ni[i], rev[i])) for i in range(len(periods))],
    }


def stability(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """유동비율 / 당좌비율 / 부채비율 / 자기자본비율."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    curA = extractSeries(norm, "currentAssets", periods)
    curL = extractSeries(norm, "currentLiabilities", periods)
    liab = extractSeries(norm, "liabilities", periods)
    eq = extractSeries(norm, "equity", periods)
    assets = extractSeries(norm, "assets", periods)
    cash = extractSeries(norm, "cash", periods)
    rec = extractSeries(norm, "receivables", periods)

    def _quick(i: int) -> float | None:
        """당좌비율 = (현금+매출채권) / 유동부채."""
        num = (cash[i] or 0) + (rec[i] or 0) if curL[i] else None
        return _pct(safeDiv(num, curL[i]))

    return {
        "periods": periods,
        "currentRatio": [_pct(safeDiv(curA[i], curL[i])) for i in range(len(periods))],
        "quickRatio": [_quick(i) for i in range(len(periods))],
        "cashRatio": [_pct(safeDiv(cash[i], curL[i])) for i in range(len(periods))],
        "debtRatio": [_pct(safeDiv(liab[i], eq[i])) for i in range(len(periods))],
        "equityRatio": [_pct(safeDiv(eq[i], assets[i])) for i in range(len(periods))],
    }


def efficiency(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """자산회전 / 재고회전 / 매출채권회전 + DSO / DIO."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    rev = extractSeries(norm, "revenue", periods)
    cos = extractSeries(norm, "costOfSales", periods)
    assets = extractSeries(norm, "assets", periods)
    inv = extractSeries(norm, "inventories", periods)
    rec = extractSeries(norm, "receivables", periods)
    assetTurn = [safeDiv(rev[i], assets[i]) for i in range(len(periods))]
    invTurn = [safeDiv(cos[i], inv[i]) for i in range(len(periods))]
    recTurn = [safeDiv(rev[i], rec[i]) for i in range(len(periods))]
    return {
        "periods": periods,
        "assetTurnover": assetTurn,
        "inventoryTurnover": invTurn,
        "receivableTurnover": recTurn,
        "dso": [safeDiv(365.0, v) for v in recTurn],
        "dio": [safeDiv(365.0, v) for v in invTurn],
    }


def growth(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """매출 YoY / 영업이익 YoY / 순이익 YoY + CAGR3y."""
    periods = lastNPeriods(norm, nPeriods + 1, periodKind)
    rev = extractSeries(norm, "revenue", periods)
    op = extractSeries(norm, "operatingIncome", periods)
    ni = extractSeries(norm, "netIncome", periods)

    def _yoy(values: list[float | None]) -> list[float | None]:
        out: list[float | None] = [None]
        for i in range(1, len(values)):
            prev, curr = values[i - 1], values[i]
            if prev is None or curr is None or prev <= 0:
                out.append(None)
            else:
                out.append((curr - prev) / prev * 100)
        return out

    revYoy = _yoy(rev)
    opYoy = _yoy(op)
    niYoy = _yoy(ni)

    cagr3y: float | None = None
    if len(periods) >= 4 and rev[-4] and rev[-4] > 0 and rev[-1] and rev[-1] > 0:
        cagr3y = ((rev[-1] / rev[-4]) ** (1 / 3) - 1) * 100

    return {
        "periods": periods[1:],
        "revenueYoy": revYoy[1:],
        "operatingYoy": opYoy[1:],
        "netIncomeYoy": niYoy[1:],
        "cagr3y": cagr3y,
    }
