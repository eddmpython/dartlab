"""사채/부채 구조 추출 — XBRL LongTermDebt, DebtInstrument 태그."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company

_DEBT_TAGS = [
    "LongTermDebt",
    "LongTermDebtNoncurrent",
    "ShortTermBorrowings",
    "CommercialPaper",
    "DebtInstrumentFaceAmount",
    "DebtInstrumentInterestRateStatedPercentage",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive",
]


def extractCorporateBond(company: "Company") -> pl.DataFrame | None:
    """사채/부채 구조 추출."""
    from dartlab.providers.edgar.report import edgarFinancePath

    cik = getattr(company, "cik", None)
    if not cik:
        return None

    path = edgarFinancePath(cik)
    if not path.exists():
        return None

    try:
        # 태그 패턴으로 필터
        tagPattern = "|".join(f"(?i){t}" for t in _DEBT_TAGS[:5])
        df = (
            pl.scan_parquet(path)
            .filter(
                pl.col("tag").str.contains(f"(?i)LongTermDebt|ShortTermBorrow|CommercialPaper|DebtInstrument")
                & pl.col("form").is_in(["10-K", "10-Q", "20-F"])
            )
            .collect()
        )

        if df.is_empty():
            return None

        records: list[dict] = []
        for fy in df["fy"].unique().drop_nulls().sort().to_list():
            fyRows = df.filter(pl.col("fy") == fy)
            record: dict = {"period": str(fy)}

            for row in fyRows.sort("filed", descending=True).iter_rows(named=True):
                tag = str(row.get("tag") or "")
                val = row.get("val")
                if val is None:
                    continue

                tagLower = tag.lower()
                if "longtermdebt" in tagLower and "maturity" not in tagLower:
                    record.setdefault("longTermDebt", val)
                elif "shorttermborrowings" in tagLower or "commercialpaper" in tagLower:
                    record.setdefault("shortTermDebt", val)
                elif "faceamount" in tagLower:
                    record.setdefault("faceAmount", val)
                elif "interestratestate" in tagLower:
                    record.setdefault("interestRate", val)

            if len(record) > 1:
                records.append(record)

        return pl.DataFrame(records) if records else None
    except (pl.exceptions.ComputeError, OSError):
        return None
