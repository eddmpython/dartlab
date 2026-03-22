"""
실험 ID: 014
실험명: section_content 실제 포맷 확인 + 다종목 비교

목적:
- section_content가 HTML인지 plain text인지 확인
- 서술형 섹션의 실제 내용 샘플 확인
- 5종목 비교로 업종별 차이 파악

방법:
1. 삼성전자 2025 — 대분류별 content 첫 500자 샘플
2. 5종목 대분류 구조 비교 (제조업, 금융업, IT, 바이오, 유통)

결과 (실험 후 작성):

결론:

실험일: 2026-03-11
"""

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport


def sampleContent(stockCode: str, year: str = None):
    """대분류별 content 샘플 출력."""
    df = loadData(stockCode)
    corpName = df.row(0, named=True).get("corp_name", stockCode)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    if not year:
        for y in years:
            report = selectReport(df, y, reportKind="annual")
            if report is not None:
                contentCol = "section_content" if "section_content" in report.columns else "content"
                nonEmpty = report.filter(
                    pl.col(contentCol).is_not_null()
                    & (pl.col(contentCol).str.len_chars() > 0)
                )
                if len(nonEmpty) > 0:
                    year = y
                    break

    if not year:
        print(f"{corpName}: content 있는 사업보고서 없음")
        return

    report = selectReport(df, year, reportKind="annual")
    contentCol = "section_content" if "section_content" in report.columns else "content"

    print(f"\n{'='*80}")
    print(f" {corpName} ({stockCode}) — {year}")
    print(f"{'='*80}")

    interestingSections = [
        "II. 사업의 내용",
        "1. 사업의 개요",
        "5. 위험관리 및 파생거래",
        "6. 주요계약 및 연구개발활동",
        "IV. 이사의 경영진단 및 분석의견",
        "V. 회계감사인의 감사의견 등",
        "XI. 그 밖에 투자자 보호를 위하여 필요한 사항",
    ]

    for row in report.sort("section_order").iter_rows(named=True):
        title = row.get("section_title", "")
        content = row.get(contentCol, "") or ""

        if not any(title.strip() == s or title.strip().endswith(s) for s in interestingSections):
            continue

        print(f"\n--- {title} ({len(content):,} chars) ---")

        isHtml = bool(re.search(r'<[a-zA-Z][^>]*>', content[:1000]))
        print(f"포맷: {'HTML' if isHtml else 'Plain Text'}")

        sample = content[:800].replace('\n', '\n  ')
        print(f"  {sample}")
        if len(content) > 800:
            print(f"  ... ({len(content) - 800:,} chars more)")


def compareMajorSections(codes: list):
    """다종목 대분류 구조 비교."""
    print(f"\n{'='*80}")
    print(f" 다종목 대분류 비교")
    print(f"{'='*80}")

    results = {}

    for stockCode in codes:
        df = loadData(stockCode)
        corpName = df.row(0, named=True).get("corp_name", stockCode)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = None
        year = None
        for y in years:
            report = selectReport(df, y, reportKind="annual")
            if report is not None:
                contentCol = "section_content" if "section_content" in report.columns else "content"
                nonEmpty = report.filter(
                    pl.col(contentCol).is_not_null()
                    & (pl.col(contentCol).str.len_chars() > 0)
                )
                if len(nonEmpty) > 0:
                    year = y
                    break

        if not year or report is None:
            results[stockCode] = {"name": corpName, "year": None, "majors": {}}
            continue

        majors = {}
        for row in report.sort("section_order").iter_rows(named=True):
            title = row.get("section_title", "")
            content = row.get(contentCol, "") or ""

            m = re.match(r'^([IVXivx]+)\.\s+(.+)', title.strip())
            if m:
                roman = m.group(1).upper()
                label = m.group(2).strip()
                majors[roman] = {
                    "label": label,
                    "chars": len(content),
                }

        results[stockCode] = {"name": corpName, "year": year, "majors": majors}

    allRomans = set()
    for r in results.values():
        allRomans.update(r["majors"].keys())

    romanOrder = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]
    sortedRomans = [r for r in romanOrder if r in allRomans]

    header = f"{'대분류':<6} | {'섹션명':<30}"
    for code in codes:
        name = results[code]["name"][:6]
        header += f" | {name:>8}"
    print(f"\n{header}")
    print("─" * len(header))

    for roman in sortedRomans:
        labels = set()
        for r in results.values():
            if roman in r["majors"]:
                labels.add(r["majors"][roman]["label"][:28])
        label = list(labels)[0] if labels else "?"

        row = f"{roman:<6} | {label:<30}"
        for code in codes:
            majors = results[code]["majors"]
            if roman in majors:
                chars = majors[roman]["chars"]
                if chars > 0:
                    row += f" | {chars:>7,}"
                else:
                    row += f" | {'없음':>8}"
            else:
                row += f" | {'—':>8}"
        print(row)


if __name__ == "__main__":
    sampleContent("005930")

    print("\n\n")

    compareMajorSections([
        "005930",
        "000660",
        "005380",
        "000020",
        "003550",
    ])
