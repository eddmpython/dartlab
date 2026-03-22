"""10개 종목 원재료/생산설비 섹션 구조 비교."""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("005380", "현대차"),
    ("051910", "LG화학"),
    ("006400", "삼성SDI"),
    ("035720", "카카오"),
    ("068270", "셀트리온"),
    ("003550", "LG"),
    ("055550", "신한지주"),
]

for code, name in STOCKS:
    print(f"\n{'='*60}")
    print(f"  {name} ({code})")
    print(f"{'='*60}")

    df = loadData(code)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        print("  보고서 없음")
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        print("  원재료/생산설비 섹션 없음")
        continue

    for i in range(sections.height):
        title = sections["section_title"][i]
        content = sections["section_content"][i]
        lines = content.split("\n")

        tableCount = 0
        headers = []
        subSections = []
        for line in lines:
            s = line.strip()
            if s.startswith("|") and "---" not in s:
                cells = [c.strip() for c in s.split("|") if c.strip()]
                joined = " ".join(cells)
                if any(kw in joined for kw in ["부 문", "부문", "품 목", "품목", "사업부문",
                                                  "구 분", "구분", "자산항목",
                                                  "매입유형", "원재료명"]):
                    tableCount += 1
                    headers.append(joined[:80])
            elif s and not s.startswith("|") and not s.startswith("※"):
                if any(c in s for c in "가나다라마바사"):
                    if ". " in s or ")" in s:
                        subSections.append(s[:60])

        print(f"\n  [{title}] — {len(lines)} lines, {tableCount} tables")
        print(f"  서브섹션:")
        for ss in subSections[:10]:
            print(f"    {ss}")
        print(f"  테이블 헤더:")
        for h in headers[:10]:
            print(f"    {h}")
