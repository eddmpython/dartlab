"""
실험 ID: 014
실험명: 대분류/소분류 content 중복 여부 + 청킹 전략 탐색

목적:
- 대분류 content 안에 소분류 content가 중복 포함되는지 확인
- 대분류만 있고 소분류 없는 섹션 파악
- 실제 텍스트 내부 구조 (번호, 가/나/다, 소제목 패턴) 분석
- LLM용 청킹 전략 수립

가설:
1. 대분류 content = 소분류 content 합산 (중복)이라면, 소분류만 쓰면 된다
2. 대분류만 있고 소분류 없는 경우, 내부 패턴으로 분할 가능할 것

방법:
1. 삼성전자 2025 — 각 대분류의 content vs 소분류들의 content 비교
2. content 내부의 구조 패턴 (제목, 번호) 분석
3. 텍스트 크기 분포로 청킹 임계값 결정

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


def analyzeOverlap(stockCode: str):
    """대분류 content vs 소분류 content 중복 분석."""
    df = loadData(stockCode)
    corpName = df.row(0, named=True).get("corp_name", stockCode)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    report = None
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

    if report is None:
        return

    print(f"\n{'='*80}")
    print(f" {corpName} ({stockCode}) — {year} 대분류/소분류 중복 분석")
    print(f"{'='*80}")

    contentCol = "section_content" if "section_content" in report.columns else "content"
    rows = report.sort("section_order").to_dicts()

    currentMajor = None
    majorContent = None
    subContents = []

    def flushMajor():
        if currentMajor is None:
            return
        majorLen = len(majorContent) if majorContent else 0
        subTotal = sum(len(c) for c in subContents)

        if majorLen == 0 and subTotal == 0:
            return

        hasSubOnly = majorLen == 0 and subTotal > 0
        hasMajorOnly = majorLen > 0 and subTotal == 0

        overlap = ""
        if majorLen > 0 and subTotal > 0:
            combinedSub = "\n".join(subContents)
            if combinedSub in majorContent:
                overlap = "소분류⊂대분류(완전포함)"
            elif majorContent[:200] in combinedSub[:300]:
                overlap = "부분중복"
            else:
                ratio = subTotal / majorLen if majorLen > 0 else 0
                overlap = f"비율={ratio:.1f}x"

        status = ""
        if hasMajorOnly:
            status = "대분류만 (소분류 없음)"
        elif hasSubOnly:
            status = "소분류만 (대분류 빈)"
        else:
            status = f"대분류+소분류 ({overlap})"

        print(f"\n  {currentMajor}")
        print(f"    대분류: {majorLen:>8,} chars")
        print(f"    소분류: {subTotal:>8,} chars ({len(subContents)}개)")
        print(f"    상태: {status}")

    for row in rows:
        title = row.get("section_title", "").strip()
        content = row.get(contentCol, "") or ""

        m = re.match(r'^([IVXivx]+)\.\s', title)
        if m:
            flushMajor()
            currentMajor = title
            majorContent = content
            subContents = []
        elif re.match(r'^\d+\.\s', title):
            subContents.append(content)

    flushMajor()


def analyzeInternalStructure(stockCode: str, sectionTitle: str):
    """특정 섹션의 내부 구조 패턴 분석."""
    df = loadData(stockCode)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for y in years:
        report = selectReport(df, y, reportKind="annual")
        if report is not None:
            break

    if report is None:
        return

    contentCol = "section_content" if "section_content" in report.columns else "content"
    matched = report.filter(pl.col("section_title").str.contains(sectionTitle))
    if len(matched) == 0:
        print(f"'{sectionTitle}' 섹션 없음")
        return

    content = matched.row(0, named=True).get(contentCol, "") or ""
    corpName = df.row(0, named=True).get("corp_name", stockCode)

    print(f"\n{'='*80}")
    print(f" {corpName} — '{sectionTitle}' 내부 구조 ({len(content):,} chars)")
    print(f"{'='*80}")

    lines = content.split("\n")
    print(f"  총 {len(lines)} 줄")

    headingPatterns = {
        "가나다": r'^[가-힣]\.\s',
        "괄호숫자": r'^\(\d+\)\s',
        "숫자점": r'^\d+\.\s',
        "숫자괄호": r'^\d+\)\s',
        "로마숫자": r'^[IVXivx]+\.\s',
        "굵은제목": r'^\[.+\]',
        "테이블구분": r'^\|',
        "빈줄": r'^\s*$',
    }

    for name, pat in headingPatterns.items():
        matches = [l for l in lines if re.match(pat, l.strip())]
        if matches:
            print(f"\n  [{name}] {len(matches)}개:")
            for m in matches[:5]:
                print(f"    {m.strip()[:80]}")
            if len(matches) > 5:
                print(f"    ... +{len(matches)-5}개")

    tableLines = sum(1 for l in lines if l.strip().startswith("|"))
    textLines = sum(1 for l in lines if l.strip() and not l.strip().startswith("|"))
    print(f"\n  테이블 줄: {tableLines}, 텍스트 줄: {textLines}")
    print(f"  테이블 비율: {tableLines/(tableLines+textLines)*100:.1f}%" if (tableLines+textLines) > 0 else "")


def findChunkBoundaries(content: str):
    """텍스트 내 청크 경계 후보 탐지."""
    lines = content.split("\n")
    boundaries = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^[가-힣]\.\s', stripped):
            boundaries.append((i, "가나다", stripped[:60]))
        elif re.match(r'^\(\d+\)\s', stripped):
            boundaries.append((i, "괄호숫자", stripped[:60]))
        elif re.match(r'^\d+\.\s[가-힣]', stripped) and len(stripped) < 50:
            boundaries.append((i, "소제목", stripped[:60]))
        elif re.match(r'^\[.+\]$', stripped):
            boundaries.append((i, "대괄호", stripped[:60]))

    return boundaries


if __name__ == "__main__":
    analyzeOverlap("005930")

    print("\n\n")

    for section in [
        "II. 사업의 내용",
        "IV. 이사의 경영진단",
        "XI. 그 밖에 투자자",
        "VIII. 임원 및 직원",
    ]:
        analyzeInternalStructure("005930", section)
