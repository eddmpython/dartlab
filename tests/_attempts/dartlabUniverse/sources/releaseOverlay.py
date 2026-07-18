"""DATA_RELEASES 선언을 HF live tree와 분리된 overlay로 읽는다."""

from __future__ import annotations

from pathlib import PurePosixPath
from types import ModuleType
from typing import Any

from ..canonical import ReleaseDeclaration


def _safePrefix(rawPrefix: Any, releaseId: str) -> str:
    prefix = str(rawPrefix or "").strip().replace("\\", "/").strip("/")
    purePath = PurePosixPath(prefix)
    if not prefix or purePath.is_absolute() or ".." in purePath.parts:
        raise ValueError(f"안전하지 않은 release prefix: {releaseId}={rawPrefix!r}")
    return purePath.as_posix()


def readReleaseOverlay(configModule: ModuleType | Any | None = None) -> tuple[ReleaseDeclaration, ...]:
    """현재 DATA_RELEASES를 경로 선언 overlay로 변환한다.

    Args:
        configModule: 테스트에서 대체할 설정 객체.

    Returns:
        release ID로 정렬된 불변 선언 tuple.

    Raises:
        ValueError: 설정 형식, repo 또는 prefix가 잘못된 경우.

    Example:
        ``readReleaseOverlay()``.
    """
    if configModule is None:
        from dartlab.core import dataConfig as configModule

    releases = getattr(configModule, "DATA_RELEASES", None)
    defaultRepo = str(getattr(configModule, "HF_REPO", "") or "").strip()
    if not isinstance(releases, dict) or not defaultRepo:
        raise ValueError("DATA_RELEASES 또는 HF_REPO 설정 누락")
    records = []
    for releaseId, spec in releases.items():
        if not isinstance(spec, dict):
            raise ValueError(f"release 선언이 dict가 아님: {releaseId}")
        repoId = str(spec.get("repo") or defaultRepo).strip()
        if not repoId:
            raise ValueError(f"release repo 누락: {releaseId}")
        records.append(
            ReleaseDeclaration(
                releaseId=str(releaseId),
                repoId=repoId,
                prefix=_safePrefix(spec.get("dir"), str(releaseId)),
                public=bool(spec.get("public", False)),
                ipcMirror=bool(spec.get("ipcMirror", False)),
            )
        )
    return tuple(sorted(records, key=lambda record: record.releaseId))
