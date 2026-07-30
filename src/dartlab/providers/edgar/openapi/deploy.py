"""EDGAR 데이터 → HuggingFace 데이터셋 배포.

⛔ **원칙: finance / meta 는 HF 에 올리지 않는다.**
SEC 자체 벌크(`companyfacts.zip` daily + 분기 `{Y}q{Q}.zip`) 가 원본이고
사용자 PC 에서 자동 다운로드·변환하므로 HF 미러링은 낭비 + rate limit 원인.

HF 에 올리는 것은 **dartlab 파생물** 만:
- `scan` → edgar/scan + US terminal aggregate (검증된 cohort 단일 CAS commit)
- `docs` → edgar/docs  (submissions API HTML 섹션 파싱 결과, PR-E7 안전 게이트 통과 후 폐기 대상)
- `sections` → edgar/sections  (period-sharded SSOT, plan delegated-prancing-tower PR-E3)

사용법::

    from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF
    deployEdgarToHF(categories=["scan", "docs", "sections"])  # 기본값

`data.sec.gov/api/xbrl/companyfacts` API 파생물은 업로드 대상이 아니다 —
사용자가 `c.refreshFromApi()` 로 로컬만 갱신한다.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import string
from pathlib import Path

from dartlab.core.dataConfig import DATA_RELEASES, HF_REPO

_log = logging.getLogger(__name__)

# HF 에 업로드 허용된 카테고리 — dartlab 파생물만.
# finance 는 본 deploy 가 아니라 **edgar stage(pipeline.stages.edgar)** 가 detectChanged 증분으로
# edgar/finance 에 발행한다(브라우저 터미널 HF 직독 패리티). 여기서는 중복 방지로 계속 제외.
# meta 는 SEC 벌크가 원본(사용자 PC 자동 다운로드) — 미러링 없음.
_CATEGORY_MAP = {
    "scan": "edgarScan",
    "docs": "edgarDocs",
    # plan delegated-prancing-tower PR-E3 — period-sharded sections SSOT artifact.
    # nested=True (data/edgar/sections/{ticker}/{period}.parquet) — rglob 자동 처리.
    "sections": "edgarSections",
    # EDGAR panel(공시 수평화) artifact — DART panel 미러. flat (data/edgar/panel/{ticker}.parquet).
    "panel": "edgarPanel",
}

# 업로드 명시 차단 목록 (원본이 SEC 벌크, HF 미러링 정책상 제외)
_BULK_ORIGIN_CATEGORIES = {"finance", "meta"}
_SCAN_MANIFEST_NAME = "prebuild-manifest.json"
_SCAN_MANIFEST_KIND = "dartlab.edgar.scan.prebuild"
_SCAN_MANIFEST_ARTIFACT_COUNT = 8


def _validateScanManifest(scanDir: Path, parquets: list[Path]) -> Path:
    """scan validator가 봉인한 manifest와 로컬 artifact digest 일치를 검증한다."""

    manifestPath = scanDir / _SCAN_MANIFEST_NAME
    if not manifestPath.is_file():
        raise FileNotFoundError(f"EDGAR scan prebuild manifest 누락: {manifestPath}")
    payload = json.loads(manifestPath.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts")
    if (
        payload.get("kind") != _SCAN_MANIFEST_KIND
        or payload.get("schemaVersion") != 1
        or not isinstance(artifacts, list)
        or len(artifacts) != _SCAN_MANIFEST_ARTIFACT_COUNT
    ):
        raise ValueError(f"EDGAR scan prebuild manifest 계약 불일치: {manifestPath}")
    available = {path.relative_to(scanDir).as_posix(): path for path in parquets}
    declared: set[str] = set()
    for artifact in artifacts:
        relative = artifact.get("path") if isinstance(artifact, dict) else None
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or relative in declared
        ):
            raise ValueError(f"EDGAR scan prebuild manifest path 위반: {relative!r}")
        declared.add(relative)
        path = available.get(relative)
        expectedDigest = artifact.get("sha256")
        if path is None or not isinstance(expectedDigest, str) or len(expectedDigest) != 64:
            raise ValueError(f"EDGAR scan prebuild manifest artifact 위반: {relative}")
        if any(character not in string.hexdigits for character in expectedDigest):
            raise ValueError(f"EDGAR scan prebuild manifest digest 형식 위반: {relative}")
        with path.open("rb") as source:
            actualDigest = hashlib.file_digest(source, "sha256").hexdigest()
        if path.stat().st_size != artifact.get("bytes") or actualDigest != expectedDigest.lower():
            raise ValueError(f"EDGAR scan prebuild artifact digest 불일치: {relative}")
    return manifestPath


def deployEdgarToHF(
    categories: list[str] | None = None,
    *,
    token: str | None = None,
    dryRun: bool = False,
    commitMessage: str | None = None,
) -> dict[str, int]:
    """EDGAR 파생 데이터를 HuggingFace datasets repo에 category 단위로 배포한다.

    scan은 prebuild 계약 검증 후 terminal aggregate와 함께 단일 CAS commit으로
    발행한다. 나머지 카테고리는 단일 upload_folder commit으로 발행한다.

    Parameters
    ----------
    categories : list
        업로드할 카테고리: "scan" | "docs" | "sections" | "panel".
        None 이면 ["scan", "docs", "sections"].
    token : str
        HuggingFace API 토큰 (없으면 HF_TOKEN 환경변수).
    dryRun : bool
        True 면 업로드하지 않고 파일 개수만 반환.
    commitMessage : str
        커밋 메시지. 없으면 한국어 category별 기본값.

    Returns
    -------
    dict : {"finance": N, ...} 업로드한 카테고리별 파일 수.

    Raises:
        ValueError: HF_TOKEN 부재, scan 계약 위반.
        FileNotFoundError: 배포 입력 또는 scan terminal aggregate 누락.
        Exception: HF 조회와 배포 실패를 원인 그대로 전파.

    Example:
        >>> deployEdgarToHF(categories=["scan"], dryRun=True)

    Args:
        categories: 배포 카테고리 ("scan"/"docs"). None 이면 전체.
        token: HF API 토큰. None 이면 HF_TOKEN 환경변수.
        dryRun: True 면 실제 업로드 X, 검증만.
        commitMessage: HF commit message. None 이면 자동.

    Returns:
        dict[str, int] — 카테고리 별 업로드 건수.

    SeeAlso:
        - ``DATA_RELEASES`` (frame.dataConfig) — HF 대상 카테고리.

    Requires:
        - dartlab
        - logging

    Capabilities:
        - EDGAR dartlab 파생물 (scan/docs) → HuggingFace 데이터셋 배포. finance/meta 차단.

    Guide:
        - 운영자 배포 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal deploy — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - finance/meta 업로드 시도 → 정책 차단.
            - HF_TOKEN 미설정 → 업로드 실패.
        OutputSchema:
            - dict[str, int] — 카테고리 별 업로드 건수.
        Prerequisites:
            - HF_TOKEN + dartlab 파생물 (scan/docs).
        Freshness:
            - 본 함수 호출 시점.
        Dataflow:
            - 로컬 parquet → HuggingFace API → HF 데이터셋.
        TargetMarkets:
            - US (EDGAR) HF 배포.
    """
    from huggingface_hub import CommitOperationAdd, HfApi

    from dartlab.core.hfRetry import retryHfCall

    hfToken = token or os.getenv("HF_TOKEN")
    if not hfToken and not dryRun:
        raise ValueError("HF_TOKEN이 필요합니다. 환경변수 또는 token 파라미터로 설정하세요.")

    cats = categories or ["scan", "docs", "sections"]

    # plan delegated-prancing-tower PR-E7b — 운영자 트리거 게이트.
    # DARTLAB_EDGAR_DOCS_DEPRECATED=1 환경변수 set 시 'docs' 카테고리 HF push 자동 제외.
    # PR-E7a 의 sectionsParityEdgar 4 주 연속 0 violations 통과 후 운영자가 env set.
    import os as _os

    if _os.environ.get("DARTLAB_EDGAR_DOCS_DEPRECATED", "").strip() in ("1", "true", "True"):
        if "docs" in cats:
            cats = [c for c in cats if c != "docs"]
            _log.info("[deploy] DARTLAB_EDGAR_DOCS_DEPRECATED gate — 'docs' 카테고리 자동 제외")

    validCats: list[str] = []
    for cat in cats:
        if cat in _BULK_ORIGIN_CATEGORIES:
            _log.info(
                "[deploy] '%s' 는 SEC 벌크가 원본이라 HF 미러링 정책상 제외 (사용자 PC 에서 자동 다운로드). 스킵.",
                cat,
            )
            continue
        configKey = _CATEGORY_MAP.get(cat, cat)
        if configKey not in DATA_RELEASES:
            _log.info(f"[deploy] 카테고리 '{cat}' → configKey '{configKey}'가 DATA_RELEASES에 없음. 스킵.")
            continue
        validCats.append(cat)

    if not validCats:
        _log.info("[deploy] 유효한 카테고리가 없습니다.")
        return {}

    api = HfApi(token=hfToken) if not dryRun else None
    result: dict[str, int] = {}

    for cat in validCats:
        configKey = _CATEGORY_MAP.get(cat, cat)
        config = DATA_RELEASES[configKey]

        from dartlab.core.dataLoader import _getDataRoot

        localDir = _getDataRoot() / config["dir"]
        if not localDir.exists():
            if dryRun:
                _log.info(f"[deploy] {localDir} 없음. 스킵.")
                result[cat] = 0
                continue
            raise FileNotFoundError(f"EDGAR 배포 디렉토리 없음: category={cat}, path={localDir}")

        # scan/meta 는 하위 폴더 구조가 있음 (scan/finance.parquet, meta/sub/*.parquet)
        parquets = sorted(localDir.rglob("*.parquet"))
        if not parquets:
            if dryRun:
                _log.info(f"[deploy] {localDir}에 parquet 없음. 스킵.")
                result[cat] = 0
                continue
            raise FileNotFoundError(f"EDGAR 배포 parquet 없음: category={cat}, path={localDir}")
        temporaryArtifacts = [str(path) for path in parquets if cat == "scan" and path.name.startswith((".", "_"))]
        if temporaryArtifacts:
            raise RuntimeError(f"EDGAR 배포 임시 artifact 잔존: {temporaryArtifacts}")

        hfDir = config["dir"]
        nFiles = len(parquets)

        if dryRun:
            _log.info(f"[deploy] DRY RUN — {cat}: {nFiles}개 파일 → {HF_REPO}/{hfDir}/")
            result[cat] = nFiles
            continue

        assert api is not None
        msg = commitMessage or f"갱신: EDGAR {cat} ({nFiles}개 파일)"
        if cat == "scan":
            manifestPath = _validateScanManifest(localDir, parquets)
            dataRoot = _getDataRoot()
            aggregates = (
                (dataRoot.parent / "landing/static/dashboards/finance-us.json", "landing/dashboards/finance-us.json"),
                (dataRoot.parent / "landing/static/map/search-index-us.json", "landing/map/search-index-us.json"),
            )
            missingAggregates = [str(path) for path, _ in aggregates if not path.is_file()]
            if missingAggregates:
                raise FileNotFoundError(f"EDGAR scan cohort aggregate 누락: {missingAggregates}")
            operations = [
                CommitOperationAdd(
                    path_in_repo=f"{hfDir}/{path.relative_to(localDir).as_posix()}",
                    path_or_fileobj=str(path),
                )
                for path in parquets
            ]
            operations.append(
                CommitOperationAdd(
                    path_in_repo=f"{hfDir}/{manifestPath.name}",
                    path_or_fileobj=str(manifestPath),
                )
            )
            operations.extend(
                CommitOperationAdd(path_in_repo=repoPath, path_or_fileobj=str(path)) for path, repoPath in aggregates
            )
            parentCommit = retryHfCall(api.repo_info, repo_id=HF_REPO, repo_type="dataset").sha
            retryHfCall(
                api.create_commit,
                repo_id=HF_REPO,
                repo_type="dataset",
                operations=operations,
                commit_message=msg,
                parent_commit=parentCommit,
            )
            result[cat] = len(operations)
            _log.info(f"[deploy] {cat}: {len(operations)}개 cohort 파일 업로드 완료 (단일 커밋)")
        else:
            _log.info(f"[deploy] {cat}: {nFiles}개 파일 upload_folder → {HF_REPO}/{hfDir}/")
            retryHfCall(
                api.upload_folder,
                folder_path=str(localDir),
                path_in_repo=hfDir,
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message=msg,
                ignore_patterns=["*.freshness", "*.etag", "*.tmp-*", "*.tmp", "*.bak-*"],
            )
            result[cat] = nFiles
            _log.info(f"[deploy] {cat}: {nFiles} 업로드 완료 (단일 커밋)")

    return result
