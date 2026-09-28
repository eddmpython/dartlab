"""brokerage.fetch 단위 테스트 — 디코드 + 스모크 (네트워크 0)."""

from __future__ import annotations

import importlib

import pytest

from dartlab.gather.sources.brokerage.fetch import _decode, _healthProblems

pytestmark = pytest.mark.unit

# 2개사 × 2카테고리 기대 — 헬스 판정 시나리오 공통 fixture.
_ENABLED = {"miraeasset": ["기업분석", "산업분석"], "nh": ["기업분석", "시황전략"]}
_FULL = {k: 1.0 for k in _ENABLED}


def test_smoke_import() -> None:
    importlib.import_module("dartlab.gather.sources.brokerage.fetch")
    importlib.import_module("dartlab.gather.sources.brokerage")


def test_decode_with_enc() -> None:
    raw = "리포트".encode("cp949")
    assert _decode(raw, "garbled", "cp949") == "리포트"


def test_decode_no_enc_uses_text() -> None:
    assert _decode(b"x", "이미디코드", None) == "이미디코드"


def test_health_all_healthy() -> None:
    counts = {"miraeasset": {"기업분석": 30, "산업분석": 5}, "nh": {"기업분석": 12, "시황전략": 4}}
    assert _healthProblems(counts, _FULL, _ENABLED) == []


def test_health_broker_fully_dead() -> None:
    # nh 가 enabled 인데 전 카테고리 0행 → 전체 깨짐 1건(카테고리별 중복 보고 안 함)
    counts = {"miraeasset": {"기업분석": 30, "산업분석": 5}}
    problems = _healthProblems(counts, _FULL, _ENABLED)
    assert len(problems) == 1
    assert problems[0].startswith("nh: 전체 0행")


def test_health_category_dead() -> None:
    # miraeasset 은 살아있으나 산업분석만 0행 → 카테고리 셀렉터 깨짐
    counts = {"miraeasset": {"기업분석": 30}, "nh": {"기업분석": 12, "시황전략": 4}}
    problems = _healthProblems(counts, _FULL, _ENABLED)
    assert problems == ["miraeasset/산업분석: 0행 — 보드 URL/셀렉터 깨짐 의심"]


def test_health_low_completeness() -> None:
    counts = {"miraeasset": {"기업분석": 30, "산업분석": 5}, "nh": {"기업분석": 12, "시황전략": 4}}
    comp = {"miraeasset": 1.0, "nh": 0.5}  # nh 필드 절반 누락
    problems = _healthProblems(counts, comp, _ENABLED)
    assert len(problems) == 1
    assert "파싱 완전성" in problems[0] and problems[0].startswith("nh")


def test_health_dynamic_label_no_false_positive() -> None:
    # NH 처럼 report_type 이 config 라벨과 다른 동적 브로커: cats=[] → 카테고리별 검사 생략, 총량만.
    counts = {"nh": {"ETF": 1, "기업": 6, "시황": 3, "전략": 2}}
    enabled = {"nh": []}
    assert _healthProblems(counts, {"nh": 1.0}, enabled) == []


# ── 네트워크 장애 vs 셀렉터 깨짐 (2026-09-15 bookook DNS 실패가 "셀렉터 깨짐" 으로 보고된 회귀) ──


def _networkError() -> Exception:
    """GatherHttpClient 가 재시도 소진 후 던지는 형태: SourceUnavailableError from httpx.ConnectError."""
    import httpx

    from dartlab.gather.types import SourceUnavailableError

    try:
        try:
            raise httpx.ConnectError("[Errno -3] Temporary failure in name resolution")
        except httpx.ConnectError as inner:
            raise SourceUnavailableError("www.bookook.co.kr 요청 실패 (3회 재시도)") from inner
    except SourceUnavailableError as exc:
        return exc


def test_health_network_failure_category_is_not_breakage() -> None:
    """네트워크 장애로 못 받은 카테고리의 0 행은 셀렉터 깨짐으로 세지 않는다."""
    counts = {"miraeasset": {"기업분석": 30}, "nh": {"기업분석": 12, "시황전략": 4}}
    outcomes = {"miraeasset": {"기업분석": "ok", "산업분석": "network: SourceUnavailableError: DNS"}}
    assert _healthProblems(counts, _FULL, _ENABLED, fetchOutcomes=outcomes) == []


def test_health_ok_response_with_zero_rows_is_still_breakage() -> None:
    """200 OK 인데 0 행(셀렉터 깨짐) 은 fetch 결과가 있어도 그대로 깨짐이다."""
    counts = {"miraeasset": {"기업분석": 30}, "nh": {"기업분석": 12, "시황전략": 4}}
    outcomes = {"miraeasset": {"기업분석": "ok", "산업분석": "ok"}}
    problems = _healthProblems(counts, _FULL, _ENABLED, fetchOutcomes=outcomes)
    assert problems == ["miraeasset/산업분석: 0행 — 보드 URL/셀렉터 깨짐 의심"]


def test_health_mixed_network_and_breakage() -> None:
    """한 증권사는 전 요청이 네트워크 장애(경고 대상), 다른 증권사는 HTTP 오류로 0 행(깨짐)."""
    counts = {"miraeasset": {"기업분석": 30, "산업분석": 5}}
    outcomes = {
        "miraeasset": {"기업분석": "ok", "산업분석": "ok"},
        "nh": {"기업분석": "network: ConnectError", "시황전략": "error: HTTPStatusError: 404"},
    }
    problems = _healthProblems(counts, _FULL, _ENABLED, fetchOutcomes=outcomes)
    assert problems == ["nh: 전체 0행 — 사이트 차단/다운 또는 전체 셀렉터 깨짐"]

    allNetwork = {**outcomes, "nh": {"기업분석": "network: ConnectError", "시황전략": "network: ConnectTimeout"}}
    assert _healthProblems(counts, _FULL, _ENABLED, fetchOutcomes=allNetwork) == []


def test_health_every_broker_zero_rows_stays_red_even_if_network() -> None:
    """전 증권사 0 행이면 원인이 네트워크여도 깨짐 1 건을 남겨 실제 장애가 조용히 넘어가지 않는다."""
    outcomes = {
        "miraeasset": {"기업분석": "network: x", "산업분석": "network: x"},
        "nh": {"기업분석": "network: x", "시황전략": "network: x"},
    }
    problems = _healthProblems({}, {"miraeasset": 0.0, "nh": 0.0}, _ENABLED, fetchOutcomes=outcomes)
    assert problems == ["전 증권사 0행: 네트워크 장애로 수집 전체 실패"]


def test_fetch_broker_records_network_and_http_outcomes(monkeypatch) -> None:
    """_fetchBroker 는 카테고리별 결과를 남긴다: 성공 ok, 전송 장애 network, HTTP 상태 오류 error."""
    import asyncio

    import httpx

    from dartlab.gather.sources.brokerage import fetch
    from dartlab.gather.types import SourceUnavailableError

    urls = {
        "기업분석": "https://ok.example/list",
        "시황": "https://dns.example/list",
        "산업": "https://gone.example/list",
    }

    class _Resp:
        content = b"<html></html>"
        text = "<html></html>"

    class _Client:
        async def get(self, url, **_kwargs):
            if "dns" in url:
                raise _networkError()
            if "gone" in url:
                request = httpx.Request("GET", url)
                response = httpx.Response(404, request=request)
                try:
                    raise httpx.HTTPStatusError("404", request=request, response=response)
                except httpx.HTTPStatusError as inner:
                    raise SourceUnavailableError("gone.example 요청 실패 (3회 재시도)") from inner
            return _Resp()

    monkeypatch.setitem(fetch.PARSERS, "testbroker", lambda html, label, url: [])
    monkeypatch.setitem(fetch.BROKERS, "testbroker", {"enabled": True, "enc": None, "categories": urls})

    asyncio.run(fetch._fetchAsync(_Client(), brokers=["testbroker"], resolveTickers=False))
    outcomes = fetch._lastFetchOutcomes()["testbroker"]

    assert outcomes["기업분석"] == "ok"
    assert outcomes["시황"].startswith("network: SourceUnavailableError")
    assert outcomes["산업"].startswith("error: SourceUnavailableError")
    assert fetch._networkFailures({"testbroker": []}, {"testbroker": outcomes}) == [
        f"testbroker/시황: {outcomes['시황'].removeprefix('network: ')}"
    ]
