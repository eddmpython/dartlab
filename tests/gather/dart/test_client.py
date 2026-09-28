"""gather/dart/client.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.gather.dart.client  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_get_bytes_callable() -> None:
    """getBytes() callable smoke."""
    from dartlab.gather.dart.client import DartClient

    assert hasattr(DartClient, "getBytes")


def test_get_df_callable() -> None:
    """getDf() callable smoke."""
    from dartlab.gather.dart.client import DartClient

    assert hasattr(DartClient, "getDf")


def test_get_df_all_callable() -> None:
    """getDfAll() callable smoke."""
    from dartlab.gather.dart.client import DartClient

    assert hasattr(DartClient, "getDfAll")


def test_get_json_callable() -> None:
    """getJson() callable smoke."""
    from dartlab.gather.dart.client import DartClient

    assert hasattr(DartClient, "getJson")


class _FakeJsonResp:
    status_code = 200
    headers = {"Content-Type": "application/json"}

    def raise_for_status(self) -> None:  # 2xx → no-op
        pass

    def json(self) -> dict:
        return {"status": "000", "ok": True}


def test_get_json_retries_transient_transport_error(monkeypatch) -> None:
    """getJson 은 전송 계층 일시 장애(RemoteProtocolError)를 재시도하고 회복한다.

    Original SSOT Sync dart-reconcile 가 DART 서버 연결 끊김 한 번에 잡 전체가 죽던 갭의 회귀 가드.
    """
    import httpx

    from dartlab.gather.dart import client as client_mod

    monkeypatch.setattr(client_mod.time, "sleep", lambda *_a, **_k: None)  # 백오프 즉시
    c = client_mod.DartClient(apiKey="DUMMY")

    calls = {"n": 0}

    def fake_get(url, params=None, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.RemoteProtocolError("Server disconnected without sending a response.")
        return _FakeJsonResp()

    monkeypatch.setattr(c._session, "get", fake_get)
    out = c.getJson("list.json", params={})
    assert out["status"] == "000"
    assert calls["n"] == 3  # 2회 끊김 후 3회차 성공


def test_get_json_raises_after_transient_retries_exhausted(monkeypatch) -> None:
    """재시도 소진 시 마지막 전송 예외를 그대로 올린다(무한 재시도·조용한 삼킴 아님)."""
    import httpx

    from dartlab.gather.dart import client as client_mod

    monkeypatch.setattr(client_mod.time, "sleep", lambda *_a, **_k: None)
    c = client_mod.DartClient(apiKey="DUMMY")

    def always_disconnect(url, params=None, timeout=None):
        raise httpx.RemoteProtocolError("Server disconnected without sending a response.")

    monkeypatch.setattr(c._session, "get", always_disconnect)
    with pytest.raises(httpx.RemoteProtocolError):
        c.getJson("list.json", params={})


# ── 연결 단계(TCP connect) 실패 전용 재시도 ─────────────────────────────
# OpenDART 는 단일 A 레코드라 TCP 연결이 수 분(실측 3~7분) 막히는 구간이 있다. connect 타임아웃이
# 요청 전체 timeout(60초)과 같고 백오프가 0.5초·1초라 3회가 같은 불통 구간에서 다 소진됐다
# (KindList "Fetch OpenDART CORPCODE.xml" 182초 ConnectTimeout). 아래는 그 갭의 회귀 가드다.

_CONNECT_ENV = "DARTLAB_DART_CONNECT_RETRY_ATTEMPTS"


class _FakeBytesResp:
    status_code = 200
    headers = {"Content-Type": "application/zip"}
    content = b"PK\x03\x04fake"

    def raise_for_status(self) -> None:  # 2xx → no-op
        pass


def _recordWaits(monkeypatch, clientMod, *, jitter: float = 1.0) -> list[float]:
    """time.sleep 을 기록기로, random.uniform 을 고정 배율로 바꿔 대기열을 결정적으로 만든다."""
    waits: list[float] = []
    monkeypatch.setattr(clientMod.time, "sleep", waits.append)
    monkeypatch.setattr(clientMod.random, "uniform", lambda _low, _high: jitter)
    return waits


def testGetJsonRetriesConnectTimeoutWithConnectBackoff(monkeypatch) -> None:
    """연결 타임아웃 (N-1)회 뒤 성공. 대기는 짧은 전송 백오프가 아니라 _CONNECT_BACKOFF_SEC 를 따른다."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.delenv(_CONNECT_ENV, raising=False)  # 기본 3회
    waits = _recordWaits(monkeypatch, clientMod)
    c = clientMod.DartClient(apiKey="DUMMY")
    calls = {"n": 0}

    def fakeGet(url, params=None, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectTimeout("timed out")
        return _FakeJsonResp()

    monkeypatch.setattr(c._session, "get", fakeGet)
    out = c.getJson("list.json", params={})
    assert out["status"] == "000"
    assert calls["n"] == 3  # 연결 실패 2회 후 3회차 성공
    assert waits == list(clientMod._CONNECT_BACKOFF_SEC[:2])  # 5초, 15초


def testConnectRetryEnvOverrideFollowsFullBackoffSchedule(monkeypatch) -> None:
    """env 로 시도 횟수를 올리면(CI 6회) 연결 실패 5회를 _CONNECT_BACKOFF_SEC 순서대로 기다려 넘긴다."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.setenv(_CONNECT_ENV, "6")
    waits = _recordWaits(monkeypatch, clientMod)
    c = clientMod.DartClient(apiKey="DUMMY")
    calls = {"n": 0}

    def fakeGet(url, params=None, timeout=None):
        calls["n"] += 1
        if calls["n"] < 6:
            raise httpx.ConnectTimeout("timed out")
        return _FakeBytesResp()

    monkeypatch.setattr(c._session, "get", fakeGet)
    assert c.getBytes("corpCode.xml") == _FakeBytesResp.content
    assert calls["n"] == 6
    assert waits == [5.0, 15.0, 30.0, 60.0, 90.0]
    assert waits == list(clientMod._CONNECT_BACKOFF_SEC)


@pytest.mark.parametrize("excName", ["ConnectTimeout", "ConnectError"])
def testConnectRetryExhaustionReraisesConnectFailure(monkeypatch, excName: str) -> None:
    """연결 단계 재시도를 다 쓰면 마지막 연결 예외를 그 타입 그대로 올린다(조용한 삼킴 아님)."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.delenv(_CONNECT_ENV, raising=False)
    waits = _recordWaits(monkeypatch, clientMod)
    c = clientMod.DartClient(apiKey="DUMMY")
    excType = getattr(httpx, excName)
    calls = {"n": 0}

    def alwaysFail(url, params=None, timeout=None):
        calls["n"] += 1
        raise excType("connect failed")

    monkeypatch.setattr(c._session, "get", alwaysFail)
    with pytest.raises(excType) as excInfo:
        c.getJson("list.json", params={})
    assert excInfo.type is excType
    assert calls["n"] == 3
    assert waits == [5.0, 15.0]


def testRequestTimeoutShortensConnectPhaseOnly(monkeypatch) -> None:
    """요청 timeout 은 httpx.Timeout 으로 넘기고 connect 만 10초로 줄인다(read 는 30/60초 유지)."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.setattr(clientMod.time, "sleep", lambda *_a, **_k: None)  # slot throttle 대기 생략
    c = clientMod.DartClient(apiKey="DUMMY")
    seen: list[object] = []

    def fakeGet(url, params=None, timeout=None):
        seen.append(timeout)
        return _FakeJsonResp() if url.endswith(".json") else _FakeBytesResp()

    monkeypatch.setattr(c._session, "get", fakeGet)
    c.getJson("list.json", params={})
    c.getBytes("corpCode.xml")

    jsonTimeout, bytesTimeout = seen
    assert isinstance(jsonTimeout, httpx.Timeout)
    assert isinstance(bytesTimeout, httpx.Timeout)
    assert jsonTimeout.connect == 10
    assert bytesTimeout.connect == 10
    assert jsonTimeout.read == 30
    assert bytesTimeout.read == 60


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 3), ("6", 6), ("1", 1), ("0", 1), ("-4", 1), ("abc", 3), ("", 3), ("2.5", 3)],
)
def testConnectRetryAttemptsEnvParsing(monkeypatch, raw: str | None, expected: int) -> None:
    """미설정·정수 아님은 기본 3, 1 미만은 최소 1 로 고정한다."""
    from dartlab.gather.dart import client as clientMod

    if raw is None:
        monkeypatch.delenv(_CONNECT_ENV, raising=False)
    else:
        monkeypatch.setenv(_CONNECT_ENV, raw)
    assert clientMod._connectRetryAttempts() == expected


def testConnectRetrySingleAttemptFailsFast(monkeypatch) -> None:
    """시도 횟수 1 이면 연결 실패를 대기 없이 바로 올린다."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.setenv(_CONNECT_ENV, "1")
    waits = _recordWaits(monkeypatch, clientMod)
    c = clientMod.DartClient(apiKey="DUMMY")
    calls = {"n": 0}

    def alwaysRefused(url, params=None, timeout=None):
        calls["n"] += 1
        raise httpx.ConnectError("[Errno 111] Connection refused")

    monkeypatch.setattr(c._session, "get", alwaysRefused)
    with pytest.raises(httpx.ConnectError):
        c.getJson("list.json", params={})
    assert calls["n"] == 1
    assert waits == []


def testConnectBackoffJitterWithinTwentyPercent(monkeypatch) -> None:
    """jitter 는 ±20% 범위에서 뽑고, 순번이 표를 넘으면 끝값(90초)을 반복한다."""
    from dartlab.gather.dart import client as clientMod

    bounds: list[tuple[float, float]] = []

    def upperBound(low: float, high: float) -> float:
        bounds.append((low, high))
        return high

    monkeypatch.setattr(clientMod.random, "uniform", upperBound)
    assert clientMod._connectBackoffWait(0) == pytest.approx(6.0)  # 5초 +20%
    assert clientMod._connectBackoffWait(99) == pytest.approx(108.0)  # 끝값 90초 +20%
    assert len(bounds) == 2
    for low, high in bounds:
        assert low == pytest.approx(0.8)
        assert high == pytest.approx(1.2)


def testNonConnectTransportErrorKeepsShortBackoff(monkeypatch) -> None:
    """ReadTimeout 등 그 밖의 전송 장애는 기존 짧은 경로(3회, 0.5초·1초)를 유지한다."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.setenv(_CONNECT_ENV, "6")  # 연결 단계 설정이 이 경로로 새지 않는지 확인
    waits = _recordWaits(monkeypatch, clientMod)
    c = clientMod.DartClient(apiKey="DUMMY")
    calls = {"n": 0}

    def alwaysReadTimeout(url, params=None, timeout=None):
        calls["n"] += 1
        raise httpx.ReadTimeout("read timed out")

    monkeypatch.setattr(c._session, "get", alwaysReadTimeout)
    with pytest.raises(httpx.ReadTimeout):
        c.getJson("list.json", params={})
    assert calls["n"] == 3
    assert waits == [0.5, 1.0]


def testConnectAndTransientFailuresAreCountedSeparately(monkeypatch) -> None:
    """연결 실패와 5xx 가 섞여도 두 갈래의 시도 횟수를 따로 세고 각자의 백오프를 쓴다."""
    import httpx

    from dartlab.gather.dart import client as clientMod

    monkeypatch.delenv(_CONNECT_ENV, raising=False)
    waits = _recordWaits(monkeypatch, clientMod)
    c = clientMod.DartClient(apiKey="DUMMY")
    request = httpx.Request("GET", f"{clientMod.BASE_URL}/list.json")
    results: list[object] = [
        httpx.ConnectTimeout("timed out"),
        httpx.Response(503, request=request),
        httpx.ConnectTimeout("timed out"),
        httpx.Response(503, request=request),
        _FakeJsonResp(),
    ]
    calls = {"n": 0}

    def fakeGet(url, params=None, timeout=None):
        result = results[calls["n"]]
        calls["n"] += 1
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(c._session, "get", fakeGet)
    out = c.getJson("list.json", params={})
    assert out["status"] == "000"
    assert calls["n"] == 5  # 연결 실패 2회(<3) + 5xx 2회(<3) 뒤 성공
    assert waits == [5.0, 0.5, 15.0, 1.0]
