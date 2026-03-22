"""10종목 핵심 topic 품질 검증."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.company import Company


def _isPeriodCol(c):
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))

stocks = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "네이버"),
    ("005380", "현대차"), ("068270", "셀트리온"), ("105560", "KB금융"),
    ("051910", "LG화학"), ("003550", "LG"), ("028260", "삼성물산"), ("034730", "SK"),
]
topics = ["dividend", "audit", "companyOverview", "employee", "salesOrder"]

print("10종목 핵심 5 topic 검증")
print("=" * 70)

for code, name in stocks:
    c = Company(code)
    print(f"\n--- {name} ({code}) ---")
    for topic in topics:
        result = c.show(topic)
        if result is None:
            print(f"  {topic}: show() None (topic 없음)")
            continue

        # block index
        blocks = result
        tableBlocks = blocks.filter(pl.col("type") == "table") if "type" in blocks.columns else pl.DataFrame()
        totalBlocks = blocks.height
        tableCount = tableBlocks.height

        # 각 table block 수평화 시도
        successBlocks = 0
        for row in blocks.iter_rows(named=True):
            if row.get("type") != "table":
                continue
            bo = row.get("block", row.get("blockOrder"))
            if bo is None:
                continue
            data = c.show(topic, bo)
            if data is not None:
                successBlocks += 1

        print(f"  {topic}: {totalBlocks}블록 (table {tableCount}), 수평화 {successBlocks}/{tableCount}")

        # dividend는 상세 출력
        if topic == "dividend" and tableCount > 0:
            firstTableBo = None
            for row in blocks.iter_rows(named=True):
                if row.get("type") == "table":
                    firstTableBo = row.get("block", row.get("blockOrder"))
                    break
            if firstTableBo is not None:
                data = c.show(topic, firstTableBo)
                if data is not None:
                    pCols = [col for col in data.columns if _isPeriodCol(col)]
                    recent = pCols[-3:] if len(pCols) >= 3 else pCols
                    print(f"    bo={firstTableBo}: {data.height}행 × {len(pCols)}기간")
                    if "항목" in data.columns:
                        for row in data.head(5).iter_rows(named=True):
                            item = row.get("항목", "")
                            vals = " | ".join(str(row.get(p, "")) for p in recent)
                            print(f"      {item}: {vals}")
