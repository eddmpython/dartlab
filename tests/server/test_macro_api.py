"""FRED 매크로 API 오류 응답 단위 테스트.

/api/fred/correlation 이 FredError 문자열 (FRED 응답 본문 포함) 을 응답에 싣지 않고
예외 타입별 고정 문구만 돌려주는지 확인한다. _getFred 를 가짜 객체로 바꿔 네트워크 0.
"""

from __future__ import annotations

import importlib
import logging

import polars as pl
import pytest

pytestmark = pytest.mark.unit

# FRED 400 응답 본문을 흉내 낸 내부 정보. 응답에는 없어야 하고 서버 로그에만 남아야 한다.
_UPSTREAM_BODY = "<html>\nBad Request internal-host-10.0.0.5\n</html>"


class _FakeFred:
    """correlation / leadLag 만 가진 Fred 대역."""

    def __init__(self, exc: Exception | None) -> None:
        self._exc = exc

    def correlation(self, seriesIds, *, start=None, end=None):
        if self._exc is not None:
            raise self._exc
        return pl.DataFrame({"a": [1.0]})

    def leadLag(self, a, b, *, maxLag=12, start=None, end=None):
        if self._exc is not None:
            raise self._exc
        return pl.DataFrame({"lag": [0], "corr": [1.0]})


def _client(monkeypatch: pytest.MonkeyPatch, fake: _FakeFred):
    macro = importlib.import_module("dartlab.server.api.macro")
    monkeypatch.setattr(macro, "_getFred", lambda: fake)
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(macro.router)
    return TestClient(app)


@pytest.mark.parametrize(
    ("excName", "expected"),
    [
        ("RateLimitError", "FRED 요청 한도 초과. 잠시 후 다시 시도하세요."),
        ("AuthenticationError", "FRED API 키를 확인하세요."),
        ("SeriesNotFoundError", "FRED 시리즈를 찾을 수 없습니다."),
        ("FredError", "FRED 데이터를 가져오지 못했습니다."),
    ],
)
def test_correlation_error_is_constant_message(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, excName: str, expected: str
) -> None:
    """예외 타입별 고정 문구만 응답에 싣고, 상세는 서버 로그 한 줄로 남긴다."""
    types = importlib.import_module("dartlab.gather.fred.types")
    exc = getattr(types, excName)(f"FRED API 오류 400: {_UPSTREAM_BODY}")
    client = _client(monkeypatch, _FakeFred(exc))

    with caplog.at_level(logging.WARNING, logger="dartlab.server.api.macro"):
        resp = client.get("/api/fred/correlation", params={"ids": "GDP,UNRATE", "leadLag": "GDP,UNRATE"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["correlation_error"] == expected
    assert body["lead_lag_error"] == expected
    assert "internal-host" not in resp.text

    records = [r.getMessage() for r in caplog.records if r.name == "dartlab.server.api.macro"]
    assert len(records) == 2
    assert all("internal-host-10.0.0.5" in m for m in records)
    assert all("\n" not in m for m in records)


def test_correlation_success_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """정상 경로 응답 schema 는 그대로."""
    client = _client(monkeypatch, _FakeFred(None))

    resp = client.get("/api/fred/correlation", params={"ids": "GDP,UNRATE", "leadLag": "GDP,UNRATE"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["correlation"] == [{"a": 1.0}]
    assert body["lead_lag"] == [{"lag": 0, "corr": 1.0}]
    assert "correlation_error" not in body
    assert "lead_lag_error" not in body
