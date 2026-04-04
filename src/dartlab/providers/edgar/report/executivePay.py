"""임원 보수 추출 — XBRL 보상 관련 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractExecutivePay(company: "Company") -> pl.DataFrame | None:
    """임원 보수 관련 XBRL 데이터 추출.

    현재: XBRL 태그에서 추출 가능한 범위 (제한적).
    향후: DEF 14A proxy statement 수집 시 Summary Compensation Table 파싱.
    """
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
                    "(?i)ShareBasedCompensation|StockBasedCompensation|"
                    "AllocatedShareBasedCompensationExpense|"
                    "DefinedBenefitPlanNetPeriodicBenefitCost"
                )
                & pl.col("form").is_in(["10-K", "20-F"])
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
                if "stockbasedcompensation" in tag or "sharebasedcompensation" in tag:
                    record.setdefault("stockBasedCompensation", val)
                elif "definedbenefit" in tag:
                    record.setdefault("pensionCost", val)

            if len(record) > 1:
                records.append(record)

        return pl.DataFrame(records) if records else None
    except (pl.exceptions.ComputeError, OSError):
        return None
