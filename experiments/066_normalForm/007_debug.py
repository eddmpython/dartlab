"""빠른 디버그: 왜 0% 인지."""
import re, sys
from collections import defaultdict
from dataclasses import dataclass, field
import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables, _headerCells, _isJunk, _dataRows, _normalizeHeader,
)
from dartlab.engines.dart.docs.sections.pipeline import sections as buildSections

code = "005930"  # 삼성전자
sec = buildSections(code)

meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
table_rows = sec.filter(pl.col("blockType") == "table")
topics = table_rows["topic"].unique().to_list()
period_cols = sorted([
    col for col in table_rows.columns
    if col not in meta_cols and re.match(r"\d{4}", col)
])

print(f"topics: {len(topics)}, periods: {len(period_cols)}")
print(f"columns: {table_rows.columns[:10]}")

# dividend 확인
topic = "dividend"
tt = table_rows.filter(pl.col("topic") == topic)
print(f"\n{topic}: {tt.height} rows, {tt.columns}")

# 첫 기간 확인
p = period_cols[-1]
print(f"\n기간 {p}:")
for ri in range(tt.height):
    md = tt[p][ri]
    if md is None:
        print(f"  row {ri}: None")
    else:
        md_str = str(md)
        subs = splitSubtables(md_str)
        print(f"  row {ri}: {len(subs)} subs, md[:80]={md_str[:80]}")
        for si, sub in enumerate(subs[:2]):
            hc = _headerCells(sub)
            dr = _dataRows(sub)
            print(f"    sub[{si}]: hc={hc[:3]}, isJunk={_isJunk(hc)}, dr={len(dr)}")
            if hc:
                print(f"      headers joined: {'|'.join(hc[:4])}")
                print(f"      multi_year check: {any(kw in ' '.join(hc) for kw in {'당기','전기','전전기'})}")
