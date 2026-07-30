"""network runtime과 계열회사 prebuild 계약 회귀."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from random import Random

import polars as pl
import pyarrow.parquet as pq
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _legalIdentityProfile(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.scan.builders.kr import network as builder

    monkeypatch.setattr(
        builder,
        "_loadJurirStockMap",
        lambda: {"1234561234567": "000002"},
    )


def test_scan_invested_keeps_each_company_latest_period(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.scan.network import scanner

    raw = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A", "B"],
            "year": ["2023", "2024", "2024", "2022"],
            "quarter": ["4분기", "1분기", "3분기", "4분기"],
            "inv_prm": ["old", "early", "latest", "only"],
        }
    )
    monkeypatch.setattr(scanner, "scanParquets", lambda *_args, **_kwargs: raw)

    result = scanner.scanInvested()

    assert set(result["stockCode"]) == {"A", "B"}
    assert result.filter(pl.col("stockCode") == "A")["inv_prm"].to_list() == ["latest"]
    assert result.filter(pl.col("stockCode") == "B")["inv_prm"].to_list() == ["only"]


def test_deduplicate_edges_keeps_company_specific_latest_year() -> None:
    from dartlab.scan.network.edges import deduplicateEdges

    edges = pl.DataFrame(
        {
            "from_code": ["A", "A", "B"],
            "from_name": ["A", "A", "B"],
            "to_name": ["old", "new", "only"],
            "to_name_norm": ["old", "new", "only"],
            "to_code": ["X", "Y", "Z"],
            "is_listed": [True, True, True],
            "ownership_pct": [10.0, 20.0, 30.0],
            "book_value": [1.0, 2.0, 3.0],
            "purpose": ["기타", "기타", "기타"],
            "year": ["2023", "2024", "2022"],
        }
    )

    result = deduplicateEdges(edges)

    assert set(result["from_code"]) == {"A", "B"}
    assert result.filter(pl.col("from_code") == "A")["year"].to_list() == ["2024"]
    assert result.filter(pl.col("from_code") == "B")["year"].to_list() == ["2022"]


def test_compile_affiliate_groups_uses_inverted_overlap_index() -> None:
    from dartlab.scan.network.affiliates import compileAffiliateGroups

    memberships = pl.DataFrame(
        {
            "sourceStockCode": [
                "R1",
                "R1",
                "R1",
                "R1",
                "R2",
                "R2",
                "R2",
                "R2",
                "R3",
                "R3",
                "R3",
            ],
            "affiliateStockCode": ["R1", "A", "B", "C", "R2", "A", "B", "C", "R3", "A", "B"],
        }
    )
    listingCodes = set(memberships["sourceStockCode"]) | set(memberships["affiliateStockCode"])
    names = {code: code for code in listingCodes}

    groups = compileAffiliateGroups(memberships, names, listingCodes)

    assert set(groups) == {"R1", "R2", "A", "B", "C"}
    assert len(set(groups.values())) == 1
    assert "R3" not in groups


def test_inverted_overlap_matches_pairwise_reference() -> None:
    from dartlab.scan.network.affiliates import compileAffiliateGroups

    rng = Random(20260730)
    sources = [f"S{i:02d}" for i in range(16)]
    affiliates = [f"A{i:02d}" for i in range(24)]
    rows: list[tuple[str, str]] = []
    sourceSets: dict[str, set[str]] = {}
    for source in sources:
        selected = {source, *rng.sample(affiliates, rng.randint(2, 10))}
        sourceSets[source] = selected
        rows.extend((source, affiliate) for affiliate in selected)

    memberships = pl.DataFrame(
        rows,
        schema={"sourceStockCode": pl.Utf8, "affiliateStockCode": pl.Utf8},
        orient="row",
    )
    listingCodes = set(sources) | set(affiliates)
    names = {code: code for code in listingCodes}
    optimized = compileAffiliateGroups(memberships, names, listingCodes)

    parent = {source: source for source in sources}

    def find(code: str) -> str:
        while parent[code] != code:
            parent[code] = parent[parent[code]]
            code = parent[code]
        return code

    def union(left: str, right: str) -> None:
        leftRoot, rightRoot = find(left), find(right)
        if leftRoot != rightRoot:
            parent[rightRoot] = leftRoot

    for index, left in enumerate(sources):
        for right in sources[index + 1 :]:
            if len(sourceSets[left] & sourceSets[right]) >= 3:
                union(left, right)
    referenceSources: dict[str, set[str]] = {}
    for source in sources:
        referenceSources.setdefault(find(source), set()).add(source)
    expected = {
        frozenset(affiliate for source in componentSources for affiliate in sourceSets[source])
        for componentSources in referenceSources.values()
        if len(componentSources) >= 2
    }
    actual = {
        frozenset(code for code, label in optimized.items() if label == groupLabel)
        for groupLabel in set(optimized.values())
    }
    assert actual == expected


def test_compile_affiliate_groups_does_not_vote_on_name_only_cross_group_claims() -> None:
    from dartlab.scan.network.affiliates import compileAffiliateGroups

    memberships = pl.DataFrame(
        {
            "sourceStockCode": [
                "A1",
                "A1",
                "A1",
                "A1",
                "A1",
                "A2",
                "A2",
                "A2",
                "A2",
                "A2",
                "B1",
                "B1",
                "B1",
                "B1",
                "B1",
                "B2",
                "B2",
                "B2",
                "B2",
            ],
            "affiliateStockCode": [
                "A1",
                "AX",
                "AY",
                "AZ",
                "SHARED",
                "A2",
                "AX",
                "AY",
                "AZ",
                "SHARED",
                "B1",
                "BX",
                "BY",
                "BZ",
                "SHARED",
                "B2",
                "BX",
                "BY",
                "BZ",
            ],
        }
    )
    listingCodes = set(memberships["sourceStockCode"]) | set(memberships["affiliateStockCode"])
    names = {code: code for code in listingCodes}

    groups = compileAffiliateGroups(memberships, names, listingCodes)

    assert "SHARED" not in groups
    assert groups["A1"] != groups["B1"]


def test_compile_affiliate_groups_prefers_the_affiliates_own_source_component() -> None:
    from dartlab.scan.network.affiliates import compileAffiliateGroups

    memberships = pl.DataFrame(
        {
            "sourceStockCode": [
                "A1",
                "A1",
                "A1",
                "A1",
                "A2",
                "A2",
                "A2",
                "A2",
                "B1",
                "B1",
                "B1",
                "B1",
                "B2",
                "B2",
                "B2",
                "B2",
                "SHARED",
                "SHARED",
                "SHARED",
                "SHARED",
            ],
            "affiliateStockCode": [
                "A1",
                "AX",
                "AY",
                "SHARED",
                "A2",
                "AX",
                "AY",
                "SHARED",
                "B1",
                "BX",
                "BY",
                "SHARED",
                "B2",
                "BX",
                "BY",
                "SHARED",
                "SHARED",
                "AX",
                "AY",
                "A1",
            ],
        }
    )
    listingCodes = set(memberships["sourceStockCode"]) | set(memberships["affiliateStockCode"])
    names = {code: code for code in listingCodes}

    groups = compileAffiliateGroups(memberships, names, listingCodes)

    assert groups["SHARED"] == groups["A1"]
    assert groups["A1"] != groups["B1"]


def test_compile_affiliate_groups_rejects_component_with_known_label_conflict() -> None:
    from dartlab.scan.network.affiliates import compileAffiliateGroups

    memberships = pl.DataFrame(
        {
            "sourceStockCode": [
                "029780",
                "029780",
                "029780",
                "029780",
                "007160",
                "007160",
                "007160",
                "007160",
            ],
            "affiliateStockCode": [
                "029780",
                "COMMON1",
                "COMMON2",
                "COMMON3",
                "007160",
                "COMMON1",
                "COMMON2",
                "COMMON3",
            ],
        }
    )
    listingCodes = set(memberships["sourceStockCode"]) | set(memberships["affiliateStockCode"])
    names = {code: code for code in listingCodes}

    groups = compileAffiliateGroups(memberships, names, listingCodes)

    assert groups == {}


def test_build_graph_reads_prebuild_not_raw_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab.providers.dart.panel.text as panelText
    import dartlab.scan.network as network

    investEdges = pl.DataFrame(
        {
            "from_code": ["A"],
            "from_name": ["A사"],
            "to_name": ["B사"],
            "to_name_norm": ["B사"],
            "to_code": ["B"],
            "is_listed": [True],
            "ownership_pct": [10.0],
            "book_value": [1.0],
            "purpose": ["경영참여"],
            "year": ["2024"],
        }
    )
    corpEdges = pl.DataFrame(
        {
            "from_code": ["A"],
            "from_name": ["A사"],
            "to_code": ["B"],
            "relate": ["최대주주"],
            "ownership_pct": [20.0],
            "year": ["2024"],
        }
    )
    personEdges = pl.DataFrame(
        schema={
            "person_name": pl.Utf8,
            "to_code": pl.Utf8,
            "relate": pl.Utf8,
            "ownership_pct": pl.Float64,
            "year": pl.Utf8,
        }
    )
    monkeypatch.setattr(panelText, "panelTextRows", lambda *_args, **_kwargs: pytest.fail("raw panel read"))
    monkeypatch.setattr(
        network,
        "loadListing",
        lambda: (
            {"A사": "A", "B사": "B", "C사": "C"},
            {"A": "A사", "B": "B사", "C": "C사"},
            {"A", "B", "C"},
            {},
        ),
    )
    monkeypatch.setattr(network, "scanInvested", lambda: pl.DataFrame())
    monkeypatch.setattr(network, "buildInvestEdges", lambda *_args: investEdges)
    monkeypatch.setattr(network, "deduplicateEdges", lambda frame: frame)
    monkeypatch.setattr(network, "scanMajorHolders", lambda: pl.DataFrame())
    monkeypatch.setattr(network, "buildHolderEdges", lambda *_args: (corpEdges, personEdges))
    monkeypatch.setattr(network, "loadAffiliateGroups", lambda *_args: {"A": "그룹", "B": "그룹", "C": "그룹"})
    monkeypatch.setattr(
        network,
        "classifyBalanced",
        lambda *_args, **_kwargs: {code: "그룹" for code in _args[3]},
    )
    monkeypatch.setattr(network, "detectCycles", lambda *_args, **_kwargs: [])

    result = network.buildGraph(verbose=False)

    assert result["code_to_group"] == {"A": "그룹", "B": "그룹", "C": "그룹"}
    assert result["all_node_ids"] == {"A", "B", "C"}


def _panelFrame(content: str, *, period: str = "2024Q4") -> pl.DataFrame:
    return pl.DataFrame(
        {
            "sectionLeaf": ["계열회사 현황"],
            "contentRaw": [content],
            "period": [period],
            "rceptNo": ["20250319000001"],
        }
    )


def test_affiliate_membership_builder_full_and_incremental(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    output = tmp_path / "scan" / "network" / "affiliateDocs.parquet"
    table = (
        "<TABLE><TR><TH>회사명</TH><TH>법인등록번호</TH></TR><TR><TD>(주)알파</TD><TD>123456-1234567</TD></TR></TABLE>"
    )
    _panelFrame(table).write_parquet(panelDir / "000001.parquet")
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(
        builder,
        "loadListing",
        lambda: ({"알파": "000002"}, {}, {"000001", "000002"}, {}),
    )

    resultPath = builder.buildAffiliateDocs(outputPath=output)
    result = pl.read_parquet(resultPath)
    assert set(result["affiliateStockCode"]) == {"000001", "000002"}

    prior = pl.concat(
        [
            result,
            pl.DataFrame(
                {
                    "sourceStockCode": ["000003", "000004"],
                    "affiliateStockCode": ["000003", "000004"],
                    "sourcePeriod": ["2023Q4", "2023Q4"],
                    "sourceRceptNo": ["20240319000001", "20240319000002"],
                    "groupName": [None, None],
                    "datasetAsOf": ["20240319", "20240319"],
                    "schemaVersion": [builder.AFFILIATE_DOCS_SCHEMA_VERSION] * 2,
                },
                schema=builder._OUTPUT_SCHEMA,
            ),
        ],
        how="vertical_relaxed",
    )
    prior.write_parquet(output)
    pl.DataFrame(
        {
            "sectionLeaf": ["사업의 개요"],
            "contentRaw": ["본문"],
            "period": ["2025Q1"],
            "rceptNo": ["20250515000001"],
        }
    ).write_parquet(panelDir / "000001.parquet")

    builder.buildAffiliateDocs(
        outputPath=output,
        incremental=True,
        changedCodes=["000001"],
    )
    updated = pl.read_parquet(output)
    assert set(updated["sourceStockCode"]) == {"000003", "000004"}

    builder.buildAffiliateDocs(
        outputPath=output,
        incremental=True,
        changedCodes=[],
        removedCodes=["000003"],
    )
    pruned = pl.read_parquet(output)
    assert set(pruned["sourceStockCode"]) == {"000004"}
    assert "000003" not in pruned["affiliateStockCode"].to_list()


def test_affiliate_membership_missing_changed_source_preserves_prior(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    output = tmp_path / "affiliateDocs.parquet"
    pl.DataFrame(
        {
            "sourceStockCode": ["000001"],
            "affiliateStockCode": ["000001"],
            "sourcePeriod": ["2024Q4"],
            "sourceRceptNo": ["20250319000001"],
            "groupName": [None],
            "datasetAsOf": ["20250319"],
            "schemaVersion": [builder.AFFILIATE_DOCS_SCHEMA_VERSION],
        },
        schema=builder._OUTPUT_SCHEMA,
    ).write_parquet(output)
    priorBytes = output.read_bytes()
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(builder, "loadListing", lambda: ({}, {}, {"000001"}, {}))

    with pytest.raises(FileNotFoundError, match="변경 panel source 누락"):
        builder.buildAffiliateDocs(
            outputPath=output,
            incremental=True,
            changedCodes=["000001"],
        )

    assert output.read_bytes() == priorBytes


def test_affiliate_membership_rejects_noncanonical_prior_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder
    from dartlab.scan.io.parquet import ScanDataError

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    output = tmp_path / "affiliateDocs.parquet"
    pl.DataFrame(
        {
            "sourceStockCode": ["000001"],
            "affiliateStockCode": ["000001"],
            "sourcePeriod": ["2024Q4"],
            "sourceRceptNo": ["20250319000001"],
            "groupName": ["그룹"],
            "datasetAsOf": ["20250319"],
            "schemaVersion": [1],
        }
    ).write_parquet(output)
    priorBytes = output.read_bytes()
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(builder, "loadListing", lambda: ({}, {}, {"000001"}, {}))

    with pytest.raises(ScanDataError, match="dtype mismatch"):
        builder.buildAffiliateDocs(
            outputPath=output,
            incremental=True,
            changedCodes=[],
        )

    assert output.read_bytes() == priorBytes


@pytest.mark.parametrize("mode", ["full", "changed-to-empty", "removed-last"])
def test_affiliate_membership_publishes_valid_empty_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
) -> None:
    from dartlab.scan.builders.kr import network as builder
    from dartlab.scan.network import affiliates

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    output = tmp_path / "affiliateDocs.parquet"
    emptyPanel = pl.DataFrame(
        {
            "sectionLeaf": ["사업의 개요"],
            "contentRaw": ["본문"],
            "period": ["2025Q1"],
            "rceptNo": ["20250515000001"],
        }
    )
    if mode != "removed-last":
        emptyPanel.write_parquet(panelDir / "000001.parquet")
    if mode != "full":
        pl.DataFrame(
            {
                "sourceStockCode": ["000001"],
                "affiliateStockCode": ["000001"],
                "sourcePeriod": ["2024Q4"],
                "sourceRceptNo": ["20250319000001"],
                "groupName": [None],
                "datasetAsOf": ["20250319"],
                "schemaVersion": [builder.AFFILIATE_DOCS_SCHEMA_VERSION],
            },
            schema=builder._OUTPUT_SCHEMA,
        ).write_parquet(output)

    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(builder, "loadListing", lambda: ({}, {}, {"000001"}, {}))
    if mode == "changed-to-empty":
        resultPath = builder.buildAffiliateDocs(
            outputPath=output,
            incremental=True,
            changedCodes=["000001"],
        )
    elif mode == "removed-last":
        resultPath = builder.buildAffiliateDocs(
            outputPath=output,
            incremental=True,
            changedCodes=[],
            removedCodes=["000001"],
        )
    else:
        resultPath = builder.buildAffiliateDocs(outputPath=output)
    result = pl.read_parquet(resultPath)
    monkeypatch.setattr(affiliates, "ensureScanArtifact", lambda _path: resultPath)

    assert result.is_empty()
    assert result.schema == builder._OUTPUT_SCHEMA
    assert affiliates.loadAffiliateGroups() == {}


def test_affiliate_membership_uses_latest_revision_with_a_table(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    table = (
        "<TABLE><TR><TH>회사명</TH><TH>법인등록번호</TH></TR><TR><TD>(주)알파</TD><TD>123456-1234567</TD></TR></TABLE>"
    )
    omitted = "<TABLE><TR><TD>분기보고서의 본 항목은 기재를 생략합니다.</TD></TR></TABLE>"
    pl.DataFrame(
        {
            "sectionLeaf": ["계열회사 현황", "계열회사 현황"],
            "contentRaw": [table, omitted],
            "period": ["2023Q4", "2024Q1"],
            "rceptNo": ["20240319000001", "20240515000001"],
        }
    ).write_parquet(panelDir / "000001.parquet", row_group_size=1)
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(
        builder,
        "loadListing",
        lambda: ({"알파": "000002"}, {}, {"000001", "000002"}, {}),
    )

    output = builder.buildAffiliateDocs(outputPath=tmp_path / "affiliateDocs.parquet")
    result = pl.read_parquet(output)

    assert set(result["affiliateStockCode"]) == {"000001", "000002"}
    assert result["sourcePeriod"].unique().to_list() == ["2023Q4"]


def test_affiliate_membership_rejects_name_only_listing_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    table = "<TABLE><TR><TH>투자회사</TH></TR><TR><TD>알파</TD></TR></TABLE>"
    _panelFrame(table).write_parquet(panelDir / "000001.parquet")
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(
        builder,
        "loadListing",
        lambda: ({"알파": "000002"}, {}, {"000001", "000002"}, {}),
    )

    output = builder.buildAffiliateDocs(outputPath=tmp_path / "affiliateDocs.parquet")

    assert set(pl.read_parquet(output)["affiliateStockCode"]) == {"000001"}


def test_affiliate_membership_rejects_same_name_with_different_legal_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    table = (
        "<TABLE><TR><TH>회사명</TH><TH>법인등록번호</TH></TR><TR><TD>(주)알파</TD><TD>999999-9999999</TD></TR></TABLE>"
    )
    _panelFrame(table).write_parquet(panelDir / "000001.parquet")
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(
        builder,
        "loadListing",
        lambda: ({"알파": "000002"}, {}, {"000001", "000002"}, {}),
    )

    output = builder.buildAffiliateDocs(outputPath=tmp_path / "affiliateDocs.parquet")

    assert set(pl.read_parquet(output)["affiliateStockCode"]) == {"000001"}


def test_affiliate_identity_does_not_read_receipt_number_as_legal_id() -> None:
    from dartlab.scan.builders.kr import network as builder

    resolved, unknownLegal, nameOnly, nameMismatch, hasCandidates = builder._resolveTableAffiliates(
        [[["알파", "20250319000001"]]],
        {"알파": "000002"},
        {"2025031900000": "000002"},
    )

    assert resolved == set()
    assert (unknownLegal, nameOnly, nameMismatch, hasCandidates) == (0, 1, 0, True)


def test_affiliate_identity_rejects_unicode_digit_lookalikes() -> None:
    from dartlab.scan.builders.kr import network as builder

    resolved, unknownLegal, nameOnly, nameMismatch, hasCandidates = builder._resolveTableAffiliates(
        [
            [
                ["회사", "１２３４５６-１２３４５６７"],
                ["회사", "١٢٣٤٥٦-١٢٣٤٥٦٧"],
                ["회사", "１123456-1234567"],
                ["회사", "123456-1234567١"],
            ]
        ],
        {},
        {"1234561234567": "005930"},
    )

    assert resolved == set()
    assert (unknownLegal, nameOnly, nameMismatch, hasCandidates) == (0, 0, 0, False)


def test_affiliate_membership_builder_preserves_corrupt_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    pl.DataFrame({"wrong": [1]}).write_parquet(panelDir / "000001.parquet")
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(builder, "loadListing", lambda: ({}, {}, set(), {}))

    output = tmp_path / "out.parquet"
    output.write_bytes(b"existing")
    with pytest.raises(builder.AffiliateDocsBuildError, match="000001"):
        builder.buildAffiliateDocs(outputPath=output)
    assert output.read_bytes() == b"existing"


def test_affiliate_membership_atomic_writer_preserves_prior_and_cleans_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    output = tmp_path / "affiliateDocs.parquet"
    output.write_bytes(b"prior")
    frame = pl.DataFrame(schema=builder._OUTPUT_SCHEMA)

    def failWrite(_self, _path, **_kwargs) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(pl.DataFrame, "write_parquet", failWrite)

    with pytest.raises(OSError, match="disk full"):
        builder._writeAtomic(frame, output)

    assert output.read_bytes() == b"prior"
    assert list(tmp_path.glob("*.tmp.parquet")) == []


def test_affiliate_membership_builder_streams_legacy_large_row_group(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    table = (
        "<TABLE><TR><TH>회사명</TH><TH>법인등록번호</TH></TR><TR><TD>(주)알파</TD><TD>123456-1234567</TD></TR></TABLE>"
    )
    pl.DataFrame(
        {
            "sectionLeaf": ["계열회사 현황"] * 4097,
            "contentRaw": [table, *(["<P>본문</P>"] * 4096)],
            "period": ["2024Q4"] * 4097,
            "rceptNo": ["20250319000001"] * 4097,
        }
    ).write_parquet(panelDir / "000001.parquet")
    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(
        builder,
        "loadListing",
        lambda: ({"알파": "000002"}, {}, {"000001", "000002"}, {}),
    )

    output = builder.buildAffiliateDocs(outputPath=tmp_path / "affiliateDocs.parquet")

    assert set(pl.read_parquet(output)["affiliateStockCode"]) == {"000001", "000002"}


def test_legacy_dictionary_reader_preserves_selected_rows_and_nulls(tmp_path: Path) -> None:
    from dartlab.scan.builders.kr import network as builder

    source = tmp_path / "legacy.parquet"
    contents = ["<P>첫째</P>", None, "<P>셋째</P>"]
    frame = pl.DataFrame(
        {
            "sectionLeaf": ["계열회사"] * 3,
            "contentRaw": contents,
            "period": ["2024Q4"] * 3,
            "rceptNo": ["20250319000001"] * 3,
        }
    )
    pq.write_table(
        frame.to_arrow(),
        source,
        compression="zstd",
        use_dictionary=True,
    )

    parquet = pq.ParquetFile(source, memory_map=False, pre_buffer=False)
    try:
        selected = builder._readDictionarySelectedContents(source, parquet, {0, 1, 2})
    finally:
        parquet.close()

    assert selected == {0: contents[0], 2: contents[2]}


def test_bounded_arrow_fallback_supports_non_dictionary_data_page_v2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    source = tmp_path / "page-v2.parquet"
    contents = [f"<P>{index}</P>" for index in range(40)]
    frame = pl.DataFrame(
        {
            "sectionLeaf": ["계열회사"] * len(contents),
            "contentRaw": contents,
            "period": ["2024Q4"] * len(contents),
            "rceptNo": ["20250319000001"] * len(contents),
        }
    )
    pq.write_table(
        frame.to_arrow(),
        source,
        compression="zstd",
        use_dictionary=False,
        data_page_version="2.0",
        data_page_size=64,
        write_batch_size=8,
        row_group_size=8,
    )
    monkeypatch.setattr(builder, "_MAX_ARROW_CONTENT_BYTES", 0)
    selectedIndexes = set(range(24, 32))

    parquet = pq.ParquetFile(source, memory_map=False, pre_buffer=False)
    try:
        selected = builder._readSelectedContents(source, parquet, selectedIndexes)
    finally:
        parquet.close()

    assert selected == {index: contents[index] for index in selectedIndexes}


def test_dictionary_multi_page_uses_bounded_arrow_fallback(tmp_path: Path) -> None:
    from dartlab.scan.builders.kr import network as builder

    source = tmp_path / "multi-page.parquet"
    contents = [f"<P>{index}-{'x' * 100}</P>" for index in range(1_000)]
    frame = pl.DataFrame(
        {
            "sectionLeaf": ["계열회사"] * len(contents),
            "contentRaw": contents,
            "period": ["2024Q4"] * len(contents),
            "rceptNo": ["20250319000001"] * len(contents),
        }
    )
    pq.write_table(
        frame.to_arrow(),
        source,
        compression="zstd",
        use_dictionary=True,
        data_page_size=64,
        write_batch_size=8,
    )
    selectedIndexes = set(range(len(contents)))

    parquet = pq.ParquetFile(source, memory_map=False, pre_buffer=False)
    try:
        with pytest.raises(builder._UnsupportedContentLayout, match="단일 zstd frame"):
            builder._readDictionarySelectedContents(source, parquet, selectedIndexes)
        selected = builder._readSelectedContents(source, parquet, selectedIndexes)
    finally:
        parquet.close()

    assert selected == dict(enumerate(contents))


def test_oversized_unsupported_layout_uses_serial_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    source = tmp_path / "000001.parquet"
    _panelFrame("<TABLE><TR><TD>본문</TD></TR></TABLE>").write_parquet(source)
    monkeypatch.setattr(builder, "_MAX_ARROW_CONTENT_BYTES", 0)

    def rejectLayout(*_args: object) -> dict[int, str]:
        raise builder._UnsupportedContentLayout("multi-page")

    monkeypatch.setattr(builder, "_readDictionarySelectedContents", rejectLayout)

    parquet = pq.ParquetFile(source, memory_map=False, pre_buffer=False)
    try:
        selected = builder._readSelectedContents(source, parquet, {0})
    finally:
        parquet.close()

    assert selected == {0: "<TABLE><TR><TD>본문</TD></TR></TABLE>"}


def test_oversized_fallback_failure_preserves_company_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    source = tmp_path / "000001.parquet"
    _panelFrame("<TABLE><TR><TD>본문</TD></TR></TABLE>").write_parquet(source)
    monkeypatch.setattr(builder, "_MAX_ARROW_CONTENT_BYTES", 0)

    def rejectLayout(*_args: object) -> dict[int, str]:
        raise builder._UnsupportedContentLayout("multi-page")

    def failFallback(*_args: object) -> dict[int, str]:
        raise ValueError("fallback failed")

    monkeypatch.setattr(builder, "_readDictionarySelectedContents", rejectLayout)
    monkeypatch.setattr(builder, "_readSelectedContentsDuckDb", failFallback)

    with pytest.raises(builder.AffiliateDocsBuildError, match=r"code=000001.*fallback failed") as caught:
        builder._readAffiliateRows(source, "000001", {}, {})

    assert isinstance(caught.value.__cause__, ValueError)


def test_dictionary_length_bomb_is_rejected_before_value_read(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder
    from dartlab.scan.builders.kr import parquetContent

    source = tmp_path / "legacy.parquet"
    _panelFrame("<P>본문</P>").write_parquet(source)
    monkeypatch.setattr(
        parquetContent,
        "_readExact",
        lambda _stream, size, _label: b"\xff" * size,
    )

    parquet = pq.ParquetFile(source, memory_map=False, pre_buffer=False)
    try:
        with pytest.raises(ValueError, match="크기가 비정상"):
            builder._readDictionarySelectedContents(source, parquet, {0})
    finally:
        parquet.close()


def test_affiliate_membership_builder_limits_company_parallelism(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.builders.kr import network as builder

    panelDir = tmp_path / "panel"
    panelDir.mkdir()
    for code in ("000001", "000002", "000003", "000004"):
        (panelDir / f"{code}.parquet").write_bytes(b"source")

    active = 0
    maxActive = 0
    lock = threading.Lock()

    def readSource(
        _source: Path,
        code: str,
        _nameToCode: dict[str, str],
        _jurirToCode: dict[str, str],
    ) -> builder._AffiliateReadResult:
        nonlocal active, maxActive
        with lock:
            active += 1
            maxActive = max(maxActive, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return builder._AffiliateReadResult(frozenset({(code, code, "2024Q4", f"20250319{code}")}))

    monkeypatch.setattr(builder, "panelDir", lambda: panelDir)
    monkeypatch.setattr(
        builder,
        "loadListing",
        lambda: ({}, {}, {"000001", "000002", "000003", "000004"}, {}),
    )
    monkeypatch.setattr(builder, "_readAffiliateRows", readSource)

    output = builder.buildAffiliateDocs(outputPath=tmp_path / "affiliateDocs.parquet")

    assert pl.read_parquet(output).height == 4
    assert maxActive == 2


def test_affiliate_docs_runtime_rejects_conflicting_groups(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from dartlab.scan.network import affiliates

    artifact = tmp_path / "affiliateDocs.parquet"
    pl.DataFrame(
        {
            "sourceStockCode": ["A", "B"],
            "affiliateStockCode": ["X", "X"],
            "sourcePeriod": ["2024Q4", "2024Q4"],
            "sourceRceptNo": ["1", "2"],
            "groupName": ["G1", "G2"],
            "datasetAsOf": ["2024", "2024"],
            "schemaVersion": [affiliates.AFFILIATE_DOCS_SCHEMA_VERSION] * 2,
        },
        schema=affiliates.AFFILIATE_DOCS_SCHEMA,
    ).write_parquet(artifact)
    monkeypatch.setattr(affiliates, "ensureScanArtifact", lambda _path: artifact)

    with pytest.raises(affiliates.ScanDataError, match="conflicting groups"):
        affiliates.loadAffiliateGroups()


def test_legacy_affiliate_scanner_delegates_to_prebuild(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.scan.network import affiliates, scanner

    monkeypatch.setattr(affiliates, "loadAffiliateGroups", lambda: {"005930": "삼성"})

    assert scanner.scanAffiliateDocs({}, {}) == {"005930": "삼성"}
