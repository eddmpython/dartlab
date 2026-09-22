"""allFilings stage — 비정기 공시 **일별** parquet forward 증분 (recent N days).

원본=SSOT 전략([[project_original_ssot_strategy]]): allFilings 는 원본 zip 보관 안 함 —
``collectMetaRange``+``fillContent`` 로 **일자별** parquet(``data/dart/allFilings/{date}.parquet``,
``{date}``=YYYYMMDD)만 유지. 일자가 immutable 키라 윈도가 월 경계를 넘어도 손상 0(각 날짜 독립
파일). 정기보고서(사업/분기/반기)는 ``report_nm`` 으로 자동 제외 → docs(정기 zip) 와 중복 0.
``pushAllFilings`` 가 자체 HF 업로드(``_meta`` 제외, dart/allFilings 단일 소유 = 본 stage —
옛 검색 인덱스 워크플로의 이중 push 제거됨). lookback 일수는 ``SYNC_LOOKBACK_DAYS`` env(기본 7)
또는 ``DART_ALLFILINGS_LOOKBACK``.
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta

from dartlab.pipeline.types import PipelineMode, StageResult

_TRANSIENT_ERROR_NAMES = (
    "Timeout",
    "Connect",
    "Connection",
    "Network",
    "Protocol",
    "Transport",
)


def _recentDates(days: int) -> list[str]:
    """오늘 포함 최근 ``days`` 일의 YYYYMMDD 리스트(최신→과거)."""
    today = date.today()
    return [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]


def _prevMonths(earliestYm: str, months: int, floorYm: str) -> list[str]:
    """``earliestYm``(YYYYMM) 직전부터 과거로 최대 ``months`` 개월(YYYYMM), ``floorYm`` 이상만."""
    out: list[str] = []
    y, m = int(earliestYm[:4]), int(earliestYm[4:6])
    for _ in range(months):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        ym = f"{y:04d}{m:02d}"
        if ym < floorYm:
            break
        out.append(ym)
    return out


def _monthDays(ym: str) -> list[str]:
    """``ym``(YYYYMM) 의 1일~말일 YYYYMMDD 리스트(과거→미래)."""
    import calendar

    y, m = int(ym[:4]), int(ym[4:6])
    last = calendar.monthrange(y, m)[1]
    return [f"{ym}{d:02d}" for d in range(1, last + 1)]


def _stageRetries() -> int:
    """Return transient retry count for allFilings source-owner stages."""
    raw = os.environ.get("DART_ALLFILINGS_STAGE_RETRIES", "2")
    try:
        return max(0, int(raw))
    except ValueError:
        return 2


def _progressEnabled() -> bool:
    """Return whether collector-level allFilings progress logs should be emitted."""
    raw = (os.environ.get("DART_ALLFILINGS_SHOW_PROGRESS") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _retrySleepSeconds(attempt: int) -> float:
    """Backoff seconds for transient DART list/content failures."""
    raw = os.environ.get("DART_ALLFILINGS_RETRY_SLEEP_SECONDS")
    if raw is not None:
        try:
            return max(0.0, float(raw))
        except ValueError:
            return 0.0
    return min(30.0, float(2**attempt))


def _isTransientError(exc: Exception) -> bool:
    """Network/API transport failures are retryable; data contract errors are not."""
    name = type(exc).__name__
    text = str(exc).lower()
    if isinstance(exc, OSError):
        return True
    if any(part in name for part in _TRANSIENT_ERROR_NAMES):
        return True
    return any(
        token in text
        for token in (
            "timed out",
            "timeout",
            "connection",
            "temporarily unavailable",
            "too many requests",
            "503",
            "504",
        )
    )


def _retryTransient(label: str, fn):
    """Run a transient-prone source call with bounded retries."""
    retries = _stageRetries()
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — stage-level transient gate
            if attempt >= retries or not _isTransientError(exc):
                raise
            wait = _retrySleepSeconds(attempt)
            print(
                f"[pipeline] allFilings {label} 일시 실패 "
                f"({attempt + 1}/{retries + 1}, {type(exc).__name__}: {exc}) — retry",
                flush=True,
            )
            if wait > 0:
                time.sleep(wait)


def runAllFilings(
    *,
    category: str = "allFilings",
    mode: PipelineMode = "incremental",
    codes: list[str] | None = None,
    upload: bool = True,
    token: str | None = None,
) -> StageResult:
    """allFilings 비정기 공시 forward 증분 수집 → 월별 parquet + HF push.

    Args:
        category: 미사용("allFilings" 고정).
        mode: 미사용(incremental 고정).
        codes: 미사용(날짜 윈도 기반).
        upload: HF 업로드(``pushAllFilings``) 여부.
        token: HF 토큰.

    Returns:
        StageResult (rows=수집 본문 행수, uploaded=push 한 일자수).

    Raises:
        없음 (수집/업로드 예외는 StageResult 로 격리).

    Example:
        >>> runAllFilings(upload=False)  # doctest: +SKIP
        StageResult(category='allFilings', ...)
    """
    from dartlab.gather.dart.allFilingsCollector import collectMetaRange, fillContent
    from dartlab.gather.dart.allFilingsSync import pushAllFilings

    days = int(os.environ.get("SYNC_LOOKBACK_DAYS") or os.environ.get("DART_ALLFILINGS_LOOKBACK") or "7")
    dates = _recentDates(days)
    start, end = dates[-1], dates[0]
    progress = _progressEnabled()
    res = StageResult(category="allFilings")
    started = time.monotonic()

    try:
        print(
            f"[pipeline] allFilings forward 시작: {start}~{end} "
            f"({len(dates)}일) · upload={upload} · progress={progress}",
            flush=True,
        )
        _retryTransient("collectMetaRange", lambda: collectMetaRange(start, end, showProgress=progress))
        rows = 0
        for d in dates:
            dayStarted = time.monotonic()
            print(f"[pipeline] allFilings fillContent 시작: {d}", flush=True)
            df = _retryTransient(f"fillContent {d}", lambda d=d: fillContent(d, showProgress=progress))
            dayRows = df.height if df is not None else 0
            if df is not None:
                rows += dayRows
            print(
                f"[pipeline] allFilings fillContent 완료: {d} · rows={dayRows} · "
                f"elapsed={time.monotonic() - dayStarted:.1f}s",
                flush=True,
            )
        res.rows = rows
        res.report.ok = 1
        print(
            f"[pipeline] allFilings forward 수집 완료: rows={rows} · elapsed={time.monotonic() - started:.1f}s",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001 — 수집 실패 격리(다음 sync 자연 회복)
        res.report.err = 1
        res.report.failures.append(f"allFilings collect {start}~{end}: {type(exc).__name__}: {exc}")
        print(f"[pipeline] allFilings 수집 실패(격리): {exc}", flush=True)
        return res

    if upload:
        try:
            pushAllFilings(dates, token=token)
            res.uploaded = len(dates)
        except Exception as exc:  # noqa: BLE001 — 업로드 실패 격리
            res.report.fail = 1
            res.report.failures.append(f"allFilings push: {type(exc).__name__}: {exc}")
            print(f"[pipeline] allFilings push 실패(격리): {exc}", flush=True)
    return res


def runAllFilingsReconcile(
    *,
    category: str = "allFilingsReconcile",
    mode: PipelineMode = "incremental",
    codes: list[str] | None = None,
    upload: bool = True,
    token: str | None = None,
) -> StageResult:
    """allFilings 로컬 ↔ HF **양방향 reconcile** stage (운영자 트리거).

    forward 증분(``runAllFilings``)이 최근 N일만 본다면, 본 stage 는 로컬·HF 전 일자를
    집합 비교해 부족분만 양쪽으로 채운다(``reconcileAllFilings``): HF 가 앞선 일자는
    로컬로 pull, 로컬이 앞선 일자는 HF 로 push. 월 단위 백필 후 또는 머신/CI 간 동기화에
    쓴다. ⚠ ephemeral CI runner 에서 부르면 pull 이 전 이력 재다운로드라 무의미 —
    영속 로컬 store(운영자 머신)용. daily 최신화는 ``originalSync.yml`` allfilings job 이 담당.

    Args:
        category: 미사용("allFilingsReconcile" 고정).
        mode: 미사용.
        codes: 미사용(전 일자 집합 비교).
        upload: False 면 push 방향 끔(pull-only reconcile).
        token: HF 토큰.

    Returns:
        StageResult (rows=pull 한 일자수, uploaded=push 한 일자수).

    Raises:
        없음 (reconcile 예외는 StageResult 로 격리).

    Example:
        >>> runAllFilingsReconcile(upload=False)  # doctest: +SKIP
        StageResult(category='allFilingsReconcile', ...)
    """
    from dartlab.gather.dart.allFilingsSync import reconcileAllFilings

    res = StageResult(category="allFilingsReconcile")
    try:
        summary = reconcileAllFilings(pull=True, push=upload, token=token)
        res.rows = int(summary["pulled"])
        res.uploaded = int(summary["pushed"])
        res.report.ok = 1
        print(
            f"[pipeline] allFilings reconcile: 로컬 {summary['localBefore']}→{summary['localAfter']}일, "
            f"HF {summary['remoteBefore']}일 · pull {summary['pulled']} · push {summary['pushed']}"
            f" · inSync={summary['inSync']}",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001 — reconcile 실패 격리(다음 호출 자연 회복)
        res.report.err = 1
        res.report.failures.append(f"allFilings reconcile: {type(exc).__name__}: {exc}")
        print(f"[pipeline] allFilings reconcile 실패(격리): {exc}", flush=True)
    return res


def runAllFilingsBackfill(
    *,
    category: str = "allFilingsBackfill",
    mode: PipelineMode = "backfill",
    codes: list[str] | None = None,
    upload: bool = True,
    token: str | None = None,
) -> StageResult:
    """allFilings 과거 백필 — 현 커버리지 직전부터 과거로 N개월씩(floor 2015-01) 채워 push.

    forward(``runAllFilings``)가 최신을 좇는다면, 본 stage 는 과거 커버리지를 한 run 당
    ``DART_ALLFILINGS_BACKFILL_MONTHS``(기본 2) 개 캘린더 월만큼 늘린다. 로컬
    (``collectedDates``)·HF(``_remoteDates``) 합집합의 최오래 일자를 앵커로 그 *직전* 달부터
    과거로 월을 걷되, ``DART_ALLFILINGS_BACKFILL_FLOOR``(기본 201501) 이전은 건드리지 않는다 —
    앵커 월이 floor 이하면 no-op(커버리지 달성). 휴일은 ``fillContent`` 가 자동 skip.
    월 단위로 수집·push 해 timeout 내성을 갖는다(중간에 끊겨도 앞 월은 immutable 보존).
    ephemeral CI 안전: HF 전 이력 다운로드 없이 ``_remoteDates`` 스코프 목록만 읽고 DART
    에서 신규 일자만 수집 후 일자별 immutable push(reconcile 의 전이력 pull 안티패턴 회피).

    Args:
        category: 미사용("allFilingsBackfill" 고정).
        mode: 미사용(backfill 고정).
        codes: 미사용(날짜 윈도 기반).
        upload: HF 업로드(``pushAllFilings``) 여부.
        token: HF 토큰. None 이면 env ``HF_TOKEN``.

    Returns:
        StageResult (rows=수집 본문 행수, uploaded=push 한 일자수). 커버리지 달성 시 0/0 이고
        ``skipped=True`` (할 일 없음). 장애 격리(skip)는 ``skipped`` 를 켜지 않는다.

    Raises:
        없음 (앵커 조회/수집/업로드 예외는 StageResult 로 격리).

    Example:
        >>> runAllFilingsBackfill(upload=False)  # doctest: +SKIP
        StageResult(category='allFilingsBackfill', ...)
    """
    from dartlab.core.dartClient import DartClient
    from dartlab.gather.dart.allFilingsCollector import collectedDates, fillContent
    from dartlab.gather.dart.allFilingsSync import _remoteDates, pushAllFilings

    months = int(os.environ.get("DART_ALLFILINGS_BACKFILL_MONTHS") or "2")
    floorYm = (os.environ.get("DART_ALLFILINGS_BACKFILL_FLOOR") or "201501").strip()
    progress = _progressEnabled()
    res = StageResult(category="allFilingsBackfill")
    started = time.monotonic()

    try:
        existing = set(collectedDates()) | _remoteDates(token=token)
    except Exception as exc:  # noqa: BLE001 — 백필은 forward/search 갱신을 막지 않는 opportunistic 단계.
        res.report.skip = 1
        res.report.failures.append(f"allFilings backfill 앵커 조회: {type(exc).__name__}: {exc}")
        print(f"[pipeline] allFilings backfill 앵커 조회 실패(격리): {exc}", flush=True)
        return res

    if not existing:
        # 선행 조건 이상이지 "할 일 없음" 이 아니다. HF 목록이 비는 레이아웃 변경 같은 사고를 초록으로
        # 덮지 않게 skipped 를 켜지 않는다. 뒤 버킷 단계가 빈 입력으로 실패해 드러난다.
        res.report.skip = 1
        res.report.failures.append("allFilings backfill: 로컬·HF 기존 일자 0 (forward seed 선행 필요)")
        print("[pipeline] allFilings backfill: 기존 일자 0, forward seed 선행 필요", flush=True)
        return res

    earliestYm = min(existing)[:6]
    targetMonths = _prevMonths(earliestYm, months, floorYm)
    if not targetMonths:
        # 할 일이 없다는 선언. 워크플로는 이 값을 보고 버킷 빌드와 카탈로그를 건너뛴다. 수집 장애로 0일을
        # 모은 경우는 skipped 가 아니므로 뒤 단계가 빈 입력으로 실패해 장애가 드러난다.
        res.skipped = True
        res.report.ok = 1
        print(
            f"[pipeline] allFilings backfill: 앵커 월 {earliestYm} ≤ floor {floorYm} — 커버리지 달성, no-op",
            flush=True,
        )
        return res

    client = DartClient()
    rows = 0
    uploaded = 0
    print(
        f"[pipeline] allFilings backfill 시작: months={targetMonths} · "
        f"existing={len(existing)}일 · upload={upload} · progress={progress}",
        flush=True,
    )
    for ym in targetMonths:
        days = [d for d in _monthDays(ym) if d not in existing]
        collected: list[str] = []
        monthRows = 0
        monthStarted = time.monotonic()
        print(f"[pipeline] allFilings backfill {ym} 시작: 대상 {len(days)}일", flush=True)
        try:
            for d in days:
                dayStarted = time.monotonic()
                df = fillContent(d, client=client, showProgress=progress)
                dayRows = df.height if df is not None else 0
                if df is not None:
                    rows += dayRows
                    monthRows += dayRows
                    collected.append(d)
                print(
                    f"[pipeline] allFilings backfill {ym}/{d} 완료: rows={dayRows} · "
                    f"elapsed={time.monotonic() - dayStarted:.1f}s",
                    flush=True,
                )
        except Exception as exc:  # noqa: BLE001 — 월 수집 실패는 다음 백필 run 에서 재시도.
            res.report.skip += 1
            res.report.failures.append(f"allFilings backfill {ym}: {type(exc).__name__}: {exc}")
            print(f"[pipeline] allFilings backfill {ym} 수집 실패(격리): {exc}", flush=True)
            break

        if upload and collected:
            try:
                pushAllFilings(collected, token=token)
                uploaded += len(collected)
            except Exception as exc:  # noqa: BLE001 — push 실패는 다음 백필 run 에서 재시도.
                res.report.skip += 1
                res.report.failures.append(f"allFilings backfill push {ym}: {type(exc).__name__}: {exc}")
                print(f"[pipeline] allFilings backfill {ym} push 실패(격리): {exc}", flush=True)
        print(
            f"[pipeline] allFilings backfill {ym}: {len(collected)}일 수집·push · "
            f"rows={monthRows} · elapsed={time.monotonic() - monthStarted:.1f}s",
            flush=True,
        )

    res.rows = rows
    res.uploaded = uploaded
    res.report.ok = 1
    print(
        f"[pipeline] allFilings backfill 완료: {targetMonths} ({len(targetMonths)}개월) · "
        f"{rows} rows · push {uploaded}일 · floor={floorYm} · "
        f"elapsed={time.monotonic() - started:.1f}s",
        flush=True,
    )
    return res
