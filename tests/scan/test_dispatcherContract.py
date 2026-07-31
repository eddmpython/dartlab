"""scan US 시장 dispatch 정체성·계약 회귀.

US scan 축이 형제 축과 같은 상장 universe와 ticker 정체성을 쓰는지, 미구현 축을
값처럼 보이는 DataFrame 대신 loud 하게 거부하는지 고정한다.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def testEdgarScanUnknownAxisRaisesLoud() -> None:
    """미구현 US 축은 값처럼 보이는 info DataFrame 이 아니라 ValueError 로 거부한다."""
    from dartlab.scan.builders.edgar.scan import edgarScan

    with pytest.raises(ValueError, match="구현되지 않았"):
        edgarScan("__nonexistent__")


def testEdgarScanKnownAxisStillDispatches(monkeypatch: pytest.MonkeyPatch) -> None:
    """구현된 축은 그대로 dispatch 된다 (loud 전환이 정상 경로를 깨지 않는다)."""
    import dartlab.scan.builders.edgar.scan as scanModule

    monkeypatch.setattr(scanModule, "scanEdgarAccounts", lambda *_a, **_k: pl.DataFrame({"stockCode": []}))
    out = scanModule.edgarScan("profitability")
    assert isinstance(out, pl.DataFrame)


def _writeFinanceParquet(path: Path, tag: str, val: float, fy: int, entityName: str) -> None:
    """합성 EDGAR finance parquet 한 종목을 쓴다."""
    pl.DataFrame(
        {
            "tag": [tag],
            "val": [float(val)],
            "fy": [fy],
            "form": ["10-K"],
            "entityName": [entityName],
        }
    ).write_parquet(path)


def testScanEdgarRawTagsUsesTickerIdentityAndListedUniverse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """audit(raw tags)이 형제 US 축과 같은 ticker 정체성 + 상장 universe만 쓴다."""
    financeDir = tmp_path / "edgar" / "finance"
    financeDir.mkdir(parents=True)
    _writeFinanceParquet(financeDir / "0000000001.parquet", "AuditFees", 1000, 2024, "Alpha Inc")
    _writeFinanceParquet(financeDir / "0000000002.parquet", "AuditFees", 2000, 2024, "Beta Inc")
    _writeFinanceParquet(financeDir / "0000000009.parquet", "AuditFees", 9000, 2024, "Delisted Inc")

    import dartlab.scan.builders.edgar.helpers as h

    monkeypatch.setattr("dartlab.core.dataLoader._getDataRoot", lambda: tmp_path)
    monkeypatch.setattr(h, "edgarCikToTicker", lambda *_a, **_k: {"0000000001": "AAA", "0000000002": "BBB"})

    out = h.scanEdgarRawTags(["AuditFees"])
    codes = out["stockCode"].to_list()

    # 상장 ticker 정체성 (raw CIK 아님)
    assert set(codes) == {"AAA", "BBB"}
    # 비상장 CIK 는 universe 에서 제외
    assert "0000000009" not in codes
    assert "9000" not in [str(v) for v in codes]
    # 값 보존
    rows = {r["stockCode"]: r for r in out.iter_rows(named=True)}
    assert rows["AAA"]["AuditFees"] == 1000.0
    assert rows["BBB"]["AuditFees"] == 2000.0
