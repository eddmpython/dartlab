"""런타임 매니페스트 레지스트리."""

from __future__ import annotations

import tomllib
from pathlib import Path

from .contracts import RuntimeDescriptor


def manifestRoot() -> Path:
    """Sig: manifestRoot() -> Path.

    Args: 없음.
    Returns: 패키지 내부 런타임 TOML 디렉터리다.
    Example: `root = manifestRoot()`.
    """
    return Path(__file__).parent / "manifests"


def loadRuntimeRegistry(root: Path | None = None) -> dict[str, RuntimeDescriptor]:
    """Sig: loadRuntimeRegistry(root=None) -> dict[str, RuntimeDescriptor].

    Args: root는 선택적 매니페스트 디렉터리다.
    Returns: runtimeId로 색인한 descriptor dict다.
    Raises: ValueError if an id is duplicated or a required field is absent.
    Example: `registry = loadRuntimeRegistry()`.
    """
    descriptors: dict[str, RuntimeDescriptor] = {}
    for path in sorted((root or manifestRoot()).glob("*.toml")):
        value = tomllib.loads(path.read_text(encoding="utf-8"))
        runtimeId = str(value["runtimeId"])
        if runtimeId in descriptors:
            raise ValueError(f"중복 runtimeId: {runtimeId}")
        descriptors[runtimeId] = RuntimeDescriptor(
            runtimeId=runtimeId,
            displayName=str(value["displayName"]),
            driver=str(value["driver"]),
            protocol=str(value["protocol"]),
            executableCandidates=tuple(str(item) for item in value["executableCandidates"]),
            versionArgs=tuple(str(item) for item in value["versionArgs"]),
            launchArgs=tuple(str(item) for item in value["launchArgs"]),
            installArgs=tuple(str(item) for item in value["installArgs"]),
            officialUrl=str(value["officialUrl"]),
            windowsLaunch=tuple(str(item) for item in value.get("windowsLaunch", ())),
            embeddedGrounding=bool(value.get("embeddedGrounding", True)),
            authProbeArgs=tuple(str(item) for item in value.get("authProbeArgs", ())),
            authSuccessPattern=str(value["authSuccessPattern"]) if value.get("authSuccessPattern") else None,
            loginArgs=tuple(str(item) for item in value.get("loginArgs", ())),
        )
    return descriptors
