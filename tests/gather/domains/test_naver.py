"""dartlab.gather.domains.naver mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import asyncio
import importlib
from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.domains.naver`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.naver")


def test_revenue_consensus_failure_is_not_empty_data() -> None:
    """요청 실패를 정상 컨센서스 0건으로 위장하지 않는다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class FailingClient:
        async def get(self, *_args, **_kwargs):
            raise OSError("network down")

    with pytest.raises(SourceUnavailableError, match="요청 실패") as excInfo:
        asyncio.run(naver.fetchRevenueConsensus("005930", FailingClient()))

    assert isinstance(excInfo.value.__cause__, OSError)


def test_revenue_consensus_schema_failure_is_explicit() -> None:
    """존재하는 응답의 schema 손상은 빈 목록이 아니다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class Response:
        def json(self):
            return {"financeInfo": {"trTitleList": {}, "rowList": []}}

    class Client:
        async def get(self, *_args, **_kwargs):
            return Response()

    with pytest.raises(SourceUnavailableError, match="title/row schema"):
        asyncio.run(naver.fetchRevenueConsensus("005930", Client()))


def test_revenue_consensus_does_not_publish_missing_revenue_as_zero() -> None:
    """영업이익만 있는 기간에 가짜 매출 0.0을 발행하지 않는다."""
    from dartlab.gather.domains import naver

    class Response:
        def json(self):
            return {
                "financeInfo": {
                    "trTitleList": [{"key": "2026", "isConsensus": "Y"}],
                    "rowList": [
                        {
                            "title": "영업이익",
                            "columns": {"2026": {"value": "100"}},
                        }
                    ],
                }
            }

    class Client:
        async def get(self, *_args, **_kwargs):
            return Response()

    assert asyncio.run(naver.fetchRevenueConsensus("005930", Client())) == []


def test_sector_per_failure_is_not_missing_data() -> None:
    """업종 PER endpoint 실패를 정상 업종정보 부재 None으로 위장하지 않는다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class FailingClient:
        async def get(self, *_args, **_kwargs):
            raise OSError("network down")

    with pytest.raises(SourceUnavailableError, match="요청 실패") as excInfo:
        asyncio.run(naver.fetchSectorPer("005930", FailingClient()))

    assert isinstance(excInfo.value.__cause__, OSError)


def test_fetch_flow_trend_paginates_by_bizdate() -> None:
    """Naver front-api flow 는 end+1 cursor 로 시작해 start 전에서 멈춘다."""
    from dartlab.gather.domains import naver

    class FakeResponse:
        def __init__(self, rows):
            self._rows = rows

        def json(self):
            return {"isSuccess": True, "result": self._rows}

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, **kwargs):
            params = kwargs.get("params") or {}
            self.calls.append((url, params))
            cursor = params.get("bizdate")
            if cursor == "20200201":
                return FakeResponse(
                    [
                        {
                            "bizdate": "20200131",
                            "foreignerPureBuyQuant": "-3,776,715",
                            "foreignerHoldRatio": "57.19%",
                            "organPureBuyQuant": "+1,648,681",
                            "individualPureBuyQuant": "+2,215,461",
                        },
                        {
                            "bizdate": "20200130",
                            "foreignerPureBuyQuant": "+10",
                            "foreignerHoldRatio": "57.10%",
                            "organPureBuyQuant": "-20",
                            "individualPureBuyQuant": "+10",
                        },
                    ]
                )
            if cursor == "20200130":
                return FakeResponse(
                    [
                        {
                            "bizdate": "20200129",
                            "foreignerPureBuyQuant": "+30",
                            "foreignerHoldRatio": "57.00%",
                            "organPureBuyQuant": "-40",
                            "individualPureBuyQuant": "+10",
                        },
                        {
                            "bizdate": "20200128",
                            "foreignerPureBuyQuant": "+50",
                            "foreignerHoldRatio": "56.90%",
                            "organPureBuyQuant": "-60",
                            "individualPureBuyQuant": "+10",
                        },
                    ]
                )
            return FakeResponse([])

    client = FakeClient()
    rows = asyncio.run(
        naver.fetchFlow(
            "005930",
            client,
            start="2020-01-29",
            end="2020-01-31",
            pageSize=2,
        )
    )

    assert rows is not None
    assert [row["date"] for row in rows] == ["20200131", "20200130", "20200129"]
    assert rows[0]["foreignNet"] == -3776715.0
    assert client.calls[0][0] == naver._FLOW_TREND_URL
    assert client.calls[0][1]["bizdate"] == "20200201"
    assert client.calls[0][1]["pageSize"] == 2


def test_fetch_flow_trend_auto_pages_historical_range() -> None:
    """기간 조회는 pageSize 입력 없이 Naver 최대 단위로 자동 조회한다."""
    from dartlab.gather.domains import naver

    class FakeResponse:
        def json(self):
            return {
                "isSuccess": True,
                "result": [
                    {
                        "bizdate": "20200131",
                        "foreignerPureBuyQuant": "1",
                        "foreignerHoldRatio": "57.19%",
                        "organPureBuyQuant": "2",
                        "individualPureBuyQuant": "-3",
                    },
                    {
                        "bizdate": "20200130",
                        "foreignerPureBuyQuant": "4",
                        "foreignerHoldRatio": "57.10%",
                        "organPureBuyQuant": "5",
                        "individualPureBuyQuant": "-9",
                    },
                ],
            }

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, **kwargs):
            self.calls.append((url, kwargs.get("params") or {}))
            return FakeResponse()

    client = FakeClient()
    rows = asyncio.run(
        naver.fetchFlow(
            "005930",
            client,
            start="2020-01-30",
            end="2020-01-31",
        )
    )

    assert rows is not None
    assert [row["date"] for row in rows] == ["20200131", "20200130"]
    assert client.calls[0][1]["bizdate"] == "20200201"
    assert client.calls[0][1]["pageSize"] == 50


def test_fetch_flow_default_latest_stays_small() -> None:
    """기본 최신 조회는 사용자 실수로 장기 백필하지 않도록 5건만 요청한다."""
    from dartlab.gather.domains import naver

    class FakeResponse:
        def json(self):
            return {
                "isSuccess": True,
                "result": [
                    {
                        "bizdate": f"202606{i:02d}",
                        "foreignerPureBuyQuant": "1",
                        "foreignerHoldRatio": "50.00%",
                        "organPureBuyQuant": "0",
                        "individualPureBuyQuant": "0",
                    }
                    for i in range(10, 5, -1)
                ],
            }

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, **kwargs):
            self.calls.append((url, kwargs.get("params") or {}))
            return FakeResponse()

    client = FakeClient()
    rows = asyncio.run(naver.fetchFlow("005930", client))

    assert rows is not None
    assert len(rows) == 5
    assert len(client.calls) == 1
    assert client.calls[0][1]["pageSize"] == 5


def test_fetch_flow_trend_passes_proxy_to_http_client() -> None:
    """proxy 옵션은 Naver trend HTTP 호출로 전달한다."""
    from dartlab.gather.domains import naver

    class FakeResponse:
        def json(self):
            return {
                "isSuccess": True,
                "result": [
                    {
                        "bizdate": "20260611",
                        "foreignerPureBuyQuant": "1",
                        "foreignerHoldRatio": "50.00%",
                        "organPureBuyQuant": "0",
                        "individualPureBuyQuant": "0",
                    }
                ],
            }

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return FakeResponse()

    client = FakeClient()
    rows = asyncio.run(naver.fetchFlow("005930", client, proxy="http://proxy.example:8080"))

    assert rows is not None
    assert len(rows) == 1
    assert client.calls[0][1]["proxy"] == "http://proxy.example:8080"


def test_fetch_flow_trend_large_page_size_splits_to_server_cap() -> None:
    """큰 pageSize 요청은 서버 한도 50건 단위로 나눠 최신 N건을 채운다."""
    from dartlab.gather.domains import naver

    def make_rows(offset: int, count: int):
        base = date(2026, 6, 10) - timedelta(days=offset)
        return [
            {
                "bizdate": (base - timedelta(days=i)).strftime("%Y%m%d"),
                "foreignerPureBuyQuant": str(offset + i),
                "foreignerHoldRatio": "50.00%",
                "organPureBuyQuant": "0",
                "individualPureBuyQuant": "0",
            }
            for i in range(count)
        ]

    class FakeResponse:
        def __init__(self, rows):
            self._rows = rows

        def json(self):
            return {"isSuccess": True, "result": self._rows}

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, **kwargs):
            params = kwargs.get("params") or {}
            self.calls.append((url, params))
            return FakeResponse(make_rows(0 if len(self.calls) == 1 else 50, 50))

    client = FakeClient()
    rows = asyncio.run(naver.fetchFlow("005930", client, pageSize=75))

    assert rows is not None
    assert len(rows) == 75
    assert len(client.calls) == 2
    assert [call[1]["pageSize"] for call in client.calls] == [50, 50]


def test_fetch_flow_all_history_runs_until_source_exhausted() -> None:
    """all=True 는 limit 없이 서버가 빈 페이지를 줄 때까지 자동 순회한다."""
    from dartlab.gather.domains import naver

    def make_rows(offset: int, count: int):
        base = date(2026, 6, 10) - timedelta(days=offset)
        return [
            {
                "bizdate": (base - timedelta(days=i)).strftime("%Y%m%d"),
                "foreignerPureBuyQuant": str(offset + i),
                "foreignerHoldRatio": "50.00%",
                "organPureBuyQuant": "0",
                "individualPureBuyQuant": "0",
            }
            for i in range(count)
        ]

    class FakeResponse:
        def __init__(self, rows):
            self._rows = rows

        def json(self):
            return {"isSuccess": True, "result": self._rows}

    class FakeClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, **kwargs):
            params = kwargs.get("params") or {}
            self.calls.append((url, params))
            idx = len(self.calls)
            if idx == 1:
                return FakeResponse(make_rows(0, 50))
            if idx == 2:
                return FakeResponse(make_rows(50, 50))
            return FakeResponse(make_rows(100, 10))

    client = FakeClient()
    rows = asyncio.run(naver.fetchFlow("005930", client, full=True))

    assert rows is not None
    assert len(rows) == 110
    assert len(client.calls) == 3
    assert [call[1]["pageSize"] for call in client.calls] == [50, 50, 50]


def test_fetch_flow_network_failure_is_not_empty_data() -> None:
    """trend와 integration 요청이 모두 실패하면 typed source 오류를 전달한다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class FailingClient:
        async def get(self, *args, **kwargs):
            raise SourceUnavailableError("network down")

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(naver.fetchFlow("005930", FailingClient()))

    assert isinstance(excInfo.value.__cause__, SourceUnavailableError)


def test_fetch_flow_valid_empty_response_returns_none() -> None:
    """두 endpoint가 유효한 빈 schema를 반환하면 정상 무데이터로 판정한다."""
    from dartlab.gather.domains import naver

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return FakeResponse({"isSuccess": True, "result": []})
            return FakeResponse({"dealTrendInfos": []})

    assert asyncio.run(naver.fetchFlow("005930", FakeClient())) is None


def test_fetch_flow_malformed_number_raises() -> None:
    """유효하지 않은 수급 숫자를 0으로 바꾸지 않는다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return FakeResponse(
                    {
                        "isSuccess": True,
                        "result": [
                            {
                                "bizdate": "20260102",
                                "foreignerPureBuyQuant": "broken",
                                "organPureBuyQuant": "1",
                                "individualPureBuyQuant": "-1",
                                "foreignerHoldRatio": "50%",
                            }
                        ],
                    }
                )
            return FakeResponse({"dealTrendInfos": []})

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(naver.fetchFlow("005930", FakeClient()))

    assert isinstance(excInfo.value.__cause__, SourceUnavailableError)


def test_fetch_history_network_and_schema_failures_raise() -> None:
    """Naver history의 네트워크 장애와 손상 행은 빈 list로 바뀌지 않는다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class FailingClient:
        async def get(self, *args, **kwargs):
            raise SourceUnavailableError("network down")

    with pytest.raises(SourceUnavailableError) as networkError:
        asyncio.run(naver.fetchHistory("005930", FailingClient()))
    assert isinstance(networkError.value.__cause__, SourceUnavailableError)

    class BadResponse:
        text = '<protocol><chartdata><item data="20260101|bad|110|90|105|1000" /></chartdata></protocol>'

    class BadClient:
        async def get(self, *args, **kwargs):
            return BadResponse()

    with pytest.raises(SourceUnavailableError) as schemaError:
        asyncio.run(naver.fetchHistory("005930", BadClient()))
    assert isinstance(schemaError.value.__cause__, ValueError)


def test_fetch_history_valid_empty_envelope_returns_empty() -> None:
    """유효한 chart envelope에 item이 없으면 정상 무데이터다."""
    from dartlab.gather.domains import naver

    class EmptyResponse:
        text = "<protocol><chartdata></chartdata></protocol>"

    class EmptyClient:
        async def get(self, *args, **kwargs):
            return EmptyResponse()

    assert asyncio.run(naver.fetchHistory("005930", EmptyClient())) == []


# --- fetchIntraday (당일 + 과거 세션 + 최근 거래일 폴백) ---


def _minute_item(dt14: str, price: float) -> dict:
    """네이버 분봉 API 항목 1 개 (localDateTime 14 자리)."""
    return {
        "localDateTime": dt14,
        "currentPrice": price,
        "openPrice": price,
        "highPrice": price + 10,
        "lowPrice": price - 10,
        "accumulatedTradingVolume": 100,
    }


class _MinuteResponse:
    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return self._rows


class _MinuteClient:
    """호출별 응답을 순서대로 돌려주는 fake. calls 에 (url, params) 기록."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def get(self, url, **kwargs):
        self.calls.append((url, kwargs.get("params")))
        idx = len(self.calls) - 1
        rows = self._responses[min(idx, len(self._responses) - 1)]
        return _MinuteResponse(rows)


def test_intraday_stamp_fills_and_normalizes() -> None:
    """날짜만이면 0900/1530 채우고, 구분자 제거, 12 자리는 통과."""
    from dartlab.gather.domains import naver

    assert naver._intradayStamp("2026-07-03", isEnd=False) == "202607030900"
    assert naver._intradayStamp("2026-07-03", isEnd=True) == "202607031530"
    assert naver._intradayStamp("2026-07-03T09:30", isEnd=False) == "202607030930"
    assert naver._intradayStamp("202607030930", isEnd=False) == "202607030930"
    assert naver._intradayStamp("bad", isEnd=False) == ""


def test_intraday_parse_rows_sorts_and_rejects_bad_schema() -> None:
    """정상 행은 정렬하고 결측/비-dict/schema 손상은 명시적으로 거부한다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    rows = naver._parseIntradayRows(
        [
            _minute_item("20260703091500", 71000.0),
            _minute_item("20260703090000", 70000.0),
        ]
    )
    assert [r["datetime"] for r in rows] == ["2026-07-03T09:00:00", "2026-07-03T09:15:00"]
    with pytest.raises(SourceUnavailableError, match="currentPrice"):
        naver._parseIntradayRows([{"localDateTime": "20260703093000", "currentPrice": None}])
    with pytest.raises(SourceUnavailableError, match="객체"):
        naver._parseIntradayRows(["not-a-dict"])
    with pytest.raises(SourceUnavailableError, match="배열"):
        naver._parseIntradayRows({"not": "list"})


def test_intraday_default_uses_plain_call() -> None:
    """start/end 미지정 = 당일. 파라미터 없는 단일 호출."""
    from dartlab.gather.domains import naver

    client = _MinuteClient([[_minute_item("20260706090000", 70000.0)]])
    rows = asyncio.run(naver.fetchIntraday("005930", client))

    assert len(rows) == 1
    assert len(client.calls) == 1
    assert client.calls[0][1] is None  # params 미부착


def test_intraday_explicit_start_sends_12digit_param() -> None:
    """start 지정 시 startDateTime 12 자리 파라미터 + 폴백 없이 1 회 호출."""
    from dartlab.gather.domains import naver

    client = _MinuteClient([[_minute_item("20260703090000", 70000.0)]])
    rows = asyncio.run(naver.fetchIntraday("005930", client, start="2026-07-03"))

    assert len(rows) == 1
    assert len(client.calls) == 1
    assert client.calls[0][1] == {"startDateTime": "202607030900"}


def test_intraday_fallback_to_latest_session_when_today_empty() -> None:
    """당일 빈 응답이면 소급 윈도우 조회 후 최근 거래일 세션만 반환."""
    from dartlab.gather.domains import naver

    client = _MinuteClient(
        [
            [],  # 1) 당일 = 빈 응답 (휴장/장전)
            [  # 2) 윈도우 조회 = 이전일 + 최근 거래일 섞임
                _minute_item("20260702093000", 69000.0),
                _minute_item("20260703090000", 70000.0),
                _minute_item("20260703091500", 71000.0),
            ],
        ]
    )
    rows = asyncio.run(naver.fetchIntraday("005930", client, fallbackDays=8))

    assert len(client.calls) == 2
    assert client.calls[0][1] is None  # 당일 plain
    assert "startDateTime" in client.calls[1][1]  # 폴백 윈도우
    # 최근 거래일(07-03) 세션만
    assert sorted({r["datetime"][:10] for r in rows}) == ["2026-07-03"]
    assert len(rows) == 2


def test_intraday_fallback_disabled_returns_empty() -> None:
    """fallbackDays=0 이면 당일 빈 응답에서 폴백하지 않는다."""
    from dartlab.gather.domains import naver

    client = _MinuteClient([[]])
    rows = asyncio.run(naver.fetchIntraday("005930", client, fallbackDays=0))

    assert rows == []
    assert len(client.calls) == 1


def test_intraday_market_and_code_guards() -> None:
    """KR 외 시장 / 6 자리 아닌 코드는 네트워크 없이 빈 리스트."""
    from dartlab.gather.domains import naver

    client = _MinuteClient([[_minute_item("20260706090000", 70000.0)]])
    with pytest.raises(ValueError, match="KR 시장"):
        asyncio.run(naver.fetchIntraday("005930", client, market="US"))
    with pytest.raises(ValueError, match="KR 종목코드"):
        asyncio.run(naver.fetchIntraday("12", client))
    assert len(client.calls) == 0


def test_fetch_price_network_failure_preserves_cause() -> None:
    """Naver price 요청 장애를 정상 무데이터로 바꾸지 않는다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class FailingClient:
        async def get(self, *args, **kwargs):
            raise SourceUnavailableError("network down")

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(naver.fetchPrice("005930", FailingClient()))

    assert isinstance(excInfo.value.__cause__, SourceUnavailableError)


def test_fetch_price_malformed_basic_schema_raises() -> None:
    """Naver basic JSON root 손상을 정상 무데이터로 바꾸지 않는다."""
    from dartlab.gather.domains import naver
    from dartlab.gather.types import SourceUnavailableError

    class BadResponse:
        def json(self):
            return []

    class BadClient:
        async def get(self, *args, **kwargs):
            return BadResponse()

    with pytest.raises(SourceUnavailableError, match="schema"):
        asyncio.run(naver.fetchPrice("005930", BadClient()))
