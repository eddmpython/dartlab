"""core.persist freshness-gated 로컬 저장 단위 테스트 (네트워크 없음).

config.dataDir 를 tmp_path 로 monkeypatch — 실제 data/ 오염 없이 저장/직독/신선도 검증.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from dartlab import config as cfg
from dartlab.core import persist

pytestmark = pytest.mark.unit


@pytest.fixture
def tmpDataDir(tmp_path, monkeypatch):
    """config.dataDir → tmp_path."""
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    return tmp_path


def _sample() -> pl.DataFrame:
    return pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})


def test_savesAndStampsCollectedAt(tmpDataDir):
    """수집 시 collectedAt(ISO) 컬럼 박고 parquet 저장."""
    df = persist.loadOrCollect("naver/theme", _sample)
    assert "collectedAt" in df.columns
    assert (tmpDataDir / "naver" / "theme" / "data.parquet").exists()
    # ISO 파싱 가능
    datetime.fromisoformat(df["collectedAt"][0])


def test_freshReloadSkipsCollect(tmpDataDir):
    """신선하면 collectFn 재호출 없이 로컬 직독."""
    calls = {"n": 0}

    def collect():
        calls["n"] += 1
        return _sample()

    persist.loadOrCollect("cat", collect, maxAgeDays=7)
    persist.loadOrCollect("cat", collect, maxAgeDays=7)  # 두 번째는 직독
    assert calls["n"] == 1


def test_staleTriggersRecollect(tmpDataDir):
    """collectedAt 가 maxAgeDays 초과면 재수집."""
    path = tmpDataDir / "cat" / "data.parquet"
    path.parent.mkdir(parents=True)
    stale = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    pl.DataFrame({"a": [1], "collectedAt": [stale]}).write_parquet(path)

    calls = {"n": 0}

    def collect():
        calls["n"] += 1
        return _sample()

    persist.loadOrCollect("cat", collect, maxAgeDays=7)
    assert calls["n"] == 1  # 10일 > 7일 → 재수집


def test_refreshForceRecollect(tmpDataDir):
    """refresh=True 면 신선해도 재수집."""
    calls = {"n": 0}

    def collect():
        calls["n"] += 1
        return _sample()

    persist.loadOrCollect("cat", collect)
    persist.loadOrCollect("cat", collect, refresh=True)
    assert calls["n"] == 2


def test_emptyResultNotSaved(tmpDataDir):
    """빈 수집 결과는 저장하지 않음 (다음 호출 재시도)."""
    out = persist.loadOrCollect("cat", lambda: pl.DataFrame())
    assert out.is_empty()
    assert not (tmpDataDir / "cat" / "data.parquet").exists()


def test_loadOrCollectAsync(tmpDataDir):
    """async 변형 — 신선하면 직독, 아니면 await collectFn."""
    calls = {"n": 0}

    async def collect():
        calls["n"] += 1
        return _sample()

    async def run():
        await persist.loadOrCollectAsync("cat", collect, maxAgeDays=7)
        df = await persist.loadOrCollectAsync("cat", collect, maxAgeDays=7)
        return df

    df = asyncio.run(run())
    assert "collectedAt" in df.columns
    assert calls["n"] == 1  # 두 번째는 직독
