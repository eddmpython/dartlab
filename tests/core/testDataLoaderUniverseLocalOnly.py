"""EDGAR universe의 갱신 경로와 snapshot-only 경계를 검증한다."""

from __future__ import annotations

import polars as pl
import pytest


def testEdgarListedUniverseLocalOnlyNeverCallsUpdater(tmp_path, monkeypatch):
    """Data Workbench용 local-only read는 network 갱신 seam을 건드리지 않는다."""

    from dartlab.core import dataLoader

    universePath = tmp_path / "edgar" / "listedUniverse.parquet"
    universePath.parent.mkdir(parents=True)
    expected = pl.DataFrame(
        {
            "cik": ["0000320193"],
            "ticker": ["AAPL"],
            "title": ["Apple Inc."],
            "exchange": ["Nasdaq"],
            "is_exchange_listed": [True],
            "is_otc": [False],
        }
    )
    expected.write_parquet(universePath)
    monkeypatch.setattr(dataLoader, "_getDataRoot", lambda: tmp_path)
    monkeypatch.setattr(
        dataLoader,
        "updateEdgarListedUniverse",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("localOnly=True가 updater를 호출했습니다")),
    )

    observed = dataLoader.loadEdgarListedUniverse(localOnly=True)

    assert observed.equals(expected)


def testEdgarListedUniverseRejectsConflictingRefreshPolicy():
    """강제 갱신과 local-only는 모호하게 함께 실행하지 않는다."""

    from dartlab.core.dataLoader import loadEdgarListedUniverse

    with pytest.raises(ValueError, match="함께 사용할 수 없습니다"):
        loadEdgarListedUniverse(forceUpdate=True, localOnly=True)
