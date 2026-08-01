"""DataResult를 Arrow payload와 control metadata로 나누는 wire codec."""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import hmac
import json
from typing import Any

from dartlab.dataHub.continuation import canonicalJsonBytes
from dartlab.dataHub.contracts import DataResult
from dartlab.dataHub.controlPlane.errors import DataHubControlError
from dartlab.dataHub.controlPlane.policy import MAX_RESULT_PAYLOAD_BYTES, MAX_RESULT_WIRE_BYTES
from dartlab.dataHub.materialization import MaterializationReceipt
from dartlab.dataHub.paging.composite import (
    decodeMaterializationPage,
    encodeMaterializationPage,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_FORMAT_VERSION = 1


_log = dataHubLogger(__name__)


def encodeDataResult(result: DataResult) -> bytes:
    """한 bounded DataResult page를 canonical wire bytes로 봉인한다."""

    if not isinstance(result, DataResult):
        raise TypeError("result는 DataResult여야 합니다")
    receiptTree = None
    if result.materializationReceipt is not None:
        try:
            receiptTree = MaterializationReceipt.fromTree(dict(result.materializationReceipt)).asTree()
        except (TypeError, ValueError):
            raise DataHubControlError("DATA_HUB_CORRUPT") from None
    try:
        payload = encodeMaterializationPage(result, maxBytes=MAX_RESULT_PAYLOAD_BYTES)
    except Exception:
        recordFailure(_log, "DATA_HUB_PAYLOAD_BUDGET")
        raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET") from None
    payloadDigest = hashlib.sha256(payload).hexdigest()
    encoded = canonicalJsonBytes(
        {
            "formatVersion": _FORMAT_VERSION,
            "payload": base64.b64encode(payload).decode("ascii"),
            "payloadDigest": payloadDigest,
            "continuation": result.continuation,
            "materializationReceipt": receiptTree,
        }
    )
    if len(encoded) > MAX_RESULT_WIRE_BYTES:
        raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
    return encoded


def decodeDataResult(payload: bytes) -> DataResult:
    """Canonical wire bytes를 검증해 DataResult page로 복원한다."""

    if not isinstance(payload, bytes):
        raise TypeError("payload는 bytes여야 합니다")
    if len(payload) > MAX_RESULT_WIRE_BYTES:
        raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
    try:
        tree = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DataHubControlError("DATA_HUB_CORRUPT") from None
    expected = {
        "formatVersion",
        "payload",
        "payloadDigest",
        "continuation",
        "materializationReceipt",
    }
    if (
        not isinstance(tree, dict)
        or set(tree) != expected
        or tree["formatVersion"] != _FORMAT_VERSION
        or not isinstance(tree["payload"], str)
        or not isinstance(tree["payloadDigest"], str)
        or tree["continuation"] is not None
        and not isinstance(tree["continuation"], str)
        or tree["materializationReceipt"] is not None
        and not isinstance(tree["materializationReceipt"], dict)
    ):
        raise DataHubControlError("DATA_HUB_CORRUPT")
    try:
        resultPayload = base64.b64decode(tree["payload"], validate=True)
    except (ValueError, TypeError):
        raise DataHubControlError("DATA_HUB_CORRUPT") from None
    if len(resultPayload) > MAX_RESULT_PAYLOAD_BYTES or not hmac.compare_digest(
        hashlib.sha256(resultPayload).hexdigest(),
        tree["payloadDigest"],
    ):
        raise DataHubControlError("DATA_HUB_CORRUPT")
    try:
        result = decodeMaterializationPage(resultPayload)
    except Exception:
        recordFailure(_log, "DATA_HUB_CORRUPT")
        raise DataHubControlError("DATA_HUB_CORRUPT") from None
    receiptTree = None
    if tree["materializationReceipt"] is not None:
        try:
            receiptTree = MaterializationReceipt.fromTree(tree["materializationReceipt"]).asTree()
        except (TypeError, ValueError):
            raise DataHubControlError("DATA_HUB_CORRUPT") from None
    return dataclasses.replace(
        result,
        continuation=tree["continuation"],
        materializationReceipt=receiptTree,
    )
