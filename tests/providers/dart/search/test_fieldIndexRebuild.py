"""mirror smoke — dart/search/fieldIndexRebuild.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    import dartlab.providers.dart.search.fieldIndexRebuild as mod

    assert mod is not None


def test_write_index_manifest_callable() -> None:
    from dartlab.providers.dart.search.fieldIndexRebuild import writeIndexManifest

    assert callable(writeIndexManifest)


def test_manifest_meta_read_is_streamed_and_canary_text_is_bounded(tmp_path, monkeypatch) -> None:
    import polars as pl

    from dartlab.providers.dart.search.fieldIndexRebuild import _readManifestMeta

    path = tmp_path / "main_meta.parquet"
    pl.DataFrame(
        {
            "source": ["allFilings"],
            "text": ["긴 본문" * 1000],
            "evidenceText": ["더 긴 증거 본문" * 1000],
        }
    ).write_parquet(path)

    def _eagerReadForbidden(*args, **kwargs):
        raise AssertionError("manifest generation must not eagerly read segment metadata")

    monkeypatch.setattr(pl, "read_parquet", _eagerReadForbidden)
    meta = _readManifestMeta(path)

    assert meta.columns == ["source", "text"]
    assert len(meta.item(0, "text")) == 120


def test_rebuild_main_from_catalog_callable() -> None:
    from dartlab.providers.dart.search.fieldIndexRebuild import rebuildMainFromCatalog

    assert callable(rebuildMainFromCatalog)


def test_write_index_manifest_includes_artifact_canary_pack(tmp_path) -> None:
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar, writeIndexManifest

    idx, meta = buildContentSegment(
        [
            {
                "section_content": "유상증자 자금조달 계획",
                "rcept_no": "20260615000001",
                "section_order": 0,
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "rcept_dt": "20260615",
                "report_nm": "주요사항보고서",
                "section_title": "",
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20260615000001#section=0",
            }
        ],
        showProgress=False,
    )
    saveSegmentWithSidecar(idx, meta, "main", tmp_path)
    (tmp_path / "source_manifest_set.json").write_text(
        json.dumps(
            {
                "schemaVersion": "searchSourceManifestSet.v1",
                "sourceManifestSetId": "abc123",
                "expectedSources": ["allFilings"],
                "combinedCatalogRows": 1,
                "combinedCatalogSha256": "hash",
                "sources": [
                    {
                        "source": "allFilings",
                        "dataAsOf": "20260615",
                        "snapshotScope": "full",
                        "totalRows": 1,
                        "catalogRows": 1,
                        "manifestSha256": "manifest-hash",
                        "catalogSha256": "catalog-hash",
                        "producer": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    import polars as pl

    pl.DataFrame(
        [
            {
                "corpName": "삼성전자",
                "stockCode": "005930",
                "grade": "AA",
                "weakAxis": "inventory",
                "dataAsOf": "20260616",
                "neighborsJson": "[]",
            }
        ]
    ).write_parquet(tmp_path / "entityGraphCatalog.parquet")
    pl.DataFrame(
        [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20260615000001#section=0",
                "text": "유상증자",
            }
        ]
    ).write_parquet(tmp_path / "catalog_snapshot.parquet")

    manifest = writeIndexManifest(tmp_path, tier="full", buildCommand="test")

    assert manifest["canaryPackVersion"] == "artifact-source-v3"
    assert manifest["sourceCanaryPack"][0]["expectedSource"] == "allFilings"
    assert manifest["sourceCanaryPack"][0]["expectedSourceRef"] == "dart:allFilings:20260615000001#section=0"
    assert manifest["sourceCanaryPack"][-1]["target"] == "noAnswer"
    assert "catalog_snapshot.parquet" in manifest["requiredFiles"]
    assert "catalog_snapshot.parquet" in manifest["fileHashes"]
    assert "source_manifest_set.json" in manifest["requiredFiles"]
    assert "source_manifest_set.json" in manifest["fileHashes"]
    assert manifest["sourceManifestSetId"] == "abc123"
    assert manifest["sourceManifestSet"]["sources"][0]["source"] == "allFilings"
    assert "entityGraphCatalog.parquet" in manifest["requiredFiles"]
    assert "entityGraphCatalog.parquet" in manifest["fileHashes"]
    assert manifest["entityGraphCatalog"]["schemaVersion"] == "searchEntityGraphCatalog.v1"
    assert manifest["entityGraphCatalog"]["nEntities"] == 1
    assert manifest["entityGraphCatalog"]["stockCodeCount"] == 1
    assert manifest["entityGraphCatalog"]["dataAsOf"] == "20260616"


def test_edgar_period_to_data_as_of_uses_quarter_end() -> None:
    from dartlab.providers.dart.search.freshness import periodToDataAsOf

    assert periodToDataAsOf("2025Q4") == "20251231"
    assert periodToDataAsOf("2026Q1") == "20260331"
    assert periodToDataAsOf("bad") == ""
