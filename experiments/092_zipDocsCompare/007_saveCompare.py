"""실험 ID: 007
실험명: ZIP 추출 결과를 collector 동일 스키마 parquet로 저장 + 눈으로 비교

목적:
- ZIP에서 추출한 섹션을 collector와 완전히 동일한 11개 컬럼 parquet로 저장
- temp 폴더에 collector 결과 / ZIP 결과 나란히 저장하여 직접 비교
- 컬럼 값, 타입, 순서가 완전 동일한지 확인

가설:
1. ZIP 추출 결과를 collector 동일 스키마로 저장할 수 있다
2. section_url만 다르고 나머지 10개 컬럼은 동일하게 맞출 수 있다

방법:
1. 삼성전자 최근 사업보고서 1건 선택
2. collector 결과(기존 parquet)에서 해당 rcept_no 추출 → temp/collector.parquet
3. ZIP 다운로드 → 파싱 → 동일 스키마 dict → temp/zip.parquet
4. 두 파일의 스키마, 행 수, 값 비교 출력

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
from pathlib import Path

import polars as pl
from bs4 import BeautifulSoup
from lxml import etree

from dartlab.providers.dart.openapi.client import DartClient


TEMP_DIR = Path(__file__).parent / "temp"


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
    xmlStr = etree.tostring(element, encoding="unicode")
    tag = element.tag
    xmlStr = re.sub(rf"^<{re.escape(tag)}[^>]*>", "", xmlStr, count=1)
    xmlStr = re.sub(rf"</{re.escape(tag)}>$", "", xmlStr)
    xmlStr = re.sub(r"<title[^>]*>.*?</title>", "", xmlStr, flags=re.DOTALL | re.IGNORECASE)
    for d in range(1, 4):
        xmlStr = re.sub(
            rf"<section-{d}[^>]*>.*?</section-{d}>",
            "",
            xmlStr,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return _xmlToText(xmlStr)


def _parseSections(xmlContent: str) -> list[dict]:
    """DART XML → 섹션 목록 (SECTION-1/2만, SECTION-3은 상위에 합산)."""
    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    sections = []
    order = 0

    def _walk(parent):
        nonlocal order
        for child in parent:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag in ("section-1", "section-2"):
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
            elif tag == "section-3":
                pass  # SECTION-3은 건너뜀 (collector에 없으므로)
            else:
                _walk(child)

    _walk(tree)
    return sections


def main():
    client = DartClient()

    # 대상: 삼성전자 최근 사업보고서
    rceptNo = "20250311001085"

    # 원본 parquet 직접 읽기 (dataLoader 정규화 전)
    from dartlab import config
    from dartlab.core.dataConfig import DATA_RELEASES
    rawPath = Path(config.dataDir) / DATA_RELEASES["docs"]["dir"] / "005930.parquet"
    rawDf = pl.read_parquet(rawPath)
    collAll = rawDf.filter(pl.col("rcept_no") == rceptNo).sort("section_order")

    if collAll.is_empty():
        print("해당 rcept_no 데이터 없음")
        return

    firstRow = collAll.row(0, named=True)
    corpCode = firstRow["corp_code"]
    corpName = firstRow["corp_name"]
    rceptDate = firstRow["rcept_date"]
    reportType = firstRow["report_type"]
    year = firstRow["year"]

    print("=" * 70)
    print(f"대상: {corpName} {reportType} (rcept_no={rceptNo})")
    print("=" * 70)

    # ── 1. collector 결과 저장 ──
    TEMP_DIR.mkdir(exist_ok=True)
    collPath = TEMP_DIR / "collector.parquet"
    collAll.write_parquet(collPath)
    print(f"\ncollector 결과 → {collPath}")
    print(f"  행: {collAll.height}, 컬럼: {collAll.columns}")
    print(f"  스키마: {collAll.schema}")

    # ── 2. ZIP 다운로드 → 파싱 → 동일 스키마 저장 ──
    raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    content = zf.read(largest)

    xmlContent = None
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            xmlContent = content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if xmlContent is None:
        xmlContent = content.decode("utf-8", errors="replace")

    zipSections = _parseSections(xmlContent)
    print(f"\nZIP 추출 섹션: {len(zipSections)}개")

    # collector 동일 스키마로 변환
    zipRows = []
    for s in zipSections:
        zipRows.append({
            "corp_code": corpCode,
            "corp_name": corpName,
            "year": year,
            "rcept_date": rceptDate,
            "rcept_no": rceptNo,
            "report_type": reportType,
            "section_order": s["order"],
            "section_title": s["title"],
            "section_url": "",  # ZIP에는 URL 없음
            "section_content": s["content"],
        })

    zipDf = pl.DataFrame(zipRows)

    # 타입 맞추기 — collector 스키마에 맞춤
    for col in collAll.columns:
        if col in zipDf.columns:
            collType = collAll.schema[col]
            zipType = zipDf.schema[col]
            if collType != zipType:
                print(f"  타입 차이: {col} — collector={collType}, zip={zipType}")
                zipDf = zipDf.with_columns(pl.col(col).cast(collType))

    zipPath = TEMP_DIR / "zip.parquet"
    zipDf.write_parquet(zipPath)
    print(f"\nZIP 결과 → {zipPath}")
    print(f"  행: {zipDf.height}, 컬럼: {zipDf.columns}")
    print(f"  스키마: {zipDf.schema}")

    # ── 3. 스키마 비교 ──
    print("\n" + "=" * 70)
    print("스키마 비교")
    print("=" * 70)
    print(f"{'컬럼':25s} | {'collector':20s} | {'zip':20s} | 일치")
    print("-" * 75)
    for col in collAll.columns:
        cType = str(collAll.schema[col])
        zType = str(zipDf.schema.get(col, "없음"))
        match = "O" if cType == zType else "X"
        print(f"{col:25s} | {cType:20s} | {zType:20s} | {match}")

    extraCols = set(zipDf.columns) - set(collAll.columns)
    if extraCols:
        print(f"\nZIP에만 있는 컬럼: {extraCols}")
    missingCols = set(collAll.columns) - set(zipDf.columns)
    if missingCols:
        print(f"\nZIP에 없는 컬럼: {missingCols}")

    # ── 4. 행별 비교 (section_url 제외) ──
    print("\n" + "=" * 70)
    print("행별 비교 (section_url 제외, 앞 20개)")
    print("=" * 70)

    compareCols = ["section_order", "section_title", "section_content"]
    collRows = list(collAll.iter_rows(named=True))
    zipRowsList = list(zipDf.iter_rows(named=True))

    maxRows = min(20, len(collRows), len(zipRowsList))
    matchCount = 0
    for i in range(maxRows):
        cr = collRows[i]
        zr = zipRowsList[i]
        titleMatch = re.sub(r"\s+", "", cr["section_title"]) == re.sub(r"\s+", "", zr["section_title"])
        cLen = len(cr["section_content"] or "")
        zLen = len(zr["section_content"] or "")

        mark = "O" if titleMatch else "X"
        if titleMatch:
            matchCount += 1

        print(
            f"  [{i:2d}] {mark} coll: {cr['section_title'][:30]:30s} ({cLen:>7,}자) | "
            f"zip: {zr['section_title'][:30]:30s} ({zLen:>7,}자)"
        )

    print(f"\n제목 일치: {matchCount}/{maxRows}")
    print(f"collector 총 행: {len(collRows)}")
    print(f"ZIP 총 행: {len(zipRowsList)}")

    # ── 5. section_url 차이 안내 ──
    print("\n" + "=" * 70)
    print("section_url 차이")
    print("=" * 70)
    if collRows:
        print(f"  collector 예시: {collRows[0].get('section_url', '')[:80]}")
    print(f"  zip: (빈 문자열)")
    print("  → ZIP에는 DART viewer URL이 없으므로 빈 문자열 또는 rcept_no 기반 URL 생성 가능")

    print(f"\n저장 위치: {TEMP_DIR.resolve()}")
    print("  collector.parquet — 기존 collector 결과")
    print("  zip.parquet       — ZIP에서 추출한 결과 (동일 스키마)")


if __name__ == "__main__":
    main()
