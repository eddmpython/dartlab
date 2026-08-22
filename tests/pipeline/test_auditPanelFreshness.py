"""DART panel 신선도 감사(auditPanelFreshness) + 모니터 합류 단위 테스트. 네트워크 0(stub).

2026-08 사고 재발 방지 가드: 수집 run 이 전부 초록이어도 HF panel 에 최신 정기보고서가 없으면
감사가 breach 를 내고 모니터가 persistent(조치 필요) entry 로 Issue 에 올리는지 확인한다.
"""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    path = ROOT / ".github" / "scripts" / "ops" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_judge_threshold_is_max_of_floor_and_ratio():
    mod = _load("auditPanelFreshness")
    assert mod.judge(0, 0) is False
    assert mod.judge(100, 20) is False  # 절대 하한(20) 이하
    assert mod.judge(100, 21) is True  # 하한 초과(비율 2% = 2 보다 큰 쪽이 하한)
    assert mod.judge(2900, 58) is False  # ceil(2%) = 58 이하
    assert mod.judge(2900, 59) is True
    assert mod.judge(2789, 2591) is True  # 사고 당시 실측 비율


def _wire(monkeypatch, *, filings: list[tuple[str, str, str, str]], panelHave: dict[str, set[str] | None]):
    """listFilings·DartClient·_panelRceptsFromHf 를 stub 으로 막는다."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import panelRceptReconcile

    monkeypatch.setattr("dartlab.gather.dart.client.DartClient", lambda *a, **k: object())

    def _listFilings(client, corp=None, start=None, end=None, **kw):
        return pl.DataFrame(
            {
                "stock_code": [f[0] for f in filings],
                "rcept_no": [f[1] for f in filings],
                "rcept_dt": [f[2] for f in filings],
                "report_nm": [f[3] for f in filings],
            }
        )

    monkeypatch.setattr(disclosure, "listFilings", _listFilings)
    monkeypatch.setattr(
        panelRceptReconcile, "_panelRceptsFromHf", lambda repo, relDir, code, *, token=None: panelHave.get(code)
    )


def test_audit_counts_missing_after_grace_and_ignores_fresh_and_unknown(monkeypatch):
    mod = _load("auditPanelFreshness")
    today = date(2026, 8, 22)
    _wire(
        monkeypatch,
        filings=[
            ("000A", "20260814000001", "20260814", "반기보고서 (2026.06)"),  # panel 보유
            ("000B", "20260814000002", "20260814", "반기보고서 (2026.06)"),  # panel 누락
            ("000C", "20260814000003", "20260814", "반기보고서 (2026.06)"),  # panel 미존재(404 = 빈 set) -> 누락
            ("000D", "20260821000004", "20260821", "반기보고서 (2026.06)"),  # grace(3일) 안 -> 제외
            ("000E", "20260814000005", "20260814", "반기보고서 (2026.06)"),  # 조회 일시 실패(None) -> 모수 제외
            ("000F", "20260814000006", "20260814", "주요사항보고서"),  # 비정기 -> 제외
            (
                "000A",
                "20260815000008",
                "20260815",
                "[첨부정정]반기보고서 (2026.06)",
            ),  # 첨부만 정정(본문 zip 없음) -> 제외
            ("000B", "20260815000009", "20260815", "[첨부추가]반기보고서 (2026.06)"),  # 첨부 추가 -> 제외
            ("", "20260814000007", "20260814", "반기보고서 (2026.06)"),  # 종목코드 없음 -> 제외
        ],
        panelHave={"000A": {"20260814000001"}, "000B": {"20250514000099"}, "000C": set(), "000E": None},
    )

    result = mod.auditPanelFreshness(today=today)

    assert result["expected"] == 3  # A, B, C
    assert result["missing"] == 2  # B, C
    assert result["unknownCompanies"] == 1  # E
    assert result["companies"] == 4  # A, B, C, E (D 는 grace 로 빠짐)
    assert [s[0] for s in result["samples"]] == ["000B", "000C"]
    assert result["breach"] is False  # 2 건은 하한(20) 이하
    assert result["window"] == "20260724~20260819"


def test_audit_breach_when_panel_stalls_for_many_companies(monkeypatch):
    """사고 재현: 수백 종목의 정기 rcept 가 panel 에 없으면 breach."""
    mod = _load("auditPanelFreshness")
    filings = [(f"{i:06d}", f"2026081400{i:04d}", "20260814", "반기보고서 (2026.06)") for i in range(1, 301)]
    _wire(monkeypatch, filings=filings, panelHave={f"{i:06d}": set() for i in range(1, 301)})

    result = mod.auditPanelFreshness(today=date(2026, 8, 22))

    assert result["expected"] == 300 and result["missing"] == 300
    assert result["breach"] is True
    assert len(result["samples"]) == 20


def test_audit_raises_when_listing_empty(monkeypatch):
    """감사 불능(공시목록 0)은 숨기지 않고 예외로 드러낸다."""
    mod = _load("auditPanelFreshness")
    _wire(monkeypatch, filings=[], panelHave={})
    from dartlab.gather.dart import disclosure

    monkeypatch.setattr(disclosure, "listFilings", lambda *a, **k: pl.DataFrame())
    with pytest.raises(RuntimeError):
        mod.auditPanelFreshness(today=date(2026, 8, 22))


def test_monitor_freshness_entry_breach_is_persistent():
    monitor = _load("monitorPipeline")
    audit = _load("auditPanelFreshness")
    result = {
        "breach": True,
        "expected": 2789,
        "missing": 2591,
        "unknownCompanies": 0,
        "window": "a~b",
        "samples": [("000A", "1", "20260814", "반기보고서")],
    }

    entry = monitor._freshnessEntry(result, auditName=audit.AUDIT_NAME, describe=audit.describe)

    assert entry["state"] == "persistent" and entry["name"] == audit.AUDIT_NAME
    assert "2591/2789" in entry["conclusion"]
    assert entry["samples"] == result["samples"]
    body = monitor._buildIssueBody([entry], [entry], [], [])
    assert "데이터 신선도 누락 표본" in body and "000A" in body
    assert monitor._issueTitle([entry], []) == f"Pipeline failure: {audit.AUDIT_NAME}"


def test_monitor_freshness_entry_ok_is_not_failure():
    monitor = _load("monitorPipeline")
    audit = _load("auditPanelFreshness")
    entry = monitor._freshnessEntry(
        {"breach": False, "expected": 2900, "missing": 3, "unknownCompanies": 0, "window": "a~b", "samples": []},
        auditName=audit.AUDIT_NAME,
        describe=audit.describe,
    )
    assert entry["state"] == "ok" and entry["classification"] == ""


def test_monitor_skips_freshness_without_dart_keys(monkeypatch):
    monitor = _load("monitorPipeline")
    monkeypatch.delenv("DART_API_KEYS", raising=False)
    monkeypatch.delenv("DART_API_KEY", raising=False)
    assert monitor._auditFreshness() is None


def test_monitor_skips_freshness_when_trigger_gate_is_off(monkeypatch):
    """workflow_run 잡음 트리거에서는 DARTLAB_FRESHNESS_AUDIT=0 으로 감사를 건너뛴다(키가 있어도)."""
    monitor = _load("monitorPipeline")
    monkeypatch.setenv("DART_API_KEYS", "k")
    monkeypatch.setenv("DARTLAB_FRESHNESS_AUDIT", "0")
    assert monitor._auditFreshness() is None


def test_monitor_reports_freshness_audit_failure_as_unknown(monkeypatch):
    """감사 자체가 실패해도 run 감시는 계속되고, 그 사실은 entry 로 남는다."""
    monitor = _load("monitorPipeline")
    monkeypatch.setenv("DART_API_KEYS", "k")

    class _Mod:
        AUDIT_NAME = "DART panel 신선도"

        @staticmethod
        def auditPanelFreshness(*, token=None):
            raise RuntimeError("DART down")

        describe = staticmethod(str)

    monkeypatch.setattr(monitor, "_loadFreshnessModule", lambda: _Mod)
    entry = monitor._auditFreshness()
    assert entry is not None and entry["state"] == "unknown" and "DART down" in entry["conclusion"]


def test_data_audit_workflow_passes_dart_keys_to_monitor():
    """dataAudit.yml 이 DART_API_KEYS 를 넘기지 않으면 신선도 감사는 조용히 건너뛴다. 배선을 고정한다."""
    text = (ROOT / ".github" / "workflows" / "dataAudit.yml").read_text(encoding="utf-8")
    assert "DART_API_KEYS: ${{ secrets.DART_API_KEYS }}" in text
    assert "monitorPipeline.py" in text
    assert "DARTLAB_FRESHNESS_AUDIT:" in text  # 트리거 게이트 배선
    assert "github.event.workflow_run.name == 'Original SSOT Sync'" in text  # panel 생산자 완료 뒤엔 반드시 감사
    assert "cancel-in-progress: false" in text  # 진행 중 감사가 뒤따르는 트리거에 끊기지 않게


def test_lookup_with_budget_returns_partial_when_slow():
    """HF 가 느리면 예산 안에 본 종목만 돌려주고 timedOut 을 올린다(daemon 스레드라 프로세스 종료를 안 묶는다)."""
    import time

    mod = _load("auditPanelFreshness")

    def slow(code: str):
        time.sleep(0.3)
        return {code}

    results, timedOut = mod.lookupWithBudget([f"{i:06d}" for i in range(40)], slow, workers=4, budgetSeconds=0.5)
    assert timedOut is True
    assert 0 < len(results) < 40
    fast, timedOutFast = mod.lookupWithBudget(["a", "b"], lambda c: {c}, workers=2, budgetSeconds=5)
    assert timedOutFast is False and fast == {"a": {"a"}, "b": {"b"}}


def test_audit_budget_exhaustion_counts_unseen_as_unknown(monkeypatch):
    """예산 초과로 못 본 종목은 조회 실패로 세고 판정 모수에서 빠진다."""
    import time

    mod = _load("auditPanelFreshness")
    filings = [(f"{i:06d}", f"2026081400{i:04d}", "20260814", "반기보고서 (2026.06)") for i in range(1, 41)]
    _wire(monkeypatch, filings=filings, panelHave={})
    from dartlab.pipeline.stages import panelRceptReconcile

    def slowLookup(repo, relDir, code, *, token=None):
        time.sleep(0.3)
        return set()

    monkeypatch.setattr(panelRceptReconcile, "_panelRceptsFromHf", slowLookup)

    result = mod.auditPanelFreshness(today=date(2026, 8, 22), budgetSeconds=0.5)

    assert result["timedOut"] is True
    assert result["companies"] == 40
    assert 0 < result["lookedUp"] < 40
    assert result["unknownCompanies"] == 40 - result["lookedUp"]
    assert result["expected"] == result["lookedUp"]  # 본 종목만 모수
    assert "예산 초과" in mod.describe(result)


def test_monitor_withholds_verdict_when_sample_is_thin():
    """예산 초과 + 표본 절반 미만이면 unknown(알림도 통과도 아님). 표본이 충분하면 평소대로 판정한다."""
    monitor = _load("monitorPipeline")
    audit = _load("auditPanelFreshness")
    thin = {"breach": True, "timedOut": True, "coverage": 0.3, "expected": 10, "missing": 9, "samples": []}
    entry = monitor._freshnessEntry(thin, auditName=audit.AUDIT_NAME, describe=audit.describe)
    assert entry["state"] == "unknown" and "표본 부족" in entry["classification"]
    enough = {"breach": True, "timedOut": True, "coverage": 0.8, "expected": 100, "missing": 90, "samples": []}
    entry = monitor._freshnessEntry(enough, auditName=audit.AUDIT_NAME, describe=audit.describe)
    assert entry["state"] == "persistent"


def test_audit_counts_only_successful_lookups_as_sample(monkeypatch):
    """HF 429 처럼 조회가 None 으로 무더기 실패하면 표본이 아니다. thinSample 이 올라가 판정을 유보한다."""
    mod = _load("auditPanelFreshness")
    filings = [(f"{i:06d}", f"2026081400{i:04d}", "20260814", "반기보고서 (2026.06)") for i in range(1, 41)]
    have = {
        f"{i:06d}": (set() if i <= 4 else None) for i in range(1, 41)
    }  # 4 종목만 조회 성공(전부 누락), 36 종목 None
    _wire(monkeypatch, filings=filings, panelHave=have)
    monkeypatch.setattr(mod, "LOOKUP_RETRIES", 1)

    result = mod.auditPanelFreshness(today=date(2026, 8, 22), budgetSeconds=30)

    assert result["lookedUp"] == 4 and result["unknownCompanies"] == 36
    assert result["coverage"] == 0.1 and result["thinSample"] is True
    assert (
        result["missing"] == 4 and result["breach"] is False
    )  # 절대 하한(20) 미만이라 breach 는 아니지만 pass 도 아니다
    assert "조회 실패" in mod.describe(result)


def test_monitor_withholds_verdict_on_thin_sample_without_timeout():
    """429 폭주로 조회 성공이 적으면(timedOut 아님) 'pass' 를 찍지 않고 unknown."""
    monitor = _load("monitorPipeline")
    audit = _load("auditPanelFreshness")
    result = {
        "breach": False,
        "thinSample": True,
        "timedOut": False,
        "coverage": 0.01,
        "expected": 20,
        "missing": 16,
        "samples": [],
    }
    entry = monitor._freshnessEntry(result, auditName=audit.AUDIT_NAME, describe=audit.describe)
    assert entry["state"] == "unknown"


def test_monitor_keeps_freshness_issue_when_audit_skipped_or_withheld():
    """신선도 실패로 열린 Issue 는 감사를 건너뛴 run(None)·유보한 run(unknown)이 닫지 않는다. ok 로 잰 run 만 닫는다."""
    monitor = _load("monitorPipeline")
    body = "## report\n" + monitor.FRESHNESS_SAMPLE_MARKER + "\n- 000A"
    assert monitor._mayCloseIssue(None, body) is False
    assert monitor._mayCloseIssue({"state": "unknown"}, body) is False
    assert monitor._mayCloseIssue({"state": "ok"}, body) is True
    assert monitor._mayCloseIssue(None, "## report without freshness") is True
