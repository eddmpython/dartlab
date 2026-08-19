"""파이프라인 모니터 triage/분류/알림 단위 테스트.

``_triage`` 가 연속 2회+ 실패를 persistent(조치 필요), 첫 실패를 transient(자동 재실행)로
구분 판정하는지 + ``_classifyFailure`` 시그니처 분류 + ``_issueTitle`` 제목 + 모든 scheduled
파이프라인이 MONITORED_WORKFLOWS 에 등록됐는지(미등록=조용한 실패 가드) 검증한다.
정책: 단발이든 연속이든 **모든 실패를 알린다**(단발은 auto-rerun 병행, 가시성 우선).
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _loadMonitor():
    path = ROOT / ".github" / "scripts" / "ops" / "monitorPipeline.py"
    spec = importlib.util.spec_from_file_location("monitorPipeline", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── _triage (순수 로직) ──────────────────────────────────────────────


def test_triage_no_runs():
    mod = _loadMonitor()
    assert mod._triage([])["state"] == "no_runs"


def test_triage_running_skips():
    mod = _loadMonitor()
    runs = [{"conclusion": None, "status": "in_progress", "databaseId": 1, "url": "u"}]
    assert mod._triage(runs)["state"] == "running"


def test_triage_ok():
    mod = _loadMonitor()
    runs = [{"conclusion": "success", "status": "completed", "databaseId": 1, "url": "u"}]
    assert mod._triage(runs)["state"] == "ok"


def test_triage_transient_first_failure():
    """최신 실패 + 직전 성공 = transient (자동 재실행 + 알림 — 단발도 surface)."""
    mod = _loadMonitor()
    runs = [
        {"conclusion": "failure", "status": "completed", "databaseId": 2, "url": "u2"},
        {"conclusion": "success", "status": "completed", "databaseId": 1, "url": "u1"},
    ]
    t = mod._triage(runs)
    assert t["state"] == "transient"
    assert t["runId"] == 2


def test_triage_persistent_two_consecutive():
    """최신+직전 모두 실패 = persistent (Issue 알림 대상)."""
    mod = _loadMonitor()
    runs = [
        {"conclusion": "failure", "status": "completed", "databaseId": 3, "url": "u3"},
        {"conclusion": "failure", "status": "completed", "databaseId": 2, "url": "u2"},
    ]
    assert mod._triage(runs)["state"] == "persistent"


def test_triage_single_run_failure_is_transient():
    """이력 1건뿐(직전 없음)인 첫 실패는 transient (직전을 success 로 간주)."""
    mod = _loadMonitor()
    runs = [{"conclusion": "failure", "status": "completed", "databaseId": 5, "url": "u"}]
    assert mod._triage(runs)["state"] == "transient"


# ─── staleness (cron drop — opt-in cadence 감지) ──────────────────────

_NOW = datetime(2026, 6, 16, 5, 0, tzinfo=timezone.utc)  # 화 05:00 KST 감사 시점 가정


def test_triage_stale_when_latest_success_too_old():
    """최신이 success 라도 maxGapHours 초과(GitHub cron drop)면 stale → 자동 트리거 대상."""
    mod = _loadMonitor()
    runs = [
        {
            "conclusion": "success",
            "status": "completed",
            "databaseId": 9,
            "url": "u",
            "createdAt": "2026-06-13T15:06:27Z",
        }
    ]
    # 6/13 15:06 → 6/16 05:00 ≈ 61.9h > 42
    assert mod._triage(runs, maxGapHours=42, now=_NOW)["state"] == "stale"


def test_triage_fresh_success_not_stale():
    """최신 success 가 임계 이내면 ok — 정상 주말 갭 오탐 없음."""
    mod = _loadMonitor()
    runs = [
        {
            "conclusion": "success",
            "status": "completed",
            "databaseId": 9,
            "url": "u",
            "createdAt": "2026-06-16T00:00:00Z",
        }
    ]
    assert mod._triage(runs, maxGapHours=42, now=_NOW)["state"] == "ok"  # 5h 경과


def test_triage_opt_in_no_maxgap_never_stale():
    """maxGapHours 미지정(opt-in 아님)이면 아무리 오래돼도 ok — 기존 동작 보존."""
    mod = _loadMonitor()
    runs = [
        {
            "conclusion": "success",
            "status": "completed",
            "databaseId": 9,
            "url": "u",
            "createdAt": "2020-01-01T00:00:00Z",
        }
    ]
    assert mod._triage(runs, now=_NOW)["state"] == "ok"


def test_stale_after_hours_covers_gov():
    """gov price·index 가 staleness opt-in 에 등록 (2026-06-15 월요일 cron drop 갭 가드)."""
    mod = _loadMonitor()
    assert "Gov Price Sync (Bulk)" in mod.STALE_AFTER_HOURS
    assert "Gov Index Sync (Bulk)" in mod.STALE_AFTER_HOURS


def test_stale_after_hours_covers_notify_watch():
    """Notify Watch(퍼블릭 IPO SSOT bake + 신규상장 알림)도 cron drop staleness opt-in.

    3일+ 연속 스케줄 누락 시 퍼블릭 reports.parquet 동결·알림 정지가 초록불 뒤에 숨는 것을 방지.
    임계는 금~월 72h 주말 갭을 넘겨(오탐 방지) 잡는다.
    """
    mod = _loadMonitor()
    assert "Notify Watch" in mod.STALE_AFTER_HOURS
    assert mod.STALE_AFTER_HOURS["Notify Watch"] > 72


# ─── _classifyFailure (시그니처 매칭) ─────────────────────────────────


@pytest.mark.parametrize(
    "logText,expected",
    [
        ("The hosted runner lost communication with the server", "메모리/디스크 (runner)"),
        ("HTTP 429 Too Many Requests — retry this action in 5 minutes", "HF rate-limit (429)"),
        ("Your push was rejected because it contains too many files per directory", "HF directory file limit"),
        ("The job running on runner timed out after 120 minutes", "timeout/cancelled"),
        ("Traceback: ValueError in buildScan", "code/기타"),
        ("", "unknown"),
    ],
)
def test_classifyFailure(monkeypatch, logText, expected):
    mod = _loadMonitor()
    monkeypatch.setattr(mod, "_gh", lambda *a, **k: logText)
    assert mod._classifyFailure(123) == expected


def test_classify_failure_reads_failed_log_before_summary(monkeypatch):
    mod = _loadMonitor()
    calls: list[list[str]] = []

    def gh(args, **_kwargs):
        calls.append(args)
        return "timed out" if "--log-failed" in args else ""

    monkeypatch.setattr(mod, "_gh", gh)
    assert mod._classifyFailure(123) == "timeout/cancelled"
    assert calls == [["run", "view", "123", "--log-failed"]]


def test_classify_timeout_wins_over_unrelated_429(monkeypatch):
    mod = _loadMonitor()
    logText = "dependency build 429 records\nTraceback\nhttpx.ConnectTimeout: connection timed out"
    monkeypatch.setattr(mod, "_gh", lambda *a, **k: logText)
    assert mod._classifyFailure(123) == "timeout/cancelled"


def test_classify_uses_last_specific_failure_signal(monkeypatch):
    mod = _loadMonitor()
    logText = "earlier timeout while installing\nHfHubHTTPError: 429 Client Error"
    monkeypatch.setattr(mod, "_gh", lambda *a, **k: logText)
    assert mod._classifyFailure(123) == "HF rate-limit (429)"


def test_classify_failure_window_preserves_consecutive_causes(monkeypatch):
    mod = _loadMonitor()
    causes = {3: "메모리/디스크 (runner)", 2: "timeout/cancelled"}
    monkeypatch.setattr(mod, "_classifyFailure", lambda runId, conclusion="": causes[runId])
    result = mod._classifyFailureWindow(
        [
            {"conclusion": "failure", "databaseId": 3, "url": "u3"},
            {"conclusion": "failure", "databaseId": 2, "url": "u2"},
            {"conclusion": "success", "databaseId": 1, "url": "u1"},
        ]
    )
    assert result["classification"].startswith("메모리/디스크")
    assert [item["runId"] for item in result["causeHistory"]] == [3, 2]


def test_update_issue_refreshes_title_and_body(monkeypatch):
    mod = _loadMonitor()
    calls: list[list[str]] = []
    monkeypatch.setattr(mod, "_gh", lambda args, **_kwargs: calls.append(args) or "")
    mod._updateIssue(82, "새 원인", "새 본문")
    assert calls == [["issue", "edit", "82", "--title", "새 원인", "--body", "새 본문"]]


# ─── _issueTitle (연속 vs 단발 표기) ──────────────────────────────────


def test_issue_title_persistent():
    """연속 실패 있으면 'Pipeline failure: …' (조치 필요 톤)."""
    mod = _loadMonitor()
    title = mod._issueTitle([{"name": "Original SSOT Sync"}], [])
    assert title == "Pipeline failure: Original SSOT Sync"


def test_issue_title_transient_only():
    """단발 실패뿐이면 '(자동 재실행 중)' 표기 — 알림은 하되 심각도 구분."""
    mod = _loadMonitor()
    title = mod._issueTitle([], [{"name": "Macro Data Sync (Bulk)"}])
    assert title.startswith("Pipeline failure (자동 재실행 중):")
    assert "Macro Data Sync (Bulk)" in title


def test_issue_title_truncates_when_many():
    """워크플로우가 많아 100자 초과면 개수 요약으로 축약."""
    mod = _loadMonitor()
    many = [{"name": f"Very Long Workflow Name Number {i}"} for i in range(10)]
    title = mod._issueTitle(many, [])
    assert len(title) <= 100
    assert "10개 워크플로우" in title


# ─── MONITORED_WORKFLOWS 커버리지 (미등록 = 조용한 실패 가드) ──────────


def test_monitored_covers_core_scheduled_pipelines():
    """핵심 scheduled 파이프라인이 모두 감시목록에 — 특히 Original SSOT Sync(과거 미등록=조용한 실패)."""
    mod = _loadMonitor()
    required = {
        "Original SSOT Sync",
        "AllFilings Backfill",
        "Data Sync",
        "EDGAR Data Sync (Bulk)",
        "Gov Price Sync (Bulk)",
        "Gov Index Sync (Bulk)",
        "Macro Data Sync (Bulk)",
        "News Archive Sync",
        "GDELT Sync",
        "Valuation Snapshot",
        "Search Index Build",
        "Quant Audit",
        "Update KindList",
    }
    missing = required - set(mod.MONITORED_WORKFLOWS)
    assert not missing, f"감시목록 누락(조용한 실패 위험): {missing}"


def test_data_audit_rechecks_after_monitored_workflow_completion():
    """복구 재실행이 끝나면 다음 날까지 기다리지 않고 이슈를 즉시 다시 판정한다."""
    workflow = (ROOT / ".github" / "workflows" / "dataAudit.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in workflow
    assert "types: [completed]" in workflow
    for name in ("EDGAR Data Sync (Bulk)", "Gov Price Sync (Bulk)", "Macro Data Sync (Bulk)"):
        assert f"- {name}" in workflow


# ─── concurrency 큐 축출 + 데이터 정지 (2026-08 사고 회귀 가드) ───────────


def test_queue_evicted_run_is_classified_separately(monkeypatch):
    """job 0 개인 cancelled 는 timeout 이 아니라 큐 축출로 분류한다."""
    mod = _loadMonitor()
    calls: list[list[str]] = []

    def fakeGh(args, **_kwargs):
        calls.append(args)
        if args[0] == "api":
            return "0"
        return "The operation was canceled."

    monkeypatch.setattr(mod, "_gh", fakeGh)
    assert mod._classifyFailure(123, "cancelled") == mod.QUEUE_EVICTED
    # 축출 판정이 먼저 끝나 로그 조회까지 가지 않는다.
    assert all(args[0] == "api" for args in calls)


def test_run_with_jobs_is_not_queue_evicted(monkeypatch):
    """job 이 실제로 돈 cancelled 는 축출이 아니라 기존 시그니처 분류를 따른다."""
    mod = _loadMonitor()

    def fakeGh(args, **_kwargs):
        if args[0] == "api":
            return "2"
        # 실제 GitHub 출력 순서: 원인(초과) 다음에 결과(취소)가 찍힌다.
        return "The job has exceeded the maximum execution time of 1h30m0s" + chr(10) + "The operation was canceled."

    monkeypatch.setattr(mod, "_gh", fakeGh)
    assert mod._classifyFailure(123, "cancelled") == mod.JOB_TIMEOUT


def test_job_count_unavailable_does_not_claim_eviction(monkeypatch):
    """job 수 조회가 실패하면 축출로 단정하지 않는다."""
    mod = _loadMonitor()
    monkeypatch.setattr(mod, "_gh", lambda args, **_kwargs: "" if args[0] == "api" else "timed out")
    assert mod._isQueueEvicted(123, "cancelled") is False


def test_persistent_failure_reports_data_stall():
    """연속 실패 중에도 마지막 성공 이후 경과로 데이터 정지를 표면화한다."""
    mod = _loadMonitor()
    now = datetime(2026, 8, 19, 5, 0, tzinfo=timezone.utc)
    runs = [
        {"conclusion": "cancelled", "databaseId": 5, "url": "u5", "createdAt": "2026-08-18T18:47:27Z"},
        {"conclusion": "cancelled", "databaseId": 4, "url": "u4", "createdAt": "2026-08-18T06:49:17Z"},
        {"conclusion": "success", "databaseId": 1, "url": "u1", "createdAt": "2026-08-14T19:02:29Z"},
    ]
    result = mod._triage(runs, maxGapHours=30, now=now)
    assert result["state"] == "persistent"
    assert result["dataStalled"] is True
    assert result["lastSuccessAgeHours"] > 100


def test_recent_success_during_transient_failure_is_not_stalled():
    """직전에 성공이 있으면 단발 실패를 데이터 정지로 부풀리지 않는다."""
    mod = _loadMonitor()
    now = datetime(2026, 8, 19, 5, 0, tzinfo=timezone.utc)
    runs = [
        {"conclusion": "failure", "databaseId": 5, "url": "u5", "createdAt": "2026-08-19T04:00:00Z"},
        {"conclusion": "success", "databaseId": 4, "url": "u4", "createdAt": "2026-08-19T00:00:00Z"},
    ]
    result = mod._triage(runs, maxGapHours=30, now=now)
    assert result["state"] == "transient"
    assert "dataStalled" not in result


def test_stale_after_hours_covers_dart_collection_axis():
    """DART 수집 축이 staleness 감시에 등록돼 있다 (미등록 = 정지 미탐)."""
    mod = _loadMonitor()
    required = {
        "Original SSOT Sync",
        "Data Sync",
        "AllFilings Backfill",
        "Data Prebuild (DART)",
        "DART New Stocks Sync",
    }
    missing = required - set(mod.STALE_AFTER_HOURS)
    assert missing == set(), f"staleness 미등록: {sorted(missing)}"


def test_only_skipped_runs_since_last_success_is_stale():
    """skipped 만 이어져도 마지막 성공이 오래됐으면 stale 로 잡는다."""
    mod = _loadMonitor()
    now = datetime(2026, 8, 19, 5, 0, tzinfo=timezone.utc)
    runs = [
        {"conclusion": "skipped", "databaseId": 9, "url": "u9", "createdAt": "2026-08-19T04:00:00Z"},
        {"conclusion": "skipped", "databaseId": 8, "url": "u8", "createdAt": "2026-08-18T20:18:00Z"},
        {"conclusion": "success", "databaseId": 1, "url": "u1", "createdAt": "2026-08-14T20:16:14Z"},
    ]
    result = mod._triage(runs, maxGapHours=42, now=now)
    assert result["state"] == "stale"
    assert "마지막 성공" in result["conclusion"]
