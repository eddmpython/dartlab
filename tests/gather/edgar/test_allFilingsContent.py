"""allFilingsContent.getFilingBody 상태 분류 계약. 주입 fake client, 네트워크/OOM 무관.

200+본문=ok · 200+빈/404=no_body(final) · 403/5xx/예외=error(retry). DART fillContent fetch_status 동형.
"""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.unit


class _Resp:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class _Client:
    """주입용 fake httpx client. get() 이 고정 응답 또는 예외."""

    def __init__(self, resp: _Resp | Exception) -> None:
        self._resp = resp

    def get(self, url: str, **_):
        if isinstance(self._resp, Exception):
            raise self._resp
        return self._resp


def test_ok_when_200_with_body():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    body, status = getFilingBody("http://x/doc.htm", client=_Client(_Resp(200, "<html>본문</html>")))
    assert status == "ok"
    assert body == "<html>본문</html>"


def test_no_body_when_200_empty_or_404_or_missing_url():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    assert getFilingBody("http://x", client=_Client(_Resp(200, "   ")))[1] == "no_body"  # 빈 body
    assert getFilingBody("http://x", client=_Client(_Resp(404)))[1] == "no_body"  # 삭제/이동
    assert getFilingBody("", client=_Client(_Resp(200, "x")))[1] == "no_body"  # url 부재


def test_error_when_403_5xx_or_exception():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    assert getFilingBody("http://x", client=_Client(_Resp(403)))[1] == "error"  # rate/forbidden
    assert getFilingBody("http://x", client=_Client(_Resp(500)))[1] == "error"  # 서버 오류
    assert getFilingBody("http://x", client=_Client(httpx.ConnectError("boom")))[1] == "error"  # 예외


def test_error_reasons_are_counted():
    """error 원인을 세어 로그로 남긴다. 2026-10-09 run 은 85 분 무엇에 막혔는지 가를 수 없었다."""
    from collections import Counter

    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    reasons: Counter = Counter()
    getFilingBody("http://x", client=_Client(_Resp(429)), reasons=reasons)
    getFilingBody("http://x", client=_Client(httpx.ReadTimeout("slow")), reasons=reasons)
    assert reasons == Counter({"HTTP 429": 1, "ReadTimeout": 1})


def _dayMeta(n: int):
    import polars as pl

    return pl.DataFrame(
        {
            "accessionNo": [f"a{i:03d}" for i in range(n)],
            "stockCode": ["AAPL"] * n,
            "filingDate": ["20260105"] * n,
            "url": [f"http://x/{i}" for i in range(n)],
        }
    )


def test_fill_content_day_stops_at_deadline_and_marks_rest_error(monkeypatch, tmp_path):
    """마감이 지나면 fetch 를 멈추고 남은 행을 error(재시도 대상)로 남긴다. 재방문이 footer 로 찾는다."""
    import time
    from collections import Counter

    from dartlab.gather.edgar import allFilingsContent as mod

    monkeypatch.setattr(mod, "getFilingBody", lambda *a, **k: pytest.fail("마감 뒤 fetch 했다"))
    reasons: Counter = Counter()
    out = mod.fillContentDay(_dayMeta(3), tmp_path / "d.parquet", deadline=time.monotonic() - 1, reasons=reasons)
    assert out["fetch_status"].to_list() == ["error"] * 3
    assert reasons[mod.STOP_DEADLINE] == 3


def test_fill_content_day_trips_after_consecutive_errors(monkeypatch, tmp_path):
    """error 가 연달아 tripAfter 건이면 멈추고, 남은 행은 error 로 남긴다(SEC 차단 추정)."""
    from collections import Counter

    from dartlab.gather.edgar import allFilingsContent as mod

    calls: list[str] = []

    def fakeBody(url, *, client, reasons=None, **_):
        calls.append(url)
        return None, "error"

    monkeypatch.setattr(mod, "getFilingBody", fakeBody)
    monkeypatch.setattr(mod, "_PACE_SECONDS", 0)
    reasons: Counter = Counter()
    out = mod.fillContentDay(_dayMeta(10), tmp_path / "d.parquet", tripAfter=4, reasons=reasons)
    assert len(calls) == 4
    assert out.height == 10 and set(out["fetch_status"].to_list()) == {"error"}
    assert reasons[mod.STOP_TRIP] == 6
