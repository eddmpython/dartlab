"""SecretStore의 원자성, 보안 backend, 오류 투명성 회귀."""

from __future__ import annotations

import json
import multiprocessing
import os
import queue
import shutil
import stat
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import filelock
import pytest
from cryptography.fernet import Fernet

import dartlab.core.providers.secrets as secretModule
from dartlab.core.providers.secrets import (
    SecretStore,
    SecretStoreBackendError,
    SecretStoreCompositeError,
    SecretStoreCorruptError,
    SecretStoreDecryptError,
    SecretStoreError,
    SecretStoreLockError,
    SecretStoreWriteError,
)

pytestmark = pytest.mark.unit


def _useFastDpapi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: True)
    monkeypatch.setattr(secretModule, "_protectWindows", lambda raw: raw)
    monkeypatch.setattr(secretModule, "_unprotectWindows", lambda raw: raw)


def _saveFromProcess(path: str, name: str, barrier, failures) -> None:
    secretModule._usesDpapi = lambda: True
    secretModule._protectWindows = lambda raw: raw
    secretModule._unprotectWindows = lambda raw: raw
    store = SecretStore(Path(path))
    originalLoad = store._load

    def coordinatedLoad():
        data = originalLoad()
        try:
            barrier.wait(timeout=0.2)
        except threading.BrokenBarrierError:
            pass
        return data

    store._load = coordinatedLoad
    try:
        store.set(name, f"value-{name}")
    except BaseException as exc:
        failures.put(f"{type(exc).__name__}: {exc}")


def _holdProcessLock(lockPath: str, ready, release) -> None:
    lock = filelock.FileLock(lockPath)
    with lock:
        ready.set()
        release.wait(timeout=10)


def test_concurrent_distinct_updates_are_not_lost(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    path = tmp_path / "secrets.json"
    stores = [SecretStore(path), SecretStore(path)]
    originalLoad = SecretStore._load
    concurrentLoads = threading.Barrier(2)
    failures: list[BaseException] = []

    def coordinatedLoad(store: SecretStore):
        data = originalLoad(store)
        if threading.current_thread() is not threading.main_thread():
            try:
                concurrentLoads.wait(timeout=0.1)
            except threading.BrokenBarrierError:
                pass
        return data

    monkeypatch.setattr(SecretStore, "_load", coordinatedLoad)

    def save(store: SecretStore, name: str) -> None:
        try:
            store.set(name, f"value-{name}")
        except BaseException as exc:  # 테스트 스레드의 실패를 메인 스레드로 전달
            failures.append(exc)

    threads = [threading.Thread(target=save, args=(store, f"key-{index}")) for index, store in enumerate(stores)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert all(not thread.is_alive() for thread in threads)
    assert failures == []
    assert SecretStore(path).keys() == {"key-0", "key-1"}


def test_cross_process_distinct_updates_are_not_lost(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    path = tmp_path / "secrets.json"
    context = multiprocessing.get_context("spawn")
    concurrentLoads = context.Barrier(2)
    failures = context.Queue()
    processes = [
        context.Process(target=_saveFromProcess, args=(str(path), f"key-{index}", concurrentLoads, failures))
        for index in range(2)
    ]

    try:
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=10)

        assert all(not process.is_alive() for process in processes)
        assert [process.exitcode for process in processes] == [0, 0]
        try:
            failure = failures.get_nowait()
        except queue.Empty:
            failure = None
        assert failure is None
        assert SecretStore(path).keys() == {"key-0", "key-1"}
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)


def test_actual_process_lock_timeout_is_typed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")
    lockPath = store.path.with_name(f"{store.path.name}.lock")
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    release = context.Event()
    process = context.Process(target=_holdProcessLock, args=(str(lockPath), ready, release))
    process.start()
    try:
        assert ready.wait(timeout=5)
        monkeypatch.setattr(secretModule, "_LOCK_TIMEOUT_SECONDS", 0.05)

        with pytest.raises(SecretStoreLockError, match="시간 초과"):
            store.set("api-key", "secret")
    finally:
        release.set()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)

    assert process.exitcode == 0


@pytest.mark.skipif(os.name != "nt", reason="Windows DPAPI 실제 회귀")
def test_windows_dpapi_parallel_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secretModule, "_WINDOWS_CRYPTO_STATE", None)

    def roundtrip(index: int) -> bool:
        value = f"non-sensitive-probe-{index}"
        store = SecretStore(tmp_path / f"secrets-{index}.json")
        store.set("probe", value)
        return store.get("probe") == value and value not in store.path.read_text(encoding="utf-8")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(roundtrip, range(32)))

    assert results == [True] * 32


@pytest.mark.skipif(os.name == "nt", reason="POSIX 권한과 directory fsync 회귀")
def test_posix_store_and_lock_permissions_are_owner_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DARTLAB_SECRET_KEY", Fernet.generate_key().decode("ascii"))
    store = SecretStore(tmp_path / "secrets.json")

    store.set("api-key", "secret")

    lockPath = store.path.with_name(f"{store.path.name}.lock")
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert stat.S_IMODE(lockPath.stat().st_mode) == 0o600


def test_non_windows_requires_explicit_fernet_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.delenv("DARTLAB_SECRET_KEY", raising=False)

    def unavailableKeyring(_path: Path, *, create: bool):
        raise SecretStoreBackendError("DARTLAB_SECRET_KEY 필요")

    monkeypatch.setattr(secretModule, "_keyringFernet", unavailableKeyring)
    store = SecretStore(tmp_path / "secrets.json")

    with pytest.raises(SecretStoreError, match="DARTLAB_SECRET_KEY"):
        store.set("api-key", "secret-value")


def test_non_windows_fernet_never_writes_plaintext(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.setenv("DARTLAB_SECRET_KEY", Fernet.generate_key().decode("ascii"))
    store = SecretStore(tmp_path / "secrets.json")

    store.set("api-key", "secret-value")

    raw = store.path.read_text(encoding="utf-8")
    entry = json.loads(raw)["api-key"]
    assert entry["backend"] == "fernet-env"
    assert "secret-value" not in raw
    assert store.get("api-key") == "secret-value"


def test_non_windows_uses_keyring_master_key_when_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.delenv("DARTLAB_SECRET_KEY", raising=False)
    fernet = Fernet(Fernet.generate_key())
    monkeypatch.setattr(secretModule, "_keyringFernet", lambda _path, *, create: fernet)
    store = SecretStore(tmp_path / "secrets.json")

    store.set("api-key", "secret-value")

    raw = store.path.read_text(encoding="utf-8")
    assert json.loads(raw)["api-key"]["backend"] == "fernet-keyring"
    assert "secret-value" not in raw
    assert store.get("api-key") == "secret-value"


def test_keyring_master_key_is_reused_across_store_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class SecureBackend:
        def get_password(self, service: str, account: str) -> str | None:
            return passwords.get((service, account))

        def set_password(self, service: str, account: str, value: str) -> None:
            passwords[(service, account)] = value
            writes.append((service, account))

    passwords: dict[tuple[str, str], str] = {}
    writes: list[tuple[str, str]] = []
    fakeKeyring = SimpleNamespace(get_keyring=lambda: SecureBackend())
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.delenv("DARTLAB_SECRET_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "keyring", fakeKeyring)
    monkeypatch.setattr(secretModule, "_isTrustedKeyringBackend", lambda _backend: True)
    monkeypatch.setattr(secretModule, "_keyringLockTarget", lambda: tmp_path / "master")
    first = SecretStore(tmp_path / "first.json")
    second = SecretStore(tmp_path / "second.json")

    first.set("a", "one")
    monkeypatch.setenv("DARTLAB_SECRET_KEY", Fernet.generate_key().decode("ascii"))
    first.set("b", "two")
    monkeypatch.delenv("DARTLAB_SECRET_KEY")
    second.set("a", "three")
    shutil.copyfile(first.path, second.path)

    assert first.get("a") == "one"
    assert first.get("b") == "two"
    assert second.get("a") == "one"
    assert second.get("b") == "two"
    assert len(writes) == 1
    assert {entry["backend"] for entry in json.loads(first.path.read_text(encoding="utf-8")).values()} == {
        "fernet-keyring"
    }


def test_missing_keyring_master_blocks_write_without_changing_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class SecureBackend:
        def get_password(self, service: str, account: str) -> str | None:
            return passwords.get((service, account))

        def set_password(self, service: str, account: str, value: str) -> None:
            passwords[(service, account)] = value

    passwords: dict[tuple[str, str], str] = {}
    fakeKeyring = SimpleNamespace(get_keyring=lambda: SecureBackend())
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.delenv("DARTLAB_SECRET_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "keyring", fakeKeyring)
    monkeypatch.setattr(secretModule, "_isTrustedKeyringBackend", lambda _backend: True)
    monkeypatch.setattr(secretModule, "_keyringLockTarget", lambda: tmp_path / "master")
    store = SecretStore(tmp_path / "secrets.json")
    store.set("a", "one")
    stored = json.loads(store.path.read_text(encoding="utf-8"))
    stored["legacy"] = {"backend": "plain", "value": "bGVnYWN5"}
    store.path.write_text(json.dumps(stored), encoding="utf-8")
    original = store.path.read_bytes()
    sentinel = secretModule._keyringSentinelPath()
    originalSentinel = sentinel.read_bytes()
    passwords.clear()
    emptyStore = SecretStore(tmp_path / "empty.json")
    plainStore = SecretStore(tmp_path / "plain.json")
    plainStore.path.write_text(
        json.dumps({"legacy": {"backend": "plain", "value": "bGVnYWN5"}}),
        encoding="utf-8",
    )
    originalPlain = plainStore.path.read_bytes()

    with pytest.raises(SecretStoreBackendError, match="master key"):
        store.set("b", "two")
    with pytest.raises(SecretStoreBackendError, match="master key"):
        store.get("legacy")
    with pytest.raises(SecretStoreBackendError, match="master key"):
        emptyStore.set("new", "value")
    with pytest.raises(SecretStoreBackendError, match="master key"):
        plainStore.get("legacy")

    assert store.path.read_bytes() == original
    assert not emptyStore.path.exists()
    assert plainStore.path.read_bytes() == originalPlain
    assert sentinel.read_bytes() == originalSentinel
    assert passwords == {}


def test_insecure_keyring_backend_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class PlaintextBackend:
        pass

    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.delenv("DARTLAB_SECRET_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "keyring", SimpleNamespace(get_keyring=lambda: PlaintextBackend()))

    with pytest.raises(SecretStoreBackendError, match="안전한 OS keyring"):
        SecretStore(tmp_path / "secrets.json").set("api-key", "secret")


def test_legacy_plain_backend_is_atomically_migrated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "secrets.json"
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.setenv("DARTLAB_SECRET_KEY", Fernet.generate_key().decode("ascii"))
    path.write_text(
        json.dumps({"api-key": {"backend": "plain", "value": "c2VjcmV0"}}),
        encoding="utf-8",
    )

    assert SecretStore(path).get("api-key") == "secret"
    raw = path.read_text(encoding="utf-8")
    entry = json.loads(raw)["api-key"]
    assert entry["backend"] == "fernet-env"
    assert "c2VjcmV0" not in raw


def test_legacy_plain_backend_remains_unchanged_without_secure_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "secrets.json"
    original = json.dumps({"api-key": {"backend": "plain", "value": "c2VjcmV0"}})
    path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.delenv("DARTLAB_SECRET_KEY", raising=False)

    def unavailableKeyring(_path: Path, *, create: bool):
        raise SecretStoreBackendError("안전한 backend 없음")

    monkeypatch.setattr(secretModule, "_keyringFernet", unavailableKeyring)

    with pytest.raises(SecretStoreBackendError, match="안전한 backend"):
        SecretStore(path).get("api-key")

    assert path.read_text(encoding="utf-8") == original


def test_malformed_entry_is_not_silently_dropped(tmp_path: Path) -> None:
    path = tmp_path / "secrets.json"
    path.write_text(json.dumps({"api-key": {"backend": "dpapi"}}), encoding="utf-8")

    with pytest.raises(SecretStoreError, match="엔트리 형식"):
        SecretStore(path).keys()


def test_entry_with_extra_fields_is_a_typed_corruption(tmp_path: Path) -> None:
    path = tmp_path / "secrets.json"
    path.write_text(
        json.dumps({"api-key": {"backend": "dpapi", "value": "eA==", "extra": "unexpected"}}),
        encoding="utf-8",
    )

    with pytest.raises(SecretStoreCorruptError, match="엔트리 형식"):
        SecretStore(path).get("api-key")


def test_atomic_replace_failure_is_wrapped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")

    def failReplace(_source, _target):
        raise PermissionError("locked")

    monkeypatch.setattr(secretModule.os, "replace", failReplace)

    with pytest.raises(SecretStoreWriteError, match="원자 저장 실패") as exc:
        store.set("api-key", "secret")

    assert isinstance(exc.value.__cause__, PermissionError)
    assert exc.value.committed is False


def test_post_replace_sync_failure_reports_committed_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    monkeypatch.setattr(secretModule, "_isWindows", lambda: False)
    store = SecretStore(tmp_path / "secrets.json")

    def failSync(_path: Path) -> None:
        raise OSError("sync failed")

    monkeypatch.setattr(secretModule, "_syncDirectory", failSync)

    with pytest.raises(SecretStoreWriteError, match="교체 후") as exc:
        store.set("api-key", "secret")

    assert exc.value.committed is True
    assert store.get("api-key") == "secret"


def test_successful_write_with_release_failure_reports_committed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")

    class ReleaseFails:
        def __init__(self, path, **_kwargs) -> None:
            self.path = Path(path)

        def acquire(self) -> None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.touch()

        def release(self) -> None:
            raise OSError("release failed")

    monkeypatch.setattr(filelock, "FileLock", ReleaseFails)

    with pytest.raises(SecretStoreLockError, match="잠금 해제 실패") as exc:
        store.set("api-key", "secret")

    assert exc.value.committed is True
    assert store.get("api-key") == "secret"


def test_operation_and_release_failure_remain_in_secret_store_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")

    class ReleaseFails:
        def __init__(self, path, **_kwargs) -> None:
            self.path = Path(path)

        def acquire(self) -> None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.touch()

        def release(self) -> None:
            raise OSError("release failed")

    monkeypatch.setattr(filelock, "FileLock", ReleaseFails)

    def failReplace(*_args) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(secretModule.os, "replace", failReplace)

    with pytest.raises(SecretStoreCompositeError) as exc:
        store.set("api-key", "secret")

    assert exc.value.committed is False
    assert len(exc.value.errors) == 2
    assert all(isinstance(error, SecretStoreError) for error in exc.value.errors)


def test_write_and_temp_cleanup_failure_remain_in_secret_store_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")

    def failReplace(*_args) -> None:
        raise OSError("replace failed")

    def failUnlink(*_args) -> None:
        raise OSError("unlink failed")

    monkeypatch.setattr(secretModule.os, "replace", failReplace)
    monkeypatch.setattr(secretModule.os, "unlink", failUnlink)

    with pytest.raises(SecretStoreCompositeError) as exc:
        store.set("api-key", "secret")

    assert exc.value.committed is False
    assert len(exc.value.errors) == 2
    assert all(isinstance(error, SecretStoreError) for error in exc.value.errors)


def test_lock_timeout_is_typed_and_chained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")

    def failAcquire(_self):
        raise filelock.Timeout(str(store.path.with_name(f"{store.path.name}.lock")))

    monkeypatch.setattr(filelock.FileLock, "acquire", failAcquire)

    with pytest.raises(SecretStoreLockError, match="시간 초과") as exc:
        store.set("api-key", "secret")

    assert isinstance(exc.value.__cause__, filelock.Timeout)


def test_invalid_dpapi_payload_is_a_typed_decrypt_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    path = tmp_path / "secrets.json"
    path.write_text(json.dumps({"api-key": {"backend": "dpapi", "value": "***"}}), encoding="utf-8")

    with pytest.raises(SecretStoreDecryptError, match="복호화 실패") as exc:
        SecretStore(path).get("api-key")

    assert isinstance(exc.value.__cause__, Exception)


def test_wrong_fernet_key_is_a_typed_decrypt_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: False)
    monkeypatch.setenv("DARTLAB_SECRET_KEY", Fernet.generate_key().decode("ascii"))
    store = SecretStore(tmp_path / "secrets.json")
    store.set("api-key", "secret")
    monkeypatch.setenv("DARTLAB_SECRET_KEY", Fernet.generate_key().decode("ascii"))

    with pytest.raises(SecretStoreDecryptError, match="복호화 실패"):
        store.get("api-key")


def test_non_mapping_json_secret_is_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _useFastDpapi(monkeypatch)
    store = SecretStore(tmp_path / "secrets.json")
    store.set("oauth", json.dumps(["not", "a", "mapping"]))

    with pytest.raises(SecretStoreError, match="JSON secret 형식"):
        store.getJson("oauth")
