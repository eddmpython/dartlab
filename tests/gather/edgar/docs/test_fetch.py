"""gather/edgar/docs/fetch.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.gather.edgar.docs.fetch  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_build_edgar_collectible_universe_callable() -> None:
    """buildEdgarCollectibleUniverse() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import buildEdgarCollectibleUniverse

    assert callable(buildEdgarCollectibleUniverse)


def test_download_listed_edgar_docs_callable() -> None:
    """downloadListedEdgarDocs() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import downloadListedEdgarDocs

    assert callable(downloadListedEdgarDocs)


def test_fetch_edgar_docs_callable() -> None:
    """fetchEdgarDocs() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import fetchEdgarDocs

    assert callable(fetchEdgarDocs)


def test_iter_edgar_docs_callable() -> None:
    """iterEdgarDocs() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import iterEdgarDocs

    assert callable(iterEdgarDocs)


def test_prepare_edgar_collectible_universe_callable() -> None:
    """prepareEdgarCollectibleUniverse() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import prepareEdgarCollectibleUniverse

    assert callable(prepareEdgarCollectibleUniverse)


def test_summarize_edgar_docs_frame_callable() -> None:
    """summarizeEdgarDocsFrame() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import summarizeEdgarDocsFrame

    assert callable(summarizeEdgarDocsFrame)


def test_summarize_edgar_docs_parquet_callable() -> None:
    """summarizeEdgarDocsParquet() callable smoke."""
    from dartlab.gather.edgar.docs.fetch import summarizeEdgarDocsParquet

    assert callable(summarizeEdgarDocsParquet)


def _runInThread(fn):
    """fn 을 worker thread 에서 실행하고 (반환값, 예외) 를 돌려준다."""
    import threading

    box: dict = {}

    def target():
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 (스레드 예외를 호출자로 전달)
            box["error"] = exc

    worker = threading.Thread(target=target)
    worker.start()
    worker.join(timeout=30)
    return box.get("value"), box.get("error")


def _simulateSigalrmPlatform(monkeypatch, fetch) -> None:
    """Linux 처럼 SIGALRM 이 있는 플랫폼을 흉내 낸다 (Windows 에서도 같은 결함을 재현).

    실제 ``signal.signal`` 은 그대로 두어 메인 스레드 밖 등록이 ValueError 가 되는 규칙을 유지한다.
    """
    import signal

    monkeypatch.setattr(fetch, "_HAS_SIGALRM", True)
    monkeypatch.setattr(signal, "SIGALRM", signal.SIGINT, raising=False)
    monkeypatch.setattr(signal, "alarm", lambda _seconds: 0, raising=False)


def test_filing_timeout_in_worker_thread_does_not_register_signal(monkeypatch) -> None:
    """worker thread 의 _FilingTimeout 은 signal 등록 없이 Timer 폴백을 쓴다.

    batchCollectEdgar 는 asyncio 를 worker thread 에서 돌린다. 예전에는 filing 마다 signal.signal 이
    ValueError 를 던져 일요일 docs 수집 7,720 ticker 가 전부 실패했다.
    """
    from dartlab.gather.edgar.docs import fetch

    _simulateSigalrmPlatform(monkeypatch, fetch)

    def enterAndExit():
        timer = fetch._FilingTimeout(5)
        with timer:
            pass
        return timer

    timer, error = _runInThread(enterAndExit)
    assert error is None
    assert timer._useAlarm is False
    assert timer.timedOut is False


def test_filing_timeout_main_thread_uses_alarm(monkeypatch) -> None:
    """메인 스레드에서는 SIGALRM 핸들러를 걸고 빠져나올 때 알람 해제 + 핸들러 복원."""
    import types

    from dartlab.gather.edgar.docs import fetch

    calls: list[tuple] = []
    fakeSignal = types.SimpleNamespace(
        SIGALRM=14,
        getsignal=lambda _num: "previous",
        signal=lambda num, handler: calls.append(("signal", num, handler)),
        alarm=lambda seconds: calls.append(("alarm", seconds)),
    )
    monkeypatch.setattr(fetch, "_HAS_SIGALRM", True)
    monkeypatch.setattr(fetch, "signal", fakeSignal)

    timer = fetch._FilingTimeout(7)
    with timer:
        assert timer._useAlarm is True
    assert calls[0][:2] == ("signal", 14)
    assert calls[1] == ("alarm", 7)
    assert calls[2] == ("alarm", 0)
    assert calls[3] == ("signal", 14, "previous")


def test_collect_filing_rows_in_worker_thread_keeps_filings(monkeypatch) -> None:
    """worker thread 에서도 filing 이 skip 되지 않고 section row 가 쌓인다 (batch 경로 회귀 가드)."""
    from dartlab.gather.edgar.docs import fetch

    _simulateSigalrmPlatform(monkeypatch, fetch)
    monkeypatch.setattr(fetch, "_downloadFilingSource", lambda filing: "<html>Item 1. Business</html>")
    monkeypatch.setattr(fetch, "_htmlToText", lambda html: "Item 1. Business\nWe make things.")
    monkeypatch.setattr(fetch, "_splitItems", lambda text, formType: [{"title": "Item 1", "content": text}])
    filing = {
        "formType": "10-K",
        "periodEnd": "2025-12-31",
        "year": "2025",
        "accessionNumber": "0000000000-26-000001",
        "filingDate": "2026-02-01",
        "filingUrl": "https://www.sec.gov/Archives/edgar/data/1/x.htm",
    }
    meta = {"cik": "0000000001", "title": "Example Corp"}
    rows: list[dict] = []
    skipped: list[str] = []
    reasons: list[str] = []

    _value, error = _runInThread(
        lambda: fetch._collectFilingRows(rows, [filing], meta, "EXM", None, 5, skipped, skipReasons=reasons)
    )
    assert error is None
    assert skipped == [] and reasons == []
    assert [r["section_title"] for r in rows] == ["Item 1"]


def test_fetch_edgar_docs_reports_first_skip_reason(monkeypatch, tmp_path) -> None:
    """전 filing 이 건너뛰어지면 "section 추출 실패" 에 첫 사유를 붙여 원인을 드러낸다."""
    import httpx

    from dartlab.gather.edgar.docs import fetch

    filing = {
        "formType": "10-K",
        "periodEnd": "2025-12-31",
        "year": "2025",
        "accessionNumber": "0000000000-26-000002",
        "filingDate": "2026-02-01",
        "filingUrl": "https://www.sec.gov/Archives/edgar/data/1/y.htm",
    }

    def refuse(_filing):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(fetch, "_resolveTickerMeta", lambda ticker: {"cik": "0000000001", "title": "Example Corp"})
    monkeypatch.setattr(fetch, "_getSubmissions", lambda cik: {})
    monkeypatch.setattr(fetch, "_findFilings", lambda submissions, sinceYear: [filing])
    monkeypatch.setattr(fetch, "_downloadFilingSource", refuse)

    with pytest.raises(ValueError, match="section 추출 실패") as info:
        fetch.fetchEdgarDocs("EXM", tmp_path / "EXM.parquet", showProgress=False, filingTimeout=0)
    assert "ConnectError" in str(info.value)
    assert "0000000000-26-000002" in str(info.value)
