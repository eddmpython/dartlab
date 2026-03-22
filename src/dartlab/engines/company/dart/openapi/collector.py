"""DART 공시문서 수집기 — eddmpython DartDocs.py 포팅.

프록시 없이 requests 기반 동기 크롤링.
DartClient를 재사용하여 API 키 관리를 openapi 체계에 통합.

사용법::

    from dartlab.engines.company.dart.openapi.collector import DocsCollector

    collector = DocsCollector("005930")
    collector.collect(quarters=8)

    # 여러 종목
    from dartlab.engines.company.dart.openapi.collector import collectMultiple
    collectMultiple(["005930", "000660"], quarters=8)

CLI::

    dartlab collect 005930
    dartlab collect 005930 --quarters 12
    dartlab collect --stats
"""

from __future__ import annotations

import random
import re
import time
from datetime import datetime
from pathlib import Path

import polars as pl
import requests
from bs4 import BeautifulSoup

from dartlab import config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.engines.company.dart.openapi.client import DartClient
from dartlab.engines.company.dart.openapi.corpCode import findCorpCode, loadCorpCodes
from dartlab.engines.company.dart.openapi.disclosure import listFilings

# ── 상수 ──────────────────────────────────────────────

_MIN_CONTENT_LENGTH = 50
_REQUEST_TIMEOUT = 30
_DART_VIEWER_BASE = "http://dart.fss.or.kr/report/viewer.do"
_DART_MAIN_BASE = "https://dart.fss.or.kr/dsaf001/main.do"

# 하위 섹션 URL 파싱용 정규식 (다중 페이지)
_MULTI_PAGE_RE = re.compile(
    r"\s+node[12]\['text'\][ =]+\"(.*?)\"\;"
    r"\s+node[12]\['id'\][ =]+\"(\d+)\";"
    r"\s+node[12]\['rcpNo'\][ =]+\"(\d+)\";"
    r"\s+node[12]\['dcmNo'\][ =]+\"(\d+)\";"
    r"\s+node[12]\['eleId'\][ =]+\"(\d+)\";"
    r"\s+node[12]\['offset'\][ =]+\"(\d+)\";"
    r"\s+node[12]\['length'\][ =]+\"(\d+)\";"
    r"\s+node[12]\['dtd'\][ =]+\"(.*?)\";"
    r"\s+node[12]\['tocNo'\][ =]+\"(\d+)\";"
)

_SINGLE_PAGE_RE = re.compile(r"\t\tviewDoc\('(\d+)', '(\d+)', '(\d+)', '(\d+)', '(\d+)', '(\S+)',''\)\;")


# ── HTML → 텍스트 변환 ───────────────────────────────


def _tableToMarkdown(table) -> str:
    """HTML 테이블 → 마크다운 테이블."""
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells: list[str] = []
        for cell in tr.find_all(["td", "th"]):
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


def _htmlToText(html: str) -> str:
    """HTML → 텍스트 (테이블은 마크다운으로 보존)."""
    soup = BeautifulSoup(html, "lxml")

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
    for p in soup.find_all(["p", "div", "li"]):
        p.insert_after("\n")

    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── 하위 섹션 URL 파싱 ───────────────────────────────


def _parseSubDocs(content: str, rcpNo: str) -> list[dict]:
    """공시 페이지 HTML → 하위 섹션 [{title, url, order, rcept_no}]."""
    matches = _MULTI_PAGE_RE.findall(content)
    if matches:
        result = []
        for idx, m in enumerate(matches):
            params = f"rcpNo={m[2]}&dcmNo={m[3]}&eleId={m[4]}&offset={m[5]}&length={m[6]}&dtd={m[7]}"
            result.append(
                {
                    "title": m[0],
                    "url": f"{_DART_VIEWER_BASE}?{params}",
                    "order": idx,
                    "rcept_no": rcpNo,
                }
            )
        return result

    matches = _SINGLE_PAGE_RE.findall(content)
    if matches:
        titleTag = BeautifulSoup(content, "lxml").title
        docTitle = titleTag.text.strip() if titleTag else "unknown"
        m = matches[0]
        params = f"rcpNo={m[0]}&dcmNo={m[1]}&eleId={m[2]}&offset={m[3]}&length={m[4]}&dtd={m[5]}"
        return [
            {
                "title": docTitle,
                "url": f"{_DART_VIEWER_BASE}?{params}",
                "order": 0,
                "rcept_no": rcpNo,
            }
        ]

    return []


# ── requests 세션 ────────────────────────────────────


def _makeSession() -> requests.Session:
    """크롤링용 세션."""
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        }
    )
    return s


# ── 수집기 클래스 ─────────────────────────────────────


class DocsCollector:
    """DART 공시문서 수집기.

    Parameters
    ----------
    stockCode : str
        종목코드 (6자리).
    client : DartClient | None
        기존 클라이언트 재사용. None이면 새로 생성 (환경변수에서 API 키 탐색).
    """

    def __init__(self, stockCode: str, *, client: DartClient | None = None):
        self.stockCode = stockCode
        self._client = client or DartClient()
        self._corpCode = findCorpCode(self._client, stockCode)
        if self._corpCode is None:
            raise ValueError(f"종목코드 '{stockCode}'에 해당하는 corp_code를 찾을 수 없습니다")

        # corp_name 조회
        codes = loadCorpCodes(self._client)
        match = codes.filter(pl.col("stock_code") == stockCode)
        self.corpName = match["corp_name"][0] if match.height > 0 else stockCode

        self._dataDir = _resolveDataDir()
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

    def _getFilingList(
        self,
        *,
        quarters: int = 8,
        includeQuarterly: bool = True,
    ) -> pl.DataFrame:
        """수집 대상 공시 목록 조회."""
        years = (quarters + 3) // 4
        startYear = datetime.now().year - years
        start = f"{startYear}0101"

        filings = listFilings(
            self._client,
            self.stockCode,
            start=start,
            filingType="A",
            fetchAll=True,
        )

        if filings.is_empty():
            return filings

        if not includeQuarterly:
            annualKw = ["사업보고서", "연결재무제표"]
            quarterKw = ["분기", "반기"]
            mask = pl.lit(False)
            for kw in annualKw:
                mask = mask | pl.col("report_nm").str.contains(kw, literal=True)
            qMask = pl.lit(False)
            for kw in quarterKw:
                qMask = qMask | pl.col("report_nm").str.contains(kw, literal=True)
            filings = filings.filter(mask & ~qMask)

        if self._existingReports:
            filings = filings.filter(~pl.col("rcept_no").is_in(list(self._existingReports)))

        return filings

    def _appendSections(self, newSections: list[dict]) -> int:
        """새 섹션을 parquet에 추가 (원자적 교체)."""
        newDf = pl.DataFrame(newSections)

        if self._parquetPath.exists():
            existingDf = pl.read_parquet(self._parquetPath)
            combinedDf = pl.concat([existingDf, newDf])
        else:
            combinedDf = newDf

        tmpPath = self._parquetPath.with_suffix(".parquet.tmp")
        combinedDf.write_parquet(tmpPath)

        if self._parquetPath.exists():
            self._parquetPath.unlink()
        tmpPath.rename(self._parquetPath)

        return len(newSections)

    def collect(
        self,
        *,
        quarters: int = 8,
        includeQuarterly: bool = True,
        minDelay: float = 5.0,
        maxDelay: float = 10.0,
    ) -> int:
        """공시문서 수집 (동기 — requests 기반 순차 크롤링).

        Parameters
        ----------
        quarters : int
            최근 분기 수 (기본 8 = 2년치).
        includeQuarterly : bool
            분기/반기보고서 포함 여부.
        minDelay : float
            요청 간 최소 대기 초.
        maxDelay : float
            요청 간 최대 대기 초.

        Returns
        -------
        int
            저장된 섹션 수.
        """
        filings = self._getFilingList(
            quarters=quarters,
            includeQuarterly=includeQuarterly,
        )

        if filings.is_empty():
            print(f"수집할 문서 없음: {self.corpName}")
            return 0

        print(f"수집 대상: {filings.height}건 ({self.corpName})")

        rceptNos = filings["rcept_no"].to_list()
        rceptDates = filings["rcept_dt"].to_list()
        reportNames = filings["report_nm"].to_list()
        corpNames = (
            filings["corp_name"].to_list() if "corp_name" in filings.columns else [self.corpName] * len(rceptNos)
        )

        from alive_progress import alive_bar

        session = _makeSession()

        # Phase 1: 하위 섹션 URL 수집
        allSubDocs: list[dict] = []
        failCount1 = 0

        with alive_bar(
            len(rceptNos),
            title=f"[1/2] 목차 수집 ({self.corpName})",
            bar="smooth",
        ) as bar:
            for i, rcpNo in enumerate(rceptNos):
                url = f"{_DART_MAIN_BASE}?rcpNo={rcpNo}"
                try:
                    resp = session.get(url, timeout=_REQUEST_TIMEOUT)
                    resp.raise_for_status()
                    subDocs = _parseSubDocs(resp.text, rcpNo)
                    for sd in subDocs:
                        sd["rcept_date"] = rceptDates[i]
                        sd["report_type"] = reportNames[i]
                        sd["corp_name"] = corpNames[i]
                    allSubDocs.extend(subDocs)
                    bar.text(f"{rcpNo} → {len(subDocs)}개")
                except requests.RequestException:
                    failCount1 += 1
                    bar.text(f"{rcpNo} 실패")

                bar()
                if i < len(rceptNos) - 1:
                    time.sleep(random.uniform(minDelay, maxDelay))

        if failCount1:
            print(f"  목차 수집 실패: {failCount1}건")

        if not allSubDocs:
            print("하위문서 없음")
            return 0

        # Phase 2: HTML 수집 및 텍스트 변환
        uniqueUrls = []
        seen: set[str] = set()
        for sd in allSubDocs:
            if sd["url"] not in seen:
                uniqueUrls.append(sd["url"])
                seen.add(sd["url"])

        uniqueReports = len(set(sd["rcept_no"] for sd in allSubDocs))
        urlToHtml: dict[str, str] = {}
        failCount2 = 0

        with alive_bar(
            len(uniqueUrls),
            title=f"[2/2] HTML 수집 ({uniqueReports}개 보고서, {len(uniqueUrls)}개 섹션)",
            bar="smooth",
        ) as bar:
            for i, url in enumerate(uniqueUrls):
                try:
                    resp = session.get(url, timeout=_REQUEST_TIMEOUT)
                    resp.raise_for_status()
                    urlToHtml[url] = resp.text
                except requests.RequestException:
                    failCount2 += 1

                bar()
                if i < len(uniqueUrls) - 1:
                    time.sleep(random.uniform(minDelay, maxDelay))

        if failCount2:
            print(f"  HTML 수집 실패: {failCount2}건")

        # Phase 3: 텍스트 변환 → parquet 저장
        allSections: list[dict] = []
        seenReports: set[str] = set()

        for sd in allSubDocs:
            url = sd["url"]
            if url not in urlToHtml:
                continue

            text = _htmlToText(urlToHtml[url])
            if len(text.strip()) < _MIN_CONTENT_LENGTH:
                continue

            rcpNo = sd["rcept_no"]
            rceptDate = sd["rcept_date"]
            year = rceptDate[:4] if len(rceptDate) >= 4 else "unknown"

            allSections.append(
                {
                    "corp_code": self._corpCode,
                    "corp_name": sd["corp_name"],
                    "stock_code": self.stockCode,
                    "year": year,
                    "rcept_date": rceptDate,
                    "rcept_no": rcpNo,
                    "report_type": sd["report_type"],
                    "section_order": sd["order"],
                    "section_title": sd["title"],
                    "section_url": url,
                    "section_content": text,
                }
            )
            seenReports.add(rcpNo)

        if allSections:
            savedCount = self._appendSections(allSections)
            print(f"\n저장 완료: {len(seenReports)}개 보고서, {savedCount}개 섹션")
            print(f"파일: {self._parquetPath}")
            self._loadExisting()
            return savedCount

        print("저장할 섹션 없음")
        return 0


# ── 배치 수집 헬퍼 ────────────────────────────────────


def _resolveDataDir() -> Path:
    """docs 데이터 디렉토리 (dartlab 캐시 경로)."""
    root = Path(_cfg.dataDir)
    d = root / DATA_RELEASES["docs"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def collectMultiple(
    stockCodes: list[str],
    *,
    quarters: int = 8,
    includeQuarterly: bool = True,
    minDelay: float = 5.0,
    maxDelay: float = 10.0,
    stockDelay: tuple[float, float] = (30.0, 60.0),
    client: DartClient | None = None,
) -> dict[str, int]:
    """여러 종목 순차 수집.

    Returns
    -------
    dict
        {종목코드: 저장된 섹션 수}. 실패 시 -1.
    """
    sharedClient = client or DartClient()
    results: dict[str, int] = {}
    successCount = 0
    failCount = 0

    for i, code in enumerate(stockCodes):
        print(f"\n{'=' * 60}")
        print(f"[{i + 1}/{len(stockCodes)}] {code}")
        print("=" * 60)

        try:
            collector = DocsCollector(code, client=sharedClient)
            count = collector.collect(
                quarters=quarters,
                includeQuarterly=includeQuarterly,
                minDelay=minDelay,
                maxDelay=maxDelay,
            )
            results[code] = count
            if count > 0:
                successCount += 1
        except (ValueError, OSError) as e:
            print(f"수집 실패: {e}")
            results[code] = -1
            failCount += 1

        if i < len(stockCodes) - 1:
            delay = random.uniform(*stockDelay)
            print(f"\n다음 종목까지 {delay:.0f}초 대기...")
            time.sleep(delay)

    print(f"\n전체 완료: 성공 {successCount} / 실패 {failCount} / 총 {len(stockCodes)}")
    return results


def listUncollected(*, client: DartClient | None = None) -> list[tuple[str, str]]:
    """아직 수집되지 않은 상장 종목 리스트.

    Returns
    -------
    list
        [(종목코드, 회사명), ...]
    """
    c = client or DartClient()
    codes = loadCorpCodes(c)

    listed = codes.filter(pl.col("stock_code").is_not_null() & (pl.col("stock_code").str.strip_chars() != ""))

    dataDir = _resolveDataDir()
    existing = {f.stem for f in dataDir.glob("*.parquet") if not f.name.startswith(".")}

    uncollected = listed.filter(~pl.col("stock_code").is_in(list(existing)))
    return list(
        zip(
            uncollected["stock_code"].to_list(),
            uncollected["corp_name"].to_list(),
        )
    )


def collectionStats(*, client: DartClient | None = None) -> dict:
    """수집 현황 통계."""
    c = client or DartClient()
    codes = loadCorpCodes(c)

    listed = codes.filter(pl.col("stock_code").is_not_null() & (pl.col("stock_code").str.strip_chars() != ""))

    dataDir = _resolveDataDir()
    existing = {f.stem for f in dataDir.glob("*.parquet") if not f.name.startswith(".")}
    collected = listed.filter(pl.col("stock_code").is_in(list(existing)))

    return {
        "totalListed": listed.height,
        "collected": collected.height,
        "uncollected": listed.height - collected.height,
    }


def listUncollectedKind(
    *,
    limit: int | None = None,
) -> list[tuple[str, str]]:
    """KRX KIND 기준 미수집 상장 종목 리스트.

    corp_code API 없이도 동작 (KIND HTML만 사용).

    Parameters
    ----------
    limit : int | None
        최대 개수. None이면 전체.

    Returns
    -------
    list
        [(종목코드, 회사명), ...]
    """
    from dartlab.engines.gather.listing import getKindList

    kindDf = getKindList()
    kindDf = kindDf.filter(pl.col("종목코드").str.contains(r"^\d{6}$"))

    dataDir = _resolveDataDir()
    existing = {f.stem for f in dataDir.glob("*.parquet") if not f.name.startswith(".")}

    uncollected = kindDf.filter(~pl.col("종목코드").is_in(list(existing)))

    result = list(
        zip(
            uncollected["종목코드"].to_list(),
            uncollected["회사명"].to_list(),
        )
    )
    if limit:
        result = result[:limit]
    return result
