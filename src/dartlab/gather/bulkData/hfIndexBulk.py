"""KR 지수 HF 데이터셋 부분 액세스.

Summary
-------
``gather("krxIndex", ...)`` 의 사용자 기본 경로. KRX API 키를 읽지 않고
HuggingFace 데이터셋의 ``gov/indices/date/{YYYY}.parquet`` 만 사용한다 (공공데이터포털
gov 축 publish, KRX 지수 schema 동질).

Description
-----------
저장 SSOT 는 ``DATA_RELEASES["govIndices"]`` 이다. 연도별 date parquet 을
``core.dataLoader.loadData`` 로 읽으므로 로컬 캐시, HF 다운로드, ETag/size
freshness 검증은 dartlab 공통 데이터 로더 정책을 그대로 따른다.

Data Contract
-------------
파일 단위:
    ``raw-{YYYY}.parquet`` — 해당 연도 KRX/KOSPI/KOSDAQ 시장군 전체 지수.
중복 키:
    ``BAS_DD`` + ``MARKET_GROUP`` + ``IDX_CLSS`` + ``IDX_NM``.
반환 스키마:
    KRX idx 원본 컬럼 + ``MARKET_GROUP``.

Guide
-----
일반 사용자는 이 모듈을 직접 부르지 않고
``dartlab.gather("krxIndex", "close", market="KOSPI")`` 를 호출한다. quant나
macro 쪽 내부 엔진이 raw long 지수 데이터를 직접 소비해야 할 때만
``loadFiltered`` 를 사용한다.

See Also
--------
``dartlab.gather.krxIndex`` — 공개 gather 축.
``.github/scripts/sync/buildKrxIndexData.py`` — 운영자 수집/배포.
``engines.gather`` — gather KRX 지수 계약.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime
from typing import Literal

import polars as pl

from dartlab.gather.bulkData.dateKey import parseDateKey

log = logging.getLogger(__name__)

_CATEGORY = "govIndices"  # DATA_RELEASES["govIndices"] SSOT — gov/indices/date 샤딩
_COL_DATE = "BAS_DD"
_COL_MARKET = "MARKET_GROUP"


def _resolveYears(
    year: int | None,
    start: str | _date | None,
    end: str | _date | None,
) -> list[int]:
    """필요한 연도 리스트 결정."""
    if year is not None:
        return [int(year)]
    if start is None and end is None:
        return list(range(2010, datetime.now().year + 1))
    s = parseDateKey(start) if start else _date(2010, 1, 1)
    e = parseDateKey(end) if end else _date.today()
    if s > e:
        s, e = e, s
    return list(range(s.year, e.year + 1))


def _loadYear(year: int) -> pl.DataFrame | None:
    """``krx/indices/raw-{year}.parquet`` 를 로컬/HF에서 로드한다.

    Parameters
    ----------
    year : int
        조회 연도.

    Returns
    -------
    pl.DataFrame | None
        해당 연도 raw long DataFrame. HF 에 아직 없는 연도면 None.

    Notes
    -----
    여기서 직접 URL을 만들지 않는다. ``DATA_RELEASES["krxIndices"]`` 와
    ``loadData`` 가 경로와 freshness 를 관리하는 단일 진입점이다.
    """
    from dartlab.core.dataLoader import loadData

    name = f"{year}"  # date 는 dir(gov/indices/date)에 포함 → 파일명 = {year}.parquet
    try:
        return loadData(name, category=_CATEGORY)
    except Exception as exc:
        log.debug(
            "govIndices/%s.parquet 미가용 (HF 미빌드 또는 해당 연도 미수집): %s",
            name,
            type(exc).__name__,
        )
        return None


def loadFiltered(
    *,
    market: Literal["KRX", "KOSPI", "KOSDAQ"] | None = None,
    year: int | None = None,
    start: str | _date | None = None,
    end: str | _date | None = None,
) -> pl.DataFrame:
    """HF ``krx/indices`` 에서 KRX 지수 raw long 데이터를 로드한다.

    Capabilities: 연도별 raw-{year}.parquet 다운로드 + 시장군/기간 필터 + concat.
    AIContext: gatherKrxIndex (사용자 진입) 의 기본 backend — apiKey 없는 사용자 path.
    Requires: 인터넷 + ``huggingface-hub`` + HF dataset ``krx/indices`` publish 된 연도.

    Summary
    -------
    연도/기간/시장군 조건으로 KRX 지수 raw parquet 을 부분 로드한다.

    Description
    -----------
    사용자가 API 키 없이 ``gather("krxIndex", ...)`` 를 호출할 때 실행되는
    기본 데이터 경로다. 파일은 연도별로 나뉘어 있어 필요한 연도만 로드하고,
    각 연도 파일 내부에서 ``BAS_DD`` 와 ``MARKET_GROUP`` 필터를 적용한다.

    Parameters
    ----------
    market : {"KRX", "KOSPI", "KOSDAQ"} | None
        지수 시장군. None 이면 세 시장군 전체.
    year : int | None
        단일 연도. ``start``/``end`` 와 동시 사용 불가.
    start : str | date | None
        시작일 (YYYY-MM-DD, YYYYMMDD, date). None 이면 2010-01-01.
    end : str | date | None
        종료일. None 이면 오늘.

    Returns
    -------
    pl.DataFrame
        ``BAS_DD`` : str — 기준일 (YYYYMMDD)
        ``MARKET_GROUP`` : str — 시장군 (KRX/KOSPI/KOSDAQ)
        ``IDX_CLSS`` : str — 지수 분류
        ``IDX_NM`` : str — 지수명
        ``CLSPRC_IDX`` : float — 종가지수 (포인트)
        ``OPNPRC_IDX`` : float — 시가지수 (포인트)
        ``HGPRC_IDX`` : float — 고가지수 (포인트)
        ``LWPRC_IDX`` : float — 저가지수 (포인트)
        ``ACC_TRDVOL`` : int — 누적 거래량 (주)
        ``ACC_TRDVAL`` : int — 누적 거래대금 (원)
        ``MKTCAP`` : int — 시가총액 (원)

    Raises
    ------
    ValueError
        ``year`` 와 ``start``/``end`` 를 동시에 지정하거나 market 값이 잘못된 경우.

    Examples
    --------
    >>> from dartlab.gather.bulkData.hfIndexBulk import loadFiltered
    >>> loadFiltered(market="KOSPI", start="2026-04-28", end="2026-04-28")
    >>> loadFiltered(year=2025)

    Notes
    -----
    데이터셋 미빌드 연도는 조용히 skip 한다. 호출자가 빈 DataFrame 을 받으면
    아직 HF에 해당 연도 파일이 없거나 조건에 맞는 지수 row가 없는 상태다.

    Guide
    -----
    When: 엔진 내부에서 지수 raw long 데이터가 필요할 때.
    How: 사용자-facing wide pivot 은 ``gatherKrxIndex`` 가 담당한다.
    Verified:
        - 2010~2026 연도별 parquet 로드 및 KOSPI 2026-04-28 smoke 확인.

    See Also
    --------
    dartlab.gather.krxIndex.gatherKrxIndex : 공개 호출.
    scripts.build.buildKrxIndexData : parquet 생성 경로.
    """
    if year is not None and (start is not None or end is not None):
        raise ValueError("year 와 start/end 는 동시 사용 불가")
    if market is not None and market not in {"KRX", "KOSPI", "KOSDAQ"}:
        raise ValueError(f"market 은 'KRX' / 'KOSPI' / 'KOSDAQ' 만 허용: {market!r}")

    frames: list[pl.DataFrame] = []
    for y in _resolveYears(year, start, end):
        df = _loadYear(y)
        if df is None or df.is_empty():
            continue
        if market is not None and _COL_MARKET in df.columns:
            df = df.filter(pl.col(_COL_MARKET) == market)
        if start is not None:
            df = df.filter(pl.col(_COL_DATE) >= parseDateKey(start).strftime("%Y%m%d"))
        if end is not None:
            df = df.filter(pl.col(_COL_DATE) <= parseDateKey(end).strftime("%Y%m%d"))
        if not df.is_empty():
            frames.append(df)

    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="diagonal_relaxed").sort([_COL_DATE, _COL_MARKET, "IDX_CLSS", "IDX_NM"])
