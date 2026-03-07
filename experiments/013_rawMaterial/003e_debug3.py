"""현대차/LG/LG화학/카카오 원재료+생산설비 테이블 구조 디버깅."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

TARGETS = [
    ("005380", "현대차"),
    ("003550", "LG"),
    ("051910", "LG화학"),
    ("035720", "카카오"),
    ("006400", "삼성SDI"),
]

for code, name in TARGETS:
    print(f"\n{'='*70}")
    print(f"  {name} ({code})")
    print(f"{'='*70}")

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

    for si in range(sections.height):
        title = sections["section_title"][si]
        content = sections["section_content"][si]
        lines = content.split("\n")

        print(f"\n  --- [{title}] ({len(lines)} lines) ---")

        # 원재료 테이블 헤더 근처 출력
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|") and "---" not in s:
                cells = s.strip().split("|")
                if cells and cells[0].strip() == "":
                    cells = cells[1:]
                if cells and cells[-1].strip() == "":
                    cells = cells[:-1]
                cells = [c.strip() for c in cells]
                joined = " ".join(cells)

                # 원재료 헤더 감지
                if ("품 목" in joined or "품목" in joined) and ("매입" in joined or "비율" in joined or "비중" in joined):
                    print(f"\n  [원재료 헤더] line {i}: cols={len(cells)}")
                    print(f"    cells: {cells}")
                    # 다음 10줄 출력
                    for j in range(i+1, min(i+12, len(lines))):
                        s2 = lines[j].strip()
                        if s2.startswith("|") and "---" not in s2:
                            c2 = s2.strip().split("|")
                            if c2 and c2[0].strip() == "":
                                c2 = c2[1:]
                            if c2 and c2[-1].strip() == "":
                                c2 = c2[:-1]
                            c2 = [c.strip() for c in c2]
                            print(f"    [{j:3d}] cols={len(c2)} {c2}")

                # 유형자산 헤더 감지
                if ("토지" in joined or "기계" in joined) and ("합계" in joined or "계" in cells[-1] if cells else False):
                    print(f"\n  [유형자산 헤더] line {i}: cols={len(cells)}")
                    print(f"    cells: {cells}")
                    for j in range(i+1, min(i+15, len(lines))):
                        s2 = lines[j].strip()
                        if s2.startswith("|") and "---" not in s2:
                            c2 = s2.strip().split("|")
                            if c2 and c2[0].strip() == "":
                                c2 = c2[1:]
                            if c2 and c2[-1].strip() == "":
                                c2 = c2[:-1]
                            c2 = [c.strip() for c in c2]
                            print(f"    [{j:3d}] cols={len(c2)} {c2}")
