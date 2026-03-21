from __future__ import annotations

import base64
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _dartlab_home() -> Path:
    raw = os.environ.get("DARTLAB_HOME")
    if raw:
        return Path(raw)
    return Path.home() / ".dartlab"


@dataclass(frozen=True)
class SecretEntry:
    backend: str
    value: str


class SecretStoreError(RuntimeError):
    pass


class SecretStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (_dartlab_home() / "secrets.json")

    def _load(self) -> dict[str, dict[str, str]]:
        if not self.path.exists():
            return {}
        raw = self.path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretStoreError("secret store JSON 파싱 실패") from exc
        if not isinstance(data, dict):
            raise SecretStoreError("secret store 형식이 올바르지 않습니다")
        return {
            str(key): value
            for key, value in data.items()
            if isinstance(value, dict) and isinstance(value.get("backend"), str) and isinstance(value.get("value"), str)
        }

    def _save(self, data: dict[str, dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(data, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            fd = -1
            tmp = Path(tmp_path)
            if os.name != "nt":
                tmp.chmod(0o600)
            tmp.replace(self.path)
        finally:
            if fd >= 0:
                os.close(fd)
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def get(self, name: str) -> str | None:
        data = self._load()
        entry = data.get(name)
        if not entry:
            return None
        return self._decode_entry(SecretEntry(**entry))

    def set(self, name: str, value: str) -> None:
        data = self._load()
        entry = self._encode_entry(value)
        data[name] = {"backend": entry.backend, "value": entry.value}
        self._save(data)

    def delete(self, name: str) -> None:
        data = self._load()
        if name in data:
            data.pop(name, None)
            self._save(data)

    def has(self, name: str) -> bool:
        return self.get(name) is not None

    def get_json(self, name: str) -> dict[str, Any] | None:
        raw = self.get(name)
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretStoreError("JSON secret 파싱 실패") from exc
        return data if isinstance(data, dict) else None

    def set_json(self, name: str, value: dict[str, Any]) -> None:
        self.set(name, json.dumps(value, ensure_ascii=False))

    def _encode_entry(self, value: str) -> SecretEntry:
        raw = value.encode("utf-8")
        if os.name == "nt":
            encrypted = _protect_windows(raw)
            return SecretEntry(backend="dpapi", value=base64.b64encode(encrypted).decode("ascii"))
        return SecretEntry(backend="plain", value=base64.b64encode(raw).decode("ascii"))

    def _decode_entry(self, entry: SecretEntry) -> str:
        raw = base64.b64decode(entry.value.encode("ascii"))
        if entry.backend == "dpapi":
            decrypted = _unprotect_windows(raw)
            return decrypted.decode("utf-8")
        if entry.backend == "plain":
            return raw.decode("utf-8")
        raise SecretStoreError(f"지원하지 않는 secret backend: {entry.backend}")


def _protect_windows(data: bytes) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
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

    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL

    buffer = ctypes.create_string_buffer(data, len(data))
    data_in = DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    data_out = DATA_BLOB()
    if not crypt32.CryptProtectData(ctypes.byref(data_in), "dartlab", None, None, None, 0, ctypes.byref(data_out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(data_out.pbData, data_out.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(data_out.pbData, wintypes.HLOCAL))


def _unprotect_windows(data: bytes) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

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
        if description:
            kernel32.LocalFree(ctypes.cast(description, wintypes.HLOCAL))
        kernel32.LocalFree(ctypes.cast(data_out.pbData, wintypes.HLOCAL))


def get_secret_store() -> SecretStore:
    return SecretStore()
