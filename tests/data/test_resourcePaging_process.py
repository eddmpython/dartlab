"""Public resource workbench restart and committed replay integration tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

pytestmark = pytest.mark.integration

_CHILD = r"""
import json
import sys

import dartlab

token = sys.stdin.read().strip()
if token:
    query = {"continuation": token}
else:
    query = {
        "requests": [
            {
                "assetId": "resource.finance",
                "requestId": "dartAll",
                "params": {"columns": ["companyId", "value"]},
            },
            {
                "assetId": "resource.edgar",
                "requestId": "edgarAll",
                "params": {"columns": ["cik", "valueUsd"]},
            },
        ],
        "budget": {
            "maxRows": 2,
            "maxBytes": 1048576,
            "maxAssets": 8,
            "timeoutMs": 120000,
        },
    }
result = dartlab.data("query", query=query)
print(json.dumps({
    "status": result.status,
    "continuation": result.continuation,
    "partitions": {
        partition.requestId: partition.data.to_dicts()
        for partition in result.partitions
    },
    "coverage": {
        item.requestId: {
            "market": item.market,
            "provider": item.provider,
            "matched": item.matchedEntities,
            "missing": item.missingEntities,
            "status": item.status,
        }
        for item in result.universeCoverage
    },
    "receipts": list(result.executionReceipts),
}, ensure_ascii=False, sort_keys=True))
"""


def _writeShard(path: Path, table: pa.Table) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _runChild(env: dict[str, str], token: str = "") -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", _CHILD],
        input=token,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        timeout=180,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def testOnePublicCallPagesDartAndEdgarAcrossProcessRestarts(tmp_path: Path) -> None:
    dataRoot = tmp_path / "data"
    dartRoot = dataRoot / "dart" / "finance"
    edgarRoot = dataRoot / "edgar" / "finance"
    for index, companyId in enumerate(("K1", "K2")):
        _writeShard(
            dartRoot / f"{companyId}.parquet",
            pa.table({"companyId": [companyId], "value": [index + 1]}),
        )
    for index, cik in enumerate((10, 20)):
        _writeShard(
            edgarRoot / f"{cik}.parquet",
            pa.table({"cik": [cik], "valueUsd": [index + 1.5]}),
        )

    env = os.environ.copy()
    env["DARTLAB_DATA_DIR"] = str(dataRoot)
    env["DARTLAB_HOME"] = str(tmp_path / "dartlab-home")

    first = _runChild(env)
    assert first["status"] == "partial"
    assert isinstance(first["continuation"], str)
    assert first["partitions"] == {
        "dartAll": [{"companyId": "K1", "sourcePath": "K1.parquet", "value": 1}],
        "edgarAll": [{"cik": 10, "sourcePath": "10.parquet", "valueUsd": 1.5}],
    }

    second = _runChild(env, str(first["continuation"]))
    assert second["status"] == "ok"
    assert second["continuation"] is None
    assert second["partitions"] == {
        "dartAll": [{"companyId": "K2", "sourcePath": "K2.parquet", "value": 2}],
        "edgarAll": [{"cik": 20, "sourcePath": "20.parquet", "valueUsd": 2.5}],
    }
    assert second["coverage"] == {
        "dartAll": {
            "market": "KR",
            "provider": "dart",
            "matched": 2,
            "missing": 0,
            "status": "complete",
        },
        "edgarAll": {
            "market": "US",
            "provider": "edgar",
            "matched": 2,
            "missing": 0,
            "status": "complete",
        },
    }

    dartRoot.rename(dartRoot.with_name("finance-offline"))
    edgarRoot.rename(edgarRoot.with_name("finance-offline"))
    replay = _runChild(env, str(first["continuation"]))

    assert replay == second
