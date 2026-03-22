"""Quick regression check: companyOverview -3."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.core.dataLoader import _dataDir
from dartlab.engines.company.dart.company import Company
from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


def _isPeriodCol(c):
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))

dataDir = _dataDir("docs")
files = sorted(dataDir.glob("*.parquet"))
codes = [f.stem for f in files]

# Find companyOverview regressions: was success, now None
regressions = []
for i, code in enumerate(codes):
    try:
        sec = sections(code)
    except Exception:
        continue
    if sec is None:
        continue
    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topicFrame = sec.filter(pl.col("topic") == "companyOverview")
    tableRows = topicFrame.filter(pl.col("blockType") == "table")
    if tableRows.is_empty():
        continue

    c = Company(code)
    blockOrders = sorted(tableRows["blockOrder"].unique().to_list())
    for bo in blockOrders:
        boRow = topicFrame.filter(
            (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
        )

        # Old logic (no strip, no fallback)
        oldItems = set()
        for p in periodCols:
            md = boRow[p][0] if p in boRow.columns else None
            if md is None:
                continue
            m = re.match(r"\d{4}", p)
            if m is None:
                continue
            pYear = int(m.group())
            for sub in splitSubtables(str(md)):
                hc = _headerCells(sub)
                if _isJunk(hc):
                    continue
                dr = _dataRows(sub)
                if not dr:
                    continue
                st = _classifyStructure(hc)
                if st == "multi_year" and "Q" not in p:
                    triples, _ = _parseMultiYear(sub, pYear)
                    for item, year, val in triples:
                        if year == str(pYear):
                            oldItems.add(item)
                elif st in ("key_value", "matrix"):
                    rows, _, _ = _parseKeyValueOrMatrix(sub)
                    for item, vals in rows:
                        if vals:
                            oldItems.add(item)

        oldSuccess = len(oldItems) > 0

        # New logic
        result = c._horizontalizeTableBlock(topicFrame, bo, periodCols)
        newSuccess = result is not None

        if oldSuccess and not newSuccess:
            regressions.append({"code": code, "bo": bo, "oldItems": len(oldItems)})

    if (i + 1) % 50 == 0:
        print(f"  [{i+1}/{len(codes)}]...")

print(f"\ncompanyOverview regressions: {len(regressions)}")
for r in regressions[:10]:
    print(f"  {r['code']} bo={r['bo']} oldItems={r['oldItems']}")
