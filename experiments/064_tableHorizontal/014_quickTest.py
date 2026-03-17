"""Quick test of patched _horizontalizeTableBlock."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import re
import polars as pl
from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.company import Company

def _isPeriodCol(c):
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))

# Test riskDerivative 000020
c = Company("000020")
sec = c.docs.sections
periodCols = [col for col in sec.columns if _isPeriodCol(col)]
topicFrame = sec.filter(pl.col("topic") == "riskDerivative")

for bo in [1, 3, 5]:
    result = c._horizontalizeTableBlock(topicFrame, bo, periodCols)
    if result is not None:
        print(f"riskDerivative bo={bo}: {result.height}행 × {len([c2 for c2 in result.columns if _isPeriodCol(c2)])}기간")
        print(result.head(5))
    else:
        print(f"riskDerivative bo={bo}: None")

# Test salesOrder 000270
print("\n" + "=" * 50)
c2 = Company("000270")
sec2 = c2.docs.sections
periodCols2 = [col for col in sec2.columns if _isPeriodCol(col)]
topicFrame2 = sec2.filter(pl.col("topic") == "salesOrder")

for bo in [1, 3]:
    result2 = c2._horizontalizeTableBlock(topicFrame2, bo, periodCols2)
    if result2 is not None:
        print(f"salesOrder 000270 bo={bo}: {result2.height}행 × {len([c2 for c2 in result2.columns if _isPeriodCol(c2)])}기간")
        print(result2.head(5))
    else:
        print(f"salesOrder 000270 bo={bo}: None")

# Test dividend KB금융
print("\n" + "=" * 50)
c3 = Company("105560")
sec3 = c3.docs.sections
periodCols3 = [col for col in sec3.columns if _isPeriodCol(col)]
topicFrame3 = sec3.filter(pl.col("topic") == "dividend")
bos = sorted(topicFrame3.filter(pl.col("blockType") == "table")["blockOrder"].unique().to_list())
for bo in bos[:3]:
    result3 = c3._horizontalizeTableBlock(topicFrame3, bo, periodCols3)
    if result3 is not None:
        print(f"dividend 105560 bo={bo}: {result3.height}행 × {len([c2 for c2 in result3.columns if _isPeriodCol(c2)])}기간")
    else:
        print(f"dividend 105560 bo={bo}: None")
