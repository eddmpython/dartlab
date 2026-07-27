"""corp_code 관리 — 종목코드/회사명 ↔ 8자리 고유번호 변환.

OpenDART API는 모든 조회에 8자리 corp_code가 필요.
corpCode.xml (ZIP)을 한 번 다운받아 로컬 캐시하고 즉시 조회.
"""

from __future__ import annotations

import io
import threading
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path

import polars as pl

from dartlab.core.dartClient import DartClient
from dartlab.core.market import isKrStockCode, normalizeKrCode

# 캐시 경로: ~/.dartlab/corpCode.parquet
_CACHE_DIR = Path.home() / ".dartlab"
_CACHE_FILE = _CACHE_DIR / "corpCode.parquet"
_CACHE_MAX_AGE_HOURS = 24
_memCache: pl.DataFrame | None = None
_memCacheLock = threading.Lock()


def _isCacheFresh() -> bool:
    """캐시가 24시간 이내인지 확인."""
    if not _CACHE_FILE.exists():
        return False
    mtime = datetime.fromtimestamp(_CACHE_FILE.stat().st_mtime)
    ageHours = (datetime.now() - mtime).total_seconds() / 3600
    return ageHours < _CACHE_MAX_AGE_HOURS


def _downloadCorpCodes(client: DartClient) -> pl.DataFrame:
    """OpenDART에서 corpCode.xml ZIP 다운로드 → DataFrame."""
    raw = client.getBytes("corpCode.xml")

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        xmlData = zf.read("CORPCODE.xml")
    except (zipfile.BadZipFile, KeyError) as e:
        raise ValueError(f"corpCode.xml 다운로드 실패 (ZIP 손상): {e}") from e

    try:
        tree = ET.XML(xmlData)
    except ET.ParseError as e:
        raise ValueError(f"corpCode.xml 파싱 실패 (XML 손상): {e}") from e

    records = []
    for item in tree.findall("list"):
        record = {child.tag: (child.text or "") for child in item}
        records.append(record)

    if not records:
        return pl.DataFrame()

    return pl.DataFrame(records)


def loadCorpCodes(client: DartClient, refresh: bool = False) -> pl.DataFrame:
    """corp_code 전체 목록 로드 (인메모리 → 디스크 → API 순).

    Parameters
    ----------
    client : DartClient
        인증된 클라이언트.
    refresh : bool
        True면 캐시 무시하고 새로 다운로드.

    Returns
    -------
    pl.DataFrame
        columns: corp_code, corp_name, stock_code, modify_date

    Raises:
        없음.

    Example:
        >>> loadCorpCodes(...)

    Args:
        client: DartClient 인스턴스.
        refresh: True 면 캐시 무시 후 새로 다운로드.

    Returns:
        pl.DataFrame — corp_code 전체 목록.

    SeeAlso:
        - ``findCorpCode`` / ``searchCompanies`` — 본 모듈 다른 함수.
        - ``DartClient`` — 다운로드 backend.

    Requires:
        - dartlab
        - datetime
        - io
        - polars
        - threading

    Capabilities:
        - 8 자리 corp_code 와 종목코드/회사명 변환. 24 h 캐시.

    Guide:
        - "회사명 → corp_code" → ``findCorpCode``.

    AIContext:
        internal lookup — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 24 h 캐시 — 신규 회사 누락 시 refresh=True.
            - 동명이인 best match 1 개만.
        OutputSchema:
            - str / pl.DataFrame / None — 함수별.
        Prerequisites:
            - DART_API_KEY (다운로드 시).
        Freshness:
            - corp_code parquet 24 h 캐시.
        Dataflow:
            - DART API corpCode.xml → parquet → 본 함수.
        TargetMarkets:
            - KR (DART) corp_code.
    """
    global _memCache

    if not refresh and _memCache is not None:
        return _memCache

    with _memCacheLock:
        if not refresh and _memCache is not None:
            return _memCache

        if not refresh and _isCacheFresh():
            _memCache = pl.read_parquet(_CACHE_FILE)
            return _memCache

        df = _downloadCorpCodes(client)

        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.write_parquet(_CACHE_FILE)
        _memCache = df
    return df


def findCorpCode(
    client: DartClient,
    query: str,
    refresh: bool = False,
) -> str | None:
    """종목코드(6자리) 또는 회사명으로 corp_code(8자리) 조회.

    Parameters
    ----------
    query : str
        종목코드 (예: "005930") 또는 회사명 (예: "삼성전자").

    Returns
    -------
    str | None
        8자리 corp_code. 못 찾으면 None.

    Raises:
        없음.

    Args:
        client: DartClient 인스턴스.
        query: 회사명 또는 종목코드.
        refresh: True 면 캐시 무시 후 새로 다운로드.

    Returns:
        str — 8 자리 corp_code 또는 None.

    SeeAlso:
        - ``findCorpCode`` / ``searchCompanies`` — 본 모듈 다른 함수.
        - ``DartClient`` — 다운로드 backend.

    Requires:
        - dartlab
        - datetime
        - io
        - polars
        - threading

    Capabilities:
        - 8 자리 corp_code 와 종목코드/회사명 변환. 24 h 캐시.

    Guide:
        - "회사명 → corp_code" → ``findCorpCode``.

    AIContext:
        internal lookup — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 24 h 캐시 — 신규 회사 누락 시 refresh=True.
            - 동명이인 best match 1 개만.
        OutputSchema:
            - str / pl.DataFrame / None — 함수별.
        Prerequisites:
            - DART_API_KEY (다운로드 시).
        Freshness:
            - corp_code parquet 24 h 캐시.
        Dataflow:
            - DART API corpCode.xml → parquet → 본 함수.
        TargetMarkets:
            - KR (DART) corp_code.
    """
    df = loadCorpCodes(client, refresh=refresh)

    # 종목코드로 검색 (KRX 단축코드. 6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0)
    if isKrStockCode(query):
        match = df.filter(pl.col("stock_code") == normalizeKrCode(query))
        if match.height > 0:
            return match["corp_code"][0]
        return None

    # 회사명 정확 매치
    match = df.filter(pl.col("corp_name") == query)
    if match.height > 0:
        return match["corp_code"][0]

    # 회사명 부분 매치 (literal=True로 정규식 인젝션 방지)
    match = df.filter(pl.col("corp_name").str.contains(query, literal=True))
    if match.height == 1:
        return match["corp_code"][0]
    if match.height > 1:
        listed = match.filter(pl.col("stock_code").str.strip_chars() != "")
        if listed.height == 1:
            return listed["corp_code"][0]
        if listed.height > 1:
            names = listed["corp_name"].head(5).to_list()
            raise ValueError(
                f"'{query}' 검색 결과가 {listed.height}개입니다. 더 정확한 이름 또는 종목코드를 사용하세요: {names}"
            )
        return match["corp_code"][0]

    return None


def searchCompanies(
    client: DartClient,
    query: str,
    listedOnly: bool = False,
    *,
    limit: int | None = None,
) -> pl.DataFrame:
    """회사명 부분 매치 검색.

    Args:
        client: DartClient.
        query: 검색어 (회사명 부분 매치).
        listedOnly: True면 상장사만 (stock_code 비빈).
        limit: 최대 행 수. None 이면 무제한.

    Returns:
        매칭된 회사 목록 DataFrame.

    Example:
        >>> searchCompanies(client, "삼성", listedOnly=True, limit=20)

    Raises:
        없음.

    SeeAlso:
        - ``findCorpCode`` / ``searchCompanies`` — 본 모듈 다른 함수.
        - ``DartClient`` — 다운로드 backend.

    Requires:
        - dartlab
        - datetime
        - io
        - polars
        - threading

    Capabilities:
        - 8 자리 corp_code 와 종목코드/회사명 변환. 24 h 캐시.

    Guide:
        - "회사명 → corp_code" → ``findCorpCode``.

    AIContext:
        internal lookup — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 24 h 캐시 — 신규 회사 누락 시 refresh=True.
            - 동명이인 best match 1 개만.
        OutputSchema:
            - str / pl.DataFrame / None — 함수별.
        Prerequisites:
            - DART_API_KEY (다운로드 시).
        Freshness:
            - corp_code parquet 24 h 캐시.
        Dataflow:
            - DART API corpCode.xml → parquet → 본 함수.
        TargetMarkets:
            - KR (DART) corp_code.
    """
    df = loadCorpCodes(client)
    result = df.filter(pl.col("corp_name").str.contains(query, literal=True))

    if listedOnly:
        result = result.filter(pl.col("stock_code").str.strip_chars() != "")

    if limit is not None:
        result = result.head(limit)
    return result


def iterCompanies(
    client: DartClient,
    query: str,
    listedOnly: bool = False,
    *,
    limit: int | None = None,
):
    """``searchCompanies`` 의 iterator pair (룰 10).

    Args:
        client: DartClient.
        query: 검색어.
        listedOnly: True 면 상장사만.
        limit: 최대 행 수. None 이면 무제한.

    Yields:
        row dict.

    Raises:
        없음.

    Example:
        >>> for row in iterCompanies(client, "삼성", limit=10):
        ...     print(row["corp_name"])

    SeeAlso:
        - ``findCorpCode`` / ``searchCompanies`` — 본 모듈 다른 함수.
        - ``DartClient`` — 다운로드 backend.

    Requires:
        - dartlab
        - datetime
        - io
        - polars
        - threading

    Capabilities:
        - 8 자리 corp_code 와 종목코드/회사명 변환. 24 h 캐시.

    Guide:
        - "회사명 → corp_code" → ``findCorpCode``.

    AIContext:
        internal lookup — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 24 h 캐시 — 신규 회사 누락 시 refresh=True.
            - 동명이인 best match 1 개만.
        OutputSchema:
            - str / pl.DataFrame / None — 함수별.
        Prerequisites:
            - DART_API_KEY (다운로드 시).
        Freshness:
            - corp_code parquet 24 h 캐시.
        Dataflow:
            - DART API corpCode.xml → parquet → 본 함수.
        TargetMarkets:
            - KR (DART) corp_code.
    """
    df = searchCompanies(client, query, listedOnly, limit=limit)
    yield from df.iter_rows(named=True)
