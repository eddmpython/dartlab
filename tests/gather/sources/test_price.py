"""dartlab.gather.sources.price real unit test (A 트랙 O2 + T4).

price 의 fallback chain emit 신호 + 모듈 import 회귀 검증. 실제 외부 fetch 는
monkeypatch 으로 mock — 네트워크 0.
"""

from __future__ import annotations

import asyncio
import importlib
import types

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.price`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.price")


def test_price_fallback_emit(monkeypatch: pytest.MonkeyPatch) -> None:
    """primary source 실패 시 emitGatherFallback 호출 — A 트랙 O2.

    chain 의 첫 source 가 GatherError raise 하면 두 번째 source 가 fallback 으로
    선언되어야 한다. core.messaging.emit 을 capture 하여 신호 도달 검증.
    """
    from dartlab.gather.infra import telemetry as telemetryMod
    from dartlab.gather.sources import price as priceMod
    from dartlab.gather.types import GatherError

    captured: list = []

    def fakeEmit(key: str, **kwargs: object) -> None:
        captured.append((key, kwargs))

    monkeypatch.setattr(telemetryMod, "_coreEmit", fakeEmit)

    monkeypatch.setattr(priceMod, "getPriceFallback", lambda market: ["naver", "yahooChart"])
    priceMod._staleCache.clear()

    fakeHealth = types.SimpleNamespace(reorder=lambda chain: chain, record=lambda *a, **kw: None)
    fakeCircuit = types.SimpleNamespace(
        isOpen=lambda src: False,
        recordFailure=lambda src: None,
        recordSuccess=lambda src: None,
    )
    monkeypatch.setattr(priceMod, "healthTracker", fakeHealth)
    monkeypatch.setattr(priceMod, "circuitBreaker", fakeCircuit)

    async def fakeFetchPriceFail(stockCode, client, *, market):
        raise GatherError("simulated source failure")

    async def fakeFetchPriceOk(stockCode, client, *, market):
        from dartlab.gather.types import PriceSnapshot

        return PriceSnapshot(current=70000.0, change=0.0, change_pct=0.0)

    def fakeLoadDomain(name: str):
        mod = types.SimpleNamespace()
        if name == "naver":
            mod.fetchPrice = fakeFetchPriceFail
        else:
            mod.fetchPrice = fakeFetchPriceOk
        return mod

    monkeypatch.setattr(priceMod, "loadDomain", fakeLoadDomain)

    async def runner():
        return await priceMod.fetch("005930", market="KR", client=object())

    result = asyncio.run(runner())
    assert result is not None

    fallbackEmits = [c for c in captured if c[0] == "gather:fallback"]
    assert len(fallbackEmits) == 1
    _, kwargs = fallbackEmits[0]
    assert kwargs["axis"] == "price"
    assert kwargs["primary"] == "naver"
    assert kwargs["fallback"] == "yahooChart"


def test_price_fallback_no_emit_when_last_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """마지막 source 실패 시에는 fallback emit 안 함 — 다음 source 가 없음."""
    from dartlab.gather.infra import telemetry as telemetryMod
    from dartlab.gather.sources import price as priceMod
    from dartlab.gather.types import GatherError, SourceAttemptsExhaustedError

    captured: list = []
    monkeypatch.setattr(telemetryMod, "_coreEmit", lambda k, **kw: captured.append((k, kw)))

    monkeypatch.setattr(priceMod, "getPriceFallback", lambda market: ["naver"])
    priceMod._staleCache.clear()

    fakeHealth = types.SimpleNamespace(reorder=lambda chain: chain, record=lambda *a, **kw: None)
    fakeCircuit = types.SimpleNamespace(
        isOpen=lambda src: False,
        recordFailure=lambda src: None,
        recordSuccess=lambda src: None,
    )
    monkeypatch.setattr(priceMod, "healthTracker", fakeHealth)
    monkeypatch.setattr(priceMod, "circuitBreaker", fakeCircuit)

    async def fakeFail(stockCode, client, *, market):
        raise GatherError("only source failed")

    def fakeLoadDomain(name: str):
        mod = types.SimpleNamespace()
        mod.fetchPrice = fakeFail
        return mod

    monkeypatch.setattr(priceMod, "loadDomain", fakeLoadDomain)

    async def runner():
        return await priceMod.fetch("005930", market="KR", client=object())

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(runner())

    fallbackEmits = [c for c in captured if c[0] == "gather:fallback"]
    assert len(fallbackEmits) == 0
    assert isinstance(excInfo.value.failures["naver"], GatherError)


def test_price_valid_empty_is_not_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """공급자가 정상 응답으로 None을 반환하면 정상 무데이터로 유지한다."""
    from dartlab.gather.sources import price as priceMod

    priceMod._staleCache.clear()
    monkeypatch.setattr(priceMod, "getPriceFallback", lambda market: ["naver"])
    monkeypatch.setattr(
        priceMod,
        "healthTracker",
        types.SimpleNamespace(reorder=lambda chain: chain, record=lambda *a, **kw: None),
    )
    monkeypatch.setattr(
        priceMod,
        "circuitBreaker",
        types.SimpleNamespace(
            isOpen=lambda src: False,
            recordFailure=lambda src: None,
            recordSuccess=lambda src: None,
        ),
    )

    async def empty(*args, **kwargs):
        return None

    monkeypatch.setattr(priceMod, "loadDomain", lambda name: types.SimpleNamespace(fetchPrice=empty))

    assert asyncio.run(priceMod.fetch("005930", market="KR", client=object())) is None


def test_price_empty_response_stays_distinct_from_other_source_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """한 source의 정상 무데이터가 있으면 다른 source 장애와 구분해 None을 반환한다."""
    from dartlab.gather.sources import price as priceMod
    from dartlab.gather.types import SourceUnavailableError

    priceMod._staleCache.clear()
    monkeypatch.setattr(priceMod, "getPriceFallback", lambda market: ["naver", "fdr"])
    monkeypatch.setattr(
        priceMod,
        "healthTracker",
        types.SimpleNamespace(reorder=lambda chain: chain, record=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        priceMod,
        "circuitBreaker",
        types.SimpleNamespace(
            isOpen=lambda src: False,
            recordFailure=lambda src: None,
            recordSuccess=lambda src: None,
        ),
    )

    async def empty(*args, **kwargs):
        return None

    async def fail(*args, **kwargs):
        raise SourceUnavailableError("down")

    modules = {
        "naver": types.SimpleNamespace(fetchPrice=empty),
        "fdr": types.SimpleNamespace(fetchPrice=fail),
    }
    monkeypatch.setattr(priceMod, "loadDomain", modules.__getitem__)

    assert asyncio.run(priceMod.fetch("005930", market="KR", client=object())) is None


def test_price_invalid_input_is_not_fallback_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """호출자 입력 ValueError는 fallback aggregate로 감싸거나 다음 source로 넘기지 않는다."""
    from dartlab.gather.sources import price as priceMod

    calls: list[str] = []
    priceMod._staleCache.clear()
    monkeypatch.setattr(priceMod, "getPriceFallback", lambda market: ["naver", "fdr"])
    monkeypatch.setattr(
        priceMod,
        "healthTracker",
        types.SimpleNamespace(reorder=lambda chain: chain, record=lambda *a, **kw: None),
    )
    monkeypatch.setattr(
        priceMod,
        "circuitBreaker",
        types.SimpleNamespace(
            isOpen=lambda src: False,
            recordFailure=lambda src: None,
            recordSuccess=lambda src: None,
        ),
    )

    async def invalid(*args, **kwargs):
        raise ValueError("invalid stock code")

    monkeypatch.setattr(
        priceMod,
        "loadDomain",
        lambda name: calls.append(name) or types.SimpleNamespace(fetchPrice=invalid),
    )

    with pytest.raises(ValueError, match="invalid stock code"):
        asyncio.run(priceMod.fetch("bad", market="KR", client=object()))

    assert calls == ["naver"]


def test_price_all_circuits_open_preserves_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """모든 circuit open은 빈 스냅샷이 아니라 source별 실패 원인이다."""
    from dartlab.gather.sources import price as priceMod
    from dartlab.gather.types import CircuitOpenError, SourceAttemptsExhaustedError

    priceMod._staleCache.clear()
    monkeypatch.setattr(priceMod, "getPriceFallback", lambda market: ["naver", "fdr"])
    monkeypatch.setattr(
        priceMod,
        "healthTracker",
        types.SimpleNamespace(reorder=lambda chain: chain, record=lambda *a, **kw: None),
    )
    monkeypatch.setattr(priceMod, "circuitBreaker", types.SimpleNamespace(isOpen=lambda src: True))

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(priceMod.fetch("005930", market="KR", client=object()))

    assert list(excInfo.value.failures) == ["naver", "fdr"]
    assert all(isinstance(exc, CircuitOpenError) for exc in excInfo.value.failures.values())
