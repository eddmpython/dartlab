"""ai/tools/webSearch.py DuckDuckGo redirect 해제 회귀.

예전 ``netloc.endswith("duckduckgo.com")`` 는 ``evilduckduckgo.com`` 같은 남의 도메인 링크도 redirect 로
보고 ``uddg`` 값을 꺼내 줬다(CodeQL py/incomplete-url-substring-sanitization). host 가 duckduckgo.com
자신이거나 점 경계의 하위 도메인일 때만 푼다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

_TARGET = "https://example.com/page?x=1"
_ENCODED = "https%3A%2F%2Fexample.com%2Fpage%3Fx%3D1"


@pytest.mark.parametrize(
    "href",
    [
        f"//duckduckgo.com/l/?uddg={_ENCODED}",
        f"https://duckduckgo.com/l/?uddg={_ENCODED}&rut=abc",
        f"https://html.duckduckgo.com/l/?uddg={_ENCODED}",
        f"//html.duckduckgo.com/l/?uddg={_ENCODED}",
        f"https://DuckDuckGo.COM/l/?uddg={_ENCODED}",
        f"https://duckduckgo.com:443/l/?uddg={_ENCODED}",
    ],
)
def test_resolve_redirect_unwraps_duckduckgo_hosts(href: str) -> None:
    """duckduckgo.com 과 그 하위 도메인의 /l/ redirect 는 uddg 대상 URL 로 풀린다."""
    from dartlab.ai.tools.webSearch import _resolveRedirect

    assert _resolveRedirect(href) == _TARGET


@pytest.mark.parametrize(
    "href",
    [
        f"https://evilduckduckgo.com/l/?uddg={_ENCODED}",
        f"//evilduckduckgo.com/l/?uddg={_ENCODED}",
        f"https://duckduckgo.com.evil.example/l/?uddg={_ENCODED}",
        f"https://evil.example/l/?uddg={_ENCODED}",
        f"https://duckduckgo.com/html/?uddg={_ENCODED}",
    ],
)
def test_resolve_redirect_keeps_other_hosts(href: str) -> None:
    """duckduckgo.com 이 아닌 host(접미만 같은 도메인 포함)나 /l/ 이 아닌 경로는 그대로 둔다."""
    from dartlab.ai.tools.webSearch import _resolveRedirect

    expected = "https:" + href if href.startswith("//") else href
    assert _resolveRedirect(href) == expected


def test_web_search_does_not_unwrap_lookalike_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """SERP 결과에 비슷한 이름의 도메인 링크가 섞여도 ref source 는 그 링크 자체다."""
    from dartlab.ai.tools import webSearch as wsMod

    html = (
        "<html><body>"
        f'<a class="result__a" href="//duckduckgo.com/l/?uddg={_ENCODED}">Real result</a>'
        '<a class="result__snippet">real snippet</a>'
        '<a class="result__a" href="//evilduckduckgo.com/l/?uddg=https%3A%2F%2Ftrusted.example%2F">Lookalike</a>'
        '<a class="result__snippet">lookalike snippet</a>'
        "</body></html>"
    ).encode("utf-8")

    class _MockResponse:
        def read(self) -> bytes:
            return html

        def __enter__(self):
            return self

        def __exit__(self, *args) -> bool:
            return False

    monkeypatch.setattr(wsMod, "urlopen", lambda req, timeout=None: _MockResponse())
    result = wsMod.webSearch("dartlab")

    assert result.ok, result.error
    sources = [ref.source for ref in result.refs]
    assert sources == [
        _TARGET,
        "https://evilduckduckgo.com/l/?uddg=https%3A%2F%2Ftrusted.example%2F",
    ]
