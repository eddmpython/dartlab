"""실패 종목 심층 분석 — 매입액 테이블이 진짜 있는지."""

import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

dataDir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docsData")
files = sorted(f for f in os.listdir(dataDir) if f.endswith(".parquet"))

# 003f 파서 로드
_parserPath = os.path.join(os.path.dirname(__file__), "003f_improvedParser.py")
with open(_parserPath, encoding="utf-8") as _f:
    _code = _f.read()
_cutoff = _code.find("\nSTOCKS = [")
if _cutoff > 0:
    _code = _code[:_cutoff]
_code = _code.replace('sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")', '')
_ns = {"__name__": "_p_", "re": re, "sys": sys, "io": io}
exec(compile(_code, _parserPath, "exec"), _ns)
parseRawMaterials = _ns["parseRawMaterials"]

# 분류: 매입액 테이블이 있는데 파싱 실패 vs 매입액 테이블 자체가 없음
hasPurchaseTable = 0
noPurchaseTable = 0
failedWithTable = []
failedTypes = {}

for f in files:
    code = f.replace(".parquet", "")
    try:
        df = loadData(code)
    except Exception:
        continue

    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        continue

    # 이미 파싱 성공하면 skip
    for si in range(sections.height):
        c = sections["section_content"][si]
        if parseRawMaterials(c) is not None:
            break
    else:
        # 파싱 실패 — 매입액 관련 테이블이 있는지 확인
        hasTable = False
        tableType = "none"
        for si in range(sections.height):
            c = sections["section_content"][si]
            for line in c.split("\n"):
                s = line.strip()
                if s.startswith("|") and "---" not in s:
                    cells = [c2.strip() for c2 in s.split("|") if c2.strip()]
                    joined = " ".join(cells)
                    # 매입액이 헤더에 있는 경우
                    if "매입액" in joined or "매입금액" in joined or "투입액" in joined:
                        hasTable = True
                        tableType = "매입액헤더"
                        break
                    # "매입액 비율" 반복 패턴 (연도별)
                    if joined.count("매입") >= 2:
                        hasTable = True
                        tableType = "연도별매입"
                        break
                    # 금액 컬럼이 있는 원재료 관련 테이블
                    if ("금액" in joined) and ("원재료" in joined or "원부재료" in joined or "품목" in joined):
                        hasTable = True
                        tableType = "금액헤더"
                        break
            if hasTable:
                break

        if hasTable:
            hasPurchaseTable += 1
            failedWithTable.append((code, tableType))
            if tableType not in failedTypes:
                failedTypes[tableType] = 0
            failedTypes[tableType] += 1
        else:
            noPurchaseTable += 1

print(f"=== 원재료 파싱 실패 종목 분석 ===")
print(f"  매입 테이블 있는데 실패: {hasPurchaseTable}건")
print(f"  매입 테이블 자체 없음:   {noPurchaseTable}건")
print()
print(f"  실패 유형:")
for t, cnt in sorted(failedTypes.items(), key=lambda x: -x[1]):
    print(f"    {t}: {cnt}건")
print()

# 매입액헤더 있는 실패 종목 샘플
print(f"=== 매입액 헤더 있는 실패 종목 샘플 ===")
for code, ttype in failedWithTable[:10]:
    df = loadData(code)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )
    print(f"\n  {code} ({ttype})")
    for si in range(sections.height):
        c = sections["section_content"][si]
        for line in c.split("\n"):
            s = line.strip()
            if s.startswith("|") and "---" not in s:
                cells = [c2.strip() for c2 in s.split("|") if c2.strip()]
                joined = " ".join(cells)
                if "매입" in joined or "투입" in joined or "금액" in joined:
                    print(f"    {joined[:100]}")
                    break
        else:
            continue
        break
