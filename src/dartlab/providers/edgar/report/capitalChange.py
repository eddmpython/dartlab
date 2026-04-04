"""증자/감자 이력 추출 — XBRL 주식 발행/소각 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractCapitalChange(company: "Company") -> pl.DataFrame | None:
    """주식 발행/소각 이력 추출."""
    from dartlab.providers.edgar.report import loadXbrlTags

    df = loadXbrlTags(
        company,
        "(?i)CommonStockSharesIssued|StockIssuedDuringPeriod|"
        "StockRepurchas|TreasuryStockSharesAcquired|"
        "StockRepurchaseProgramAuthorizedAmount",
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
            if "sharesoutstanding" in tag or "commonstocksharesiss" in tag:
                record.setdefault("sharesIssued", val)
            elif "repurchas" in tag and "amount" in tag:
                record.setdefault("repurchaseAuthorized", val)
            elif "repurchas" in tag and "shares" in tag:
                record.setdefault("sharesRepurchased", val)
            elif "treasurystockshares" in tag:
                record.setdefault("treasurySharesAcquired", val)

        if len(record) > 1:
            records.append(record)

    return pl.DataFrame(records) if records else None
