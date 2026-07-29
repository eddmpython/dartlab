"""newsIo 단위 — 일별 parquet write/load 공유 IO (네트워크 0, tmp_path 격리).

writeDailyParquet upsert(url dedup)·canonical 강제, loadSourceDay 로컬 읽기·
private 로컬 only·미등록 KeyError. _DATA_ROOT patch + lru cache_clear 패턴.
"""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from dartlab.gather.sources import newsIo
from dartlab.gather.sources.newsIo import loadSourceDay, writeDailyParquet
from dartlab.gather.sources.newsSchema import NEWS_ARCHIVE_SCHEMA
from dartlab.gather.types import SourceUnavailableError

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _isolated_data_root(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """_DATA_ROOT 를 tmp 로 격리 + loadSourceDay LRU 무효화 (모듈 docstring 계약)."""
    monkeypatch.setattr(newsIo, "_DATA_ROOT", tmp_path)
    loadSourceDay.cache_clear()
    yield
    loadSourceDay.cache_clear()


def _df(*urls: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date": [date(2026, 6, 8)] * len(urls),
            "title": [f"t-{u}" for u in urls],
            "source": ["s"] * len(urls),
            "url": list(urls),
        }
    )


def test_write_creates_canonical_daily_parquet(tmp_path) -> None:
    """신규 write → data/{dir}/{MARKET}/{day}.parquet, canonical 17컬럼·행수 반환."""
    path, total, added = writeDailyParquet(_df("u1", "u2"), dir="news/public/rss", market="kr", day="2026-06-08")
    assert path == tmp_path / "news" / "public" / "rss" / "KR" / "2026-06-08.parquet"
    assert (total, added) == (2, 2)
    saved = pl.read_parquet(path)
    assert list(saved.columns) == list(NEWS_ARCHIVE_SCHEMA.keys())


def test_write_upsert_dedups_url_keep_first(tmp_path) -> None:
    """같은 날짜 재실행 → url unique(기존 우선), 신규만 added 집계."""
    writeDailyParquet(_df("u1"), dir="news/public/rss", market="KR", day=date(2026, 6, 8))
    path, total, added = writeDailyParquet(_df("u1", "u2"), dir="news/public/rss", market="KR", day=date(2026, 6, 8))
    assert (total, added) == (2, 1)
    saved = pl.read_parquet(path)
    # keep="first" — 기존 행(title=t-u1) 보존
    assert saved.filter(pl.col("url") == "u1")["title"][0] == "t-u1"


def test_load_source_day_reads_local() -> None:
    """로컬 파일 존재 → 그대로 로드 (rss 소스 dir 매핑)."""
    writeDailyParquet(_df("u1"), dir="news/public/rss", market="KR", day="2026-06-08")
    out = loadSourceDay("rss", "KR", "2026-06-08")
    assert out is not None and out.height == 1
    assert out["url"][0] == "u1"


def test_load_private_source_local_only() -> None:
    """private(naver) 미존재 → HF 폴백 없이 None (저작권 비공개 캐시 계약)."""
    assert loadSourceDay("naver", "KR", "2026-06-08") is None
    writeDailyParquet(_df("n1"), dir="news/private/naver", market="KR", day="2026-06-08")
    loadSourceDay.cache_clear()
    out = loadSourceDay("naver", "KR", "2026-06-08")
    assert out is not None and out["url"][0] == "n1"


def test_load_corrupt_local_source_raises_with_context(tmp_path) -> None:
    """존재하는 로컬 artifact 손상은 정상 부재로 강등하지 않는다."""
    local = tmp_path / "news" / "public" / "rss" / "KR" / "2026-06-08.parquet"
    local.parent.mkdir(parents=True)
    local.write_bytes(b"not parquet")

    with pytest.raises(SourceUnavailableError, match="source=rss") as excInfo:
        loadSourceDay("rss", "KR", "2026-06-08")

    assert isinstance(excInfo.value.__cause__, (OSError, pl.exceptions.ComputeError))


def test_load_public_hf_failure_raises_with_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    """public HF 장애는 해당 일자의 정상 무데이터로 위장하지 않는다."""
    upstream = RuntimeError("hf unavailable")

    def failLoad(*_args, **_kwargs):
        raise upstream

    monkeypatch.setattr("dartlab.core.dataLoader.loadData", failLoad)

    with pytest.raises(SourceUnavailableError, match="source=rss") as excInfo:
        loadSourceDay("rss", "KR", "2026-06-08")

    assert excInfo.value.__cause__ is upstream


def test_load_unknown_source_raises() -> None:
    """미등록 sourceId → KeyError (getNewsSource 경유)."""
    with pytest.raises(KeyError, match="미등록"):
        loadSourceDay("nope", "KR", "2026-06-08")
