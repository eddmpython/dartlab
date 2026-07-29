"""EDGAR native payload — 별도 panelCell 없이 panel contentRaw 에서 encode/decode."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_native_payload_roundtrip() -> None:
    from dartlab.providers.edgar.panel.native import decodeNativeCellsPayload, encodeNativeCellsPayload

    cells = [{"statement": "IS", "concept": "Revenues", "valueRaw": "123"}]
    payload = encodeNativeCellsPayload(cells)
    assert decodeNativeCellsPayload(payload) == cells


def test_account_mapping_failure_is_not_relabelled_as_unmapped(monkeypatch) -> None:
    """매핑 SSOT 고장은 원래 concept fallback으로 위장하지 않고 호출자에게 전달한다."""
    from dartlab.providers.edgar.finance import mapper as mapperModule
    from dartlab.providers.edgar.panel.native import _accountColumn

    class BrokenMapper:
        def __init__(self):
            raise RuntimeError("mapping ledger corrupt")

    monkeypatch.setattr(mapperModule, "EdgarMapper", BrokenMapper)

    with pytest.raises(RuntimeError, match="mapping ledger corrupt"):
        _accountColumn(pl.DataFrame({"concept": ["Revenue"]}), "IS")
