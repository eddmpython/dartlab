"""EDGAR coverage 감사 하네스 회귀.

로컬 EDGAR parquet 없이 도는 부분만 본다. 전종목 실행은 운영자 명령이지 CI 게이트가
아니다. 여기서 지키는 것은 universe 고정, 실패 분류, envelope 계약 셋이다.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from tests.audit.edgarCoverageAudit import (
    LoaderAccessError,
    NetworkAccessError,
    _digestFile,
    _loadUniverse,
    classifyError,
    validateEnvelope,
)


def _envelope(*, signalIds: tuple[str, ...], entityId: str = "US:AAA") -> dict[str, object]:
    return {
        "schemaVersion": "feature-observation-input-v1",
        "specs": tuple({"signalId": item} for item in signalIds),
        "observations": tuple(
            {
                "signalId": item,
                "entityId": entityId,
                "eventAt": "20260630",
                "availableAt": "20260723",
                "revisionId": "rev-1",
            }
            for item in signalIds
        ),
    }


def testLoadUniverseMatchesProductionListedFilter(tmp_path: Path) -> None:
    """OTC 를 빼고 ticker 를 대문자로 세운 뒤 중복을 접는다. 순서는 ticker 오름차순이다."""

    path = tmp_path / "listedUniverse.parquet"
    pl.DataFrame(
        {
            "cik": ["1", "2", "3", "4"],
            "ticker": ["bbb", "AAA", "OTC1", "AAA"],
            "title": ["B", "A", "O", "duplicate"],
            "exchange": ["NYSE", "Nasdaq", "OTC", "Nasdaq"],
            "is_exchange_listed": [True, True, False, True],
            "is_otc": [False, False, True, False],
        }
    ).write_parquet(path)

    entities = _loadUniverse(path)

    assert tuple(item.ticker for item in entities) == ("AAA", "BBB")
    assert tuple(item.cik for item in entities) == ("0000000002", "0000000001")


def testLoadUniverseRejectsListingMissingRequiredColumn(tmp_path: Path) -> None:
    """listing schema 가 모자라면 조용히 좁혀진 universe 를 재지 않고 실패한다."""

    path = tmp_path / "listedUniverse.parquet"
    pl.DataFrame({"cik": ["1"], "ticker": ["AAA"]}).write_parquet(path)

    with pytest.raises(ValueError, match="필수 columns"):
        _loadUniverse(path)


def testClassifyErrorKeepsPitAndFeatureFailuresSeparate() -> None:
    """PIT cutoff, flow window, 원천 schema 실패가 한 통에 섞이지 않는다."""

    assert (
        classifyError(ValueError("no periodic EDGAR facts are available by knowledgeAsOf"))
        == "PIT_NO_FILING_BEFORE_CUTOFF"
    )
    assert (
        classifyError(ValueError("four common standalone revenue quarters are required"))
        == "FEATURE_NO_COHERENT_FOUR_QUARTER_WINDOW"
    )
    assert classifyError(ValueError("EDGAR facts missing columns: ['tag']")) == "SOURCE_SCHEMA_MISSING"
    assert classifyError(ValueError("balance identity check failed")) == ("FEATURE_BALANCE_IDENTITY_FAILED")


def testClassifyErrorSurfacesGuardBreachesAsTheirOwnCodes() -> None:
    """loader 나 network 접근 시도는 feature 실패로 위장되지 않는다."""

    assert classifyError(LoaderAccessError("blocked")) == "LOADER_ACCESS_ATTEMPT"
    assert classifyError(NetworkAccessError("blocked")) == "NETWORK_ACCESS_ATTEMPT"


def testValidateEnvelopeRequiresExactRequestedMeasures() -> None:
    """measure 를 지정하면 owner 는 그 signal 만 그 순서로 돌려줘야 한다."""

    measures = ("financial.revenue", "financial.operatingMargin")
    count, eventAt, availableAt = validateEnvelope(
        _envelope(signalIds=measures),
        ticker="AAA",
        measures=measures,
    )
    assert (count, eventAt, availableAt) == (2, "20260630", "20260723")

    with pytest.raises(ValueError, match="요청한 measure"):
        validateEnvelope(
            _envelope(signalIds=("financial.operatingMargin", "financial.revenue")),
            ticker="AAA",
            measures=measures,
        )


def testValidateEnvelopeAcceptsOwnerChosenSetWhenNoMeasureRequested() -> None:
    """full-state 실행은 owner 가 고르는 집합을 그대로 받는다."""

    count, _eventAt, _availableAt = validateEnvelope(
        _envelope(signalIds=("financial.revenue", "financial.totalAssets")),
        ticker="AAA",
        measures=(),
    )
    assert count == 2


def testValidateEnvelopeRejectsMultiRevisionObservations() -> None:
    """한 회사 결과가 두 revision 에 걸치면 성공으로 세지 않는다."""

    envelope = _envelope(signalIds=("financial.revenue", "financial.operatingMargin"))
    observations = list(envelope["observations"])  # type: ignore[arg-type]
    observations[1] = {**observations[1], "revisionId": "rev-2"}  # type: ignore[index]
    envelope["observations"] = tuple(observations)

    with pytest.raises(ValueError, match="하나의 revision"):
        validateEnvelope(envelope, ticker="AAA", measures=())


def testValidateEnvelopeRejectsEntityIdentityMismatch() -> None:
    """다른 회사 결과가 섞여 들어오면 즉시 실패한다."""

    with pytest.raises(ValueError, match="entity identity"):
        validateEnvelope(
            _envelope(signalIds=("financial.revenue",), entityId="US:BBB"),
            ticker="AAA",
            measures=(),
        )


def testDigestFileReturnsExactBytesIdentity(tmp_path: Path) -> None:
    """원천 무결성 증명은 파일 전체 bytes 의 SHA-256 이다."""

    path = tmp_path / "source.parquet"
    path.write_bytes(b"exact-source")

    digest, size = _digestFile(path)

    assert digest == "5c9c784359cfb0585ad3b4708aef518720b26a516a71d59337f21ff488584346"
    assert size == 12
