"""실험 ID: 009
실험명: ZIP 전체 기간 수집 + sections 품질 비교

목적:
- 삼성전자 2016Q1~최신 40건 전체를 ZIP으로 수집하여 parquet 저장
- collector parquet과 동일 기간으로 잘라서 sections를 각각 생성
- topic별, 기간별 텍스트 품질 직접 비교

가설:
1. ZIP 전체 기간 수집이 collector와 동등 이상의 sections를 만들 수 있다
2. 소분류 content는 95%+ 유사, 대분류는 합산 로직 추가 시 동일

방법:
1. 기존 collector parquet에서 2016~최신 rcept_no 40건 추출
2. 각 rcept_no에 대해 ZIP 다운로드 → XML 파싱 → SECTION-1/2 추출
3. collector 동일 스키마로 temp/zip_full.parquet 저장
4. 두 parquet로 sections 생성 → 비교

결과 (실험 후 작성):
- (실행 후 채울 것)

결론:
- (실행 후 채울 것)

실험일: 2026-03-24
"""

from __future__ import annotations

import io
import re
import time
import zipfile
from pathlib import Path

import polars as pl
from bs4 import BeautifulSoup
from lxml import etree

from dartlab.engines.company.dart.openapi.client import DartClient

TEMP_DIR = Path(__file__).parent / "temp"


# ── XML → 텍스트 변환 (collector와 동일 로직) ──

def _tableToMarkdown(table) -> str:
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
    """XML/HTML → 텍스트. collector의 _htmlToText와 완전 동일 로직."""
    soup = BeautifulSoup(xmlStr, "lxml")
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()
    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"\n\n{md}\n\n", "lxml"))
        else:
            table.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li"]):  # collector와 동일 (tu, te 제외)
        p.insert_after("\n")
    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _getFullContent(element) -> str:
    """element 전체를 텍스트로 변환 (하위 section 포함, TITLE만 제거).

    collector가 DART 웹 뷰어에서 대분류 페이지를 크롤링하면
    하위 소분류 HTML이 전부 포함되어 있다.
    ZIP에서도 동일한 결과를 내려면 SECTION-1의 전체 XML을 텍스트화해야 한다.
    """
    xmlStr = etree.tostring(element, encoding="unicode")
    tag = element.tag
    xmlStr = re.sub(rf"^<{re.escape(tag)}[^>]*>", "", xmlStr, count=1)
    xmlStr = re.sub(rf"</{re.escape(tag)}>$", "", xmlStr)
    # TITLE 태그만 제거 (하위 section은 유지)
    xmlStr = re.sub(r"<title[^>]*>.*?</title>", "", xmlStr, flags=re.DOTALL | re.IGNORECASE)
    return _xmlToText(xmlStr)


def _getOwnContent(element) -> str:
    """element의 직접 content만 추출 (하위 section 제외, TITLE 제외).

    소분류(SECTION-2)용. 하위 SECTION을 제거해야 중복이 안 생긴다.
    """
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
    """DART XML → 섹션 목록 (SECTION-1/2만, SECTION-3 건너뜀).

    SECTION-1(대분류): 하위 전체 포함 content (collector 동일)
    SECTION-2(소분류): 자기 자신만 (하위 section 제외)
    """
    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    sections = []
    order = 0

    def _walk(parent):
        nonlocal order
        for child in parent:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag == "section-1":
                titleEl = child.find(".//title")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = re.sub(r"\s+", " ", title)
                else:
                    title = f"({tag})"
                # 대분류: 하위 전체 포함 (collector와 동일)
                content = _getFullContent(child)
                sections.append({
                    "order": order,
                    "title": title,
                    "content": content,
                })
                order += 1
                _walk(child)
            elif tag == "section-2":
                titleEl = child.find(".//title")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = re.sub(r"\s+", " ", title)
                else:
                    title = f"({tag})"
                # 소분류: 자기 자신만
                content = _getOwnContent(child)
                sections.append({
                    "order": order,
                    "title": title,
                    "content": content,
                })
                order += 1
                _walk(child)
            elif tag == "section-3":
                pass  # collector에 없으므로 건너뜀
            else:
                _walk(child)

    _walk(tree)
    return sections


def _collectOneZip(client: DartClient, rceptNo: str) -> list[dict] | None:
    """단일 rcept_no에 대해 ZIP → 섹션 추출."""
    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except (RuntimeError, OSError) as e:
        print(f"    ZIP 다운로드 실패: {e}")
        return None

    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    if not names:
        return None

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

    return _parseSections(xmlContent)


def main():
    client = DartClient()
    TEMP_DIR.mkdir(exist_ok=True)

    # 기존 collector parquet 로드
    from dartlab import config
    from dartlab.core.dataConfig import DATA_RELEASES
    rawPath = Path(config.dataDir) / DATA_RELEASES["docs"]["dir"] / "005930.parquet"
    rawDf = pl.read_parquet(rawPath)

    # 2016~ 정기보고서만
    filings = (
        rawDf.select("rcept_no", "rcept_date", "report_type")
        .unique(subset=["rcept_no"])
        .filter(pl.col("rcept_date") >= "20160101")
        .filter(pl.col("report_type").str.contains("사업보고서|분기보고서|반기보고서"))
        .sort("rcept_date")
    )

    rceptList = filings.to_dicts()
    print(f"수집 대상: {len(rceptList)}건")

    # collector parquet에서 메타데이터 가져오기
    firstRow = rawDf.filter(pl.col("rcept_no") == rceptList[0]["rcept_no"]).row(0, named=True)
    corpCode = firstRow["corp_code"]
    corpName = firstRow["corp_name"]

    # ── ZIP 전체 수집 ──
    allRows = []
    failCount = 0
    startTime = time.time()

    for i, filing in enumerate(rceptList):
        rceptNo = filing["rcept_no"]
        rceptDate = filing["rcept_date"]
        reportType = filing["report_type"]
        year = rceptDate[:4]

        print(f"  [{i + 1:2d}/{len(rceptList)}] {rceptNo} {reportType}...", end=" ", flush=True)

        sections = _collectOneZip(client, rceptNo)
        if sections is None:
            failCount += 1
            print("FAIL")
            continue

        for s in sections:
            allRows.append({
                "corp_code": corpCode,
                "corp_name": corpName,
                "year": year,
                "rcept_date": rceptDate,
                "rcept_no": rceptNo,
                "report_type": reportType,
                "section_order": s["order"],
                "section_title": s["title"],
                "section_url": "",
                "section_content": s["content"],
            })

        print(f"{len(sections)}섹션")

    elapsed = time.time() - startTime
    print(f"\n수집 완료: {len(rceptList) - failCount}/{len(rceptList)}건, "
          f"{len(allRows)}행, {elapsed:.1f}초, 실패 {failCount}건")

    # parquet 저장
    zipDf = pl.DataFrame(allRows)

    # 타입 맞추기
    collSchema = rawDf.schema
    for col in zipDf.columns:
        if col in collSchema and collSchema[col] != zipDf.schema[col]:
            zipDf = zipDf.with_columns(pl.col(col).cast(collSchema[col]))

    zipPath = TEMP_DIR / "zip_full.parquet"
    zipDf.write_parquet(zipPath)
    print(f"\nZIP parquet → {zipPath} ({zipDf.height}행)")

    # collector도 같은 기간으로 잘라서 저장
    collFiltered = rawDf.filter(
        (pl.col("rcept_date") >= "20160101")
        & pl.col("report_type").str.contains("사업보고서|분기보고서|반기보고서")
    )
    collPath = TEMP_DIR / "collector_full.parquet"
    collFiltered.write_parquet(collPath)
    print(f"collector parquet → {collPath} ({collFiltered.height}행)")

    # ── 기본 통계 비교 ──
    print("\n" + "=" * 80)
    print("기본 통계")
    print("=" * 80)
    print(f"  collector: {collFiltered.height}행, {collFiltered.n_unique('rcept_no')}건")
    print(f"  ZIP:       {zipDf.height}행, {zipDf.n_unique('rcept_no')}건")
    print(f"  스키마 일치: {collFiltered.schema == zipDf.schema}")

    # rcept_no별 행 수 비교
    collCounts = collFiltered.group_by("rcept_no").len().rename({"len": "coll_rows"})
    zipCounts = zipDf.group_by("rcept_no").len().rename({"len": "zip_rows"})
    merged = collCounts.join(zipCounts, on="rcept_no", how="outer_coalesce")
    merged = merged.with_columns([
        pl.col("coll_rows").fill_null(0),
        pl.col("zip_rows").fill_null(0),
    ])

    print(f"\n{'rcept_no':20s} | {'coll':>5s} | {'zip':>5s} | 차이")
    print("-" * 50)
    diffCount = 0
    for row in merged.sort("rcept_no").iter_rows(named=True):
        diff = row["zip_rows"] - row["coll_rows"]
        if diff != 0:
            diffCount += 1
            print(f"  {row['rcept_no']:20s} | {row['coll_rows']:5d} | {row['zip_rows']:5d} | {diff:+d}")
    if diffCount == 0:
        print("  (모두 동일)")
    else:
        print(f"\n  차이 있는 건: {diffCount}/{merged.height}")

    print(f"\n저장 완료. sections 비교는 별도 실험(010)에서 진행")
    print(f"  {TEMP_DIR / 'collector_full.parquet'}")
    print(f"  {TEMP_DIR / 'zip_full.parquet'}")


if __name__ == "__main__":
    main()
