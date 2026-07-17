"""HF 미디어 저장소를 콘텐츠 주소 객체와 두 런타임 manifest로 통합한다.

안전 순서:
1. 레거시 바이너리의 SHA-256을 `media/catalog.json`과 대조한다.
2. 빠진 객체를 `objects/sha256/`에 먼저 올린다.
3. 모든 이미지가 객체 경로인 `manifests/*.json`을 올린다.
4. 새 소비자 배포가 끝난 뒤에만 `--delete-legacy`로 옛 폴더를 지운다.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

from blogMedia import IMAGE_SUFFIXES, loadMediaCatalog, mediaPath, saveMediaCatalog
from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi, hf_hub_download
from huggingface_hub.hf_api import RepoFile

from dartlab.core.dataConfig import HF_MEDIA_REPO
from dartlab.core.hfRetry import retryHfCall
from dartlab.pipeline.hfUpload import _resolveHfToken

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "media" / "catalog.json"
COMPANIES_MANIFEST = "manifests/companies.json"
CAROUSELS_MANIFEST = "manifests/carousels.json"
CANONICAL_PREFIXES = ("objects/sha256/", "manifests/")
LEGACY_PREFIXES = ("companies/", "issues/", "podcasts/", "tech-story/", "carousels/")
HASHED_STEM_RE = re.compile(r"^(?P<key>.+)\.(?P<hash>[0-9a-f]{8})$")


def semanticKey(filename: str) -> str:
    stem = PurePosixPath(filename).stem
    match = HASHED_STEM_RE.fullmatch(stem)
    return match.group("key") if match else stem


def loadRemoteJson(repo: str, path: str) -> dict[str, object]:
    localPath = hf_hub_download(repo, path, repo_type="dataset")
    payload = json.loads(Path(localPath).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"HF JSON 최상위 값은 객체여야 함: {path}")
    return payload


def remoteSha256(repo: str, row: RepoFile) -> tuple[str, Path | None]:
    if row.lfs and row.lfs.sha256:
        return row.lfs.sha256, None
    localPath = Path(hf_hub_download(repo, row.path, repo_type="dataset"))
    return hashlib.sha256(localPath.read_bytes()).hexdigest(), localPath


def listRemoteFiles(api: HfApi, repo: str) -> list[RepoFile]:
    rows = api.list_repo_tree(repo, repo_type="dataset", recursive=True, expand=True)
    return [row for row in rows if isinstance(row, RepoFile)]


def ensureCollectionAsset(target: dict[str, str], key: str, sha256: str, source: str) -> None:
    previous = target.get(key)
    if previous and previous != sha256:
        raise ValueError(f"컬렉션 semantic key 충돌: {source} ({previous} != {sha256})")
    target[key] = sha256


def ensureVersionedCollectionAsset(target: dict[str, str], key: str, sha256: str) -> None:
    previous = target.get(key)
    if not previous or previous == sha256:
        target[key] = sha256
        return
    target.pop(key)
    target[f"{key}-{previous[:8]}"] = previous
    target[f"{key}-{sha256[:8]}"] = sha256


def buildCollections(
    companiesIndex: dict[str, object],
    pathToSha: dict[str, str],
) -> tuple[dict[str, object], dict[str, object]]:
    rawCompanies = companiesIndex.get("companies")
    if not isinstance(rawCompanies, dict):
        raise ValueError("companies/index.json companies 계약 위반")

    companyCollection: dict[str, object] = {}
    companyManifest: dict[str, object] = {"version": 3, "companies": {}}
    servedCompanies = companyManifest["companies"]
    assert isinstance(servedCompanies, dict)

    for companyKey, rawCompany in sorted(rawCompanies.items()):
        if not isinstance(rawCompany, dict):
            raise ValueError(f"회사 manifest 계약 위반: {companyKey}")
        rawAssets = rawCompany.get("assets")
        if not isinstance(rawAssets, list):
            raise ValueError(f"회사 assets 계약 위반: {companyKey}")
        collectionAssets: dict[str, str] = {}
        servedAssets: list[dict[str, str]] = []
        for rawAsset in rawAssets:
            if not isinstance(rawAsset, dict):
                continue
            filename = str(rawAsset.get("name") or "")
            oldPath = f"companies/{companyKey}/{filename}"
            sha256 = pathToSha.get(oldPath)
            if not sha256:
                raise ValueError(f"회사 바이너리 누락: {oldPath}")
            key = semanticKey(filename)
            ensureCollectionAsset(collectionAssets, key, sha256, oldPath)
            servedAssets.append({"key": key, "path": "", "sha256": sha256})
        common = {
            "displayName": str(rawCompany.get("displayName") or companyKey),
            "market": str(rawCompany.get("market") or ("kr" if str(companyKey).isdigit() else "us")),
            "similarTo": [str(value) for value in rawCompany.get("similarTo", []) if str(value)],
        }
        companyCollection[str(companyKey)] = {**common, "assets": collectionAssets}
        servedCompanies[str(companyKey)] = {**common, "assets": servedAssets}

    collections: dict[str, object] = {"companies": companyCollection}
    for prefix, collectionName in (
        ("issues", "issues"),
        ("podcasts", "podcasts"),
        ("tech-story", "techStories"),
    ):
        grouped: dict[str, object] = {}
        for oldPath, sha256 in sorted(pathToSha.items()):
            parts = PurePosixPath(oldPath).parts
            if len(parts) < 3 or parts[0] != prefix:
                continue
            slug = parts[1]
            entry = grouped.setdefault(slug, {"assets": {}})
            assert isinstance(entry, dict)
            assets = entry["assets"]
            assert isinstance(assets, dict)
            ensureVersionedCollectionAsset(assets, semanticKey(parts[-1]), sha256)
        collections[collectionName] = grouped
    return collections, companyManifest


def objectPath(catalog: dict[str, object], sha256: str) -> str:
    objects = catalog.get("objects")
    record = objects.get(sha256) if isinstance(objects, dict) else None
    if not isinstance(record, dict) or not record.get("path"):
        raise ValueError(f"카탈로그 객체 누락: {sha256}")
    return str(record["path"])


def fillCompanyManifestPaths(companyManifest: dict[str, object], catalog: dict[str, object]) -> None:
    companies = companyManifest.get("companies")
    if not isinstance(companies, dict):
        raise ValueError("회사 manifest 계약 위반")
    for company in companies.values():
        if not isinstance(company, dict):
            continue
        for asset in company.get("assets", []):
            if isinstance(asset, dict):
                asset["path"] = objectPath(catalog, str(asset.get("sha256") or ""))


def rewriteCarousels(
    carouselsIndex: dict[str, object],
    collections: dict[str, object],
    pathToSha: dict[str, str],
    catalog: dict[str, object],
) -> dict[str, object]:
    rewritten = copy.deepcopy(carouselsIndex)
    posts = rewritten.get("posts")
    companies = collections.get("companies")
    if not isinstance(posts, list) or not isinstance(companies, dict):
        raise ValueError("carousel 또는 company 컬렉션 계약 위반")
    for post in posts:
        if not isinstance(post, dict):
            continue
        rawCode = str(post.get("code") or "")
        companyKey = rawCode if rawCode.isdigit() else rawCode.upper()
        company = companies.get(companyKey)
        companyAssets = company.get("assets") if isinstance(company, dict) else None
        for slide in post.get("slides", []):
            if not isinstance(slide, dict):
                continue
            image = str(slide.get("image") or "")
            if not image:
                continue
            if image.startswith("objects/sha256/"):
                continue
            if "/" in image:
                sha256 = pathToSha.get(image)
            else:
                sha256 = companyAssets.get(image) if isinstance(companyAssets, dict) else None
                if not sha256 and isinstance(companyAssets, dict):
                    sha256 = companyAssets.get(f"bg-{image}")
            if not sha256:
                raise ValueError(f"캐러셀 이미지 해석 실패: {post.get('slug')} -> {image}")
            slide["image"] = objectPath(catalog, str(sha256))
        ogImage = str(post.get("ogImage") or "")
        if ogImage and not ogImage.startswith("objects/sha256/"):
            sha256 = pathToSha.get(ogImage)
            if not sha256:
                post.pop("ogImage", None)
            else:
                post["ogImage"] = objectPath(catalog, sha256)
    rewritten["version"] = 3
    return rewritten


def commitBatches(
    api: HfApi,
    repo: str,
    operations: list[CommitOperationAdd | CommitOperationDelete],
    messagePrefix: str,
    batchSize: int,
) -> None:
    for offset in range(0, len(operations), batchSize):
        batch = operations[offset : offset + batchSize]
        number = offset // batchSize + 1
        total = (len(operations) + batchSize - 1) // batchSize
        print(f"[{number}/{total}] {messagePrefix}: {len(batch)}개")
        retryHfCall(
            api.create_commit,
            repo_id=repo,
            repo_type="dataset",
            operations=batch,
            commit_message=f"{messagePrefix} {number}/{total}",
        )


def plannedLegacyPaths(rows: Iterable[RepoFile]) -> list[str]:
    paths = []
    for row in rows:
        if row.path == ".gitattributes" or row.path.startswith(CANONICAL_PREFIXES):
            continue
        if not row.path.startswith(LEGACY_PREFIXES):
            raise ValueError(f"알 수 없는 HF 루트 경로: {row.path}")
        paths.append(row.path)
    return sorted(paths)


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HF 미디어를 전역 콘텐츠 주소 SSOT로 통합한다.")
    parser.add_argument("--apply", action="store_true", help="객체와 새 manifest를 실제 업로드")
    parser.add_argument(
        "--delete-legacy",
        action="store_true",
        help="새 소비자 배포 확인 뒤 옛 companies/issues/podcasts/tech-story/carousels 경로 삭제",
    )
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--repo", default=HF_MEDIA_REPO)
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    if args.delete_legacy and not args.apply:
        raise SystemExit("--delete-legacy는 --apply와 함께 사용해야 함")
    catalog, errors = loadMediaCatalog(CATALOG_PATH)
    if catalog is None or errors:
        raise SystemExit("중앙 카탈로그 오류: " + "; ".join(errors))

    readApi = HfApi()
    rows = listRemoteFiles(readApi, args.repo)
    repoFiles = {row.path for row in rows}
    companiesIndex = loadRemoteJson(args.repo, "companies/index.json")
    carouselsIndex = loadRemoteJson(args.repo, "carousels/index.json")

    pathToSha: dict[str, str] = {}
    sourceRows: dict[str, RepoFile] = {}
    sourceLocal: dict[str, Path] = {}
    objects = catalog.get("objects")
    if not isinstance(objects, dict):
        raise SystemExit("media/catalog.json objects 계약 위반")
    for row in rows:
        suffix = PurePosixPath(row.path).suffix.lower()
        if not row.path.startswith(("companies/", "issues/", "podcasts/", "tech-story/")):
            continue
        if suffix not in IMAGE_SUFFIXES:
            continue
        sha256, downloaded = remoteSha256(args.repo, row)
        pathToSha[row.path] = sha256
        sourceRows.setdefault(sha256, row)
        if downloaded is not None:
            sourceLocal.setdefault(sha256, downloaded)
        record = objects.get(sha256)
        if not isinstance(record, dict) or not record.get("path"):
            canonicalPath = mediaPath(sha256, suffix)
            objects[sha256] = {"bytes": row.size, "path": canonicalPath}

    collections, companiesManifest = buildCollections(companiesIndex, pathToSha)
    catalog["collections"] = collections
    catalog["manifests"] = {
        "carousels": CAROUSELS_MANIFEST,
        "companies": COMPANIES_MANIFEST,
    }
    fillCompanyManifestPaths(companiesManifest, catalog)
    carouselsManifest = rewriteCarousels(carouselsIndex, collections, pathToSha, catalog)

    missingObjects: dict[str, tuple[str, RepoFile]] = {}
    for sha256, row in sourceRows.items():
        target = objectPath(catalog, sha256)
        if target not in repoFiles:
            missingObjects[sha256] = (target, row)
    legacyPaths = plannedLegacyPaths(rows)
    print(
        f"원격 {len(rows)}개, 레거시 {len(legacyPaths)}개, "
        f"중앙 객체 {len(objects)}개, 신규 객체 {len(missingObjects)}개"
    )
    print(f"새 manifest: {COMPANIES_MANIFEST}, {CAROUSELS_MANIFEST}")
    if not args.apply:
        print("dry-run: HF와 로컬 카탈로그를 변경하지 않음")
        return

    writeApi = HfApi(token=_resolveHfToken())
    addOperations: list[CommitOperationAdd] = []
    for sha256, (target, row) in sorted(missingObjects.items()):
        localPath = sourceLocal.get(sha256)
        if localPath is None:
            localPath = Path(hf_hub_download(args.repo, row.path, repo_type="dataset"))
        addOperations.append(CommitOperationAdd(path_in_repo=target, path_or_fileobj=str(localPath)))
    commitBatches(writeApi, args.repo, addOperations, "미디어 객체 통합", args.batch_size)

    with tempfile.TemporaryDirectory() as tempDir:
        tempRoot = Path(tempDir)
        companiesPath = tempRoot / "companies.json"
        carouselsPath = tempRoot / "carousels.json"
        companiesPath.write_text(
            json.dumps(companiesManifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        carouselsPath.write_text(
            json.dumps(carouselsManifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifestOperations = [
            CommitOperationAdd(path_in_repo=COMPANIES_MANIFEST, path_or_fileobj=str(companiesPath)),
            CommitOperationAdd(path_in_repo=CAROUSELS_MANIFEST, path_or_fileobj=str(carouselsPath)),
        ]
        commitBatches(writeApi, args.repo, manifestOperations, "미디어 manifest 전환", args.batch_size)

    saveMediaCatalog(CATALOG_PATH, catalog)
    if args.delete_legacy:
        current = set(writeApi.list_repo_files(args.repo, repo_type="dataset"))
        required = {COMPANIES_MANIFEST, CAROUSELS_MANIFEST}
        if not required.issubset(current):
            raise SystemExit("새 manifest 원격 검증 실패. 레거시를 삭제하지 않음")
        deleteOperations = [CommitOperationDelete(path_in_repo=path) for path in legacyPaths]
        commitBatches(writeApi, args.repo, deleteOperations, "레거시 미디어 삭제", args.batch_size)

    finalFiles = set(writeApi.list_repo_files(args.repo, repo_type="dataset"))
    missingCanonical = [
        str(record.get("path"))
        for record in objects.values()
        if isinstance(record, dict) and str(record.get("path")) not in finalFiles
    ]
    if missingCanonical:
        raise SystemExit(f"원격 객체 누락 {len(missingCanonical)}개")
    if args.delete_legacy:
        leftovers = [path for path in finalFiles if path.startswith(LEGACY_PREFIXES)]
        if leftovers:
            raise SystemExit(f"레거시 경로 잔존 {len(leftovers)}개")
    print(
        f"완료: 객체 {len(objects)}개, 회사 {len(collections['companies'])}개, "
        f"레거시 삭제 {'완료' if args.delete_legacy else '대기'}"
    )


if __name__ == "__main__":
    main()
