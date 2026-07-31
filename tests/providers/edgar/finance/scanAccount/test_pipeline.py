"""scanAccount parquet 실행과 결과 조립 회귀."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from dartlab.providers.edgar.finance.scanAccount.pipeline import (
    _EdgarFileProcessor,
    _listedParquetFiles,
    _resultFromLong,
)
from dartlab.providers.edgar.finance.scanAccount.types import EdgarScanMappingError, _TaxonomyTagKeys

pytestmark = pytest.mark.unit


def _keys() -> _TaxonomyTagKeys:
    """매출 하나만 보는 최소 tag key 묶음."""
    return _TaxonomyTagKeys(
        usGaap=("revenues",),
        ifrsFull=("revenue",),
        usGaapCommon=frozenset({"revenues"}),
        ifrsFullCommon=frozenset({"revenue"}),
    )


def testListedFilesKeepOnlyMappedCiks(tmp_path: Path) -> None:
    """상장 매핑에 없는 shard 는 스캔 대상에서 빠진다."""
    for cik in ("0000000001", "0000000002", "0000000009"):
        (tmp_path / f"{cik}.parquet").write_bytes(b"x")

    files = _listedParquetFiles(tmp_path, {"0000000001": "AAA", "0000000002": "BBB"})

    assert sorted(f.stem for f in files) == ["0000000001", "0000000002"]


def testListedFilesAreDeterministic(tmp_path: Path) -> None:
    """같은 입력은 같은 순서를 낸다. 순서가 흔들리면 결과 봉인이 깨진다."""
    for cik in ("0000000003", "0000000001", "0000000002"):
        (tmp_path / f"{cik}.parquet").write_bytes(b"x")
    mapping = {f"000000000{i}": f"T{i}" for i in (1, 2, 3)}

    assert _listedParquetFiles(tmp_path, mapping) == _listedParquetFiles(tmp_path, mapping)


def testUnmappedCikRaisesInsteadOfSkipping(tmp_path: Path) -> None:
    """ticker 매핑이 없는 shard 는 조용히 건너뛰지 않고 실패로 올린다."""
    shard = tmp_path / "0000000009.parquet"
    shard.write_bytes(b"x")
    processor = _EdgarFileProcessor(_keys(), freq="Y", cikToTicker={}, isInstant=False)

    with pytest.raises(EdgarScanMappingError):
        processor(shard)


def testResultFromLongPivotsPeriodsDescending() -> None:
    """기간 열은 최신이 앞에 오도록 정렬된다."""
    long = pl.DataFrame(
        {
            "fileCik": ["0000000001", "0000000001"],
            "period": ["2023", "2024"],
            "amount": [1.0, 2.0],
        }
    )

    out = _resultFromLong(long, {"0000000001": "AAA"}, {"AAA": "Alpha Inc"})

    periods = [c for c in out.columns if c not in ("stockCode", "corpName")]
    assert periods == sorted(periods, reverse=True)


def testResultFromLongEmptyKeepsStockCodeSchema() -> None:
    """빈 입력도 stockCode 스키마를 유지해 소비자가 분기하지 않게 한다."""
    out = _resultFromLong(pl.DataFrame({"fileCik": [], "period": [], "amount": []}), {}, {})

    assert "stockCode" in out.columns
