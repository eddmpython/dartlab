"""블로그 미디어가 Git이 아니라 HF 객체만 쓰도록 강제한다.

커밋 전에는 Git index 스냅샷을, CI와 push 전에는 지정한 Git ref를 읽는다.
작업 트리를 읽지 않으므로 staged 내용과 실제 검사 대상이 어긋나지 않는다.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = "media/catalog.json"
HF_REPO = "eddmpython/dartlab-media"
HF_OBJECT_PREFIX = "objects/sha256"
HF_OBJECT_URL_PREFIX = "https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/"
MEDIA_SUFFIXES = frozenset(
    {
        ".svg",
        ".webp",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".avif",
        ".bmp",
        ".tif",
        ".tiff",
        ".ico",
        ".heic",
    }
)
CATALOG_MEDIA_SUFFIXES = frozenset({".svg", ".webp", ".png", ".jpg", ".gif"})
SHARED_UI_MEDIA_REFS = frozenset(
    {
        "/avatar-celebrate.png",
        "/avatar-chart.png",
        "/avatar-code.png",
        "/avatar-curious.png",
        "/avatar-default.png",
        "/avatar-study.png",
    }
)
POST_INDEX_RE = re.compile(r"^blog/[0-9]{2}-[^/]+/[^/]+/index\.md$")
CANONICAL_HF_URL_RE = re.compile(
    rf"^{re.escape(HF_OBJECT_URL_PREFIX)}(?P<prefix>[0-9a-f]{{2}})/"
    r"(?P<sha256>[0-9a-f]{64})(?P<suffix>\.[a-z0-9]+)$"
)
FRONTMATTER_MEDIA_RE = re.compile(
    r"^(?:ogImage|cardPreview|thumbnail|thumbnailBg):\s*[\"']?([^\"'\s]+)",
    re.M,
)
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(<?([^\s)>]+)", re.I)
HTML_MEDIA_RE = re.compile(r"<(?:img|source)\b[^>]*(?:src|srcset)=[\"']([^\"']+)", re.I)


def runGit(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def splitNull(raw: str) -> list[str]:
    return [value for value in raw.split("\0") if value]


def snapshotPaths(sourceRef: str) -> set[str]:
    if sourceRef == "INDEX":
        result = runGit("ls-files", "-z")
    else:
        result = runGit("ls-tree", "-r", "-z", "--name-only", sourceRef)
    return set(splitNull(result.stdout))


def snapshotTexts(paths: list[str], sourceRef: str) -> dict[str, str | None]:
    if not paths:
        return {}
    objectRefs = [f":{path}" if sourceRef == "INDEX" else f"{sourceRef}:{path}" for path in paths]
    process = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=REPO_ROOT,
        check=True,
        input=("\n".join(objectRefs) + "\n").encode(),
        capture_output=True,
    )
    stream = io.BytesIO(process.stdout)
    payloads: dict[str, str | None] = {}
    for path in paths:
        header = stream.readline().decode("utf-8").rstrip("\n")
        if header.endswith(" missing"):
            payloads[path] = None
            continue
        fields = header.split()
        if len(fields) != 3 or fields[1] != "blob":
            payloads[path] = None
            continue
        size = int(fields[2])
        payloads[path] = stream.read(size).decode("utf-8")
        stream.read(1)
    return payloads


def stagedChangedPaths() -> set[str]:
    result = runGit("diff", "--cached", "--name-only", "--diff-filter=ACDMRT", "-z")
    return set(splitNull(result.stdout))


def postIndexPath(path: str) -> str | None:
    parts = Path(path.replace("\\", "/")).parts
    if len(parts) < 4 or parts[0] != "blog" or not re.fullmatch(r"[0-9]{2}-.+", parts[1]):
        return None
    return "/".join((*parts[:3], "index.md"))


def postKey(indexPath: str) -> str:
    parts = Path(indexPath).parts
    return "/".join(parts[1:3])


def isTrackedMediaPath(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if Path(normalized).suffix.lower() not in MEDIA_SUFFIXES:
        return False
    if normalized.startswith("landing/static/thumbnails/"):
        return True
    indexPath = postIndexPath(normalized)
    return indexPath is not None and normalized != indexPath


def renderedMediaRefs(raw: str) -> set[str]:
    refs = {match.group(1).strip() for match in FRONTMATTER_MEDIA_RE.finditer(raw)}
    refs.update(match.group(1).strip() for match in MARKDOWN_IMAGE_RE.finditer(raw))
    for match in HTML_MEDIA_RE.finditer(raw):
        for item in match.group(1).split(","):
            value = item.strip().split(maxsplit=1)[0]
            if value:
                refs.add(value)
    return refs


def loadCatalog(raw: str | None) -> tuple[dict[str, object] | None, list[str]]:
    if raw is None:
        return None, ["media/catalog.json 중앙 카탈로그가 없음"]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"media/catalog.json JSON 오류: {exc}"]
    if not isinstance(payload, dict):
        return None, ["media/catalog.json 최상위 값은 객체여야 함"]
    errors: list[str] = []
    if payload.get("repo") != HF_REPO:
        errors.append(f"media/catalog.json repo는 {HF_REPO}여야 함")
    if payload.get("objectPrefix") != HF_OBJECT_PREFIX:
        errors.append(f"media/catalog.json objectPrefix는 {HF_OBJECT_PREFIX}여야 함")
    for field in ("files", "objects", "posts"):
        if not isinstance(payload.get(field), dict):
            errors.append(f"media/catalog.json {field}는 객체여야 함")
    return payload, errors


def canonicalUrlForSource(catalog: dict[str, object], source: str) -> tuple[str | None, str | None]:
    files = catalog.get("files")
    objects = catalog.get("objects")
    if not isinstance(files, dict) or not isinstance(objects, dict):
        return None, "카탈로그 files 또는 objects 계약 위반"
    sha256 = str(files.get(source) or "")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        return None, f"카탈로그 파일 해시 없음: {source}"
    record = objects.get(sha256)
    if not isinstance(record, dict):
        return None, f"카탈로그 객체 없음: {sha256}"
    remotePath = str(record.get("path") or "")
    suffix = Path(remotePath).suffix.lower()
    expectedPath = f"{HF_OBJECT_PREFIX}/{sha256[:2]}/{sha256}{suffix}"
    if suffix not in CATALOG_MEDIA_SUFFIXES or remotePath != expectedPath:
        return None, f"카탈로그 콘텐츠 주소 경로 위반: {source} -> {remotePath}"
    return f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/{remotePath}", None


def allowedPostUrls(catalog: dict[str, object], key: str) -> tuple[set[str], list[str]]:
    posts = catalog.get("posts")
    if not isinstance(posts, dict):
        return set(), ["media/catalog.json posts 계약 위반"]
    entry = posts.get(key)
    if not isinstance(entry, dict):
        return set(), [f"media/catalog.json에 글 매핑 없음: {key}"]
    sources: set[str] = set()
    for field in ("assets", "diagrams"):
        group = entry.get(field)
        if isinstance(group, dict):
            sources.update(str(source) for source in group.values() if source)
    for field in ("og", "card"):
        source = str(entry.get(field) or "")
        if source:
            sources.add(source)
    urls: set[str] = set()
    errors: list[str] = []
    for source in sorted(sources):
        url, error = canonicalUrlForSource(catalog, source)
        if error:
            errors.append(error)
        elif url:
            urls.add(url)
    return urls, errors


def validateRenderedRef(indexPath: str, ref: str, allowedUrls: set[str]) -> list[str]:
    if ref in SHARED_UI_MEDIA_REFS:
        return []
    match = CANONICAL_HF_URL_RE.fullmatch(ref)
    if not match:
        return [f"HF 콘텐츠 주소 객체 외 렌더링 미디어 금지: {indexPath} -> {ref}"]
    if match.group("prefix") != match.group("sha256")[:2]:
        return [f"HF 객체 prefix와 SHA-256 불일치: {indexPath} -> {ref}"]
    if match.group("suffix") not in CATALOG_MEDIA_SUFFIXES:
        return [f"지원하지 않는 HF 미디어 확장자: {indexPath} -> {ref}"]
    if ref not in allowedUrls:
        return [f"글의 media/catalog.json 매핑 밖 HF 객체 참조: {indexPath} -> {ref}"]
    return []


def validateSnapshot(sourceRef: str, *, changedPaths: set[str] | None = None) -> list[str]:
    paths = snapshotPaths(sourceRef)
    errors = [f"Git 추적 블로그 미디어 금지: {path}" for path in sorted(paths) if isTrackedMediaPath(path)]

    allIndexes = sorted(path for path in paths if POST_INDEX_RE.fullmatch(path))
    if changedPaths is None or CATALOG_PATH in changedPaths:
        selectedIndexes = allIndexes
    else:
        selected = {postIndexPath(path) for path in changedPaths}
        selectedIndexes = sorted(path for path in selected if path and path in paths)

    if not selectedIndexes:
        return errors
    rawByPath = snapshotTexts([CATALOG_PATH, *selectedIndexes], sourceRef)
    catalog, catalogErrors = loadCatalog(rawByPath.get(CATALOG_PATH))
    errors.extend(catalogErrors)
    if catalog is None or catalogErrors:
        return sorted(set(errors))

    for indexPath in selectedIndexes:
        raw = rawByPath.get(indexPath)
        if raw is None:
            errors.append(f"블로그 본문을 읽을 수 없음: {indexPath}")
            continue
        refs = renderedMediaRefs(raw)
        remoteRefs = refs - SHARED_UI_MEDIA_REFS
        if not remoteRefs:
            continue
        allowedUrls, mappingErrors = allowedPostUrls(catalog, postKey(indexPath))
        errors.extend(mappingErrors)
        for ref in sorted(remoteRefs):
            errors.extend(validateRenderedRef(indexPath, ref, allowedUrls))
    return sorted(set(errors))


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="블로그 미디어 HF SSOT를 Git 스냅샷에서 검사한다.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--staged", action="store_true", help="커밋할 Git index와 바뀐 글을 검사한다.")
    group.add_argument("--ref", default="HEAD", help="지정한 Git ref 전체를 검사한다. 기본 HEAD.")
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    if args.staged:
        changedPaths = stagedChangedPaths()
        errors = validateSnapshot("INDEX", changedPaths=changedPaths)
        label = "staged"
    else:
        errors = validateSnapshot(args.ref)
        label = args.ref
    if errors:
        print(f"[blog-media-ssot] FAIL: {label}")
        for error in errors:
            print(f"  - {error}")
        print("  publishBlogAssets.py로 HF 업로드, catalog 등록, 본문 치환, 로컬 정리를 완료해야 함.")
        raise SystemExit(1)
    print(f"[blog-media-ssot] PASS: {label}")


if __name__ == "__main__":
    main()
