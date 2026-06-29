"""freshness-gated 로컬 수집 저장 SSOT — 느린 크롤 결과를 collectedAt 박아 로컬 parquet 으로.

``dataLoader`` (HF 다운로드 freshness) 의 자매 — 이쪽은 *로컬 수집* 데이터(네이버 그룹 크롤
등)를 ``config.dataDir`` 아래에 저장하고 ``collectedAt`` 컬럼 기준 ``maxAgeDays`` 신선도로
직독/재수집을 가른다.

설계
    - 일자 박기 : 파일명/​mtime 이 아니라 데이터 안 ``collectedAt`` (ISO8601) 컬럼 — 자기기술적
      (xlsx 등으로 내보내도 날짜가 따라감), 단일 정본 파일 1개 덮어쓰기.
    - 신선도   : ``max(collectedAt)`` 가 ``maxAgeDays`` 내면 로컬 직독, 아니면 재수집+저장.
    - 런타임-SSOT 경계 : 로컬 전용·gitignore·HF 미적재. stale 이면 원천 재수집이라 '굽기'가
      아니라 '신선도 미러'. 빈 결과(수집 실패)는 저장하지 않아 다음 호출이 재시도한다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl

__all__ = ["loadOrCollect", "loadOrCollectAsync"]

_COLLECTED_AT = "collectedAt"


def _storePath(category: str) -> Path:
    """``config.dataDir / <category> / data.parquet`` — 카테고리별 정본 파일 경로."""
    from dartlab import config

    return Path(config.dataDir) / category / "data.parquet"


def _asUtc(value: datetime) -> datetime:
    """tz-naive datetime 은 UTC 로 간주."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _isFresh(df: pl.DataFrame, maxAgeDays: float) -> bool:
    """``max(collectedAt)`` 가 maxAgeDays 내면 True. 빈 df/컬럼 없음/파싱 실패 시 False."""
    if df.is_empty() or _COLLECTED_AT not in df.columns:
        return False
    latest = df[_COLLECTED_AT].max()
    if not latest:
        return False
    try:
        collected = _asUtc(datetime.fromisoformat(str(latest)))
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - collected) <= timedelta(days=maxAgeDays)


def _save(path: Path, df: pl.DataFrame) -> pl.DataFrame:
    """df 에 collectedAt(ISO) 박아 parquet 저장 후 반환. 빈 df 는 저장 안 함(다음 재시도)."""
    if df.is_empty():
        return df
    stamped = df.with_columns(pl.lit(datetime.now(timezone.utc).isoformat()).alias(_COLLECTED_AT))
    path.parent.mkdir(parents=True, exist_ok=True)
    stamped.write_parquet(path)
    return stamped


def _loadFresh(category: str, maxAgeDays: float, refresh: bool) -> pl.DataFrame | None:
    """로컬 파일이 있고 신선하면 반환, 아니면 None (재수집 필요)."""
    if refresh:
        return None
    path = _storePath(category)
    if not path.exists():
        return None
    try:
        cached = pl.read_parquet(path)
    except (OSError, pl.exceptions.PolarsError):
        return None
    return cached if _isFresh(cached, maxAgeDays) else None


def loadOrCollect(
    category: str,
    collectFn: Callable[[], pl.DataFrame],
    *,
    maxAgeDays: float = 7.0,
    refresh: bool = False,
) -> pl.DataFrame:
    """freshness-gated 로컬 저장 — 신선하면 직독, 아니면 collectFn 재수집+저장 (동기).

    Sig: ``loadOrCollect(category, collectFn, *, maxAgeDays=7.0, refresh=False) -> pl.DataFrame``

    Capabilities: collectedAt 컬럼 기준 maxAgeDays 신선도 판정 → 로컬 parquet 직독 또는 재수집.
    Args:
        category: 저장 카테고리 경로 (예: "naverGroups/theme"). config.dataDir 하위.
        collectFn: 재수집 함수 — DataFrame 반환 (느린 크롤 등).
        maxAgeDays: 신선도 윈도우(일). 기본 7. 이내면 재수집 안 함.
        refresh: True 면 신선도 무시하고 항상 재수집.
    Returns:
        pl.DataFrame — collectedAt 컬럼 포함. 직독이면 저장된 것, 재수집이면 갓 저장한 것.
    Raises:
        없음 — 손상/없는 파일은 재수집으로 흡수.
    Example::

        df = loadOrCollect("naverGroups/theme", crawlAllThemes, maxAgeDays=7)
    """
    cached = _loadFresh(category, maxAgeDays, refresh)
    if cached is not None:
        return cached
    return _save(_storePath(category), collectFn())


async def loadOrCollectAsync(
    category: str,
    collectFn: Callable[[], Awaitable[pl.DataFrame]],
    *,
    maxAgeDays: float = 7.0,
    refresh: bool = False,
) -> pl.DataFrame:
    """``loadOrCollect`` 의 async 변형 — collectFn 이 coroutine (비동기 크롤용).

    Sig: ``await loadOrCollectAsync(category, asyncCollectFn, *, maxAgeDays=7.0, refresh=False)``

    Capabilities: 신선하면 로컬 직독(수집 skip), 아니면 ``await collectFn()`` 재수집+저장.
    Args:
        category: 저장 카테고리 경로 (config.dataDir 하위).
        collectFn: 재수집 coroutine 함수 — DataFrame 반환.
        maxAgeDays: 신선도 윈도우(일). 기본 7.
        refresh: True 면 항상 재수집.
    Returns:
        pl.DataFrame — collectedAt 컬럼 포함.
    Raises:
        없음.
    Example::

        df = await loadOrCollectAsync("naverGroups/theme", lambda: crawlAll(client), maxAgeDays=7)
    """
    cached = _loadFresh(category, maxAgeDays, refresh)
    if cached is not None:
        return cached
    return _save(_storePath(category), await collectFn())
