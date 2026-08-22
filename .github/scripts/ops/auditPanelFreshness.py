"""DART panel 신선도 감사. 워크플로 결론과 무관하게 "데이터가 실제로 들어왔는가" 를 잰다.

2026-07-30~08-21 사고: 모든 수집 job 이 초록이었는데 HF panel(공시뷰어가 직접 읽는 parquet)은
6 월 이후 멈춰 있었다. 종목 단위 실패가 run 결론에 반영되지 않아 run 기반 모니터는 아무것도 보지
못했다. 이 감사는 DART 공시목록(정기보고서 rcept)을 진실로 삼아 HF panel 의 ``rceptNo`` 보유와
직접 대조한다. 원인이 레이아웃 계약이든 업로드 실패든 큐 축출이든, panel 이 멈추면 여기서 드러난다.

판정: grace 일이 지난 정기 rcept 중 panel 에 없는 것이 ``max(MIN_MISSING_ALERT, 비율 임계 * 기대)``
를 넘으면 breach. 단발 fetch 실패나 신규 상장 잔여는 reconcile(85일 윈도, 매일)이 흡수하므로
작은 잔여는 알리지 않는다.

시간 예산: HF 조회가 느린 날(2026-08-22 실측: 연결 끊김 재시도가 겹쳐 Data Audit 이 20 분 timeout)
감사가 모니터 전체를 끌고 죽지 않게, 예산(초)을 넘기면 남은 종목을 포기하고 그때까지의 표본으로
돌아온다. 못 본 종목은 조회 실패로 세고, 표본이 절반도 안 되면 모니터는 판정을 유보한다.

환경변수:
  DART_API_KEYS: 공시목록 조회(필수. 없으면 감사를 건너뛰고 그 사실을 보고한다).
  HF_TOKEN: 선택(공개 dataset 이라 없어도 읽는다).
  DARTLAB_FRESHNESS_BUDGET_SECONDS: 조회 예산(초). 기본 AUDIT_BUDGET_SECONDS.
"""

from __future__ import annotations

import math
import os
import queue
import re
import sys
import threading
import time
from collections.abc import Callable
from datetime import date, timedelta

AUDIT_NAME = "DART panel 신선도"
WINDOW_DAYS = 30  # 공시목록 조회 창. corp 생략 list.json 의 3개월 cap 안쪽.
GRACE_DAYS = 3  # 제출 뒤 이 일수 안의 rcept 는 아직 도달 중으로 보고 판정에서 뺀다(forward 7일 + reconcile 매일).
MIN_MISSING_ALERT = 20  # 절대 하한. 이 수 이하의 잔여는 reconcile 이 흡수한다.
MISSING_RATIO_ALERT = 0.02  # 기대 rcept 대비 비율 상한.
LOOKUP_WORKERS = 8
AUDIT_BUDGET_SECONDS = 900.0  # HF rceptNo 조회 예산. Data Audit job 상한(30분) 안에서 gh 호출 몫을 남긴다.
MIN_COVERAGE_FOR_VERDICT = 0.5  # 예산 초과 시 이 비율 미만으로만 봤으면 판정하지 않는다.
# 첨부만 바뀐 정정은 DART document API 가 status 014(파일 없음)를 돌려줘 본문 zip 이 없다(2026-08-22 실측:
# 000440 20260730000361·20260730000551). panel 에 들어올 수 없으므로 기대 집합에서 뺀다. 두면 영구 "누락" 이 된다.
_ATTACHMENT_ONLY_RE = re.compile(r"^\[(?:첨부정정|첨부추가)\]")


def judge(expected: int, missing: int) -> bool:
    """누락 수가 알림 임계를 넘는지(순수 함수).

    Args:
        expected: grace 를 지난 정기 rcept 수.
        missing: 그중 panel 에 없는 수.

    Returns:
        breach 면 True.

    Raises:
        없음.

    Example:
        >>> judge(2900, 19), judge(2900, 58), judge(2900, 59)
        (False, False, True)
    """
    if expected <= 0:
        return False
    return missing > max(MIN_MISSING_ALERT, math.ceil(expected * MISSING_RATIO_ALERT))


def lookupWithBudget(
    codes: list[str],
    fn: Callable[[str], object],
    *,
    workers: int,
    budgetSeconds: float,
) -> tuple[dict[str, object], bool]:
    """daemon 스레드 풀로 fn(code) 를 병렬 호출하되 예산(초)을 넘기면 남은 종목을 포기하고 돌아온다.

    ThreadPoolExecutor 는 종료 시 실행 중 스레드를 기다려 프로세스 종료까지 묶는다. daemon 스레드 + 큐로
    받고, 예산이 끝나면 그때까지의 결과만 돌려준다. 결과에 없는 종목은 호출자가 조회 실패로 센다.

    Args:
        codes: 조회할 종목코드.
        fn: 종목코드 하나를 받아 결과를 돌려주는 함수. 예외는 None 결과로 흡수한다.
        workers: 동시 스레드 수.
        budgetSeconds: 전체 예산(초).

    Returns:
        ``({code: 결과}, 예산 초과 여부)``.

    Raises:
        없음.

    Example:
        >>> lookupWithBudget(["a", "b"], len, workers=2, budgetSeconds=5)
        ({'a': 1, 'b': 1}, False)
    """
    if not codes:
        return {}, False
    pending: queue.Queue[str] = queue.Queue()
    for code in codes:
        pending.put(code)
    done: queue.Queue[tuple[str, object]] = queue.Queue()

    def worker() -> None:
        """큐가 빌 때까지 종목을 하나씩 조회해 결과 큐에 넣는다."""
        while True:
            try:
                code = pending.get_nowait()
            except queue.Empty:
                return
            try:
                done.put((code, fn(code)))
            except Exception:  # noqa: BLE001 (개별 조회 실패는 None. 호출자가 조회 실패로 센다)
                done.put((code, None))

    for index in range(min(workers, len(codes))):
        threading.Thread(target=worker, daemon=True, name=f"freshness-{index}").start()
    deadline = time.monotonic() + budgetSeconds
    results: dict[str, object] = {}
    while len(results) < len(codes):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            code, value = done.get(timeout=min(remaining, 5.0))
        except queue.Empty:
            continue
        results[code] = value
    return results, len(results) < len(codes)


def auditPanelFreshness(
    *,
    windowDays: int = WINDOW_DAYS,
    graceDays: int = GRACE_DAYS,
    today: date | None = None,
    token: str | None = None,
    budgetSeconds: float | None = None,
) -> dict:
    """DART 정기 rcept 대비 HF panel 보유를 대조해 누락 통계를 돌려준다.

    Args:
        windowDays: 공시목록 조회 창(일).
        graceDays: 판정에서 제외할 최근 일수.
        today: 기준일(테스트 주입용). None 이면 오늘.
        token: HF 토큰(선택).
        budgetSeconds: HF 조회 예산(초). None 이면 env DARTLAB_FRESHNESS_BUDGET_SECONDS, 없으면 기본값.

    Returns:
        ``{"expected", "missing", "unknownCompanies", "companies", "lookedUp", "coverage", "timedOut",
        "breach", "samples", "window"}``. ``samples`` 는 누락 (stockCode, rceptNo, rceptDt, reportNm)
        최대 20 건(오래된 순). 예산 초과로 못 본 종목은 ``unknownCompanies`` 에 들어가고 판정 모수에서 빠진다.

    Raises:
        RuntimeError: 공시목록 조회가 실패하거나 비어 있을 때(감사 불능은 숨기지 않는다).

    Example:
        >>> auditPanelFreshness()["breach"]  # doctest: +SKIP
        False
    """
    import polars as pl

    from dartlab.core.dataConfig import DATA_RELEASES, repoFor
    from dartlab.gather.dart.client import DartClient
    from dartlab.gather.dart.disclosure import listFilings
    from dartlab.pipeline.stages.panelRceptReconcile import _PERIODIC_RE, _panelRceptsFromHf

    if budgetSeconds is None:
        budgetSeconds = float(os.environ.get("DARTLAB_FRESHNESS_BUDGET_SECONDS") or AUDIT_BUDGET_SECONDS)
    anchor = today or date.today()
    start = (anchor - timedelta(days=windowDays - 1)).strftime("%Y%m%d")
    end = anchor.strftime("%Y%m%d")
    cutoff = (anchor - timedelta(days=graceDays)).strftime("%Y%m%d")

    client = DartClient()
    filings = listFilings(client, corp=None, start=start, end=end, filingType="A", fetchAll=True)
    if filings.is_empty() or "rcept_no" not in filings.columns or "stock_code" not in filings.columns:
        raise RuntimeError(f"정기공시 목록이 비어 있습니다: {start}~{end}")

    periodic = filings.filter(
        pl.col("report_nm").str.contains(_PERIODIC_RE)
        & pl.col("stock_code").is_not_null()
        & (pl.col("stock_code").str.strip_chars() != "")
        & (pl.col("rcept_dt").cast(pl.Utf8) <= cutoff)
    )
    expectedByCode: dict[str, dict[str, tuple[str, str]]] = {}
    for stockCode, rceptNo, rceptDt, reportNm in periodic.select(
        ["stock_code", "rcept_no", "rcept_dt", "report_nm"]
    ).iter_rows():
        code = (stockCode or "").strip()
        if not code or not rceptNo or _ATTACHMENT_ONLY_RE.match(str(reportNm)):
            continue
        expectedByCode.setdefault(code, {})[str(rceptNo)] = (str(rceptDt), str(reportNm))

    repo = repoFor("panel")
    relDir = DATA_RELEASES["panel"]["dir"]
    have, timedOut = lookupWithBudget(
        sorted(expectedByCode),
        lambda code: _panelRceptsFromHf(repo, relDir, code, token=token),
        workers=LOOKUP_WORKERS,
        budgetSeconds=budgetSeconds,
    )

    expected = 0
    unknownCompanies = 0
    missing: list[tuple[str, str, str, str]] = []
    for code, rcepts in expectedByCode.items():
        owned = have.get(code)
        if owned is None:
            unknownCompanies += 1  # 조회 일시 실패 또는 예산 초과. 판정 모수에서 뺀다(다음 감사에서 다시 본다).
            continue
        expected += len(rcepts)
        for rceptNo, (rceptDt, reportNm) in rcepts.items():
            if rceptNo not in owned:  # type: ignore[operator]
                missing.append((code, rceptNo, rceptDt, reportNm))
    missing.sort(key=lambda item: (item[2], item[0], item[1]))
    companies = len(expectedByCode)
    lookedUp = len(have)
    return {
        "expected": expected,
        "missing": len(missing),
        "unknownCompanies": unknownCompanies,
        "companies": companies,
        "lookedUp": lookedUp,
        "coverage": (lookedUp / companies) if companies else 1.0,
        "timedOut": timedOut,
        "breach": judge(expected, len(missing)),
        "samples": missing[:20],
        "window": f"{start}~{cutoff}",
    }


def describe(result: dict) -> str:
    """감사 결과를 한 줄 요약으로 만든다(Issue 본문·step summary 용).

    Args:
        result: ``auditPanelFreshness`` 반환값.

    Returns:
        예: ``누락 12/2905 (0.4%) · 조회실패 0종목 · 창 20260724~20260819``. 예산 초과면 미조회 수를 덧붙인다.

    Raises:
        없음.

    Example:
        >>> describe({"expected": 100, "missing": 1, "unknownCompanies": 0, "window": "a~b"})
        '누락 1/100 (1.0%) · 조회실패 0종목 · 창 a~b'
    """
    expected = int(result.get("expected", 0))
    missing = int(result.get("missing", 0))
    ratio = (missing / expected) if expected else 0.0
    text = (
        f"누락 {missing}/{expected} ({ratio:.1%}) · 조회실패 {int(result.get('unknownCompanies', 0))}종목 · "
        f"창 {result.get('window', '-')}"
    )
    if result.get("timedOut"):
        unseen = int(result.get("companies", 0)) - int(result.get("lookedUp", 0))
        text += f" · 예산 초과(미조회 {unseen}종목, 표본 {float(result.get('coverage', 0.0)):.0%})"
    return text


def main() -> int:
    """CLI: 감사를 돌리고 요약을 찍는다. breach 면 종료코드 1.

    Args:
        없음.

    Returns:
        0 정상, 1 breach, 2 감사 불능(키 없음·조회 실패·표본 부족).

    Raises:
        없음.

    Example:
        >>> main()  # doctest: +SKIP
        0
    """
    if not os.environ.get("DART_API_KEYS") and not os.environ.get("DART_API_KEY"):
        print(f"[{AUDIT_NAME}] DART_API_KEYS 없음. 감사를 건너뜁니다.", flush=True)
        return 2
    try:
        result = auditPanelFreshness(token=os.environ.get("HF_TOKEN") or None)
    except Exception as exc:  # noqa: BLE001 (감사 불능은 그 사실을 보고하고 2 로 끝낸다)
        print(f"[{AUDIT_NAME}] 감사 실패: {type(exc).__name__}: {exc}", flush=True)
        return 2
    print(f"[{AUDIT_NAME}] {describe(result)} · breach={result['breach']}", flush=True)
    for code, rceptNo, rceptDt, reportNm in result["samples"]:
        print(f"  - {code} {rceptNo} {rceptDt} {reportNm}", flush=True)
    if result["timedOut"] and result["coverage"] < MIN_COVERAGE_FOR_VERDICT:
        print(f"[{AUDIT_NAME}] 표본 부족으로 판정 유보.", flush=True)
        return 2
    return 1 if result["breach"] else 0


if __name__ == "__main__":
    sys.exit(main())
