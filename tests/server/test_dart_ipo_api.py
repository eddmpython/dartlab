"""L6 Backend. /api/dart/ipo/{report,scan} 라우트 단위 테스트.

IPO 리포트/스캔은 로컬 서버가 런타임 파싱해 서빙(베이크 0). 무거운 fetch/parse 는 monkeypatch 격리하고
라우트 배선(파라미터, 함수 호출, 응답 형태)만 검증한다.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from dartlab.server.api import dart

    app = FastAPI()
    app.include_router(dart.router)
    return TestClient(app), dart


def test_ipo_report_route_returns_report(monkeypatch):
    _c, dart = _client()
    captured = {}

    def _fake(rcept, *, corpName=None, confirmationRcept=None):
        captured.update(rcept=rcept, corpName=corpName, confirmationRcept=confirmationRcept)
        return {
            "title": f"{corpName} 공모분석",
            "sections": [{"title": "공모 개요", "rows": [], "badge": None}],
            "markdown": "# 리포트",
        }

    import dartlab.story.ipoReport as mod

    monkeypatch.setattr(mod, "buildIpoReport", _fake)
    resp = _c.get("/api/dart/ipo/report", params={"rcept": "20260626000715", "corp": "기도산업"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "기도산업 공모분석"
    assert body["sections"][0]["title"] == "공모 개요"
    assert captured == {"rcept": "20260626000715", "corpName": "기도산업", "confirmationRcept": None}


def test_ipo_report_route_requires_rcept():
    _c, _ = _client()
    resp = _c.get("/api/dart/ipo/report")  # rcept 필수
    assert resp.status_code == 422


def test_ipo_scan_route_returns_rows(monkeypatch):
    _c, dart = _client()

    def _fakeScan(*, dateFrom=None, deep=True, verbose=True):
        return pl.DataFrame({"corpName": ["기도산업"], "freeFloatPct": [32.5], "appliedPer": [10.01]})

    import dartlab.scan.ipo as scanmod

    monkeypatch.setattr(scanmod, "scanIpo", _fakeScan)
    resp = _c.get("/api/dart/ipo/scan", params={"deep": "false"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["rows"][0]["corpName"] == "기도산업"
