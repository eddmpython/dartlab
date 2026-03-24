"""실험 ID: 003
실험명: ZIP XML → docs parquet 스키마 변환 + collector 결과와 비교

목적:
- ZIP 원본 XML을 파싱해서 현재 docs parquet 스키마 동일하게 재현
- collector 결과물과 section_title, section_content 비교
- 동일 rcept_no가 있는 보고서로 1:1 비교

가설:
1. SECTION-1/SECTION-2 + TITLE 태그로 section_order, section_title 추출 가능
2. 각 SECTION 내 HTML/XML → 텍스트 변환 결과가 collector와 유사할 것

방법:
1. collector가 이미 수집한 rcept_no 중 하나를 선택
2. 같은 rcept_no에 대해 document.xml API로 ZIP 다운로드
3. XML 파싱 → docs parquet 스키마로 변환
4. collector 결과와 section별 비교 (title 일치, content 유사도)

결과 (실험 후 작성):
- (실행 후 채울 것)

결론:
- (실행 후 채울 것)

실험일: 2026-03-24
"""

from __future__ import annotations

import io
import re
import zipfile
from difflib import SequenceMatcher

import polars as pl
from bs4 import BeautifulSoup

from dartlab.core.dataLoader import loadData
from dartlab.engines.company.dart.openapi.client import DartClient


def _xmlSectionToText(sectionXml: str) -> str:
    """DART XML 섹션 → 텍스트 (collector의 _htmlToText와 동일 로직)."""
    soup = BeautifulSoup(sectionXml, "lxml")

    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()

    # 테이블 → 마크다운
    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"\n\n{md}\n\n", "lxml"))
        else:
            table.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li", "tu", "te"]):
        p.insert_after("\n")

    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _tableToMarkdown(table) -> str:
    """HTML/XML 테이블 → 마크다운."""
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells: list[str] = []
        for cell in tr.find_all(["td", "th", "te"]):
            colspan = int(cell.get("colspan", 1))
            text = cell.get_text(strip=True)
            text = re.sub(r"\s+", " ", text)
            text = text.replace("|", "｜")
            cells.append(text)
            cells.extend("" for _ in range(colspan - 1))
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    maxCols = max(len(row) for row in rows)
    for row in rows:
        while len(row) < maxCols:
            row.append("")

    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * maxCols) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _parseSectionsFromXml(xmlContent: str) -> list[dict]:
    """DART XML → 섹션 목록 [{order, title, content}]."""
    sections = []
    order = 0

    # SECTION-1과 SECTION-2를 순서대로 찾기
    # 정규식으로 SECTION 태그와 내부 TITLE 추출
    sectionPattern = re.compile(
        r"<(SECTION-[123])[^>]*>(.*?)</\1>",
        re.IGNORECASE | re.DOTALL,
    )

    for match in sectionPattern.finditer(xmlContent):
        sectionTag = match.group(1)
        sectionBody = match.group(2)

        # TITLE 추출
        titleMatch = re.search(
            r"<TITLE[^>]*>(.*?)</TITLE>",
            sectionBody,
            re.IGNORECASE | re.DOTALL,
        )
        if titleMatch:
            rawTitle = titleMatch.group(1)
            title = re.sub(r"<[^>]+>", "", rawTitle).strip()
            title = re.sub(r"\s+", " ", title)
        else:
            title = f"({sectionTag})"

        # TITLE 이후 내용을 텍스트로 변환
        content = _xmlSectionToText(sectionBody)

        # TITLE 텍스트를 content에서 제거 (중복 방지)
        if content.startswith(title):
            content = content[len(title) :].strip()

        sections.append(
            {
                "order": order,
                "title": title,
                "content": content,
                "depth": sectionTag,
            }
        )
        order += 1

    return sections


def main():
    client = DartClient()

    # 1. collector가 가진 삼성전자 최근 사업보고서 rcept_no 찾기
    print("=" * 60)
    print("1. 비교 대상 rcept_no 선택")
    print("=" * 60)

    docsParquet = loadData("005930", category="docs")
    if docsParquet is None or docsParquet.is_empty():
        print("docs parquet 없음")
        return

    annualDocs = docsParquet.filter(pl.col("report_type").str.contains("사업보고서"))
    if annualDocs.is_empty():
        print("사업보고서 없음")
        return

    latestRcept = annualDocs.sort("rcept_date", descending=True)["rcept_no"][0]
    reportType = annualDocs.sort("rcept_date", descending=True)["report_type"][0]
    print(f"대상: {reportType} (rcept_no={latestRcept})")

    # 2. ZIP 다운로드 및 XML 파싱
    print("\n" + "=" * 60)
    print("2. ZIP 다운로드 → XML 섹션 파싱")
    print("=" * 60)

    raw = client.getBytes("document.xml", {"rcept_no": latestRcept})
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    xmlContent = zf.read(largest).decode("utf-8")

    zipSections = _parseSectionsFromXml(xmlContent)
    print(f"ZIP에서 추출한 섹션 수: {len(zipSections)}")

    for s in zipSections:
        contentPreview = s["content"][:50].replace("\n", " ") if s["content"] else "(빈)"
        print(f"  [{s['order']:2d}] ({s['depth']}) {s['title'][:60]:60s} | {len(s['content']):,}자 | {contentPreview}...")

    # 3. collector 결과
    print("\n" + "=" * 60)
    print("3. collector 결과 (동일 rcept_no)")
    print("=" * 60)

    collectorSections = docsParquet.filter(pl.col("rcept_no") == latestRcept).sort("section_order")
    print(f"collector 섹션 수: {collectorSections.height}")

    for row in collectorSections.iter_rows(named=True):
        contentLen = len(row["section_content"]) if row["section_content"] else 0
        print(f"  [{row['section_order']:2d}] {row['section_title'][:60]:60s} | {contentLen:,}자")

    # 4. title 매칭 비교
    print("\n" + "=" * 60)
    print("4. title 매칭 비교")
    print("=" * 60)

    collectorTitles = collectorSections["section_title"].to_list()
    zipTitles = [s["title"] for s in zipSections]

    matched = 0
    unmatched = []
    for zt in zipTitles:
        ztNorm = re.sub(r"\s+", "", zt)
        found = False
        for ct in collectorTitles:
            ctNorm = re.sub(r"\s+", "", ct)
            if ztNorm == ctNorm or SequenceMatcher(None, ztNorm, ctNorm).ratio() > 0.85:
                found = True
                break
        if found:
            matched += 1
        else:
            unmatched.append(zt)

    print(f"매칭: {matched}/{len(zipTitles)}")
    if unmatched:
        print(f"미매칭 ZIP 섹션:")
        for u in unmatched:
            print(f"  - {u}")

    zipOnly = set(re.sub(r"\s+", "", t) for t in zipTitles)
    collectorOnly = set(re.sub(r"\s+", "", t) for t in collectorTitles)
    onlyInCollector = collectorOnly - zipOnly
    if onlyInCollector:
        print(f"\ncollector에만 있는 섹션 ({len(onlyInCollector)}개):")
        for t in sorted(onlyInCollector):
            print(f"  - {t}")

    # 5. content 유사도 비교 (매칭된 섹션)
    print("\n" + "=" * 60)
    print("5. content 유사도 비교 (title 매칭된 섹션, 상위 10개)")
    print("=" * 60)

    comparisons = 0
    for zs in zipSections:
        ztNorm = re.sub(r"\s+", "", zs["title"])
        for row in collectorSections.iter_rows(named=True):
            ctNorm = re.sub(r"\s+", "", row["section_title"])
            if ztNorm == ctNorm or SequenceMatcher(None, ztNorm, ctNorm).ratio() > 0.85:
                zipContent = zs["content"][:2000]
                collContent = (row["section_content"] or "")[:2000]
                ratio = SequenceMatcher(None, zipContent, collContent).ratio()
                print(f"  {zs['title'][:40]:40s} | ZIP {len(zs['content']):>6,}자 vs coll {len(row['section_content'] or ''):>6,}자 | 유사도 {ratio:.1%}")
                comparisons += 1
                break
        if comparisons >= 10:
            break


if __name__ == "__main__":
    main()
