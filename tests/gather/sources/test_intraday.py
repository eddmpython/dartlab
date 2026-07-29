"""dartlab.gather.sources.intraday mirror + 단위 테스트.

룰 7 (src↔tests 1:1 mirror) + 분봉 source 위임/가드 검증.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.intraday`` 모듈 import 가능."""
    importlib.import_module("dartlab.gather.sources.intraday")


def _bars() -> list[dict]:
    return [{"datetime": "2026-07-06T09:00:00", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10}]


class _FakeNaver:
    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    async def fetchIntraday(self, stockCode, client, *, market="KR", start="", end="", limit=None):
        self.calls.append({"stockCode": stockCode, "market": market, "start": start, "end": end, "limit": limit})
        return self._rows


class _FakeBreaker:
    def __init__(self, isOpenValue):
        self._isOpen = isOpenValue

    def isOpen(self, name):
        return self._isOpen


def test_intraday_delegates_to_naver(monkeypatch) -> None:
    """KR 조회는 loadDomain('naver').fetchIntraday 로 위임하고 인자를 전달한다."""
    from dartlab.gather.sources import intraday

    fake = _FakeNaver(_bars())
    monkeypatch.setattr(intraday, "loadDomain", lambda name: fake)
    monkeypatch.setattr(intraday, "circuitBreaker", _FakeBreaker(False))

    rows = asyncio.run(intraday.fetch("005930", client=object(), start="2026-07-03"))

    assert rows == _bars()
    assert fake.calls[0]["stockCode"] == "005930"
    assert fake.calls[0]["start"] == "2026-07-03"


def test_intraday_non_kr_raises(monkeypatch) -> None:
    """KR 외 시장은 네트워크 접근 없이 명시적 입력 오류."""
    from dartlab.gather.sources import intraday

    def _forbidden(name):
        raise AssertionError("KR 외 시장에서 loadDomain 호출 금지")

    monkeypatch.setattr(intraday, "loadDomain", _forbidden)

    with pytest.raises(ValueError, match="KR 시장"):
        asyncio.run(intraday.fetch("AAPL", market="US", client=object()))


def test_intraday_circuit_open_raises_with_cause(monkeypatch) -> None:
    """naver 서킷이 열려 있으면 source 실패 원인을 보존한다."""
    from dartlab.gather.sources import intraday
    from dartlab.gather.types import CircuitOpenError, SourceAttemptsExhaustedError

    def _forbidden(name):
        raise AssertionError("서킷 open 시 loadDomain 호출 금지")

    monkeypatch.setattr(intraday, "circuitBreaker", _FakeBreaker(True))
    monkeypatch.setattr(intraday, "loadDomain", _forbidden)

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(intraday.fetch("005930", client=object()))

    assert isinstance(excInfo.value.failures["naver"], CircuitOpenError)


def test_intraday_invalid_code_value_error_is_not_aggregated(monkeypatch) -> None:
    """도메인 입력 ValueError는 source 실패 aggregate로 감싸지 않는다."""
    from dartlab.gather.sources import intraday

    class InvalidNaver:
        async def fetchIntraday(self, *args, **kwargs):
            raise ValueError("invalid stock code")

    monkeypatch.setattr(intraday, "loadDomain", lambda name: InvalidNaver())
    monkeypatch.setattr(intraday, "circuitBreaker", _FakeBreaker(False))

    with pytest.raises(ValueError, match="invalid stock code"):
        asyncio.run(intraday.fetch("bad", client=object()))
