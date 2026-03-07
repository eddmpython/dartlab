"""실패 종목 분석 — 원재료/생산설비 섹션은 있지만 파싱 실패."""

import sys
import io
import re
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

dataDir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docsData")
files = sorted(f for f in os.listdir(dataDir) if f.endswith(".parquet"))

# 003f 파서 기본 함수
def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip().replace(",", "").replace(" ", "")
    isNeg = "△" in cleaned or "▲" in cleaned or (cleaned.startswith("(") and cleaned.endswith(")"))
    cleaned = re.sub(r"[△▲\(\)]", "", cleaned)
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned or cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNeg else val


rawFails = []
eqFails = []

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

    # 섹션 내용 분석
    for si in range(sections.height):
        title = sections["section_title"][si]
        content = sections["section_content"][si]
        lines = content.split("\n")

        # 원재료 테이블 구조 분석
        hasRawSection = False
        rawHeaders = []
        for line in lines:
            s = line.strip().replace("\xa0", " ")
            if "주요 원재료" in s and ("현황" in s or "등의 현황" in s):
                hasRawSection = True
            if s.startswith("|") and "---" not in s:
                cells = [c.strip() for c in s.split("|") if c.strip()]
                joined = " ".join(cells)
                if ("품 목" in joined or "품목" in joined) and \
                   ("매입액" in joined or "투입액" in joined or "비율" in joined or "비중" in joined):
                    rawHeaders.append(joined[:80])

        # 유형자산 헤더 분석
        eqHeaders = []
        for line in lines:
            s = line.strip().replace("\xa0", " ")
            if s.startswith("|") and "---" not in s:
                cells = [c.strip() for c in s.split("|") if c.strip()]
                joined = " ".join(cells)
                if ("토지" in joined or "기계" in joined) and ("합계" in joined or "계" in cells[-1] if cells else False):
                    eqHeaders.append(joined[:80])

        if not rawHeaders and "원재료" in title:
            rawFails.append((code, title, "원재료 테이블 헤더 없음", lines[:10]))
        if not eqHeaders and "생산설비" in title:
            eqFails.append((code, title, "유형자산 테이블 헤더 없음", lines[:10]))


print(f"=== 원재료 파싱 실패 분석 ===")
print(f"테이블 헤더 못 찾은 종목: {len(rawFails)}건")
print()

# 패턴별 분류
patterns = {}
for code, title, reason, firstLines in rawFails[:50]:
    # 첫 몇 줄로 패턴 파악
    tableLines = [l.strip() for l in firstLines if l.strip().startswith("|")]
    key = "no_table" if not tableLines else "has_table"
    textLines = [l.strip() for l in firstLines if l.strip() and not l.strip().startswith("|")]
    pattern = textLines[0][:50] if textLines else "(empty)"
    if pattern not in patterns:
        patterns[pattern] = []
    patterns[pattern].append(code)

print(f"섹션 시작 패턴:")
for pat, codes in sorted(patterns.items(), key=lambda x: -len(x[1]))[:15]:
    print(f"  ({len(codes):3d}건) {pat}")
    for c in codes[:3]:
        print(f"         {c}")

print(f"\n=== 상세 샘플 (실패 종목 처음 5건) ===")
for code, title, reason, firstLines in rawFails[:5]:
    print(f"\n  {code} [{title}] — {reason}")
    for l in firstLines:
        print(f"    {l.strip()[:100]}")
