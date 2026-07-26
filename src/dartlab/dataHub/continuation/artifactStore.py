"""Atomic SHA-256 artifact storage for continuation state and pages."""

from __future__ import annotations

import hashlib
import os
import re
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .contracts import ContinuationError
from .privateStorage import _resolvePrivateRoot, securePrivatePath, verifyPrivatePath

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DIRECTORY_SECURITY_LOCK = threading.RLock()


_log = dataHubLogger(__name__)


@dataclass(frozen=True, slots=True)
class LegacyArtifactScan:
    """한 legacy fan-out prefix에서 raw-entry bound를 지킨 migration page."""

    digests: tuple[str, ...]
    complete: bool
    entriesExamined: int


def _ensurePrivateDirectory(path: Path) -> None:
    with _DIRECTORY_SECURITY_LOCK:
        path.mkdir(parents=True, exist_ok=True)
        try:
            verifyPrivatePath(path)
        except ContinuationError as error:
            if error.code != "CONTINUATION_SECURITY_FAILED":
                raise
            securePrivatePath(path)


class ArtifactStore:
    """Private atomic content-addressed byte store."""

    def __init__(
        self,
        root: Path,
        *,
        registrationCheck: Callable[[str, int], bool] | None = None,
    ):
        self.root = _resolvePrivateRoot(root)
        if registrationCheck is not None and not callable(registrationCheck):
            raise TypeError("registrationCheck는 callable 또는 None이어야 합니다")
        self.registrationCheck = registrationCheck
        self.legacyObjectRoot = self.root / "objects" / "sha256"
        self.objectRoot = self.root / "objects" / "sha256-v3"
        _ensurePrivateDirectory(self.root)
        _ensurePrivateDirectory(self.root / "objects")
        _ensurePrivateDirectory(self.legacyObjectRoot)
        _ensurePrivateDirectory(self.objectRoot)

    @staticmethod
    def _validateDigest(digest: str) -> None:
        if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
            raise ContinuationError("CONTINUATION_CORRUPT")

    def _newPathForDigest(self, digest: str) -> Path:
        self._validateDigest(digest)
        path = self.objectRoot.joinpath(digest[:2], digest[2:4], digest[4:6], digest[6:8], digest)
        if path.parents[4] != self.objectRoot:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return path

    def _legacyPathForDigest(self, digest: str) -> Path:
        self._validateDigest(digest)
        path = self.legacyObjectRoot / digest[:2] / digest
        if path.parent.parent != self.legacyObjectRoot:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return path

    def _pathsForDigest(self, digest: str) -> tuple[Path, Path]:
        return self._newPathForDigest(digest), self._legacyPathForDigest(digest)

    def _existingPath(self, digest: str) -> Path:
        current, legacy = self._pathsForDigest(digest)
        currentExists = current.is_file()
        legacyExists = legacy.is_file()
        if currentExists and legacyExists:
            try:
                if not os.path.samefile(current, legacy):
                    raise ContinuationError("CONTINUATION_CORRUPT")
            except OSError:
                raise ContinuationError("CONTINUATION_CORRUPT") from None
            return current
        if currentExists:
            return current
        if legacyExists:
            return legacy
        return current

    def _ensureCurrentParents(self, destination: Path) -> None:
        parents = list(reversed(destination.parents[:4]))
        for parent in parents:
            if parent == self.objectRoot or self.objectRoot in parent.parents:
                _ensurePrivateDirectory(parent)

    def pathForDigest(self, digest: str) -> Path:
        """검증한 digest를 private CAS 내부 경로로 변환한다.

        Capabilities:
            lowercase SHA-256만 fan-out object path로 바꾼다.

        Args:
            digest: lowercase SHA-256 hex digest.

        Returns:
            private object root 안의 deterministic path.

        Raises:
            ContinuationError: digest 형식이나 경계가 잘못됐을 때.

        Example:
            ``store.pathForDigest("0" * 64)``.

        Guide:
            raw filename이나 caller path를 받지 않는다.

        When:
            CAS object를 읽고 쓰고 지우기 전에 호출한다.

        How:
            digest 앞 두 글자를 fan-out directory로 사용한다.

        SeeAlso:
            ``putBytes``, ``readBytes``.

        Requires:
            objectRoot가 초기화되어 있어야 한다.

        AIContext:
            digest-only path는 query와 cursor 원문이 filename에 새는 것을 막는다.
        """
        return self._existingPath(digest)

    def putBytes(self, payload: bytes) -> str:
        """bytes를 fsync와 atomic hard-link publish로 CAS에 기록한다.

        Capabilities:
            같은 payload의 thread와 process 경합을 immutable object 하나로 수렴한다.

        Args:
            payload: private state 또는 Arrow page bytes.

        Returns:
            committed object의 SHA-256 digest.

        Raises:
            ContinuationError: 기존 object digest가 맞지 않을 때.
            TypeError: payload가 bytes가 아닐 때.

        Example:
            ``digest = store.putBytes(b"bounded")``.

        Guide:
            ledger registration을 보유한 SQLite write lock 안에서 호출한다.

        When:
            query state 또는 검증된 page를 durable CAS에 등록할 때 호출한다.

        How:
            unique temp를 fsync한 뒤 hard link로 destination을 원자 생성한다.

        SeeAlso:
            ``readBytes``, ``deleteBytes``.

        Requires:
            temp와 destination이 hard link를 지원하는 같은 filesystem에 있어야 한다.

        AIContext:
            payload 원문은 SQLite가 아니라 private object에만 기록한다.
        """
        if not isinstance(payload, bytes):
            raise TypeError("CAS payload는 bytes여야 합니다")
        digest = hashlib.sha256(payload).hexdigest()
        if self.registrationCheck is not None:
            try:
                registered = self.registrationCheck(digest, len(payload))
            except ContinuationError:
                raise
            except Exception:
                recordFailure(_log, "CONTINUATION_CORRUPT")
                raise ContinuationError("CONTINUATION_CORRUPT") from None
            if registered is not True:
                raise ContinuationError("CONTINUATION_CORRUPT")
        destination = self._existingPath(digest)
        if destination.is_file():
            verifyPrivatePath(destination)
            self.readBytes(digest)
            return digest
        destination = self._newPathForDigest(digest)
        self._ensureCurrentParents(destination)
        temporary = destination.parent / f".{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            securePrivatePath(temporary)
            try:
                os.link(temporary, destination)
            except FileExistsError:
                self.readBytes(digest)
                return digest
            securePrivatePath(destination)
        finally:
            temporary.unlink(missing_ok=True)
        self.readBytes(digest)
        return digest

    def readBytes(
        self,
        digest: str,
        *,
        maxBytes: int | None = None,
        budgetCode: str = "CONTINUATION_STATE_BUDGET",
    ) -> bytes:
        """CAS object의 size와 SHA-256을 검증해 읽는다.

        Capabilities:
            optional pre-read bound와 content digest를 모두 강제한다.

        Args:
            digest: object SHA-256.
            maxBytes: 읽을 수 있는 최대 bytes.
            budgetCode: bound 위반 시 사용할 안전한 오류 코드.

        Returns:
            digest가 검증된 immutable bytes.

        Raises:
            ContinuationError: object 부재, budget, digest 검증 실패 시.

        Example:
            ``payload = store.readBytes(digest, maxBytes=4096)``.

        Guide:
            state와 page는 각각 정책에 맞는 maxBytes를 반드시 넘긴다.

        When:
            context 복원, page replay, integrity audit에서 호출한다.

        How:
            file size를 먼저 확인하고 최대 ``maxBytes + 1``만 읽은 뒤 hash한다.

        SeeAlso:
            ``putBytes``.

        Requires:
            caller가 등록된 ContinuationError code를 budgetCode로 넘긴다.

        AIContext:
            corrupt object가 unbounded memory read를 일으키지 않게 한다.
        """
        path = self.pathForDigest(digest)
        if not path.is_file():
            raise ContinuationError("CONTINUATION_CORRUPT")
        verifyPrivatePath(path)
        if maxBytes is not None and path.stat().st_size > maxBytes:
            raise ContinuationError(budgetCode)
        if maxBytes is None:
            payload = path.read_bytes()
        else:
            with path.open("rb") as stream:
                payload = stream.read(maxBytes + 1)
        if maxBytes is not None and len(payload) > maxBytes:
            raise ContinuationError(budgetCode)
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return payload

    def deleteBytes(self, digest: str) -> tuple[bool, int]:
        """ledger에서 unreferenced임을 확인한 CAS object를 제거한다.

        Capabilities:
            idempotent object delete와 실제 해제 byte 수를 제공한다.

        Args:
            digest: 삭제할 CAS object digest.

        Returns:
            삭제 여부와 해제한 encoded byte 수.

        Raises:
            ContinuationError: filesystem delete가 실패했을 때.

        Example:
            ``deleted, freed = store.deleteBytes(digest)``.

        Guide:
            ``ContinuationStore.pruneExpired``의 reference 재검증 뒤에만 호출한다.

        When:
            expired chain 삭제 뒤 tombstone object가 unreferenced일 때 호출한다.

        How:
            object를 지우고 비어 있는 fan-out directory 정리를 시도한다.

        SeeAlso:
            ``putBytes``.

        Requires:
            caller가 같은 SQLite write lock으로 새 registration을 차단해야 한다.

        AIContext:
            missing object는 crash retry를 위해 성공적인 no-op으로 취급한다.
        """
        current, legacy = self._pathsForDigest(digest)
        existing = [path for path in (current, legacy) if path.is_file()]
        if not existing:
            return False, 0
        if len(existing) == 2:
            try:
                if not os.path.samefile(existing[0], existing[1]):
                    raise ContinuationError("CONTINUATION_CORRUPT")
            except OSError:
                raise ContinuationError("CONTINUATION_CORRUPT") from None
        for path in existing:
            verifyPrivatePath(path)
        try:
            byteCount = existing[0].stat().st_size
            for path in existing:
                path.unlink()
        except OSError:
            raise ContinuationError("CONTINUATION_GC_FAILED") from None
        for path in existing:
            parent = path.parent
            root = (
                self.objectRoot
                if self.objectRoot in parent.parents or parent == self.objectRoot
                else self.legacyObjectRoot
            )
            while parent != root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        return True, byteCount

    def byteCount(self, digest: str) -> int:
        """CAS object를 payload materialization 없이 검증하고 byte 수를 읽는다.

        Capabilities:
            orphan sweep이 unknown object 원문을 메모리에 올리지 않고 tombstone을 만든다.

        Args:
            digest: lowercase SHA-256 object digest.

        Returns:
            private regular file의 encoded byte 수.

        Raises:
            ContinuationError: object가 없거나 private regular file이 아닐 때.

        Example:
            ``size = store.byteCount(digest)``.

        Guide:
            content verification이 필요한 read path는 ``readBytes``를 사용한다.

        When:
            ledger 밖 CAS object를 GC_PENDING으로 등록할 때 호출한다.

        How:
            digest-only path, ACL, regular-file metadata를 검증한다.

        SeeAlso:
            ``scanDigestPrefix``, ``deleteBytes``.

        Requires:
            caller는 object를 참조하지 않는다는 SQLite write lock을 보유한다.

        AIContext:
            손상된 거대 orphan도 unbounded read 없이 삭제 대상으로 전환한다.
        """
        path = self.pathForDigest(digest)
        if not path.is_file():
            raise ContinuationError("CONTINUATION_CORRUPT")
        verifyPrivatePath(path)
        try:
            size = path.stat().st_size
        except OSError:
            raise ContinuationError("CONTINUATION_GC_FAILED") from None
        if type(size) is not int or size < 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return size

    def iterDigests(self) -> tuple[str, ...]:
        """검증 가능한 CAS object digest 목록을 반환한다.

        Args:
            없음.

        Returns:
            정렬된 lowercase SHA-256 tuple.

        Raises:
            없음.

        Example:
            ``assert store.iterDigests() == ()``.

        Requires:
            objectRoot를 다른 process가 교체하지 않는다.
        """
        current = (
            path.name
            for path in self.objectRoot.glob("*/*/*/*/*")
            if path.is_file() and _DIGEST_RE.fullmatch(path.name) is not None
        )
        legacy = (
            path.name
            for path in self.legacyObjectRoot.glob("*/*")
            if path.is_file() and _DIGEST_RE.fullmatch(path.name) is not None
        )
        return tuple(sorted(set(current) | set(legacy)))

    def scanLegacyPrefix(self, prefix: int, *, limit: int) -> LegacyArtifactScan:
        """Legacy CAS prefix에서 raw directory entry를 exact bound 안에서 읽는다.

        Capabilities:
            처리한 entry를 migration으로 제거하는 restart-safe legacy sweep 입력을 제공한다.

        Args:
            prefix: 0~255 범위의 legacy fan-out byte.
            limit: 한 호출에서 열어볼 raw directory entry 최대 수.

        Returns:
            검증된 digest, prefix 완료 여부, 실제 검사 entry 수.

        Raises:
            ValueError: prefix 또는 limit이 잘못됐을 때.
            ContinuationError: legacy directory 구조가 손상됐을 때.

        Example:
            ``page = store.scanLegacyPrefix(0, limit=100)``.

        Guide:
            caller는 반환 digest를 모두 migrate한 뒤에만 prefix cursor를 전진한다.

        When:
            v2 이하 CAS object와 crash orphan을 ledger-first layout으로 옮길 때 호출한다.

        How:
            ``os.scandir``에서 최대 ``limit`` entry만 소비하고 더 읽지 않는다.

        SeeAlso:
            ``migrateLegacyDigest``, ``ContinuationStore.maintain``.

        Requires:
            legacy producer는 maintenance 시작 뒤 이 directory에 새 object를 쓰지 않는다.

        AIContext:
            처리된 파일 자체를 제거하므로 OS enumeration order를 cursor로 신뢰하지 않는다.
        """
        if type(prefix) is not int or not 0 <= prefix <= 0xFF:
            raise ValueError("legacy CAS prefix는 0~255 int여야 합니다")
        if type(limit) is not int or limit <= 0:
            raise ValueError("legacy CAS scan limit은 양의 int여야 합니다")
        prefixText = f"{prefix:02x}"
        directory = self.legacyObjectRoot / prefixText
        if not directory.exists():
            return LegacyArtifactScan((), True, 0)
        verifyPrivatePath(directory)
        if not directory.is_dir():
            raise ContinuationError("CONTINUATION_CORRUPT")
        try:
            iterator = os.scandir(directory)
        except OSError:
            raise ContinuationError("CONTINUATION_GC_FAILED") from None
        rawEntries = []
        with iterator:
            for entry in iterator:
                rawEntries.append(entry)
                if len(rawEntries) >= limit:
                    break

        digests = []
        for entry in rawEntries:
            name = entry.name
            if _DIGEST_RE.fullmatch(name) is None or not name.startswith(prefixText):
                raise ContinuationError("CONTINUATION_CORRUPT")
            try:
                isFile = entry.is_file(follow_symlinks=False)
            except OSError:
                raise ContinuationError("CONTINUATION_GC_FAILED") from None
            if not isFile:
                raise ContinuationError("CONTINUATION_CORRUPT")
            digests.append(name)
        return LegacyArtifactScan(tuple(digests), len(rawEntries) < limit, len(rawEntries))

    def migrateLegacyDigest(self, digest: str) -> Path:
        """검증된 legacy digest path를 ledger-first CAS layout으로 원자 이동한다.

        Capabilities:
            hard-link publish와 idempotent duplicate recovery로 bounded sweep 진행을 영속화한다.

        Args:
            digest: scan에서 얻은 lowercase SHA-256 digest.

        Returns:
            현재 CAS layout의 object path.

        Raises:
            ContinuationError: source, duplicate, link, 보안 검증이 실패했을 때.

        Example:
            ``current = store.migrateLegacyDigest(digest)``.

        Guide:
            SQLite artifact row를 확인하거나 생성한 뒤 호출한다.

        When:
            ``scanLegacyPrefix``가 반환한 각 object를 처리할 때 호출한다.

        How:
            같은 filesystem에 hard link를 만든 뒤 private ACL을 검증하고 legacy link를 지운다.

        SeeAlso:
            ``scanLegacyPrefix``, ``deleteBytes``.

        Requires:
            caller는 continuation SQLite write lock을 보유한다.

        AIContext:
            crash가 두 link 사이에 나도 samefile 확인으로 다음 호출이 수렴한다.
        """
        current, legacy = self._pathsForDigest(digest)
        if not legacy.is_file():
            if current.is_file():
                verifyPrivatePath(current)
                return current
            raise ContinuationError("CONTINUATION_CORRUPT")
        verifyPrivatePath(legacy)
        self._ensureCurrentParents(current)
        if current.exists():
            try:
                if not current.is_file() or not os.path.samefile(current, legacy):
                    raise ContinuationError("CONTINUATION_CORRUPT")
            except OSError:
                raise ContinuationError("CONTINUATION_CORRUPT") from None
        else:
            try:
                os.link(legacy, current)
            except FileExistsError:
                try:
                    if not os.path.samefile(current, legacy):
                        raise ContinuationError("CONTINUATION_CORRUPT")
                except OSError:
                    raise ContinuationError("CONTINUATION_CORRUPT") from None
            except OSError:
                raise ContinuationError("CONTINUATION_GC_FAILED") from None
            securePrivatePath(current)
        try:
            legacy.unlink()
        except OSError:
            raise ContinuationError("CONTINUATION_GC_FAILED") from None
        try:
            legacy.parent.rmdir()
        except OSError:
            pass
        return current
