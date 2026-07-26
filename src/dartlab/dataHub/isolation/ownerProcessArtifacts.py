"""Owner process의 canonical control frame와 private Arrow artifact I/O."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.continuation.privateStorage import (
    _resolvePrivateRoot,
    securePrivatePath,
    verifyPrivatePath,
)
from dartlab.dataHub.isolation.ownerProcessModels import (
    _ARTIFACT_ID_RE,
    _DIGEST_RE,
    _ERROR_CODE_RE,
    _FORMAT_VERSION,
    _REPARSE_POINT,
    _ProtocolViolation,
)
from dartlab.dataHub.paging.runtime import (
    MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES,
    MAX_OWNER_PROCESS_REQUEST_BYTES,
    MAX_STATE_BYTES,
    ownerProcessArtifactRoot,
)


def _strictJson(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _rejectDuplicatePairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _ProtocolViolation("OWNER_PROCESS_CONTROL_DUPLICATE_KEY")
        result[key] = value
    return result


def _loadStrictJson(payload: bytes, *, maxBytes: int) -> dict[str, Any]:
    if not isinstance(payload, bytes) or not payload or len(payload) > maxBytes:
        raise _ProtocolViolation("OWNER_PROCESS_JSON_BYTE_BUDGET")
    try:
        value = json.loads(payload.decode("ascii"), object_pairs_hook=_rejectDuplicatePairs)
    except _ProtocolViolation:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _ProtocolViolation("OWNER_PROCESS_JSON_INVALID") from None
    if not isinstance(value, dict) or _strictJson(value) != payload:
        raise _ProtocolViolation("OWNER_PROCESS_JSON_NONCANONICAL")
    return value


def _decodeControlFrame(payload: bytes, *, artifactId: str) -> dict[str, Any]:
    frame = _loadStrictJson(payload, maxBytes=MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES)
    kind = frame.get("kind")
    if kind == "ready":
        if set(frame) != {"kind", "pid", "threadNativeId"}:
            raise _ProtocolViolation("OWNER_PROCESS_READY_SCHEMA")
        if type(frame["pid"]) is not int or frame["pid"] <= 0:
            raise _ProtocolViolation("OWNER_PROCESS_READY_PID")
        if type(frame["threadNativeId"]) is not int or frame["threadNativeId"] <= 0:
            raise _ProtocolViolation("OWNER_PROCESS_READY_THREAD")
        return frame
    if kind != "result" or set(frame) != {
        "artifactId",
        "byteCount",
        "digest",
        "errorCode",
        "kind",
        "rowCount",
        "status",
    }:
        raise _ProtocolViolation("OWNER_PROCESS_RESULT_SCHEMA")
    if frame["artifactId"] != artifactId:
        raise _ProtocolViolation("OWNER_PROCESS_ARTIFACT_ID_MISMATCH")
    statusValue = frame["status"]
    if statusValue == "ok":
        if (
            type(frame["byteCount"]) is not int
            or frame["byteCount"] <= 0
            or type(frame["rowCount"]) is not int
            or frame["rowCount"] < 0
            or type(frame["digest"]) is not str
            or _DIGEST_RE.fullmatch(frame["digest"]) is None
            or frame["errorCode"] is not None
        ):
            raise _ProtocolViolation("OWNER_PROCESS_RESULT_CLAIM")
        return frame
    if statusValue == "failed":
        errorCode = frame["errorCode"]
        if (
            frame["byteCount"] is not None
            or frame["rowCount"] is not None
            or frame["digest"] is not None
            or type(errorCode) is not str
            or _ERROR_CODE_RE.fullmatch(errorCode) is None
        ):
            raise _ProtocolViolation("OWNER_PROCESS_FAILURE_CLAIM")
        return frame
    raise _ProtocolViolation("OWNER_PROCESS_RESULT_STATUS")


def _buildRequest(
    sessionPayload: bytes,
    *,
    artifactId: str,
    workDeadline: float,
) -> bytes:
    if not isinstance(sessionPayload, bytes) or not sessionPayload or len(sessionPayload) > MAX_STATE_BYTES:
        raise ValueError("owner session payload 크기가 유효하지 않습니다")
    if _ARTIFACT_ID_RE.fullmatch(artifactId) is None:
        raise ValueError("owner artifact ID가 유효하지 않습니다")
    payload = _strictJson(
        {
            "artifactId": artifactId,
            "sessionDigest": hashlib.sha256(sessionPayload).hexdigest(),
            "sessionPayload": base64.b64encode(sessionPayload).decode("ascii"),
            "version": _FORMAT_VERSION,
            "workDeadlineNs": int(workDeadline * 1_000_000_000),
        }
    )
    if len(payload) > MAX_OWNER_PROCESS_REQUEST_BYTES:
        raise ValueError("owner process input payload가 상한을 초과했습니다")
    return payload


def _decodeRequest(payload: bytes) -> tuple[str, bytes, float]:
    root = _loadStrictJson(payload, maxBytes=MAX_OWNER_PROCESS_REQUEST_BYTES)
    if (
        set(root)
        != {
            "artifactId",
            "sessionDigest",
            "sessionPayload",
            "version",
            "workDeadlineNs",
        }
        or root["version"] != _FORMAT_VERSION
    ):
        raise _ProtocolViolation("OWNER_PROCESS_REQUEST_SCHEMA")
    artifactId = root["artifactId"]
    sessionDigest = root["sessionDigest"]
    encoded = root["sessionPayload"]
    workDeadlineNs = root["workDeadlineNs"]
    if (
        type(artifactId) is not str
        or _ARTIFACT_ID_RE.fullmatch(artifactId) is None
        or type(sessionDigest) is not str
        or _DIGEST_RE.fullmatch(sessionDigest) is None
        or type(encoded) is not str
        or type(workDeadlineNs) is not int
        or workDeadlineNs <= 0
    ):
        raise _ProtocolViolation("OWNER_PROCESS_REQUEST_VALUE")
    try:
        sessionPayload = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError):
        raise _ProtocolViolation("OWNER_PROCESS_REQUEST_BASE64") from None
    if (
        not sessionPayload
        or len(sessionPayload) > MAX_STATE_BYTES
        or not secrets.compare_digest(hashlib.sha256(sessionPayload).hexdigest(), sessionDigest)
    ):
        raise _ProtocolViolation("OWNER_PROCESS_REQUEST_DIGEST")
    return artifactId, sessionPayload, workDeadlineNs / 1_000_000_000


def _isReparse(path: Path) -> bool:
    try:
        isJunction = getattr(path, "is_junction", None)
        if path.is_symlink() or (callable(isJunction) and isJunction()):
            return True
        metadata = path.lstat()
    except OSError:
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & _REPARSE_POINT)


def _ensureArtifactRoot() -> Path:
    root = _resolvePrivateRoot(ownerProcessArtifactRoot())
    root.mkdir(parents=True, exist_ok=True)
    if _isReparse(root):
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")
    try:
        verifyPrivatePath(root)
    except ContinuationError as error:
        if error.code != "CONTINUATION_SECURITY_FAILED":
            raise
        securePrivatePath(root)
        verifyPrivatePath(root)
    return root


def _artifactPath(root: Path, artifactId: str) -> Path:
    if _ARTIFACT_ID_RE.fullmatch(artifactId) is None:
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")
    path = root / f"{artifactId}.arrow"
    if path.parent != root:
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")
    return path


def _requireArtifactFile(path: Path, root: Path) -> os.stat_result:
    if path.parent != root or _isReparse(root) or _isReparse(path):
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")
    try:
        verifyPrivatePath(root)
        verifyPrivatePath(path)
        metadata = path.lstat()
    except ContinuationError:
        raise
    except OSError:
        raise ContinuationError("CONTINUATION_SECURITY_FAILED") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")
    return metadata


def _createArtifact(path: Path, root: Path) -> None:
    if path.parent != root or _isReparse(root):
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")
    try:
        with path.open("xb"):
            pass
        securePrivatePath(path)
        metadata = _requireArtifactFile(path, root)
    except ContinuationError:
        raise
    except OSError:
        raise ContinuationError("CONTINUATION_SECURITY_FAILED") from None
    if metadata.st_size != 0:
        raise ContinuationError("CONTINUATION_SECURITY_FAILED")


def _writeArtifact(path: Path, root: Path, payload: bytes, *, maxBytes: int) -> None:
    if not isinstance(payload, bytes) or not payload or len(payload) > maxBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    before = _requireArtifactFile(path, root)
    try:
        with path.open("r+b", buffering=0) as stream:
            opened = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
                or getattr(opened, "st_file_attributes", 0) & _REPARSE_POINT
            ):
                raise ContinuationError("CONTINUATION_SECURITY_FAILED")
            stream.truncate(0)
            view = memoryview(payload)
            offset = 0
            while offset < len(view):
                written = stream.write(view[offset:])
                if not isinstance(written, int) or written <= 0:
                    raise OSError("owner artifact write가 진행되지 않았습니다")
                offset += written
            stream.flush()
            os.fsync(stream.fileno())
    except ContinuationError:
        raise
    except OSError:
        raise ContinuationError("CONTINUATION_ARTIFACT_WRITE_FAILED") from None
    after = _requireArtifactFile(path, root)
    if after.st_size != len(payload):
        raise ContinuationError("CONTINUATION_ARTIFACT_WRITE_FAILED")


def _readArtifact(
    path: Path,
    root: Path,
    *,
    byteCount: int,
    digest: str,
    maxBytes: int,
) -> bytes:
    if type(byteCount) is not int or byteCount <= 0 or byteCount > maxBytes or _DIGEST_RE.fullmatch(digest) is None:
        raise ContinuationError("CONTINUATION_ARTIFACT_INVALID")
    before = _requireArtifactFile(path, root)
    if before.st_size != byteCount:
        raise ContinuationError("CONTINUATION_ARTIFACT_INVALID")
    try:
        with path.open("rb", buffering=0) as stream:
            opened = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
                or getattr(opened, "st_file_attributes", 0) & _REPARSE_POINT
            ):
                raise ContinuationError("CONTINUATION_SECURITY_FAILED")
            payload = stream.read(byteCount + 1)
    except ContinuationError:
        raise
    except OSError:
        raise ContinuationError("CONTINUATION_ARTIFACT_INVALID") from None
    if len(payload) != byteCount or not secrets.compare_digest(hashlib.sha256(payload).hexdigest(), digest):
        raise ContinuationError("CONTINUATION_ARTIFACT_INVALID")
    after = _requireArtifactFile(path, root)
    if after.st_size != byteCount or after.st_dev != before.st_dev or after.st_ino != before.st_ino:
        raise ContinuationError("CONTINUATION_ARTIFACT_INVALID")
    return payload


def _removeArtifact(path: Path) -> None:
    try:
        if path.is_dir() and not path.is_symlink():
            raise ContinuationError("CONTINUATION_SECURITY_FAILED")
        path.unlink(missing_ok=True)
    except ContinuationError:
        raise
    except OSError:
        raise ContinuationError("CONTINUATION_ARTIFACT_CLEANUP_FAILED") from None


def _safeErrorCode(error: BaseException) -> str:
    code = getattr(error, "code", None)
    if type(code) is str and _ERROR_CODE_RE.fullmatch(code) is not None:
        return code
    if isinstance(error, _ProtocolViolation):
        text = str(error)
        if _ERROR_CODE_RE.fullmatch(text) is not None:
            return text
    return "OWNER_PROCESS_CHILD_FAILED"
