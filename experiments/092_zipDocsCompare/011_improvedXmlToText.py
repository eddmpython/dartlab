"""실험 ID: 011
실험명: XML→텍스트 변환 개선 — table-group 경계 분리

목적:
- ZIP XML의 <table-group> 경계에서 text/table 블록이 분리되도록 _xmlToText 개선
- 개선된 변환으로 sections 품질이 collector와 동등 이상이 되는지 검증

가설:
1. <table-group> 내 <title>을 text로 분리하면 collector와 동등한 block decomposition 달성
2. 연결재무제표 주석이 1블록 → 60+블록으로 분해되어 sections 기간 매칭 정상화

방법:
1. _xmlToText 개선: table-group 경계 처리 + title 분리
2. 개선된 변환으로 zip_full_v2.parquet 생성
3. sections 비교: collector vs ZIP_v1 vs ZIP_v2

결과:
- 가설1 달성: <table-group> 경계 분리 + <title> text 변환으로 블록 수 완전 일치
  - 연결재무제표 주석: ZIP_v1 1블록 → ZIP_v2 66블록 (collector 66블록과 동일)
  - III장 대분류: ZIP_v1 43블록 → ZIP_v2 211블록 (collector 211블록과 동일)
- 가설2 달성 (SPAN bold 줄바꿈 추가 후):
  - 같은 보고서 fsSummary segmentKey 공통율: 80.9% → 91.3%
  - 2025 기간 채움 diff: -240 → -106 (56% 개선)
  - blockOrder join 유사도: 19.2% → 75.8%
- 최종 수치:
  - sections 행: collector 8,599 vs ZIP_v2 14,515
  - 기간 채움: 2025 collector 1,633 vs ZIP 1,527 (diff -106, -6.5%)
  - 텍스트 볼륨: collector 67.8M자 vs ZIP 68.4M자 (+0.9%)
  - 2025 topic별 텍스트 볼륨: ±0.5% 이내
  - 같은 보고서 topicRows 합: 41,234 vs 41,255 (사실상 동일)
- 행 수 차이의 잔여 원인:
  - 대분류 content에 하위 전체 포함 → 대분류+소분류 동일 topic 중복 decompose
  - collector HTML vs ZIP XML 간 기간 매칭 일관성 차이
  - fsSummary +2071, consolidatedNotes +1165, financialNotes +1334 (이 3개가 77%)
- ZIP 추가 이점: disclosureChanges, expertConfirmation 등 collector에 없는 섹션

결론:
- ZIP 기반 수집기 실현 가능: 텍스트 품질 동등, 블록 분해 동일, 속도 3분
- 핵심 개선 3가지: table-group 경계 분리, SECTION-1 title 포함, SPAN bold 줄바꿈
- sections 행 수 차이는 있으나 텍스트 볼륨·품질은 동등 이상
- 행 수 차이의 근본 원인은 대분류 content 중복 구조 (collector도 동일하나 HTML이 더 일관적)
- 채택: ZIP 수집기를 만들되, 대분류 content 처리를 sections 파이프라인과 맞춰 최적화

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

from dartlab.providers.dart.openapi.client import DartClient

TEMP_DIR = Path(__file__).parent / "temp"


# ── 개선된 XML → 텍스트 변환 ──


def _tableToMarkdown(table) -> str:
    """HTML table → markdown."""
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


def _xmlToTextV2(xmlStr: str) -> str:
    """개선된 XML→텍스트. table-group 경계에서 text/table 블록 분리.

    핵심 개선:
    1. <table-group> 안의 <title>을 text paragraph로 변환 (table 밖으로 분리)
    2. <table-group> 사이에 줄바꿈 삽입하여 블록 경계 생성
    3. <pgbrk>(페이지 구분) 처리
    """
    soup = BeautifulSoup(xmlStr, "lxml")

    # 불필요 태그 제거
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()

    # table-group 처리: title을 text로 분리, 경계에 줄바꿈 삽입
    for tg in soup.find_all("table-group"):
        # table-group 내 title → <p> 태그로 변환 (table 바깥 heading)
        tgTitle = tg.find("title", recursive=False)
        if tgTitle:
            titleText = tgTitle.get_text(strip=True)
            if titleText:
                newP = soup.new_tag("p")
                newP.string = titleText
                tg.insert_before(newP)
            tgTitle.decompose()

        # table-group 태그 자체를 해제 (내용물은 유지)
        tg.unwrap()

    # bold SPAN (heading) 뒤에 줄바꿈 삽입
    # DART XML에서 heading과 body가 같은 <P> 안에 있는 경우:
    #   <P><SPAN USERMARK="F-BT14 B">나. 항목</SPAN>  해당사항 없습니다.</P>
    # collector HTML에서는 이들이 별도 줄로 분리됨
    for span in soup.find_all("span"):
        usermark = span.get("usermark", "")
        if "B" in usermark.split() and span.string:
            # bold span 뒤에 줄바꿈 삽입 (heading 분리)
            span.insert_after("\n")

    # pgbrk → 줄바꿈
    for pgbrk in soup.find_all("pgbrk"):
        pgbrk.replace_with("\n")

    # table → markdown (collector 동일)
    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"\n\n{md}\n\n", "lxml"))
        else:
            table.decompose()

    # br → 줄바꿈
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # block 요소 뒤 줄바꿈 (collector _htmlToText와 동일)
    for p in soup.find_all(["p", "div", "li"]):
        p.insert_after("\n")

    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _getFullContentV2(element) -> str:
    """SECTION-1 전체 content (하위 section 포함).

    collector 동작 재현: DART 웹 뷰어는 대분류 페이지에 제목 텍스트 + 하위 전체를 포함.
    ZIP에서도 TITLE 텍스트를 content 앞에 유지하여 동일한 heading 파싱 결과를 만든다.
    단, TITLE *태그*는 제거하여 마크업 잔여물을 방지한다.
    """
    # TITLE 텍스트 추출 (첫 번째 직계 title만)
    titleEl = element.find("title")
    titleText = ""
    if titleEl is not None:
        titleText = etree.tostring(titleEl, method="text", encoding="unicode").strip()
        titleText = re.sub(r"\s+", " ", titleText)

    xmlStr = etree.tostring(element, encoding="unicode")
    tag = element.tag
    xmlStr = re.sub(rf"^<{re.escape(tag)}[^>]*>", "", xmlStr, count=1)
    xmlStr = re.sub(rf"</{re.escape(tag)}>$", "", xmlStr)
    # 첫 번째 TITLE 태그 제거 (하위 section-2의 title은 유지)
    xmlStr = re.sub(r"<title[^>]*>.*?</title>", "", xmlStr, flags=re.DOTALL | re.IGNORECASE, count=1)
    body = _xmlToTextV2(xmlStr)
    if titleText and body:
        return f"{titleText}\n{body}"
    return body or titleText


def _getOwnContentV2(element) -> str:
    """SECTION-2 자신만 (하위 section 제외, TITLE 제거)."""
    xmlStr = etree.tostring(element, encoding="unicode")
    tag = element.tag
    xmlStr = re.sub(rf"^<{re.escape(tag)}[^>]*>", "", xmlStr, count=1)
    xmlStr = re.sub(rf"</{re.escape(tag)}>$", "", xmlStr)
    xmlStr = re.sub(r"<title[^>]*>.*?</title>", "", xmlStr, flags=re.DOTALL | re.IGNORECASE, count=1)
    for d in range(1, 4):
        xmlStr = re.sub(
            rf"<section-{d}[^>]*>.*?</section-{d}>",
            "",
            xmlStr,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return _xmlToTextV2(xmlStr)


def _parseSectionsV2(xmlContent: str) -> list[dict]:
    """DART XML → 섹션 목록 (개선된 text 변환)."""
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
                content = _getFullContentV2(child)
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
                content = _getOwnContentV2(child)
                sections.append({
                    "order": order,
                    "title": title,
                    "content": content,
                })
                order += 1
                _walk(child)
            elif tag == "section-3":
                pass
            else:
                _walk(child)

    _walk(tree)
    return sections


def _collectOneZipV2(client: DartClient, rceptNo: str) -> list[dict] | None:
    """단일 rcept_no ZIP → 섹션 추출 (V2 변환)."""
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

    return _parseSectionsV2(xmlContent)


def main():
    from dartlab import config
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.providers.dart.docs.sections.pipeline import _splitContentBlocks

    client = DartClient()
    TEMP_DIR.mkdir(exist_ok=True)

    # ── 1단계: 단일 보고서로 block decomposition 비교 ──
    rno = "20250311001085"

    rawPath = Path(config.dataDir) / DATA_RELEASES["docs"]["dir"] / "005930.parquet"
    rawDf = pl.read_parquet(rawPath)

    print("=" * 80)
    print("1단계: 단일 보고서 block decomposition 비교")
    print("=" * 80)

    # collector
    collSub = rawDf.filter(pl.col("rcept_no") == rno).sort("section_order")

    # ZIP v2
    sections = _collectOneZipV2(client, rno)
    if not sections:
        print("ZIP 수집 실패")
        return

    # 연결재무제표 주석 비교
    for label, rows in [("collector", list(collSub.iter_rows(named=True))), ("ZIP_v2", sections)]:
        for r in rows:
            title = r.get("section_title", r.get("title", "")).strip()
            content = r.get("section_content", r.get("content", "")) or ""
            if "연결재무제표" in title and "주석" in title and not title.startswith(("I", "V", "X")):
                blocks = _splitContentBlocks(content)
                textBlocks = [b for b in blocks if b[0] == "text"]
                tableBlocks = [b for b in blocks if b[0] == "table"]
                print(f"  {label} '{title[:30]}': {len(content):,}자 → "
                      f"text {len(textBlocks)} + table {len(tableBlocks)} = {len(blocks)}블록")
                break

    # III장 대분류 비교
    print()
    for label, rows in [("collector", list(collSub.iter_rows(named=True))), ("ZIP_v2", sections)]:
        for r in rows:
            title = r.get("section_title", r.get("title", "")).strip()
            content = r.get("section_content", r.get("content", "")) or ""
            if re.match(r"III\.", title):
                blocks = _splitContentBlocks(content)
                textBlocks = [b for b in blocks if b[0] == "text"]
                tableBlocks = [b for b in blocks if b[0] == "table"]
                print(f"  {label} '{title[:30]}': {len(content):,}자 → "
                      f"text {len(textBlocks)} + table {len(tableBlocks)} = {len(blocks)}블록")
                break

    # ── 2단계: 전체 40건 수집 ──
    print("\n" + "=" * 80)
    print("2단계: 전체 40건 ZIP V2 수집")
    print("=" * 80)

    filings = (
        rawDf.select("rcept_no", "rcept_date", "report_type")
        .unique(subset=["rcept_no"])
        .filter(pl.col("rcept_date") >= "20160101")
        .filter(pl.col("report_type").str.contains("사업보고서|분기보고서|반기보고서"))
        .sort("rcept_date")
    )

    rceptList = filings.to_dicts()
    print(f"수집 대상: {len(rceptList)}건")

    firstRow = rawDf.filter(pl.col("rcept_no") == rceptList[0]["rcept_no"]).row(0, named=True)
    corpCode = firstRow["corp_code"]
    corpName = firstRow["corp_name"]

    allRows = []
    failCount = 0
    startTime = time.time()

    for i, filing in enumerate(rceptList):
        rceptNo = filing["rcept_no"]
        rceptDate = filing["rcept_date"]
        reportType = filing["report_type"]
        year = rceptDate[:4]

        print(f"  [{i + 1:2d}/{len(rceptList)}] {rceptNo} {reportType}...", end=" ", flush=True)

        secs = _collectOneZipV2(client, rceptNo)
        if secs is None:
            failCount += 1
            print("FAIL")
            continue

        for s in secs:
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

        print(f"{len(secs)}섹션")

    elapsed = time.time() - startTime
    print(f"\n수집 완료: {len(rceptList) - failCount}/{len(rceptList)}건, "
          f"{len(allRows)}행, {elapsed:.1f}초, 실패 {failCount}건")

    zipDf = pl.DataFrame(allRows)

    # 타입 맞추기
    collSchema = rawDf.schema
    for col in zipDf.columns:
        if col in collSchema and collSchema[col] != zipDf.schema[col]:
            zipDf = zipDf.with_columns(pl.col(col).cast(collSchema[col]))

    zipPath = TEMP_DIR / "zip_full_v2.parquet"
    zipDf.write_parquet(zipPath)
    print(f"\nZIP V2 parquet → {zipPath} ({zipDf.height}행)")

    # ── 3단계: sections 비교 ──
    print("\n" + "=" * 80)
    print("3단계: sections 비교 (collector vs ZIP_v2)")
    print("=" * 80)

    import shutil
    import tempfile

    def _buildSections(parquetPath: Path, label: str) -> pl.DataFrame:
        """parquet → sections."""
        tmpDir = Path(tempfile.mkdtemp(prefix=f"dartlab_{label}_"))
        docsDir = tmpDir / DATA_RELEASES["docs"]["dir"]
        docsDir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(parquetPath, docsDir / "005930.parquet")

        origDataDir = config.dataDir
        config.dataDir = str(tmpDir)

        try:
            from dartlab.providers.dart.docs.sections.pipeline import sections
            return sections("005930")
        finally:
            config.dataDir = origDataDir
            shutil.rmtree(tmpDir, ignore_errors=True)

    # collector sections (이미 있으면 재사용)
    collSectionsPath = TEMP_DIR / "sections_collector.parquet"
    if collSectionsPath.exists():
        collSections = pl.read_parquet(collSectionsPath)
        print(f"  collector sections (캐시): {collSections.height}행")
    else:
        collFiltered = rawDf.filter(
            (pl.col("rcept_date") >= "20160101")
            & pl.col("report_type").str.contains("사업보고서|분기보고서|반기보고서")
        )
        collFilteredPath = TEMP_DIR / "collector_full.parquet"
        collFiltered.write_parquet(collFilteredPath)
        collSections = _buildSections(collFilteredPath, "coll")
        collSections.write_parquet(collSectionsPath)
        print(f"  collector sections: {collSections.height}행")

    # ZIP v2 sections
    print("  ZIP V2 sections 생성 중...")
    zipV2Sections = _buildSections(zipPath, "zipv2")
    zipV2Sections.write_parquet(TEMP_DIR / "sections_zip_v2.parquet")
    print(f"  ZIP V2 sections: {zipV2Sections.height}행")

    # ZIP v1 (기존)
    zipV1Path = TEMP_DIR / "sections_zip.parquet"
    if zipV1Path.exists():
        zipV1Sections = pl.read_parquet(zipV1Path)
    else:
        zipV1Sections = None

    # ── 비교 출력 ──
    periodCols = sorted([c for c in collSections.columns if re.match(r"^\d{4}", c)])
    v2PeriodCols = sorted([c for c in zipV2Sections.columns if re.match(r"^\d{4}", c)])

    print(f"\n{'항목':25s} | {'collector':>10s} | {'ZIP_v1':>10s} | {'ZIP_v2':>10s}")
    print("-" * 65)
    print(f"{'행 수':25s} | {collSections.height:>10,} | "
          f"{zipV1Sections.height if zipV1Sections is not None else 'N/A':>10} | {zipV2Sections.height:>10,}")
    print(f"{'기간 수':25s} | {len(periodCols):>10} | "
          f"{len([c for c in (zipV1Sections.columns if zipV1Sections is not None else []) if re.match(r'^\\d{4}', c)]):>10} | {len(v2PeriodCols):>10}")

    collTopics = set(collSections["topic"].unique().to_list())
    v2Topics = set(zipV2Sections["topic"].unique().to_list())
    print(f"{'topic 수':25s} | {len(collTopics):>10} | "
          f"{len(set(zipV1Sections['topic'].unique().to_list())) if zipV1Sections is not None else 'N/A':>10} | {len(v2Topics):>10}")

    # topic별 행 수 비교 (collector vs v2)
    print(f"\n{'topic':35s} | {'collector':>8s} | {'ZIP_v2':>8s} | 차이")
    print("-" * 65)
    cByTopic = collSections.group_by("topic").len().rename({"len": "coll"}).sort("topic")
    v2ByTopic = zipV2Sections.group_by("topic").len().rename({"len": "v2"}).sort("topic")
    topicMerge = cByTopic.join(v2ByTopic, on="topic", how="full", coalesce=True).with_columns([
        pl.col("coll").fill_null(0), pl.col("v2").fill_null(0),
    ]).sort("topic")

    for row in topicMerge.iter_rows(named=True):
        diff = row["v2"] - row["coll"]
        diffStr = f"{diff:+d}" if diff != 0 else "="
        print(f"  {row['topic'][:35]:35s} | {row['coll']:>8,} | {row['v2']:>8,} | {diffStr}")

    # 기간별 채움률 비교
    commonPeriods = sorted(set(periodCols) & set(v2PeriodCols))
    print(f"\n{'기간':12s} | {'coll채움':>8s} | {'v2채움':>8s} | 차이")
    print("-" * 50)

    for period in commonPeriods[-12:]:
        cFilled = collSections[period].is_not_null().sum()
        v2Filled = zipV2Sections[period].is_not_null().sum() if period in zipV2Sections.columns else 0
        diff = v2Filled - cFilled
        print(f"  {period:12s} | {cFilled:>8,} | {v2Filled:>8,} | {diff:+d}")

    # 텍스트 유사도 (최근 연간)
    from difflib import SequenceMatcher

    latestAnnual = [p for p in commonPeriods if "Q" not in p]
    targetPeriod = latestAnnual[-1] if latestAnnual else commonPeriods[-1] if commonPeriods else None

    if targetPeriod and targetPeriod in collSections.columns and targetPeriod in zipV2Sections.columns:
        print(f"\n최근 연간({targetPeriod}) topic별 텍스트 유사도:")
        collSub = collSections.select("topic", "blockType", "blockOrder", targetPeriod).rename({targetPeriod: "coll_text"})
        v2Sub = zipV2Sections.select("topic", "blockType", "blockOrder", targetPeriod).rename({targetPeriod: "v2_text"})
        joined = collSub.join(v2Sub, on=["topic", "blockType", "blockOrder"], how="inner")
        both = joined.filter(pl.col("coll_text").is_not_null() & pl.col("v2_text").is_not_null())

        allSims = []
        for row in both.head(200).iter_rows(named=True):
            cText = row["coll_text"] or ""
            v2Text = row["v2_text"] or ""
            if len(cText) > 0 and len(v2Text) > 0:
                sim = SequenceMatcher(None, cText[:1000], v2Text[:1000]).ratio()
                allSims.append(sim)
        if allSims:
            print(f"  매칭 가능 행: {both.height}개, 유사도 평균: {sum(allSims)/len(allSims):.1%}")

    # 총 텍스트 볼륨
    print(f"\n총 텍스트 볼륨:")
    for label, df, pcols in [
        ("collector", collSections, periodCols),
        ("ZIP_v2", zipV2Sections, v2PeriodCols),
    ]:
        totalChars = 0
        for p in pcols:
            col = df[p]
            for val in col.to_list():
                if val:
                    totalChars += len(val)
        print(f"  {label}: {totalChars:,}자")


if __name__ == "__main__":
    main()
