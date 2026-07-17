"""블로그 발행의 단일 진입점.

신규 글에는 기획 계약 v2를 강제하고, 기존 글은 현재 계약으로 감사한다.
모든 대상은 auditBlog 하드 게이트와 SEO 점수를 함께 통과해야 한다.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from audit_seo import score_post as scorePost
from auditBlog import CONTENT_GENRE_CATEGORIES
from auditBlog import publish_gate as auditPublishGate
from blogMedia import mediaManifestPath
from publishBlogAssets import verifyRemoteAssets

REPO_ROOT = Path(__file__).resolve().parents[2]
SEO_SCORE_MIN = 95
EMPTY_TREE_REF = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


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
        if normalizedCategory not in CONTENT_GENRE_CATEGORIES:
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


def trackedBinaryErrors(postDir: Path) -> list[str]:
    if not mediaManifestPath(postDir).is_file():
        return []
    try:
        relativeAssets = (postDir / "assets").relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return []
    tracked = _git(
        "ls-files",
        "--",
        f"{relativeAssets}/*.webp",
        f"{relativeAssets}/*.jpg",
        f"{relativeAssets}/*.jpeg",
        f"{relativeAssets}/*.png",
    )
    paths = [line.strip() for line in tracked.stdout.splitlines() if line.strip()]
    return [f"contract v2 바이너리는 Git 추적 금지, HF에만 발행: {path}" for path in paths]


def validatePost(postDir: Path, *, requireContractV2: bool) -> list[str]:
    errors = auditPublishGate(postDir, requireContractV2=requireContractV2)
    errors.extend(trackedBinaryErrors(postDir))
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
    targets: dict[Path, bool] = {}

    if args.changedFrom:
        baseRef, changed = changedPostDirs(args.changedFrom, args.head)
        for postDir in changed:
            targets[postDir] = not existedAtRef(postDir, baseRef)

    for rawPost in args.post:
        postDir = Path(rawPost)
        if not postDir.is_absolute():
            postDir = REPO_ROOT / postDir
        postDir = postDir.resolve()
        targets[postDir] = not existedAtRef(postDir, "HEAD")

    if not args.changedFrom and not args.post:
        raise SystemExit("--post 또는 --changed-from 중 하나가 필요함")
    if not targets:
        print("발행 게이트 대상 글 없음")
        return

    failed = False
    for postDir, requireContractV2 in sorted(targets.items()):
        errors = validatePost(postDir, requireContractV2=requireContractV2)
        if errors:
            failed = True
            print(f"발행 게이트 실패: {postDir.relative_to(REPO_ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            contractLabel = "v2" if requireContractV2 else "legacy-compatible"
            print(f"발행 게이트 통과: {postDir.relative_to(REPO_ROOT)} ({contractLabel})")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
