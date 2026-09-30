"""providers/dart/search/sourceCatalogMerge.py mirror tests."""

from __future__ import annotations

import json

import polars as pl
import pytest


def test_merged_news_source_catalog_upserts_urls_without_dropping_same_article_date(tmp_path) -> None:
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows
    from dartlab.providers.dart.search.sourceCatalogMerge import writeMergedSourceCatalogArtifacts

    changed = tmp_path / "2026-06-16.parquet"
    keepPath = tmp_path / "2026-06-15.parquet"
    previousCatalog = tmp_path / "previous.catalog_snapshot.parquet"
    pl.DataFrame(
        [
            {
                "url": "https://n.example/new",
                "date": "20260616",
                "title": "새 뉴스",
                "content": "유상증자 새 기사",
            }
        ]
    ).write_parquet(changed)
    normalizeCatalogRows(
        [
            {
                "source": "newsPublic",
                "url": "https://n.example/new",
                "date": "20260616",
                "title": "이전 같은 URL",
                "content": "같은 URL의 이전 내용",
            },
            {
                "source": "newsPublic",
                "url": "https://n.example/old",
                "date": "20260616",
                "title": "이전 뉴스",
                "content": "오늘 수집에 다시 안 보이지만 forward archive 에서는 보존",
            },
            {
                "source": "newsPublic",
                "url": "https://n.example/keep",
                "date": "20260615",
                "title": "보존 뉴스",
                "content": "다른 날짜는 보존",
            },
        ]
    ).write_parquet(previousCatalog)
    previousManifest = {
        "source": "newsPublic",
        "snapshotScope": "full",
        "dataAsOf": "20260616",
        "files": [
            {"path": keepPath.as_posix(), "rowCount": 1, "maxDate": "20260615"},
            {"path": changed.as_posix(), "rowCount": 2, "maxDate": "20260616"},
        ],
        "totalRows": 3,
        "completenessCheck": {"catalogRows": 3},
    }

    result = writeMergedSourceCatalogArtifacts(
        "newsPublic",
        [changed],
        previousCatalog=previousCatalog,
        previousManifest=previousManifest,
        outDir=tmp_path / "out",
        minFiles=2,
        minRows=3,
        minCatalogRows=3,
    )

    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    catalog = pl.read_parquet(result["catalog"])
    urls = set(catalog.get_column("url").to_list())
    texts = set(catalog.get_column("searchText").to_list())
    assert manifest["snapshotScope"] == "full"
    assert manifest["deltaSource"]["catalogRows"] == 1
    assert manifest["completenessCheck"]["valid"] is True
    assert urls == {"https://n.example/new", "https://n.example/old", "https://n.example/keep"}
    assert "유상증자 새 기사" in texts
    assert "같은 URL의 이전 내용" not in texts


def test_merged_panel_source_catalog_replaces_changed_company_partition(tmp_path) -> None:
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows
    from dartlab.providers.dart.search.sourceCatalogMerge import writeMergedSourceCatalogArtifacts

    changed = tmp_path / "005930.parquet"
    keepPath = tmp_path / "000660.parquet"
    previousCatalog = tmp_path / "previous.catalog_snapshot.parquet"
    pl.DataFrame(
        [
            {
                "rceptNo": "20260330009999",
                "corp": "삼성전자",
                "period": "2025Q4",
                "sectionLeaf": "사업의 내용",
                "contentRaw": "HBM 신규 투자",
            }
        ]
    ).write_parquet(changed)
    normalizeCatalogRows(
        [
            {
                "source": "dartPanel",
                "rceptNo": "20250330001111",
                "stockCode": "005930",
                "date": "20250330",
                "contentRaw": "이전 삼성전자 행",
            },
            {
                "source": "dartPanel",
                "rceptNo": "20250330002222",
                "stockCode": "000660",
                "date": "20250330",
                "contentRaw": "SK하이닉스 행",
            },
        ]
    ).write_parquet(previousCatalog)
    previousManifest = {
        "source": "dartPanel",
        "snapshotScope": "full",
        "dataAsOf": "20261231",
        "files": [
            {"path": keepPath.as_posix(), "rowCount": 1, "maxDate": "20250330"},
            {"path": changed.as_posix(), "rowCount": 1, "maxDate": "20261231"},
        ],
        "totalRows": 2,
        "completenessCheck": {"catalogRows": 2},
    }

    result = writeMergedSourceCatalogArtifacts(
        "dartPanel",
        [changed],
        previousCatalog=previousCatalog,
        previousManifest=previousManifest,
        outDir=tmp_path / "out",
        minFiles=2,
        minRows=2,
        minCatalogRows=2,
    )

    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    catalog = pl.read_parquet(result["catalog"])
    rows = catalog.select(["stockCode", "sourceRef", "searchText"]).to_dicts()
    assert manifest["dataAsOf"] == "20260330"
    assert {row["stockCode"] for row in rows} == {"005930", "000660"}
    assert any(row["sourceRef"] == "dart:panel:20260330009999#section=0" for row in rows)
    assert all(row["sourceRef"] != "dart:panel:20250330001111#section=0" for row in rows)


def test_merged_allfilings_source_catalog_upserts_changed_filings(tmp_path) -> None:
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows
    from dartlab.providers.dart.search.sourceCatalogMerge import writeMergedSourceCatalogArtifacts

    changed = tmp_path / "2026-06-17.parquet"
    keepPath = tmp_path / "2026-06-15.parquet"
    previousCatalog = tmp_path / "previous.catalog_snapshot.parquet"
    pl.DataFrame(
        [
            {
                "rcept_no": "20260617000001",
                "rcept_dt": "20260617",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "report_nm": "주요사항보고서",
                "content_raw": "전환사채 발행 조건 변경 새 원문",
                "fetch_status": "ok",
            }
        ]
    ).write_parquet(changed)
    normalizeCatalogRows(
        [
            {
                "source": "allFilings",
                "rcept_no": "20260617000001",
                "rcept_dt": "20260617",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "report_nm": "주요사항보고서",
                "content_raw": "이전 전환사채 원문",
            },
            {
                "source": "allFilings",
                "rcept_no": "20260615000002",
                "rcept_dt": "20260615",
                "corp_name": "SK하이닉스",
                "stock_code": "000660",
                "report_nm": "사업보고서",
                "content_raw": "보존할 공시 원문",
            },
        ]
    ).write_parquet(previousCatalog)
    previousManifest = {
        "source": "allFilings",
        "snapshotScope": "full",
        "dataAsOf": "20260617",
        "files": [
            {"path": keepPath.as_posix(), "rowCount": 1, "maxDate": "20260615"},
            {"path": changed.as_posix(), "rowCount": 1, "maxDate": "20260617"},
        ],
        "totalRows": 2,
        "completenessCheck": {"catalogRows": 2},
    }

    result = writeMergedSourceCatalogArtifacts(
        "allFilings",
        [changed],
        previousCatalog=previousCatalog,
        previousManifest=previousManifest,
        outDir=tmp_path / "out",
        minFiles=2,
        minRows=2,
        minCatalogRows=2,
    )

    catalog = pl.read_parquet(result["catalog"])
    texts = set(catalog.get_column("searchText").to_list())
    assert "전환사채 발행 조건 변경 새 원문" in texts
    assert "보존할 공시 원문" in texts
    assert "이전 전환사채 원문" not in texts


def test_merged_edgar_source_catalog_replaces_changed_ticker_partition(tmp_path) -> None:
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows
    from dartlab.providers.dart.search.sourceCatalogMerge import writeMergedSourceCatalogArtifacts

    changed = tmp_path / "AAPL.parquet"
    keepPath = tmp_path / "MSFT.parquet"
    previousCatalog = tmp_path / "previous.catalog_snapshot.parquet"
    pl.DataFrame(
        [
            {
                "rceptNo": "0000320193-26-000001",
                "period": "2026Q1",
                "contentRaw": "Apple supply chain investment disclosure",
                "sectionLeaf": "Risk Factors",
                "corp": "Apple Inc.",
            }
        ]
    ).write_parquet(changed)
    normalizeCatalogRows(
        [
            {
                "source": "edgarPanel",
                "accession": "0000320193-25-000001",
                "rceptNo": "0000320193-25-000001",
                "ticker": "AAPL",
                "date": "20250330",
                "contentRaw": "old Apple disclosure",
            },
            {
                "source": "edgarPanel",
                "accession": "0000789019-25-000001",
                "rceptNo": "0000789019-25-000001",
                "ticker": "MSFT",
                "date": "20250330",
                "contentRaw": "Microsoft disclosure",
            },
        ]
    ).write_parquet(previousCatalog)
    previousManifest = {
        "source": "edgarPanel",
        "snapshotScope": "full",
        "dataAsOf": "20260330",
        "files": [
            {"path": keepPath.as_posix(), "rowCount": 1, "maxDate": "20250330"},
            {"path": changed.as_posix(), "rowCount": 1, "maxDate": "20260330"},
        ],
        "totalRows": 2,
        "completenessCheck": {"catalogRows": 2},
    }

    result = writeMergedSourceCatalogArtifacts(
        "edgarPanel",
        [changed],
        previousCatalog=previousCatalog,
        previousManifest=previousManifest,
        outDir=tmp_path / "out",
        minFiles=2,
        minRows=2,
        minCatalogRows=2,
    )

    catalog = pl.read_parquet(result["catalog"])
    rows = catalog.select(["ticker", "sourceRef", "searchText"]).to_dicts()
    assert {row["ticker"] for row in rows} == {"AAPL", "MSFT"}
    assert any(row["sourceRef"] == "edgar:panel:0000320193-26-000001#section=0" for row in rows)
    assert all(row["sourceRef"] != "edgar:panel:0000320193-25-000001#section=0" for row in rows)


def test_panelManifestUsesStablePathsAndPublishedByteDigest(tmp_path):
    import hashlib

    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts
    from dartlab.providers.dart.search.sourceCatalogMerge import writeMergedSourceCatalogArtifacts

    old = tmp_path / "old" / "005930.parquet"
    changed = tmp_path / "another-run" / "005930.parquet"
    old.parent.mkdir()
    changed.parent.mkdir()
    pl.DataFrame({"rceptNo": ["20260515002181"], "contentRaw": ["1분기 원문"]}).write_parquet(old)
    previous = writeSourceCatalogArtifacts("dartPanel", [old], outDir=tmp_path / "before")
    manifest = json.loads(previous["manifest"].read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = "data/dart/panel/005930.parquet"
    pl.DataFrame(
        {"rceptNo": ["20260515002181", "20260814003699"], "contentRaw": ["1분기 원문", "반기 원문"]}
    ).write_parquet(changed)
    result = writeMergedSourceCatalogArtifacts(
        "dartPanel",
        [changed],
        previousCatalog=previous["catalog"],
        previousManifest=manifest,
        outDir=tmp_path / "after",
    )
    current = json.loads(result["manifest"].read_text(encoding="utf-8"))
    assert len(current["files"]) == 1
    assert current["files"][0]["path"] == "dart/panel/005930.parquet"
    assert current["files"][0]["sha256"] == hashlib.sha256(changed.read_bytes()).hexdigest()
    assert set(pl.read_parquet(result["catalog"])["rceptNo"]) == {"20260515002181", "20260814003699"}


def test_panelCatalogDoesNotAcknowledgeUnreadableSource(tmp_path):
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    path = tmp_path / "005930.parquet"
    pl.DataFrame({"unrelated": ["not a panel"]}).write_parquet(path)
    with pytest.raises(ValueError, match="source schema invalid"):
        writeSourceCatalogArtifacts("dartPanel", [path], outDir=tmp_path / "out")
    assert not (tmp_path / "out" / "dartPanel.source_manifest.json").exists()
