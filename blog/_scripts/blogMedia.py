"""블로그 HF 객체 저장소와 중앙 미디어 카탈로그의 단일 계약."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from dartlab.core.dataConfig import HF_MEDIA_BASE_URL, HF_MEDIA_REPO

MEDIA_CATALOG_VERSION = 4
MEDIA_CATALOG_RELATIVE = Path("media") / "catalog.json"
OBJECT_PREFIX = "objects/sha256"
RASTER_SUFFIXES = (".webp", ".jpg", ".jpeg", ".png", ".gif")
IMAGE_SUFFIX_ORDER = (*RASTER_SUFFIXES, ".svg")
IMAGE_SUFFIXES = frozenset(IMAGE_SUFFIX_ORDER)
RASTER_EXTENSION_RE = "|".join(re.escape(suffix.lstrip(".")) for suffix in RASTER_SUFFIXES)
IMAGE_EXTENSION_RE = "|".join(re.escape(suffix.lstrip(".")) for suffix in IMAGE_SUFFIX_ORDER)
ASSET_KEY_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SVG_FORBIDDEN_TAGS = {"foreignobject", "script"}
SVG_DANGEROUS_PREFIXES = ("javascript:", "data:text/html")


def blogRoot(postDir: Path) -> Path:
    """`blog/<category>/<post>`에서 blog 루트를 반환한다."""
    if postDir.parent.parent.name != "blog":
        raise ValueError(f"블로그 글 폴더가 아님: {postDir}")
    return postDir.parent.parent


def mediaCatalogPath(postDir: Path) -> Path:
    return blogRoot(postDir).parent / MEDIA_CATALOG_RELATIVE


def mediaManifestPath(postDir: Path) -> Path:
    """이전 호출부 호환용 이름. 실제 SSOT는 media/catalog.json 하나다."""
    return mediaCatalogPath(postDir)


def mediaPostKey(postDir: Path) -> str:
    return postDir.relative_to(blogRoot(postDir)).as_posix()


def contentSha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonicalSuffix(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jpeg":
        return ".jpg"
    if suffix not in IMAGE_SUFFIXES:
        raise ValueError(f"지원하지 않는 블로그 이미지 확장자: {path}")
    return suffix


def mediaPath(sha256: str, suffix: str = ".webp") -> str:
    normalizedSuffix = ".jpg" if suffix.lower() == ".jpeg" else suffix.lower()
    if not SHA256_RE.fullmatch(sha256):
        raise ValueError(f"올바르지 않은 SHA-256: {sha256!r}")
    if normalizedSuffix not in IMAGE_SUFFIXES - {".jpeg"}:
        raise ValueError(f"지원하지 않는 이미지 확장자: {suffix}")
    return f"{OBJECT_PREFIX}/{sha256[:2]}/{sha256}{normalizedSuffix}"


def mediaUrl(path: str) -> str:
    return f"{HF_MEDIA_BASE_URL}/{path}"


def svgObjectMetadata(path: Path) -> dict[str, object]:
    """SVG를 이미지로 안전하게 서빙하기 위한 최소 계약과 감사 메타데이터."""
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ET.ParseError) as exc:
        raise ValueError(f"SVG XML 파싱 실패: {path}: {exc}") from exc
    if root.tag.split("}")[-1].lower() != "svg":
        raise ValueError(f"SVG 루트 요소가 아님: {path}")
    textNodes = 0
    for element in root.iter():
        tag = element.tag.split("}")[-1].lower()
        if tag in SVG_FORBIDDEN_TAGS:
            raise ValueError(f"SVG 금지 요소 <{tag}>: {path}")
        if tag == "text":
            textNodes += 1
        for rawName, rawValue in element.attrib.items():
            name = rawName.split("}")[-1].lower()
            value = str(rawValue).strip().lower()
            if name.startswith("on"):
                raise ValueError(f"SVG 이벤트 속성 금지: {path} ({name})")
            if name in {"href", "src"} and value.startswith(SVG_DANGEROUS_PREFIXES):
                raise ValueError(f"SVG 위험 링크 금지: {path} ({rawValue})")
    raw = path.read_text(encoding="utf-8")
    return {
        "colorCount": len(set(re.findall(r"#[0-9A-Fa-f]{6}", raw))),
        "mediaType": "image/svg+xml",
        "textNodes": textNodes,
        "viewBox": str(root.attrib.get("viewBox") or ""),
    }


def emptyMediaCatalog() -> dict[str, object]:
    return {
        "version": MEDIA_CATALOG_VERSION,
        "repo": HF_MEDIA_REPO,
        "objectPrefix": OBJECT_PREFIX,
        "collections": {},
        "manifests": {
            "carousels": "manifests/carousels.json",
            "companies": "manifests/companies.json",
        },
        "objects": {},
        "files": {},
        "posts": {},
    }


def loadMediaCatalog(path: Path) -> tuple[dict[str, object] | None, list[str]]:
    if not path.is_file():
        return None, ["media/catalog.json 중앙 HF 카탈로그가 필요함"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"media/catalog.json 읽기 실패: {exc}"]
    if not isinstance(payload, dict):
        return None, ["media/catalog.json 최상위 값은 객체여야 함"]
    errors: list[str] = []
    version = payload.get("version")
    if version not in {3, MEDIA_CATALOG_VERSION}:
        errors.append(f"media/catalog.json version은 {MEDIA_CATALOG_VERSION}이어야 함")
    elif version == 3:
        payload["version"] = MEDIA_CATALOG_VERSION
    if payload.get("repo") != HF_MEDIA_REPO:
        errors.append(f"media/catalog.json repo는 {HF_MEDIA_REPO}여야 함")
    if payload.get("objectPrefix") != OBJECT_PREFIX:
        errors.append(f"media/catalog.json objectPrefix는 {OBJECT_PREFIX}여야 함")
    for key in ("collections", "manifests", "objects", "files", "posts"):
        if not isinstance(payload.get(key), dict):
            errors.append(f"media/catalog.json {key}는 객체여야 함")
    return payload, errors


def saveMediaCatalog(path: Path, catalog: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def registerMediaFile(catalog: dict[str, object], source: str, localPath: Path) -> dict[str, str]:
    sha256 = contentSha256(localPath)
    suffix = canonicalSuffix(localPath)
    objects = catalog.setdefault("objects", {})
    files = catalog.setdefault("files", {})
    if not isinstance(objects, dict) or not isinstance(files, dict):
        raise ValueError("media/catalog.json objects/files 계약 위반")
    existingObject = objects.get(sha256)
    if isinstance(existingObject, dict) and existingObject.get("path"):
        remotePath = str(existingObject["path"])
    else:
        remotePath = mediaPath(sha256, suffix)
        objects[sha256] = {
            "bytes": localPath.stat().st_size,
            "path": remotePath,
        }
    if suffix == ".svg":
        objectRecord = objects.get(sha256)
        if not isinstance(objectRecord, dict):
            raise ValueError(f"media/catalog.json SVG 객체 계약 위반: {source}")
        objectRecord.update(svgObjectMetadata(localPath))
    files[source] = sha256
    return {"path": remotePath, "sha256": sha256, "source": source}


def mediaRecord(catalog: dict[str, object], source: str) -> dict[str, str] | None:
    files = catalog.get("files")
    objects = catalog.get("objects")
    if not isinstance(files, dict) or not isinstance(objects, dict):
        return None
    sha256 = str(files.get(source) or "")
    obj = objects.get(sha256)
    if not SHA256_RE.fullmatch(sha256) or not isinstance(obj, dict) or not obj.get("path"):
        return None
    remotePath = str(obj["path"])
    try:
        expectedPath = mediaPath(sha256, Path(remotePath).suffix)
    except ValueError:
        return None
    if remotePath != expectedPath:
        return None
    return {"path": remotePath, "sha256": sha256, "source": source}


def loadMediaManifest(postDir: Path) -> tuple[dict[str, object] | None, list[str]]:
    """중앙 카탈로그에서 한 글이 쓰는 역할별 뷰를 만든다."""
    try:
        catalogPath = mediaCatalogPath(postDir)
        postKey = mediaPostKey(postDir)
    except ValueError as exc:
        return None, [str(exc)]
    catalog, errors = loadMediaCatalog(catalogPath)
    if catalog is None or errors:
        return None, errors
    posts = catalog.get("posts")
    post = posts.get(postKey) if isinstance(posts, dict) else None
    if not isinstance(post, dict):
        return None, [f"media/catalog.json에 글 매핑 없음: {postKey}"]
    assetSources = post.get("assets")
    if not isinstance(assetSources, dict):
        return None, [f"media/catalog.json 글 assets 계약 위반: {postKey}"]
    assets: dict[str, dict[str, str]] = {}
    for key, source in assetSources.items():
        record = mediaRecord(catalog, str(source))
        if record is None:
            errors.append(f"media/catalog.json 파일 매핑 없음: {source}")
        else:
            assets[str(key)] = record
    diagramSources = post.get("diagrams")
    diagrams: dict[str, dict[str, str]] = {}
    if isinstance(diagramSources, dict):
        for key, source in diagramSources.items():
            record = mediaRecord(catalog, str(source))
            if record is None:
                errors.append(f"media/catalog.json SVG 파일 매핑 없음: {source}")
            else:
                diagrams[str(key)] = record
    ogSource = str(post.get("og") or "")
    og = mediaRecord(catalog, ogSource)
    if og is None:
        errors.append(f"media/catalog.json OG 매핑 없음: {postKey}")
        return None, errors
    manifest = {
        "version": MEDIA_CATALOG_VERSION,
        "repo": HF_MEDIA_REPO,
        "og": og,
        "assets": assets,
        "diagrams": diagrams,
    }
    cardSource = str(post.get("card") or "")
    card = mediaRecord(catalog, cardSource) if cardSource else None
    if card is not None:
        manifest["card"] = card
    return manifest, errors


def buildMediaRecord(localPath: Path, source: str | None = None) -> dict[str, str]:
    """독립 경로 계산 헬퍼. 중앙 카탈로그 등록은 `registerMediaFile`을 쓴다."""
    sha256 = contentSha256(localPath)
    return {
        "path": mediaPath(sha256, canonicalSuffix(localPath)),
        "sha256": sha256,
        "source": source or localPath.as_posix(),
    }
