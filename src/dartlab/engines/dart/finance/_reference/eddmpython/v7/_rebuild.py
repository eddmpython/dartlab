"""Rebuild prepared.parquet without hierarchy (temporary fix)"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

import polars as pl
from core.dart.searchDart.finance.v6.search import FinanceSearch

fs = FinanceSearch()
preparedPath = fs._cacheDir / fs.PREPARED_FILENAME

rawLf = fs._buildRawLf()
rawLf = rawLf.filter(pl.col("bsns_year") != "2015")

nameToIdDf, idToNameDf = fs._buildMappingTables(rawLf)
lf = fs._applyNormalization(rawLf, nameToIdDf, idToNameDf)
lf = fs._applyCfsPriority(lf)
lf = fs._normalizeQ4(lf)
lf = fs._addPeriodColumn(lf)

df = lf.collect()
print(f"Prepared df: {df.shape}")

fs._ensureCacheDir()
df.write_parquet(preparedPath)
print(f"Saved to {preparedPath}")

# mtime을 원본보다 새롭게 설정하여 rebuild 방지
import os

financeDir = fs._financeDir
parquets = list(financeDir.glob("*.parquet"))
if parquets:
    maxMtime = max(f.stat().st_mtime for f in parquets)
    newTime = maxMtime + 10
    os.utime(preparedPath, (newTime, newTime))
    print("Updated mtime to prevent rebuild")
