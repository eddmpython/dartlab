"""Eager seal 호출의 인자 검증과 child request payload 조립.

child 를 하나도 띄우지 않는 앞단이다. 자원을 잡기 전에 끝나야 하는 검사와, 부모가
자식에게 넘길 canonical JSON 요청을 여기서 만든다. 자원 취득과 섞이면 실패 시
되돌릴 것이 생기므로 supervisor 본체에서 분리해 둔다.
"""

from __future__ import annotations

import hmac
import importlib
import math
from collections.abc import Mapping, Sequence

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.contracts import DataAssetDescriptor, DataQuery
from dartlab.dataHub.isolation.eagerProcess import (
    _BUNDLE_OVERHEAD_BYTES,
    _FORMAT_VERSION,
    _MAX_BUNDLE_BYTES,
    eagerCodePin,
)
from dartlab.dataHub.isolation.ownerProcess import _strictJson
from dartlab.dataHub.paging.runtime import MAX_OWNER_PROCESS_REQUEST_BYTES


def _validateSealArguments(
    selectors: Sequence[Mapping[str, str]],
    *,
    publicDeadline: float,
    cleanupGraceSeconds: float,
    minimumWorkSeconds: float,
    maxBundleBytes: int,
) -> None:
    """Spawn 전에 끝나야 하는 deadline 과 seal 예산 계약을 검사한다.

    세 검사의 순서가 곧 오류 메시지의 순서다. 어느 하나라도 앞당기거나 미루면
    호출자가 받는 ``ValueError`` 문구가 달라진다.
    """

    numeric = (publicDeadline, cleanupGraceSeconds, minimumWorkSeconds)
    if any(type(value) not in {int, float} or not math.isfinite(value) for value in numeric):
        raise ValueError("eager process deadline 값은 유한한 숫자여야 합니다")
    if cleanupGraceSeconds <= 0 or minimumWorkSeconds <= 0:
        raise ValueError("eager process deadline 예약은 양수여야 합니다")
    if (
        not selectors
        or type(maxBundleBytes) is not int
        or not _BUNDLE_OVERHEAD_BYTES < maxBundleBytes <= _MAX_BUNDLE_BYTES
    ):
        raise ValueError("eager process seal 예산이 유효하지 않습니다")


def _buildSealRequest(
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    selectors: Sequence[Mapping[str, str]],
    *,
    requestId: str,
    snapshotId: str,
    contractHash: str,
    universeSnapshotId: str | None,
    codePin: str | None,
    maxBundleBytes: int,
    workDeadline: float,
) -> bytes:
    """Code pin 을 확정하고 자식에게 보낼 canonical 요청 bytes 를 만든다.

    artifactId 는 아직 비어 있는 자리(64 개의 ``0``)로 둔다. 실제 ID 는 부모가 artifact
    를 만든 뒤에만 알 수 있어서, launch 단계에서 같은 자리에 덮어쓴다.

    Raises:
        ValueError: Code pin 형식이나 payload 상한이 계약을 벗어날 때.
        ContinuationError: 자식과 부모의 code pin 이 다를 때.
    """

    composite = importlib.import_module("dartlab.dataHub.paging.composite")
    execution = importlib.import_module("dartlab.dataHub.execution")
    owner = importlib.import_module("dartlab.dataHub.paging.owner")
    requestedMeasures = execution._requestedMeasures(query)
    expectedCodePin = eagerCodePin(
        descriptor,
        requestedMeasures=requestedMeasures,
    )
    activeCodePin = expectedCodePin if codePin is None else codePin
    if (
        type(activeCodePin) is not str
        or len(activeCodePin) != 64
        or any(character not in "0123456789abcdef" for character in activeCodePin)
    ):
        raise ValueError("eager code pin이 유효하지 않습니다")
    if not hmac.compare_digest(activeCodePin, expectedCodePin):
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED")
    requestPayload = _strictJson(
        {
            "artifactId": "0" * 64,
            "codePin": activeCodePin,
            "contractHash": contractHash,
            "descriptor": owner._descriptorTree(descriptor),
            "maxBytes": maxBundleBytes,
            "maxRows": query.budget.maxRows,
            "query": composite._queryTree(query),
            "requestId": requestId,
            "selectors": [dict(selector) for selector in selectors],
            "snapshotId": snapshotId,
            "universeSnapshotId": universeSnapshotId,
            "version": _FORMAT_VERSION,
            "workDeadlineNs": int(workDeadline * 1_000_000_000),
        }
    )
    if len(requestPayload) > MAX_OWNER_PROCESS_REQUEST_BYTES:
        raise ValueError("eager process input payload가 상한을 초과했습니다")
    return requestPayload


__all__: list[str] = []
