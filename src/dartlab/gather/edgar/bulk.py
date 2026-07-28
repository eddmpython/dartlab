"""SEC daily companyfacts.zip 벌크 다운로더·파서.

URL: https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip
주기: 매일 04:25 UTC, 크기 ~1.37GB
내용: 전체 상장사 XBRL facts가 `CIK{0padded10}.json` 파일들로 압축

파이프라인:
    downloadCompanyfactsBulk()  → data/edgar/_bulk/companyfacts.zip
    extractCompanyfactsZip()    → iter (cik, json_dict)
    convertBulkToParquets()     → data/edgar/finance/{cik}.parquet

기존 `openapi/facts.py::companyFactsToRows()` 를 그대로 재사용.
이 모듈은 zip 스트리밍과 일괄 변환만 책임진다.
"""

from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import httpx
import polars as pl

from dartlab.core.edgarBulkFreshness import (
    bulkDir,
    isBulkFresh,
    readSavedEtag,
    touchBulkFreshness,
)
from dartlab.core.edgarClient import (
    EDGAR_COMPANYFACTS_SCHEMA,
    companyFactsToRows,
)

_log = logging.getLogger(__name__)

_BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"

# SEC fair access: User-Agent with contact required.
# https://www.sec.gov/os/accessing-edgar-data
_UA = "dartlab eddmpython@gmail.com"

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, read=None, write=60.0, connect=30.0)


def _financeDir() -> Path:
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _getDataRoot

    d = _getDataRoot() / DATA_RELEASES["edgar"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def downloadCompanyfactsBulk(
    *,
    force: bool = False,
    ttlHours: int = 24,
    progress: bool = True,
) -> Path:
    """SEC companyfacts.zip 를 `data/edgar/_bulk/companyfacts.zip` 로 다운로드.

    HEAD 요청으로 원격 ETag + Last-Modified 확인 후 로컬 TTL/ETag와 비교.
    force=False (기본) 이면 TTL 내이고 ETag 일치하면 스킵.

    Parameters
    ----------
    force : bool
        True 면 로컬 파일 상태와 무관하게 재다운로드.
    ttlHours : int
        로컬 freshness TTL. SEC companyfacts 는 매일 04:25 UTC 갱신되므로 24h 기본.
    progress : bool
        rich.Progress 진행률 표시 (SSOT Console).

    Raises:
        httpx.HTTPError: SEC bulk endpoint 호출 실패.
        OSError: 파일 쓰기 실패.

    Example:
        >>> downloadCompanyfactsBulk(force=False)

    Args:
        force: bool.
        ttlHours: int.
        progress: bool.

    Returns:
        Path — 결과.
    """
    zipPath = bulkDir() / "companyfacts.zip"
    tag = "companyfacts"

    if not force and zipPath.exists() and isBulkFresh(tag, ttlHours=ttlHours):
        _log.info("companyfacts.zip fresh (TTL=%dh) — 다운로드 스킵", ttlHours)
        return zipPath

    headers = {"User-Agent": _UA, "Accept-Encoding": "identity"}

    # HEAD 로 ETag + Content-Length 확인 (네트워크 낭비 방지)
    savedEtag = readSavedEtag(tag)
    with httpx.Client(timeout=_DEFAULT_TIMEOUT, headers=headers) as client:
        head = client.head(_BULK_URL, follow_redirects=True)
        head.raise_for_status()
        remoteEtag = head.headers.get("ETag", "").strip('"')
        remoteLen = int(head.headers.get("Content-Length", "0") or 0)
        remoteLastModified = head.headers.get("Last-Modified", "")

        if (
            not force
            and savedEtag
            and remoteEtag
            and savedEtag == remoteEtag
            and zipPath.exists()
            and zipPath.stat().st_size == remoteLen
        ):
            _log.info("companyfacts.zip ETag+Size 일치 — 다운로드 스킵 (%s)", remoteEtag)
            touchBulkFreshness(tag, etag=remoteEtag)
            return zipPath

        _log.info(
            "companyfacts.zip 다운로드 시작: %s (%.1f MB, Last-Modified=%s)",
            _BULK_URL,
            remoteLen / 1024 / 1024,
            remoteLastModified,
        )
        _emitStart(remoteLen)

        tmpPath = zipPath.with_suffix(".zip.tmp")
        with client.stream("GET", _BULK_URL, follow_redirects=True) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", "0") or 0) or remoteLen
            downloaded = 0
            chunk = 1024 * 1024  # 1MB
            bar = _initBar(total, show=progress)
            try:
                with tmpPath.open("wb") as f:
                    for data in resp.iter_bytes(chunk_size=chunk):
                        f.write(data)
                        downloaded += len(data)
                        if bar is not None:
                            bar.update(len(data))
            finally:
                if bar is not None:
                    bar.close()

        tmpPath.replace(zipPath)
        touchBulkFreshness(tag, etag=remoteEtag)
        _emitDone(zipPath, downloaded)
        return zipPath


def extractCompanyfactsZip(zipPath: Path) -> Iterator[tuple[str, dict]]:
    """companyfacts.zip 스트리밍 해제 → (cik, json_dict) yield.

    zip 안의 파일명은 `CIK{10자리}.json` 형식. cik 는 0-padded 10자리 문자열로
    반환된다. 손상된 JSON 항목은 로깅 후 건너뛴다.

    Args:
        zipPath: companyfacts.zip 경로.

    Yields:
        ``(cik, payload)`` tuple.

    Raises:
        zipfile.BadZipFile: zip 손상.
        OSError: 파일 IO 실패.

    Example:
        >>> for cik, payload in extractCompanyfactsZip(Path("companyfacts.zip")):
        ...     print(cik)

    Returns:
        Iterator[tuple[str, dict]] — 결과.
    """
    with zipfile.ZipFile(zipPath, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if not name.endswith(".json"):
                continue
            stem = Path(name).stem
            cik = stem.replace("CIK", "").lstrip("0") or "0"
            cikPadded = cik.zfill(10)
            try:
                with zf.open(info) as f:
                    payload = json.load(f)
            except (json.JSONDecodeError, zipfile.BadZipFile, OSError) as exc:
                _log.warning("zip entry %s 파싱 실패: %s", name, exc)
                continue
            yield cikPadded, payload


def convertBulkToParquets(
    zipPath: Path | None = None,
    *,
    outDir: Path | None = None,
    onlyCiks: set[str] | None = None,
    progress: bool = True,
    force: bool = False,
    detectChanged: bool = False,
) -> dict:
    """companyfacts.zip → `data/edgar/finance/{cik}.parquet` 일괄 생성.

    Parameters
    ----------
    zipPath : Path | None
        None 이면 `data/edgar/_bulk/companyfacts.zip` 사용. 없으면 자동 다운로드.
    outDir : Path | None
        None 이면 DATA_RELEASES["edgar"]["dir"] (`data/edgar/finance`).
    onlyCiks : set[str] | None
        지정된 cik(0-padded 10자리)만 변환. 테스트/샘플용.
    progress : bool
        rich.Progress 진행률.
    force : bool
        True 면 stamp 무시하고 항상 재변환 (CI 강제 리빌드 용).
        기본 False: zip mtime 이 `companyfacts.converted` 스탬프보다 최신이거나
        스탬프 없을 때만 변환 (3분+/16,600 CIK 중복 작업 회피).
    detectChanged : bool
        True 면 fact 해시 매니페스트(`_factHash.json`)로 *변경된 CIK 만* 재변환하고
        ``changed`` 리스트(``{cik}.parquet`` 파일명)를 반환 — HF 증분 업로드용(daily
        파이프라인이 16,600 전체 대신 그날 공시한 회사만 올린다). 미변경은 skip.
        매니페스트 부재(최초 run)면 전부 changed.

    Returns
    -------
    dict {"converted": N, "skipped": M, "failed": K, "stampSkipped": bool, "changed": list[str]}

    Raises:
        FileNotFoundError: zip 경로 부재.
        httpx.HTTPError: 자동 다운로드 시 SEC API 호출 실패.

    Example:
        >>> convertBulkToParquets(force=False)

    Args:
        zipPath: Path | None.
        outDir: Path | None.
        onlyCiks: set[str] | None.
        progress: bool.
        force: bool.

    Returns:
        dict[str, int] — 결과.
    """
    if zipPath is None:
        zipPath = downloadCompanyfactsBulk(progress=progress)
    if not zipPath.exists():
        raise FileNotFoundError(zipPath)

    target = outDir or _financeDir()
    target.mkdir(parents=True, exist_ok=True)

    # stamp 기반 skip — zip 미갱신 + 이전 변환 완료 이력 있으면 skip.
    # onlyCiks 지정 시 stamp 무시 (샘플 변환 목적).
    stamp = zipPath.parent / "companyfacts.converted"
    if not force and onlyCiks is None and stamp.exists() and zipPath.stat().st_mtime <= stamp.stat().st_mtime:
        _log.info("companyfacts.zip 변환 최신 상태 (stamp=%s) — skip", stamp)
        return {"converted": 0, "skipped": 0, "failed": 0, "stampSkipped": True, "changed": []}

    converted = 0
    skipped = 0
    failed = 0
    changed: list[str] = []

    # 변경 감지용 fact 해시 매니페스트 — daily 증분 업로드 SSOT(미변경 CIK 재변환·업로드 skip).
    hashManifest: dict[str, str] = {}
    manifestPath = target / "_factHash.json"
    if detectChanged and manifestPath.exists():
        try:
            loaded = json.loads(manifestPath.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                hashManifest = loaded
        except (OSError, json.JSONDecodeError):
            hashManifest = {}

    with zipfile.ZipFile(zipPath, "r") as zf:
        entries = [i for i in zf.infolist() if i.filename.endswith(".json")]

    bar = _initBar(len(entries), show=progress, unit="files")

    try:
        for cik, payload in extractCompanyfactsZip(zipPath):
            if onlyCiks is not None and cik not in onlyCiks:
                skipped += 1
                if bar is not None:
                    bar.update(1)
                continue
            outPath = target / f"{cik}.parquet"
            factHash = ""
            if detectChanged:
                factHash = hashlib.sha1(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                if hashManifest.get(cik) == factHash and outPath.exists():
                    skipped += 1  # 미변경(공시 없음) — 재변환·업로드 skip
                    if bar is not None:
                        bar.update(1)
                    continue
            try:
                df = companyFactsToRows(payload)
                if df.height == 0:
                    skipped += 1
                else:
                    tmpPath = outPath.with_suffix(".parquet.tmp")
                    df.write_parquet(tmpPath, compression="zstd")
                    tmpPath.replace(outPath)
                    converted += 1
                    if detectChanged:
                        hashManifest[cik] = factHash
                        changed.append(f"{cik}.parquet")
            except (
                ValueError,
                TypeError,
                OSError,
                pl.exceptions.PolarsError,
            ) as exc:
                failed += 1
                _log.warning("CIK %s 변환 실패: %s", cik, exc)
            if bar is not None:
                bar.update(1)
    finally:
        if bar is not None:
            bar.close()

    if detectChanged:
        try:
            manifestPath.write_text(json.dumps(hashManifest), encoding="utf-8")
        except OSError as exc:
            _log.warning("_factHash.json 저장 실패: %s", exc)

    # 변환 완료 시각 기록 (다운스트림 스크립트 용).
    # skip 가드가 이 파일 mtime 을 zip mtime 과 비교하므로 touch 이후 작성.
    stamp = zipPath.parent / "companyfacts.converted"
    stamp.write_text(datetime.now(timezone.utc).isoformat(timespec="seconds"), encoding="utf-8")

    _log.info(
        "companyfacts.zip → parquet 변환 완료: converted=%d skipped=%d failed=%d",
        converted,
        skipped,
        failed,
    )
    return {
        "converted": converted,
        "skipped": skipped,
        "failed": failed,
        "stampSkipped": False,
        "changed": changed,
    }


# ── 진행률/이벤트 헬퍼 ─────────────────────────────────────────────────


class _RichBar:
    """rich.Progress 어댑터 — tqdm 호환 (.update(n), .close())."""

    def __init__(self, total: int, *, unit: str) -> None:
        from rich.progress import (
            BarColumn,
            DownloadColumn,
            MofNCompleteColumn,
            Progress,
            TextColumn,
            TimeRemainingColumn,
            TransferSpeedColumn,
        )

        from dartlab.core.logger import getConsole

        if unit == "B":
            cols = (
                TextColumn("[cyan]companyfacts.zip"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            )
        else:
            cols = (
                TextColumn("[cyan]companyfacts.zip"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
            )
        self._progress = Progress(*cols, console=getConsole(), transient=False)
        self._progress.start()
        self._task = self._progress.add_task("companyfacts.zip", total=total)

    def update(self, advance: int) -> None:
        """진행률을 advance 만큼 전진 — tqdm.update 호환.

        Capabilities:
            rich.Progress.update 를 tqdm 호환 시그니처로 노출해 기존 caller 의
            ``bar.update(n)`` 패턴을 유지한다.

        Args:
            advance: 누적 advance (바이트 수 또는 파일 수).

        Returns:
            None.

        Example:
            >>> bar = _initBar(1024, show=True)
            >>> if bar: bar.update(256)

        Guide:
            tqdm 어댑터 — caller 는 update/close 만 호출하면 된다.

        AIContext:
            companyfactsBulk 다운로드/변환 진행률을 SSOT rich Console 로 라우팅.

        SeeAlso:
            :meth:`_RichBar.close` · :func:`_initBar` · :func:`dartlab.core.logger.getConsole`.

        Requires:
            인스턴스가 ``__init__`` 에서 rich.Progress.start() 호출 후 task_id 를
            확보한 상태여야 한다.

        LLM Specifications:
            AntiPatterns: tqdm.update 대용으로 호출. update 후 close 없이 종료 금지.
            OutputSchema: None.
            Prerequisites: _RichBar 인스턴스 (생성자에서 task 등록 완료).
            Freshness: 호출 즉시 rich Console 에 반영 (refresh_per_second 기본).
            Dataflow: caller(zip 다운로드 청크) → _RichBar.update → rich.Progress → Console.
            TargetMarkets: EDGAR bulk 다운로드 진행률 관찰.

        Raises:
            없음. 내부 rich.Progress.update 에 위임.
        """
        self._progress.update(self._task, advance=advance)

    def close(self) -> None:
        """rich.Progress 컨텍스트 종료 — tqdm.close 호환.

        Capabilities:
            rich.Progress.stop 을 tqdm 호환 시그니처로 노출해 기존 caller 의
            ``bar.close()`` 패턴을 유지한다.

        Args:
            없음.

        Returns:
            None.

        Example:
            >>> bar = _initBar(1024, show=True)
            >>> if bar: bar.close()

        Guide:
            try/finally 패턴에서 bar 가 None 이 아닐 때만 호출.

        AIContext:
            companyfactsBulk 다운로드 종료 시 rich Progress task 정리.

        SeeAlso:
            :meth:`_RichBar.update` · :func:`_initBar` · :func:`dartlab.core.logger.getConsole`.

        Requires:
            인스턴스가 ``__init__`` 에서 rich.Progress.start() 호출 후 활성 상태여야 한다.

        LLM Specifications:
            AntiPatterns: close 두 번 호출 금지 (rich.Progress.stop 멱등 아님).
            OutputSchema: None.
            Prerequisites: _RichBar 인스턴스 (생성자에서 start 완료).
            Freshness: 호출 즉시 Live frame 종료.
            Dataflow: caller(finally 블록) → _RichBar.close → rich.Progress.stop.
            TargetMarkets: EDGAR bulk 다운로드/변환 종료 시 자원 정리.

        Raises:
            없음. 내부 rich.Progress.stop 에 위임.
        """
        self._progress.stop()


def _initBar(total: int, *, show: bool, unit: str = "B"):
    """rich.Progress 어댑터 생성 (tqdm 호환 .update/.close)."""
    if not show or total <= 0:
        return None
    try:
        return _RichBar(total, unit=unit)
    except ImportError:
        return None


def _emitStart(totalBytes: int) -> None:
    """companyfacts.zip 다운로드 시작 안내 — guide.emit 으로 [dartlab] 출력."""
    try:
        from dartlab.core.messaging import emit

        emit("edgar:bulk_download_start")
    except ImportError:
        pass
    _log.info("companyfacts.zip 다운로드 시작 — %.1f MB", totalBytes / 1024 / 1024)


def _emitDone(zipPath: Path, downloaded: int, *, elapsedSec: float = 0.0) -> None:
    """다운로드 완료 안내."""
    try:
        from dartlab.core.messaging import emit

        emit(
            "edgar:bulk_download_done",
            sizeMB=downloaded / 1024 / 1024,
            elapsedSec=elapsedSec,
        )
    except ImportError:
        pass
    _log.info(
        "companyfacts.zip 다운로드 완료 — %s (%.1f MB)",
        zipPath,
        downloaded / 1024 / 1024,
    )


def _emitFresh(ttlHours: int) -> None:
    try:
        from dartlab.core.messaging import emit

        emit("edgar:bulk_fresh", ttlHours=ttlHours)
    except ImportError:
        pass


def _emitConvertStart(totalCiks: int) -> None:
    try:
        from dartlab.core.messaging import emit

        emit("edgar:bulk_convert_start", totalCiks=totalCiks)
    except ImportError:
        pass


def _emitConvertDone(*, converted: int, skipped: int, failed: int, elapsedSec: float) -> None:
    try:
        from dartlab.core.messaging import emit

        emit(
            "edgar:bulk_convert_done",
            converted=converted,
            skipped=skipped,
            failed=failed,
            elapsedSec=elapsedSec,
        )
    except ImportError:
        pass


def ensureFinanceParquet(stockCode: str, path: Path, *, refresh: bool = False) -> None:
    """EDGAR finance ``{cik}.parquet`` 을 SEC 벌크에서 보장.

    dartlab 은 ``companyfacts.zip`` (SEC daily, ~1.37GB) 을 사용자 PC 에 받아서
    16,600+ CIK parquet 으로 일괄 변환한다. HF 미러링 없음 — SEC 가 원본.

    정책:
    - path 없으면: 벌크 다운로드 + 전체 변환 (최초 1회 5~15분)
    - refresh=True + zip 갱신: 전체 재변환 (daily 갱신 반영)
    - refresh=True + zip 미갱신: 아무것도 안 함 (낭비 방지)

    Args:
        stockCode: 종목 ticker.
        path: 결과 parquet 경로 (CIK 기반).
        refresh: zip 갱신 시 재변환 여부.

    Raises
    ------
    FileNotFoundError
        zip 변환 후에도 해당 CIK parquet 이 없으면 (상장 폐지/비공시 기업).

    Example:
        >>> ensureFinanceParquet("AAPL", Path("data/edgar/finance/0000320193.parquet"))
    """
    zipPath = downloadCompanyfactsBulk(force=False)  # ETag + TTL 기반 재사용
    # convertBulkToParquets 자체가 zip mtime vs stamp 비교로 skip 가드.
    # 최초 로드 (path 없음) 는 stamp 가드 우회하기 위해 force=True.
    if not path.exists():
        convertBulkToParquets(zipPath=zipPath, force=True)
    elif refresh:
        convertBulkToParquets(zipPath=zipPath)  # stamp 비교 → 필요시만 재변환
    if not path.exists():
        raise FileNotFoundError(
            f"{stockCode} (CIK={path.stem}) EDGAR finance parquet 생성 실패 — "
            f"companyfacts.zip 에 해당 CIK 없음 (상장 폐지/비공시 기업 가능성)."
        )


__all__ = [
    "EDGAR_COMPANYFACTS_SCHEMA",
    "convertBulkToParquets",
    "downloadCompanyfactsBulk",
    "ensureFinanceParquet",
    "extractCompanyfactsZip",
]
