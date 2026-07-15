"""entityIdentityProbe의 canonical ID와 ambiguity 경계를 검증한다."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.identity import (
    AliasRecord,
    canonicalFilingId,
    canonicalLegalEntityId,
    canonicalSecurityId,
    inspectIdentitySources,
    resolveAlias,
)


def _assertLegalEntityIds() -> None:
    assert canonicalLegalEntityId("KR", "00126380") == "kr:dart:corp:00126380"
    assert canonicalLegalEntityId("US", "320193") == "us:sec:cik:0000320193"
    assert canonicalLegalEntityId("US", "0000320193") == "us:sec:cik:0000320193"


def _assertSecurityIds() -> None:
    assert canonicalSecurityId("KR", isin="KR7005930003") == "kr:krx:security:KR7005930003"
    assert canonicalSecurityId("KR", isin="KYG3931T1076") == "kr:krx:security:KYG3931T1076"
    assert canonicalSecurityId("KR", stockCode="005930") == "kr:krx:stock:005930"
    assert canonicalSecurityId("US", ticker="aapl", exchange="Nasdaq") == "us:nasdaq:ticker:AAPL"
    assert canonicalLegalEntityId("US", "320193") != canonicalSecurityId("US", ticker="AAPL", exchange="Nasdaq")


def _assertFilingIds() -> None:
    assert canonicalFilingId("KR", "20260317000632") == "kr:dart:filing:20260317000632"
    dashed = canonicalFilingId("US", "0001193125-09-153165")
    compact = canonicalFilingId("US", "000119312509153165")
    assert dashed == compact == "us:sec:filing:0001193125-09-153165"


def _assertAmbiguousAliasIsNotAutoResolved() -> None:
    records = [
        AliasRecord("Same Name", "kr:dart:corp:00000001", sourceRef="source:1"),
        AliasRecord("same  name", "kr:dart:corp:00000002", sourceRef="source:2"),
    ]
    resolution = resolveAlias(records, "SAME NAME")
    assert resolution.status == "ambiguous"
    assert resolution.selectedId == ""
    assert resolution.matchedIds == (
        "kr:dart:corp:00000001",
        "kr:dart:corp:00000002",
    )


def _assertEntityAndSecurityResolutionDiffer() -> None:
    entityId = "us:sec:cik:0001652044"
    records = [
        AliasRecord(
            "Alphabet Inc.",
            entityId,
            securityId="us:nasdaq:ticker:GOOG",
            sourceRef="source:goog",
        ),
        AliasRecord(
            "Alphabet Inc.",
            entityId,
            securityId="us:nasdaq:ticker:GOOGL",
            sourceRef="source:googl",
        ),
    ]
    entity = resolveAlias(records, "Alphabet Inc.", targetKind="entity")
    security = resolveAlias(records, "Alphabet Inc.", targetKind="security")
    assert entity.status == "resolved"
    assert entity.selectedId == entityId
    assert security.status == "ambiguous"
    assert security.selectedId == ""


def _assertHistoricalValidityFailsClosed() -> None:
    missingValidity = [
        AliasRecord(
            "OLD",
            "us:sec:cik:0000000001",
            securityId="us:nyse:ticker:OLD",
            sourceRef="source:current",
        )
    ]
    unresolved = resolveAlias(missingValidity, "OLD", targetKind="security", validAt="2020-01-01")
    assert unresolved.status == "unresolvedValidity"
    assert unresolved.selectedId == ""

    complete = [
        AliasRecord(
            "RENAMED",
            "us:sec:cik:0000000001",
            securityId="us:nyse:ticker:OLD",
            validFrom="2010-01-01",
            validTo="2020-01-01",
            sourceRef="source:old",
        ),
        AliasRecord(
            "RENAMED",
            "us:sec:cik:0000000001",
            securityId="us:nyse:ticker:NEW",
            validFrom="2020-01-01",
            validTo="2030-01-01",
            sourceRef="source:new",
        ),
    ]
    historical = resolveAlias(complete, "RENAMED", targetKind="security", validAt="2019-12-31")
    current = resolveAlias(complete, "RENAMED", targetKind="security", validAt="2020-01-01")
    assert historical.selectedId == "us:nyse:ticker:OLD"
    assert current.selectedId == "us:nyse:ticker:NEW"


def _assertFuzzyNameIsNotIdentity() -> None:
    records = [AliasRecord("Apple Inc.", "us:sec:cik:0000320193", sourceRef="source:apple")]
    assert resolveAlias(records, "Apple Inc.").status == "resolved"
    assert resolveAlias(records, "Apple").status == "unresolved"


def _assertMalformedIdentifiersFailClosed() -> None:
    with pytest.raises(ValueError, match="8-digit corpCode"):
        canonicalLegalEntityId("KR", "005930")
    with pytest.raises(ValueError, match="ISIN is invalid"):
        canonicalSecurityId("KR", isin="005930")
    with pytest.raises(ValueError, match="14-digit receipt"):
        canonicalFilingId("KR", "20260317")
    with pytest.raises(ValueError, match="valid accession"):
        canonicalFilingId("US", "AAPL-10-K")


def _assertLiveIdentityCensus(repoRoot: Path) -> None:
    census = inspectIdentitySources(
        repoRoot / "data" / "dartList" / "dartList.parquet",
        repoRoot / "data" / "krxList" / "corpList.parquet",
        repoRoot / "data" / "edgar" / "tickers.parquet",
        repoRoot / "data" / "dart" / "finance",
        repoRoot / "data" / "edgar",
    )
    assert census.representative is False
    assert census.krDartRowCount == 115963
    assert census.krListedLegalEntityRowCount == 3959
    assert census.krUniqueCorpCodeCount == 115963
    assert census.krUniqueStockCodeCount == 3959
    assert census.krLegalSampleCount == census.krLegalSampleCanonicalCount == 50
    assert census.krAmbiguousNameCount == 5392
    assert census.krAmbiguousStockCodeCount == 0
    assert census.krHistoricalValidityFieldCount == 0
    assert census.krxSecurityRowCount == census.krxIsinCanonicalCount == 2872
    assert census.krxIssuerLinkCount == 2742
    assert census.krxIssuerGapCount == 130
    assert census.usTickerRowCount == 10436
    assert census.usUniqueCikCount == 8023
    assert census.usUniqueTickerCount == 10436
    assert census.usLegalSampleCount == census.usLegalSampleCanonicalCount == 30
    assert census.usAmbiguousTitleCount == 0
    assert census.usAmbiguousTickerCount == 0
    assert census.usMultiSecurityEntityCount == 1473
    assert census.usHistoricalValidityFieldCount == 0
    assert census.krFilingSourceFileCount == 30
    assert census.krFilingSampleCount == census.krFilingCanonicalCount == 50
    assert census.usFilingSourceFileCount == 2
    assert census.usFilingEntityCount == 2
    assert census.usFilingSampleCount == census.usFilingCanonicalCount == 30
    assert census.exactIdentifierCoverage == 1.0
    assert census.historicalAliasReady is False
    assert census.liveReady is False


def testLegalEntityIds() -> None:
    """CorpCode와 CIK의 deterministic legal entity ID를 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Canonical legal entity builder.

    Raises
        AssertionError: Provider identifier가 다른 canonical ID를 만들 때.
    """

    _assertLegalEntityIds()


def testSecurityIds() -> None:
    """ISIN, stock fallback, exchange ticker security identity 분리를 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Canonical security builder.

    Raises
        AssertionError: Security가 entity와 혼합되거나 정규화가 깨졌을 때.
    """

    _assertSecurityIds()


def testFilingIds() -> None:
    """DART receipt와 SEC accession filing identity를 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Canonical filing builder.

    Raises
        AssertionError: Filing normalization이 provider identity를 바꿀 때.
    """

    _assertFilingIds()


def testAmbiguousAliasIsNotAutoResolved() -> None:
    """같은 alias의 다중 entity를 첫 행으로 자동 해소하지 않음을 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Synthetic duplicate alias records.

    Raises
        AssertionError: Ambiguous alias에 selectedId가 생겼을 때.
    """

    _assertAmbiguousAliasIsNotAutoResolved()


def testEntityAndSecurityResolutionDiffer() -> None:
    """한 issuer의 복수 share class가 entity와 security에서 다르게 해소됨을 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Multi-class US alias fixture.

    Raises
        AssertionError: Entity와 security identity가 같은 방식으로 접힐 때.
    """

    _assertEntityAndSecurityResolutionDiffer()


def testHistoricalValidityFailsClosed() -> None:
    """Validity 결손과 ticker interval 경계를 fail closed로 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Missing과 complete historical alias fixtures.

    Raises
        AssertionError: Historical alias가 validity 없이 해소될 때.
    """

    _assertHistoricalValidityFailsClosed()


def testFuzzyNameIsNotIdentity() -> None:
    """부분 회사명이 exact entity identity로 승격되지 않음을 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Exact company alias fixture.

    Raises
        AssertionError: Partial query가 exact alias로 수용될 때.
    """

    _assertFuzzyNameIsNotIdentity()


def testMalformedIdentifiersFailClosed() -> None:
    """StockCode, malformed ISIN과 filing identifier를 거부하는지 검증한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Canonical ID validation.

    Raises
        AssertionError: Malformed identifier가 조용히 수용될 때.
    """

    _assertMalformedIdentifiersFailClosed()


def testLiveIdentityCensus() -> None:
    """Current KR 50, US 30 exact identity와 historical blocker를 고정한다.

    Example
        ``pytest testEntityIdentityProbe.py``

    Requires
        Local DART, KRX, SEC parquet와 Polars.

    Raises
        AssertionError: Identity source coverage가 drift했을 때.
    """

    _assertLiveIdentityCensus(Path(__file__).resolve().parents[4])
