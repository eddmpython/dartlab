"""파일 기반 비밀 저장소 — OS 보안 저장소 기반 암호화. core 강등 SSOT.

이전: src/dartlab/ai/settings/secrets.py (0.10 까지 shim 유지)
사유: SecretStore 는 cross-cutting primitive (ai/cli/server/credentials 모두 사용).
Windows는 OS 사용자 컨텍스트 DPAPI를 사용한다. macOS/Linux는 keyring에 보관한
Fernet master key를 기본으로 사용하고, headless 환경은 ``DARTLAB_SECRET_KEY``를
명시할 수 있다. 안전한 backend가 없으면 평문으로 내려가지 않고 실패한다.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

_SECRET_KEY_ENV = "DARTLAB_SECRET_KEY"
_KEYRING_SERVICE = "dartlab.secret-store"
_KEYRING_ACCOUNT = "fernet-master-v1"
_LOCK_TIMEOUT_SECONDS = 10.0
_WINDOWS_CRYPTO_STATE: tuple[Any, ...] | None = None
_WINDOWS_CRYPTO_INIT_LOCK = threading.Lock()


def dartlabHome() -> Path:
    """dartlab 사용자 상태 디렉터리. ``DARTLAB_HOME`` 이 있으면 그것, 없으면 ``~/.dartlab``.

    Args:
        없음.

    Returns:
        Path. 존재 여부는 확인하지 않는다. 만드는 것은 쓰는 쪽 몫이다.

    Raises:
        없음.

    Example:
        >>> dartlabHome().name
        '.dartlab'
    """
    raw = os.environ.get("DARTLAB_HOME")
    if raw:
        return Path(raw)
    return Path.home() / ".dartlab"


@dataclass(frozen=True)
class SecretEntry:
    """암호화된 비밀 값 엔트리 (backend + 인코딩된 value)."""

    backend: str
    value: str


class SecretStoreError(RuntimeError):
    """SecretStore 조작 중 발생하는 오류."""


class SecretStoreCorruptError(SecretStoreError):
    """저장 파일 또는 엔트리 형식이 손상됨."""


class SecretStoreReadError(SecretStoreError):
    """저장 파일을 읽지 못함."""


class SecretStoreWriteError(SecretStoreError):
    """저장 파일을 쓰지 못함.

    ``committed``가 True면 process-visible 파일 교체는 끝난 상태다. Windows처럼
    디렉터리 fsync를 제공하지 않는 플랫폼의 power-loss durability까지 뜻하지는 않는다.
    호출자는 재시도 전에 실제 값을 다시 읽어야 한다.
    """

    def __init__(self, message: str, *, committed: bool) -> None:
        super().__init__(message)
        self.committed = committed


class SecretStoreLockError(SecretStoreError):
    """저장소 갱신 잠금을 획득하거나 해제하지 못함."""

    def __init__(self, message: str, *, committed: bool = False) -> None:
        super().__init__(message)
        self.committed = committed


class SecretStoreCompositeError(SecretStoreError):
    """둘 이상의 저장소 실패를 원인 손실 없이 전달."""

    def __init__(self, message: str, errors: tuple[Exception, ...], *, committed: bool) -> None:
        super().__init__(message)
        self.errors = errors
        self.committed = committed


class SecretStoreBackendError(SecretStoreError):
    """사용 가능한 안전한 암호화 backend가 없거나 설정이 잘못됨."""


class SecretStoreDecryptError(SecretStoreError):
    """저장된 secret을 복호화하거나 문자열로 복원하지 못함."""


class SecretStore:
    """파일 기반 비밀 저장소 — Windows DPAPI 또는 keyring/Fernet."""

    def __init__(self, path: Path | None = None) -> None:
        target = path or (dartlabHome() / "secrets.json")
        self.path = target.expanduser().resolve(strict=False)

    def _load(self) -> dict[str, dict[str, str]]:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except FileNotFoundError:
            return {}
        except OSError as exc:
            raise SecretStoreReadError("secret store 읽기 실패") from exc
        except json.JSONDecodeError as exc:
            raise SecretStoreCorruptError("secret store JSON 파싱 실패") from exc
        if not isinstance(data, dict):
            raise SecretStoreCorruptError("secret store 형식이 올바르지 않습니다")
        for key, value in data.items():
            if (
                not isinstance(key, str)
                or not isinstance(value, dict)
                or set(value) != {"backend", "value"}
                or not isinstance(value.get("backend"), str)
                or not isinstance(value.get("value"), str)
            ):
                raise SecretStoreCorruptError("secret store 엔트리 형식이 올바르지 않습니다")
        return data

    def _save(self, data: dict[str, dict[str, str]]) -> None:
        tmpPath: str | None = None
        committed = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmpPath = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
            try:
                stream = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
            except BaseException as openError:
                try:
                    os.close(fd)
                except OSError as closeError:
                    raise _combinedFailure(
                        "secret store 임시 파일 열기와 descriptor 정리가 함께 실패했습니다",
                        openError,
                        closeError,
                        committed=False,
                    ) from None
                raise
            with stream:
                json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            tmp = Path(tmpPath)
            if not _isWindows():
                tmp.chmod(0o600)
            os.replace(tmp, self.path)
            committed = True
            if not _isWindows():
                self.path.chmod(0o600)
                _syncDirectory(self.path.parent)
        except BaseException as operationError:
            wrapped = _wrapWriteError(operationError, committed=committed)
            if wrapped is not operationError:
                wrapped.__cause__ = operationError
            cleanupError = _cleanupTemporaryFile(tmpPath, committed=committed)
            if cleanupError is not None:
                raise _combinedFailure(
                    "secret store 저장과 임시 파일 정리가 함께 실패했습니다",
                    wrapped,
                    cleanupError,
                    committed=committed,
                ) from None
            if wrapped is operationError:
                raise
            raise wrapped from operationError
        cleanupError = _cleanupTemporaryFile(tmpPath, committed=committed)
        if cleanupError is not None:
            raise cleanupError

    def get(self, name: str) -> str | None:
        """이름으로 비밀 값 조회. 없으면 None."""
        data = self._load()
        entry = data.get(name)
        if not entry:
            return None
        secretEntry = SecretEntry(**entry)
        if secretEntry.backend == "plain":
            return self._migratePlain(name)
        return self._decodeEntry(secretEntry)

    def set(self, name: str, value: str) -> None:
        """비밀 값 저장 (암호화 후 파일에 기록)."""
        with _mutationLock(self.path) as mutation:
            data = self._load()
            codecs = self._validateEncryptedEntries(data)
            entry = self._encodeEntry(value, preferredBackend=_preferredFernetBackend(data), codecs=codecs)
            data[name] = {"backend": entry.backend, "value": entry.value}
            self._save(data)
            mutation.committed = True

    def delete(self, name: str) -> None:
        """이름에 해당하는 비밀 값 삭제."""
        with _mutationLock(self.path) as mutation:
            data = self._load()
            if name in data:
                del data[name]
                self._save(data)
                mutation.committed = True

    def has(self, name: str) -> bool:
        """비밀 값 존재 여부 — DPAPI decrypt 없이 키 존재만 체크.

        과거 `self.get(name) is not None` 로 구현해 호출 1 회당 DPAPI CryptUnprotectData
        ~10s 가 누적, /api/ai/profile 가 9 개 provider 에 대해 has() 9 번 호출 → 90s 블락.
        존재 여부 판정에 복호화는 불필요.
        """
        return name in self._load()

    def keys(self) -> set[str]:
        """저장된 모든 비밀 이름 — _load() 1 회로 N 개 has() 일괄 판정용."""
        return set(self._load().keys())

    def usableKeys(self, names: Iterable[str] | None = None) -> set[str]:
        """요청한 secret을 한 번 읽어 실제 복호화 가능한 이름만 반환.

        손상이나 master key 유실은 빈 값으로 바꾸지 않고 typed error로 전파한다.
        구버전 평문 엔트리는 ``get``의 잠금 migration 계약을 거친다.
        """
        data = self._load()
        selected = set(data) if names is None else set(names).intersection(data)
        usable: set[str] = set()
        codecs: dict[str, Any] = {}
        for name in selected:
            entry = SecretEntry(**data[name])
            if entry.backend == "plain":
                if self.get(name) is not None:
                    usable.add(name)
            else:
                self._decodeEntry(entry, codecs=codecs)
                usable.add(name)
        return usable

    def getJson(self, name: str) -> dict[str, Any] | None:
        """JSON으로 저장된 비밀 값을 dict로 파싱하여 반환."""
        raw = self.get(name)
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretStoreCorruptError("JSON secret 파싱 실패") from exc
        if not isinstance(data, dict):
            raise SecretStoreCorruptError("JSON secret 형식이 올바르지 않습니다")
        return data

    def setJson(self, name: str, value: dict[str, Any]) -> None:
        """dict를 JSON 직렬화하여 비밀 값으로 저장."""
        self.set(name, json.dumps(value, ensure_ascii=False))

    def _encodeEntry(
        self,
        value: str,
        *,
        preferredBackend: str | None = None,
        codecs: dict[str, Any] | None = None,
    ) -> SecretEntry:
        raw = value.encode("utf-8")
        if _usesDpapi():
            try:
                encrypted = _protectWindows(raw)
            except OSError as exc:
                raise SecretStoreBackendError("DPAPI secret 암호화 실패") from exc
            return SecretEntry(backend="dpapi", value=base64.b64encode(encrypted).decode("ascii"))
        if preferredBackend in {"fernet", "fernet-env"}:
            fernet = codecs.get("fernet-env") if codecs is not None else None
            fernet = fernet or _fernetFromEnvironment()
            return SecretEntry(backend="fernet-env", value=fernet.encrypt(raw).decode("ascii"))
        if preferredBackend == "fernet-keyring":
            fernet = codecs.get("fernet-keyring") if codecs is not None else None
            fernet = fernet or _keyringFernet(self.path, create=False)
            return SecretEntry(backend="fernet-keyring", value=fernet.encrypt(raw).decode("ascii"))
        fernet, backend = _fernetForWrite(self.path)
        return SecretEntry(backend=backend, value=fernet.encrypt(raw).decode("ascii"))

    def _decodeEntry(self, entry: SecretEntry, *, codecs: dict[str, Any] | None = None) -> str:
        if entry.backend == "dpapi":
            if not _usesDpapi():
                raise SecretStoreBackendError("DPAPI secret은 Windows에서만 읽을 수 있습니다")
            try:
                raw = base64.b64decode(entry.value.encode("ascii"), validate=True)
                return _unprotectWindows(raw).decode("utf-8")
            except (binascii.Error, OSError, UnicodeError, ValueError) as exc:
                raise SecretStoreDecryptError("DPAPI secret 복호화 실패") from exc
        if entry.backend in {"fernet", "fernet-env", "fernet-keyring"}:
            try:
                from cryptography.fernet import InvalidToken

                codecKey = "fernet-env" if entry.backend == "fernet" else entry.backend
                fernet = codecs.get(codecKey) if codecs is not None else None
                if fernet is None:
                    fernet = _fernetForRead(self.path, entry.backend)
                    if codecs is not None:
                        codecs[codecKey] = fernet
                return fernet.decrypt(entry.value.encode("ascii")).decode("utf-8")
            except InvalidToken as exc:
                raise SecretStoreDecryptError("Fernet secret 복호화 실패") from exc
            except UnicodeError as exc:
                raise SecretStoreDecryptError("Fernet secret 문자열 복원 실패") from exc
        if entry.backend == "plain":
            raise SecretStoreCorruptError("평문 secret은 get()의 보안 migration 경로로만 읽을 수 있습니다")
        raise SecretStoreCorruptError(f"지원하지 않는 secret backend: {entry.backend}")

    def _migratePlain(self, name: str) -> str | None:
        """구버전 평문 엔트리를 잠금 안에서 읽고 즉시 안전한 backend로 교체."""
        with _mutationLock(self.path) as mutation:
            data = self._load()
            rawEntry = data.get(name)
            if rawEntry is None:
                return None
            entry = SecretEntry(**rawEntry)
            if entry.backend != "plain":
                return self._decodeEntry(entry)
            codecs = self._validateEncryptedEntries(data)
            value = _decodeLegacyPlain(entry.value)
            secured = self._encodeEntry(
                value,
                preferredBackend=_preferredFernetBackend(data),
                codecs=codecs,
            )
            data[name] = {"backend": secured.backend, "value": secured.value}
            self._save(data)
            mutation.committed = True
            return value

    def _validateEncryptedEntries(self, data: dict[str, dict[str, str]]) -> dict[str, Any]:
        """갱신 전 기존 암호문을 검증해 master key 유실·교체에 의한 혼합 저장을 차단."""
        codecs: dict[str, Any] = {}
        for rawEntry in data.values():
            entry = SecretEntry(**rawEntry)
            if entry.backend != "plain":
                self._decodeEntry(entry, codecs=codecs)
        return codecs


def _isWindows() -> bool:
    return os.name == "nt"


def _usesDpapi() -> bool:
    return _isWindows()


def _fernetFromKey(key: str, *, source: str) -> Any:
    try:
        from cryptography.fernet import Fernet

        return Fernet(key.encode("ascii"))
    except ImportError as exc:
        raise SecretStoreBackendError("Fernet backend를 사용하려면 cryptography가 필요합니다") from exc
    except (UnicodeError, ValueError) as exc:
        raise SecretStoreBackendError(f"{source}에 올바른 Fernet 키가 없습니다") from exc


def _fernetFromEnvironment() -> Any:
    key = os.environ.get(_SECRET_KEY_ENV, "").strip()
    if not key:
        raise SecretStoreBackendError(f"{_SECRET_KEY_ENV}에 Fernet 키를 설정해야 이 secret을 읽을 수 있습니다")
    return _fernetFromKey(key, source=_SECRET_KEY_ENV)


def _isTrustedKeyringBackend(backend: Any) -> bool:
    identity = f"{type(backend).__module__}.{type(backend).__qualname__}".lower()
    return identity.startswith(
        (
            "keyring.backends.secretservice.",
            "keyring.backends.kwallet.",
            "keyring.backends.macos.",
            "keyring.backends.windows.",
        )
    )


def _secureKeyringBackend(keyringModule: Any) -> Any:
    backend = keyringModule.get_keyring()
    identity = f"{type(backend).__module__}.{type(backend).__qualname__}".lower()
    if "chainer" in identity:
        candidates = tuple(getattr(backend, "backends", ()))
        for candidate in candidates:
            if _isTrustedKeyringBackend(candidate):
                return candidate
        raise SecretStoreBackendError(
            f"안전한 OS keyring backend가 없습니다. {_SECRET_KEY_ENV}에 Fernet 키를 설정하세요"
        )
    if not _isTrustedKeyringBackend(backend):
        raise SecretStoreBackendError(
            f"안전한 OS keyring backend가 없습니다. {_SECRET_KEY_ENV}에 Fernet 키를 설정하세요"
        )
    return backend


def _keyringLockTarget() -> Path:
    return Path.home() / ".dartlab" / "keyring-master"


def _keyringSentinelPath() -> Path:
    return _keyringLockTarget().with_suffix(".json")


def _masterFingerprint(key: str) -> str:
    return hashlib.sha256(key.encode("ascii")).hexdigest()


def _readMasterFingerprint() -> str | None:
    try:
        data = SecretStore(_keyringSentinelPath())._load()
    except SecretStoreError as exc:
        raise SecretStoreBackendError("OS keyring bootstrap fingerprint를 읽을 수 없습니다") from exc
    if not data:
        return None
    if set(data) != {"master"}:
        raise SecretStoreBackendError("OS keyring bootstrap fingerprint 형식이 올바르지 않습니다")
    entry = data["master"]
    fingerprint = entry["value"]
    if entry["backend"] != "sha256" or len(fingerprint) != 64:
        raise SecretStoreBackendError("OS keyring bootstrap fingerprint 형식이 올바르지 않습니다")
    try:
        int(fingerprint, 16)
    except ValueError as exc:
        raise SecretStoreBackendError("OS keyring bootstrap fingerprint 형식이 올바르지 않습니다") from exc
    return fingerprint


def _writeMasterFingerprint(fingerprint: str) -> None:
    try:
        SecretStore(_keyringSentinelPath())._save({"master": {"backend": "sha256", "value": fingerprint}})
    except SecretStoreError as exc:
        raise SecretStoreBackendError("OS keyring bootstrap fingerprint를 저장할 수 없습니다") from exc


def _keyringFernet(_path: Path, *, create: bool) -> Any:
    try:
        import keyring
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise SecretStoreBackendError(
            f"OS keyring backend가 없습니다. {_SECRET_KEY_ENV}에 Fernet 키를 설정하세요"
        ) from exc

    try:
        backend = _secureKeyringBackend(keyring)
        key = backend.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT)
        if not create:
            if key is None:
                raise SecretStoreBackendError("OS keyring master key가 없습니다. 기존 master를 복원해야 합니다")
            fingerprint = _readMasterFingerprint()
            if fingerprint is None:
                raise SecretStoreBackendError("OS keyring bootstrap fingerprint가 없습니다")
            if fingerprint != _masterFingerprint(key):
                raise SecretStoreBackendError("OS keyring master key fingerprint가 일치하지 않습니다")
            return _fernetFromKey(key, source="OS keyring")

        if key is None or _readMasterFingerprint() is None:
            try:
                with _mutationLock(_keyringLockTarget()) as mutation:
                    key = backend.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT)
                    fingerprint = _readMasterFingerprint()
                    if key is None:
                        if fingerprint is not None:
                            raise SecretStoreBackendError(
                                "OS keyring master key가 유실됐습니다. 기존 master를 복원해야 합니다"
                            )
                        key = Fernet.generate_key().decode("ascii")
                        backend.set_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT, key)
                        mutation.committed = True
                    if backend.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT) != key:
                        raise SecretStoreBackendError("OS keyring master key 저장 검증에 실패했습니다")
                    expected = _masterFingerprint(key)
                    if fingerprint is None:
                        _writeMasterFingerprint(expected)
                        mutation.committed = True
                    elif fingerprint != expected:
                        raise SecretStoreBackendError("OS keyring master key fingerprint가 일치하지 않습니다")
            except SecretStoreError as exc:
                raise SecretStoreBackendError("OS keyring master key 초기화에 실패했습니다") from exc
        else:
            fingerprint = _readMasterFingerprint()
            if fingerprint != _masterFingerprint(key):
                raise SecretStoreBackendError("OS keyring master key fingerprint가 일치하지 않습니다")
        return _fernetFromKey(key, source="OS keyring")
    except SecretStoreBackendError:
        raise
    except Exception as exc:
        raise SecretStoreBackendError(
            f"OS keyring을 사용할 수 없습니다. {_SECRET_KEY_ENV}에 Fernet 키를 설정하세요"
        ) from exc


def _fernetForWrite(path: Path) -> tuple[Any, str]:
    if os.environ.get(_SECRET_KEY_ENV, "").strip():
        return _fernetFromEnvironment(), "fernet-env"
    return _keyringFernet(path, create=True), "fernet-keyring"


def _fernetForRead(path: Path, backend: str) -> Any:
    if backend in {"fernet", "fernet-env"}:
        return _fernetFromEnvironment()
    if backend == "fernet-keyring":
        return _keyringFernet(path, create=False)
    raise SecretStoreCorruptError(f"지원하지 않는 Fernet backend: {backend}")


def _preferredFernetBackend(data: dict[str, dict[str, str]]) -> str | None:
    backends = {
        "fernet-env" if entry["backend"] == "fernet" else entry["backend"]
        for entry in data.values()
        if entry["backend"] in {"fernet", "fernet-env", "fernet-keyring"}
    }
    if len(backends) == 1:
        return next(iter(backends))
    if "fernet-env" in backends and os.environ.get(_SECRET_KEY_ENV, "").strip():
        return "fernet-env"
    if "fernet-keyring" in backends:
        return "fernet-keyring"
    return None


def _decodeLegacyPlain(encoded: str) -> str:
    try:
        return base64.b64decode(encoded.encode("ascii"), validate=True).decode("utf-8")
    except (binascii.Error, UnicodeError, ValueError) as exc:
        raise SecretStoreCorruptError("구버전 평문 secret 형식이 손상되었습니다") from exc


def _syncDirectory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directoryFd = os.open(path, flags)
    try:
        os.fsync(directoryFd)
    finally:
        os.close(directoryFd)


def _wrapWriteError(error: BaseException, *, committed: bool) -> BaseException:
    if not isinstance(error, OSError):
        return error
    if committed:
        message = "secret store 교체 후 권한 또는 내구성 동기화 실패"
    else:
        message = "secret store 원자 저장 실패"
    return SecretStoreWriteError(message, committed=committed)


def _cleanupTemporaryFile(path: str | None, *, committed: bool) -> SecretStoreWriteError | None:
    if path is None:
        return None
    try:
        os.unlink(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        error = SecretStoreWriteError("secret store 임시 파일 정리 실패", committed=committed)
        error.__cause__ = exc
        return error
    return None


def _combinedFailure(
    message: str,
    first: BaseException,
    second: BaseException,
    *,
    committed: bool,
) -> BaseException:
    if isinstance(first, Exception) and isinstance(second, Exception):
        return SecretStoreCompositeError(message, (first, second), committed=committed)
    return BaseExceptionGroup(message, [first, second])


@dataclass
class _MutationState:
    committed: bool = False


@contextmanager
def _mutationLock(path: Path) -> Iterator[_MutationState]:
    normalized = path.expanduser().resolve(strict=False)
    lockPath = normalized.with_name(f"{normalized.name}.lock")
    try:
        from filelock import FileLock, Timeout
    except ImportError as exc:
        raise SecretStoreBackendError("secret store 잠금 backend인 filelock이 필요합니다") from exc

    try:
        lockPath.parent.mkdir(parents=True, exist_ok=True)
        lock = FileLock(lockPath, timeout=_LOCK_TIMEOUT_SECONDS)
        lock.acquire()
    except Timeout as exc:
        raise SecretStoreLockError(f"secret store 잠금 획득 시간 초과: {lockPath}") from exc
    except Exception as exc:
        raise SecretStoreLockError(f"secret store 잠금 획득 실패: {lockPath}") from exc

    try:
        if not _isWindows():
            lockPath.chmod(0o600)
    except Exception as permissionError:
        try:
            lock.release()
        except Exception as releaseError:
            wrappedPermission = SecretStoreLockError(
                f"secret store 잠금 권한 설정 실패: {lockPath}",
                committed=False,
            )
            wrappedPermission.__cause__ = permissionError
            wrappedRelease = SecretStoreLockError(
                f"secret store 잠금 해제 실패: {lockPath}",
                committed=False,
            )
            wrappedRelease.__cause__ = releaseError
            raise SecretStoreCompositeError(
                "secret store 잠금 권한 설정과 해제가 함께 실패했습니다",
                (wrappedPermission, wrappedRelease),
                committed=False,
            ) from None
        raise SecretStoreLockError(f"secret store 잠금 권한 설정 실패: {lockPath}") from permissionError

    state = _MutationState()
    try:
        yield state
    except BaseException as operationError:
        try:
            lock.release()
        except Exception as exc:
            committed = state.committed or bool(getattr(operationError, "committed", False))
            unlockError = SecretStoreLockError(
                f"secret store 잠금 해제 실패: {lockPath}",
                committed=committed,
            )
            unlockError.__cause__ = exc
            raise _combinedFailure(
                "secret store 작업과 잠금 해제가 함께 실패했습니다",
                operationError,
                unlockError,
                committed=committed,
            ) from None
        raise
    else:
        try:
            lock.release()
        except Exception as exc:
            raise SecretStoreLockError(
                f"secret store 잠금 해제 실패: {lockPath}",
                committed=state.committed,
            ) from exc


def _windowsCrypto() -> tuple[Any, ...]:
    global _WINDOWS_CRYPTO_STATE
    if _WINDOWS_CRYPTO_STATE is not None:
        return _WINDOWS_CRYPTO_STATE
    with _WINDOWS_CRYPTO_INIT_LOCK:
        if _WINDOWS_CRYPTO_STATE is not None:
            return _WINDOWS_CRYPTO_STATE

        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            """CryptProtectData/CryptUnprotectData 입출력 버퍼."""

            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(DATA_BLOB),
            wintypes.LPCWSTR,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(DATA_BLOB),
        ]
        crypt32.CryptProtectData.restype = wintypes.BOOL
        crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(DATA_BLOB),
            ctypes.POINTER(wintypes.LPWSTR),
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(DATA_BLOB),
        ]
        crypt32.CryptUnprotectData.restype = wintypes.BOOL
        kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
        kernel32.LocalFree.restype = wintypes.HLOCAL
        _WINDOWS_CRYPTO_STATE = ctypes, wintypes, DATA_BLOB, crypt32, kernel32
    return _WINDOWS_CRYPTO_STATE


def _freeWindowsPointers(ctypes: Any, wintypes: Any, kernel32: Any, *pointers: Any) -> None:
    errors: list[Exception] = []
    for pointer in pointers:
        if not pointer:
            continue
        if kernel32.LocalFree(ctypes.cast(pointer, wintypes.HLOCAL)):
            errors.append(ctypes.WinError())
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise SecretStoreCompositeError(
            "Windows DPAPI native buffer 정리에 실패했습니다",
            tuple(errors),
            committed=False,
        )


def _protectWindows(data: bytes) -> bytes:
    """Windows DPAPI CryptProtectData — 사용자 컨텍스트로 암호화."""
    ctypes, wintypes, DATA_BLOB, crypt32, kernel32 = _windowsCrypto()
    buffer = ctypes.create_string_buffer(data, len(data))
    data_in = DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    data_out = DATA_BLOB()
    if not crypt32.CryptProtectData(ctypes.byref(data_in), "dartlab", None, None, None, 0, ctypes.byref(data_out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(data_out.pbData, data_out.cbData)
    finally:
        _freeWindowsPointers(ctypes, wintypes, kernel32, data_out.pbData)


def _unprotectWindows(data: bytes) -> bytes:
    """Windows DPAPI CryptUnprotectData — 사용자 컨텍스트로 복호화."""
    ctypes, wintypes, DATA_BLOB, crypt32, kernel32 = _windowsCrypto()
    buffer = ctypes.create_string_buffer(data, len(data))
    data_in = DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    data_out = DATA_BLOB()
    description = wintypes.LPWSTR()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(data_in),
        ctypes.byref(description),
        None,
        None,
        None,
        0,
        ctypes.byref(data_out),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(data_out.pbData, data_out.cbData)
    finally:
        _freeWindowsPointers(ctypes, wintypes, kernel32, description, data_out.pbData)


def getSecretStore() -> SecretStore:
    """기본 경로의 SecretStore 인스턴스 반환."""
    return SecretStore()
