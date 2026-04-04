"""감사의견 추출 — XBRL AuditFees + 10-K 감사보고서 섹션."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def extractAuditOpinion(company: "Company") -> pl.DataFrame | None:
    """감사의견 + 감사법인 + 감사비용 추출."""
    from dartlab.providers.edgar.report import loadXbrlTags

    df = loadXbrlTags(company, "(?i)Auditor|AuditFee")
    if df is None:
        return None

    records: list[dict] = []
    for fy in df["fy"].unique().drop_nulls().sort().to_list():
        fyRows = df.filter(pl.col("fy") == fy)
        record: dict = {"period": str(fy)}

        for row in fyRows.iter_rows(named=True):
            tag = str(row.get("tag") or "").lower()
            val = row.get("val")
            label = row.get("label") or ""

            if "auditorname" in tag:
                record["auditorName"] = label if not val else str(val)
            elif "auditorlocation" in tag:
                record["auditorLocation"] = label if not val else str(val)
            elif "auditfee" in tag and "non" not in tag:
                record["auditFees"] = val
            elif "nonaudit" in tag or "allotherfees" in tag:
                record["nonAuditFees"] = val

        if len(record) > 1:
            records.append(record)

    return pl.DataFrame(records) if records else None
