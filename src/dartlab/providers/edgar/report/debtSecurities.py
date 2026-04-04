"""채무증권 현황 추출 — XBRL Debt Securities 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractDebtSecurities(company: "Company") -> pl.DataFrame | None:
    """채무증권 발행/보유 현황 추출."""
    from dartlab.providers.edgar.report import loadXbrlTags

    df = loadXbrlTags(
        company,
        "(?i)DebtSecurities|AvailableForSaleDebt|HeldToMaturitySecurities|"
        "CommercialPaper|ShortTermBorrowings|ShortTermDebt",
        unitFilter="(?i)USD",
    )
    if df is None:
        return None

    records: list[dict] = []
    for fy in df["fy"].unique().drop_nulls().sort().to_list():
        fyRows = df.filter(pl.col("fy") == fy).sort("filed", descending=True)
        record: dict = {"period": str(fy)}

        for row in fyRows.iter_rows(named=True):
            tag = str(row.get("tag") or "").lower()
            val = row.get("val")
            if val is None:
                continue
            if "commercialpaper" in tag and "proceeds" not in tag:
                record.setdefault("commercialPaper", val)
            elif "shorttermdebt" in tag or "shorttermborrowings" in tag:
                record.setdefault("shortTermDebt", val)
            elif "availableforsaledebt" in tag:
                record.setdefault("availableForSaleDebt", val)
            elif "heldtomaturity" in tag:
                record.setdefault("heldToMaturity", val)

        if len(record) > 1:
            records.append(record)

    return pl.DataFrame(records) if records else None
