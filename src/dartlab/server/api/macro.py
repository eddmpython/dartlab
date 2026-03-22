"""FRED 매크로 경제지표 API 엔드포인트."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


def _get_fred():
    """Fred 인스턴스 생성 — API 키 없으면 503."""
    from dartlab.engines.gather.fred import Fred
    from dartlab.engines.gather.fred.types import AuthenticationError

    try:
        return Fred()
    except AuthenticationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def _to_records(df):
    """Polars DataFrame → list[dict] (JSON serializable)."""
    if df.is_empty():
        return []
    return df.to_dicts()


# ── 시계열 ──


@router.get("/api/fred/series/{series_id}")
async def api_fred_series(
    series_id: str,
    start: str | None = Query(None),
    end: str | None = Query(None),
    frequency: str | None = Query(None),
    transform: str = Query("raw"),
    window: int = Query(12),
):
    """FRED 시계열 조회 + 변환."""
    from dartlab.engines.gather.fred.types import FredError

    f = _get_fred()
    try:
        if transform == "yoy":
            df = await asyncio.to_thread(f.yoy, series_id, start=start, end=end)
        elif transform == "mom":
            df = await asyncio.to_thread(f.mom, series_id, start=start, end=end)
        elif transform == "ma":
            df = await asyncio.to_thread(f.movingAverage, series_id, window=window, start=start, end=end)
        else:
            df = await asyncio.to_thread(f.series, series_id, start=start, end=end, frequency=frequency)
    except FredError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    meta = await asyncio.to_thread(f.meta, series_id)
    return {
        "meta": {
            "id": meta.id,
            "title": meta.title,
            "frequency": meta.frequency,
            "units": meta.units,
        },
        "data": _to_records(df),
    }


# ── 검색 ──


@router.get("/api/fred/search")
async def api_fred_search(
    q: str = Query(...),
    limit: int = Query(20),
):
    """FRED 시리즈 검색."""
    from dartlab.engines.gather.fred.types import FredError

    f = _get_fred()
    try:
        df = await asyncio.to_thread(f.search, q, limit=limit)
    except FredError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"results": _to_records(df)}


# ── 비교 ──


@router.get("/api/fred/compare")
async def api_fred_compare(
    ids: str = Query(..., description="콤마 구분 시리즈 ID"),
    start: str | None = Query(None),
    end: str | None = Query(None),
    normalize_to: str | None = Query(None),
):
    """복수 시계열 비교."""
    from dartlab.engines.gather.fred import transform as _transform
    from dartlab.engines.gather.fred.types import FredError

    series_ids = [s.strip() for s in ids.split(",") if s.strip()]
    if len(series_ids) < 2:
        raise HTTPException(status_code=400, detail="시리즈 ID 2개 이상 필요")

    f = _get_fred()
    try:
        df = await asyncio.to_thread(f.compare, series_ids, start=start, end=end)
    except FredError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if normalize_to:
        df = _transform.normalize_multi(df, base_date=normalize_to)

    return {"data": _to_records(df)}


# ── 카탈로그 ──


@router.get("/api/fred/catalog")
async def api_fred_catalog(
    group: str | None = Query(None),
):
    """주요 경제지표 카탈로그."""
    from dartlab.engines.gather.fred.catalog import get_groups, to_dataframe

    if group and group not in get_groups():
        raise HTTPException(status_code=400, detail=f"그룹 없음. 사용 가능: {', '.join(get_groups())}")

    df = to_dataframe(group)
    return {"catalog": _to_records(df)}


# ── 상관분석 ──


@router.get("/api/fred/correlation")
async def api_fred_correlation(
    ids: str = Query(..., description="콤마 구분 시리즈 ID"),
    start: str | None = Query(None),
    end: str | None = Query(None),
    max_lag: int = Query(12),
    lead_lag: str | None = Query(None, description="선행/후행 분석 쌍 (콤마 구분 2개)"),
):
    """시계열 상관분석 + 선행/후행."""
    from dartlab.engines.gather.fred.types import FredError

    series_ids = [s.strip() for s in ids.split(",") if s.strip()]
    if len(series_ids) < 2:
        raise HTTPException(status_code=400, detail="시리즈 ID 2개 이상 필요")

    f = _get_fred()
    result: dict = {}

    try:
        corr = await asyncio.to_thread(f.correlation, series_ids, start=start, end=end)
        result["correlation"] = _to_records(corr)
    except FredError as exc:
        result["correlation_error"] = str(exc)

    if lead_lag:
        pair = [s.strip() for s in lead_lag.split(",") if s.strip()]
        if len(pair) == 2:
            try:
                ll = await asyncio.to_thread(
                    f.leadLag, pair[0], pair[1], max_lag=max_lag, start=start, end=end,
                )
                result["lead_lag"] = _to_records(ll)
            except FredError as exc:
                result["lead_lag_error"] = str(exc)

    return result
