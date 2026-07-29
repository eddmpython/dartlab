"""Phase A — newsHeadlines.loadNewsArchive 단위 테스트.

일별 sharding concat + asof PIT 필터 + dedup + 빈 결과 schema 회귀 가드.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import polars as pl
import pytest

from dartlab.gather.bulkData import newsHeadlines
from dartlab.gather.sources import newsIo
from dartlab.gather.sources.newsSchema import NEWS_ARCHIVE_SCHEMA
from dartlab.gather.sources.newsSources import getNewsSource
from dartlab.gather.types import SourceUnavailableError

pytestmark = pytest.mark.unit

_RSS_DIR = getNewsSource("rss").dir  # "news/public/rss"
_NAVER_DIR = getNewsSource("naver").dir  # "news/private/naver"


def _writeDay(root: Path, market: str, day: str, rows: list[dict], *, sourceDir: str = _RSS_DIR) -> None:
    p = root / sourceDir / market / f"{day}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows).with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("captured_at").cast(pl.Datetime("us", time_zone="UTC")),
    )
    df.write_parquet(p)


@pytest.fixture
def isolatedArchive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """newsIo._DATA_ROOT 를 tmp 로 격리 + loadSourceDay lru_cache 초기화."""
    monkeypatch.setattr(newsIo, "_DATA_ROOT", tmp_path)
    # 로컬 부재 시 public 소스가 HF loadData 로 실데이터 auto-download → 격리 깨짐.
    # loadData 를 None 으로 막아 로컬(tmp)만 보게 한다(완전 오프라인 단위 테스트).
    monkeypatch.setattr("dartlab.core.dataLoader.loadData", lambda *a, **k: None)
    newsIo.loadSourceDay.cache_clear()
    return tmp_path


def test_loader_empty_returns_schema(isolatedArchive: Path) -> None:
    """archive 0 일 → 빈 DataFrame + canonical 17 컬럼 schema 유지."""
    df = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-03", "KR")
    assert df.height == 0
    assert set(df.columns) == set(NEWS_ARCHIVE_SCHEMA.keys())


def test_loader_concat_range(isolatedArchive: Path) -> None:
    """기간 [a..c] 3 일 parquet 각각 1 행 → 3 행 concat."""
    cap = datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc)
    for day, url in [("2026-05-01", "u1"), ("2026-05-02", "u2"), ("2026-05-03", "u3")]:
        _writeDay(
            isolatedArchive,
            "KR",
            day,
            [{"date": day, "title": "t", "source": "s", "url": url, "market": "KR", "query": "q", "captured_at": cap}],
        )

    df = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-03", "KR")
    assert df.height == 3
    assert sorted(df["url"].to_list()) == ["u1", "u2", "u3"]


def test_loader_asof_filter(isolatedArchive: Path) -> None:
    """asof=2026-05-02 → 그 이전 captured_at 만 유지."""
    cap1 = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    cap2 = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    cap3 = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc)
    rows_by_day = [
        ("2026-05-01", "u1", cap1),
        ("2026-05-02", "u2", cap2),
        ("2026-05-03", "u3", cap3),
    ]
    for day, url, cap in rows_by_day:
        _writeDay(
            isolatedArchive,
            "KR",
            day,
            [{"date": day, "title": "t", "source": "s", "url": url, "market": "KR", "query": "q", "captured_at": cap}],
        )

    df = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-03", "KR", asof="2026-05-02")
    urls = set(df["url"].to_list())
    assert "u1" in urls
    assert "u3" not in urls  # captured_at 5-03 > asof 5-02


def test_loader_dedup_by_url(isolatedArchive: Path) -> None:
    """같은 url 이 두 일자 parquet 에 등장 → 1 행만 유지."""
    cap = datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc)
    _writeDay(
        isolatedArchive,
        "KR",
        "2026-05-01",
        [
            {
                "date": "2026-05-01",
                "title": "t1",
                "source": "s",
                "url": "shared",
                "market": "KR",
                "query": "q1",
                "captured_at": cap,
            }
        ],
    )
    _writeDay(
        isolatedArchive,
        "KR",
        "2026-05-02",
        [
            {
                "date": "2026-05-02",
                "title": "t2",
                "source": "s",
                "url": "shared",
                "market": "KR",
                "query": "q2",
                "captured_at": cap,
            }
        ],
    )

    df = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-02", "KR")
    assert df.height == 1
    assert df["url"][0] == "shared"


def test_loader_market_isolation(isolatedArchive: Path) -> None:
    """KR 과 US 디렉터리 격리 — KR fetch 시 US 안 섞임."""
    cap = datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc)
    _writeDay(
        isolatedArchive,
        "KR",
        "2026-05-01",
        [
            {
                "date": "2026-05-01",
                "title": "kr",
                "source": "s",
                "url": "u-kr",
                "market": "KR",
                "query": "q",
                "captured_at": cap,
            }
        ],
    )
    _writeDay(
        isolatedArchive,
        "US",
        "2026-05-01",
        [
            {
                "date": "2026-05-01",
                "title": "us",
                "source": "s",
                "url": "u-us",
                "market": "US",
                "query": "q",
                "captured_at": cap,
            }
        ],
    )

    df = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-01", "KR")
    assert df.height == 1
    assert df["url"][0] == "u-kr"


def test_loader_includes_naver_and_sources_filter(isolatedArchive: Path) -> None:
    """private naver 로컬 parquet 포함 + sources=["rss"] 선택 시 naver 제외."""
    cap = datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc)
    rssRow = {
        "date": "2026-05-01",
        "title": "rss",
        "source": "s",
        "url": "u-rss",
        "market": "KR",
        "query": "q",
        "captured_at": cap,
    }
    naverRow = {
        "date": "2026-05-01",
        "title": "naver",
        "source": "naver.com",
        "url": "u-naver",
        "market": "KR",
        "query": "q",
        "captured_at": cap,
        "description": "스니펫",
    }
    _writeDay(isolatedArchive, "KR", "2026-05-01", [rssRow], sourceDir=_RSS_DIR)
    _writeDay(isolatedArchive, "KR", "2026-05-01", [naverRow], sourceDir=_NAVER_DIR)

    # 기본 — rss + naver 둘 다
    both = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-01", "KR")
    assert set(both["url"].to_list()) == {"u-rss", "u-naver"}
    # naver description 보존
    naverDesc = both.filter(pl.col("url") == "u-naver")["description"].to_list()
    assert naverDesc == ["스니펫"]

    # sources=["rss"] — naver 제외
    rssOnly = newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-01", "KR", sources=["rss"])
    assert rssOnly["url"].to_list() == ["u-rss"]


def test_loader_propagates_source_failure(isolatedArchive: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """기간 로더도 소스 장애를 빈 archive로 바꾸지 않는다."""

    def failLoad(*_args, **_kwargs):
        raise SourceUnavailableError("rss failed")

    monkeypatch.setattr(newsHeadlines, "loadSourceDay", failLoad)

    with pytest.raises(SourceUnavailableError, match="rss failed"):
        newsHeadlines.loadNewsArchive("2026-05-01", "2026-05-01", "KR", sources=["rss"])
