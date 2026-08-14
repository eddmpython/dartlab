"""stage 충실성 — runScript 호출 인자가 워크플로와 동형인지(mock, 실행 0)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _capture(monkeypatch, modname):
    """모듈의 runScript 를 호출 기록 mock 으로 교체."""
    import importlib

    mod = importlib.import_module(modname)
    calls: list[tuple] = []
    monkeypatch.setattr(mod, "runScript", lambda *a, **k: calls.append((a, k)) or 0)
    return mod, calls


def test_macro_faithful(monkeypatch):
    """macro — in-library 흡수: runMacroData(source=MACRO_SOURCE) + cycle + regime.

    옛 runScript 서브프로세스 위임은 흡수됨(stages/macro.py). MACRO_SOURCE 입구 해석 +
    data 성공 시 cycle/regime 독립 호출 + token/upload 전파를 단언한다.
    """
    import importlib

    from dartlab.pipeline.types import StageResult

    monkeypatch.setenv("MACRO_SOURCE", "fred")
    mod = importlib.import_module("dartlab.pipeline.stages.macro")
    seen: list[tuple[str, dict]] = []

    def _ok(cat):
        def _fn(**k):
            seen.append((cat, k))
            r = StageResult(category=cat)
            r.report.ok = 1
            return r

        return _fn

    monkeypatch.setattr(mod, "runMacroData", _ok("data"))
    monkeypatch.setattr(mod, "runMacroCycle", _ok("cycle"))
    monkeypatch.setattr(mod, "runMacroRegime", _ok("regime"))
    res = mod.runMacro(upload=False, token="tok")
    cats = [c for c, _ in seen]
    assert cats == ["data", "cycle", "regime"]
    assert seen[0][1]["source"] == "fred"  # MACRO_SOURCE 입구 해석
    assert all(k["upload"] is False and k["token"] == "tok" for _, k in seen)  # 전파
    assert res.report.ok == 1


def test_krx_incremental_and_backfill(monkeypatch):
    """krx — 기본 incremental, KRX_MODE=backfill 시 --start/--end 포함."""
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.krx")
    monkeypatch.delenv("KRX_MODE", raising=False)
    mod.runKrx()
    assert calls[-1][0] == (".github/scripts/sync/buildKrxData.py", "--mode", "incremental", "--push")
    monkeypatch.setenv("KRX_MODE", "backfill")
    monkeypatch.setenv("KRX_START", "2020")
    monkeypatch.setenv("KRX_END", "2024")
    mod.runKrxIndex()
    assert calls[-1][0] == (
        ".github/scripts/sync/buildKrxIndexData.py",
        "--mode",
        "backfill",
        "--start",
        "2020",
        "--end",
        "2024",
        "--push",
    )


def test_news_faithful(monkeypatch):
    """news — KR/US fetch(--once --max-queries) + bulkUploadHf(--since 86400)."""
    monkeypatch.setenv("NEWS_MAX_QUERIES_KR", "150")
    monkeypatch.setenv("NEWS_MAX_QUERIES_US", "80")
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.news")
    res = mod.runNewsHeadlines(upload=True)
    scripts = [c[0] for c in calls]
    assert scripts[0] == (
        ".github/scripts/sync/syncNewsHeadlines.py",
        "--market",
        "KR",
        "--once",
        "--max-queries",
        "150",
    )
    assert scripts[1] == (
        ".github/scripts/sync/syncNewsHeadlines.py",
        "--market",
        "US",
        "--once",
        "--max-queries",
        "80",
    )
    assert scripts[2] == (".github/scripts/sync/bulkUploadHf.py", "newsHeadlines", "--since", "86400")
    assert res.report.ok == 1


def test_news_no_upload(monkeypatch):
    """news --no-upload — bulkUploadHf 미호출."""
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.news")
    mod.runNewsHeadlines(upload=False)
    assert all("bulkUploadHf" not in c[0][0] for c in calls)


def test_news_enrich_faithful(monkeypatch):
    """newsEnrich(Phase B) — KR/US enrich(--since 86400 --model) + bulkUploadHf(newsEnriched)."""
    monkeypatch.delenv("NEWS_ENRICH_MODEL", raising=False)
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.news")
    res = mod.runNewsEnrich(upload=True)
    scripts = [c[0] for c in calls]
    assert scripts[0] == (
        ".github/scripts/sync/enrichNewsHeadlines.py",
        "--market",
        "KR",
        "--since",
        "86400",
        "--model",
        "lm_dict",  # CI 기본 — 모델 미가용 안전
    )
    assert scripts[1][1:4] == ("--market", "US", "--since")
    assert scripts[2] == (".github/scripts/sync/bulkUploadHf.py", "newsEnriched", "--since", "86400")
    assert res.report.ok == 1


def test_gdelt_forward_faithful(monkeypatch):
    """gdeltForward(Phase D) — syncGdeltBackfill(--start/--end yesterday, --markets, --step) + upload."""
    monkeypatch.delenv("GDELT_LOOKBACK_DAYS", raising=False)
    monkeypatch.delenv("GDELT_STEP_MINUTES", raising=False)
    monkeypatch.delenv("GDELT_MARKETS", raising=False)
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.news")
    res = mod.runGdeltForward(upload=True)
    a = calls[0][0]
    assert a[0] == ".github/scripts/sync/syncGdeltBackfill.py"
    assert a[1] == "--start" and a[3] == "--end"
    assert a[2] < a[4]  # start < end(yesterday) — ISO 비교
    assert "--step-minutes" in a and "360" in a
    assert "--markets" in a and "KR" in a and "GLOBAL" in a
    assert calls[1][0] == (".github/scripts/sync/bulkUploadHf.py", "newsGdelt", "--since", "86400")
    assert res.report.ok == 1


def test_naver_faithful(monkeypatch):
    """naverNews — syncNaverNews forward args + bulkUploadHf(newsNaver --since 86400)."""
    monkeypatch.setenv("NAVER_MAX_QUERIES", "200")
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.news")
    res = mod.runNaverNews(upload=True)
    scripts = [c[0] for c in calls]
    assert scripts[0] == (
        ".github/scripts/sync/syncNaverNews.py",
        "--once",
        "--max-queries",
        "200",
        "--pages",
        "1",
        "--days",
        "1",
    )
    assert scripts[1] == (".github/scripts/sync/bulkUploadHf.py", "newsNaver", "--since", "86400")
    assert res.report.ok == 1


def test_news_enrich_gdelt_registered():
    """buildRegistry 에 newsEnrich·gdeltForward·naverNews 등록 + run 바인딩 + uploadCategories."""
    from dartlab.pipeline.registry import buildRegistry
    from dartlab.pipeline.stages.news import runGdeltForward, runNaverNews, runNewsEnrich

    reg = buildRegistry()
    assert reg["newsEnrich"].run is runNewsEnrich
    assert reg["gdeltForward"].run is runGdeltForward
    assert reg["naverNews"].run is runNaverNews
    assert "newsEnriched" in reg["newsEnrich"].uploadCategories
    assert "newsGdelt" in reg["gdeltForward"].uploadCategories
    assert "newsNaver" in reg["naverNews"].uploadCategories


def test_edgar_four_quarters():
    """edgar 4분기 wrap — 분기 경계 음수 보정."""
    from dartlab.pipeline.stages.edgar import _fourQuarters

    assert _fourQuarters(2024, 2) == [(2024, 2), (2024, 1), (2023, 4), (2023, 3)]


def test_edgar_bulk_quarterly(monkeypatch):
    """edgar — companyfacts bulk + 4분기 download/convert 호출(누락분만)."""
    import dartlab.providers.edgar.bulk as bulk

    seen = {"convertQ": []}
    monkeypatch.setattr(bulk, "downloadCompanyfactsBulk", lambda **k: "/cf.zip")
    monkeypatch.setattr(bulk, "convertBulkToParquets", lambda **k: {"ok": 1})
    monkeypatch.setattr(bulk, "discoverLatestQuarter", lambda: (2024, 2))
    monkeypatch.setattr(bulk, "listLocalQuarters", lambda **k: [(2023, 4)])  # 1개 보유
    monkeypatch.setattr(bulk, "downloadQuarterlyDataset", lambda y, q, **k: f"/{y}Q{q}.zip")
    monkeypatch.setattr(
        bulk, "convertQuarterlyToParquets", lambda y, q, **k: seen["convertQ"].append((y, q)) or {"sub": 1}
    )

    from dartlab.pipeline.stages.edgar import runEdgar

    res = runEdgar()
    # 4분기 중 (2023,4) 보유 → 3개만 convert
    assert seen["convertQ"] == [(2024, 2), (2024, 1), (2023, 3)]
    assert res.report.ok == 2 and res.report.err == 0


def test_edgar_universe_ciks_seeds_ticker_map(monkeypatch):
    """클린 러너에서도 SEC ticker map을 먼저 만들고 상장 CIK만 반환한다."""
    import polars as pl

    import dartlab.gather.edgar.identity as identity
    import dartlab.pipeline.stages.edgarPanel as edgarPanel
    from dartlab.pipeline.stages.edgar import _universeCiks

    monkeypatch.setattr(edgarPanel, "_priorityTickers", lambda: ["AAPL", "MSFT"])
    monkeypatch.setattr(
        identity,
        "loadTickers",
        lambda refresh=False: pl.DataFrame(
            {"ticker": ["AAPL", "MSFT", "PRIVATE"], "cik": ["320193", "789019", "999999"]}
        ),
    )

    assert _universeCiks() == {"0000320193", "0000789019"}


def test_edgar_public_upload_fails_closed_without_universe(monkeypatch):
    """상장 universe가 비면 17k filer를 HF flat 경로에 발행하지 않고 stage를 실패시킨다."""
    import dartlab.pipeline.stages.edgar as stage
    import dartlab.providers.edgar.bulk as bulk

    monkeypatch.setattr(bulk, "downloadCompanyfactsBulk", lambda **_kwargs: "/cf.zip")
    monkeypatch.setattr(
        bulk,
        "convertBulkToParquets",
        lambda **_kwargs: {"changed": ["0000320193.parquet"], "failed": 0},
    )
    monkeypatch.setattr(bulk, "discoverLatestQuarter", lambda: None)
    monkeypatch.setattr(stage, "_universeCiks", lambda: set())

    result = stage.runEdgar(upload=True)

    assert result.report.err == 1
    assert any("상장 universe" in failure for failure in result.report.failures)


def test_edgar_workflow_does_not_cache_full_panel_tree():
    """약 9GB panel 전체 cache가 bulk와 finance cache를 축출하는 회귀를 막는다."""
    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "edgarSync.yml").read_text(
        encoding="utf-8"
    )
    assert "Restore EDGAR panel cache" not in workflow
    assert "Save EDGAR panel cache" not in workflow
    assert "path: data/edgar/panel" not in workflow


def test_dart_recent_respects_sync_categories_env(monkeypatch):
    """dart recent — SYNC_CATEGORIES env(다중) 우선, 없으면 category 단일."""
    mod, calls = _capture(monkeypatch, "dartlab.pipeline.stages.dart")
    monkeypatch.setattr(mod, "readChanged", lambda c: [])
    monkeypatch.setenv("SYNC_CATEGORIES", "finance,report")
    mod.runDartRecent(category="finance", upload=False)
    assert calls[-1][1]["env"] == {"SYNC_CATEGORIES": "finance,report"}
    monkeypatch.delenv("SYNC_CATEGORIES", raising=False)
    mod.runDartRecent(category="report", upload=False)
    assert calls[-1][1]["env"] == {"SYNC_CATEGORIES": "report"}
