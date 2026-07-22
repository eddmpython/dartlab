"""JSON-friendly 외부 호출과 EngineCall 경로 검증."""

from __future__ import annotations

import polars as pl


def testJsonMappingQueryBuildsTypedFactorProjection(monkeypatch):
    import dartlab

    monkeypatch.setattr(
        dartlab,
        "scan",
        lambda *args, **kwargs: pl.DataFrame({"종목코드": ["005930"], "종목명": ["삼성전자"], "2025": [12.0]}),
    )
    result = dartlab.data(
        "query",
        "scan.ratio",
        query={
            "projection": {
                "kind": "factor",
                "measures": ["roe"],
                "unit": "percent",
                "frequency": "Y",
            }
        },
    )

    assert result.status == "ok"
    assert result.partitions[0].projectionKind == "factor"
    assert result.partitions[0].data["measureId"].to_list() == ["roe"]


def testEngineCallCanReachDataCatalogWithJsonArgs():
    from dartlab.ai.tools.engineCall import engineCall

    result = engineCall(
        {
            "apiRef": "data",
            "args": {
                "axis": "catalog",
                "query": {"owners": ["scan"], "search": "ratio"},
            },
        }
    )

    assert result.ok
    payload = result.data["result"]
    assert any(asset["assetId"] == "scan.ratio" for asset in payload["assets"])
