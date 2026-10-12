"""DART 공시 원본 zip 수집 → ``data/original/dart/{docs,allFilings}/``.

날짜 범위의 전 종목 공시를 ``list.json`` 으로 열거하고, 각 ``rcept_no`` 의
``document.xml`` 원본 zip 을 **가공 0** 으로 디스크에 보관한다. 정기보고서는
``docs/``, 비정기는 ``allFilings/`` 로 분리(panel/refScan 혼입 차단). 이미 있는
zip 은 skip(idempotent). zip 저장은 ``.tmp`` → ``os.replace`` atomic.

``allFilingsCollector``(parquet content_raw)와 공존한다. 본 모듈은 원본 zip 백업,
저쪽은 파생 parquet. 둘은 독립.

``list.json``·``document.xml`` 은 공용 ``DartClient`` 로 부른다. 예전에는 같은 키풀 로직을 복제한 전용
client 를 썼는데 전송·연결 재시도가 없어, 응답 없는 끊김 한 번에 archive 전체가 죽었다(2026-10-02, 10-08,
10-11 Original SSOT Sync dart-zip). 공용 client 는 재시도, XML 상태 본문 해석, XML 020 키 로테이션을 갖는다.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from dartlab.core.logger import getLogger
from dartlab.gather.dart.client import DartClient

from .paths import dartDocsDir, dartFilingsDir

_log = getLogger(__name__)

# 정기보고서 식별 — docs/ 로 분리. allFilingsCollector 와 동일 패턴.
_PERIODIC_PATTERNS: tuple[str, ...] = ("사업보고서", "분기보고서", "반기보고서")
_ZIP_MAGIC = b"PK\x03\x04"
_MIN_VALID_BYTES = 64  # 이보다 작으면 status XML(본문 부재) 로 간주


def _iterDays(start: str, end: str) -> list[str]:
    """``YYYYMMDD`` start~end(포함) 일자 list — 최신→과거.

    Args:
        start: 시작일 YYYYMMDD.
        end: 종료일 YYYYMMDD.

    Returns:
        list[str] — 일자 문자열(내림차순).

    Raises:
        ValueError: 날짜 형식 오류.

    Example:
        >>> _iterDays("20260601", "20260603")
        ['20260603', '20260602', '20260601']
    """
    s = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    days: list[str] = []
    cur = e
    while cur >= s:
        days.append(cur.strftime("%Y%m%d"))
        cur -= timedelta(days=1)
    return days


def _isPeriodic(reportNm: str) -> bool:
    """report_nm 이 정기보고서인지(docs/ 분리 판정).

    Args:
        reportNm: 공시 보고서명.

    Returns:
        bool — 사업/반기/분기보고서면 True.

    Raises:
        없음.

    Example:
        >>> _isPeriodic("사업보고서 (2025.12)")
        True
    """
    return any(p in reportNm for p in _PERIODIC_PATTERNS)


def _writeZip(client: DartClient, rceptNo: str, outPath) -> str:
    """단일 rcept document.xml → zip 파일 atomic write.

    Args:
        client: DartClient. 013/014 XML 상태 본문은 예외가 아니라 bytes 로 돌려받는다.
        rceptNo: 14자리 접수번호.
        outPath: 저장 경로(``Path``).

    Returns:
        str — ``"ok"``(저장) / ``"no_body"``(본문 부재 통지) / ``"error"``(실패).

    Raises:
        없음 — 모든 예외는 ``"error"`` 로 흡수.

    Example:
        >>> _writeZip(client, "20240101000001", path)  # doctest: +SKIP
    """
    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except Exception:  # noqa: BLE001 — 개별 실패는 수집 전체 중단 X
        return "error"
    if not raw or len(raw) < _MIN_VALID_BYTES:
        # status XML(013 접수번호 오류 / 014 파일 부재) 또는 빈 응답
        head = (raw or b"")[:300]
        if b"<status>014" in head or b"<status>013" in head:
            return "no_body"
        return "error"
    if raw[:4] != _ZIP_MAGIC:
        head = raw[:300]
        if b"<status>014" in head or b"<status>013" in head:
            return "no_body"
        return "error"
    outPath.parent.mkdir(parents=True, exist_ok=True)
    tmp = outPath.with_suffix(f".zip.tmp.{os.getpid()}.{time.monotonic_ns()}")
    try:
        tmp.write_bytes(raw)
        os.replace(tmp, outPath)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return "error"
    return "ok"


def archiveDartOriginals(
    start: str,
    end: str,
    *,
    scope: str = "all",
    corpClasses: tuple[str, ...] = ("Y", "K"),
    workers: int = 4,
    showProgress: bool = True,
) -> dict[str, object]:
    """DART 공시 원본 zip 을 ``data/original/dart/`` 에 수집(가공 0, idempotent).

    Capabilities:
        - 날짜 범위 전 종목 공시를 ``list.json`` 으로 열거 → 각 ``document.xml`` 원본
          zip 을 디스크 보관. 정기=``docs/`` · 비정기=``allFilings/`` 분리. 기존 zip
          skip, 본문 부재(013/014)는 영구 skip, atomic write. 키풀 sequential-exhausted
          로 per-IP 차단 회피(§15).

    Args:
        start: 시작일 ``YYYYMMDD``.
        end: 종료일 ``YYYYMMDD``.
        scope: ``"all"``(정기+비정기) / ``"periodic"`` / ``"nonperiodic"``.
        corpClasses: 법인구분 필터(기본 ``("Y","K")`` = 유가·코스닥 상장).
        workers: document.xml 병렬 fetch 워커 수(기본 4 — DART 권장).
        showProgress: 진행 로그 출력.

    Returns:
        dict[str, int] — ``{"ok", "noBody", "skipped", "error", "days"}`` 집계.

    Raises:
        DartApiError: 전 키 한도 소진(020) 또는 list.json 오류 상태.
        httpx.HTTPError: list.json 전송·연결 재시도 소진.
        ValueError: DART 키 0개, 날짜 형식 또는 scope 값 오류.

    Example:
        >>> archiveDartOriginals("20260601", "20260603", scope="nonperiodic")  # doctest: +SKIP
        {'ok': 412, 'noBody': 3, 'skipped': 0, 'error': 0, 'days': 3}

    Guide:
        - ``scope="nonperiodic"`` 면 기존 정기 store(providers)와 중복 0.
        - 대량 백필은 월 단위로 끊어 호출(키 일일 한도/재개성). 재실행은 자동 이어감.

    SeeAlso:
        - ``providers.edgar.panel.build`` — EDGAR 는 raw ``.txt`` 저장 없이 panel 을 직접 빌드.
        - ``gather.dart.client.DartClient``: 본 함수의 fetch backend.
        - ``providers.dart.openapi.allFilingsCollector`` — 공존하는 parquet 수집(별개).

    Requires:
        - ``DART_API_KEY``/``DART_API_KEYS`` + 네트워크 + 쓰기 가능 ``data/original/``.

    When:
        - 운영자가 날짜 범위 원본 백업을 수집/백필할 때(분석 흐름 아님).

    How:
        - 일자별 list.json 열거 → 정기/비정기 분리 → ThreadPool document.xml → zip atomic write.

    AIContext:
        원본 백업 배치 — AI 분석 흐름이 아니라 운영자/CLI 수집. 키 평문 노출 X.

    LLM Specifications:
        AntiPatterns:
            - 분석 파이프라인에서 호출 X — 무겁고 키 소비 큼(배치 전용).
            - 단일 키 대량 수집 X — DART_API_KEYS 다중.
            - scope 미지정 대량 호출 시 정기 중복 수집 주의(scope="nonperiodic" 권장).
        OutputSchema:
            - dict[str, int] 집계.
        Prerequisites:
            - DART_API_KEY(S) + 날짜 범위.
        Freshness:
            - 매 실행 list.json 재조회(정정공시/신규 반영) + 기존 zip skip.
        Dataflow:
            - list.json(일자) → rcept 분리(정기/비정기) → ThreadPool document.xml →
              data/original/dart/{docs,allFilings}/{code}/{rcept}.zip.
        TargetMarkets:
            - KR(DART) 정기+비정기 전 공시.
    """
    if scope not in ("all", "periodic", "nonperiodic"):
        raise ValueError(f"scope 는 all/periodic/nonperiodic: {scope!r}")

    client = DartClient()
    stats: dict[str, object] = {"ok": 0, "noBody": 0, "skipped": 0, "error": 0, "days": 0}
    classSet = set(corpClasses)
    changedCodes: set[str] = set()  # 신규 zip 받은 종목 (panel 증분 재빌드 대상)

    for day in _iterDays(start, end):
        rows = _collectDayRows(client, day, classSet)
        if not rows:
            continue
        stats["days"] += 1

        skippedBefore = int(stats["skipped"])  # 일별 skip 산출용(stats 는 전 기간 누적)
        targets = []  # (rceptNo, outPath, stockCode)
        for row in rows:
            reportNm = row.get("report_nm", "") or ""
            periodic = _isPeriodic(reportNm)
            if scope == "periodic" and not periodic:
                continue
            if scope == "nonperiodic" and periodic:
                continue
            stockCode = (row.get("stock_code", "") or "").strip()
            if not stockCode:
                continue  # 비상장 filer(빈 stock_code)는 본 universe 밖
            rceptNo = row.get("rcept_no", "")
            if not rceptNo:
                continue
            outDir = dartDocsDir(stockCode) if periodic else dartFilingsDir(stockCode)
            outPath = outDir / f"{rceptNo}.zip"
            if outPath.exists():
                stats["skipped"] += 1
                continue
            targets.append((rceptNo, outPath, stockCode))

        if not targets:
            if showProgress:
                _log.info("[%s] 신규 0 (skip %d)", day, int(stats["skipped"]) - skippedBefore)
            continue

        # changed 마킹은 zip 이 *실제로 써진*(ok) 종목만. fetch 실패(error/no_body)는 제외.
        # 큐잉 시점 마킹이면 일시 fetch 실패가 panel 재빌드+원본 tar 덮어쓰기(부분이력)를 유발(데이터 손실).
        okBefore, noBodyBefore, errBefore = int(stats["ok"]), int(stats["noBody"]), int(stats["error"])
        changedCodes |= _fetchDayTargets(client, targets, workers, stats)
        if showProgress:
            # stats 는 전 기간 누적이라 일별 값은 (당일 후 − 당일 전) 차분, 마지막 항만 누적 ok.
            _log.info(
                "[%s] ok=%d noBody=%d error=%d (누적 ok=%d)",
                day,
                int(stats["ok"]) - okBefore,
                int(stats["noBody"]) - noBodyBefore,
                int(stats["error"]) - errBefore,
                stats["ok"],
            )

    stats["changedCodes"] = sorted(changedCodes)
    if showProgress:
        _log.info(
            "DART 원본 수집 완료: ok=%s skipped=%s changed종목=%d", stats["ok"], stats["skipped"], len(changedCodes)
        )
    return stats


def _collectDayRows(client: DartClient, day: str, classSet: set[str]) -> list[dict]:
    """하루치 list.json 전 페이지 수집 + corpClass 필터. 013(결과 없음)은 빈 dict 로 받아 빈 list.

    Args:
        client: DartClient.
        day: 일자 YYYYMMDD.
        classSet: 허용 법인구분 set.

    Returns:
        list[dict] — 필터된 공시 행 list.

    Raises:
        없음.

    Example:
        >>> _collectDayRows(client, "20260601", {"Y", "K"})  # doctest: +SKIP
    """
    rows: list[dict] = []
    page = 1
    while True:
        params = {"bgn_de": day, "end_de": day, "page_no": str(page), "page_count": "100"}
        data = client.getJson("list.json", params, emptyOn013=True)
        pageRows = data.get("list", []) or []
        if not pageRows:
            break
        rows.extend(pageRows)
        totalPage = int(data.get("total_page", 1) or 1)
        if page >= totalPage:
            break
        page += 1
    if classSet:
        rows = [r for r in rows if (r.get("corp_cls") in classSet)]
    return rows


def _fetchDayTargets(
    client: DartClient,
    targets: list[tuple[str, object, str]],
    workers: int,
    stats: dict[str, int],
) -> set[str]:
    """하루치 신규 target 을 ThreadPool 로 document.xml fetch + write.

    Args:
        client: DartClient(스레드 안전).
        targets: ``[(rceptNo, outPath, stockCode), ...]``.
        workers: 워커 수.
        stats: 누적 집계 dict(in-place 갱신).

    Returns:
        set[str] — zip 이 실제로 써진(``"ok"``) 종목코드 집합(panel 증분 재빌드 대상).

    Raises:
        없음 — 개별 실패는 stats["error"] 로 집계.

    Example:
        >>> _fetchDayTargets(client, [("...", path, "005930")], 4, stats)  # doctest: +SKIP
        {'005930'}
    """
    okCodes: set[str] = set()
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futures = {ex.submit(_writeZip, client, rcept, path): code for rcept, path, code in targets}
        for fut in as_completed(futures):
            result = fut.result()
            code = futures[fut]
            if result == "ok":
                stats["ok"] += 1
                okCodes.add(code)
            elif result == "no_body":
                stats["noBody"] += 1
            else:
                stats["error"] += 1
    return okCodes
