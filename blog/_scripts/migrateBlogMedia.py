"""기존 블로그 래스터를 HF 콘텐츠 주소 SSOT로 일괄 이관한다."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from blogMedia import (
    IMAGE_SUFFIXES,
    emptyMediaCatalog,
    loadMediaCatalog,
    mediaRecord,
    mediaUrl,
    registerMediaFile,
    saveMediaCatalog,
)
from huggingface_hub import CommitOperationAdd, HfApi

from dartlab.core.dataConfig import HF_MEDIA_REPO
from dartlab.core.hfRetry import retryHfCall
from dartlab.pipeline.hfUpload import _resolveHfToken as resolveHfToken

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "media" / "catalog.json"
TRACKED_PATHSPECS = (
    ":(glob)blog/**/*.webp",
    ":(glob)blog/**/*.png",
    ":(glob)blog/**/*.jpg",
    ":(glob)blog/**/*.jpeg",
    ":(glob)landing/static/thumbnails/**/*.webp",
    ":(glob)landing/static/thumbnails/**/*.png",
    ":(glob)landing/static/thumbnails/**/*.jpg",
    ":(glob)landing/static/thumbnails/**/*.jpeg",
)
PLAN_FILES = ("brief.json", "plan.json")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def trackedRasterPaths() -> list[Path]:
    raw = git("ls-files", "-z", "--", *TRACKED_PATHSPECS)
    paths: list[Path] = []
    for relative in raw.split("\0"):
        if not relative:
            continue
        path = (REPO_ROOT / relative).resolve()
        try:
            safeRelative = path.relative_to(REPO_ROOT.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"저장소 밖 추적 파일: {path}") from exc
        if not (safeRelative.startswith("blog/") or safeRelative.startswith("landing/static/thumbnails/")):
            raise ValueError(f"이관 범위 밖 추적 파일: {safeRelative}")
        if path.suffix.lower() in IMAGE_SUFFIXES and path.is_file():
            paths.append(path)
    return sorted(paths)


def plannedKeys(postDir: Path) -> set[str] | None:
    for name in PLAN_FILES:
        path = postDir / name
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        plan = payload.get("plan") if isinstance(payload, dict) and isinstance(payload.get("plan"), dict) else payload
        if not isinstance(plan, dict) or plan.get("contractVersion") != 2:
            return None
        rows = plan.get("imagePlan")
        if not isinstance(rows, list):
            return set()
        return {
            str(row.get("assetKey") or "").strip()
            for row in rows
            if isinstance(row, dict) and str(row.get("assetKey") or "").strip()
        }
    return None


def frontmatterValue(raw: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.M)
    return match.group(1).strip().strip("\"'") if match else ""


def replaceFrontmatterMedia(raw: str, field: str, catalog: dict[str, object]) -> str:
    value = frontmatterValue(raw, field)
    if not value.startswith("/thumbnails/"):
        return raw
    source = f"landing/static{value}"
    record = mediaRecord(catalog, source)
    if record is None:
        raise ValueError(f"중앙 카탈로그에 {field} 파일 없음: {source}")
    return re.sub(
        rf"^{re.escape(field)}:\s*.+$",
        f"{field}: {mediaUrl(record['path'])}",
        raw,
        count=1,
        flags=re.M,
    )


def buildCatalog(paths: list[Path]) -> tuple[dict[str, object], dict[str, Path], dict[Path, str]]:
    existing, errors = loadMediaCatalog(CATALOG_PATH)
    if existing is None and not CATALOG_PATH.exists():
        catalog = emptyMediaCatalog()
    elif existing is None or errors:
        raise ValueError("; ".join(errors))
    else:
        catalog = existing

    localByRemote: dict[str, Path] = {}
    for localPath in paths:
        source = localPath.relative_to(REPO_ROOT).as_posix()
        record = registerMediaFile(catalog, source, localPath)
        localByRemote.setdefault(record["path"], localPath)

    files = catalog.get("files")
    if not isinstance(files, dict):
        raise ValueError("media/catalog.json files 계약 위반")
    sourcesByPost: dict[Path, list[str]] = {}
    for source in files:
        parts = Path(source).parts
        if len(parts) == 5 and parts[0] == "blog" and parts[3] == "assets":
            postDir = REPO_ROOT.joinpath(*parts[:3])
            if (postDir / "index.md").is_file():
                sourcesByPost.setdefault(postDir, []).append(source)

    posts = catalog.setdefault("posts", {})
    if not isinstance(posts, dict):
        raise ValueError("media/catalog.json posts 계약 위반")
    rewritten: dict[Path, str] = {}
    for indexPath in sorted((REPO_ROOT / "blog").glob("*/*/index.md")):
        postDir = indexPath.parent
        postKey = postDir.relative_to(REPO_ROOT / "blog").as_posix()
        raw = indexPath.read_text(encoding="utf-8")
        sources = sorted(sourcesByPost.get(postDir, []))
        contractKeys = plannedKeys(postDir)
        assets: dict[str, str] = {}
        updated = raw
        for source in sources:
            filename = Path(source).name
            key = Path(filename).stem
            record = mediaRecord(catalog, source)
            if record is None:
                raise ValueError(f"중앙 카탈로그 파일 매핑 실패: {source}")
            hasLocalReference = f"./assets/{filename}" in raw or f"assets/{filename}" in raw
            if contractKeys is None or key in contractKeys or hasLocalReference:
                if key in assets and assets[key] != source:
                    raise ValueError(f"글 안의 assetKey 충돌: {postKey}/{key}")
                assets[key] = source
            updated = updated.replace(f"./assets/{filename}", mediaUrl(record["path"]))
            updated = updated.replace(f"assets/{filename}", mediaUrl(record["path"]))

        ogValue = frontmatterValue(raw, "ogImage")
        if not ogValue:
            raise ValueError(f"ogImage 없음: {postKey}")
        if ogValue.startswith("/thumbnails/"):
            ogSource = f"landing/static{ogValue}"
        else:
            oldPost = posts.get(postKey)
            ogSource = str(oldPost.get("og") or "") if isinstance(oldPost, dict) else ""
        if mediaRecord(catalog, ogSource) is None:
            raise ValueError(f"중앙 카탈로그 OG 매핑 실패: {postKey} -> {ogSource}")

        ogPath = Path(ogSource)
        cardSource = ogPath.with_name(f"{ogPath.stem}-card{ogPath.suffix}").as_posix()
        if mediaRecord(catalog, cardSource) is None:
            cardSource = ""

        updated = replaceFrontmatterMedia(updated, "ogImage", catalog)
        updated = replaceFrontmatterMedia(updated, "thumbnail", catalog)
        if cardSource:
            cardRecord = mediaRecord(catalog, cardSource)
            assert cardRecord is not None
            cardLine = f"cardPreview: {mediaUrl(cardRecord['path'])}"
            if re.search(r"^cardPreview:\s*.+$", updated, re.M):
                updated = re.sub(r"^cardPreview:\s*.+$", cardLine, updated, count=1, flags=re.M)
            else:
                updated = re.sub(r"^(ogImage:\s*.+)$", rf"\1\n{cardLine}", updated, count=1, flags=re.M)
        postEntry: dict[str, object] = {
            "assets": assets,
            "og": ogSource,
            "staging": sources,
        }
        if cardSource:
            postEntry["card"] = cardSource
        posts[postKey] = postEntry
        rewritten[indexPath] = updated

    return catalog, localByRemote, rewritten


def uploadObjects(localByRemote: dict[str, Path], batchSize: int) -> None:
    client = HfApi(token=resolveHfToken())
    existing = set(retryHfCall(client.list_repo_files, repo_id=HF_MEDIA_REPO, repo_type="dataset"))
    pending = [(remote, local) for remote, local in sorted(localByRemote.items()) if remote not in existing]
    print(f"HF 객체 업로드 대상: {len(pending)}개")
    for offset in range(0, len(pending), batchSize):
        chunk = pending[offset : offset + batchSize]
        operations = [CommitOperationAdd(path_in_repo=remote, path_or_fileobj=str(local)) for remote, local in chunk]
        retryHfCall(
            client.create_commit,
            repo_id=HF_MEDIA_REPO,
            repo_type="dataset",
            operations=operations,
            commit_message=f"블로그 콘텐츠 주소 객체 {offset + 1}-{offset + len(chunk)}",
        )
        print(f"HF 업로드 완료: {offset + len(chunk)}/{len(pending)}")
    remoteFiles = set(retryHfCall(client.list_repo_files, repo_id=HF_MEDIA_REPO, repo_type="dataset"))
    missing = sorted(set(localByRemote) - remoteFiles)
    if missing:
        raise RuntimeError(f"HF 검증 실패, 객체 {len(missing)}개 없음: {missing[:3]}")


def writeMigration(catalog: dict[str, object], rewritten: dict[Path, str]) -> None:
    for path, raw in rewritten.items():
        path.write_text(raw, encoding="utf-8")
    saveMediaCatalog(CATALOG_PATH, catalog)


def untrack(paths: list[Path], batchSize: int = 100) -> None:
    relatives = [path.relative_to(REPO_ROOT).as_posix() for path in paths]
    for offset in range(0, len(relatives), batchSize):
        git("rm", "--cached", "--ignore-unmatch", "--", *relatives[offset : offset + batchSize])
    print(f"Git 바이너리 추적 제거: {len(relatives)}개, 로컬 staging 파일은 보존")


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="기존 블로그 래스터를 HF 콘텐츠 주소 SSOT로 이관한다.")
    parser.add_argument(
        "--dry-run", dest="dryRun", action="store_true", help="집계와 계약만 계산하고 업로드·수정하지 않음"
    )
    parser.add_argument("--untrack", action="store_true", help="HF 검증 뒤 기존 바이너리를 Git 인덱스에서 제거")
    parser.add_argument("--batch-size", dest="batchSize", type=int, default=100, help="HF 커밋당 최대 객체 수")
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    if args.batchSize < 1 or args.batchSize > 200:
        raise SystemExit("--batch-size는 1 이상 200 이하여야 함")
    paths = trackedRasterPaths()
    catalog, localByRemote, rewritten = buildCatalog(paths)
    objects = catalog.get("objects")
    print(
        f"이관 계획: 추적 파일 {len(paths)}개 -> 고유 HF 객체 "
        f"{len(objects) if isinstance(objects, dict) else 0}개, 글 {len(rewritten)}편"
    )
    if args.dryRun:
        return
    uploadObjects(localByRemote, args.batchSize)
    writeMigration(catalog, rewritten)
    if args.untrack:
        untrack(paths)


if __name__ == "__main__":
    main()
