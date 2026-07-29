"""providers/dart/openapi/batch.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.gather.dart.batch  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_close_callable() -> None:
    """close() callable smoke."""
    from dartlab.gather.dart.batch import AsyncDartClient

    assert hasattr(AsyncDartClient, "close")


def test_get_bytes_callable() -> None:
    """getBytes() callable smoke."""
    from dartlab.gather.dart.batch import AsyncDartClient

    assert hasattr(AsyncDartClient, "getBytes")


def test_get_df_callable() -> None:
    """getDf() callable smoke."""
    from dartlab.gather.dart.batch import AsyncDartClient

    assert hasattr(AsyncDartClient, "getDf")


def test_get_json_callable() -> None:
    """getJson() callable smoke."""
    from dartlab.gather.dart.batch import AsyncDartClient

    assert hasattr(AsyncDartClient, "getJson")


def test_get_json_retries_transient_read_error(monkeypatch) -> None:
    """DART ReadError는 같은 요청 단위에서 재시도한다."""
    import asyncio

    import httpx

    from dartlab.gather.dart import batch
    from dartlab.gather.dart.batch import AsyncDartClient

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"status": "000", "list": [{"ok": True}]}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            self.calls = 0

        async def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise httpx.ReadError("server closed connection")
            return FakeResponse()

        async def aclose(self) -> None:
            return None

    fakeClient = FakeAsyncClient()
    monkeypatch.setattr(batch.httpx, "AsyncClient", lambda *args, **kwargs: fakeClient)

    client = AsyncDartClient("key", maxRetries=1, retryBaseDelay=0)
    result = asyncio.run(client.getJson("list.json", {"corp_code": "00126380"}))

    assert result == {"status": "000", "list": [{"ok": True}]}
    assert fakeClient.calls == 2


def test_get_json_throttles_once_per_http_attempt(monkeypatch) -> None:
    """공개 요청과 retry helper가 같은 HTTP 시도를 이중 throttle 하지 않는다."""
    import asyncio

    from dartlab.gather.dart import batch
    from dartlab.gather.dart.batch import AsyncDartClient

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"status": "000", "list": []}

    class FakeAsyncClient:
        async def get(self, *args, **kwargs):
            return FakeResponse()

        async def aclose(self) -> None:
            return None

    monkeypatch.setattr(batch.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient())
    client = AsyncDartClient("key")
    throttleCalls = 0

    async def fakeThrottle() -> None:
        nonlocal throttleCalls
        throttleCalls += 1

    monkeypatch.setattr(client, "_throttle", fakeThrottle)

    asyncio.run(client.getJson("list.json"))

    assert throttleCalls == 1


def test_get_json_raises_unknown_api_status(monkeypatch) -> None:
    """013 외 API 오류를 빈 결과로 위장하지 않는다."""
    import asyncio

    import pytest

    from dartlab.core.dartClient import DartApiError
    from dartlab.gather.dart import batch
    from dartlab.gather.dart.batch import AsyncDartClient

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"status": "800", "message": "시스템 점검"}

    class FakeAsyncClient:
        async def get(self, *args, **kwargs):
            return FakeResponse()

        async def aclose(self) -> None:
            return None

    monkeypatch.setattr(batch.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient())
    client = AsyncDartClient("key")

    with pytest.raises(DartApiError, match=r"\[800\] 시스템 점검"):
        asyncio.run(client.getDf("fnlttSinglAcntAll.json"))


def test_get_json_marks_quota_exhausted_and_raises(monkeypatch) -> None:
    """020은 중단 상태를 남기고 구조화 예외로 호출자에게 전달한다."""
    import asyncio

    import pytest

    from dartlab.core.dartClient import DartApiError
    from dartlab.gather.dart import batch
    from dartlab.gather.dart.batch import AsyncDartClient

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"status": "020", "message": "요청 제한 초과"}

    class FakeAsyncClient:
        async def get(self, *args, **kwargs):
            return FakeResponse()

        async def aclose(self) -> None:
            return None

    monkeypatch.setattr(batch.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient())
    client = AsyncDartClient("key")

    with pytest.raises(DartApiError, match=r"\[020\] 요청 제한 초과"):
        asyncio.run(client.getJson("list.json"))

    assert client.exhausted is True


def test_batch_collect_callable() -> None:
    """batchCollect() callable smoke."""
    from dartlab.gather.dart.batch import batchCollect

    assert callable(batchCollect)


def test_batch_collect_rejects_non_positive_worker_count() -> None:
    """0개 worker로 pending만 남기는 무작동 실행을 허용하지 않는다."""
    import pytest

    from dartlab.gather.dart.batch import batchCollect

    with pytest.raises(ValueError, match="1 이상"):
        batchCollect(["005930"], maxWorkers=0, showProgress=False)


def test_batch_collect_all_rejects_unknown_mode() -> None:
    """오타 mode가 전체 수집으로 확대되는 것을 막는다."""
    import pytest

    from dartlab.gather.dart.batch import batchCollectAll

    with pytest.raises(ValueError, match="'new' 또는 'all'"):
        batchCollectAll(mode="typo", showProgress=False)


def test_batch_collect_all_callable() -> None:
    """batchCollectAll() callable smoke."""
    from dartlab.gather.dart.batch import batchCollectAll

    assert callable(batchCollectAll)


def test_batch_collect_invokes_on_checkpoint_per_n_stocks(monkeypatch) -> None:
    """batchCollect 가 N 종목마다 onCheckpoint 콜백 호출 + 종료 직전 final flush.

    cancel/timeout 안전망 검증 — 90 분 timeout 사고 (2026-05-16) 의 root cause fix.
    """
    from dartlab.gather.dart import batch

    monkeypatch.setattr(batch, "_resolveCorpMap", lambda codes: {c: ("", c) for c in codes})
    monkeypatch.setattr(batch, "resolveDartKeys", lambda: ["fake-key"])

    class _FakeClient:
        exhausted = False

        def __init__(self, *args, **kwargs) -> None:
            pass

        async def close(self) -> None:
            return None

        async def getDf(self, *args, **kwargs):
            return None

    monkeypatch.setattr(batch, "AsyncDartClient", _FakeClient)

    async def _zero(*args, **kwargs):
        return 0

    monkeypatch.setattr(batch, "_collectFinance", _zero)
    monkeypatch.setattr(batch, "_collectReport", _zero)

    calls: list[list[str]] = []

    def _cb(codes: list[str]) -> None:
        calls.append(list(codes))

    batch.batchCollect(
        ["A", "B", "C", "D", "E", "F", "G"],
        categories=["finance"],
        showProgress=False,
        onCheckpoint=_cb,
        checkpointEvery=3,
    )

    flat = [code for chunk in calls for code in chunk]
    # 7 종목 / every 3 → drain at 3, drain at 6, final flush 1 종목.
    assert set(flat) == {"A", "B", "C", "D", "E", "F", "G"}
    # final flush 가 비어있지 않은 잔여를 호출 — 최소 1 회 호출.
    assert len(calls) >= 1
    # 어떤 chunk 도 checkpointEvery 초과하지 않음.
    assert all(len(chunk) <= 3 for chunk in calls)


def test_batch_collect_skips_checkpoint_when_disabled(monkeypatch) -> None:
    """checkpointEvery=0 (default) 면 콜백 자체가 호출되지 않는다 — 기존 호출자 호환."""
    from dartlab.gather.dart import batch

    monkeypatch.setattr(batch, "_resolveCorpMap", lambda codes: {c: ("", c) for c in codes})
    monkeypatch.setattr(batch, "resolveDartKeys", lambda: ["fake-key"])

    class _FakeClient:
        exhausted = False

        def __init__(self, *args, **kwargs) -> None:
            pass

        async def close(self) -> None:
            return None

        async def getDf(self, *args, **kwargs):
            return None

    monkeypatch.setattr(batch, "AsyncDartClient", _FakeClient)

    async def _zero(*args, **kwargs):
        return 0

    monkeypatch.setattr(batch, "_collectFinance", _zero)
    monkeypatch.setattr(batch, "_collectReport", _zero)

    invoked = {"n": 0}

    def _cb(_codes):
        invoked["n"] += 1

    batch.batchCollect(
        ["A", "B"],
        categories=["finance"],
        showProgress=False,
        onCheckpoint=_cb,  # callback 줘도
        checkpointEvery=0,  # every=0 이면 비활성
    )

    assert invoked["n"] == 0


def test_collect_finance_target_period_refreshes_existing_period(tmp_path, monkeypatch) -> None:
    """targetPeriods는 정정 공시 반영을 위해 기존 period도 다시 수집한다."""
    import asyncio

    import polars as pl

    import dartlab
    from dartlab.gather.dart.batch import _collectFinance

    monkeypatch.setattr(dartlab.config, "dataDir", str(tmp_path))
    financePath = tmp_path / "dart" / "finance" / "005930.parquet"
    financePath.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "bsns_year": ["2025", "2025", "2024"],
            "reprt_code": ["11013", "11013", "11011"],
            "fs_div": ["CFS", "OFS", "CFS"],
            "rcept_no": ["old-cfs", "old-ofs", "old-annual"],
            "account_nm": ["매출액", "매출액", "매출액"],
        }
    ).write_parquet(financePath)

    class FakeClient:
        exhausted = False

        async def getDf(self, endpoint, params, listKey="list"):
            if params["fs_div"] != "CFS":
                return pl.DataFrame()
            return pl.DataFrame(
                {
                    "corp_code": [params["corp_code"]],
                    "bsns_year": [params["bsns_year"]],
                    "reprt_code": [params["reprt_code"]],
                    "fs_div": [params["fs_div"]],
                    "rcept_no": ["new-cfs"],
                    "account_nm": ["매출액"],
                }
            )

    count = asyncio.run(
        _collectFinance(
            "005930",
            "00126380",
            "삼성전자",
            FakeClient(),
            incremental=True,
            targetPeriods=[("2025", "11013")],
        )
    )

    assert count == 1
    result = pl.read_parquet(financePath)
    rcepts = set(result["rcept_no"].to_list())
    assert "new-cfs" in rcepts
    assert "old-cfs" not in rcepts
    assert "old-ofs" in rcepts
    assert "old-annual" in rcepts


def test_collect_finance_api_failure_preserves_existing_file(tmp_path, monkeypatch) -> None:
    """한 요청이라도 실패하면 앞서 받은 frame을 부분 저장하지 않는다."""
    import asyncio

    import polars as pl
    import pytest

    import dartlab
    from dartlab.core.dartClient import DartApiError
    from dartlab.gather.dart.batch import _collectFinance

    monkeypatch.setattr(dartlab.config, "dataDir", str(tmp_path))
    financePath = tmp_path / "dart" / "finance" / "005930.parquet"
    financePath.parent.mkdir(parents=True)
    original = pl.DataFrame(
        {
            "bsns_year": ["2024"],
            "reprt_code": ["11011"],
            "fs_div": ["CFS"],
            "rcept_no": ["old"],
            "account_nm": ["매출액"],
        }
    )
    original.write_parquet(financePath)

    class FakeClient:
        exhausted = False
        calls = 0

        async def getDf(self, endpoint, params, listKey="list"):
            self.calls += 1
            if self.calls == 2:
                raise DartApiError("800", "시스템 점검")
            return pl.DataFrame(
                {
                    "corp_code": [params["corp_code"]],
                    "bsns_year": [params["bsns_year"]],
                    "reprt_code": [params["reprt_code"]],
                    "fs_div": [params["fs_div"]],
                    "rcept_no": ["new"],
                    "account_nm": ["매출액"],
                }
            )

    with pytest.raises(DartApiError, match=r"\[800\] 시스템 점검"):
        asyncio.run(
            _collectFinance(
                "005930",
                "00126380",
                "삼성전자",
                FakeClient(),
                targetPeriods=[("2025", "11013")],
            )
        )

    assert pl.read_parquet(financePath).to_dicts() == original.to_dicts()


def test_collect_report_target_period_refreshes_existing_api_type(tmp_path, monkeypatch) -> None:
    """report 정정 재수집은 같은 apiType/기간만 교체한다."""
    import asyncio

    import polars as pl

    import dartlab
    from dartlab.gather.dart.batch import _collectReport

    monkeypatch.setattr(dartlab.config, "dataDir", str(tmp_path))
    reportPath = tmp_path / "dart" / "report" / "005930.parquet"
    reportPath.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "year": ["2025", "2025", "2024"],
            "quarter": ["1분기", "1분기", "4분기"],
            "apiType": ["dividend", "employee", "dividend"],
            "rcept_no": ["old-dividend", "old-employee", "old-annual"],
            "stockCode": ["005930", "005930", "005930"],
        }
    ).write_parquet(reportPath)

    class FakeClient:
        exhausted = False

        async def getDf(self, endpoint, params, listKey="list"):
            if endpoint != "alotMatter.json":
                return pl.DataFrame()
            return pl.DataFrame(
                {
                    "corp_code": [params["corp_code"]],
                    "bsns_year": [params["bsns_year"]],
                    "reprt_code": [params["reprt_code"]],
                    "rcept_no": ["new-dividend"],
                }
            )

    count = asyncio.run(
        _collectReport(
            "005930",
            "00126380",
            "삼성전자",
            FakeClient(),
            incremental=True,
            targetPeriods=[("2025", "11013")],
        )
    )

    assert count == 1
    result = pl.read_parquet(reportPath)
    rcepts = set(result["rcept_no"].to_list())
    assert "new-dividend" in rcepts
    assert "old-dividend" not in rcepts
    assert "old-employee" in rcepts
    assert "old-annual" in rcepts
