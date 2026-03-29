"""KRX KIND + KRX data 상장법인 목록 — 종목코드 ↔ 회사��� 매퍼."""

from __future__ import annotations

import json
import logging
import threading
import time
from html.parser import HTMLParser
from pathlib import Path

import polars as pl
import requests

log = logging.getLogger(__name__)


def _cacheFile() -> Path:
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "kindList" / "corpList.parquet"


def _krxCacheFile() -> Path:
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "krxList" / "corpList.parquet"


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
_memoryLock = threading.Lock()

# fuzzySearch 캐시 — getKindList() 갱신 시 함께 갱신
_searchCache: dict[str, object] | None = None


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

    def handle_starttag(self, tag: str, _attrs):
        """HTML 여는 태그 처리."""
        if tag == "table":
            self._inTable = True
        elif tag == "tr" and self._inTable:
            self._inTr = True
            self._row = []
        elif tag in ("td", "th") and self._inTr:
            self._inCell = True
            self._cell = ""

    def handle_endtag(self, tag: str):
        """HTML 닫는 태그 처리."""
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
        """HTML 텍스트 데이터 처리."""
        if self._inCell:
            self._cell += data


def _fetchKind() -> pl.DataFrame:
    try:
        r = requests.post(KIND_URL, data=KIND_DATA, timeout=30)
    except (requests.exceptions.SSLError, requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return pl.DataFrame(schema={"종목코드": pl.Utf8, "회사명": pl.Utf8})
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

    df = df.with_columns(pl.col("종목코드").cast(pl.Utf8).str.zfill(6))
    df = df.filter(pl.col("종목코드").str.contains(r"^[0-9A-Z]{6}$"))
    df = df.filter(~pl.col("회사명").str.contains(r"스팩|리츠"))
    df = df.unique(subset=["종목코드"]).sort("종목코드")
    return df


def _loadCache() -> pl.DataFrame | None:
    path = _cacheFile()
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL:
        return None
    return pl.read_parquet(str(path))


def _saveCache(df: pl.DataFrame) -> None:
    path = _cacheFile()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(str(path))


def getKindList(*, forceRefresh: bool = False) -> pl.DataFrame:
    """KRX KIND 상장법인 전체 목록.

    캐시 우선순위: 메모리 → 파일(24h TTL) → KIND API.
    SPAC·리츠 제외, 6자리 종목코드만 포함.

    Args:
        forceRefresh: True면 캐시 무시하고 KIND API 재요청.

    Returns:
        DataFrame (회사명, 종목코드, 업종, 주요제품, 상장일, 결산월, 대표자명, 홈페이지, 지역, ...).
    """
    global _memory, _memoryTs, _searchCache

    if not forceRefresh and _memory is not None:
        if (time.time() - _memoryTs) < CACHE_TTL:
            return _memory

    with _memoryLock:
        # double-check
        if not forceRefresh and _memory is not None:
            if (time.time() - _memoryTs) < CACHE_TTL:
                return _memory

        if not forceRefresh:
            cached = _loadCache()
            if cached is not None:
                _memory = cached
                _memoryTs = time.time()
                _searchCache = None  # 데이터 변경 시 검색 캐시 무효화
                return cached

        from dartlab.core.guidance import emit

        emit("listing:download")
        df = _fetchKind()
        _saveCache(df)
        _memory = df
        _memoryTs = time.time()
        _searchCache = None  # 데이터 변경 시 검색 캐시 무효화
        emit("listing:done", count=df.height)
        return df


def _getSearchCache() -> dict[str, object]:
    """fuzzySearch용 사전 계산 캐시. names, names_lower, names_chosung을 한 번만 계산."""
    global _searchCache
    if _searchCache is not None:
        return _searchCache

    df = getKindList()
    names = df["회사명"].to_list()
    names_lower = [n.lower() for n in names]
    names_chosung = [_extract_chosung(n) for n in names]
    _searchCache = {
        "names": names,
        "names_lower": names_lower,
        "names_chosung": names_chosung,
    }
    return _searchCache


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
    kw = keyword.strip()
    if not kw:
        return getKindList().head(0)
    df = getKindList()
    return df.filter(pl.col("회사명").str.contains(kw, literal=True))


# ── 한글 초성/자모 유틸 ──────────────────────────────────────────

_CHOSUNG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_CHO_BASE = 0xAC00
_CHO_PERIOD = 588  # 21 * 28


def _decompose_char(ch: str) -> str:
    """한글 음절 → 초성 추출. 이미 자모이면 그대로."""
    cp = ord(ch)
    if 0xAC00 <= cp <= 0xD7A3:
        return _CHOSUNG[(cp - _CHO_BASE) // _CHO_PERIOD]
    if ch in _CHOSUNG:
        return ch
    return ch


def _extract_chosung(text: str) -> str:
    """문자열의 초성만 추출. 비한글은 원문 그대로."""
    return "".join(_decompose_char(c) for c in text)


def _is_all_chosung(text: str) -> bool:
    """입력이 모두 자음(초성)으로만 이루어졌는지 확인."""
    return all(c in _CHOSUNG for c in text)


def _levenshtein(s: str, t: str) -> int:
    """최소 편집 거리 (Levenshtein distance)."""
    if len(s) < len(t):
        s, t = t, s
    if not t:
        return len(s)
    prev = list(range(len(t) + 1))
    for i, sc in enumerate(s):
        curr = [i + 1]
        for j, tc in enumerate(t):
            cost = 0 if sc == tc else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def fuzzySearch(keyword: str, *, maxResults: int = 10) -> pl.DataFrame:
    """한글 fuzzy 종목 검색 — 초성 매칭 + Levenshtein 거리.

    지원:
    - 초성 검색: "ㅅㅅ" → 삼성전자, 삼성물산, ...
    - 약칭 부분매칭: "삼전" → 삼성전자 (초성 "ㅅㅈ" ⊂ "ㅅㅅㅈㅈ")
    - 오타 허용: "삼성전제" → 삼성전자 (편집거리 1)
    - 영문 오타: "samsun" → "samsung"에 가까운 종목
    - 기본 substring 매칭도 포함

    Args:
        keyword: 검색어 (한글, 영문, 초성, 혼합 모두 가능)
        maxResults: 최대 반환 수 (기본 10)

    Returns:
        매칭된 종목 DataFrame (회사명, 종목코드, ...), 관련도 순.
    """
    kw = keyword.strip()
    if not kw:
        return getKindList().head(0)

    df = getKindList()
    cache = _getSearchCache()
    names: list[str] = cache["names"]
    names_lower: list[str] = cache["names_lower"]
    names_chosung: list[str] = cache["names_chosung"]

    kw_lower = kw.lower()
    kw_chosung = _extract_chosung(kw)
    is_chosung_query = _is_all_chosung(kw)

    scored: list[tuple[int, float, int]] = []  # (idx, score, order)

    for idx in range(len(names)):
        name_lower = names_lower[idx]

        # 1) 정확 일치
        if name_lower == kw_lower:
            scored.append((idx, 0.0, 0))
            continue

        # 2) substring 매칭
        if kw_lower in name_lower:
            # prefix > contains
            score = 1.0 if name_lower.startswith(kw_lower) else 2.0
            scored.append((idx, score, len(scored)))
            continue

        # 3) 초성 매칭
        name_chosung = names_chosung[idx]
        if is_chosung_query:
            # 순수 초성 입력: "ㅅㅅ" → 초성열에서 연속 매칭
            if kw_chosung in name_chosung:
                # 앞에서 매칭될수록 높은 점수
                pos = name_chosung.index(kw_chosung)
                scored.append((idx, 3.0 + pos * 0.1, len(scored)))
                continue
        else:
            # 혼합 입력: 초성 subsequence 매칭
            # "삼전"(ㅅㅈ) → "삼성전자"(ㅅㅅㅈㅈ) 순서 매칭
            if len(kw) >= 2:
                # 연속 substring 먼저 (더 정확)
                if kw_chosung in name_chosung:
                    pos = name_chosung.index(kw_chosung)
                    scored.append((idx, 4.0 + pos * 0.1, len(scored)))
                    continue
                # subsequence fallback: 글자별 초성이 순서대로 나타나는지
                ci = 0
                first_pos = -1
                for ni, nc in enumerate(name_chosung):
                    if ci < len(kw_chosung) and nc == kw_chosung[ci]:
                        if ci == 0:
                            first_pos = ni
                        ci += 1
                if ci == len(kw_chosung) and first_pos >= 0:
                    # gap penalty: 이름이 짧을수록 좋음
                    scored.append((idx, 4.5 + first_pos * 0.1 + len(names[idx]) * 0.01, len(scored)))
                    continue

        # 4) Levenshtein (짧은 키워드에서만 — 비용 절약)
        if 2 <= len(kw) <= 10:
            dist = _levenshtein(kw_lower, name_lower)
            max_dist = max(1, len(kw) // 3)  # 3자당 1 오타 허용
            if dist <= max_dist:
                scored.append((idx, 5.0 + dist, len(scored)))
                continue

    if not scored:
        return df.head(0)

    scored.sort(key=lambda x: (x[1], x[2]))
    indices = [s[0] for s in scored[:maxResults]]
    return df[indices]


# ── KRX data.krx.co.kr 상장법인 목록 ──────────────────────────────


_KRX_URL = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
_KRX_DATA = {
    "locale": "ko_KR",
    "mktsel": "ALL",
    "typeNo": "0",
    "searchText": "",
    "bld": "dbms/comm/finder/finder_stkisu",
}
_KRX_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
}

_krxMemory: pl.DataFrame | None = None
_krxMemoryTs: float = 0.0
_krxMemoryLock = threading.Lock()


def _fetchKrx() -> pl.DataFrame:
    """KRX data.krx.co.kr에서 상장법인 목록 수집."""
    schema = {
        "full_code": pl.Utf8,
        "short_code": pl.Utf8,
        "codeName": pl.Utf8,
        "marketName": pl.Utf8,
    }
    try:
        r = requests.post(
            _KRX_URL,
            data=_KRX_DATA,
            headers=_KRX_HEADERS,
            timeout=30,
        )
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as exc:
        log.warning("KRX 상장법인 목록 수집 실패: %s", exc)
        return pl.DataFrame(schema=schema)

    if r.status_code != 200:
        log.warning("KRX 상장법인 목록 HTTP %d", r.status_code)
        return pl.DataFrame(schema=schema)

    try:
        jo = json.loads(r.text)
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("KRX 응답 JSON 파싱 실패: %s", exc)
        return pl.DataFrame(schema=schema)

    block = jo.get("block1", [])
    if not block:
        log.warning("KRX 응답에 block1 데이터 없음")
        return pl.DataFrame(schema=schema)

    df = pl.DataFrame(block)
    return df


def _loadKrxCache() -> pl.DataFrame | None:
    path = _krxCacheFile()
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL:
        return None
    return pl.read_parquet(str(path))


def _saveKrxCache(df: pl.DataFrame) -> None:
    path = _krxCacheFile()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(str(path))


def getKrxList(*, forceRefresh: bool = False) -> pl.DataFrame:
    """KRX data.krx.co.kr 상장법인 전체 목록.

    캐시 우선순위: 메모리 -> 파일(24h TTL) -> KRX API.
    KIND 목록보다 상세 컬럼(full_code, short_code, marketName 등) 제공.

    Args:
        forceRefresh: True면 캐시 무시하고 KRX API 재요청.

    Returns:
        DataFrame -- KRX 상장법인 목록.
    """
    global _krxMemory, _krxMemoryTs

    if not forceRefresh and _krxMemory is not None:
        if (time.time() - _krxMemoryTs) < CACHE_TTL:
            return _krxMemory

    with _krxMemoryLock:
        if not forceRefresh and _krxMemory is not None:
            if (time.time() - _krxMemoryTs) < CACHE_TTL:
                return _krxMemory

        if not forceRefresh:
            cached = _loadKrxCache()
            if cached is not None:
                _krxMemory = cached
                _krxMemoryTs = time.time()
                return cached

        from dartlab.core.guidance import emit

        emit("listing:krx:download")
        df = _fetchKrx()
        if df.height > 0:
            _saveKrxCache(df)
        _krxMemory = df
        _krxMemoryTs = time.time()
        emit("listing:krx:done", count=df.height)
        return df
