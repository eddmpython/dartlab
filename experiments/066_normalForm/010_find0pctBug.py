"""006의 hzTopic를 삼성전자 dividend에 직접 호출하여 0% 원인 확인."""
import re, sys
from collections import defaultdict
from dataclasses import dataclass, field
import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

# 006의 코드를 그대로 exec로 로드
import importlib.util
spec = importlib.util.spec_from_file_location(
    "fastbench",
    "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/experiments/066_normalForm/006_fastBench.py",
)
mod = importlib.util.module_from_spec(spec)

# main 실행 방지
import unittest.mock
with unittest.mock.patch.object(mod, '__name__', 'not_main'):
    spec.loader.exec_module(mod)

from dartlab.engines.dart.docs.sections.pipeline import sections as buildSections

code = "005930"
sec = buildSections(code)
meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
table_rows = sec.filter(pl.col("blockType") == "table")
period_cols = sorted([
    col for col in table_rows.columns
    if col not in meta_cols and re.match(r"\d{4}", col)
])

topic = "dividend"
tt = table_rows.filter(pl.col("topic") == topic)

print(f"Testing 006's hzTopic on dividend...")
try:
    results = mod.hzTopic(tt, period_cols)
    print(f"  결과: {len(results)} DataFrames")
    for i, df in enumerate(results):
        print(f"  [{i}]: {df.shape}")
        print(df.head(3))
except Exception as e:
    import traceback
    print(f"  에러: {e}")
    traceback.print_exc()
