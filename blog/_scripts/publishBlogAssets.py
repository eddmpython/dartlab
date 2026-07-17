"""새 블로그 바이너리를 HF에 올리고 Git에는 경로 매니페스트만 남긴다."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from blogMedia import ASSET_KEY_RE, buildMediaRecord, loadMediaManifest, mediaManifestPath, mediaUrl
from huggingface_hub import CommitOperationAdd, HfApi

from dartlab.core.dataConfig import HF_MEDIA_REPO
from dartlab.core.hfRetry import retryHfCall
from dartlab.pipeline.hfUpload import _resolveHfToken as resolveHfToken

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_FILES = ("brief.json", "plan.json")


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


def buildManifest(
    postDir: Path,
    keys: list[str],
    raw: str,
    existing: dict[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, Path]]:
    creditsPath = postDir / "assets" / "CREDITS.md"
    credits = creditsPath.read_text(encoding="utf-8") if creditsPath.is_file() else ""
    if not credits:
        raise ValueError("assets/CREDITS.md 출처 기록이 없음")

    localByRemote: dict[str, Path] = {}
    assets: dict[str, dict[str, str]] = {}
    existingAssets = (
        existing.get("assets") if isinstance(existing, dict) and isinstance(existing.get("assets"), dict) else {}
    )
    for key in keys:
        if key not in credits:
            raise ValueError(f"assets/CREDITS.md에 assetKey 누락: {key}")
        local = postDir / "assets" / f"{key}.webp"
        if local.is_file():
            record = buildMediaRecord(postDir, key, local)
            localByRemote[record["path"]] = local
        else:
            oldRecord = existingAssets.get(key)
            if not isinstance(oldRecord, dict) or not oldRecord.get("path") or not oldRecord.get("sha256"):
                raise ValueError(f"로컬 staging 이미지와 기존 HF 매니페스트 모두 없음: assets/{key}.webp")
            record = {"path": str(oldRecord["path"]), "sha256": str(oldRecord["sha256"])}
        assets[key] = record

    ogLocal = localOgPath(raw)
    if ogLocal is not None and ogLocal.is_file():
        ogRecord = buildMediaRecord(postDir, "og", ogLocal)
        localByRemote[ogRecord["path"]] = ogLocal
    else:
        oldOg = existing.get("og") if isinstance(existing, dict) else None
        if not isinstance(oldOg, dict) or not oldOg.get("path") or not oldOg.get("sha256"):
            raise ValueError("로컬 OG staging 이미지와 기존 HF 매니페스트 모두 없음")
        ogRecord = {"path": str(oldOg["path"]), "sha256": str(oldOg["sha256"])}
    return {"version": 1, "repo": HF_MEDIA_REPO, "og": ogRecord, "assets": assets}, localByRemote


def applyManifest(
    postDir: Path,
    manifest: dict[str, object],
    raw: str,
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
        updated = updated.replace(f"./assets/{key}.webp", nextUrl)
        oldRecord = oldAssets.get(key)
        if isinstance(oldRecord, dict) and oldRecord.get("path"):
            updated = updated.replace(mediaUrl(str(oldRecord["path"])), nextUrl)
    og = manifest["og"]
    assert isinstance(og, dict)
    updated = re.sub(r"^ogImage:\s*.+$", f"ogImage: {mediaUrl(str(og['path']))}", updated, count=1, flags=re.M)
    (postDir / "index.md").write_text(updated, encoding="utf-8")
    manifestPath = mediaManifestPath(postDir)
    manifestPath.parent.mkdir(parents=True, exist_ok=True)
    manifestPath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    manifest, localByRemote = buildManifest(postDir, keys, raw, existing)
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
            commit_message=f"블로그 미디어: {postDir.name} {len(operations)}개",
        )
    applyManifest(postDir, manifest, raw, existing)
    return manifest


def verifyRemoteAssets(postDir: Path, api: HfApi | None = None) -> list[str]:
    manifest, loadErrors = loadMediaManifest(postDir)
    if manifest is None:
        return []
    if loadErrors:
        return loadErrors
    records: list[dict[str, object]] = []
    og = manifest.get("og")
    if isinstance(og, dict):
        records.append(og)
    assets = manifest.get("assets")
    if isinstance(assets, dict):
        records.extend(record for record in assets.values() if isinstance(record, dict))
    client = api or HfApi()
    errors: list[str] = []
    for record in records:
        remote = str(record.get("path") or "")
        if not remote:
            continue
        try:
            exists = retryHfCall(client.file_exists, repo_id=HF_MEDIA_REPO, filename=remote, repo_type="dataset")
        except Exception as exc:
            errors.append(f"HF 원격 확인 실패({remote}): {exc}")
            continue
        if not exists:
            errors.append(f"HF 미디어 없음: {remote}")
    return errors


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="블로그 이미지와 OG를 HF 미디어 저장소에 발행한다.")
    parser.add_argument("--post", required=True, help="발행할 글 폴더")
    parser.add_argument("--dry-run", action="store_true", help="경로와 계약만 계산하고 업로드·파일 수정은 하지 않음")
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    postDir = Path(args.post)
    if not postDir.is_absolute():
        postDir = REPO_ROOT / postDir
    try:
        manifest = publishAssets(postDir.resolve(), dryRun=args.dryRun)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"블로그 미디어 발행 실패: {exc}") from exc
    assets = manifest.get("assets")
    count = len(assets) if isinstance(assets, dict) else 0
    suffix = "계획만 확인" if args.dryRun else "HF 업로드와 매니페스트 반영 완료"
    print(f"{postDir.name}: 본문 {count}장 + OG 1장 {suffix}")


if __name__ == "__main__":
    main()
