"""파일 기반 비밀 저장소 — Windows DPAPI 또는 plain base64. core 강등 SSOT.

이전: src/dartlab/ai/settings/secrets.py (0.10 까지 shim 유지)
사유: SecretStore 는 cross-cutting primitive (ai/cli/server/credentials 모두 사용).
외부 L2 의존 0, stdlib + ctypes 만.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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


class SecretStore:
    """파일 기반 비밀 저장소 — Windows DPAPI 또는 plain base64."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (dartlabHome() / "secrets.json")

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
        """이름으로 비밀 값 조회. 없으면 None."""
        data = self._load()
        entry = data.get(name)
        if not entry:
            return None
        return self._decodeEntry(SecretEntry(**entry))

    def set(self, name: str, value: str) -> None:
        """비밀 값 저장 (암호화 후 파일에 기록)."""
        data = self._load()
        entry = self._encodeEntry(value)
        data[name] = {"backend": entry.backend, "value": entry.value}
        self._save(data)

    def delete(self, name: str) -> None:
        """이름에 해당하는 비밀 값 삭제."""
        data = self._load()
        if name in data:
            data.pop(name, None)
            self._save(data)

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

    def getJson(self, name: str) -> dict[str, Any] | None:
        """JSON으로 저장된 비밀 값을 dict로 파싱하여 반환."""
        raw = self.get(name)
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretStoreError("JSON secret 파싱 실패") from exc
        return data if isinstance(data, dict) else None

    def setJson(self, name: str, value: dict[str, Any]) -> None:
        """dict를 JSON 직렬화하여 비밀 값으로 저장."""
        self.set(name, json.dumps(value, ensure_ascii=False))

    def _encodeEntry(self, value: str) -> SecretEntry:
        raw = value.encode("utf-8")
        if os.name == "nt":
            encrypted = _protectWindows(raw)
            return SecretEntry(backend="dpapi", value=base64.b64encode(encrypted).decode("ascii"))
        return SecretEntry(backend="plain", value=base64.b64encode(raw).decode("ascii"))

    def _decodeEntry(self, entry: SecretEntry) -> str:
        raw = base64.b64decode(entry.value.encode("ascii"))
        if entry.backend == "dpapi":
            decrypted = _unprotectWindows(raw)
            return decrypted.decode("utf-8")
        if entry.backend == "plain":
            return raw.decode("utf-8")
        raise SecretStoreError(f"지원하지 않는 secret backend: {entry.backend}")


def _protectWindows(data: bytes) -> bytes:
    """Windows DPAPI CryptProtectData — 사용자 컨텍스트로 암호화."""
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        """CryptProtectData/CryptUnprotectData 입출력 버퍼 (cbData + pbData)."""

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


def _unprotectWindows(data: bytes) -> bytes:
    """Windows DPAPI CryptUnprotectData — 사용자 컨텍스트로 복호화."""
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        """CryptProtectData/CryptUnprotectData 입출력 버퍼 (cbData + pbData)."""

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


def getSecretStore() -> SecretStore:
    """기본 경로의 SecretStore 인스턴스 반환."""
    return SecretStore()
