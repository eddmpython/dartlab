"""providers/dart/search/sourceCatalog.py mirror tests."""

from __future__ import annotations

import json

import polars as pl


def test_source_catalog_writes_manifest_and_snapshot(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    source = tmp_path / "all.parquet"
    pl.DataFrame(
        [
            {
                "rcept_no": "20260615000001",
                "rcept_dt": "20260615",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "report_nm": "주요사항보고서",
                "content_raw": "유상증자 결정",
            }
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts(
        "allFilings",
        [source],
        outDir=tmp_path / "out",
        producerRun={
            "system": "githubActions",
            "workflow": "Original SSOT Sync",
            "job": "allfilings",
            "runId": "123",
            "sha": "abc",
            "artifactName": "search-catalog-allFilings-allfilings-123",
        },
    )
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    assert manifest["source"] == "allFilings"
    assert manifest["snapshotScope"] == "full"
    assert manifest["totalRows"] == 1
    assert manifest["producerRun"]["artifactName"] == "search-catalog-allFilings-allfilings-123"
    assert manifest["completenessCheck"]["valid"] is True
    catalog = pl.read_parquet(result["catalog"])
    assert catalog.row(0, named=True)["sourceRef"] == "dart:allFilings:20260615000001#section=0"


def test_discover_source_files_glob(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import discoverSourceFiles

    (tmp_path / "a.parquet").write_bytes(b"not real parquet")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    files = discoverSourceFiles([str(tmp_path / "*.parquet")])
    assert [path.name for path in files] == ["a.parquet"]


def test_edgar_source_catalog_uses_filing_date_for_freshness(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    source = tmp_path / "AAPL.parquet"
    pl.DataFrame(
        [
            {
                "rceptNo": "0001090872-15-000032",
                "filing_date": "2015-04-28",
                "ticker": "AAPL",
                "period": "2015Q1",
                "sectionLeaf": "10-Q",
                "contentRaw": "revenue increased due to semiconductor demand",
            }
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts("edgarPanel", [source], outDir=tmp_path / "out")
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    assert manifest["dataAsOf"] == "20150428"
    catalog = pl.read_parquet(result["catalog"])
    row = catalog.row(0, named=True)
    assert row["source"] == "edgarPanel"
    assert row["sourceDataAsOf"] == "20150428"
    assert row["sourceRef"] == "edgar:panel:0001090872-15-000032#section=0"


def test_edgar_source_catalog_uses_period_for_freshness_when_date_missing(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    source = tmp_path / "AACB.parquet"
    pl.DataFrame(
        [
            {
                "rceptNo": "0001140361-26-010274",
                "corp": "AACB",
                "period": "2025Q4",
                "sectionLeaf": "10-K",
                "contentRaw": "UNITED STATES SECURITIES AND EXCHANGE COMMISSION FORM 10-K",
            }
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts("edgarPanel", [source], outDir=tmp_path / "out")
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    assert manifest["dataAsOf"] == "20251231"
    catalog = pl.read_parquet(result["catalog"])
    row = catalog.row(0, named=True)
    assert row["date"] == "20251231"
    assert row["sourceDataAsOf"] == "20251231"
    assert row["title"] == "10-K"
    assert row["searchText"] == "UNITED STATES SECURITIES AND EXCHANGE COMMISSION FORM 10-K"


def test_panel_source_catalog_rolls_blocks_to_filing_rows(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    source = tmp_path / "005930.parquet"
    pl.DataFrame(
        [
            {
                "rceptNo": "20260330001234",
                "corp": "005930",
                "period": "2025Q4",
                "sectionLeaf": "사업의 내용",
                "blockOrder": 0,
                "contentRaw": "<p>HBM 투자 확대</p>",
            },
            {
                "rceptNo": "20260330001234",
                "corp": "005930",
                "period": "2025Q4",
                "sectionLeaf": "사업의 내용",
                "blockOrder": 1,
                "contentRaw": "<p>반도체 생산능력 증가</p>",
            },
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts("dartPanel", [source], outDir=tmp_path / "out")
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    catalog = pl.read_parquet(result["catalog"])
    row = catalog.row(0, named=True)

    assert manifest["rawRows"] == 2
    assert manifest["totalRows"] == 1
    assert manifest["dataAsOf"] == "20260330"
    assert manifest["completenessCheck"]["catalogRows"] == 1
    assert catalog.height == 1
    assert row["sourceRef"] == "dart:panel:20260330001234#section=0"
    assert row["date"] == "20260330"
    assert row["stockCode"] == "005930"
    assert "HBM 투자 확대" in row["searchText"]
    assert "반도체 생산능력 증가" in row["searchText"]


def test_allfilings_source_catalog_dedupes_doc_key_with_latest_file_first(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    old = tmp_path / "20260614.parquet"
    new = tmp_path / "20260615.parquet"
    pl.DataFrame(
        [
            {
                "rcept_no": "20260615000001",
                "rcept_dt": "20260614",
                "corp_name": "삼성전자",
                "content_raw": "old text",
            }
        ]
    ).write_parquet(old)
    pl.DataFrame(
        [
            {
                "rcept_no": "20260615000001",
                "rcept_dt": "20260615",
                "corp_name": "삼성전자",
                "content_raw": "<p>new text</p>",
            }
        ]
    ).write_parquet(new)

    result = writeSourceCatalogArtifacts("allFilings", [old, new], outDir=tmp_path / "out")
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    catalog = pl.read_parquet(result["catalog"])

    assert manifest["rawRows"] == 2
    assert manifest["totalRows"] == 1
    assert manifest["completenessCheck"]["catalogRows"] == 1
    assert catalog.height == 1
    assert catalog.row(0, named=True)["searchText"] == "new text"


def test_allfilings_source_catalog_skips_latest_failed_empty_duplicate(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    old = tmp_path / "20260614.parquet"
    new = tmp_path / "20260615.parquet"
    pl.DataFrame(
        [
            {
                "rcept_no": "20260615000001",
                "rcept_dt": "20260614",
                "corp_name": "삼성전자",
                "content_raw": "old ok text",
                "fetch_status": "ok",
            }
        ]
    ).write_parquet(old)
    pl.DataFrame(
        [
            {
                "rcept_no": "20260615000001",
                "rcept_dt": "20260615",
                "corp_name": "삼성전자",
                "content_raw": "",
                "fetch_status": "error",
            }
        ]
    ).write_parquet(new)

    result = writeSourceCatalogArtifacts("allFilings", [old, new], outDir=tmp_path / "out")
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    catalog = pl.read_parquet(result["catalog"])

    assert manifest["rawRows"] == 2
    assert manifest["totalRows"] == 1
    assert catalog.height == 1
    assert catalog.row(0, named=True)["searchText"] == "old ok text"


def test_source_catalog_completeness_blocks_empty_full_snapshot() -> None:
    from dartlab.providers.dart.search.sourceCatalog import validateSourceCatalogCompleteness

    report = validateSourceCatalogCompleteness(
        {"source": "allFilings", "snapshotScope": "full", "files": [], "totalRows": 0},
        catalogRows=0,
        minFiles=1,
        minRows=1,
        minCatalogRows=1,
    )

    assert report["valid"] is False
    assert report["errors"] == [
        "emptyFullSnapshot:files",
        "emptyFullSnapshot:rows",
        "emptyFullSnapshot:catalogRows",
        "minFiles:0/1",
        "minRows:0/1",
        "minCatalogRows:0/1",
    ]


def test_source_catalog_completeness_blocks_previous_full_drop() -> None:
    from dartlab.providers.dart.search.sourceCatalog import validateSourceCatalogCompleteness

    previous = {
        "source": "dartPanel",
        "snapshotScope": "full",
        "dataAsOf": "20260615",
        "files": [{"path": f"{idx}.parquet", "rowCount": 10} for idx in range(100)],
        "totalRows": 1000,
        "completenessCheck": {"catalogRows": 1000},
    }

    report = validateSourceCatalogCompleteness(
        {
            "source": "dartPanel",
            "snapshotScope": "full",
            "files": [{"path": f"{idx}.parquet", "rowCount": 10} for idx in range(3)],
            "totalRows": 30,
        },
        catalogRows=30,
        previousManifest=previous,
        maxFileDropRatio=0.05,
        maxRowDropRatio=0.05,
        maxCatalogRowDropRatio=0.05,
    )

    assert report["valid"] is False
    assert "previousFileDrop:3/100:maxDrop=0.05" in report["errors"]
    assert "previousRowDrop:30/1000:maxDrop=0.05" in report["errors"]
    assert "previousCatalogRowDrop:30/1000:maxDrop=0.05" in report["errors"]
    assert report["previous"]["fileCount"] == 100


def test_source_catalog_completeness_allows_small_previous_full_drop() -> None:
    from dartlab.providers.dart.search.sourceCatalog import validateSourceCatalogCompleteness

    previous = {
        "source": "newsPublic",
        "snapshotScope": "full",
        "files": [{"path": f"{idx}.parquet", "rowCount": 1} for idx in range(100)],
        "totalRows": 100,
        "completenessCheck": {"catalogRows": 100},
    }

    report = validateSourceCatalogCompleteness(
        {
            "source": "newsPublic",
            "snapshotScope": "full",
            "files": [{"path": f"{idx}.parquet", "rowCount": 1} for idx in range(98)],
            "totalRows": 98,
        },
        catalogRows=98,
        previousManifest=previous,
        maxFileDropRatio=0.05,
        maxRowDropRatio=0.05,
        maxCatalogRowDropRatio=0.05,
    )

    assert report["valid"] is True
    assert report["previous"]["catalogRows"] == 100
