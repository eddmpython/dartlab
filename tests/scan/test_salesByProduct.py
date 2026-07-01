"""scanSalesByProduct 런타임 reader 테스트.

임시 parquet + monkeypatch 로 read 경로를 결정적으로 검증한다 (네트워크·베이크 불요).
"""

from __future__ import annotations

import polars as pl

import dartlab.scan.salesByProduct as sbp
from dartlab.scan.salesByProduct import _SBP_READ_SCHEMA, scanSalesByProduct


def test_reads_prebuilt_parquet(tmp_path, monkeypatch):
    df = pl.DataFrame(
        {
            "stockCode": ["005930", "009540"],
            "period": ["2025Q4", "2024Q4"],
            "nSegments": [4, 5],
            "topSegment": ["DX부문", "조선"],
            "topSharePct": [51.7, 86.4],
            "hhi": [0.4037, 0.7554],
            "grade": ["주력집중", "집중"],
            "topSegmentTrend": [-1.4, 3.3],
            "segments": ["DX부문:52%", "조선:86%"],
            "source": ["panel:salesOrder", "panel:salesOrder"],
        },
        schema_overrides=_SBP_READ_SCHEMA,
    )
    df.write_parquet(str(tmp_path / "salesByProduct.parquet"))
    monkeypatch.setattr(sbp, "_ensureScanData", lambda **_: tmp_path)

    out = scanSalesByProduct()
    assert out.height == 2
    assert set(out.columns) == set(_SBP_READ_SCHEMA)
    assert out.filter(pl.col("stockCode") == "005930")["topSegment"].item() == "DX부문"


def test_missing_file_returns_empty(tmp_path, monkeypatch):
    # 파일 없고 다운로드도 실패하는 경로 -> 빈 프레임 (축 무회귀).
    monkeypatch.setattr(sbp, "_ensureScanData", lambda **_: tmp_path)

    def _boom(scanDir, rel):
        raise RuntimeError("no remote file")

    monkeypatch.setattr(sbp, "_downloadScanFile", _boom)

    out = scanSalesByProduct()
    assert out.height == 0
    assert set(out.columns) == set(_SBP_READ_SCHEMA)
