"""KRX KIND 상장법인 목록 — 종목코드 ↔ 회사명 매퍼."""

from __future__ import annotations

import re
import time
from html.parser import HTMLParser
from pathlib import Path

import polars as pl
import requests

CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "kindList"
CACHE_FILE = CACHE_DIR / "corpList.parquet"
CACHE_TTL = 86400

KIND_URL = "https://kind.krx.co.kr/corpgeneral/corpList.do"
KIND_DATA = {
    "method": "download",
    "searchType": "13",
    "fiscalYearEnd": "all",
    "location": "all",
}

_memory: pl.DataFrame | None = None
_memoryTs: float = 0.0


class _TableParser(HTMLParser):
    """KRX KIND HTML 테이블 → 리스트 변환."""

    def __init__(self):
        super().__init__()
        self._inTable = False
        self._inTr = False
        self._inCell = False
        self._rows: list[list[str]] = []
        self._row: list[str] = []
        self._cell = ""

    def handle_starttag(self, tag: str, attrs):
        if tag == "table":
            self._inTable = True
        elif tag == "tr" and self._inTable:
            self._inTr = True
            self._row = []
        elif tag in ("td", "th") and self._inTr:
            self._inCell = True
            self._cell = ""

    def handle_endtag(self, tag: str):
        if tag in ("td", "th") and self._inCell:
            self._inCell = False
            self._row.append(self._cell.strip())
        elif tag == "tr" and self._inTr:
            self._inTr = False
            if self._row:
                self._rows.append(self._row)
        elif tag == "table":
            self._inTable = False

    def handle_data(self, data: str):
        if self._inCell:
            self._cell += data


def _fetchKind() -> pl.DataFrame:
    try:
        r = requests.post(KIND_URL, data=KIND_DATA)
    except requests.exceptions.SSLError:
        r = requests.post(KIND_URL, data=KIND_DATA, verify=False)
    html = r.content.decode("euc-kr", errors="replace")

    parser = _TableParser()
    parser.feed(html)
    rows = parser._rows
    if len(rows) < 2:
        return pl.DataFrame(schema={"종목코드": pl.Utf8, "회사명": pl.Utf8})

    header = rows[0]
    data = rows[1:]
    records = [dict(zip(header, r)) for r in data if len(r) == len(header)]
    df = pl.DataFrame(records)

    if "종목코드" not in df.columns:
        return pl.DataFrame(schema={"종목코드": pl.Utf8, "회사명": pl.Utf8})

    df = df.with_columns(
        pl.col("종목코드").cast(pl.Utf8).str.zfill(6)
    )
    df = df.filter(
        pl.col("종목코드").str.contains(r"^[0-9A-Z]{6}$")
    )
    df = df.filter(
        ~pl.col("회사명").str.contains(r"스팩|리츠")
    )
    df = df.unique(subset=["종목코드"]).sort("종목코드")
    return df


def _loadCache() -> pl.DataFrame | None:
    if not CACHE_FILE.exists():
        return None
    age = time.time() - CACHE_FILE.stat().st_mtime
    if age > CACHE_TTL:
        return None
    return pl.read_parquet(str(CACHE_FILE))


def _saveCache(df: pl.DataFrame) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(str(CACHE_FILE))


def getKindList(*, forceRefresh: bool = False) -> pl.DataFrame:
    """KRX KIND 상장법인 전체 목록.

    캐시 우선순위: 메모리 → 파일(24h TTL) → KIND API.
    SPAC·리츠 제외, 6자리 종목코드만 포함.

    Args:
        forceRefresh: True면 캐시 무시하고 KIND API 재요청.

    Returns:
        DataFrame (회사명, 종목코드, 업종, 주요제품, 상장일, 결산월, 대표자명, 홈페이지, 지역, ...).
    """
    global _memory, _memoryTs

    if not forceRefresh and _memory is not None:
        if (time.time() - _memoryTs) < CACHE_TTL:
            return _memory

    if not forceRefresh:
        cached = _loadCache()
        if cached is not None:
            _memory = cached
            _memoryTs = time.time()
            return cached

    print("[dartlab] KRX KIND 상장법인 목록 다운로드 중...")
    df = _fetchKind()
    _saveCache(df)
    _memory = df
    _memoryTs = time.time()
    print(f"[dartlab] {df.height}개 종목 로드 완료")
    return df


def codeToName(stockCode: str) -> str | None:
    """종목코드 → 회사명."""
    df = getKindList()
    match = df.filter(pl.col("종목코드") == stockCode)
    if match.height == 0:
        return None
    return match["회사명"][0]


def nameToCode(corpName: str) -> str | None:
    """회사명 → 종목코드. 정확히 일치하는 첫 번째 결과."""
    df = getKindList()
    match = df.filter(pl.col("회사명") == corpName)
    if match.height == 0:
        return None
    return match["종목코드"][0]


def searchName(keyword: str) -> pl.DataFrame:
    """회사명 부분 검색.

    Args:
        keyword: 검색 키워드 (예: "삼성", "반도체").

    Returns:
        매칭된 종목 DataFrame (회사명, 종목코드, ...).
    """
    df = getKindList()
    return df.filter(pl.col("회사명").str.contains(keyword))
