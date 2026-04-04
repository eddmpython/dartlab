"""타법인 출자 현황 추출 — XBRL 투자 관련 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractInvestedCompany(company: "Company") -> pl.DataFrame | None:
    """타법인 출자/투자 시계열 추출."""
    from dartlab.providers.edgar.report import edgarFinancePath

    cik = getattr(company, "cik", None)
    if not cik:
        return None

    path = edgarFinancePath(cik)
    if not path.exists():
        return None

    try:
        df = (
            pl.scan_parquet(path)
            .filter(
                pl.col("tag").str.contains(
                    "(?i)EquityMethodInvestment|InvestmentsInAffiliates|"
                    "LongTermInvestments|AvailableForSaleSecurities|"
                    "HeldToMaturitySecurities|MarketableSecurities"
                )
                & pl.col("form").is_in(["10-K", "20-F"])
                & pl.col("unit").str.contains("(?i)USD")
            )
            .collect()
        )

        if df.is_empty():
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
    except (pl.exceptions.ComputeError, OSError):
        return None
