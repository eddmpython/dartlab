"""Data Prism의 혼합 요청과 narrative evidence spine을 검증하는 순수 attempt."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ViewRequest:
    """Asset별 view override를 담는 attempt contract."""

    assetId: str
    requestId: str
    projection: str
    subjects: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()
    params: Mapping[str, Any] = field(default_factory=dict)


def compileViews(
    requests: tuple[ViewRequest, ...],
    *,
    subjects: tuple[str, ...] = (),
    measures: tuple[str, ...] = (),
    params: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Query 공통값과 asset별 view override를 결정적으로 합성한다.

    Capabilities:
        한 query 안의 이질적 projection을 owner 실행 단위로 분해한다.

    Args:
        requests: asset과 projection이 결박된 요청들.
        subjects: query 공통 subject.
        measures: query 공통 measure.
        params: query 공통 owner parameter.

    Returns:
        순서를 보존한 실행 단위 tuple.

    Raises:
        ValueError: requestId가 중복되거나 필수 ID가 비어 있을 때.

    Example:
        ``compileViews((ViewRequest("quant.momentum", "signal", "factor"),))``.

    Guide:
        빈 request override는 query 공통값을 상속한다.

    SeeAlso:
        production `DataRequest`와 `DataQuery`.

    AIContext:
        projection은 표현 선택이며 data owner의 계산을 대체하지 않는다.
    """
    seen: set[str] = set()
    compiled = []
    commonParams = dict(params or {})
    for request in requests:
        if not request.assetId or not request.requestId:
            raise ValueError("assetId와 requestId는 필수입니다")
        if request.requestId in seen:
            raise ValueError("requestId는 query 안에서 고유해야 합니다")
        seen.add(request.requestId)
        compiled.append(
            {
                "assetId": request.assetId,
                "requestId": request.requestId,
                "projection": request.projection,
                "subjects": request.subjects or subjects,
                "measures": request.measures or measures,
                "params": commonParams | dict(request.params),
            }
        )
    return tuple(compiled)


def narrativeChunks(
    value: Any,
    *,
    assetId: str,
    revisionId: str,
    sourceRef: str,
    evidenceRef: str,
    eventAt: str | None = None,
    availableAt: str | None = None,
    knownAt: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """임의 중첩값의 문자열 leaf를 결정적 narrative evidence 행으로 만든다.

    Capabilities:
        중첩 mapping과 sequence에서 provenance가 있는 narrative chunk를 만든다.

    Args:
        value: owner native output.
        assetId: logical data asset ID.
        revisionId: asset revision ID.
        sourceRef: 원천 참조.
        evidenceRef: 실행 영수증 참조.
        eventAt: 사실 발생 시각.
        availableAt: 공개 가능 시각.
        knownAt: knowledge cutoff.

    Returns:
        공통 evidence spine을 갖는 narrative 행 tuple.

    Raises:
        없음.

    Example:
        ``narrativeChunks({"risk": "환율 상승"}, assetId="a", revisionId="v", sourceRef="s", evidenceRef="e")``.

    Guide:
        현재 시각을 knownAt으로 자동 주입하지 않는다.

    SeeAlso:
        factor canonical long schema.

    AIContext:
        contentHash는 검색과 인용의 안정 키이며 semantic score가 아니다.
    """
    leaves: list[tuple[str, str]] = []

    def visit(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                visit(child, f"{path}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")
        elif isinstance(item, str) and item.strip():
            leaves.append((path, item.strip()))

    visit(value, "$")
    documentPayload = json.dumps(
        {"assetId": assetId, "revisionId": revisionId, "sourceRef": sourceRef},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    documentId = hashlib.sha256(documentPayload.encode()).hexdigest()
    rows = []
    for path, text in leaves:
        contentHash = hashlib.sha256(text.encode()).hexdigest()
        chunkId = hashlib.sha256(f"{documentId}:{path}:{contentHash}".encode()).hexdigest()
        rows.append(
            {
                "assetId": assetId,
                "documentId": documentId,
                "chunkId": chunkId,
                "section": path,
                "text": text,
                "language": "und",
                "contentHash": contentHash,
                "eventAt": eventAt,
                "availableAt": availableAt,
                "knownAt": knownAt,
                "revisionId": revisionId,
                "sourceRef": sourceRef,
                "evidenceRef": evidenceRef,
                "temporalStatus": "REQUESTED" if knownAt else "LATEST_ONLY",
            }
        )
    return tuple(rows)
