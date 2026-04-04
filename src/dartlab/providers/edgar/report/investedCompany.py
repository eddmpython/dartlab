"""타법인 출자 현황 추출 — XBRL 투자 관련 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractInvestedCompany(company: "Company") -> pl.DataFrame | None:
    """타법인 출자/투자 시계열 추출."""
    from dartlab.providers.edgar.report import loadXbrlTags

    df = loadXbrlTags(
        company,
        "(?i)EquityMethodInvestment|InvestmentsInAffiliates|"
        "LongTermInvestments|AvailableForSaleSecurities|"
        "HeldToMaturitySecurities|MarketableSecurities",
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
            if "equitymethod" in tag:
                record.setdefault("equityMethodInvestments", val)
            elif "availableforsale" in tag:
                record.setdefault("availableForSale", val)
            elif "heldtomaturity" in tag:
                record.setdefault("heldToMaturity", val)
            elif "marketable" in tag:
                record.setdefault("marketableSecurities", val)
            elif "longterminvestment" in tag:
                record.setdefault("longTermInvestments", val)

        if len(record) > 1:
            records.append(record)

    return pl.DataFrame(records) if records else None
