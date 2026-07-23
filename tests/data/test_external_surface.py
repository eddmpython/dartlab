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


def testEngineCallCanExecuteMixedDataRequests(monkeypatch):
    import dartlab
    from dartlab.ai.tools.engineCall import engineCall

    monkeypatch.setattr(
        dartlab,
        "scan",
        lambda *args, **kwargs: pl.DataFrame({"종목코드": ["005930"], "종목명": ["삼성전자"], "2025": [12.0]}),
    )
    monkeypatch.setattr(
        dartlab,
        "gather",
        lambda *args, **kwargs: {"risk": "수요 둔화 가능성"},
    )

    result = engineCall(
        {
            "apiRef": "data",
            "args": {
                "axis": "query",
                "query": {
                    "requests": [
                        {
                            "assetId": "scan.ratio",
                            "requestId": "factor",
                            "measures": ["roe"],
                            "projection": {"kind": "factor", "measures": ["roe"], "unit": "percent"},
                        },
                        {
                            "assetId": "gather.narrative",
                            "requestId": "evidence",
                            "subjects": ["005930"],
                            "projection": {"kind": "narrative"},
                        },
                    ]
                },
            },
        }
    )

    assert result.ok
    payload = result.data["result"]
    assert payload["status"] == "ok"
    assert [partition["requestId"] for partition in payload["partitions"]] == ["factor", "evidence"]
    assert [partition["projectionKind"] for partition in payload["partitions"]] == ["factor", "narrative"]
    assert [partition["data"]["_type"] for partition in payload["partitions"]] == [
        "DataFrame",
        "DataFrame",
    ]
    assert payload["partitions"][0]["data"]["rows"][0]["measureId"] == "roe"
    assert payload["dataSnapshotId"].startswith("data-content-snapshot:")
