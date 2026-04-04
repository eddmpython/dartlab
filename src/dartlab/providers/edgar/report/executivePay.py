"""임원 보수 추출 — XBRL 보상 관련 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractExecutivePay(company: "Company") -> pl.DataFrame | None:
    """임원 보수 관련 XBRL 데이터 추출."""
    from dartlab.providers.edgar.report import loadXbrlTags

    df = loadXbrlTags(
        company,
        "(?i)ShareBasedCompensation|StockBasedCompensation|"
        "AllocatedShareBasedCompensationExpense|"
        "DefinedBenefitPlanNetPeriodicBenefitCost",
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
            if "stockbasedcompensation" in tag or "sharebasedcompensation" in tag:
                record.setdefault("stockBasedCompensation", val)
            elif "definedbenefit" in tag:
                record.setdefault("pensionCost", val)

        if len(record) > 1:
            records.append(record)

    return pl.DataFrame(records) if records else None
