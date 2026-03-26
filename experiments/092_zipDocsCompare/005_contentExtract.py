"""실험 ID: 005
실험명: lxml 태그 변환 문제 해결 + content 정확 추출

목적:
- 004에서 content가 전부 0자인 문제 해결
- lxml HTMLParser의 태그 소문자 변환 확인
- 각 SECTION의 content를 정확히 추출하는 방법 확정
- collector 결과와 최종 비교

가설:
1. lxml HTMLParser가 태그를 소문자로 변환해서 정규식 매칭 실패
2. etree.tostring + tail 처리를 정확히 하면 content 추출 가능

방법:
1. lxml의 태그명 확인
2. 각 section element에서 직접 자식만 추출 (하위 section element 건너뛰기)
3. collector와 content 비교

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


def _xmlToText(xmlStr: str) -> str:
    """XML/HTML 조각 → 텍스트."""
    soup = BeautifulSoup(xmlStr, "lxml")
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


def _getOwnContent(element) -> str:
    """element의 직접 content만 추출 (하위 section 제외, TITLE 제외)."""
    parts = []

    # element의 text (첫 자식 태그 전까지의 텍스트)
    # 하지만 이걸로는 부족 — 자식 사이사이 텍스트도 있음
    # 대신: element를 문자열화하고, 하위 section과 title을 제거

    xmlStr = etree.tostring(element, encoding="unicode")

    # 자기 자신의 여는/닫는 태그 제거
    tag = element.tag
    xmlStr = re.sub(rf"^<{re.escape(tag)}[^>]*>", "", xmlStr, count=1)
    xmlStr = re.sub(rf"</{re.escape(tag)}>$", "", xmlStr)

    # TITLE 태그 제거
    xmlStr = re.sub(r"<title[^>]*>.*?</title>", "", xmlStr, flags=re.DOTALL | re.IGNORECASE)

    # 하위 section 태그 제거 (section-1, section-2, section-3)
    for d in range(1, 4):
        xmlStr = re.sub(
            rf"<section-{d}[^>]*>.*?</section-{d}>",
            "",
            xmlStr,
            flags=re.DOTALL | re.IGNORECASE,
        )

    return _xmlToText(xmlStr)


def _parseSections(xmlContent: str) -> list[dict]:
    """DART XML → 섹션 목록 (lxml 사용)."""
    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    sections = []
    order = 0

    def _walk(parent):
        nonlocal order
        for child in parent:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag.startswith("section-"):
                # TITLE
                titleEl = child.find(".//title")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = re.sub(r"\s+", " ", title)
                else:
                    title = f"({tag})"

                content = _getOwnContent(child)

                sections.append({
                    "order": order,
                    "title": title,
                    "content": content,
                    "depth": tag,
                })
                order += 1
                _walk(child)
            else:
                _walk(child)

    _walk(tree)
    return sections


def main():
    client = DartClient()
    rceptNo = "20250311001085"

    # 1. lxml 태그명 확인
    print("=" * 60)
    print("1. lxml 태그명 확인")
    print("=" * 60)

    raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    xmlContent = zf.read(largest).decode("utf-8")

    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    # 태그 이름 샘플
    uniqueTags = set()
    for el in tree.iter():
        if isinstance(el.tag, str):
            uniqueTags.add(el.tag)
    sectionTags = sorted(t for t in uniqueTags if "section" in t.lower())
    print(f"section 관련 태그: {sectionTags}")
    print(f"전체 태그 수: {len(uniqueTags)}")

    # 2. 전체 섹션 파싱
    print("\n" + "=" * 60)
    print("2. 전체 섹션 파싱 (content 포함)")
    print("=" * 60)

    zipSections = _parseSections(xmlContent)
    print(f"섹션 수: {len(zipSections)}")
    for s in zipSections:
        indent = "  " if "section-1" in s["depth"] else "    "
        preview = s["content"][:60].replace("\n", " ") if s["content"] else "(빈)"
        print(f"{indent}[{s['order']:2d}] {s['title'][:45]:45s} | {len(s['content']):>8,}자 | {preview}...")

    # 3. collector 결과와 비교 — SECTION-3 제외하고 비교
    print("\n" + "=" * 60)
    print("3. collector 결과와 비교 (SECTION-3 제외)")
    print("=" * 60)

    # ZIP에서 SECTION-3 제외 (collector에는 없으니까)
    zipFiltered = [s for s in zipSections if s["depth"] != "section-3"]

    # 【 대표이사 등의 확인 】, 【 전문가의 확인 】 등 collector에 없는 것 제외
    # collector는 "사업보고서" 표지 + 본문만
    zipFiltered2 = [
        s for s in zipFiltered
        if not s["title"].startswith("【") and "전문가" not in s["title"]
    ]

    docsParquet = loadData("005930", category="docs")
    collSections = docsParquet.filter(pl.col("rcept_no") == rceptNo).sort("section_order")
    collRows = list(collSections.iter_rows(named=True))

    # collector에서 "사업보고서" 표지 제외
    collFiltered = [r for r in collRows if r["section_title"].strip() not in ("사 업 보 고 서",)]

    print(f"ZIP 섹션 (필터 후): {len(zipFiltered2)}")
    print(f"collector 섹션 (필터 후): {len(collFiltered)}")

    # title 매칭
    matchCount = 0
    simResults = []
    maxLen = max(len(zipFiltered2), len(collFiltered))
    for i in range(min(len(zipFiltered2), len(collFiltered))):
        zs = zipFiltered2[i]
        cr = collFiltered[i]
        ztNorm = re.sub(r"\s+", "", zs["title"])
        ctNorm = re.sub(r"\s+", "", cr["section_title"])
        titleMatch = ztNorm == ctNorm or SequenceMatcher(None, ztNorm, ctNorm).ratio() > 0.85

        # content 비교
        zLen = len(zs["content"])
        cLen = len(cr["section_content"] or "")
        if zLen > 0 and cLen > 0:
            ratio = SequenceMatcher(
                None, zs["content"][:2000], (cr["section_content"] or "")[:2000]
            ).ratio()
        else:
            ratio = 0.0

        mark = "O" if titleMatch else "X"
        if titleMatch:
            matchCount += 1

        print(
            f"  [{i:2d}] {mark} {zs['title'][:30]:30s} | "
            f"ZIP {zLen:>8,}자 coll {cLen:>8,}자 | sim={ratio:.1%}"
        )
        simResults.append(ratio)

    print(f"\ntitle 매칭: {matchCount}/{min(len(zipFiltered2), len(collFiltered))}")
    if simResults:
        validSims = [r for r in simResults if r > 0]
        if validSims:
            print(f"content 유사도 (0 제외): 평균 {sum(validSims)/len(validSims):.1%}, "
                  f"최소 {min(validSims):.1%}, 최대 {max(validSims):.1%}")
        zeroCount = sum(1 for r in simResults if r == 0)
        print(f"content 0자 섹션: {zeroCount}개")


if __name__ == "__main__":
    main()
