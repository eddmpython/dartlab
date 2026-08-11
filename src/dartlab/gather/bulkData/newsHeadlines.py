"""news archive 부분 액세스 — 엔진 내부용 (Mode 2).

기간 [start..end] 일별 parquet 을 전 소스(rss·gdelt·naver) 레지스트리 순회로 합쳐
단일 DataFrame 반환. PIT (asof) 옵션 동행 — bitemporal
`business_time=date`/`knowledge_time=captured_at`.

데이터 흐름 (소스-무관):
    1. `newsSources.allNewsSources()` 순회 (sources= 로 선택 가능)
    2. 각 (소스×일자) → `newsIo.loadSourceDay(sourceId, market, day)`
       (로컬 우선, public 이면 HF lazy / private 는 로컬 only)
    3. 결과 concat(diagonal_relaxed) → canonical 17컬럼 coerce → asof 필터 → url dedup

본 모듈은 read-only. write 는 `.github/scripts/sync/sync{NewsHeadlines,GdeltBackfill,
NaverNews}.py` 가 `newsIo.writeDailyParquet` 로 수행 (SSOT).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import date as _date
from datetime import datetime, timedelta

import polars as pl

from ..sources.newsIo import loadSourceDay
from ..sources.newsSchema import NEWS_ARCHIVE_SCHEMA, coerceToCanonical
from ..sources.newsSources import allNewsSources
from ..transforms.pit import applyAsOf
from ..types import SourceUnavailableError

log = logging.getLogger(__name__)


def _toDate(d: str | _date) -> _date:
    """YYYY-MM-DD / YYYYMMDD / date → date."""
    if isinstance(d, _date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    s = str(d).replace("-", "").strip()
    if len(s) >= 8:
        return _date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return _date.today()


def _dayRange(start: _date, end: _date) -> list[_date]:
    """[start..end] inclusive 일자 리스트."""
    if start > end:
        start, end = end, start
    span = (end - start).days
    return [start + timedelta(days=i) for i in range(span + 1)]


def loadNewsArchive(
    start: str | _date,
    end: str | _date,
    market: str = "KR",
    *,
    asof: str | _date | None = None,
    sources: Iterable[str] | None = None,
) -> pl.DataFrame:
    """news archive 기간 로드 (전 소스 레지스트리 순회) + 옵션 PIT 필터.

    Capabilities:
        - 기간 [start..end] × 전 소스(rss·gdelt·naver) 일별 parquet concat
        - sources= 로 소스 선택 (예 ["rss"] → gdelt/naver 제외)
        - asof 지정 시 PIT 필터 (date ≤ asof AND captured_at ≤ asof)
        - canonical 17컬럼 출력 + url dedup
        - `newsIo.loadSourceDay` LRU 캐시 (256) — 반복 호출 메모리 hit

    AIContext:
        Phase B `narrativePulse` + Phase C `analyzeNarrative` + priceEvents API 의
        입력 SSOT. 모든 narrative downstream 이 본 함수 경유.

    Guide:
        forward-only archive — 시작 시점(T0) 이전 일자는 비어 있음. backtest 시
        asof= 사용으로 look-ahead bias 차단. private 소스(naver)는 로컬 데이터가
        있는 환경(sync/서버)에서만 행이 잡힌다.

    When:
        - dartlab.macro("내러티브") 진입점
        - 시나리오 엔진 narrative_signal 계산
        - 사용자 직접: `loadNewsArchive("2026-04-01","2026-05-01","KR")`

    How:
        start..end 일자 루프 × allNewsSources() → loadSourceDay → concat → coerce →
        asof → dedup.

    Requires:
        없음 — 로컬 parquet 우선. public 소스 미존재분만 HF lazy 폴백 (네트워크 선택).

    Args:
        start: 시작일 (포함). YYYY-MM-DD 또는 date.
        end: 종료일 (포함). YYYY-MM-DD 또는 date.
        market: "KR" | "US" | ... 기본 "KR".
        asof: PIT 시점 (포함). None 이면 필터 0.
        sources: 로드할 소스 id 집합. None=전체 (allNewsSources).

    Returns:
        pl.DataFrame — newsSchema.NEWS_ARCHIVE_SCHEMA canonical 17컬럼,
        date desc + url 정렬. 빈 결과도 동일 schema.

    Raises:
        예기치 않은 schema 또는 프로그래밍 오류. 개별 source/day 의
        SourceUnavailableError 는 격리하고 나머지 실제 archive 를 반환한다.

    Example::

        df = loadNewsArchive("2026-05-01", "2026-05-28", "KR")
        rssOnly = loadNewsArchive("2026-05-01", "2026-05-28", "KR", sources=["rss"])

    See Also:
        ``gather.sources.newsIo.loadSourceDay``: 단일 소스·일자 로더.
        ``gather.transforms.pit.applyAsOf``: PIT 필터 SSOT.
    """
    s = _toDate(start)
    e = _toDate(end)
    marketU = market.upper()

    specs = allNewsSources()
    if sources is not None:
        wanted = set(sources)
        specs = [sp for sp in specs if sp.id in wanted]

    frames: list[pl.DataFrame] = []
    for day in _dayRange(s, e):
        dayIso = day.isoformat()
        for sp in specs:
            if marketU not in sp.markets:
                continue
            try:
                df = loadSourceDay(sp.id, marketU, dayIso)
            except SourceUnavailableError as exc:
                log.warning(
                    "news archive source/day 로드 실패를 격리합니다: source=%s market=%s day=%s error=%s",
                    sp.id,
                    marketU,
                    dayIso,
                    exc,
                )
                continue
            if df is not None and df.height > 0:
                frames.append(df)

    if not frames:
        return pl.DataFrame(schema=NEWS_ARCHIVE_SCHEMA)

    out = coerceToCanonical(pl.concat(frames, how="diagonal_relaxed"))
    if asof is not None:
        asofIso = _toDate(asof).isoformat()
        out = applyAsOf(
            out,
            asofIso,
            businessCol="date",
            knowledgeCol="captured_at",
            fallbackCol="date",
        )
    out = out.unique(subset=["url"], keep="first")
    out = out.sort(["date", "url"], descending=[True, False])
    return out
