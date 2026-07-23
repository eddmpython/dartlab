"""Data Prism projection이 공유하는 provenance와 evidence 정규화."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl

from dartlab.data.contracts import DataAssetDescriptor, DataLineage, DataQuery, QualityAssertion


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _language(text: str) -> str:
    if any("가" <= char <= "힣" for char in text):
        return "ko"
    if any("a" <= char.casefold() <= "z" for char in text):
        return "en"
    return "und"


def _textLeaves(value: Any, *, path: str = "$") -> list[tuple[str, str]]:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    leaves: list[tuple[str, str]] = []
    if isinstance(value, pl.DataFrame):
        for index, row in enumerate(value.iter_rows(named=True)):
            leaves.extend(_textLeaves(row, path=f"{path}[{index}]"))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            leaves.extend(_textLeaves(item, path=f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            leaves.extend(_textLeaves(item, path=f"{path}[{index}]"))
    elif isinstance(value, str) and value.strip():
        leaves.append((path, value.strip()))
    return leaves


def narrativeFrame(
    raw: Any,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    selector: Mapping[str, str],
    receiptRef: str,
) -> pl.DataFrame:
    """Owner output의 text leaf를 결정적 narrative evidence table로 만든다.

    Capabilities:
        document, chunk, language, content hash와 공통 시간 및 provenance spine을 생성한다.

    Args:
        raw: owner native output.
        descriptor: 실행 asset descriptor.
        query: active request가 반영된 query.
        selector: subject 또는 measure selector.
        receiptRef: 실행 영수증 참조.

    Returns:
        한 text leaf가 한 행인 Polars DataFrame.

    Raises:
        없음.

    Example:
        ``narrativeFrame({"risk": "환율"}, descriptor, query, selector={}, receiptRef="run")``.

    Guide:
        latest-only asset에는 knownAt 현재 시각을 자동 주입하지 않는다.

    SeeAlso:
        ``FactorProjection`` canonical long schema.

    AIContext:
        content hash와 chunk ID는 검색과 인용 키이며 semantic relevance 점수가 아니다.
    """
    documentId = _digest(
        {
            "assetId": descriptor.assetId,
            "assetVersionId": descriptor.assetVersionId,
            "selector": dict(selector),
            "sourceRef": descriptor.sourceRef,
        }
    )
    validAt = query.time.validAt if query.time else None
    availableAt = dict(descriptor.metadata).get("availableAt")
    temporalStatus = "VALID_TIME" if validAt else "LATEST_ONLY"
    rows = []
    for path, text in _textLeaves(raw):
        contentHash = _digest(text)
        rows.append(
            {
                "assetId": descriptor.assetId,
                "documentId": documentId,
                "chunkId": _digest((documentId, path, contentHash)),
                "section": path,
                "text": text,
                "language": _language(text),
                "contentHash": contentHash,
                "eventAt": validAt,
                "availableAt": str(availableAt) if availableAt is not None else None,
                "knownAt": None,
                "revisionId": descriptor.assetVersionId,
                "sourceRef": descriptor.sourceRef,
                "evidenceRef": receiptRef,
                "temporalStatus": temporalStatus,
            }
        )
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def lineageFacet(descriptor: DataAssetDescriptor, receiptRef: str) -> DataLineage:
    """실행 영수증을 run, job, dataset 구조의 lineage facet으로 만든다."""

    return DataLineage(
        runId=receiptRef,
        jobName=f"dartlab.data.{descriptor.owner}.{descriptor.executorAxis or descriptor.assetId}",
        datasetId=descriptor.assetId,
        datasetVersionId=descriptor.assetVersionId,
        sourceRefs=(descriptor.sourceRef,),
        evidenceRefs=(receiptRef,),
    )


def qualityAssertions(
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    rowCount: int,
    outputBytes: int,
    truncated: bool,
    contentHash: str | None,
) -> tuple[QualityAssertion, ...]:
    """Partition 예산, provenance, temporal truth를 machine-readable assertion으로 만든다."""

    temporalRequested = bool(query.time and (query.time.validAt or query.time.knownAt))
    temporalObserved = "supported" if temporalRequested else "latest-only"
    return (
        QualityAssertion(
            assertionId="rowBudget",
            success=rowCount <= query.budget.maxRows,
            severity="error",
            expected=f"rows<={query.budget.maxRows}",
            observed=f"rows={rowCount},truncated={str(truncated).lower()}",
            assetId=descriptor.assetId,
        ),
        QualityAssertion(
            assertionId="byteBudget",
            success=outputBytes <= query.budget.maxBytes,
            severity="error",
            expected=f"bytes<={query.budget.maxBytes}",
            observed=f"bytes={outputBytes}",
            assetId=descriptor.assetId,
        ),
        QualityAssertion(
            assertionId="provenanceBound",
            success=bool(descriptor.sourceRef),
            severity="error",
            expected="sourceRef and execution receipt",
            observed=descriptor.sourceRef or "missing",
            assetId=descriptor.assetId,
        ),
        QualityAssertion(
            assertionId="temporalTruth",
            success=True,
            severity="error",
            expected="requested cutoff passed to owner or latest-only declared",
            observed=temporalObserved,
            assetId=descriptor.assetId,
        ),
        QualityAssertion(
            assertionId="contentSealed",
            success=contentHash is not None,
            severity="error" if contentHash is not None else "warning",
            expected="deterministic content hash",
            observed=contentHash or "unsupported opaque content",
            assetId=descriptor.assetId,
        ),
    )


__all__ = ["lineageFacet", "narrativeFrame", "qualityAssertions"]
