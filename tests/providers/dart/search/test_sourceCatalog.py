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


def _panelBlock(rceptNo, order, chapter, path, leaf, text, *, leafType="text", period="2025Q4", corp="035720"):
    return {
        "rceptNo": rceptNo,
        "corp": corp,
        "period": period,
        "chapter": chapter,
        "sectionPath": path,
        "sectionLeaf": leaf,
        "leafType": leafType,
        "blockOrder": order,
        "contentRaw": text,
    }


def test_panel_document_leads_with_company_report_business_and_notes(tmp_path) -> None:
    from dartlab.providers.dart.search.semanticConstraints import compileSemanticMapperFromRows
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    sep = chr(0x241F)
    rcept = "20260318001423"
    source = tmp_path / "035720.parquet"
    cover = "사업보고서 감사보고서 연결감사보고서 6.3 6.0 6.0 (주)카카오 주식회사 카카오 C A Y 110111-1129497"
    pl.DataFrame(
        [
            _panelBlock(rcept, 0, "", "", "", f"<p>{cover}</p>"),
            _panelBlock(rcept, 1, "", "", "", "<table>사업연도 2025년 01월 01일</table>", leafType="table"),
            _panelBlock(
                rcept, 2, "I. 회사의 개요", f"I. 회사의 개요{sep}1. 회사의 개요", "1. 회사의 개요", "본점은 제주"
            ),
            _panelBlock(
                rcept,
                3,
                "II. 사업의 내용",
                f"II. 사업의 내용{sep}1. 사업의 개요",
                "1. 사업의 개요",
                "1. 사업의 개요 당사는 카카오톡 플랫폼을 운영합니다",
            ),
            _panelBlock(
                rcept,
                4,
                "III. 재무에 관한 사항",
                f"III. 재무에 관한 사항{sep}3. 연결재무제표 주석",
                "3. 연결재무제표 주석",
                "1. 일반 사항 (1) 회사 개요 2. 리스 (1) 사용권자산 3. 충당부채 (단위: 원)",
            ),
            _panelBlock(
                rcept, 5, "【 대표이사 등의 확인 】", f"【 대표이사 등의 확인 】{sep}확인", "확인", "확인서 서명"
            ),
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts("dartPanel", [source], outDir=tmp_path / "out")
    row = pl.read_parquet(result["catalog"]).row(0, named=True)

    assert row["sourceRef"] == f"dart:panel:{rcept}#section=0"
    assert row["companyName"] == "카카오"
    assert row["reportName"] == "사업보고서 (2025.12)"
    assert row["title"] == "사업보고서 (2025.12)"
    assert row["searchText"].startswith("카카오 사업보고서 (2025.12) [1. 사업의 개요] 당사는 카카오톡")
    assert "주석: 일반 사항, 리스, 충당부채" in row["searchText"][:1500]
    assert row["searchText"].index("주석:") < row["searchText"].index("본점은 제주")
    assert "확인서" not in row["searchText"]
    aliases = compileSemanticMapperFromRows([row]).aliases
    assert "카카오" in aliases
    assert not {"주식회사", "주카카오", "감사보고서"} & set(aliases)


def test_panel_document_keeps_confirmation_only_filing(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    sep = chr(0x241F)
    source = tmp_path / "035720.parquet"
    pl.DataFrame(
        [
            _panelBlock(
                "20240621000676",
                0,
                "【 대표이사 등의 확인 】",
                f"【 대표이사 등의 확인 】{sep}확인",
                "확인",
                "대표이사 등의 확인서명",
                period="2024Q2",
            )
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts("dartPanel", [source], outDir=tmp_path / "out")
    row = pl.read_parquet(result["catalog"]).row(0, named=True)

    assert row["companyName"] == "035720"
    assert row["reportName"] == "반기보고서 (2024.06)"
    assert row["searchText"] == "035720 반기보고서 (2024.06) 대표이사 등의 확인서명"


def test_edgar_panel_document_groups_items_and_reads_note_heads(tmp_path) -> None:
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    sep, dash = chr(0x241F), chr(0x2014)
    rcept = "0000320193-25-000079"
    source = tmp_path / "AAPL.parquet"
    blocks = [
        ("10-K", "10-K", "UNITED STATES SECURITIES AND EXCHANGE COMMISSION FORM 10-K"),
        ("10-K", "Item 1A. Risk Factors", "ITEM 1A. RISK FACTORS Supply chain concentration in Asia"),
        ("10-K", "Item 1A. If Our Goodwill Becomes Impaired", "Item 1A If our goodwill becomes impaired"),
        ("10-K", "Item 7. Management's Discussion", "Net sales grew on iPhone demand"),
        (
            "10-K",
            "Item 8. Financial Statements",
            f"NOTE 1 {dash} ACCOUNTING POLICIES Basis of presentation. Note 2 {dash} Leases Operating leases are",
        ),
    ]
    pl.DataFrame(
        [
            _panelBlock(rcept, order, chapter, f"10-K{sep}{title}", title, text, period="2025Q4", corp="AAPL")
            for order, (chapter, title, text) in enumerate(blocks)
        ]
    ).write_parquet(source)

    result = writeSourceCatalogArtifacts("edgarPanel", [source], outDir=tmp_path / "out")
    row = pl.read_parquet(result["catalog"]).row(0, named=True)

    assert row["sourceRef"] == f"edgar:panel:{rcept}#section=0"
    assert row["companyName"] == "AAPL"
    assert row["reportName"] == "10-K (2025Q4)"
    assert row["searchText"].startswith("AAPL 10-K (2025Q4) [Item 1A. Risk Factors]")
    assert row["searchText"].count("[Item 1A") == 1
    assert "Notes: Accounting Policies, Leases" in row["searchText"]
    assert row["searchText"].index("Notes:") < row["searchText"].index("iPhone")


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
