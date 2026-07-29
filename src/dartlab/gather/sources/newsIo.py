"""뉴스 archive 공유 IO — 일별 parquet write/load 단일 구현.

옛 구조는 upsert 로직이 `syncNewsHeadlines._writeDailyParquet` 와
`syncGdeltBackfill._writeDayParquet` 에 byte 단위 중복, 읽기 로더가
`newsHeadlines._loadDay`(rss)·`_loadGdeltDay`(gdelt) 로 분리돼 있었다. 본 모듈이
소스-무관 단일 구현으로 흡수한다 (레지스트리 `dir` 로 경로 결정).

물리 경로: ``data/{spec.dir}/{MARKET}/{YYYY-MM-DD}.parquet`` (일별 sharding, upsert).
저장 파일은 항상 canonical 17컬럼 (`coerceToCanonical` 적용 후 write).

See Also:
    sources/newsSources.py — dir SSOT.
    sources/newsSchema.py — canonical 스키마.
    bulkData/newsHeadlines.py — loadSourceDay 를 순회 호출하는 read 진입점.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from functools import lru_cache
from pathlib import Path

import polars as pl

from ..types import SourceUnavailableError
from .newsSchema import coerceToCanonical
from .newsSources import getNewsSource

log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DATA_ROOT = _REPO_ROOT / "data"  # 테스트는 이 심볼을 patch + loadSourceDay.cache_clear()


def _dayIso(day: str | _date) -> str:
    """day(str|date) → 'YYYY-MM-DD' 파일명."""
    return day.isoformat() if isinstance(day, _date) else str(day)


def writeDailyParquet(
    df: pl.DataFrame,
    *,
    dir: str,
    market: str,
    day: str | _date,
) -> tuple[Path, int, int]:
    """일별 parquet upsert (url unique) — 전 소스 공유 write.

    Sig: ``writeDailyParquet(df, *, dir, market, day) -> (path, total, added)``

    Capabilities:
        - ``data/{dir}/{MARKET}/{day}.parquet`` 경로에 upsert
        - 기존 파일 있으면 concat(diagonal_relaxed) + url unique(첫 매치 유지)
        - 저장 직전 canonical 17컬럼 강제

    AIContext:
        syncNewsHeadlines·syncGdeltBackfill·syncNaverNews 가 공유 호출. 같은 날짜
        재실행 안전(url dedup).

    Guide:
        dir 은 레지스트리 spec.dir 그대로 전달 — 직접 문자열 조립 금지 (drift).
        기존 행과 url 충돌 시 기존 우선 (keep="first").

    When:
        sync 계열 스크립트의 일별 적재 마지막 단계.

    How:
        coerceToCanonical → 기존 파일 concat(diagonal_relaxed) → url unique → write.

    Requires:
        없음 — 로컬 디스크만.

    Args:
        df: 저장할 DataFrame (canonical 권장; 아니어도 coerce 됨).
        dir: 레지스트리 물리 경로 (예 ``"news/public/rss"``).
        market: 시장 코드 (대문자 정규화).
        day: 일자 (``"YYYY-MM-DD"`` 또는 date).

    Returns:
        (path, total, added) — 저장 경로, 최종 행수, 신규 추가 행수.

    Raises:
        없음 — IO 실패는 호출자에 전파(폴백 없음, 정공법).

    Example:
        >>> # writeDailyParquet(df, dir="news/public/rss", market="KR", day="2026-06-08")

    See Also:
        ``loadSourceDay``: 읽기 대칭 (소스 id 경유).
        ``gather.sources.newsSources.getNewsSource``: dir SSOT 레지스트리.
    """
    dayIso = _dayIso(day)
    outDir = _DATA_ROOT / dir / market.upper()
    outDir.mkdir(parents=True, exist_ok=True)
    target = outDir / f"{dayIso}.parquet"

    incoming = coerceToCanonical(df)
    before = 0
    if target.exists():
        existing = pl.read_parquet(target)
        before = existing.height
        merged = pl.concat([existing, incoming], how="diagonal_relaxed")
    else:
        merged = incoming
    merged = coerceToCanonical(merged).unique(subset=["url"], keep="first")
    merged.write_parquet(target)
    return target, merged.height, merged.height - before


@lru_cache(maxsize=256)
def loadSourceDay(sourceId: str, market: str, dayIso: str) -> pl.DataFrame | None:
    """단일 소스·일자 parquet 로드 — 로컬 우선, public 이면 HF lazy 폴백.

    Sig: ``loadSourceDay(sourceId, market, dayIso) -> pl.DataFrame | None``

    Capabilities:
        - 로컬 ``data/{spec.dir}/{MARKET}/{day}.parquet`` 우선
        - public 소스: 미존재 시 `dataLoader.loadData(category=spec.hfCategory)` HF 폴백
        - private 소스: 로컬 only (저작권 — HF private read 는 서버사이드 별도 훅)
        - LRU 캐시 (256). 테스트는 ``loadSourceDay.cache_clear()``.

    AIContext:
        loadNewsArchive 가 (소스×일자) 격자로 순회 호출. 미존재는 None silent.

    Guide:
        쓰기 직후 같은 키 재조회는 LRU 잔상 가능 — ``loadSourceDay.cache_clear()``
        후 조회 (테스트 패턴 동일).

    When:
        loadNewsArchive 의 (소스×일자) 격자 순회 — 직접 호출은 단일 일자 점검용.

    How:
        로컬 ``data/{spec.dir}/{MARKET}/{day}.parquet`` read → 미존재 + public 이면
        dataLoader.loadData HF 폴백 → 그 외 None.

    Requires:
        없음 — 로컬 우선. public 소스 HF 폴백 경로만 네트워크.

    Args:
        sourceId: 레지스트리 소스 id (``"rss"``|``"gdelt"``|``"naver"``).
        market: 시장 코드 (대문자 정규화).
        dayIso: ``"YYYY-MM-DD"``.

    Returns:
        pl.DataFrame | None — 해당 소스·일자 archive. 미존재 시 None.

    Raises:
        KeyError: 미등록 sourceId (getNewsSource 경유).
        SourceUnavailableError: 로컬 artifact 손상 또는 public HF 로드 실패.

    Example:
        >>> # loadSourceDay("rss", "KR", "2026-06-08")

    See Also:
        ``writeDailyParquet``: 쓰기 대칭.
        ``gather.bulkData.newsHeadlines.loadNewsArchive``: 기간 로드 caller.
    """
    spec = getNewsSource(sourceId)
    marketU = market.upper()
    local = _DATA_ROOT / spec.dir / marketU / f"{dayIso}.parquet"
    if local.exists():
        try:
            return pl.read_parquet(local)
        except (OSError, pl.exceptions.ComputeError) as exc:
            raise SourceUnavailableError(
                f"news local artifact를 읽을 수 없습니다: source={sourceId}, "
                f"market={marketU}, day={dayIso}, path={local}"
            ) from exc

    if spec.visibility != "public":
        return None  # private = 로컬 only (저작권 비공개 캐시)

    try:
        from dartlab.core.dataLoader import loadData

        return loadData(f"{marketU}/{dayIso}", category=spec.hfCategory)
    except Exception as exc:  # noqa: BLE001
        raise SourceUnavailableError(
            f"news public artifact를 가져올 수 없습니다: source={sourceId}, market={marketU}, day={dayIso}"
        ) from exc


__all__ = ["loadSourceDay", "writeDailyParquet"]
