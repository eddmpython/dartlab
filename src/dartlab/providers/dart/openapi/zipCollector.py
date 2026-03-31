"""ZIP(document.xml) 기반 DART 공시문서 수집기.

collector.py(HTML 크롤링)보다 빠르고 품질 동등.
실험 092_zipDocsCompare에서 검증 완료.

사용법::

    from dartlab.providers.dart.openapi.zipCollector import ZipDocsCollector

    collector = ZipDocsCollector("005930")
    collector.collect(quarters=8)
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import polars as pl
from bs4 import BeautifulSoup
from lxml import etree

from dartlab import config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.providers.dart.openapi.client import DartClient
from dartlab.providers.dart.openapi.corpCode import findCorpCode, loadCorpCodes
from dartlab.providers.dart.openapi.disclosure import listFilings

# ── 정규식 (모듈 레벨 컴파일) ──

_RE_WHITESPACE = re.compile(r"\s+")
_RE_MULTI_NEWLINE = re.compile(r"\n{3,}")

# ── XML → 텍스트 변환 ──


def _tableToMarkdown(table) -> str:
    """HTML table → markdown."""
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells: list[str] = []
        for cell in tr.find_all(["td", "th", "te"]):
            colspan = int(cell.get("colspan", 1))
            text = cell.get_text(strip=True)
            text = _RE_WHITESPACE.sub(" ", text)
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
    """DART XML → 텍스트. table-group 경계 분리 + SPAN bold 줄바꿈."""
    soup = BeautifulSoup(xmlStr, "lxml")

    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()

    for tg in soup.find_all("table-group"):
        tgTitle = tg.find("title", recursive=False)
        if tgTitle:
            titleText = tgTitle.get_text(strip=True)
            if titleText:
                newP = soup.new_tag("p")
                newP.string = titleText
                tg.insert_before(newP)
            tgTitle.decompose()
        tg.unwrap()

    for span in soup.find_all("span"):
        usermark = span.get("usermark", "")
        if "B" in usermark.split() and span.string:
            span.insert_after("\n")

    for pgbrk in soup.find_all("pgbrk"):
        pgbrk.replace_with("\n")

    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"\n\n{md}\n\n", "lxml"))
        else:
            table.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")

    for p in soup.find_all(["p", "div", "li"]):
        p.insert_after("\n")

    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = _RE_MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def _getFullContent(element) -> str:
    """SECTION-1 전체 content (하위 section 포함 + 자기 title 포함)."""
    titleEl = element.find("title")
    titleText = ""
    if titleEl is not None:
        titleText = etree.tostring(titleEl, method="text", encoding="unicode").strip()
        titleText = _RE_WHITESPACE.sub(" ", titleText)

    xmlStr = etree.tostring(element, encoding="unicode")
    tag = element.tag
    xmlStr = re.sub(rf"^<{re.escape(tag)}[^>]*>", "", xmlStr, count=1)
    xmlStr = re.sub(rf"</{re.escape(tag)}>$", "", xmlStr)
    xmlStr = re.sub(r"<title[^>]*>.*?</title>", "", xmlStr, flags=re.DOTALL | re.IGNORECASE, count=1)
    body = _xmlToText(xmlStr)
    if titleText and body:
        return f"{titleText}\n{body}"
    return body or titleText


def _getOwnContent(element) -> str:
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
    return _xmlToText(xmlStr)


def _parseSections(xmlContent: str) -> list[dict]:
    """DART XML → 섹션 목록. SECTION-1/2 추출, SECTION-3 건너뜀."""
    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    sections: list[dict] = []
    order = 0

    def _walk(parent):
        nonlocal order
        for child in parent:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag == "section-1":
                titleEl = child.find(".//title")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = _RE_WHITESPACE.sub(" ", title)
                else:
                    title = f"({tag})"
                content = _getFullContent(child)
                sections.append({"order": order, "title": title, "content": content})
                order += 1
                _walk(child)
            elif tag == "section-2":
                titleEl = child.find(".//title")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = _RE_WHITESPACE.sub(" ", title)
                else:
                    title = f"({tag})"
                content = _getOwnContent(child)
                sections.append({"order": order, "title": title, "content": content})
                order += 1
                _walk(child)
            elif tag == "section-3":
                pass
            else:
                _walk(child)

    _walk(tree)
    return sections


def _collectOneZip(client: DartClient, rceptNo: str) -> list[dict] | None:
    """단일 rcept_no ZIP → 섹션 추출."""
    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except (RuntimeError, OSError):
        return None

    if raw is None:
        return None

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        return None
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


# ── 수집기 ──


def _docsDataDir() -> Path:
    """docs parquet 저장 디렉토리."""
    root = Path(_cfg.dataDir)
    d = root / DATA_RELEASES["docs"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


class ZipDocsCollector:
    """ZIP(document.xml) 기반 DART 공시문서 수집기."""

    def __init__(
        self,
        stockCode: str,
        *,
        client: DartClient | None = None,
        corpCode: str | None = None,
        corpName: str | None = None,
    ):
        self.stockCode = stockCode
        self._client = client or DartClient()

        if corpCode and corpName:
            self._corpCode = corpCode
            self._corpName = corpName
        else:
            corpCodes = loadCorpCodes(self._client)
            match = corpCodes.filter(pl.col("stock_code") == stockCode)
            if match.height > 0:
                self._corpCode = match["corp_code"][0]
                self._corpName = match["corp_name"][0]
            else:
                self._corpCode = findCorpCode(self._client, stockCode) or ""
                self._corpName = stockCode

        self._dataDir = _docsDataDir()
        self._parquetPath = self._dataDir / f"{stockCode}.parquet"
        self._existingReports: set[str] = set()
        self._loadExisting()

    def _loadExisting(self) -> None:
        """기존 parquet에서 이미 수집된 rcept_no 세트 로드."""
        if self._parquetPath.exists():
            try:
                df = pl.scan_parquet(self._parquetPath).select("rcept_no").collect()
                self._existingReports = set(df["rcept_no"].unique().to_list())
            except (pl.exceptions.ComputeError, OSError):
                self._existingReports = set()

    def collect(
        self,
        *,
        includeQuarterly: bool = True,
        showProgress: bool = True,
        onProgress=None,
    ) -> int:
        """2016Q1부터 전체 정기보고서 수집 → parquet 저장. 반환: 저장된 섹션 수."""
        from dartlab.core.guidance import emit

        # 공시 목록 조회 (K-IFRS 전면 도입 이후)
        filings = listFilings(
            self._client,
            self.stockCode,
            start="20160101",
            filingType="A",
            fetchAll=True,
        )
        if filings.height == 0:
            return 0

        # 정기보고서만 + 분기보고서 선택
        reportFilter = r"사업보고서|반기보고서"
        if includeQuarterly:
            reportFilter += r"|분기보고서"
        filings = filings.filter(pl.col("report_nm").str.contains(reportFilter))
        filings = filings.sort("rcept_dt", descending=True)

        # 이미 수집된 것 제외
        newFilings = filings.filter(~pl.col("rcept_no").is_in(list(self._existingReports)))
        if newFilings.height == 0:
            return 0

        # ZIP 수집
        from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

        allSections: list[dict] = []
        failCount = 0
        total = newFilings.height

        _progress = Progress(
            SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(), MofNCompleteColumn(),
            disable=not showProgress,
        )
        _task = _progress.add_task(f"docs 수집 | {self._corpName}", total=total)
        with _progress:
            for rowIdx, row in enumerate(newFilings.iter_rows(named=True)):
                rceptNo = row["rcept_no"]
                rceptDt = row["rcept_dt"]
                reportNm = row["report_nm"]

                # 결산연도: report_nm에서 추출 (예: "사업보고서 (2025.12)" → "2025")
                ym = re.search(r"\((\d{4})\.\d{2}\)", reportNm)
                year = ym.group(1) if ym else rceptDt[:4]

                _progress.update(_task, description=f"docs | {self._corpName} | {reportNm}")
                if onProgress:
                    onProgress(f"docs {rowIdx + 1}/{total} {reportNm}")

                sections = _collectOneZip(self._client, rceptNo)
                if sections is None:
                    failCount += 1
                    _progress.advance(_task)
                    continue

                for s in sections:
                    allSections.append(
                        {
                            "corp_code": self._corpCode,
                            "corp_name": self._corpName,
                            "stock_code": self.stockCode,
                            "year": year,
                            "rcept_date": rceptDt,
                            "rcept_no": rceptNo,
                            "report_type": reportNm,
                            "section_order": s["order"],
                            "section_title": s["title"],
                            "section_url": "",
                            "section_content": s["content"],
                        }
                    )
                _progress.advance(_task)

        if not allSections:
            return 0

        # parquet 저장 (기존 파일 있으면 누적)
        newDf = pl.DataFrame(allSections)

        if self._parquetPath.exists():
            existingDf = pl.read_parquet(self._parquetPath)
            combinedDf = pl.concat([existingDf, newDf], how="diagonal_relaxed")
        else:
            combinedDf = newDf

        tmpPath = self._parquetPath.with_suffix(".parquet.tmp")
        combinedDf.write_parquet(tmpPath)

        if self._parquetPath.exists():
            self._parquetPath.unlink()
        tmpPath.rename(self._parquetPath)

        self._loadExisting()

        savedCount = len(allSections)
        if showProgress:
            emit(
                "collect:done",
                label="docs",
                sizeStr=f"{savedCount}섹션, {total - failCount}/{total}건",
            )
        return savedCount
