"""scanAccount 오류 계약과 내부 값 타입 회귀."""

from __future__ import annotations

import pytest

from dartlab.providers.edgar.finance.scanAccount.types import (
    EdgarScanError,
    EdgarScanExecutionError,
    EdgarScanMappingError,
    EdgarScanStorageError,
    _TaxonomyTagKeys,
    _TickerUniverse,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "cls",
    [EdgarScanMappingError, EdgarScanStorageError, EdgarScanExecutionError],
)
def testEveryScanErrorSharesOneRoot(cls: type[EdgarScanError]) -> None:
    """모든 스캔 실패는 EdgarScanError 하나로 잡힌다."""
    assert issubclass(cls, EdgarScanError)
    assert issubclass(cls, RuntimeError)


def testErrorKeepsStageAndSource() -> None:
    """실패는 stage 와 source 를 잃지 않는다. 원인 없는 실패를 만들지 않는다."""
    error = EdgarScanStorageError("file_loop_read", "shard read failed", source="/tmp/0001.parquet")

    assert error.stage == "file_loop_read"
    assert error.source == "/tmp/0001.parquet"
    assert "file_loop_read" in str(error)


def testTaxonomyTagKeysIsImmutable() -> None:
    """tag key 묶음은 frozen 이라 소비자가 바꿔 오염시킬 수 없다."""
    keys = _TaxonomyTagKeys(
        usGaap=("revenues",), ifrsFull=("revenue",), usGaapCommon=frozenset(), ifrsFullCommon=frozenset()
    )

    with pytest.raises(AttributeError):
        keys.usGaap = ("changed",)  # type: ignore[misc]


def testTickerUniverseHoldsBothDirections() -> None:
    """universe 는 cik->ticker 와 ticker->title 을 함께 들고 다닌다."""
    universe = _TickerUniverse(cikToTicker={"0000000001": "AAA"}, tickerToTitle={"AAA": "Alpha Inc"})

    assert universe.cikToTicker["0000000001"] == "AAA"
    assert universe.tickerToTitle["AAA"] == "Alpha Inc"
