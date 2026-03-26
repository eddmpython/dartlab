"""실험 ID: 004
실험명: DART XML 전체 섹션 파싱 (SECTION-1/2/3 중첩 처리)

목적:
- 003에서 SECTION-1만 14개 추출된 문제 해결
- XML 파서(lxml)로 중첩 SECTION-1 > SECTION-2 > SECTION-3 구조를 순회
- collector 47개 섹션과 1:1 매칭되는지 최종 확인

가설:
1. lxml으로 SECTION 태그를 재귀 순회하면 collector와 동일한 개수의 섹션을 뽑을 수 있다
2. 각 SECTION의 직접 자식 content만 추출하면 소분류 content도 정확히 대응한다

방법:
1. lxml.etree로 XML 파싱 (대소문자 보존)
2. BODY 내 SECTION-N 태그를 DFS로 순회
3. 각 SECTION에서 TITLE 추출 + 하위 SECTION 제외한 직접 content 추출
4. collector 결과와 title/content 비교

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
from lxml import etree

from dartlab.core.dataLoader import loadData
from dartlab.providers.dart.openapi.client import DartClient


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


def _xmlFragmentToText(xmlFragment: str) -> str:
    """XML 조각 → 텍스트 (collector의 _htmlToText와 동일 로직)."""
    soup = BeautifulSoup(xmlFragment, "lxml")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()
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


def _getDirectContent(element) -> str:
    """element의 직접 자식 content만 추출 (하위 SECTION 제외)."""
    parts = []
    # 이 element를 문자열화하되 하위 SECTION을 제거
    xmlStr = etree.tostring(element, encoding="unicode")

    # 하위 SECTION-N 태그 제거 (중첩 content 제외)
    for depth in range(1, 4):
        tag = f"SECTION-{depth}"
        xmlStr = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>",
            "",
            xmlStr,
            flags=re.DOTALL | re.IGNORECASE,
        )

    return _xmlFragmentToText(xmlStr)


def _parseSectionsRecursive(xmlContent: str) -> list[dict]:
    """lxml으로 DART XML의 모든 SECTION을 재귀 순회."""
    # lxml은 소문자로 변환할 수 있으므로 recover 모드 사용
    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    sections = []
    order = 0

    def _walkSections(parent):
        nonlocal order
        for child in parent:
            tagName = child.tag.upper() if isinstance(child.tag, str) else ""
            if tagName.startswith("SECTION-"):
                # TITLE 추출
                titleEl = child.find(".//title")
                if titleEl is None:
                    titleEl = child.find(".//TITLE")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = re.sub(r"\s+", " ", title)
                else:
                    title = f"({tagName})"

                # 직접 content (하위 SECTION 제외)
                content = _getDirectContent(child)
                # title 중복 제거
                if content.startswith(title):
                    content = content[len(title):].strip()

                sections.append({
                    "order": order,
                    "title": title,
                    "content": content,
                    "depth": tagName,
                })
                order += 1

                # 재귀: 하위 SECTION
                _walkSections(child)
            else:
                _walkSections(child)

    _walkSections(tree)
    return sections


def main():
    client = DartClient()

    # 비교 대상
    rceptNo = "20250311001085"  # 삼성전자 사업보고서 2024.12

    # 1. ZIP 다운로드 → 전체 섹션 파싱
    print("=" * 60)
    print("1. ZIP XML → 전체 섹션 파싱 (lxml 재귀)")
    print("=" * 60)

    raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    xmlContent = zf.read(largest).decode("utf-8")

    zipSections = _parseSectionsRecursive(xmlContent)
    print(f"ZIP 추출 섹션 수: {len(zipSections)}")
    for s in zipSections:
        indent = "  " if "SECTION-1" in s["depth"] else "    "
        print(f"{indent}[{s['order']:2d}] ({s['depth']}) {s['title'][:60]} | {len(s['content']):,}자")

    # 2. collector 결과
    print("\n" + "=" * 60)
    print("2. collector 결과")
    print("=" * 60)

    docsParquet = loadData("005930", category="docs")
    collSections = docsParquet.filter(pl.col("rcept_no") == rceptNo).sort("section_order")
    print(f"collector 섹션 수: {collSections.height}")

    # 3. 제목 1:1 비교
    print("\n" + "=" * 60)
    print("3. 제목 1:1 비교 (순서대로)")
    print("=" * 60)

    zipTitles = [s["title"] for s in zipSections]
    collTitles = collSections["section_title"].to_list()

    maxLen = max(len(zipTitles), len(collTitles))
    matchCount = 0
    for i in range(maxLen):
        zt = zipTitles[i] if i < len(zipTitles) else "(없음)"
        ct = collTitles[i] if i < len(collTitles) else "(없음)"
        ztNorm = re.sub(r"\s+", "", zt)
        ctNorm = re.sub(r"\s+", "", ct)
        isMatch = ztNorm == ctNorm or SequenceMatcher(None, ztNorm, ctNorm).ratio() > 0.85
        mark = "O" if isMatch else "X"
        if isMatch:
            matchCount += 1
        print(f"  [{i:2d}] {mark} ZIP: {zt[:35]:35s} | coll: {ct[:35]}")

    print(f"\n매칭: {matchCount}/{maxLen}")

    # 4. content 유사도 (매칭된 것만)
    print("\n" + "=" * 60)
    print("4. content 유사도 (매칭 섹션, 전체)")
    print("=" * 60)

    collRows = list(collSections.iter_rows(named=True))
    compared = 0
    highSim = 0
    for zs in zipSections:
        ztNorm = re.sub(r"\s+", "", zs["title"])
        for cr in collRows:
            ctNorm = re.sub(r"\s+", "", cr["section_title"])
            if ztNorm == ctNorm or SequenceMatcher(None, ztNorm, ctNorm).ratio() > 0.85:
                zLen = len(zs["content"])
                cLen = len(cr["section_content"] or "")
                # 앞 2000자만 비교 (속도)
                ratio = SequenceMatcher(
                    None,
                    zs["content"][:2000],
                    (cr["section_content"] or "")[:2000],
                ).ratio()
                compared += 1
                if ratio > 0.9:
                    highSim += 1
                sim = f"{ratio:.1%}"
                print(f"  {zs['title'][:35]:35s} | ZIP {zLen:>8,}자 coll {cLen:>8,}자 | {sim}")
                break

    print(f"\n비교: {compared}쌍, 90%이상 유사: {highSim}개")


if __name__ == "__main__":
    main()
