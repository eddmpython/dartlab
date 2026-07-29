"""Remote freshness and HF download helpers for ``core.dataLoader``."""

from __future__ import annotations

import os
import socket
import time
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


def _noRefreshEnv() -> bool:
    """``DARTLAB_NO_REFRESH=1`` 시 HF refresh 우회."""
    return os.environ.get("DARTLAB_NO_REFRESH") == "1"


def downloadWithRetry(
    url: str,
    dest: Path,
    *,
    maxRetries: int,
    socketTimeout,
    urlretrieve,
) -> None:
    """URL → dest 다운로드. 실패 시 지수 backoff로 재시도한다."""
    parsedUrl = urlsplit(url)
    if parsedUrl.scheme != "https" or not parsedUrl.hostname:
        raise ValueError(f"download URL은 HTTPS여야 합니다: {url!r}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    lastErr: OSError | None = None
    token = os.environ.get("HF_TOKEN", "").strip()
    for attempt in range(maxRetries):
        try:
            with socketTimeout():
                if token:
                    req = Request(url)
                    req.add_header("Authorization", f"Bearer {token}")
                    with urlopen(req) as resp, tmp.open("wb") as f:  # nosec B310
                        while chunk := resp.read(1 << 20):
                            f.write(chunk)
                else:
                    urlretrieve(url, tmp)  # tmp 로 받고 atomic rename — 중단 시 손상 dest 미생성
            tmp.replace(dest)
            return
        except (URLError, socket.timeout, OSError) as exc:
            lastErr = exc
            if tmp.exists():
                tmp.unlink()
            if attempt < maxRetries - 1:
                time.sleep(2 ** (attempt + 1))
    if lastErr is None:
        raise RuntimeError("download retry가 오류 원인 없이 종료되었습니다")
    raise lastErr


def checkRemoteFreshness(
    stockCode: str,
    localPath: Path,
    category: str,
    *,
    hfBaseUrl: Callable[[str], str],
    fetchRemoteEtagAndSize: Callable[[str], tuple[str, int]],
) -> bool | None:
    """로컬 파일이 원격보다 오래됐는지 ETag와 크기로 확인한다."""
    hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    etagPath = localPath.with_suffix(".parquet.etag")
    try:
        remoteEtag, remoteSize = fetchRemoteEtagAndSize(hfUrl)
        if not remoteEtag:
            return None
        if remoteSize > 0 and localPath.exists():
            try:
                if localPath.stat().st_size != remoteSize:
                    return True
            except OSError:
                pass
        if etagPath.exists():
            localEtag = etagPath.read_text(encoding="utf-8").strip()
            return remoteEtag != localEtag
        return True
    except (URLError, socket.timeout, OSError, ValueError):
        return None


def saveEtag(
    stockCode: str,
    dest: Path,
    category: str,
    *,
    hfBaseUrl: Callable[[str], str],
    fetchRemoteEtag: Callable[[str], str],
) -> None:
    """다운로드 성공 후 HF ETag를 사이드카 파일에 저장한다."""
    hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    etagPath = dest.with_suffix(".parquet.etag")
    try:
        etag = fetchRemoteEtag(hfUrl)
        if etag:
            etagPath.write_text(etag, encoding="utf-8")
    except (URLError, socket.timeout, OSError) as exc:
        _log.warning(
            "HF ETag sidecar 저장 실패 (category=%s, stockCode=%s, path=%s, error=%s): %s",
            category,
            stockCode,
            etagPath,
            type(exc).__name__,
            exc,
        )


def maybeWarnStale(path: Path, *, warnedPaths: set[str], staleWarnDays: int) -> None:
    """오래된 로컬 데이터 경고를 세션당 경로별 1회만 보낸다."""
    key = str(path)
    if key in warnedPaths:
        return
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return
    ageDays = int(age // 86400)
    if ageDays >= staleWarnDays:
        warnedPaths.add(key)
        try:
            from dartlab.core.messaging import emit

            emit("data:stale_warning", ageDays=ageDays)
        except ImportError:
            pass


def shouldRefreshDart(
    path: Path,
    refresh: str,
    *,
    staleWarnDays: int,
    dartFreshnessTtlHours: int,
    warnStale: Callable[[Path], None],
) -> bool:
    """DART 카테고리 로컬 파일의 갱신 필요 여부를 판단한다."""
    if _noRefreshEnv():
        return False
    if refresh == "local_only":
        return False
    if refresh == "force_check":
        return True
    etagPath = path.with_suffix(".parquet.etag")
    if not etagPath.exists():
        try:
            age = time.time() - path.stat().st_mtime
            if age > staleWarnDays * 86400:
                warnStale(path)
            return age > dartFreshnessTtlHours * 3600 * 7
        except OSError:
            return False
    try:
        age = time.time() - etagPath.stat().st_mtime
        if age > staleWarnDays * 86400:
            warnStale(etagPath)
        return age > dartFreshnessTtlHours * 3600
    except OSError:
        return False


def shouldRefreshHfCategory(
    path: Path,
    category: str,
    refresh: str,
    *,
    krxFreshnessTtlHours: int,
    shouldRefreshDartFunc: Callable[[Path, str], bool],
) -> bool:
    """HF 공개 parquet 카테고리별 freshness 정책."""
    if _noRefreshEnv():
        return False
    if category not in {"krxPrices", "krxIndices", "govPrices", "govPriceCompany", "govIndices", "govIndexPerIndex"}:
        return shouldRefreshDartFunc(path, refresh)
    if refresh == "local_only":
        return False
    if refresh == "force_check":
        return True
    etagPath = path.with_suffix(".parquet.etag")
    if not etagPath.exists():
        return True
    try:
        age = time.time() - etagPath.stat().st_mtime
        return age > krxFreshnessTtlHours * 3600
    except OSError:
        return True


def refreshFromHf(
    stockCode: str,
    path: Path,
    category: str,
    *,
    dataReleases: dict,
    hfBaseUrl: Callable[[str], str],
    checkRemoteFreshness: Callable[[str, Path, str], bool | None],
    downloadWithRetry: Callable[[str, Path], None],
    saveEtag: Callable[[str, Path, str], None],
    validateParquet: Callable[[Path], None] | None = None,
) -> bool:
    """ETag 비교 후 HF가 최신이면 다운로드로 갱신하고 실패 시 기존 파일을 유지한다."""
    stale = checkRemoteFreshness(stockCode, path, category)
    if stale is None:
        # 확인 실패를 "확인했고 최신" 으로 기록하지 않는다. etag 파일의 mtime 이 바로
        # "마지막으로 확인한 시각" 이라, 여기서 touch 하면 TTL 동안 갱신 시도조차 하지
        # 않는다. 오프라인이나 프록시 차단이 길어질수록 자료가 더 최신처럼 보이고,
        # 실패할 때마다 그 침묵이 다시 연장된다.
        _log.warning("원격 신선도 확인 실패로 로컬 자료를 그대로 쓴다 (%s, %s)", stockCode, category)
        return False
    if stale is not True:
        etagPath = path.with_suffix(".parquet.etag")
        if etagPath.exists():
            etagPath.touch()
        return True
    from dartlab.core.messaging import emit

    label = dataReleases[category]["label"]
    tmpPath = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.refresh")
    try:
        emit("download:start", stockCode=stockCode, label=label)
        hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
        downloadWithRetry(hfUrl, tmpPath)
        if validateParquet is not None:
            validateParquet(tmpPath)
        tmpPath.replace(path)
        saveEtag(stockCode, path, category)
        size = path.stat().st_size
        sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
        emit("download:done_short", sizeStr=sizeStr)
        return True
    except (URLError, socket.timeout, OSError) as exc:
        try:
            tmpPath.unlink(missing_ok=True)
        except OSError as cleanupExc:
            _log.error(
                "refresh 임시 artifact 정리 실패 (%s, prior=%s): %s",
                tmpPath,
                type(exc).__name__,
                cleanupExc,
            )
        _log.warning(
            "refresh payload 검증·교체 실패로 기존 parquet을 유지한다 (category=%s, stockCode=%s, error=%s): %s",
            category,
            stockCode,
            type(exc).__name__,
            exc,
        )
        emit("download:failed_single", stockCode=stockCode, label=label, error=str(exc))
        return False


__all__ = [
    "checkRemoteFreshness",
    "downloadWithRetry",
    "maybeWarnStale",
    "refreshFromHf",
    "saveEtag",
    "shouldRefreshDart",
    "shouldRefreshHfCategory",
]
