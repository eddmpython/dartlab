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

from dartlab.providers.dart.openapi.client import DartClient

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
    """
    df = loadCorpCodes(client, refresh=refresh)

    # 종목코드로 검색 (6자리 숫자)
    if query.isdigit() and len(query) == 6:
        match = df.filter(pl.col("stock_code") == query)
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
) -> pl.DataFrame:
    """회사명 부분 매치 검색.

    Parameters
    ----------
    query : str
        검색어 (회사명 부분 매치).
    listedOnly : bool
        True면 상장사만 (stock_code가 빈 문자열이 아닌 것).

    Returns
    -------
    pl.DataFrame
        매칭된 회사 목록.
    """
    df = loadCorpCodes(client)
    result = df.filter(pl.col("corp_name").str.contains(query, literal=True))

    if listedOnly:
        result = result.filter(pl.col("stock_code").str.strip_chars() != "")

    return result
