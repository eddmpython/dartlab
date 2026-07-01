"""allFilingsContent.fetchFilingBody 상태 분류 계약. 주입 fake client, 네트워크/OOM 무관.

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
    from dartlab.gather.edgar.allFilingsContent import fetchFilingBody

    body, status = fetchFilingBody("http://x/doc.htm", client=_Client(_Resp(200, "<html>본문</html>")))
    assert status == "ok"
    assert body == "<html>본문</html>"


def test_no_body_when_200_empty_or_404_or_missing_url():
    from dartlab.gather.edgar.allFilingsContent import fetchFilingBody

    assert fetchFilingBody("http://x", client=_Client(_Resp(200, "   ")))[1] == "no_body"  # 빈 body
    assert fetchFilingBody("http://x", client=_Client(_Resp(404)))[1] == "no_body"  # 삭제/이동
    assert fetchFilingBody("", client=_Client(_Resp(200, "x")))[1] == "no_body"  # url 부재


def test_error_when_403_5xx_or_exception():
    from dartlab.gather.edgar.allFilingsContent import fetchFilingBody

    assert fetchFilingBody("http://x", client=_Client(_Resp(403)))[1] == "error"  # rate/forbidden
    assert fetchFilingBody("http://x", client=_Client(_Resp(500)))[1] == "error"  # 서버 오류
    assert fetchFilingBody("http://x", client=_Client(httpx.ConnectError("boom")))[1] == "error"  # 예외
