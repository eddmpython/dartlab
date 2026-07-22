"""Queryable asset 하나를 격리 프로세스에서 실제 물질화한다."""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import dartlab
from dartlab.data import DataQuery, DataRequest, QueryBudget, ResourceProjection

_GATHER_SUBJECTS = {
    "calendar": "005930",
    "dartDoc": "20160330003535",
    "flow": "005930",
    "insider": "005930",
    "krx": "close",
    "krxIndex": "close",
    "macro": "CPI",
    "narrative": "score",
    "naverEtf": "KODEX",
    "naverEtn": "원유",
    "naverIndustry": "반도체",
    "naverTheme": "2차전지",
    "news": "삼성전자",
    "ownership": "005930",
    "peers": "005930",
    "price": "005930",
    "sector": "005930",
}

_SCAN_MEASURES = {
    "account": "sales",
    "note": "inventory",
    "ratio": "roe",
}


def _request(asset) -> DataRequest:
    axis = asset.executorAxis or ""
    subjects: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()
    params: dict[str, Any] = {}
    projection = ResourceProjection() if asset.executorKind == "resource" else None

    if asset.owner in {"analysis", "credit", "quant"}:
        subjects = ("005930",)
    elif asset.owner == "gather" and asset.executorKind == "engineAxis":
        subjects = (_GATHER_SUBJECTS.get(axis, "005930"),)
    elif asset.owner == "industry":
        subjects = ("secondaryBattery" if axis == "theme" else "semiconductor",)
    elif asset.owner == "macro":
        if axis == "scenario":
            subjects = ("2008 금융위기",)
        params = {"market": "US"}
    elif asset.owner == "scan" and asset.executorKind == "engineAxis":
        if axis in _SCAN_MEASURES:
            measures = (_SCAN_MEASURES[axis],)
        elif axis == "macroBeta":
            params = {"stockCode": "005930"}

    return DataRequest(
        asset.assetId,
        requestId=asset.assetId,
        projection=projection,
        subjects=subjects,
        measures=measures,
        params=params,
    )


def audit(assetId: str, *, timeoutMs: int = 15_000) -> dict[str, Any]:
    catalog = dartlab.data("catalog")
    asset = next(item for item in catalog.assets if item.assetId == assetId)
    started = time.perf_counter()
    result = dartlab.data(
        "query",
        query=DataQuery(
            requests=(_request(asset),),
            budget=QueryBudget(maxRows=5, maxBytes=1024 * 1024, timeoutMs=timeoutMs, maxAssets=1),
        ),
    )
    return {
        "assetId": assetId,
        "owner": asset.owner,
        "layer": asset.layer,
        "executorKind": asset.executorKind,
        "status": result.status,
        "elapsedMs": round((time.perf_counter() - started) * 1000, 3),
        "partitionCount": len(result.partitions),
        "rowCount": sum(partition.rowCount for partition in result.partitions),
        "truncated": any(partition.truncated for partition in result.partitions),
        "gapCodes": [gap.code for gap in result.gaps],
        "gapMessages": [gap.message[:500] for gap in result.gaps],
        "schemas": [list(partition.schema) for partition in result.partitions],
    }


if __name__ == "__main__":
    try:
        workerTimeoutMs = int(sys.argv[2]) if len(sys.argv) > 2 else 15_000
        print(json.dumps(audit(sys.argv[1], timeoutMs=workerTimeoutMs), ensure_ascii=False, separators=(",", ":")))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "assetId": sys.argv[1] if len(sys.argv) > 1 else None,
                    "status": "workerFailed",
                    "error": f"{type(exc).__name__}: {exc}",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        raise
