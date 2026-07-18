"""Universe U1 immutable SHA-256 content-addressed object store."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path

_OBJECT_REF_RE = re.compile(r"^cas:sha256:([0-9a-f]{64})$")


class CasIntegrityError(RuntimeError):
    pass


class ContentAddressedStore:
    """Dedicated Universe home 아래에서만 byte를 원자적으로 저장한다."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.objectRoot = self.root / "objects" / "sha256"
        self.objectRoot.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def objectRef(digest: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"잘못된 SHA-256: {digest}")
        return f"cas:sha256:{digest}"

    @staticmethod
    def digestFromRef(objectRef: str) -> str:
        match = _OBJECT_REF_RE.fullmatch(objectRef)
        if match is None:
            raise ValueError(f"잘못된 CAS ref: {objectRef}")
        return match.group(1)

    def pathForDigest(self, digest: str) -> Path:
        self.objectRef(digest)
        path = (self.objectRoot / digest[:2] / digest).resolve()
        if not path.is_relative_to(self.objectRoot.resolve()):
            raise ValueError("CAS root 밖 object path")
        return path

    def putBytes(self, payload: bytes) -> str:
        """Byte를 digest path에 원자적으로 저장하고 immutable object ref를 반환한다."""
        digest = hashlib.sha256(payload).hexdigest()
        destination = self.pathForDigest(digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                raise CasIntegrityError(f"기존 CAS object digest mismatch: {digest}")
            return self.objectRef(digest)
        temporary = destination.parent / f".{digest}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise CasIntegrityError(f"CAS commit 검증 실패: {digest}")
        return self.objectRef(digest)

    def readBytes(self, objectRef: str) -> bytes:
        digest = self.digestFromRef(objectRef)
        path = self.pathForDigest(digest)
        if not path.is_file():
            raise CasIntegrityError(f"CAS object 누락: {objectRef}")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise CasIntegrityError(f"CAS object digest mismatch: {objectRef}")
        return payload

    def verify(self, objectRef: str) -> bool:
        self.readBytes(objectRef)
        return True
