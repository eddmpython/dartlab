from __future__ import annotations

import json

import buildLensProducts as subject
import polars as pl


def _bundle(target: str) -> dict:
    return {
        "schemaVersion": 1,
        "target": target,
        "market": "KR",
        "engines": [],
        "products": {},
        "statusCounts": {},
        "gaps": [],
        "noComposite": True,
    }


def test_shard_codes_is_complete_disjoint_and_stable():
    codes = ["000004", "000001", "000003", "000002", "000001"]
    shards = [subject.shardCodes(codes, shardIndex=index, shardCount=3) for index in range(3)]

    assert sorted(code for shard in shards for code in shard) == ["000001", "000002", "000003", "000004"]
    assert all(set(shards[left]).isdisjoint(shards[right]) for left in range(3) for right in range(left + 1, 3))
    assert subject.shardCodes(codes, shardIndex=1, shardCount=3) == shards[1]


def test_all_codes_consumes_public_korean_scan_contract(monkeypatch):
    import dartlab

    frames = {
        "debt": pl.DataFrame({"종목코드": ["000002", "000001"]}),
        "valuation": pl.DataFrame({"종목코드": ["000003", "000002"]}),
    }
    monkeypatch.setattr(dartlab, "scan", lambda axis: frames[axis])

    assert subject._allCodes() == ["000001", "000002", "000003"]


def test_merge_manifests_requires_and_preserves_full_coverage(tmp_path):
    targets = ["000001", "000002", "000003"]
    rows = [
        {
            "schemaVersion": 1,
            "requested": 2,
            "covered": 2,
            "published": 1,
            "shardIndex": 0,
            "shardCount": 2,
            "companies": [{"target": "000001", "productCount": 5, "path": "000001.json"}],
            "failures": [{"target": "000003", "error": "blocked", "path": "000003.json"}],
            "noComposite": True,
        },
        {
            "schemaVersion": 1,
            "requested": 1,
            "covered": 1,
            "published": 1,
            "shardIndex": 1,
            "shardCount": 2,
            "companies": [{"target": "000002", "productCount": 4, "path": "000002.json"}],
            "failures": [],
            "noComposite": True,
        },
    ]
    for index, row in enumerate(rows):
        (tmp_path / f"_shard-{index:02d}.json").write_text(json.dumps(row), encoding="utf-8")
    for target in targets:
        (tmp_path / f"{target}.json").write_text(json.dumps(_bundle(target)), encoding="utf-8")

    merged = subject.mergeManifests(tmp_path, expectedShards=2)

    assert merged["requested"] == merged["covered"] == 3
    assert merged["published"] == 2
    assert merged["coverageRate"] == 1.0
    assert not list(tmp_path.glob("_shard-*.json"))
    assert json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))["noComposite"] is True
