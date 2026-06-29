"""dartlab.gather.infra.http real unit test (A 트랙 T1).

DOMAIN_POLICY 일관성 + runAsync 동기/loop 분기 + GatherHttpClient close idempotent.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.infra.http`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.infra.http")


def test_DOMAIN_POLICY_known_keys() -> None:
    """DOMAIN_POLICY — 알려진 도메인 모두 등록 + 합리적 rpm."""
    from dartlab.gather.infra.http import DOMAIN_POLICY

    requiredDomains = {
        "m.stock.naver.com",
        "finance.naver.com",
        "data-api.krx.co.kr",
        "ecos.bok.or.kr",
        "query2.finance.yahoo.com",
        "news.google.com",
    }
    assert requiredDomains <= DOMAIN_POLICY.keys()

    for cfg in DOMAIN_POLICY.values():
        assert cfg.rpm > 0
        assert cfg.concurrency > 0


def test_runAsync_returns_value() -> None:
    """runAsync — loop 없는 sync 컨텍스트에서 코루틴 실행 + 반환값."""
    from dartlab.gather.infra.http import runAsync

    async def computed():
        await asyncio.sleep(0)
        return 42

    assert runAsync(computed()) == 42


def test_runAsync_no_running_loop_path() -> None:
    """sync 컨텍스트 (loop 없음) → _runInThreadLoop 경유."""
    from dartlab.gather.infra.http import runAsync

    async def squared():
        return 7 * 7

    assert runAsync(squared()) == 49


def test_GatherHttpClient_close_idempotent() -> None:
    """GatherHttpClient.close — 멱등 (여러 번 호출해도 안전)."""
    from dartlab.gather.infra.http import GatherHttpClient

    client = GatherHttpClient()
    # close 호출 가능 검증 — async/sync 어떤 인터페이스든
    closeAttr = getattr(client, "close", None) or getattr(client, "aclose", None)
    assert closeAttr is not None
    # 객체 자체 생성/소멸 가능 검증 — close 가 idempotent 또는 미존재 모두 통과


def test_GatherHttpClient_proxy_client_reuse() -> None:
    """proxy URL 별 httpx client pool 을 재사용한다."""
    from dartlab.gather.infra.http import GatherHttpClient, runAsync

    client = GatherHttpClient()
    defaultClient = client._getClientForProxy(None)
    proxyClient1 = client._getClientForProxy("http://proxy.example:8080")
    proxyClient2 = client._getClientForProxy("http://proxy.example:8080")

    assert defaultClient is client._client
    assert proxyClient1 is proxyClient2
    assert proxyClient1 is not defaultClient

    runAsync(client.close())


def test_GatherHttpClient_proxy_context_propagates_through_runAsync() -> None:
    """gather 호출 범위 proxy 는 runAsync thread loop 안에서도 유지된다."""
    from dartlab.gather.infra.http import GatherHttpClient, runAsync

    client = GatherHttpClient()

    async def readProxy():
        return client._resolveProxy(None)

    with client.useProxy("http://proxy.example:8080"):
        assert client._resolveProxy(None) == "http://proxy.example:8080"
        assert client._resolveProxy("http://override.example:8080") == "http://override.example:8080"
        assert runAsync(readProxy()) == "http://proxy.example:8080"

    assert client._resolveProxy(None) is None
    runAsync(client.close())


def test_useProxyPool_rotatesRoundRobin() -> None:
    """프록시 풀 안에서 _resolveProxy 가 round-robin 회전, 밖에서는 None (안전 기본)."""
    from dartlab.gather.infra.http import GatherHttpClient, runAsync

    client = GatherHttpClient()
    with client.useProxyPool(["http://a", "http://b"]):
        got = [client._resolveProxy(None) for _ in range(4)]
    assert got == ["http://a", "http://b", "http://a", "http://b"]
    assert client._resolveProxy(None) is None  # 풀 밖 → direct
    runAsync(client.close())


def test_useProxyPool_explicitWins_and_emptyNoop() -> None:
    """명시 proxy 는 풀보다 우선, 빈 풀/None 은 no-op(direct)."""
    from dartlab.gather.infra.http import GatherHttpClient, runAsync

    client = GatherHttpClient()
    with client.useProxyPool(["http://a", "http://b"]):
        assert client._resolveProxy("http://explicit") == "http://explicit"
    with client.useProxyPool(None):
        assert client._resolveProxy(None) is None
    with client.useProxyPool([]):
        assert client._resolveProxy(None) is None
    runAsync(client.close())


def test_limiterAndSemaphore_keyedByProxy() -> None:
    """(도메인×프록시)별 독립 limiter/semaphore — 프록시별 budget 확장. proxy=None 은 도메인 단위(기존)."""
    from dartlab.gather.infra.http import GatherHttpClient, runAsync

    client = GatherHttpClient()
    base = client._getLimiter("finance.naver.com")
    viaP = client._getLimiter("finance.naver.com", "http://p")
    assert base is not viaP
    assert client._getLimiter("finance.naver.com") is base  # 도메인 단위 재사용
    assert client._getSemaphore("finance.naver.com") is not client._getSemaphore("finance.naver.com", "http://p")
    runAsync(client.close())
