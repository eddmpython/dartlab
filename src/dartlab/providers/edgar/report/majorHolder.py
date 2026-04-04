"""주요 주주 추출 — XBRL + 10-K Item 12."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractMajorHolder(company: "Company") -> pl.DataFrame | None:
    """주요 주주 정보 추출."""
    from dartlab.providers.edgar.report import loadXbrlTags

    df = loadXbrlTags(
        company,
        "(?i)CommonStockSharesOutstanding|EntityPublicFloat|"
        "SharesOutstanding|EntityCommonStockSharesOutstanding",
        forms=["10-K", "10-Q", "20-F"],
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
            if "sharesoutstanding" in tag:
                record.setdefault("sharesOutstanding", val)
            elif "publicfloat" in tag:
                record.setdefault("publicFloat", val)

        if len(record) > 1:
            records.append(record)

    return pl.DataFrame(records) if records else None
