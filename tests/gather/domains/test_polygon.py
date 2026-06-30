"""dartlab.gather.domains.polygon mirror — fetchGroupedDaily 단위 테스트 (P-G7).

룰 7 (src↔tests 1:1 mirror) 슬롯 + grouped-daily 파싱 계약 검증. 주입 fake httpx.Client 로
네트워크 없이: OK 파싱(ticker 대문자·date 정규화·volume 반올림 int)·404 빈·비OK status 빈·빈 apiKey raise.
"""

from __future__ import annotations

import importlib

import polars as pl
import pytest

pytestmark = pytest.mark.unit


class _FakeResp:
    """httpx.Response 최소 더블 — status_code·raise_for_status·json 만."""

    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        # 4xx/5xx 면 예외 — 단 polygon 코드는 404 를 raise 전에 가로채므로 본 테스트는 미발화.
        if self.status_code >= 400:
            raise AssertionError(f"unexpected raise_for_status on {self.status_code}")

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    """주입용 동기 client — get(url, params=) 1회 응답 고정. own=False 라 close 미호출."""

    def __init__(self, resp: _FakeResp) -> None:
        self._resp = resp
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, params: dict | None = None) -> _FakeResp:
        self.calls.append((url, params or {}))
        return self._resp

    def close(self) -> None:  # pragma: no cover - own=False 라 안 불림
        pass


def test_smoke_import() -> None:
    """``dartlab.gather.domains.polygon`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.polygon")


def test_grouped_daily_parses_results() -> None:
    """OK 응답 → ticker 대문자·date(YYYYMMDD)·OHLCV·volume 반올림 int 로 정규화한다."""
    from dartlab.gather.domains import polygon

    resp = _FakeResp(
        payload={
            "status": "OK",
            "results": [
                {"T": "aapl", "o": 1.0, "h": 2.0, "l": 0.5, "c": 1.5, "v": 1000.4},
                {"T": "msft", "o": 3.0, "h": 4.0, "l": 2.5, "c": 3.5, "v": 2000.6},
                {"T": None, "c": 9.0},  # ticker 없음 → 스킵
                {"T": "skip", "c": None},  # close 없음 → 스킵
            ],
        }
    )
    client = _FakeClient(resp)

    df = polygon.fetchGroupedDaily("2026-06-22", apiKey="k", client=client)

    assert isinstance(df, pl.DataFrame)
    assert df.height == 2
    assert df.columns == ["ticker", "date", "open", "high", "low", "close", "volume"]
    assert df["ticker"].to_list() == ["AAPL", "MSFT"]
    assert df["date"].to_list() == ["20260622", "20260622"]
    assert df["volume"].to_list() == [1000, 2001]  # 반올림 int
    # date 는 '-' 제거해 ISO 로 URL 구성.
    assert client.calls[0][0].endswith("/2026-06-22")
    assert client.calls[0][1]["adjusted"] == "true"


def test_grouped_daily_class_share_normalized_to_sec_dash() -> None:
    """클래스주 점 구분자(BRK.B) → SEC 대시(BRK-B) 정규화. 유니버스(SEC)·runtime 키 일치 보장."""
    from dartlab.gather.domains import polygon

    resp = _FakeResp(
        payload={
            "status": "OK",
            "results": [
                {"T": "BRK.B", "o": 400.0, "h": 410.0, "l": 399.0, "c": 405.0, "v": 100.0},
                {"T": "BF.A", "o": 30.0, "h": 31.0, "l": 29.0, "c": 30.5, "v": 50.0},
            ],
        }
    )
    df = polygon.fetchGroupedDaily("20260629", apiKey="k", client=_FakeClient(resp))
    assert df["ticker"].to_list() == ["BRK-B", "BF-A"]  # 점 → 대시(SEC convention)


def test_grouped_daily_404_returns_empty() -> None:
    """404(미확정/휴장일) → 빈 DataFrame (raise 아님)."""
    from dartlab.gather.domains import polygon

    df = polygon.fetchGroupedDaily("20260101", apiKey="k", client=_FakeClient(_FakeResp(status_code=404)))
    assert df.is_empty()


def test_grouped_daily_non_ok_status_returns_empty() -> None:
    """status 가 OK/DELAYED 아님 → 빈 DataFrame."""
    from dartlab.gather.domains import polygon

    resp = _FakeResp(payload={"status": "ERROR", "results": []})
    df = polygon.fetchGroupedDaily("20260622", apiKey="k", client=_FakeClient(resp))
    assert df.is_empty()


def test_grouped_daily_empty_apikey_raises() -> None:
    """apiKey 빈 문자열 → ValueError (도메인은 env 미참조, 호출자 주입 강제)."""
    from dartlab.gather.domains import polygon

    with pytest.raises(ValueError, match="apiKey"):
        polygon.fetchGroupedDaily("20260622", apiKey="")
