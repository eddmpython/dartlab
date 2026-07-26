"""OS-enforced private storage permissions for continuation plaintext CAS."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Never

from .contracts import ContinuationError

_SYSTEM_SIDS = {"SY", "S-1-5-18"}


def _raiseSecurityFailure() -> Never:
    raise ContinuationError("CONTINUATION_SECURITY_FAILED")


def _windowsApis():
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    return ctypes, wintypes, advapi32, kernel32


def currentWindowsUserSid() -> str:
    """현재 Windows process token의 user SID를 문자열로 반환한다.

    Capabilities:
        환경변수가 아닌 실제 process access token에서 현재 principal을 식별한다.

    Args:
        없음.

    Returns:
        ``S-1-*`` 형식의 current user SID.

    Raises:
        ContinuationError: token 또는 SID 조회가 실패했을 때.

    Example:
        ``sid = currentWindowsUserSid()``.

    Guide:
        private DACL 생성과 재검증의 identity source로만 사용한다.

    When:
        Windows private path를 설정하거나 검사하기 직전에 호출한다.

    How:
        process token의 TOKEN_USER를 읽고 SID 문자열로 변환한다.

    SeeAlso:
        ``securePrivatePath``, ``windowsDaclSids``.

    Requires:
        Windows process token query 권한.

    AIContext:
        사용자명 대신 stable SID를 써 이름 해석과 locale 의존성을 제거한다.
    """
    if os.name != "nt":
        _raiseSecurityFailure()
    try:
        ctypes, wintypes, advapi32, kernel32 = _windowsApis()

        class _SidAndAttributes(ctypes.Structure):
            _fields_ = [("Sid", wintypes.LPVOID), ("Attributes", wintypes.DWORD)]

        class _TokenUser(ctypes.Structure):
            _fields_ = [("User", _SidAndAttributes)]

        token = wintypes.HANDLE()
        advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
            _raiseSecurityFailure()
        try:
            required = wintypes.DWORD()
            advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
            if required.value == 0:
                _raiseSecurityFailure()
            buffer = ctypes.create_string_buffer(required.value)
            if not advapi32.GetTokenInformation(token, 1, buffer, required, ctypes.byref(required)):
                _raiseSecurityFailure()
            tokenUser = ctypes.cast(buffer, ctypes.POINTER(_TokenUser)).contents
            sidString = wintypes.LPWSTR()
            advapi32.ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]
            advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
            if not advapi32.ConvertSidToStringSidW(tokenUser.User.Sid, ctypes.byref(sidString)):
                _raiseSecurityFailure()
            try:
                sid = str(sidString.value)
            finally:
                kernel32.LocalFree(sidString)
        finally:
            kernel32.CloseHandle(token)
    except ContinuationError:
        raise
    except Exception:
        _raiseSecurityFailure()
    if re.fullmatch(r"S-1(?:-\d+)+", sid) is None:
        _raiseSecurityFailure()
    return sid


def _windowsDaclSddl(path: Path) -> str:
    if os.name != "nt":
        _raiseSecurityFailure()
    try:
        ctypes, wintypes, advapi32, kernel32 = _windowsApis()
        securityDescriptor = wintypes.LPVOID()
        dacl = wintypes.LPVOID()
        advapi32.GetNamedSecurityInfoW.argtypes = [
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
        ]
        advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
        result = advapi32.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000004,
            None,
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(securityDescriptor),
        )
        if result != 0:
            _raiseSecurityFailure()
        try:
            sddlPointer = wintypes.LPWSTR()
            length = wintypes.ULONG()
            advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
                wintypes.LPVOID,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(wintypes.LPWSTR),
                ctypes.POINTER(wintypes.ULONG),
            ]
            advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = wintypes.BOOL
            if not advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(
                securityDescriptor,
                1,
                0x00000004,
                ctypes.byref(sddlPointer),
                ctypes.byref(length),
            ):
                _raiseSecurityFailure()
            try:
                return str(sddlPointer.value)
            finally:
                kernel32.LocalFree(sddlPointer)
        finally:
            kernel32.LocalFree(securityDescriptor)
    except ContinuationError:
        raise
    except Exception:
        _raiseSecurityFailure()


def _windowsOwnerSid(path: Path) -> str:
    """Windows path의 object owner SID를 native security descriptor에서 읽는다."""

    if os.name != "nt":
        _raiseSecurityFailure()
    try:
        ctypes, wintypes, advapi32, kernel32 = _windowsApis()
        securityDescriptor = wintypes.LPVOID()
        owner = wintypes.LPVOID()
        advapi32.GetNamedSecurityInfoW.argtypes = [
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.LPVOID),
        ]
        advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
        result = advapi32.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000001,
            ctypes.byref(owner),
            None,
            None,
            None,
            ctypes.byref(securityDescriptor),
        )
        if result != 0 or not owner:
            _raiseSecurityFailure()
        try:
            sidString = wintypes.LPWSTR()
            advapi32.ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]
            advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
            if not advapi32.ConvertSidToStringSidW(owner, ctypes.byref(sidString)):
                _raiseSecurityFailure()
            try:
                sid = str(sidString.value)
            finally:
                kernel32.LocalFree(sidString)
        finally:
            kernel32.LocalFree(securityDescriptor)
    except ContinuationError:
        raise
    except Exception:
        _raiseSecurityFailure()
    if re.fullmatch(r"S-1(?:-\d+)+", sid) is None:
        _raiseSecurityFailure()
    return sid


def _resolvePrivateRoot(path: Path) -> Path:
    """Resolve 전에 existing symlink와 junction이 없는 private root 경로를 고정한다."""

    try:
        absolute = Path(os.path.abspath(Path(path).expanduser()))
        for component in (absolute, *absolute.parents):
            isJunction = getattr(component, "is_junction", None)
            if component.is_symlink() or (callable(isJunction) and isJunction()):
                _raiseSecurityFailure()
        return absolute.resolve()
    except ContinuationError:
        raise
    except Exception:
        _raiseSecurityFailure()


def windowsDaclSids(path: Path) -> tuple[str, ...]:
    """Windows DACL의 explicit allow SID를 검증해 반환한다.

    Capabilities:
        protected DACL, explicit ACE, full control 권한을 동시에 검증한다.

    Args:
        path: 검사할 private directory 또는 file.

    Returns:
        explicit full-control allow SID tuple.

    Raises:
        ContinuationError: protected DACL 또는 ACE가 예상과 다를 때.

    Example:
        ``sids = windowsDaclSids(path)``.

    Guide:
        반환 SID 집합은 current user와 SYSTEM exact match에 사용한다.

    When:
        Windows private path의 ACL 설정 결과를 fail closed 검사할 때 호출한다.

    How:
        security descriptor를 SDDL로 변환해 allow ACE와 권한을 파싱한다.

    SeeAlso:
        ``currentWindowsUserSid``, ``verifyPrivatePath``.

    Requires:
        Windows security descriptor read 권한.

    AIContext:
        chmod 결과가 아니라 Windows native DACL을 confidentiality 근거로 남긴다.
    """
    sddl = _windowsDaclSddl(path)
    if not sddl.startswith("D:P"):
        _raiseSecurityFailure()
    aces = re.findall(r"\(([^()]*)\)", sddl)
    if not aces:
        _raiseSecurityFailure()
    sids = []
    for ace in aces:
        fields = ace.split(";")
        if len(fields) != 6:
            _raiseSecurityFailure()
        aceType, aceFlags, rights, _objectGuid, _inheritGuid, sid = fields
        if aceType != "A" or "ID" in aceFlags or rights not in {"FA", "0x1f01ff"}:
            _raiseSecurityFailure()
        sids.append(sid)
    return tuple(sids)


def securePrivatePath(path: Path) -> None:
    """현재 사용자와 SYSTEM만 접근하도록 path 보안을 설정하고 검증한다.

    Capabilities:
        Windows protected DACL 또는 POSIX owner-only mode를 fail closed 적용한다.

    Args:
        path: 이미 존재하는 directory 또는 file.

    Returns:
        없음.

    Raises:
        ContinuationError: 보안 설정 또는 재검증이 실패했을 때.

    Example:
        ``securePrivatePath(privateRoot)``.

    Guide:
        private query와 cursor를 기록하기 전에 호출한다.

    When:
        control root, CAS directory, CAS object를 생성한 직후 호출한다.

    How:
        Windows는 inheritance를 제거한 DACL을 설정하고 다시 읽어 SID를 검증한다.

    SeeAlso:
        ``verifyPrivatePath``.

    Requires:
        path owner가 DACL 또는 POSIX mode를 변경할 수 있어야 한다.

    AIContext:
        Windows ``chmod``를 confidentiality 근거로 사용하지 않는다.
    """
    path = Path(path)
    if not path.exists() or path.is_symlink():
        _raiseSecurityFailure()
    if os.name == "nt":
        try:
            ctypes, wintypes, advapi32, kernel32 = _windowsApis()
            userSid = currentWindowsUserSid()
            inherit = "OICI" if path.is_dir() else ""
            sddl = f"D:P(A;{inherit};FA;;;SY)(A;{inherit};FA;;;{userSid})"
            securityDescriptor = wintypes.LPVOID()
            size = wintypes.ULONG()
            advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                ctypes.POINTER(wintypes.LPVOID),
                ctypes.POINTER(wintypes.ULONG),
            ]
            advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
            if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                sddl,
                1,
                ctypes.byref(securityDescriptor),
                ctypes.byref(size),
            ):
                _raiseSecurityFailure()
            try:
                daclPresent = wintypes.BOOL()
                daclDefaulted = wintypes.BOOL()
                dacl = wintypes.LPVOID()
                advapi32.GetSecurityDescriptorDacl.argtypes = [
                    wintypes.LPVOID,
                    ctypes.POINTER(wintypes.BOOL),
                    ctypes.POINTER(wintypes.LPVOID),
                    ctypes.POINTER(wintypes.BOOL),
                ]
                advapi32.GetSecurityDescriptorDacl.restype = wintypes.BOOL
                if (
                    not advapi32.GetSecurityDescriptorDacl(
                        securityDescriptor,
                        ctypes.byref(daclPresent),
                        ctypes.byref(dacl),
                        ctypes.byref(daclDefaulted),
                    )
                    or not daclPresent
                ):
                    _raiseSecurityFailure()
                advapi32.SetNamedSecurityInfoW.argtypes = [
                    wintypes.LPWSTR,
                    wintypes.DWORD,
                    wintypes.DWORD,
                    wintypes.LPVOID,
                    wintypes.LPVOID,
                    wintypes.LPVOID,
                    wintypes.LPVOID,
                ]
                advapi32.SetNamedSecurityInfoW.restype = wintypes.DWORD
                result = advapi32.SetNamedSecurityInfoW(
                    str(path),
                    1,
                    0x00000004 | 0x80000000,
                    None,
                    None,
                    dacl,
                    None,
                )
                if result != 0:
                    _raiseSecurityFailure()
            finally:
                kernel32.LocalFree(securityDescriptor)
        except ContinuationError:
            raise
        except Exception:
            _raiseSecurityFailure()
    else:
        try:
            path.chmod(0o700 if path.is_dir() else 0o600)
        except OSError:
            _raiseSecurityFailure()
    verifyPrivatePath(path)


def verifyPrivatePath(path: Path) -> bool:
    """private path의 effective confidentiality 설정을 재검증한다.

    Capabilities:
        Windows exact SID 집합과 POSIX owner-only mode를 OS metadata에서 검증한다.

    Args:
        path: 검사할 directory 또는 file.

    Returns:
        owner-only 또는 current-user와 SYSTEM-only면 True.

    Raises:
        ContinuationError: 다른 principal 접근이나 inheritance가 있을 때.

    Example:
        ``assert verifyPrivatePath(path)``.

    Guide:
        private bytes를 읽기 전과 control-plane integrity audit에서 호출한다.

    When:
        CAS object, SQLite ledger, private directory를 신뢰하기 직전에 호출한다.

    How:
        Windows는 protected DACL을, POSIX는 group과 other mode 부재를 확인한다.

    SeeAlso:
        ``securePrivatePath``, ``windowsDaclSids``.

    Requires:
        path security metadata read 권한.

    AIContext:
        보안 metadata drift를 일반 corruption과 구분된 고정 오류로 차단한다.
    """
    path = Path(path)
    if not path.exists() or path.is_symlink():
        _raiseSecurityFailure()
    if os.name == "nt":
        currentSid = currentWindowsUserSid()
        if _windowsOwnerSid(path) not in {currentSid, "S-1-5-18"}:
            _raiseSecurityFailure()
        sids = windowsDaclSids(path)
        normalized = {"S-1-5-18" if sid == "SY" else sid for sid in sids}
        if normalized != {"S-1-5-18", currentSid}:
            _raiseSecurityFailure()
    else:
        try:
            metadata = path.stat()
            mode = stat.S_IMODE(metadata.st_mode)
        except OSError:
            _raiseSecurityFailure()
        getEffectiveUid = getattr(os, "geteuid", None)
        if callable(getEffectiveUid) and metadata.st_uid != getEffectiveUid():
            _raiseSecurityFailure()
        if mode & 0o077:
            _raiseSecurityFailure()
        required = stat.S_IRUSR | stat.S_IWUSR
        if path.is_dir():
            required |= stat.S_IXUSR
        if mode & required != required:
            _raiseSecurityFailure()
    return True
