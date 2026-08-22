"""파이프라인 건강 모니터 — 모든 실패 알림 + 단발은 자동 재실행 병행.

gh CLI로 각 워크플로우의 최근 실행을 조회한다. **실패는 단발이든 연속이든 모두 Issue 로
알린다**(운영자 가시성 우선 — 조용히 삼키지 않음). 단발 transient 실패는 알림과 **동시에 자동
재실행**(rerun)해 자가치유를 시도하고 Issue 에 "단발 — 자동 재실행 중"으로, **연속 2회+**
(persistent)는 "연속 — 조치 필요"로 표시해 심각도를 구분한다. 실패 로그/주석에서 원인(메모리/
디스크·HF 429·timeout·code)을 분류해 actionable 하게 적고, 전부 정상이면 열린 Issue 를 닫는다.

감시 대상 = **scheduled(cron) 데이터/자동화 파이프라인 전체**. 새 scheduled 워크플로우를
추가하면 여기 name 도 등록해야 그 실패가 알림된다(미등록 = 조용한 실패).

환경변수:
  GH_TOKEN: GitHub 토큰 (Actions에서 자동 제공). rerun 은 actions:write, Issue 는 issues:write.
"""

import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# scheduled(cron) 데이터/자동화 파이프라인 전체 — gh run list 의 워크플로우 `name:` 값과 정확히 일치해야 함.
# (제외: 코드 CI/CodeQL/Policy·Deploy·Publish·Metrics·EDGAR Safety Gate·Data Audit 자기 자신·mapBuild(cron 없음))
MONITORED_WORKFLOWS = [
    "Original SSOT Sync",  # dart-zip · allfilings · edgar (cron 0 2) — 핵심 원본/panel 파이프라인
    "AllFilings Backfill",  # allfilings 과거 심화 백필 (cron 30 5) — Original SSOT 이후 독립, 매일 실작업
    "Data Sync",
    "DART New Stocks Sync",
    "Data Prebuild (DART)",
    "EDGAR Data Sync (Bulk)",
    "Gov Price Sync (Bulk)",
    "Gov Index Sync (Bulk)",
    "Macro Data Sync (Bulk)",
    "News Archive Sync",
    "GDELT Sync",
    "Naver News Sync",  # 네이버 뉴스 private archive (cron 30 9) — 무키 시 green-noop, 키 설정 시 실데이터
    "Valuation Snapshot",
    "Search Index Build",  # 일·월 단일 검색 인덱스 빌드(compact-only) — 옛 Delta(일간)+Main(월간) fold
    "Quant Audit",
    "Update KindList",
    "Intent Model Pipeline",  # 공시 Q&A 라우팅 모델 빌드+회귀게이트+HF 업로드 (cron 0 20 일요일)
    "Notify Watch",  # 공개 왓처 토픽(IPO 신규상장·신규수주) 발송 (cron 0 8 평일) — 조용한 발송실패 가드
]

FAILURE_LABEL = "pipeline-failure"
RECENT_N = 5
_OK_CONCLUSIONS = ("success", "skipped")

# 데이터 신선도 축. run 결론이 전부 초록이어도 HF panel 에 최신 정기보고서가 없으면 알린다.
# 2026-07-30~08-21 사고: 종목 단위 실패가 run 결론에 안 실려 3 주 동안 아무 run 도 빨갛지 않았고,
# 공시뷰어가 읽는 panel 은 6 월에 멈춘 채였다. run 기반 감시만으로는 구조적으로 못 보는 갭이다.
FRESHNESS_URL = "https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/panel"


def _loadFreshnessModule():
    """같은 폴더의 auditPanelFreshness.py 를 경로로 적재한다(스크립트·테스트 양쪽에서 동일)."""
    path = Path(__file__).resolve().with_name("auditPanelFreshness.py")
    spec = importlib.util.spec_from_file_location("auditPanelFreshness", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"auditPanelFreshness 적재 실패: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freshnessEntry(result: dict, *, auditName: str, describe) -> dict:
    """감사 결과를 모니터 entry 로 바꾼다(순수 함수). breach 면 persistent(조치 필요), 아니면 ok.

    Args:
        result: ``auditPanelFreshness`` 반환값.
        auditName: 표시 이름.
        describe: 결과 한 줄 요약 함수.

    Returns:
        statuses/persistent 에 그대로 넣을 entry dict.

    Raises:
        없음.

    Example:
        >>> _freshnessEntry({"breach": False, "expected": 10, "missing": 0}, auditName="x", describe=str)["state"]
        'ok'
    """
    breach = bool(result.get("breach"))
    return {
        "name": auditName,
        "state": "persistent" if breach else "ok",
        "conclusion": describe(result),
        "classification": "panel 에 최신 정기보고서 미반영 (수집 job 결론과 무관한 데이터 정지)" if breach else "",
        "url": FRESHNESS_URL,
        "runId": None,
        "samples": list(result.get("samples") or []),
    }


def _auditFreshness() -> dict | None:
    """DART panel 신선도 감사를 돌려 entry 로 돌려준다. 키가 없으면 None(건너뜀 로그), 감사 불능은 unknown entry."""
    module = _loadFreshnessModule()
    # 감사는 수천 번의 HF range read 라 매 workflow_run 완료마다 돌리지 않는다. 워크플로가 일일 cron,
    # 수동, 그리고 panel 생산자(Original SSOT Sync) 완료 때만 "1" 을 준다. 미설정(로컬)은 실행.
    if os.environ.get("DARTLAB_FRESHNESS_AUDIT", "1") == "0":
        print(f"[monitor] {module.AUDIT_NAME}: 이 트리거에서는 건너뜀(DARTLAB_FRESHNESS_AUDIT=0)")
        return None
    if not (os.environ.get("DART_API_KEYS") or os.environ.get("DART_API_KEY")):
        print(f"[monitor] {module.AUDIT_NAME}: DART_API_KEYS 없음. 신선도 감사 건너뜀")
        return None
    try:
        result = module.auditPanelFreshness(token=os.environ.get("HF_TOKEN") or None)
    except Exception as exc:  # noqa: BLE001 (감사 불능은 entry 로 드러내되 run 감시를 막지 않는다)
        return {
            "name": module.AUDIT_NAME,
            "state": "unknown",
            "conclusion": f"감사 실패: {type(exc).__name__}: {str(exc)[:120]}",
            "classification": "신선도 감사 불능",
            "url": FRESHNESS_URL,
            "runId": None,
            "samples": [],
        }
    return _freshnessEntry(result, auditName=module.AUDIT_NAME, describe=module.describe)


# 스케줄 누락(cron drop) 감지 — 최신 run 이 성공이어도 이 시간(h)보다 오래됐으면 stale(드랍된 cron)로 판정.
# GitHub Actions 스케줄은 best-effort 라 혼잡 시 run 기록 없이 건너뛴다 → 실패 0 인데 데이터가 안 들어오는
# 조용한 갭(2026-06-15 실측: 월요일 gov price·index cron 둘 다 미발화, 다른 워크플로는 정상 발화).
# **opt-in** — 여기 등록된 워크플로우만 staleness 검사(미등록=실패 감지만). 값 = 정상 최대 간격(주말 포함)+여유.
# 새 등록 시 그 cron 의 정상 최대 간격을 넘겨 잡아야 정상 주말 갭 오탐(false-positive)이 없다.
STALE_AFTER_HOURS: dict[str, float] = {
    # gov = 평일(1-5) 발행 + 토 derive. 정상 최대 간격 = 토 run(~22:10 KST) → 월 13:40 KST ≈ 39.5h. 42h=+2.5h 여유.
    # 월 cron 드랍 시 화 05:00 KST 감사에서 age ~55h>42h → stale 감지+자동 트리거. 월 05:00 정상치(~31h)는 미탐.
    "Gov Price Sync (Bulk)": 42,
    "Gov Index Sync (Bulk)": 42,
    # 검색 인덱스 = 매일 04:00 KST 증분(+ source sync workflow_run). 정상 최대 간격 ~24h.
    # 30h = +6h 여유. cron 드랍(성공기록만 남고 며칠 안 돎)을 staleness 로 감지. 실패(RED)는
    # MONITORED_WORKFLOWS 가 이미 잡지만, schedule 드랍은 이 임계 없이는 미탐(2026-06 하루 RED 교훈).
    "Search Index Build": 30,
    # Notify Watch = 평일(1-5) 17시 KST cron. 일일 감사(05시 KST) 기준 정상 최대 age = 일 감사에 금 run ~57h.
    # 80h = +여유(금~월 72h 주말 갭 초과) 라 정상 주말 오탐 없음. 3일+ 연속 cron drop(퍼블릭 IPO SSOT bake
    # 동결 + 신규상장 알림 정지)만 stale 감지·자동 트리거. 트리거는 nonce 멱등이라 오탐이어도 무해(중복알림 0).
    "Notify Watch": 80,
    # DART 수집 축(hf-dart-push 직렬 그룹). 2026-08 사고 전까지 미등록이라, 8 연속 실패로
    # 수집이 5 일 멈추는 동안 "실패했다"만 알려지고 "데이터가 멈췄다"는 아무도 보지 못했다.
    # 값 = 정상 최대 간격(주말·긴 실행 포함) + 여유. 실행 시작 시각(createdAt) 기준.
    "Original SSOT Sync": 60,  # 매일 02:00 UTC. 실행 자체가 길어 여유를 크게 둔다.
    "Data Sync": 30,  # 매일 06:00·18:00 UTC (12h 간격) + 실행 ~1.5h.
    "AllFilings Backfill": 42,  # 매일 05:30 UTC.
    "Data Prebuild (DART)": 42,  # Data Sync 완료 트리거 + 주간 full.
    "DART New Stocks Sync": 80,  # 평일(1-5) 01:00 UTC. 금->월 주말 갭 72h 초과분만 잡는다.
}

# 실패 원인 분류 시그니처 (gh run view 출력 = 잡 목록 + ANNOTATIONS, 소문자 매칭).
# job timeout 은 GitHub 이 "exceeded the maximum execution time" 으로 찍고, 그 직후 결과로
# "The operation was canceled." 가 따라온다. 위치 기반 분류는 뒤에 오는 결과 문구에 밀려
# 원인을 잃으므로 이 신호만 위치와 무관하게 우선한다 (2026-08 Data Sync 오판 교훈).
JOB_TIMEOUT = "job timeout (실행시간 초과)"

_SIG = {
    JOB_TIMEOUT: ("exceeded the maximum execution time",),
    "메모리/디스크 (runner)": ("lost communication", "out of memory", "killed", "no space left", "oom"),
    "timeout/cancelled": ("timed out", "timeout", "connecttimeout", "connect timeout", "cancel"),
    "HF directory file limit": ("too many files per directory", "can only contain up to 10000 files"),
    "HF rate-limit (429)": (
        "http 429",
        "status code: 429",
        "429 client error",
        "too many requests",
        "rate limit",
        "retry this action",
    ),
}


def _gh(args: list[str], *, check: bool = True) -> str:
    """gh CLI 실행 후 stdout 반환."""
    result = subprocess.run(["gh"] + args, capture_output=True, text=True, env={**os.environ})
    if check and result.returncode != 0:
        print(f"[monitor] gh 실행 실패: {' '.join(args)}")
        print(f"  stderr: {result.stderr}")
    return result.stdout.strip()


def _recentRuns(workflowName: str, n: int = RECENT_N) -> list[dict]:
    """워크플로우의 최근 n 건 실행 조회 (최신순)."""
    raw = _gh(
        [
            "run",
            "list",
            "--workflow",
            workflowName,
            "--limit",
            str(n),
            "--json",
            "conclusion,status,databaseId,url,createdAt,displayTitle",
        ],
        check=False,
    )
    if not raw:
        return []
    try:
        runs = json.loads(raw)
        return runs if isinstance(runs, list) else []
    except json.JSONDecodeError:
        return []


QUEUE_EVICTED = "concurrency 큐 축출 (미실행)"


def _runJobCount(runId: int) -> int | None:
    """run 이 실제로 띄운 job 수. 조회 실패는 None (판정 보류)."""
    raw = _gh(
        ["api", f"repos/{{owner}}/{{repo}}/actions/runs/{runId}/jobs", "--jq", ".total_count"],
        check=False,
    )
    try:
        return int(raw.strip())
    except (AttributeError, TypeError, ValueError):
        return None


def _isQueueEvicted(runId: int, conclusion: str) -> bool:
    """concurrency 큐에서 밀려나 job 을 하나도 시작하지 못한 run 인지.

    GitHub 은 concurrency group 당 pending 을 1 개만 유지한다. 새 트리거가 오면 기존 pending 은
    cancel-in-progress 설정과 무관하게 취소된다. 이때 run 은 cancelled 로 남지만 job 은 0 개다.
    파이프라인 코드 실패가 아니므로 원인 분류와 재실행 판단을 분리해야 한다 (2026-08 실측 8 건).
    """
    if conclusion != "cancelled":
        return False
    return _runJobCount(runId) == 0


def _classifyFailure(runId: int, conclusion: str = "") -> str:
    """실패 run 의 원인 분류 — gh run view 출력(잡+ANNOTATIONS)에서 시그니처 매칭.

    Args:
        runId: 실패한 run 의 databaseId.
        conclusion: run 의 conclusion. cancelled 면 큐 축출 여부를 먼저 가린다.

    Returns:
        분류 라벨 (메모리/디스크 · HF rate-limit · timeout · code/기타 · unknown).

    Raises:
        없음 — gh 실패/빈 출력은 'unknown' 으로 흡수.

    Example:
        >>> _classifyFailure(0)  # doctest: +SKIP
        'unknown'
    """
    if _isQueueEvicted(runId, conclusion):
        return QUEUE_EVICTED
    out = _gh(["run", "view", str(runId), "--log-failed"], check=False).lower()
    if not out:
        out = _gh(["run", "view", str(runId)], check=False).lower()
    if not out:
        return "unknown"
    return _classifyLog(out)


def _classifyLog(out: str) -> str:
    """실패 로그에서 가장 뒤에 나타난 구체 원인 시그니처를 고른다.

    단 job timeout 은 뒤따르는 취소 문구가 결과일 뿐이므로 위치와 무관하게 먼저 확정한다.
    """
    if any(signature in out for signature in _SIG[JOB_TIMEOUT]):
        return JOB_TIMEOUT
    matches = [
        (out.rfind(signature), label)
        for label, signatures in _SIG.items()
        for signature in signatures
        if signature in out
    ]
    if matches:
        return max(matches, key=lambda item: item[0])[1]
    return "code/기타"


def _classifyFailureWindow(runs: list[dict]) -> dict:
    """최근 연속 실패 전체를 분류해 최신 한 건이 이전 원인을 덮지 않게 한다."""
    history: list[dict] = []
    for run in runs:
        conclusion = run.get("conclusion")
        if conclusion in (*_OK_CONCLUSIONS, "", None):
            break
        runId = run.get("databaseId")
        cause = _classifyFailure(runId, conclusion or "") if runId else "unknown"
        history.append({"runId": runId, "url": run.get("url", "-"), "cause": cause})
    if not history:
        return {"classification": "unknown", "causeHistory": []}
    counts: dict[str, int] = {}
    for item in history:
        cause = item["cause"]
        counts[cause] = counts.get(cause, 0) + 1
    priority = {label: len(_SIG) - index for index, label in enumerate(_SIG)}
    priority.update({"code/기타": 1, "unknown": 0})
    dominant = max(counts, key=lambda label: (counts[label], priority.get(label, 0)))
    classification = f"{dominant} ({counts[dominant]}/{len(history)})" if len(history) > 1 else dominant
    return {"classification": classification, "causeHistory": history}


def _rerunFailed(runId: int) -> bool:
    """실패 run 의 실패 잡만 자동 재실행 (actions:write 필요). 성공 트리거 시 True."""
    result = subprocess.run(
        ["gh", "run", "rerun", str(runId), "--failed"],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    if result.returncode != 0:
        print(f"[monitor] rerun 실패 (run {runId}): {result.stderr.strip()}")
        return False
    return True


def _triggerWorkflow(name: str) -> bool:
    """stale(드랍된 cron) 워크플로우를 새로 트리거 (gh workflow run, actions:write). 성공 시 True.

    실패 run 재실행(_rerunFailed)과 달리 stale 은 run 기록 자체가 없어 fresh dispatch 가 필요하다.
    워크플로우에 workflow_dispatch 트리거가 있어야 한다(감시 대상 데이터 파이프라인은 모두 보유).
    """
    result = subprocess.run(
        ["gh", "workflow", "run", name],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    if result.returncode != 0:
        print(f"[monitor] workflow run 트리거 실패 ({name}): {result.stderr.strip()}")
        return False
    return True


def _ageHours(createdAt: str | None, now: datetime) -> float | None:
    """ISO8601 createdAt → 경과 시간(h). 없음·파싱 실패면 None(=staleness 검사 스킵)."""
    if not createdAt:
        return None
    try:
        ts = datetime.fromisoformat(createdAt.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (now - ts).total_seconds() / 3600


def _triage(runs: list[dict], *, maxGapHours: float | None = None, now: datetime | None = None) -> dict:
    """최근 실행 목록 → 상태 판정 (부작용 없는 순수 함수, 테스트 대상).

    Args:
        runs: ``_recentRuns`` 결과 (최신순). 빈 목록 허용.
        maxGapHours: 설정 시 최신 성공 run 이 이보다 오래되면 stale(드랍된 cron) 판정. None=검사 안 함(opt-in).
        now: staleness 기준 시각(테스트 주입용). None=현재 UTC.

    Returns:
        ``{"state": ..., "conclusion": ..., "url": ..., "runId": ...}`` —
        state ∈ no_runs / running / ok / stale(성공이나 cron 누락) / transient(첫 실패) / persistent(연속 2회+).

    Raises:
        없음.

    Example:
        >>> _triage([])["state"]
        'no_runs'
    """
    if not runs:
        return {"state": "no_runs", "conclusion": "-", "url": "-", "runId": None}

    nowTs = now or datetime.now(timezone.utc)
    # 최신 run 의 결론과 무관하게 "마지막 성공 이후 경과"를 항상 계산한다.
    # 옛 판정은 최신이 성공일 때만 staleness 를 봐서, 연속 실패 중에는 데이터가 며칠 멈춰도
    # 실패 라벨만 붙고 정지 사실이 드러나지 않았다 (2026-08 실측: DART 수집 5 일 정지 미탐).
    lastSuccessAge: float | None = None
    for run in runs:
        if run.get("conclusion") == "success":
            lastSuccessAge = _ageHours(run.get("createdAt"), nowTs)
            break

    latest = runs[0]
    conclusion = latest.get("conclusion") or ""
    status = latest.get("status") or ""
    url = latest.get("url", "-")
    runId = latest.get("databaseId")

    if status == "in_progress" or conclusion == "":
        return {"state": "running", "conclusion": status or "in_progress", "url": url, "runId": runId}
    if conclusion in _OK_CONCLUSIONS:
        # 최신이 성공이어도 cron cadence 보다 오래됐으면 stale(GitHub 가 스케줄 run 을 기록없이 드랍).
        if maxGapHours is not None:
            age = _ageHours(latest.get("createdAt"), nowTs)
            if age is not None and age > maxGapHours:
                return {"state": "stale", "conclusion": f"{conclusion} · {age:.0f}h 경과", "url": url, "runId": runId}
            # skipped 만 이어지는 경우: run 은 최신이어도 실제 성공은 오래됐을 수 있다.
            if lastSuccessAge is not None and lastSuccessAge > maxGapHours:
                return {
                    "state": "stale",
                    "conclusion": f"{conclusion} · 마지막 성공 {lastSuccessAge:.0f}h 전",
                    "url": url,
                    "runId": runId,
                    "lastSuccessAgeHours": lastSuccessAge,
                }
        return {"state": "ok", "conclusion": conclusion, "url": url, "runId": runId}

    # 최신 실패. 직전 실행도 실패면 persistent, 아니면 첫 실패(transient).
    prevConclusion = runs[1].get("conclusion") if len(runs) > 1 else "success"
    prevFailed = prevConclusion not in (*_OK_CONCLUSIONS, "", None)
    state = "persistent" if prevFailed else "transient"
    result = {
        "state": state,
        "conclusion": conclusion,
        "url": url,
        "runId": runId,
        "lastSuccessAgeHours": lastSuccessAge,
    }
    # 실패가 이어지는 동안 데이터가 실제로 멈춰 있는지를 별도 신호로 남긴다.
    if maxGapHours is not None and (lastSuccessAge is None or lastSuccessAge > maxGapHours):
        result["dataStalled"] = True
    return result


def _ensureLabel() -> None:
    """pipeline-failure 라벨이 없으면 생성."""
    existing = _gh(["label", "list", "--search", FAILURE_LABEL, "--json", "name"], check=False)
    if FAILURE_LABEL not in existing:
        _gh(
            ["label", "create", FAILURE_LABEL, "--color", "d73a4a", "--description", "데이터 파이프라인 자동 실패 알림"]
        )


def _findOpenIssue() -> int | None:
    """pipeline-failure 라벨의 열린 Issue 번호."""
    raw = _gh(
        ["issue", "list", "--label", FAILURE_LABEL, "--state", "open", "--json", "number", "--limit", "1"], check=False
    )
    if not raw:
        return None
    try:
        issues = json.loads(raw)
        return issues[0]["number"] if issues else None
    except (json.JSONDecodeError, IndexError):
        return None


def _updateIssue(number: int, title: str, body: str) -> None:
    """열린 이슈의 제목과 본문을 함께 갱신해 오래된 원인이 남지 않게 한다."""
    _gh(["issue", "edit", str(number), "--title", title, "--body", body])


def _issueTitle(persistent: list[dict], retried: list[dict], stale: list[dict] | None = None) -> str:
    """실패 Issue 제목 — 연속 실패가 있으면 'Pipeline failure', 단발·누락뿐이면 '(자동 재실행 중)' 표기.

    Args:
        persistent: 연속 2회+ 실패 entry list.
        retried: 단발 실패(자동 재실행) entry list.
        stale: 스케줄 누락(cron drop, 자동 트리거) entry list.

    Returns:
        100자 이내 Issue 제목. 워크플로우가 많아 길면 개수 요약으로 축약.

    Raises:
        없음.

    Example:
        >>> _issueTitle([{"name": "Original SSOT Sync"}], [])
        'Pipeline failure: Original SSOT Sync'
        >>> _issueTitle([], [{"name": "Macro Data Sync (Bulk)"}])
        'Pipeline failure (자동 재실행 중): Macro Data Sync (Bulk)'
        >>> _issueTitle([], [], [{"name": "Gov Price Sync (Bulk)"}])
        'Pipeline failure (자동 재실행 중): Gov Price Sync (Bulk)'
    """
    stale = stale or []
    names = ", ".join(f["name"] for f in (persistent + retried + stale))
    prefix = "Pipeline failure" if persistent else "Pipeline failure (자동 재실행 중)"
    title = f"{prefix}: {names}"
    if len(title) > 100:
        title = f"{prefix}: {len(persistent) + len(retried) + len(stale)}개 워크플로우"
    return title


def main():
    print(f"[monitor] {len(MONITORED_WORKFLOWS)}개 워크플로우 상태 확인")

    statuses: list[dict] = []
    persistent: list[dict] = []  # 연속 2회+ 실패 → Issue 알림
    retried: list[dict] = []  # 첫 실패 → 자동 rerun, 알림 보류
    stale: list[dict] = []  # 스케줄 누락(cron drop) → 자동 트리거 + 알림

    for name in MONITORED_WORKFLOWS:
        runs = _recentRuns(name)
        triage = _triage(runs, maxGapHours=STALE_AFTER_HOURS.get(name))
        entry = {"name": name, **triage}

        if triage["state"] in ("persistent", "transient"):
            entry.update(_classifyFailureWindow(runs))

        if triage["state"] == "persistent":
            persistent.append(entry)
            icon = "FAIL×N"
        elif triage["state"] == "transient":
            # 큐 축출은 파이프라인 실패가 아니고 실패 job 도 없다. rerun 은 항상 실패하므로
            # 시도하지 않고, 데이터가 실제로 밀리면 staleness 축이 재트리거를 맡는다.
            evicted = str(entry.get("classification", "")).startswith(QUEUE_EVICTED)
            entry["evicted"] = evicted
            entry["reran"] = False if evicted else (_rerunFailed(triage["runId"]) if triage["runId"] else False)
            retried.append(entry)
            icon = "queue-evict" if evicted else ("retry" if entry["reran"] else "FAIL×1")
        elif triage["state"] == "stale":
            entry["triggered"] = _triggerWorkflow(name)  # run 기록 부재 → fresh dispatch (rerun 불가)
            stale.append(entry)
            icon = "stale→trig" if entry["triggered"] else "STALE"
        elif triage["state"] == "running":
            icon = "running"
        elif triage["state"] == "ok":
            icon = "pass"
        else:
            icon = "no_runs"

        statuses.append(entry)
        print(
            f"  [{icon}] {name}: {entry['conclusion']}"
            + (f" — {entry.get('classification', '')}" if entry.get("classification") else "")
        )

    freshness = _auditFreshness()
    if freshness is not None:
        statuses.append(freshness)
        if freshness["state"] == "persistent":
            persistent.append(freshness)
        icon = {"persistent": "FAIL", "ok": "pass"}.get(freshness["state"], "unknown")
        print(f"  [{icon}] {freshness['name']}: {freshness['conclusion']}")

    _ensureLabel()
    openIssue = _findOpenIssue()

    failing = persistent + retried + stale  # 실패(단발·연속)+스케줄 누락 모두 알린다(가시성 우선 — 조용한 갭 0)
    if failing:
        body = _buildIssueBody(statuses, persistent, retried, stale)
        title = _issueTitle(persistent, retried, stale)
        if openIssue:
            _updateIssue(openIssue, title, body)
            print(
                f"[monitor] 기존 Issue #{openIssue} 갱신 (연속 {len(persistent)} · 단발 {len(retried)} · 누락 {len(stale)})"
            )
        else:
            out = _gh(["issue", "create", "--title", title, "--body", body, "--label", FAILURE_LABEL])
            print(f"[monitor] Issue 생성 (연속 {len(persistent)} · 단발 {len(retried)} · 누락 {len(stale)}): {out}")
    elif openIssue:
        _gh(["issue", "close", str(openIssue), "--comment", "모든 파이프라인 정상 복구 — 자동 닫기."])
        print(f"[monitor] Issue #{openIssue} 자동 닫기 (실패 0)")
    else:
        print("[monitor] 전부 정상, 열린 Issue 없음")

    _writeSummary(statuses, persistent, retried, stale)


def _buildIssueBody(
    statuses: list[dict], persistent: list[dict], retried: list[dict], stale: list[dict] | None = None
) -> str:
    """Issue 본문 생성 — 연속 실패 + 스케줄 누락 + 원인 분류 + 자동 재실행/트리거 현황."""
    stale = stale or []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## Pipeline Monitor Report ({now})\n",
        "| 워크플로우 | 상태 | 원인 | 링크 |",
        "|-----------|------|------|------|",
    ]
    for s in statuses:
        icon = {
            "ok": ":white_check_mark:",
            "running": ":hourglass:",
            "persistent": ":x:",
            "transient": ":warning:",
            "stale": ":fast_forward:",
        }.get(s["state"], ":grey_question:")
        cls = s.get("classification", "-")
        lines.append(f"| {s['name']} | {icon} {s['conclusion']} | {cls} | [보기]({s['url']}) |")

    lines.append("\n### 연속 실패 (조치 필요)")
    for f in persistent:
        lines.append(
            f"- **{f['name']}**: `{f['conclusion']}` · 원인: **{f.get('classification', 'unknown')}**"
            + (
                f" · **데이터 정지: 마지막 성공 {f['lastSuccessAgeHours']:.0f}h 전**"
                if f.get("dataStalled") and f.get("lastSuccessAgeHours") is not None
                else (" · **데이터 정지: 최근 실행 기록에 성공 없음**" if f.get("dataStalled") else "")
            )
            + f" · [로그]({f['url']})"
        )

    if stale:
        lines.append("\n### 스케줄 누락 (cron drop — 자동 트리거)")
        for s in stale:
            mark = "트리거됨" if s.get("triggered") else "트리거 실패"
            lines.append(
                f"- {s['name']}: `{s['conclusion']}` ({mark}) — GitHub 가 스케줄 run 을 드랍 — [최근]({s['url']})"
            )

    if retried:
        lines.append("\n### 단발 실패 — 자동 재실행 중 (알림 보류)")
        for r in retried:
            mark = "재실행됨" if r.get("reran") else "재실행 실패"
            lines.append(f"- {r['name']}: {r.get('classification', '-')} ({mark}) — [로그]({r['url']})")

    for f in persistent:
        if f.get("samples"):
            lines.append(f"\n### 데이터 신선도 누락 표본 ({f['name']}, 오래된 순 최대 20건)")
            for code, rceptNo, rceptDt, reportNm in f["samples"]:
                lines.append(f"- {code} `{rceptNo}` {rceptDt} {reportNm}")

    histories = [item for status in (persistent + retried) for item in status.get("causeHistory", [])]
    if histories:
        lines.append("\n### 최근 연속 실패 원인 이력")
        for item in histories:
            lines.append(
                f"- run `{item.get('runId')}`: **{item.get('cause', 'unknown')}** — [실패 로그]({item.get('url', '-')})"
            )

    lines.append(
        f"\n> 자동 생성 by Pipeline Monitor ({now}). 모든 실패 알림 — 단발은 자동 재실행, 스케줄 누락(cron drop)은 "
        "자동 트리거 병행(자가치유), 연속 2회+ 는 조치 필요. 복구되면 자동 닫힘."
    )
    return "\n".join(lines)


def _writeSummary(
    statuses: list[dict], persistent: list[dict], retried: list[dict], stale: list[dict] | None = None
) -> None:
    """GitHub Actions step summary."""
    stale = stale or []
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summaryPath:
        return

    with open(summaryPath, "a", encoding="utf-8") as f:
        f.write("## Pipeline Health\n\n")
        f.write("| 워크플로우 | 상태 | 원인 |\n|-----------|------|------|\n")
        for s in statuses:
            icon = {"ok": ":white_check_mark:", "persistent": ":x:", "stale": ":fast_forward:"}.get(
                s["state"], ":warning:"
            )
            f.write(f"| {s['name']} | {icon} {s['conclusion']} | {s.get('classification', '-')} |\n")

        if persistent:
            f.write(f"\n**{len(persistent)}개 연속 실패** → Issue 생성/갱신됨\n")
        elif stale:
            f.write(f"\n**{len(stale)}개 스케줄 누락(cron drop)** → 자동 트리거\n")
        elif retried:
            f.write(f"\n**{len(retried)}개 단발 실패** → 자동 재실행 (알림 보류)\n")
        else:
            f.write("\n**전체 정상**\n")


if __name__ == "__main__":
    main()
