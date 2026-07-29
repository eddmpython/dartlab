"""KRX KIND 상장법인 등록부 — 종목코드 ↔ 회사명 lookup + 24h TTL 캐시 SSOT.

KIND (KOSPI/KOSDAQ 상장법인) fetch + 메모리/파일 캐시 + 단일 종목 lookup
(codeToName, nameToCode) 핵심부. KRX (data.krx) · DART (CORPCODE) 별 목록은
자매 모듈 ``krxList.py`` · ``dartList.py``. 자모 분해·fuzzy 검색은
``fuzzy.py``. DIP 등록은 ``resolver.py``.
"""

from __future__ import annotations

import threading
import time
from html.parser import HTMLParser
from pathlib import Path

import httpx
import polars as pl

from dartlab.core.logger import getLogger
from dartlab.gather.infra.ttl import TTL_LISTING as CACHE_TTL

_log = getLogger(__name__)


def _cacheFile() -> Path:
    """KIND 상장법인 캐시 파일 경로 반환.

    Returns
    -------
    Path
        ``{dataRoot}/kindList/corpList.parquet`` 경로.
    """
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "kindList" / "corpList.parquet"


KIND_URL = "https://kind.krx.co.kr/corpgeneral/corpList.do"
KIND_DATA = {
    "method": "download",
    "searchType": "13",
    "fiscalYearEnd": "all",
    "location": "all",
}
# KRX KIND 는 기본 클라이언트 UA 에 드물게 비-테이블 오류 페이지를 반환한다(WAF/혼잡). 브라우저 UA +
# 짧은 재시도로 일시 응답을 흡수 — 이 한 곳이 KIND 수집 SSOT 라 런타임(Company/Search/Scan)·CI 파이프라인이
# 모두 같은 견고성을 공유한다(별도빌드가 각자 재구현하지 않는다).
_KIND_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
_KIND_RETRIES = 3
_KIND_BACKOFF_SEC = 2.0

_memory: pl.DataFrame | None = None
_memoryTs: float = 0.0
_memoryLock = threading.Lock()


class _TableParser(HTMLParser):
    """KRX KIND HTML 테이블 → 2차원 리스트 변환.

    KIND에서 반환하는 EUC-KR 인코딩 HTML 테이블을 파싱하여
    ``list[list[str]]`` (행 × 열) 형태로 변환한다.

    Attributes
    ----------
    _rows : list[list[str]]
        파싱 완료된 전체 행 목록.
    """

    def __init__(self):
        super().__init__()
        self._inTable = False
        self._inTr = False
        self._inCell = False
        self._rows: list[list[str]] = []
        self._row: list[str] = []
        self._cell = ""

    def handle_starttag(self, tag: str, _attrs):
        """HTML 여는 태그 처리 (stdlib HTMLParser hook).

        Capabilities: table/tr/td/th 진입 추적.
        AIContext: KIND HTML 응답을 polars DataFrame 으로 변환하는 첫 단계.
        Guide: stdlib HTMLParser 가 자동 콜백, 직접 호출 금지.
        When: parser.feed(html) 가 여는 태그 발견 시.
        How: 태그명 분기 + 내부 _inTable/_inTr/_inCell 플래그 갱신.

        Args:
            tag: 태그 이름 (소문자).
            _attrs: 태그 속성 리스트 — 본 파서에서 사용 안 함.

        Returns:
            None — 내부 상태만 갱신.

        Raises:
            없음.

        Example:
            stdlib HTMLParser 의 콜백 — 사용자는 ``parser.feed(html)`` 만 호출.

        Requires:
            ``html.parser.HTMLParser`` 부모 클래스 상속. ``_inTable/_inTr/_inCell``
            플래그 초기화 (``__init__``) 선행.

        See Also:
            handle_endtag : 짝 콜백 (cell/row commit).
            handle_data : 텍스트 노드 콜백.
            _TableParser.__init__ : 플래그 초기화.
        """
        if tag == "table":
            self._inTable = True
        elif tag == "tr" and self._inTable:
            self._inTr = True
            self._row = []
        elif tag in ("td", "th") and self._inTr:
            self._inCell = True
            self._cell = ""

    def handle_endtag(self, tag: str):
        """HTML 닫는 태그 처리 (stdlib HTMLParser hook).

        Capabilities: cell 누적 텍스트 commit + row 누적.
        AIContext: KIND HTML 응답 변환의 row commit 단계.
        Guide: stdlib HTMLParser 자동 콜백, 직접 호출 금지.
        When: parser.feed(html) 가 닫는 태그 발견 시.
        How: 태그명 분기 + _cell strip → _row append.

        Args:
            tag: 태그 이름 (소문자).

        Returns:
            None — 내부 상태만 갱신.

        Raises:
            없음.

        Example:
            stdlib HTMLParser 의 콜백 — 사용자는 ``parser.feed(html)`` 만 호출.

        Requires:
            handle_starttag 가 _inTable/_inTr/_inCell/_cell 을 사전 갱신해 둠.

        See Also:
            handle_starttag : 짝 콜백 (cell/row 진입).
            handle_data : 본 콜백 사이에 텍스트 누적.
        """
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
        """HTML 텍스트 데이터 처리 (stdlib HTMLParser hook).

        Capabilities: cell 내 텍스트 누적 (다중 텍스트 노드 대응).
        AIContext: KIND 응답의 EUC-KR 텍스트 cell 본문 수집.
        Guide: stdlib HTMLParser 자동 콜백, 직접 호출 금지.
        When: parser.feed(html) 가 텍스트 노드 발견 시 + _inCell True.
        How: _cell 문자열 concat — handle_endtag 가 strip + commit.

        Args:
            data: 태그 사이의 텍스트.

        Returns:
            None — 내부 cell 버퍼에 누적.

        Raises:
            없음.

        Example:
            stdlib HTMLParser 의 콜백 — 사용자는 ``parser.feed(html)`` 만 호출.

        Requires:
            handle_starttag 가 ``_inCell = True`` 와 ``_cell = ""`` 사전 셋팅.

        See Also:
            handle_starttag · handle_endtag : 셀 진입/종료 콜백.
        """
        if self._inCell:
            self._cell += data


def _fetchKind() -> pl.DataFrame:
    """KRX KIND API에서 상장법인 목록 HTML 수집 → DataFrame 변환.

    SPAC·리츠 제외, 6자리 종목코드만 포함. 전송 계층 일시 장애(연결 끊김·타임아웃·비-테이블
    응답)는 짧게 재시도하고, 소진 시 빈 DataFrame 반환(소비자 비크래시 계약).

    Returns
    -------
    pl.DataFrame
        종목코드 : str — 6자리 종목코드
        회사명 : str — 법인명
        업종 : str — 업종명
        주요제품 : str — 주요 제품
        상장일 : str — 상장일
        결산월 : str — 결산월
        대표자명 : str — 대표자명
    """
    empty = pl.DataFrame(schema={"종목코드": pl.Utf8, "회사명": pl.Utf8})
    rows: list[list[str]] = []
    for attempt in range(_KIND_RETRIES):
        try:
            r = httpx.post(KIND_URL, data=KIND_DATA, headers=_KIND_HEADERS, timeout=30)
            html = r.content.decode("euc-kr", errors="replace")
            parser = _TableParser()
            parser.feed(html)
            if len(parser._rows) >= 2:
                rows = parser._rows
                break
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as exc:
            # 전송 계층 일시 장애. 재시도하되 원인은 남긴다. 예전에는 삼켜서 재시도가
            # 소진된 뒤에도 무엇 때문에 비었는지 알 수 없었다.
            _log.warning("KIND 상장목록 조회 실패 (%d/%d): %s: %s", attempt + 1, _KIND_RETRIES, type(exc).__name__, exc)
        if attempt < _KIND_RETRIES - 1:
            time.sleep(_KIND_BACKOFF_SEC * (attempt + 1))
    if len(rows) < 2:
        return empty  # 재시도 소진 — graceful 빈 DataFrame(소비자 비크래시 계약 유지)

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
    """KIND 파일 캐시 로드. TTL(24h) 초과 또는 Pyodide면 None.

    Returns
    -------
    pl.DataFrame | None
        캐시된 상장법인 DataFrame. 없거나 만료 시 None.
    """
    import sys

    if sys.platform == "emscripten":
        return None  # Pyodide: 로컬 캐시 없음
    path = _cacheFile()
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL:
        return None
    return pl.read_parquet(str(path))


def _saveCache(df: pl.DataFrame) -> None:
    """KIND 상장법인 DataFrame을 Parquet 파일로 캐시 저장.

    Pyodide 환경에서는 저장하지 않는다 (영속 FS 없음).

    Parameters
    ----------
    df : pl.DataFrame
        저장할 상장법인 DataFrame.
    """
    import sys

    if sys.platform == "emscripten":
        return  # Pyodide: write_parquet 비활성 + 영속 FS 없음
    path = _cacheFile()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(str(path))


def getKindList(*, forceRefresh: bool = False) -> pl.DataFrame:
    """KRX KIND 상장법인 전체 목록.

    Capabilities: 메모리 → 파일(24h TTL) → KIND API 3-tier 캐시 + SPAC/리츠 제외.
    AIContext: 종목코드 ↔ 회사명 매핑의 SSOT — Company/Search/Scan 진입점.
    Guide: forceRefresh=True 시 KIND HTTP 강제 호출 (TTL 무시).
    When: 종목코드 ↔ 회사명 lookup, 새 종목 등장 점검 시.
    How: 메모리 cache check → file cache check → _fetchKind() → 저장.

    캐시 우선순위: 메모리 → 파일(24h TTL) → KIND API.
    SPAC·리츠 제외, 6자리 종목코드만 포함.

    Parameters
    ----------
    forceRefresh : bool
        True면 캐시 무시하고 KIND API 재요청. 기본 False.

    Returns
    -------
    pl.DataFrame
        종목코드 : str — 6자리 종목코드
        회사명 : str — 법인명
        업종 : str — 업종명
        주요제품 : str — 주요 제품
        상장일 : str — 상장일
        결산월 : str — 결산월
        대표자명 : str — 대표자명

    Raises
    ------
    없음
        KIND fetch 실패 시 빈 DataFrame 반환 (예외 흡수).

    Example
    -------
    >>> df = getKindList()

    Requires
    --------
    네트워크 (``kind.krx.co.kr/corpgeneral/corpList.do``) + 파일 쓰기 (``{dataRoot}/
    kindList/corpList.parquet``). Pyodide 환경에서는 KRX API(CORS) 대신 HF
    ``metadata/corpList.parquet`` (gov 발행) 을 직독한다.

    See Also
    --------
    codeToName · nameToCode : 본 목록의 단일 lookup 진입점.
    fuzzy.searchName : substring/fuzzy 검색.
    dartList.getDartList : DART CORPCODE 보강 source.
    """
    global _memory, _memoryTs

    import sys

    if sys.platform == "emscripten":
        # Pyodide: KRX API(kind.krx.co.kr)는 CORS 차단. 같은 목록이 gov 축으로 HF 에 발행돼 있으므로
        # metadata/corpList.parquet 를 직독한다(회사명↔종목코드 해석이 브라우저 노트북에서도 동작).
        if _memory is None:
            try:
                from dartlab.core.dataLoaderPyodide import loadCorpListPyodide

                _memory = loadCorpListPyodide()
            except MemoryError:
                raise
            except Exception as exc:
                _log.warning(
                    "Pyodide 상장목록 조회 실패(다음 호출 재시도): %s: %s",
                    type(exc).__name__,
                    exc,
                )
                return pl.DataFrame({"회사명": [], "종목코드": []})
        return _memory

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
                _invalidateSearchCache()
                return cached

        from dartlab.core.messaging import emit

        emit("listing:download")
        df = _fetchKind()
        # 빈 결과는 캐시하지 않는다. KIND 가 잠깐 끊겨 나온 빈 목록을 24 시간짜리 파일
        # 캐시에 굳히면 네트워크가 돌아와도 라이브러리가 하루 종일 회복하지 못한다.
        # 그동안 KR 종목코드와 회사명 해석이 통째로 죽고, 사용자에게는 0 개 로드 완료라는
        # 성공 문구가 나간다.
        if df.height > 0:
            _saveCache(df)
        else:
            _log.warning("상장목록이 비어 캐시에 저장하지 않는다. 다음 호출에서 다시 조회한다.")
        _memory = df
        _memoryTs = time.time()
        _invalidateSearchCache()
        emit("listing:done", count=df.height)
        return df


def _invalidateSearchCache() -> None:
    """getKindList 갱신 시 fuzzy module 의 검색 캐시 무효화."""
    try:
        from . import fuzzy

        fuzzy._searchCache = None
    except ImportError:
        pass


def codeToName(stockCode: str) -> str | None:
    """종목코드 → 회사명.

    Capabilities: 6자리 종목코드 lookup → 한국 법인명 변환.
    AIContext: Company/Scan/Search 가 사용자 표시용 회사명 얻을 때 진입.
    Guide: getKindList() 캐시 hit 이면 O(1) 근사 — 첫 호출만 KIND fetch.
    When: 분석 결과에 회사명 라벨 필요 시.
    How: getKindList() → 종목코드 == filter → 첫 행 회사명.

    Parameters
    ----------
    stockCode : str
        6자리 종목코드.

    Returns
    -------
    str | None
        회사명. 못 찾으면 None.

    Raises
    ------
    없음
        ``getKindList()`` 가 빈 DataFrame 반환 시 None.

    Example
    -------
    >>> codeToName("005930")
    '삼성전자'

    Requires
    --------
    ``getKindList()`` 캐시 가용 — 첫 호출 시 KIND HTTP fetch.

    See Also
    --------
    nameToCode : 역방향 — 회사명 → 코드.
    resolver.codeToName : Protocol 위임 진입점.
    """
    df = getKindList()
    match = df.filter(pl.col("종목코드") == stockCode)
    if match.height == 0:
        return None
    return match["회사명"][0]


def nameToCode(corpName: str) -> str | None:
    """회사명 → 종목코드. 정확히 일치하는 첫 번째 결과.

    Capabilities: 한국 회사명 → 6자리 종목코드 정확 매칭.
    AIContext: 사용자 자연어 (회사명) 입력 → 코드 정규화 진입.
    Guide: 정확히 일치만 — fuzzy 검색은 fuzzy.searchName 사용.
    When: "삼성전자 분석해" 류 자연어 → 종목코드 추출 필요 시.
    How: getKindList() → 회사명 == filter → 첫 행 종목코드.

    Parameters
    ----------
    corpName : str
        회사명.

    Returns
    -------
    str | None
        6자리 종목코드. 못 찾으면 None.

    Raises
    ------
    없음
        ``getKindList()`` 가 빈 DataFrame 반환 시 None.

    Example
    -------
    >>> nameToCode("삼성전자")
    '005930'

    Requires
    --------
    ``getKindList()`` 캐시 가용 + 사용자 입력이 KIND 목록과 *정확* 일치.

    See Also
    --------
    codeToName : 역방향 — 코드 → 회사명.
    fuzzy.searchName : 부분 일치 + 자모 분해 검색.
    resolver.nameToCode : Protocol 위임 진입점.
    """
    df = getKindList()
    match = df.filter(pl.col("회사명") == corpName)
    if match.height == 0:
        return None
    return match["종목코드"][0]
