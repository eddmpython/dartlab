"""컨센서스 수집의 gather 소유권 회귀 가드.

_fetchConsensusRevenue 가 공유 싱글턴 gather 를 close 하면 이후 모든 gather 호출이
"client has been closed" 로 죽는다 (2026-07-03 전상장사 sweep 2번째 회사 전멸 실측).
빌린 싱글턴을 닫지 않음을 고정한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _Item:
    fiscal_year: int = 2026
    revenue_est: float = 100.0
    source: str = "test"


class _FakeGather:
    def __init__(self):
        self.closed = False

    def revenueConsensus(self, stockCode, *, market="KR"):
        return [_Item()]

    def close(self):
        self.closed = True


class _FakeProvider:
    def __init__(self, gather):
        self._g = gather

    def getDefaultGather(self):
        return self._g


def test_consensus_fetch_does_not_close_shared_gather(monkeypatch):
    from dartlab.analysis.forecast import _revenueForecastLifecycle as helpers
    from dartlab.core import di

    fake = _FakeGather()
    monkeypatch.setattr(di, "getMacroProvider", lambda: _FakeProvider(fake))
    helpers._fetchConsensusRevenue.cache_clear()

    out = helpers._fetchConsensusRevenue("999998")  # lru_cache 회피용 고유 코드
    assert out == ((2026, 100.0, "test"),)
    assert fake.closed is False  # 싱글턴 차용: close 금지

    # 두 번째 회사도 같은 (열린) 싱글턴으로 성공해야 한다
    out2 = helpers._fetchConsensusRevenue("999997")
    assert out2 and fake.closed is False


def test_analyst_never_owns_the_singleton(monkeypatch):
    from dartlab.core import di

    fake = _FakeGather()
    monkeypatch.setattr(di, "getMacroProvider", lambda: _FakeProvider(fake))
    from dartlab.analysis.valuation.analyst import Analyst

    a = Analyst()
    a.close()
    assert fake.closed is False  # close() 는 차용 싱글턴을 건드리지 않는다
