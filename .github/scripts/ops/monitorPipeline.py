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

import json
import os
import subprocess
from datetime import datetime, timezone

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
}

# 실패 원인 분류 시그니처 (gh run view 출력 = 잡 목록 + ANNOTATIONS, 소문자 매칭).
_SIG = {
    "메모리/디스크 (runner)": ("lost communication", "out of memory", "killed", "no space left", "oom"),
    "timeout/cancelled": ("timed out", "timeout", "connecttimeout", "connect timeout", "cancel"),
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


def _classifyFailure(runId: int) -> str:
    """실패 run 의 원인 분류 — gh run view 출력(잡+ANNOTATIONS)에서 시그니처 매칭.

    Args:
        runId: 실패한 run 의 databaseId.

    Returns:
        분류 라벨 (메모리/디스크 · HF rate-limit · timeout · code/기타 · unknown).

    Raises:
        없음 — gh 실패/빈 출력은 'unknown' 으로 흡수.

    Example:
        >>> _classifyFailure(0)  # doctest: +SKIP
        'unknown'
    """
    out = _gh(["run", "view", str(runId), "--log-failed"], check=False).lower()
    if not out:
        out = _gh(["run", "view", str(runId)], check=False).lower()
    if not out:
        return "unknown"
    return _classifyLog(out)


def _classifyLog(out: str) -> str:
    """실패 로그에서 가장 뒤에 나타난 구체 원인 시그니처를 고른다."""
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
        cause = _classifyFailure(runId) if runId else "unknown"
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

    latest = runs[0]
    conclusion = latest.get("conclusion") or ""
    status = latest.get("status") or ""
    url = latest.get("url", "-")
    runId = latest.get("databaseId")

    if status == "in_progress" or conclusion == "":
        return {"state": "running", "conclusion": status or "in_progress", "url": url, "runId": runId}
    if conclusion in _OK_CONCLUSIONS:
        # 최신이 성공이어도 cron cadence 보다 오래됐으면 stale(GitHub 가 스케줄 run 을 기록없이 드랍 — 조용한 갭).
        if maxGapHours is not None:
            age = _ageHours(latest.get("createdAt"), now or datetime.now(timezone.utc))
            if age is not None and age > maxGapHours:
                return {"state": "stale", "conclusion": f"{conclusion} · {age:.0f}h 경과", "url": url, "runId": runId}
        return {"state": "ok", "conclusion": conclusion, "url": url, "runId": runId}

    # 최신 실패 — 직전 실행도 실패면 persistent, 아니면 첫 실패(transient).
    prevConclusion = runs[1].get("conclusion") if len(runs) > 1 else "success"
    prevFailed = prevConclusion not in (*_OK_CONCLUSIONS, "", None)
    state = "persistent" if prevFailed else "transient"
    return {"state": state, "conclusion": conclusion, "url": url, "runId": runId}


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
            entry["reran"] = _rerunFailed(triage["runId"]) if triage["runId"] else False
            retried.append(entry)
            icon = "retry" if entry["reran"] else "FAIL×1"
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
            f"- **{f['name']}**: `{f['conclusion']}` — 원인: **{f.get('classification', 'unknown')}** — [로그]({f['url']})"
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
