"""
실험 ID: 014
실험명: docs parquet 전체 섹션 인벤토리

목적:
- docs parquet에 저장된 section_title 전체를 대분류별로 분류
- 사업보고서 표준 목차(Ⅰ~Ⅺ)와 매핑
- 현재 파서가 처리하는 섹션 vs 무시하는 섹션 식별
- 서술형 텍스트가 포함된 섹션 식별

가설:
1. docs parquet의 section_title에 대분류 번호(I, II, III...)가 포함되어 있을 것
2. 현재 파서가 커버하지 못하는 서술형 섹션이 상당수 있을 것

방법:
1. 삼성전자(005930) docs parquet 로드
2. section_title + section_content 컬럼 확인
3. 연도별로 content 크기 확인 (최신 데이터가 비어있을 수 있음)
4. 대분류별 그룹핑 + 소분류 매핑

결과 (실험 후 작성):

결론:

실험일: 2026-03-11
"""

import sys, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport


ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}


def getContentCol(df):
    """section_content 또는 content 컬럼명 반환."""
    if "section_content" in df.columns:
        return "section_content"
    if "content" in df.columns:
        return "content"
    return None


def exploreSections(stockCode: str, targetYear: str = None):
    """한 종목의 사업보고서 섹션 구조 탐색 (content 있는 연도 자동 선택)."""
    df = loadData(stockCode)
    corpName = df.row(0, named=True).get("corp_name", stockCode)
    contentCol = getContentCol(df)

    print(f"\n{'='*80}")
    print(f" {corpName} ({stockCode})")
    print(f"{'='*80}")
    print(f"컬럼: {df.columns}")
    print(f"content 컬럼: {contentCol}")

    years = sorted(df["year"].unique().to_list(), reverse=True)

    if targetYear:
        tryYears = [targetYear]
    else:
        tryYears = years

    for year in tryYears:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        if contentCol and contentCol in report.columns:
            nonEmpty = report.filter(
                pl.col(contentCol).is_not_null()
                & (pl.col(contentCol).str.len_chars() > 0)
            )
            if len(nonEmpty) > 0:
                print(f"\n--- {year} 사업보고서 ({len(report)}행, content 있는 행: {len(nonEmpty)}) ---")
                showSections(report, contentCol)
                return year

    print("content가 있는 사업보고서를 찾지 못함")
    return None


def showSections(report, contentCol):
    """섹션별 content 크기 표시 (대분류 구분)."""
    sections = report.sort("section_order")

    currentMajor = None

    for row in sections.iter_rows(named=True):
        title = row.get("section_title", "")
        content = row.get(contentCol, "") or ""
        chars = len(content)
        order = row.get("section_order", 0)

        majorNum = detectMajorSection(title)
        if majorNum and majorNum != currentMajor:
            currentMajor = majorNum
            print(f"\n  ┌─ 대분류 {majorNum} ─────────────────────")

        hasTable = "<table" in content.lower() if content else False
        hasText = bool(re.search(r'[가-힣]{10,}', content)) if content else False

        markers = []
        if hasTable:
            markers.append("TABLE")
        if hasText:
            markers.append("TEXT")

        markerStr = f" [{','.join(markers)}]" if markers else ""
        print(f"  │ {order:3d} | {chars:>8,} chars{markerStr} | {title}")


def detectMajorSection(title: str):
    """대분류 로마 숫자 감지."""
    m = re.match(r'^([IVXivx]+)\.\s', title.strip())
    if m:
        roman = m.group(1).upper()
        return ROMAN_MAP.get(roman)
    return None


def summaryByMajor(stockCode: str, year: str):
    """대분류별 요약 — 어떤 소분류가 있고, content 유형은 뭔지."""
    df = loadData(stockCode)
    contentCol = getContentCol(df)
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return

    corpName = df.row(0, named=True).get("corp_name", stockCode)
    print(f"\n{'='*80}")
    print(f" {corpName} ({stockCode}) — {year} 대분류별 요약")
    print(f"{'='*80}")

    sections = report.sort("section_order").to_dicts()

    majorSections = {}
    currentMajor = "표지"

    for row in sections:
        title = row.get("section_title", "")
        content = row.get(contentCol, "") or ""
        chars = len(content)

        majorNum = detectMajorSection(title)
        if majorNum:
            currentMajor = f"{majorNum:02d}_{title.strip()}"

        if currentMajor not in majorSections:
            majorSections[currentMajor] = []

        hasTable = "<table" in content.lower() if content else False
        textLen = len(re.findall(r'[가-힣]+', content)) if content else 0

        majorSections[currentMajor].append({
            "title": title,
            "chars": chars,
            "hasTable": hasTable,
            "koreanWords": textLen,
        })

    for major, items in sorted(majorSections.items()):
        totalChars = sum(i["chars"] for i in items)
        tableCount = sum(1 for i in items if i["hasTable"])
        textItems = sum(1 for i in items if i["koreanWords"] > 50)

        print(f"\n{'─'*60}")
        print(f" {major}")
        print(f" 소분류: {len(items)}개 | 총 {totalChars:,} chars | 테이블: {tableCount} | 텍스트: {textItems}")
        print(f"{'─'*60}")

        for item in items:
            kind = []
            if item["hasTable"]:
                kind.append("T")
            if item["koreanWords"] > 50:
                kind.append("텍")
            kindStr = f"[{'|'.join(kind)}]" if kind else "[빈]"

            print(f"  {item['chars']:>8,} chars {kindStr:>6} | {item['title']}")


if __name__ == "__main__":
    code = "005930"
    year = exploreSections(code)

    if year:
        summaryByMajor(code, year)
