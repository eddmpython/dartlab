"""블로그 발행의 단일 진입점.

신규 글에는 기획 계약 v2를 강제하고, 기존 글은 현재 계약으로 감사한다.
모든 대상은 auditBlog 하드 게이트와 SEO 점수를 함께 통과해야 한다.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from audit_seo import score_post as scorePost
from auditBlog import BLOG_CATEGORIES, CONTENT_GENRE_CATEGORIES
from auditBlog import publish_gate as auditPublishGate
from blogMedia import (
    IMAGE_EXTENSION_RE,
    IMAGE_SUFFIX_ORDER,
    IMAGE_SUFFIXES,
    loadMediaManifest,
    mediaManifestPath,
    mediaUrl,
)
from companyReportPolicy import validateCompanyReportDebtRatioBan
from publishBlogAssets import verifyRemoteAssets

REPO_ROOT = Path(__file__).resolve().parents[2]
SEO_SCORE_MIN = 95
EMPTY_TREE_REF = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
HF_OBJECT_URL_PREFIX = "https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/"
MEDIA_FRONTMATTER_RE = re.compile(r"^(?:ogImage|cardPreview|thumbnail|thumbnailBg):\s*.*(?:\r?\n|$)", re.M)
MEDIA_LINK_RE = re.compile(
    rf"(!\[[^\]]*\]\()[^)]*\.(?:{IMAGE_EXTENSION_RE})(?:\s+[\"'][^\"']*[\"'])?(\))",
    re.I,
)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _normalizeBase(baseRef: str, headRef: str) -> str:
    if baseRef and set(baseRef) != {"0"}:
        _git("cat-file", "-e", f"{baseRef}^{{commit}}")
        return baseRef
    parent = _git("rev-parse", f"{headRef}^", check=False)
    if parent.returncode == 0:
        return parent.stdout.strip()
    return EMPTY_TREE_REF


def postDirsFromPaths(paths: list[str]) -> list[Path]:
    posts: set[Path] = set()
    for rawPath in paths:
        parts = Path(rawPath.replace("\\", "/")).parts
        if len(parts) < 4 or parts[0] != "blog":
            continue
        categoryDir = parts[1]
        prefix, separator, category = categoryDir.partition("-")
        normalizedCategory = category if separator and prefix.isdigit() else categoryDir
        if normalizedCategory not in BLOG_CATEGORIES:
            continue
        postDir = REPO_ROOT.joinpath(*parts[:3])
        if (postDir / "index.md").is_file():
            posts.add(postDir)
    return sorted(posts)


def changedPostDirs(baseRef: str, headRef: str = "HEAD") -> tuple[str, list[Path]]:
    normalizedBase = _normalizeBase(baseRef, headRef)
    diff = _git(
        "diff",
        "--name-only",
        "--diff-filter=ACDMRT",
        normalizedBase,
        headRef,
        "--",
        "blog",
    )
    paths = [line.strip() for line in diff.stdout.splitlines() if line.strip()]
    return normalizedBase, postDirsFromPaths(paths)


def existedAtRef(postDir: Path, gitRef: str) -> bool:
    try:
        relativeIndex = (postDir / "index.md").relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return False
    result = _git("cat-file", "-e", f"{gitRef}:{relativeIndex}", check=False)
    return result.returncode == 0


def normalizeMediaOnlyDiff(raw: str) -> str:
    normalized = MEDIA_FRONTMATTER_RE.sub("", raw)
    return MEDIA_LINK_RE.sub(r"\1<media>\2", normalized)


def mediaOnlyAtRefs(postDir: Path, baseRef: str, headRef: str) -> bool:
    try:
        relativeIndex = (postDir / "index.md").relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return False
    before = _git("show", f"{baseRef}:{relativeIndex}", check=False)
    after = _git("show", f"{headRef}:{relativeIndex}", check=False)
    if before.returncode != 0 or after.returncode != 0:
        return False
    return normalizeMediaOnlyDiff(before.stdout) == normalizeMediaOnlyDiff(after.stdout)


def mediaReferenceErrors(postDir: Path) -> list[str]:
    manifest, loadErrors = loadMediaManifest(postDir)
    if manifest is None:
        return loadErrors
    if loadErrors:
        return loadErrors
    raw = postDir.joinpath("index.md").read_text(encoding="utf-8")
    errors: list[str] = []
    allowedUrls: set[str] = set()
    assets = manifest.get("assets")
    records = list(assets.values()) if isinstance(assets, dict) else []
    diagrams = manifest.get("diagrams")
    if isinstance(diagrams, dict):
        records.extend(diagrams.values())
    for role in ("og", "card"):
        record = manifest.get(role)
        if isinstance(record, dict):
            records.append(record)
            expectedUrl = mediaUrl(str(record.get("path") or ""))
            allowedUrls.add(expectedUrl)
            field = "ogImage" if role == "og" else "cardPreview"
            match = re.search(rf"^{field}:\s*(\S+)", raw, re.M)
            if not match or match.group(1) != expectedUrl:
                errors.append(f"{field}가 media/catalog.json {role} 객체와 다름")
    for record in records:
        if isinstance(record, dict) and record.get("path"):
            allowedUrls.add(mediaUrl(str(record["path"])))
    localRefs = re.findall(rf"(?:\./)?assets/[^)\"' >]+\.(?:{IMAGE_EXTENSION_RE})", raw, re.I)
    if localRefs:
        errors.append(f"로컬 콘텐츠 미디어 참조 금지: {localRefs[0]}")
    usedUrls = set(re.findall(rf"{re.escape(HF_OBJECT_URL_PREFIX)}[0-9a-f/]+\.(?:{IMAGE_EXTENSION_RE})", raw, re.I))
    unexpected = sorted(usedUrls - allowedUrls)
    if unexpected:
        errors.append(f"media/catalog.json 밖 HF 객체 참조: {unexpected[0]}")
    return errors


def trackedBinaryErrors(postDir: Path) -> list[str]:
    try:
        catalogPath = mediaManifestPath(postDir)
    except ValueError:
        return []
    if not catalogPath.is_file():
        return []
    try:
        relativeAssets = (postDir / "assets").relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return []
    tracked = _git("ls-files", "--", *(f"{relativeAssets}/*{suffix}" for suffix in IMAGE_SUFFIX_ORDER))
    paths = [line.strip() for line in tracked.stdout.splitlines() if line.strip()]
    return [f"블로그 콘텐츠 미디어는 Git 추적 금지, HF 콘텐츠 주소 객체에만 발행: {path}" for path in paths]


def localMediaResidueErrors(postDir: Path) -> list[str]:
    """중앙 카탈로그가 생긴 글에는 무시된 로컬 staging도 남기지 않는다."""
    try:
        catalogPath = mediaManifestPath(postDir)
    except ValueError:
        return []
    if not catalogPath.is_file():
        return []
    residue: set[Path] = set()
    assetsDir = postDir / "assets"
    if assetsDir.is_dir():
        residue.update(
            path for path in assetsDir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
    manifest, _ = loadMediaManifest(postDir)
    if isinstance(manifest, dict):
        records: list[dict[str, object]] = []
        for role in ("og", "card"):
            record = manifest.get(role)
            if isinstance(record, dict):
                records.append(record)
        for role in ("assets", "diagrams"):
            group = manifest.get(role)
            if isinstance(group, dict):
                records.extend(record for record in group.values() if isinstance(record, dict))
        for record in records:
            source = str(record.get("source") or "")
            if not source:
                continue
            local = (REPO_ROOT / source).resolve()
            if local.is_file() and local.suffix.lower() in IMAGE_SUFFIXES:
                residue.add(local)
    errors: list[str] = []
    for path in sorted(residue):
        try:
            label = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            label = str(path)
        errors.append(f"HF 발행 후 로컬 미디어 staging 잔존 금지: {label}")
    return errors


def validatePost(postDir: Path, *, requireContractV2: bool, mediaOnly: bool = False) -> list[str]:
    if mediaOnly:
        errors = validateCompanyReportDebtRatioBan(postDir)
        errors.extend(mediaReferenceErrors(postDir))
        errors.extend(trackedBinaryErrors(postDir))
        errors.extend(localMediaResidueErrors(postDir))
        errors.extend(verifyRemoteAssets(postDir))
        return errors
    errors = auditPublishGate(postDir, requireContractV2=requireContractV2)
    errors.extend(mediaReferenceErrors(postDir))
    errors.extend(trackedBinaryErrors(postDir))
    errors.extend(localMediaResidueErrors(postDir))
    errors.extend(verifyRemoteAssets(postDir))
    score = scorePost(str(postDir))
    if score is None:
        errors.append("SEO 점수를 계산할 수 없음")
    elif int(score.get("pct", 0)) < SEO_SCORE_MIN:
        errors.append(f"SEO 점수 {score.get('pct', 0)}% < {SEO_SCORE_MIN}%")
    return errors


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="블로그 하드 게이트와 SEO를 한 번에 검사한다.")
    parser.add_argument("--post", action="append", default=[], help="검사할 글 폴더. 여러 번 지정 가능.")
    parser.add_argument("--changed-from", dest="changedFrom", help="이 git ref 이후 바뀐 글만 검사한다.")
    parser.add_argument("--head", default="HEAD", help="변경 범위의 끝 ref. 기본 HEAD.")
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    targets: dict[Path, tuple[bool, bool]] = {}

    if args.changedFrom:
        baseRef, changed = changedPostDirs(args.changedFrom, args.head)
        for postDir in changed:
            isNew = not existedAtRef(postDir, baseRef)
            targets[postDir] = (isNew, False if isNew else mediaOnlyAtRefs(postDir, baseRef, args.head))

    for rawPost in args.post:
        postDir = Path(rawPost)
        if not postDir.is_absolute():
            postDir = REPO_ROOT / postDir
        postDir = postDir.resolve()
        targets[postDir] = (not existedAtRef(postDir, "HEAD"), False)

    if not args.changedFrom and not args.post:
        raise SystemExit("--post 또는 --changed-from 중 하나가 필요함")
    if not targets:
        print("발행 게이트 대상 글 없음")
        return

    failed = False
    for postDir, (requireContractV2, mediaOnly) in sorted(targets.items()):
        errors = validatePost(postDir, requireContractV2=requireContractV2, mediaOnly=mediaOnly)
        if errors:
            failed = True
            print(f"발행 게이트 실패: {postDir.relative_to(REPO_ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            contractLabel = "media-only" if mediaOnly else "v2" if requireContractV2 else "legacy-compatible"
            print(f"발행 게이트 통과: {postDir.relative_to(REPO_ROOT)} ({contractLabel})")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
