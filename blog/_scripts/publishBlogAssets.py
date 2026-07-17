"""블로그 바이너리를 HF 콘텐츠 주소 객체로 발행하고 중앙 카탈로그만 Git에 남긴다."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from blogMedia import (
    ASSET_KEY_RE,
    MEDIA_CATALOG_VERSION,
    RASTER_SUFFIXES,
    emptyMediaCatalog,
    loadMediaCatalog,
    loadMediaManifest,
    mediaCatalogPath,
    mediaPostKey,
    mediaUrl,
    registerMediaFile,
    saveMediaCatalog,
)
from huggingface_hub import CommitOperationAdd, HfApi

from dartlab.core.dataConfig import HF_MEDIA_REPO
from dartlab.core.hfRetry import retryHfCall
from dartlab.pipeline.hfUpload import _resolveHfToken as resolveHfToken

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_FILES = ("brief.json", "plan.json")
_remoteFilesCache: set[str] | None = None


def loadPlan(postDir: Path) -> dict[str, object]:
    for name in PLAN_FILES:
        path = postDir / name
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        plan = payload.get("plan") if isinstance(payload, dict) and isinstance(payload.get("plan"), dict) else payload
        if isinstance(plan, dict):
            return plan
    raise ValueError("brief.json 또는 plan.json 기획 파일이 없음")


def plannedAssetKeys(plan: dict[str, object]) -> list[str]:
    if plan.get("contractVersion") != 2:
        raise ValueError("HF 전용 발행은 contractVersion 2 글만 지원함")
    rows = plan.get("imagePlan")
    if not isinstance(rows, list) or not rows:
        raise ValueError("imagePlan이 비어 있음")
    keys: list[str] = []
    for idx, row in enumerate(rows, start=1):
        key = str(row.get("assetKey") or "").strip() if isinstance(row, dict) else ""
        if not ASSET_KEY_RE.fullmatch(key):
            raise ValueError(f"imagePlan[{idx}].assetKey가 영문 kebab-case가 아님")
        if key in keys:
            raise ValueError(f"imagePlan[{idx}].assetKey 중복: {key}")
        keys.append(key)
    return keys


def frontmatterValue(raw: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.M)
    return match.group(1).strip().strip("\"'") if match else ""


def localOgPath(raw: str) -> Path | None:
    value = frontmatterValue(raw, "ogImage")
    if not value.startswith("/thumbnails/"):
        return None
    return REPO_ROOT / "landing" / "static" / value.lstrip("/")


def sourcePath(localPath: Path) -> str:
    try:
        return localPath.relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"저장소 밖 미디어는 발행할 수 없음: {localPath}") from exc


def localPlannedAsset(postDir: Path, key: str) -> Path | None:
    matches = [postDir / "assets" / f"{key}{suffix}" for suffix in RASTER_SUFFIXES]
    existing = [path for path in matches if path.is_file()]
    if len(existing) > 1:
        names = ", ".join(path.name for path in existing)
        raise ValueError(f"같은 assetKey의 staging 이미지가 여러 개임: {names}")
    return existing[0] if existing else None


def loadCatalog(postDir: Path) -> dict[str, object]:
    catalogPath = mediaCatalogPath(postDir)
    catalog, errors = loadMediaCatalog(catalogPath)
    if catalog is None and not catalogPath.exists():
        return emptyMediaCatalog()
    if catalog is None or errors:
        raise ValueError("; ".join(errors))
    return catalog


def buildManifest(
    postDir: Path,
    keys: list[str],
    raw: str,
    existing: dict[str, object] | None = None,
    catalog: dict[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, Path], dict[str, object]]:
    creditsPath = postDir / "CREDITS.md"
    credits = creditsPath.read_text(encoding="utf-8") if creditsPath.is_file() else ""
    if not credits:
        raise ValueError("CREDITS.md 출처 기록이 없음")

    nextCatalog = catalog or loadCatalog(postDir)
    localByRemote: dict[str, Path] = {}
    assets: dict[str, dict[str, str]] = {}
    assetSources: dict[str, str] = {}
    stagingSources: set[str] = set()
    existingAssets = (
        existing.get("assets") if isinstance(existing, dict) and isinstance(existing.get("assets"), dict) else {}
    )
    for key in keys:
        if key not in credits:
            raise ValueError(f"CREDITS.md에 assetKey 누락: {key}")
        local = localPlannedAsset(postDir, key)
        if local is not None:
            source = sourcePath(local)
            record = registerMediaFile(nextCatalog, source, local)
            localByRemote[record["path"]] = local
        else:
            oldRecord = existingAssets.get(key)
            if not isinstance(oldRecord, dict) or not oldRecord.get("path") or not oldRecord.get("sha256"):
                suffixes = ", ".join(RASTER_SUFFIXES)
                raise ValueError(f"로컬 staging 이미지와 기존 HF 카탈로그 모두 없음: assets/{key} ({suffixes})")
            record = {
                "path": str(oldRecord["path"]),
                "sha256": str(oldRecord["sha256"]),
                "source": str(oldRecord.get("source") or ""),
            }
        if not record["source"]:
            raise ValueError(f"중앙 카탈로그 source 누락: {key}")
        assets[key] = record
        assetSources[key] = record["source"]
        stagingSources.add(record["source"])

    existingDiagrams = (
        existing.get("diagrams") if isinstance(existing, dict) and isinstance(existing.get("diagrams"), dict) else {}
    )
    diagrams: dict[str, dict[str, str]] = {}
    diagramSources: dict[str, str] = {}
    for key, oldRecord in existingDiagrams.items():
        if not isinstance(oldRecord, dict) or not oldRecord.get("source"):
            continue
        record = {
            "path": str(oldRecord.get("path") or ""),
            "sha256": str(oldRecord.get("sha256") or ""),
            "source": str(oldRecord["source"]),
        }
        diagrams[str(key)] = record
        diagramSources[str(key)] = record["source"]
        stagingSources.add(record["source"])
    for local in sorted(postDir.joinpath("assets").glob("*.svg")):
        key = local.stem
        if not ASSET_KEY_RE.fullmatch(key):
            raise ValueError(f"SVG 파일명이 영문 kebab-case가 아님: {local.name}")
        source = sourcePath(local)
        record = registerMediaFile(nextCatalog, source, local)
        localByRemote[record["path"]] = local
        diagrams[key] = record
        diagramSources[key] = source
        stagingSources.add(source)

    ogLocal = localOgPath(raw)
    if ogLocal is not None and ogLocal.is_file():
        ogSource = sourcePath(ogLocal)
        ogRecord = registerMediaFile(nextCatalog, ogSource, ogLocal)
        localByRemote[ogRecord["path"]] = ogLocal
    else:
        oldOg = existing.get("og") if isinstance(existing, dict) else None
        if not isinstance(oldOg, dict) or not oldOg.get("path") or not oldOg.get("sha256"):
            raise ValueError("로컬 OG staging 이미지와 기존 HF 카탈로그 모두 없음")
        ogRecord = {
            "path": str(oldOg["path"]),
            "sha256": str(oldOg["sha256"]),
            "source": str(oldOg.get("source") or ""),
        }
    if not ogRecord["source"]:
        raise ValueError("중앙 카탈로그 OG source 누락")

    cardRecord: dict[str, str] | None = None
    cardLocal = ogLocal.with_name(f"{ogLocal.stem}-card{ogLocal.suffix}") if ogLocal is not None else None
    if cardLocal is not None and cardLocal.is_file():
        cardSource = sourcePath(cardLocal)
        cardRecord = registerMediaFile(nextCatalog, cardSource, cardLocal)
        localByRemote[cardRecord["path"]] = cardLocal
    else:
        oldCard = existing.get("card") if isinstance(existing, dict) else None
        if isinstance(oldCard, dict) and oldCard.get("path") and oldCard.get("sha256") and oldCard.get("source"):
            cardRecord = {
                "path": str(oldCard["path"]),
                "sha256": str(oldCard["sha256"]),
                "source": str(oldCard["source"]),
            }

    posts = nextCatalog.setdefault("posts", {})
    if not isinstance(posts, dict):
        raise ValueError("media/catalog.json posts 계약 위반")
    oldPost = posts.get(mediaPostKey(postDir))
    if isinstance(oldPost, dict) and isinstance(oldPost.get("staging"), list):
        stagingSources.update(str(source) for source in oldPost["staging"])
    postEntry: dict[str, object] = {
        "assets": assetSources,
        "diagrams": diagramSources,
        "og": ogRecord["source"],
        "staging": sorted(stagingSources),
    }
    if cardRecord is not None:
        postEntry["card"] = cardRecord["source"]
        stagingSources.add(cardRecord["source"])
        postEntry["staging"] = sorted(stagingSources)
    posts[mediaPostKey(postDir)] = postEntry
    manifest: dict[str, object] = {
        "version": MEDIA_CATALOG_VERSION,
        "repo": HF_MEDIA_REPO,
        "og": ogRecord,
        "assets": assets,
        "diagrams": diagrams,
    }
    if cardRecord is not None:
        manifest["card"] = cardRecord
    return manifest, localByRemote, nextCatalog


def applyManifest(
    postDir: Path,
    manifest: dict[str, object],
    raw: str,
    catalog: dict[str, object],
    existing: dict[str, object] | None = None,
) -> None:
    assets = manifest["assets"]
    assert isinstance(assets, dict)
    updated = raw
    oldAssets = (
        existing.get("assets") if isinstance(existing, dict) and isinstance(existing.get("assets"), dict) else {}
    )
    for key, record in assets.items():
        assert isinstance(record, dict)
        nextUrl = mediaUrl(str(record["path"]))
        filename = Path(str(record.get("source") or f"{key}.webp")).name
        updated = updated.replace(f"./assets/{filename}", nextUrl)
        updated = updated.replace(f"assets/{filename}", nextUrl)
        oldRecord = oldAssets.get(key)
        if isinstance(oldRecord, dict) and oldRecord.get("path"):
            updated = updated.replace(mediaUrl(str(oldRecord["path"])), nextUrl)
    diagrams = manifest.get("diagrams")
    oldDiagrams = (
        existing.get("diagrams") if isinstance(existing, dict) and isinstance(existing.get("diagrams"), dict) else {}
    )
    if isinstance(diagrams, dict):
        for key, record in diagrams.items():
            if not isinstance(record, dict):
                continue
            nextUrl = mediaUrl(str(record.get("path") or ""))
            filename = Path(str(record.get("source") or f"{key}.svg")).name
            updated = updated.replace(f"./assets/{filename}", nextUrl)
            updated = updated.replace(f"assets/{filename}", nextUrl)
            oldRecord = oldDiagrams.get(key)
            if isinstance(oldRecord, dict) and oldRecord.get("path"):
                updated = updated.replace(mediaUrl(str(oldRecord["path"])), nextUrl)
    og = manifest["og"]
    assert isinstance(og, dict)
    updated = re.sub(r"^ogImage:\s*.+$", f"ogImage: {mediaUrl(str(og['path']))}", updated, count=1, flags=re.M)
    card = manifest.get("card")
    if isinstance(card, dict) and card.get("path"):
        cardLine = f"cardPreview: {mediaUrl(str(card['path']))}"
        if re.search(r"^cardPreview:\s*.+$", updated, re.M):
            updated = re.sub(r"^cardPreview:\s*.+$", cardLine, updated, count=1, flags=re.M)
        else:
            updated = re.sub(r"^(ogImage:\s*.+)$", rf"\1\n{cardLine}", updated, count=1, flags=re.M)
    postDir.joinpath("index.md").write_text(updated, encoding="utf-8")
    saveMediaCatalog(mediaCatalogPath(postDir), catalog)


def manifestRecords(manifest: dict[str, object]) -> list[dict[str, object]]:
    """중앙 카탈로그 포스트 뷰에서 원격 검증할 객체 레코드를 모은다."""
    records: list[dict[str, object]] = []
    for role in ("og", "card"):
        record = manifest.get(role)
        if isinstance(record, dict):
            records.append(record)
    for role in ("assets", "diagrams"):
        group = manifest.get(role)
        if isinstance(group, dict):
            records.extend(record for record in group.values() if isinstance(record, dict))
    return records


def verifyManifestRemote(manifest: dict[str, object], client: HfApi, *, useList: bool = False) -> list[str]:
    """본문을 치환하기 전에 모든 콘텐츠 주소 객체가 HF에 실재하는지 확인한다."""
    remoteFiles: set[str] | None = None
    global _remoteFilesCache
    if useList:
        try:
            if _remoteFilesCache is None:
                _remoteFilesCache = set(retryHfCall(client.list_repo_files, repo_id=HF_MEDIA_REPO, repo_type="dataset"))
            remoteFiles = _remoteFilesCache
        except Exception as exc:
            return [f"HF 원격 목록 확인 실패: {exc}"]
    errors: list[str] = []
    checked: set[str] = set()
    for record in manifestRecords(manifest):
        remote = str(record.get("path") or "")
        if not remote or remote in checked:
            continue
        checked.add(remote)
        try:
            exists = (
                remote in remoteFiles
                if remoteFiles is not None
                else retryHfCall(client.file_exists, repo_id=HF_MEDIA_REPO, filename=remote, repo_type="dataset")
            )
        except Exception as exc:
            errors.append(f"HF 원격 확인 실패({remote}): {exc}")
            continue
        if not exists:
            errors.append(f"HF 미디어 없음: {remote}")
    return errors


def cleanupLocalStaging(postDir: Path, localPaths: list[Path]) -> None:
    """HF 검증이 끝난 미디어 작업본만 지우고 빈 staging 디렉터리를 제거한다."""
    postAssets = postDir.joinpath("assets").resolve()
    thumbnailRoot = REPO_ROOT.joinpath("landing", "static", "thumbnails").resolve()
    allowedRoots = (postAssets, thumbnailRoot)
    resolvedPaths: list[Path] = []
    for localPath in localPaths:
        resolved = localPath.resolve()
        if not any(resolved.is_relative_to(root) for root in allowedRoots):
            raise ValueError(f"허용된 staging 밖 파일은 정리할 수 없음: {localPath}")
        resolvedPaths.append(resolved)
    for path in sorted(set(resolvedPaths)):
        path.unlink(missing_ok=True)
    for directory in sorted({path.parent for path in resolvedPaths}, key=lambda path: len(path.parts), reverse=True):
        if directory in allowedRoots and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()


def publishAssets(postDir: Path, *, dryRun: bool = False, api: HfApi | None = None) -> dict[str, object]:
    indexPath = postDir / "index.md"
    if not indexPath.is_file():
        raise ValueError(f"index.md 없음: {postDir}")
    raw = indexPath.read_text(encoding="utf-8")
    plan = loadPlan(postDir)
    keys = plannedAssetKeys(plan)
    existing, existingErrors = loadMediaManifest(postDir)
    if existingErrors:
        existing = None
    catalog = loadCatalog(postDir)
    manifest, localByRemote, nextCatalog = buildManifest(postDir, keys, raw, existing, catalog)
    if dryRun:
        return manifest

    client = api or HfApi(token=resolveHfToken())
    operations: list[CommitOperationAdd] = []
    for remote, local in localByRemote.items():
        exists = retryHfCall(client.file_exists, repo_id=HF_MEDIA_REPO, filename=remote, repo_type="dataset")
        if not exists:
            operations.append(CommitOperationAdd(path_in_repo=remote, path_or_fileobj=str(local)))
    if operations:
        retryHfCall(
            client.create_commit,
            repo_id=HF_MEDIA_REPO,
            repo_type="dataset",
            operations=operations,
            commit_message=f"블로그 미디어 객체: {postDir.name} {len(operations)}개",
        )
    remoteErrors = verifyManifestRemote(manifest, client)
    if remoteErrors:
        raise RuntimeError("; ".join(remoteErrors))
    applyManifest(postDir, manifest, raw, nextCatalog, existing)
    cleanupLocalStaging(postDir, list(localByRemote.values()))
    return manifest


def verifyRemoteAssets(postDir: Path, api: HfApi | None = None) -> list[str]:
    manifest, loadErrors = loadMediaManifest(postDir)
    if manifest is None:
        return loadErrors
    if loadErrors:
        return loadErrors
    client = api or HfApi()
    return verifyManifestRemote(manifest, client, useList=api is None)


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="블로그 이미지·SVG·OG를 HF 콘텐츠 주소 객체로 발행한다.")
    parser.add_argument("--post", required=True, help="발행할 글 폴더")
    parser.add_argument(
        "--dry-run",
        dest="dryRun",
        action="store_true",
        help="경로와 계약만 계산하고 업로드·파일 수정은 하지 않음",
    )
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    postDir = Path(args.post)
    if not postDir.is_absolute():
        postDir = REPO_ROOT / postDir
    try:
        manifest = publishAssets(postDir.resolve(), dryRun=args.dryRun)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"블로그 미디어 발행 실패: {exc}") from exc
    assets = manifest.get("assets")
    count = len(assets) if isinstance(assets, dict) else 0
    diagrams = manifest.get("diagrams")
    diagramCount = len(diagrams) if isinstance(diagrams, dict) else 0
    suffix = "계획만 확인" if args.dryRun else "HF 업로드와 중앙 카탈로그 반영 완료"
    print(f"{postDir.name}: 본문 이미지 {count}장 + SVG {diagramCount}개 + OG 1장 {suffix}")


if __name__ == "__main__":
    main()
