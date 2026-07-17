"""블로그 HF 미디어 경로와 매니페스트 계약의 단일 정의."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from dartlab.core.dataConfig import HF_MEDIA_BASE_URL, HF_MEDIA_REPO

MEDIA_MANIFEST_VERSION = 1
MEDIA_PREFIX = "blog"
MEDIA_MANIFEST_NAME = "media.json"
IMAGE_SUFFIX = ".webp"
ASSET_KEY_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def mediaManifestPath(postDir: Path) -> Path:
    return postDir / "assets" / MEDIA_MANIFEST_NAME


def mediaSlug(postDir: Path) -> str:
    return re.sub(r"^\d+-", "", postDir.name)


def contentSha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mediaPath(postDir: Path, assetKey: str, sha256: str) -> str:
    return f"{MEDIA_PREFIX}/{mediaSlug(postDir)}/{assetKey}.{sha256[:8]}{IMAGE_SUFFIX}"


def mediaUrl(path: str) -> str:
    return f"{HF_MEDIA_BASE_URL}/{path}"


def loadMediaManifest(postDir: Path) -> tuple[dict[str, object] | None, list[str]]:
    path = mediaManifestPath(postDir)
    if not path.is_file():
        return None, ["contract v2 이미지는 assets/media.json HF 매니페스트가 필요함"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"assets/media.json 읽기 실패: {exc}"]
    if not isinstance(payload, dict):
        return None, ["assets/media.json 최상위 값은 객체여야 함"]
    errors: list[str] = []
    if payload.get("version") != MEDIA_MANIFEST_VERSION:
        errors.append(f"assets/media.json version은 {MEDIA_MANIFEST_VERSION}이어야 함")
    if payload.get("repo") != HF_MEDIA_REPO:
        errors.append(f"assets/media.json repo는 {HF_MEDIA_REPO}여야 함")
    if not isinstance(payload.get("assets"), dict):
        errors.append("assets/media.json assets는 객체여야 함")
    if not isinstance(payload.get("og"), dict):
        errors.append("assets/media.json og는 객체여야 함")
    return payload, errors


def buildMediaRecord(postDir: Path, assetKey: str, localPath: Path) -> dict[str, str]:
    sha256 = contentSha256(localPath)
    return {"path": mediaPath(postDir, assetKey, sha256), "sha256": sha256}
