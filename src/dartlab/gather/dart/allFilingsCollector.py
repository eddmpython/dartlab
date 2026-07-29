"""전체 공시 원문 수집기 — 2단계 증분 수집 + raw 본문 생긴 그대로 보존.

Phase 1: 목록 수집 (collectMeta) — 일자별 API 1회, 매우 가볍다.
Phase 2: 원문 수집 (fillContent) — 건당 API 1회, 키 소비 큼. 본문은 zip 안 largest
파일을 *생긴 그대로* (`content_raw` 컬럼) 저장한다. DART 는 공시 종류별로 두 포맷을
섞어 반환한다 — (a) dart4.xsd XML (`<DOCUMENT>` / `<TITLE ATOC ...>` / `<TABLE>`),
(b) xforms HTML (`<html><head><meta charset="euc-kr"><STYLE>.xforms ...</STYLE>`).
모든 태그·attribute 보존. plain text 가 필요한 소비자는 BeautifulSoup ``lxml``
parser 의 `get_text()` 등으로 변환 (lxml 은 XML/HTML 양쪽 안전). sections
`_raw.parquet` 와 동일 비전.

목록을 먼저 전부 모은 뒤, 원문은 키 여유 있을 때 점진적으로 채운다.

사용법::

    from dartlab.gather.dart.allFilingsCollector import (
        collectMetaRange, fillContent, stats
    )

    # Phase 1: 목록만 빠르게 (5년치도 키 1개로 가능)
    collectMetaRange("20210401", "20260330")

    # Phase 2: 원문 채우기 (일자별, 키 여유 있을 때)
    fillContent("20260327")
    fillContentAll()  # 미수집 원문 전체
"""

from __future__ import annotations

import io
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.logger import getLogger
from dartlab.core.memory import withMemoryBudget
from dartlab.gather.dart.disclosure import listFilings

if TYPE_CHECKING:
    from dartlab.gather.dart.client import DartClient
else:
    from dartlab.core.dartClient import DartClient

_log = getLogger(__name__)

# ── 상수 ──

_ALLFILINGS_DIR_KEY = "allFilings"
_META_SUFFIX = "_meta"  # 목록만: 20260327_meta.parquet
# 원문포함: 20260327.parquet


def metaSuffix() -> str:
    """allFilings 메타 parquet 파일 suffix(``_meta``) — providers 소비자가 core.dartClient seam 으로 접근."""
    return _META_SUFFIX


# 정기공시 (사업/분기/반기보고서) 본문은 panel 이 owner — allFilings 본문 수집에서 스킵.
# 89% 가 docs/ 와 중복 (2026-05 검증). 부피 큰 공시 본문 중복 호출 차단.
_PERIODIC_REPORT_PATTERNS: tuple[str, ...] = ("사업보고서", "분기보고서", "반기보고서")

# ── 내부 유틸 ──


def _allFilingsDir() -> Path:
    """allFilings parquet 저장 디렉토리."""
    root = Path(_cfg.dataDir)
    d = root / DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _collectOneRaw(client: DartClient, rceptNo: str) -> tuple[str | None, str]:
    """단일 공시 원문 raw 본문 반환 — 생긴 그대로, 모든 태그·attribute 보존.

    DART 가 반환하는 zip 안 largest 파일은 공시 종류별로 dart4.xsd XML 또는 xforms
    HTML 두 포맷 중 하나. utf-8/euc-kr/cp949 순으로 디코딩만 한다. 후처리 0.

    Returns:
        (content_raw, fetch_status) tuple.
        fetch_status:
            - ``"ok"``: 정상 본문 수집 — content_raw 는 raw XML/HTML.
            - ``"no_body"``: DART 명시 데이터 truth (행정 통지 / 첨부정정 / 접수번호
              오류). 영원히 retry 불가. status 013 (접수번호 오류) 또는 014 (파일
              부재) 응답. content_raw 는 None.
            - ``"error"``: API 장애 (network · 한도 · 시스템 점검 · decode 실패).
              retry 대상. content_raw 는 None.

    DART API 응답 구조:
        정상: ``b'PK\\x03\\x04'`` ZIP magic prefix → zip 내 largest 파일 디코딩.
        본문 부재: 147 bytes XML ``<result><status>014</status><message>파일이
        존재하지 않습니다</message></result>``.
        접수번호 오류: 147 bytes XML ``<status>013</status><message>접수번호 오류
        ...``.
        기타 에러: status 010/011/012 (API key) · 020 (한도) · 800 (점검) · 900
        (불명) → "error".
    """
    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except (RuntimeError, OSError):
        return (None, "error")

    if raw is None or len(raw) == 0:
        return (None, "error")

    # 정상 응답 — ZIP magic prefix
    if raw[:4] == b"PK\x03\x04":
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile:
            return (None, "error")

        names = zf.namelist()
        if not names:
            return (None, "error")

        largest = max(names, key=lambda n: zf.getinfo(n).file_size)
        content = zf.read(largest)

        rawContent: str | None = None
        for enc in ("utf-8", "euc-kr", "cp949"):
            try:
                rawContent = content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if rawContent is None:
            rawContent = content.decode("utf-8", errors="replace")

        if not rawContent.strip():
            return (None, "error")

        return (rawContent, "ok")

    # status XML 응답 — DART 명시 결과
    text = raw[:300].decode("utf-8", errors="replace")
    if "<status>014" in text or "<status>013" in text:
        return (None, "no_body")
    return (None, "error")


def _allFilingsWorkers(client: DartClient) -> int:
    """allFilings document.xml fetch workers; default is bounded by DART key slots."""
    raw = os.environ.get("DART_ALLFILINGS_WORKERS")
    if raw is not None:
        try:
            return max(1, int(raw))
        except ValueError:
            return 1
    slots = getattr(client, "_slots", None)
    if isinstance(slots, list) and slots:
        return max(1, min(4, len(slots)))
    return 1


# ═══════════════════════════════════════════
# Phase 1: 목록 수집 (가볍다 — 일자당 API ~15회)
# ═══════════════════════════════════════════


def collectMetaDay(
    period: str,
    *,
    client: DartClient | None = None,
    corpClasses: list[str] | None = None,
    showProgress: bool = True,
) -> pl.DataFrame | None:
    """하루치 공시 목록만 수집 → _meta.parquet 저장.

    이미 목록이 있거나 원문까지 완료된 날짜는 건너뛴다.

    Args:
        period: 인자.
        client: 인자.
        corpClasses: 인자.
        showProgress: 인자.

    Raises:
        없음.

    Example:
        >>> collectMetaDay(...)

    Returns:
        pl.DataFrame 또는 None — 수집 결과.
    """
    if client is None:
        client = DartClient()

    if corpClasses is None:
        corpClasses = ["Y", "K"]

    outDir = _allFilingsDir()
    metaPath = outDir / f"{period}{_META_SUFFIX}.parquet"

    # listFilings 1 호출 (1.5초) — 항상 호출. 당일 추가 공시 / 옛 날짜 정정공시 발견.
    meta = listFilings(client, start=period, end=period, fetchAll=True)
    if meta.height == 0:
        if showProgress:
            _log.info("[%s] 공시 없음 (휴일)", period)
        return None

    if corpClasses:
        meta = meta.filter(pl.col("corp_cls").is_in(corpClasses))

    if meta.height == 0:
        if showProgress:
            _log.info("[%s] 상장사 공시 없음", period)
        return None

    # 저장 — 옛 meta 가 있어도 신규 결과로 덮어씀 (listFilings 는 정정 포함 최신 list 반환).
    # 본문 .parquet 는 fillContent 가 별도 diff 로 incremental update.
    tmpPath = metaPath.with_suffix(".parquet.tmp")
    meta.write_parquet(tmpPath)
    tmpPath.replace(metaPath)

    if showProgress:
        _log.info("[%s] 목록 %d건 갱신", period, meta.height)

    return meta


def collectMetaRange(
    startDate: str,
    endDate: str,
    *,
    client: DartClient | None = None,
    corpClasses: list[str] | None = None,
    showProgress: bool = True,
) -> int:
    """날짜 범위 목록 일괄 수집. 최신→과거 순. 매우 가볍다.

    Returns
    -------
    int
        수집된 날짜 수.

    Raises:
        없음.

    Example:
        >>> collectMetaRange(...)

    Args:
        startDate: 시작일 (YYYYMMDD).
        endDate: 종료일 (YYYYMMDD).
        client: DartClient 인스턴스. None 이면 자동 생성.
        corpClasses: 회사 종류 필터 (KOSPI/KOSDAQ/etc). None 이면 전체.
        showProgress: True 면 progress 로그 출력.

    Returns:
        int — 수집 건수.
    """
    from datetime import datetime, timedelta

    if client is None:
        client = DartClient()

    start = datetime.strptime(startDate, "%Y%m%d")
    end = datetime.strptime(endDate, "%Y%m%d")

    dates = []
    current = end
    while current >= start:
        dates.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)

    collected = 0
    for i, date in enumerate(dates):
        if showProgress and (i + 1) % 10 == 0:
            _log.info("--- 목록 진행: %d/%d ---", i + 1, len(dates))
        result = collectMetaDay(
            date,
            client=client,
            corpClasses=corpClasses,
            showProgress=showProgress,
        )
        if result is not None:
            collected += 1

    if showProgress:
        _log.info("목록 수집 완료: %d일", collected)

    return collected


# ═══════════════════════════════════════════
# Phase 2: 원문 채우기 (무겁다 — 건당 API 1회)
# ═══════════════════════════════════════════


def _rowFromMeta(metaRow: dict, content: str | None, status: str) -> dict:
    """meta row + 본문 수집 결과 → 본문 parquet row dict."""
    return {
        "corp_code": metaRow["corp_code"],
        "corp_name": metaRow["corp_name"],
        "stock_code": metaRow.get("stock_code", ""),
        "corp_cls": metaRow["corp_cls"],
        "rcept_dt": metaRow["rcept_dt"],
        "rcept_no": metaRow["rcept_no"],
        "report_nm": metaRow["report_nm"],
        "flr_nm": metaRow.get("flr_nm", ""),
        "content_raw": content,
        "fetch_status": status,
    }


def fillContent(
    period: str,
    *,
    client: DartClient | None = None,
    showProgress: bool = True,
) -> pl.DataFrame | None:
    """하루치 본문 incremental 수집. **idempotent + diff retry**.

    매번 호출 시:
        1. ``collectMetaDay`` 호출 — listFilings 1 회 (1.5초) 로 최신 공시 목록 갱신.
           당일 추가 공시 / 옛 날짜 정정공시 발견 보장.
        2. 기존 ``.parquet`` 의 rcept_no → fetch_status 맵 빌드.
        3. 처리 대상:
           - 신규 rcept_no (목록엔 있지만 .parquet 에 없는 것) → 본문 수집
           - 기존 ``fetch_status="error"`` → retry
           - 기존 ``fetch_status="ok"`` / ``"no_body"`` → skip (final)
        4. 정기공시 (``_PERIODIC_REPORT_PATTERNS``) 는 row 자체 생략 — docs/ owner.
        5. atomic merge — skip row + 신규/retry row → tmp.parquet → rename.

    본문 0 건 안전장치 — incremental update (기존 .parquet 있음) 의 경우엔 트리거 X.
    *최초 수집* 에서 모든 row error 일 때만 .parquet 갱신 차단 (옛 사고 가드).

    Args:
        period: YYYYMMDD.
        client: DartClient 인스턴스. None 이면 자동 생성.
        showProgress: True 면 progress 로그.

    Returns:
        pl.DataFrame 또는 None — 본문 .parquet 의 최종 내용. 변경 0 시에도 기존
        .parquet 의 DataFrame 반환. listFilings 결과 0 또는 처리 대상 0 시 None.

    Raises:
        없음.

    Example:
        >>> fillContent("20260527")  # doctest: +SKIP
    """
    if client is None:
        client = DartClient()

    outDir = _allFilingsDir()
    metaPath = outDir / f"{period}{_META_SUFFIX}.parquet"
    fullPath = outDir / f"{period}.parquet"

    # Step 1: meta 갱신 — listFilings 항상 호출.
    collectMetaDay(period, client=client, showProgress=showProgress)
    if not metaPath.exists():
        if showProgress:
            _log.info("[%s] 목록 없음 (휴일)", period)
        return None
    meta = pl.read_parquet(metaPath)

    # Step 2: 기존 본문 .parquet 의 rcept_no → fetch_status 맵 (diff 판정용).
    # 본문 row dict 자체는 후속 concat 단계에서 .parquet 그대로 재사용 — 메모리에 안 올림.
    existingStatus: dict[str, str] = {}
    if fullPath.exists():
        statusDf = pl.read_parquet(fullPath, columns=["rcept_no", "fetch_status"])
        for r in statusDf.iter_rows(named=True):
            existingStatus[r["rcept_no"]] = r["fetch_status"]

    # Step 3: 처리 대상 분리.
    skipPeriodic = 0
    skipExisting = 0
    targets: list[dict] = []  # 신규 + retry — 본문 수집 대상 meta row
    for metaRow in meta.iter_rows(named=True):
        rceptNo = metaRow["rcept_no"]
        reportNm = metaRow.get("report_nm", "") or ""

        # 정기공시 — docs/ owner. row 자체 생략.
        if any(p in reportNm for p in _PERIODIC_REPORT_PATTERNS):
            skipPeriodic += 1
            continue

        existing = existingStatus.get(rceptNo)
        if existing is None:
            targets.append(metaRow)  # 신규
        elif existing == "error":
            targets.append(metaRow)  # retry
        else:
            skipExisting += 1  # ok / no_body — final, skip

    if not targets:
        if showProgress:
            _log.info(
                "[%s] 변경 없음: 기존 ok/no_body %d, 정기공시 skip %d, 처리 대상 0",
                period,
                skipExisting,
                skipPeriodic,
            )
        # 기존 .parquet 이 있으면 그대로 반환, 없으면 None
        return pl.read_parquet(fullPath) if fullPath.exists() else None

    if showProgress:
        _log.info(
            "[%s] 처리 시작: 신규/retry %d, 기존 skip %d (ok/no_body), 정기공시 skip %d",
            period,
            len(targets),
            skipExisting,
            skipPeriodic,
        )

    # Step 4: 본문 수집 — 신규 + retry.
    processedRows: dict[str, dict] = {}
    okCount = noBodyCount = errorCount = 0
    workers = _allFilingsWorkers(client)
    if showProgress:
        _log.info("[%s] document.xml fetch workers=%d", period, workers)

    def _recordResult(done: int, metaRow: dict, content: str | None, status: str) -> None:
        nonlocal okCount, noBodyCount, errorCount
        rceptNo = metaRow["rcept_no"]
        processedRows[rceptNo] = _rowFromMeta(metaRow, content, status)
        if status == "ok":
            okCount += 1
        elif status == "no_body":
            noBodyCount += 1
        else:
            errorCount += 1
        if showProgress and done % 100 == 0:
            _log.info(
                "  [%d/%d] ok=%d no_body=%d error=%d",
                done,
                len(targets),
                okCount,
                noBodyCount,
                errorCount,
            )

    if workers <= 1 or len(targets) <= 1:
        for done, metaRow in enumerate(targets, start=1):
            content, status = _collectOneRaw(client, metaRow["rcept_no"])
            _recordResult(done, metaRow, content, status)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_collectOneRaw, client, metaRow["rcept_no"]): metaRow for metaRow in targets}
            for done, fut in enumerate(as_completed(futures), start=1):
                metaRow = futures[fut]
                content, status = fut.result()
                _recordResult(done, metaRow, content, status)

    # Step 5: 본문 0 건 성공 안전장치 — 최초 수집만 트리거 (incremental update 는
    # 기존 데이터 보존이 0건 가드보다 우선).
    isFirstFill = not fullPath.exists()
    if isFirstFill and okCount == 0 and errorCount > 0:
        _log.warning(
            "[%s] 최초 수집인데 ok 0 / error %d / no_body %d — .parquet 승격 차단, _meta 보존. "
            "원인 확인 후 재시도 필요 (API 키 한도 / 네트워크 / URL 변경).",
            period,
            errorCount,
            noBodyCount,
        )
        return None

    # Step 6: skip 기존 row + 신규/retry row → atomic merge.
    # polars DataFrame schema 추론은 mixed-size 큰 string row 에서 fragile —
    # 신규 row 만 `infer_schema_length=None` 으로 build 후 기존 .parquet (이미
    # parquet schema 박혀있음) 과 concat 한다.
    processedDf = pl.DataFrame(list(processedRows.values()), infer_schema_length=None)
    if fullPath.exists():
        keepDf = pl.read_parquet(fullPath).filter(~pl.col("rcept_no").is_in(list(processedRows.keys())))
        df = pl.concat([keepDf, processedDf], how="diagonal_relaxed")
    else:
        df = processedDf

    tmpPath = fullPath.with_suffix(".parquet.tmp")
    df.write_parquet(tmpPath)
    tmpPath.replace(fullPath)

    # _meta 제거 (.parquet 승격 완료) — 매번 호출 시 재생성됨.
    if metaPath.exists():
        metaPath.unlink()

    if showProgress:
        _log.info(
            "[%s] 완료: ok=%d no_body=%d error=%d (처리 %d), 전체 %d행, %.1fMB",
            period,
            okCount,
            noBodyCount,
            errorCount,
            len(targets),
            df.height,
            fullPath.stat().st_size / 1024 / 1024,
        )

    return df


def fillContentAll(
    *,
    client: DartClient | None = None,
    showProgress: bool = True,
) -> int:
    """목록만 있는 날짜 전체의 원문을 채운다. 최신순.

    Returns
    -------
    int
        원문 수집 완료한 날짜 수.

    Raises:
        없음.

    Example:
        >>> fillContentAll(...)

    Args:
        client: DartClient 인스턴스. None 이면 자동 생성.
        showProgress: True 면 progress 로그 출력.

    Returns:
        int — 수집 건수.
    """
    if client is None:
        client = DartClient()

    pending = pendingDates()
    if not pending:
        if showProgress:
            _log.info("원문 미수집 날짜 없음")
        return 0

    if showProgress:
        _log.info("원문 미수집 %d일 처리 시작", len(pending))

    filled = 0
    for i, date in enumerate(pending):
        if showProgress:
            _log.info("=== [%d/%d] ===", i + 1, len(pending))
        try:
            result = fillContent(date, client=client, showProgress=showProgress)
            if result is not None:
                filled += 1
        except Exception as exc:
            if showProgress:
                _log.warning("[%s] 에러: %s", date, exc)
            exc.add_note(f"allFilings 원문 채우기 실패: date={date}, completedDates={filled}")
            raise

    if showProgress:
        _log.info("원문 수집 완료: %d일", filled)

    return filled


# ═══════════════════════════════════════════
# 조회/통계
# ═══════════════════════════════════════════


def collectedDates() -> list[str]:
    """원문 수집 완료된 날짜 목록 (최신순).

    Args:
        (인자 자동 생성).

    Raises:
        없음.

    Example:
        >>> collectedDates(...)

    Returns:
        list[str] — 결과 목록.
    """
    outDir = _allFilingsDir()
    dates = sorted(
        [p.stem for p in outDir.glob("*.parquet") if len(p.stem) == 8 and p.stem.isdigit()],
        reverse=True,
    )
    return dates


def pendingDates() -> list[str]:
    """목록만 있고 원문 미수집인 날짜 목록 (최신순).

    Args:
        (인자 자동 생성).

    Raises:
        없음.

    Example:
        >>> pendingDates(...)

    Returns:
        list[str] — 결과 목록.
    """
    outDir = _allFilingsDir()
    dates = sorted(
        [p.stem.replace(_META_SUFFIX, "") for p in outDir.glob(f"*{_META_SUFFIX}.parquet")],
        reverse=True,
    )
    return dates


# ═══════════════════════════════════════════
# HF 동기화 (push / lazy pull)
# ═══════════════════════════════════════════

# 다운로드 1 회 시도 가드 (period 또는 "_ALL_") — 실패 시 무한 retry 회피.
_HF_DOWNLOAD_ATTEMPTED: set[str] = set()


class HfFallbackStatus(str, Enum):
    """allFilings HF fallback의 정상 결과."""

    LOCAL = "local"
    DOWNLOADED = "downloaded"
    NOT_FOUND = "not_found"


class AllFilingsHfError(RuntimeError):
    """allFilings HF fallback 기반 오류."""

    def __init__(self, message: str, *, period: str | None) -> None:
        self.period = period
        super().__init__(message)


class AllFilingsHfUnavailableError(AllFilingsHfError):
    """HF fallback을 현재 실행 환경에서 사용할 수 없음."""


class AllFilingsHfDownloadError(AllFilingsHfError):
    """HF fallback 원격 조회·다운로드가 실패함."""


class AllFilingsHfListingError(AllFilingsHfError):
    """HF 원격 artifact 목록 조회가 실패함."""


class AllFilingsHfUploadError(AllFilingsHfError):
    """HF artifact 업로드가 일부 또는 전부 실패함."""

    def __init__(self, message: str, *, uploadedFiles: int, totalFiles: int) -> None:
        self.uploadedFiles = uploadedFiles
        self.totalFiles = totalFiles
        super().__init__(message, period=None)


def _bodyParquetFiles(outDir: Path) -> list[Path]:
    """allFilings 본문 parquet만 정렬해 반환한다."""
    return sorted(f for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)


def _hasBodyArtifact(outDir: Path, period: str | None) -> bool:
    """요청한 본문 artifact가 로컬에 존재하는지 확인한다."""
    if period is not None:
        return (outDir / f"{period}.parquet").is_file()
    return bool(_bodyParquetFiles(outDir))


def _ensureFromHf(period: str | None = None) -> HfFallbackStatus:
    """artifact 부재 시 HF dataset 에서 lazy 다운로드.

    panel sync `_ensureFromHf` 동일 패턴 — `huggingface_hub.snapshot_download`
    로 `{HF_REPO}:dart/allFilings/` 의 parquet 받음.

    Args:
        period: 특정 일자만 (YYYYMMDD) 받기. None 이면 디렉토리 전체.

    Returns:
        HfFallbackStatus — 로컬 존재, 다운로드 완료, 원격 정상 부재.

    Raises:
        AllFilingsHfUnavailableError: 환경 설정 또는 optional dependency 때문에 HF를
            사용할 수 없는 경우.
        AllFilingsHfDownloadError: 원격 조회·인증·다운로드가 실패한 경우.

    환경변수 `DARTLAB_NO_HF_DOWNLOAD=1` 시 즉시 skip. 한 (period or "_ALL_") 1 회만 시도.
    """
    import os as _os

    outDir = _allFilingsDir()
    if _hasBodyArtifact(outDir, period):
        return HfFallbackStatus.LOCAL

    if _os.environ.get("DARTLAB_NO_HF_DOWNLOAD", "").strip() in ("1", "true", "True"):
        raise AllFilingsHfUnavailableError(
            "DARTLAB_NO_HF_DOWNLOAD 설정으로 allFilings HF fallback이 비활성화되었습니다",
            period=period,
        )

    key = period or "_ALL_"
    if key in _HF_DOWNLOAD_ATTEMPTED:
        return HfFallbackStatus.NOT_FOUND

    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import (
            EntryNotFoundError,
            LocalEntryNotFoundError,
            OfflineModeIsEnabled,
        )
    except ImportError as exc:
        raise AllFilingsHfUnavailableError(
            "huggingface_hub optional dependency가 없어 allFilings HF fallback을 사용할 수 없습니다",
            period=period,
        ) from exc

    try:
        from dartlab.core.dataConfig import repoFor
        from dartlab.core.hfRetry import retryHfCall

        relDir = DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]
        pattern = f"{relDir}/{period}.parquet" if period else f"{relDir}/*.parquet"
        retryHfCall(  # HF read SSOT(core.hfRetry) — 429/503/504 단일 백오프
            snapshot_download,
            repo_id=repoFor(_ALLFILINGS_DIR_KEY),
            repo_type="dataset",
            allow_patterns=[pattern],
            local_dir=str(Path(_cfg.dataDir)),
        )
    except (LocalEntryNotFoundError, OfflineModeIsEnabled) as exc:
        raise AllFilingsHfUnavailableError(
            f"offline/cache 상태에서 allFilings HF artifact를 사용할 수 없습니다: {period or 'ALL'}",
            period=period,
        ) from exc
    except EntryNotFoundError:
        _HF_DOWNLOAD_ATTEMPTED.add(key)
        return HfFallbackStatus.NOT_FOUND
    except Exception as exc:  # noqa: BLE001
        raise AllFilingsHfDownloadError(
            f"allFilings HF 다운로드에 실패했습니다: {period or 'ALL'}",
            period=period,
        ) from exc

    _HF_DOWNLOAD_ATTEMPTED.add(key)
    if _hasBodyArtifact(outDir, period):
        return HfFallbackStatus.DOWNLOADED
    return HfFallbackStatus.NOT_FOUND


def loadDay(period: str) -> pl.DataFrame | None:
    """수집된 하루치 데이터 로드. 로컬 부재 시 HF 에서 lazy 다운로드.

    Args:
        period: YYYYMMDD.

    Raises:
        AllFilingsHfUnavailableError: 로컬 파일이 없고 HF fallback을 사용할 수 없는 경우.
        AllFilingsHfDownloadError: 로컬 파일이 없고 HF 원격 다운로드가 실패한 경우.
        OSError: parquet 파일 읽기 실패.

    Example:
        >>> loadDay("20260527")  # doctest: +SKIP

    Returns:
        pl.DataFrame 또는 None — 수집 결과.
    """
    path = _allFilingsDir() / f"{period}.parquet"
    if not path.exists():
        status = _ensureFromHf(period)
        if status is HfFallbackStatus.NOT_FOUND:
            return None
    if not path.exists():
        raise AllFilingsHfDownloadError(
            f"HF 다운로드 완료 후 allFilings artifact가 없습니다: {period}",
            period=period,
        )
    return pl.read_parquet(path)


@withMemoryBudget(limitMb=500)
def loadAll() -> pl.DataFrame:
    """원문 수집 완료된 전체 데이터 로드. 로컬 디렉토리 비어있으면 HF 에서 lazy 다운로드.

    Args:
        (인자 자동 생성).

    Raises:
        AllFilingsHfUnavailableError: 로컬 파일이 없고 HF fallback을 사용할 수 없는 경우.
        AllFilingsHfDownloadError: 로컬 파일이 없고 HF 원격 다운로드가 실패한 경우.
        OSError: parquet 파일 읽기 실패.

    Example:
        >>> loadAll()  # doctest: +SKIP

    Returns:
        pl.DataFrame — 결과.
    """
    outDir = _allFilingsDir()
    files = _bodyParquetFiles(outDir)
    if not files:
        status = _ensureFromHf()
        if status is HfFallbackStatus.NOT_FOUND:
            return pl.DataFrame()
        files = _bodyParquetFiles(outDir)
    if not files:
        raise AllFilingsHfDownloadError(
            "HF 다운로드 완료 후 allFilings artifact가 없습니다: ALL",
            period=None,
        )
    return pl.scan_parquet(files).collect(engine="streaming")


def stats() -> dict:
    """수집 현황 통계.

    Args:
        (인자 자동 생성).

    Raises:
        없음.

    Example:
        >>> stats(...)

    Returns:
        dict — 결과 dict.
    """
    completed = collectedDates()
    pending = pendingDates()

    outDir = _allFilingsDir()
    totalSize = 0
    totalRows = 0
    totalFilings = 0

    for d in completed:
        path = outDir / f"{d}.parquet"
        totalSize += path.stat().st_size
        df = pl.scan_parquet(path).select("rcept_no").collect(engine="streaming")
        totalRows += df.height
        totalFilings += df["rcept_no"].n_unique()

    pendingFilings = 0
    for d in pending:
        path = outDir / f"{d}{_META_SUFFIX}.parquet"
        df = pl.scan_parquet(path).select("rcept_no").collect(engine="streaming")
        pendingFilings += df["rcept_no"].n_unique()

    return {
        "completedDays": len(completed),
        "pendingDays": len(pending),
        "filings": totalFilings,
        "pendingFilings": pendingFilings,
        "rows": totalRows,
        "sizeMb": round(totalSize / 1024 / 1024, 1),
        "firstDate": completed[-1] if completed else None,
        "lastDate": completed[0] if completed else None,
    }
