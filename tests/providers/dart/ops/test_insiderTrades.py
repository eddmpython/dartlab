"""providers/dart/ops/insiderTrades.py mirror smoke — P6."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.dart.ops.insiderTrades  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_fetch_insider_trading_raw_callable() -> None:
    """fetchInsiderTradingRaw() callable smoke."""
    from dartlab.providers.dart.ops.insiderTrades import fetchInsiderTradingRaw

    assert callable(fetchInsiderTradingRaw)


def test_fetch_major_shareholders_raw_callable() -> None:
    """fetchMajorShareholdersRaw() callable smoke."""
    from dartlab.providers.dart.ops.insiderTrades import fetchMajorShareholdersRaw

    assert callable(fetchMajorShareholdersRaw)


def test_iter_insider_trading_raw_callable() -> None:
    """iterInsiderTradingRaw() callable smoke."""
    from dartlab.providers.dart.ops.insiderTrades import iterInsiderTradingRaw

    assert callable(iterInsiderTradingRaw)


def test_iter_major_shareholders_raw_callable() -> None:
    """iterMajorShareholdersRaw() callable smoke."""
    from dartlab.providers.dart.ops.insiderTrades import iterMajorShareholdersRaw

    assert callable(iterMajorShareholdersRaw)


@pytest.mark.asyncio
async def test_fetch_insider_trading_propagates_provider_initialization_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API key/composition 실패를 실제 0건으로 위장하지 않는다."""
    from dartlab.providers.dart.ops import insiderTrades

    def failGetDart():
        raise ValueError("DART API key missing")

    monkeypatch.setattr(insiderTrades, "_getDart", failGetDart)

    with pytest.raises(ValueError, match="API key missing"):
        await insiderTrades.fetchInsiderTradingRaw("005930")


@pytest.mark.asyncio
async def test_fetch_insider_trading_propagates_call_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """네트워크/클라이언트 오류의 원래 타입과 메시지를 보존한다."""
    from dartlab.providers.dart.ops import insiderTrades

    class FailingDart:
        def executiveShares(self, _stockCode: str):
            raise OSError("DART unavailable")

    monkeypatch.setattr(insiderTrades, "_getDart", FailingDart)

    with pytest.raises(OSError, match="DART unavailable"):
        await insiderTrades.fetchInsiderTradingRaw("005930")


@pytest.mark.asyncio
async def test_fetch_major_shareholders_returns_empty_only_for_normal_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """정상 빈 DataFrame만 의미 있는 0건으로 반환한다."""
    from dartlab.providers.dart.ops import insiderTrades

    class EmptyDart:
        def majorShareholders(self, _stockCode: str) -> pl.DataFrame:
            return pl.DataFrame()

    monkeypatch.setattr(insiderTrades, "_getDart", EmptyDart)

    assert await insiderTrades.fetchMajorShareholdersRaw("005930") == []


@pytest.mark.asyncio
async def test_fetch_insider_trading_rejects_malformed_numeric_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """손상된 숫자를 0으로 삼키지 않는다."""
    from dartlab.providers.dart.ops import insiderTrades

    class MalformedDart:
        def executiveShares(self, _stockCode: str) -> pl.DataFrame:
            return pl.DataFrame(
                {
                    "rcept_dt": ["2024-08-07"],
                    "repror": ["정용준"],
                    "sp_stock_lmp_irds_cnt": ["not-a-number"],
                    "sp_stock_lmp_cnt": ["2,000"],
                }
            )

    monkeypatch.setattr(insiderTrades, "_getDart", MalformedDart)

    with pytest.raises(ValueError, match="invalid DART integer field"):
        await insiderTrades.fetchInsiderTradingRaw("005930")


@pytest.mark.asyncio
async def test_fetch_raw_rejects_negative_limit() -> None:
    """음수 상한의 파이썬 slice 의미를 API 계약으로 노출하지 않는다."""
    from dartlab.providers.dart.ops.insiderTrades import fetchInsiderTradingRaw

    with pytest.raises(ValueError, match="0 이상"):
        await fetchInsiderTradingRaw("005930", limit=-1)


def test_safe_float_rejects_non_finite_values() -> None:
    """NaN/무한대를 지분율로 소비자에게 흘려보내지 않는다."""
    from dartlab.providers.dart.ops.insiderTrades import _safeFloat

    with pytest.raises(ValueError, match="non-finite"):
        _safeFloat("nan")
