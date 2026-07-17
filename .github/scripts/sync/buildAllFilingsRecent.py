"""비정기공시 메타를 종목코드 버킷으로 증분 빌드하고 HF에 원자적으로 배포한다.

일자별 원본은 이미 증분 수집되지만, 예전 빌더는 실행할 때마다 전 이력
``recent.parquet``를 내려받아 합치고 다시 올렸다. 이 파일은 백필이 깊어질수록 계속
커졌고 CI 시간과 메모리가 전체 이력 크기에 비례했다.

현재 레이아웃은 다음과 같다.

* ``dart/allFilings/byCode/{prefix}_recent.parquet``: stock_code 앞 2자리 버킷
* ``dart/allFilings/byCode/manifest.json``: 버킷 목록과 행 수, 날짜 범위
* ``dart/allFilings/market_recent.parquet``: 전체 시장 최근 90일 피드

manifest가 없는 첫 실행만 기존 ``recent.parquet``를 읽어 버킷을 만든다. 이후 실행은
로컬 일자 파일에 등장한 버킷과 작은 시장 피드만 읽고 쓴다. 파티션과 manifest는 HF
단일 commit으로 게시하므로 독자는 완성된 세대만 본다.

Usage:
    uv run python -X utf8 .github/scripts/sync/buildAllFilingsRecent.py [--no-push]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES, repoFor
from dartlab.gather.dart.allFilingsCollector import _ALLFILINGS_DIR_KEY, _META_SUFFIX, _allFilingsDir

_KEEP = ["stock_code", "corp_name", "rcept_dt", "report_nm", "rcept_no", "flr_nm"]
_REGULAR = ("사업보고서", "반기보고서", "분기보고서")
_LEGACY_NAME = "recent.parquet"
_PARTITION_DIR = "byCode"
_MANIFEST_NAME = "manifest.json"
_MANIFEST_VERSION = 1
_ROW_GROUP = 20_000

_FEED_NAME = "market_recent.parquet"
_FEED_WINDOW_DAYS = 90
_FEED_ROW_GROUP = 5_000
_FEED_MAX_BYTES = 1_536 * 1024


@dataclass(frozen=True)
class BuildResult:
    """이번 실행에서 작성한 변경 파티션과 게시 메타데이터."""

    partitions: dict[str, Path]
    feedPath: Path
    manifestPath: Path
    bootstrap: bool


def _relDir() -> str:
    return str(DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]).strip("/")


def _bucketKey(stockCode: str) -> str:
    code = str(stockCode).strip()
    if len(code) != 6 or not code.isdigit():
        raise ValueError(f"유효하지 않은 stock_code: {stockCode!r}")
    return code[:2]


def _partitionName(bucket: str) -> str:
    return f"{bucket}_recent.parquet"


def _emptyFrame() -> pl.DataFrame:
    return pl.DataFrame(schema={name: pl.Utf8 for name in _KEEP})


def _normalize(frames: list[pl.DataFrame]) -> pl.DataFrame:
    usable = [frame for frame in frames if frame is not None and frame.width]
    if not usable:
        return _emptyFrame()
    out = pl.concat(usable, how="diagonal_relaxed")
    missing = [name for name in _KEEP if name not in out.columns]
    if missing:
        out = out.with_columns(pl.lit(None, dtype=pl.Utf8).alias(name) for name in missing)
    out = out.select(_KEEP).with_columns(pl.col(name).cast(pl.Utf8) for name in _KEEP)
    return (
        out.filter(
            pl.col("stock_code").str.strip_chars().str.len_chars().eq(6)
            & pl.col("stock_code").str.contains(r"^\d{6}$")
            & ~pl.col("report_nm").fill_null("").str.contains("|".join(_REGULAR))
        )
        .unique(subset=["rcept_no"], keep="first")
        .sort(["stock_code", "rcept_dt"], descending=[False, True])
    )


def _localFrame() -> pl.DataFrame:
    """현재 실행이 수집한 일자 parquet만 합친다.

    GitHub runner에는 forward 또는 이번 백필 범위만 있으므로 이 프레임은 전체 원격 이력과
    함께 커지지 않는다. 산출 파일과 meta 파일은 입력에서 제외한다.
    """
    outDir = _allFilingsDir()
    files = sorted(
        path
        for path in outDir.glob("*.parquet")
        if _META_SUFFIX not in path.stem and path.name not in {_LEGACY_NAME, _FEED_NAME}
    )
    frames: list[pl.DataFrame] = []
    for path in files:
        try:
            schema = pl.read_parquet_schema(path)
            frames.append(pl.read_parquet(path, columns=[name for name in _KEEP if name in schema]))
        except Exception as exc:  # noqa: BLE001 - 손상된 일자 파일 하나를 격리한다.
            print(f"[skip] {path.name}: {type(exc).__name__}", file=sys.stderr)
    return _normalize(frames)


def _download(remoteName: str) -> Path | None:
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError

    from dartlab.core.hfRetry import retryHfCall

    try:
        path = retryHfCall(
            hf_hub_download,
            repo_id=repoFor(_ALLFILINGS_DIR_KEY),
            repo_type="dataset",
            filename=f"{_relDir()}/{remoteName}",
            token=os.environ.get("HF_TOKEN") or None,
        )
        return Path(path)
    except EntryNotFoundError:  # 최초 이관이나 새 버킷이면 파일이 없다.
        return None


def _remoteManifest() -> dict[str, Any] | None:
    path = _download(f"{_PARTITION_DIR}/{_MANIFEST_NAME}")
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("formatVersion") != _MANIFEST_VERSION or not isinstance(payload.get("partitions"), list):
        return None
    return payload


def _remoteFrame(remoteName: str) -> pl.DataFrame | None:
    path = _download(remoteName)
    if path is None:
        return None
    try:
        return pl.read_parquet(path, columns=_KEEP)
    except Exception:  # noqa: BLE001 - 손상 원격 파일은 해당 버킷 로컬분으로 복구한다.
        return None


def _legacyFrame() -> pl.DataFrame | None:
    return _remoteFrame(_LEGACY_NAME)


def _partitionFrame(bucket: str) -> pl.DataFrame | None:
    return _remoteFrame(f"{_PARTITION_DIR}/{_partitionName(bucket)}")


def _feedFrame() -> pl.DataFrame | None:
    return _remoteFrame(_FEED_NAME)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _partitionEntry(bucket: str, frame: pl.DataFrame, path: Path) -> dict[str, Any]:
    return {
        "bucket": bucket,
        "file": _partitionName(bucket),
        "rows": frame.height,
        "minDate": str(frame["rcept_dt"].min() or ""),
        "maxDate": str(frame["rcept_dt"].max() or ""),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _writeFeed(frames: list[pl.DataFrame]) -> Path:
    out = _normalize(frames)
    if out.is_empty():
        raise SystemExit("[feed] 로컬과 기존 시장 피드가 모두 비어 있음")
    dataMax = out["rcept_dt"].max()
    if dataMax is None:
        raise SystemExit("[feed] rcept_dt가 전부 null이라 피드를 만들 수 없음")
    cutoff = (datetime.strptime(str(dataMax), "%Y%m%d") - timedelta(days=_FEED_WINDOW_DAYS)).strftime("%Y%m%d")
    feed = out.filter(pl.col("rcept_dt") >= cutoff).sort("rcept_dt", descending=True)
    dest = _allFilingsDir() / _FEED_NAME
    feed.write_parquet(dest, compression="zstd", row_group_size=_FEED_ROW_GROUP)
    size = dest.stat().st_size
    if size > _FEED_MAX_BYTES:
        raise SystemExit(
            f"[feed] {dest.name} {size / 1e6:.2f}MB > {_FEED_MAX_BYTES / 1e6:.2f}MB. "
            f"whole-file GET 임계를 넘었으므로 {_FEED_WINDOW_DAYS}일 창을 줄여야 함"
        )
    print(f"[feed] {feed.height:,} rows, cutoff {cutoff} -> {dest} ({size / 1e6:.2f} MB)")
    return dest


def build() -> BuildResult:
    """변경된 코드 버킷만 merge하고 새 manifest와 시장 피드를 작성한다."""
    outDir = _allFilingsDir()
    partitionDir = outDir / _PARTITION_DIR
    partitionDir.mkdir(parents=True, exist_ok=True)

    local = _localFrame()
    previous = _remoteManifest()
    bootstrap = previous is None
    legacy = _legacyFrame() if bootstrap else None
    if local.is_empty() and legacy is None:
        raise SystemExit("로컬 allFilings 일자 파일과 이관할 HF recent.parquet가 모두 없음")

    previousEntries = {
        str(entry.get("bucket")): dict(entry)
        for entry in (previous or {}).get("partitions", [])
        if isinstance(entry, dict) and str(entry.get("bucket", "")).isdigit()
    }
    localBuckets = set(local["stock_code"].str.slice(0, 2).unique().to_list()) if not local.is_empty() else set()
    legacyNormalized = _normalize([legacy]) if legacy is not None else _emptyFrame()
    if bootstrap and not legacyNormalized.is_empty():
        localBuckets.update(legacyNormalized["stock_code"].str.slice(0, 2).unique().to_list())

    changed: dict[str, Path] = {}
    entries = previousEntries.copy()
    for bucket in sorted(str(value) for value in localBuckets):
        additions = local.filter(pl.col("stock_code").str.starts_with(bucket))
        bases: list[pl.DataFrame] = []
        if bootstrap:
            bases.append(legacyNormalized.filter(pl.col("stock_code").str.starts_with(bucket)))
        else:
            remote = _partitionFrame(bucket)
            if bucket in previousEntries and remote is None:
                raise SystemExit(f"[bucket {bucket}] manifest에 있는 원격 파티션을 읽지 못해 갱신 중단")
            if remote is not None:
                bases.append(remote)
        frame = _normalize([additions, *bases])
        if frame.is_empty():
            continue
        dest = partitionDir / _partitionName(bucket)
        frame.write_parquet(dest, compression="zstd", row_group_size=_ROW_GROUP)
        changed[bucket] = dest
        entries[bucket] = _partitionEntry(bucket, frame, dest)
        print(f"[bucket {bucket}] {frame.height:,} rows -> {dest.name} ({dest.stat().st_size / 1e6:.2f} MB)")

    feedInputs = [local]
    remoteFeed = _feedFrame()
    if not bootstrap and remoteFeed is None:
        raise SystemExit("[feed] 기존 market_recent.parquet를 읽지 못해 부분 데이터 덮어쓰기를 차단")
    if remoteFeed is not None:
        feedInputs.append(remoteFeed)
    elif bootstrap and not legacyNormalized.is_empty():
        feedInputs.append(legacyNormalized)
    feedPath = _writeFeed(feedInputs)

    orderedEntries = [entries[key] for key in sorted(entries)]
    manifest = {
        "formatVersion": _MANIFEST_VERSION,
        "layout": "stockCodePrefix2",
        "generatedAt": datetime.now(UTC).isoformat(),
        "dataAsOf": max((str(entry.get("maxDate") or "") for entry in orderedEntries), default=""),
        "partitionCount": len(orderedEntries),
        "totalRows": sum(int(entry.get("rows") or 0) for entry in orderedEntries),
        "partitions": orderedEntries,
        "legacyRecentFrozen": True,
    }
    manifestPath = partitionDir / _MANIFEST_NAME
    manifestPath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"[manifest] {len(changed)} changed / {len(orderedEntries)} total buckets, "
        f"{manifest['totalRows']:,} rows -> {manifestPath}"
    )
    return BuildResult(partitions=changed, feedPath=feedPath, manifestPath=manifestPath, bootstrap=bootstrap)


def push(result: BuildResult, token: str) -> None:
    """변경 파티션, 피드, manifest를 HF 단일 commit으로 게시한다."""
    from huggingface_hub import CommitOperationAdd, HfApi

    from dartlab.core.hfRetry import retryHfCall

    operations = [
        CommitOperationAdd(
            path_in_repo=f"{_relDir()}/{_PARTITION_DIR}/{path.name}",
            path_or_fileobj=str(path),
        )
        for _, path in sorted(result.partitions.items())
    ]
    operations.extend(
        [
            CommitOperationAdd(path_in_repo=f"{_relDir()}/{_FEED_NAME}", path_or_fileobj=str(result.feedPath)),
            CommitOperationAdd(
                path_in_repo=f"{_relDir()}/{_PARTITION_DIR}/{_MANIFEST_NAME}",
                path_or_fileobj=str(result.manifestPath),
            ),
        ]
    )
    api = HfApi(token=token)
    retryHfCall(
        api.create_commit,
        repo_id=repoFor(_ALLFILINGS_DIR_KEY),
        repo_type="dataset",
        operations=operations,
        commit_message=f"allFilings 증분 파티션: {len(result.partitions)}개 버킷 갱신",
    )
    print(f"[HF] {len(operations)} files committed atomically -> {repoFor(_ALLFILINGS_DIR_KEY)}")


def _resolveToken() -> str:
    token = os.environ.get("HF_TOKEN", "")
    if token:
        return token
    envPath = Path(_cfg.__file__).resolve().parents[2] / ".env"
    if envPath.exists():
        for line in envPath.read_text(encoding="utf-8").splitlines():
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=400, help="deprecated, 무시됨")
    parser.add_argument("--no-push", action="store_true", help="빌드만 하고 HF push는 생략")
    args = parser.parse_args()

    result = build()
    if args.no_push:
        return 0
    token = _resolveToken()
    if not token:
        print("[HF] HF_TOKEN 없음. 빌드만 완료", file=sys.stderr)
        return 1
    push(result, token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
