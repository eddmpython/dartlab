"""KIND 상장목록 장애 시 캐시 오염 회귀.

재시도가 소진되면 빈 목록이 나오고, 그것을 그대로 24 시간짜리 파일 캐시에 저장하고
있었다. 30 초짜리 네트워크 끊김 하나가 KR 종목코드와 회사명 해석을 하루 종일 죽이고,
네트워크가 돌아와도 회복되지 않는다. 사용자에게 나가는 문구는 0 개 로드 완료라서 성공처럼
읽힌다.

빈 결과는 캐시하지 않는다는 것이 여기서 고정하는 계약이다.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import polars as pl
import pytest

import dartlab.gather.krx.listing.registry as registry

_ROWS = pl.DataFrame({"종목코드": ["005930"], "회사명": ["삼성전자"]})


@pytest.fixture
def isolatedCache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """디스크 캐시와 메모리 캐시를 이 테스트 전용으로 격리한다."""

    cachePath = tmp_path / "listing.parquet"
    monkeypatch.setattr(registry, "_cacheFile", lambda: cachePath)
    monkeypatch.setattr(registry, "_memory", None, raising=False)
    monkeypatch.setattr(registry, "_memoryTs", 0.0, raising=False)
    return cachePath


def testOutageDoesNotPersistAnEmptyRegistry(isolatedCache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """장애로 비어 돌아온 목록을 캐시에 굳히면 회복이 막힌다."""

    monkeypatch.setattr(registry, "_fetchKind", lambda: pl.DataFrame({"종목코드": [], "회사명": []}))

    result = registry.getKindList()

    assert result.height == 0
    assert not isolatedCache.exists()


def testHealthyFetchIsPersisted(isolatedCache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """정상 결과는 캐시에 남아야 다음 호출이 빨라진다."""

    monkeypatch.setattr(registry, "_fetchKind", lambda: _ROWS)

    result = registry.getKindList()

    assert result.height == 1
    assert isolatedCache.exists()


def testNextCallRetriesAfterAnOutage(isolatedCache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """장애 뒤 네트워크가 돌아오면 그다음 호출이 실제로 다시 조회해야 한다."""

    calls: list[str] = []

    def failing() -> pl.DataFrame:
        calls.append("fail")
        return pl.DataFrame({"종목코드": [], "회사명": []})

    def healthy() -> pl.DataFrame:
        calls.append("ok")
        return _ROWS

    monkeypatch.setattr(registry, "_fetchKind", failing)
    assert registry.getKindList().height == 0

    monkeypatch.setattr(registry, "_memory", None, raising=False)
    monkeypatch.setattr(registry, "_memoryTs", 0.0, raising=False)
    monkeypatch.setattr(registry, "_fetchKind", healthy)

    assert registry.getKindList().height == 1
    assert calls == ["fail", "ok"]


def testTransportFailureIsRecordedNotSwallowed(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    """재시도가 소진된 뒤 무엇 때문에 비었는지 알 수 있어야 한다."""

    def boom(*_args: object, **_kwargs: object):
        raise httpx.ConnectError("연결 실패")

    monkeypatch.setattr(registry.httpx, "post", boom, raising=False)
    monkeypatch.setattr(registry, "_KIND_BACKOFF_SEC", 0.0, raising=False)

    with caplog.at_level("WARNING"):
        result = registry._fetchKind()

    assert result.height == 0
    assert any("KIND" in record.message for record in caplog.records)
