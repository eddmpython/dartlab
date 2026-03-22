"""267 종목 원재료/생산설비 전체 파서 테스트."""

import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

# 003f에서 파서 함수만 로드
_parserPath = os.path.join(os.path.dirname(__file__), "003f_improvedParser.py")
with open(_parserPath, encoding="utf-8") as _f:
    _code = _f.read()
# STOCKS 이후 테스트 코드를 제거
_cutoff = _code.find("\nSTOCKS = [")
if _cutoff > 0:
    _code = _code[:_cutoff]
# sys.stdout 재설정 코드 제거
_code = _code.replace('sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")', '')
_ns = {"__name__": "_parser_import_", "re": re, "sys": sys, "io": io}
exec(compile(_code, _parserPath, "exec"), _ns)

parseRawMaterials = _ns["parseRawMaterials"]
parseEquipment = _ns["parseEquipment"]
parseCapex = _ns["parseCapex"]

dataDir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docsData")
files = sorted(f for f in os.listdir(dataDir) if f.endswith(".parquet"))

rawOk = rawFail = rawNa = 0
eqOk = eqFail = eqNa = 0
capOk = capFail = capNa = 0
errors = []
rawDetails = []
eqDetails = []

for f in files:
    code = f.replace(".parquet", "")
    try:
        df = loadData(code)
    except Exception:
        rawNa += 1; eqNa += 1; capNa += 1
        continue

    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        rawNa += 1; eqNa += 1; capNa += 1
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        rawNa += 1; eqNa += 1; capNa += 1
        continue

    rawResult = eqResult = capResult = None
    try:
        for i in range(sections.height):
            c = sections["section_content"][i]
            if rawResult is None:
                rawResult = parseRawMaterials(c)
            if eqResult is None:
                eqResult = parseEquipment(c)
            if capResult is None:
                capResult = parseCapex(c)
    except Exception as e:
        errors.append((code, str(e)))
        continue

    if rawResult:
        rawOk += 1
        rawDetails.append((code, len(rawResult)))
    else:
        rawFail += 1

    if eqResult:
        eqOk += 1
        eqDetails.append((code, "total" in eqResult, eqResult.get("total")))
    else:
        eqFail += 1

    if capResult:
        capOk += 1
    else:
        capFail += 1


total = len(files)
hasSection = total - rawNa

print(f"{'='*60}")
print(f"  원재료/생산설비 전체 종목 테스트 결과")
print(f"{'='*60}")
print(f"  전체 종목:     {total}")
print(f"  섹션 있음:     {hasSection}")
print(f"  섹션 없음:     {rawNa}")
print()
print(f"  원재료 파싱:   {rawOk}/{hasSection} ({rawOk/hasSection*100:.1f}%)")
print(f"  생산설비 파싱: {eqOk}/{hasSection} ({eqOk/hasSection*100:.1f}%)")
print(f"  시설투자 파싱: {capOk}/{hasSection} ({capOk/hasSection*100:.1f}%)")
print()

if errors:
    print(f"  에러: {len(errors)}건")
    for code, msg in errors[:10]:
        print(f"    {code}: {msg}")
    print()

if rawDetails:
    rawDetails.sort(key=lambda x: x[1], reverse=True)
    print(f"  원재료 항목수 상위:")
    for code, n in rawDetails[:5]:
        print(f"    {code}: {n}건")
    print()

noTotal = [(code, hasT) for code, hasT, tot in eqDetails if not hasT]
if noTotal:
    print(f"  생산설비 total 없음: {len(noTotal)}건")
    for code, _ in noTotal[:10]:
        print(f"    {code}")
