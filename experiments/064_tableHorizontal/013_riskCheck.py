"""Quick check: riskDerivative 000020 after strip patch."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import re

import polars as pl

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

sec = sections("000020")
periodCols = [c for c in sec.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]
topicFrame = sec.filter(pl.col("topic") == "riskDerivative")
boRow = topicFrame.filter(
    (pl.col("blockOrder") == 1) & (pl.col("blockType") == "table")
)

for p in ["2024", "2023"]:
    md = boRow[p][0] if p in boRow.columns and boRow[p][0] is not None else None
    if md is None:
        continue
    print(f"\n=== {p} ===")
    for sub in splitSubtables(str(md)):
        hc = _headerCells(sub)
        print(f"header: {hc}, classify: {_classifyStructure(hc)}")

        # Try strip
        fixed = Company._stripUnitHeader(sub)
        if fixed:
            fixedHc = _headerCells(fixed)
            fixedDr = _dataRows(fixed)
            print(f"  FIXED header: {fixedHc}, classify: {_classifyStructure(fixedHc)}, dataRows: {len(fixedDr)}")
            if _classifyStructure(fixedHc) == "multi_year":
                triples, _ = _parseMultiYear(fixed, int(p[:4]))
                print(f"  multi_year triples: {len(triples)}")
                for t in triples[:5]:
                    print(f"    {t}")
            elif _classifyStructure(fixedHc) in ("key_value", "matrix"):
                rows, hn, _ = _parseKeyValueOrMatrix(fixed)
                print(f"  kv/matrix items: {len(rows)}, headers: {hn}")
                for item, vals in rows[:5]:
                    print(f"    {item}: {vals[:3]}")
    break
