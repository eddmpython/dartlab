"""allFilingsContent 계약. 주입 fake client, 네트워크/OOM 무관.

getFilingBody: 200+본문=ok · 200+빈/404=no_body(final) · 403/5xx/예외=error(retry). DART fetch_status 동형.
글이 아닌 형식과 풀어낸 크기 상한을 넘는 문서는 받지 않고 no_body.
fillContentDay: 하루치 본문을 메모리에 다 쌓지 않고 묶음씩 row group 으로 덜어 쓴다.
"""

from __future__ import annotations

import contextlib

import httpx
import pytest

pytestmark = pytest.mark.unit


class _Resp:
    """주입용 fake 응답. iter_bytes 는 풀어낸 바이트를 조각으로 준다."""

    def __init__(
        self,
        status_code: int,
        text: str = "",
        *,
        mediaType: str = "text/html; charset=utf-8",
        encoding: str = "utf-8",
        data: bytes | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = {"content-type": mediaType}
        self.encoding = encoding
        self._data = text.encode("utf-8") if data is None else data

    def iter_bytes(self):
        for start in range(0, len(self._data), 1024):
            yield self._data[start : start + 1024]


class _Client:
    """주입용 fake httpx client. stream() 이 고정 응답 또는 예외."""

    def __init__(self, resp: _Resp | Exception) -> None:
        self._resp = resp

    def stream(self, method: str, url: str, **_):
        if isinstance(self._resp, Exception):
            raise self._resp
        return contextlib.nullcontext(self._resp)


def test_ok_when_200_with_body():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    body, status = getFilingBody("http://x/doc.htm", client=_Client(_Resp(200, "<html>본문</html>")))
    assert status == "ok"
    assert body == "<html>본문</html>"


def test_ok_decodes_large_body_from_many_chunks():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    text = "가" * 5000
    body, status = getFilingBody("http://x", client=_Client(_Resp(200, text)))
    assert status == "ok" and body == text


def test_unknown_charset_falls_back_to_utf8():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    resp = _Resp(200, "<html>본문</html>", encoding="no-such-codec")
    assert getFilingBody("http://x", client=_Client(resp)) == ("<html>본문</html>", "ok")


def test_no_body_when_200_empty_or_404_or_missing_url():
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    assert getFilingBody("http://x", client=_Client(_Resp(200, "   ")))[1] == "no_body"  # 빈 body
    assert getFilingBody("http://x", client=_Client(_Resp(404)))[1] == "no_body"  # 삭제/이동
    assert getFilingBody("", client=_Client(_Resp(200, "x")))[1] == "no_body"  # url 부재


@pytest.mark.parametrize("mediaType", ["application/pdf", "image/png", "application/zip", "APPLICATION/PDF; x=1"])
def test_no_body_for_non_text_media_type_without_reading_body(mediaType):
    """PDF 등은 글로 풀면 깨진 글자뿐이다. 받지 않고 no_body 로 닫는다(20250513 ARS PDF 62MB)."""
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    resp = _Resp(200, "x", mediaType=mediaType)
    resp.iter_bytes = lambda: pytest.fail("글이 아닌 형식의 본문을 읽었다")
    assert getFilingBody("http://x", client=_Client(resp)) == (None, "no_body")


def test_no_body_when_decoded_size_exceeds_cap(monkeypatch):
    """gzip 1.3MB 가 23MB 로 풀리는 문서가 있어 풀어낸 바이트로 잰다. 상한을 넘으면 더 읽지 않는다."""
    from dartlab.gather.edgar import allFilingsContent as mod

    monkeypatch.setattr(mod, "_MAX_BODY_BYTES", 2048)
    seen: list[int] = []

    class _Big(_Resp):
        def iter_bytes(self):
            for _ in range(100):
                seen.append(1)
                yield b"a" * 1024

    assert mod.getFilingBody("http://x", client=_Client(_Big(200))) == (None, "no_body")
    assert len(seen) == 3  # 3번째 조각에서 상한을 넘자 멈춘다


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


def _fakeFetch(monkeypatch, mod, bodies: dict[str, tuple[str | None, str]]):
    """url 끝 번호로 (본문, 상태)를 주는 getFilingBody 로 바꾸고 불린 url 목록을 돌려준다."""
    calls: list[str] = []

    def fake(url, *, client, reasons=None, **_):
        calls.append(url)
        return bodies.get(url, (f"본문 {url}", "ok"))

    monkeypatch.setattr(mod, "getFilingBody", fake)
    monkeypatch.setattr(mod, "_PACE_SECONDS", 0)
    return calls


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


def test_fill_content_day_writes_in_row_groups_not_all_in_memory(monkeypatch, tmp_path):
    """본문이 묶음 한도를 넘을 때마다 row group 으로 덜어 쓴다. 하루치를 한 번에 메모리에 두지 않는다."""
    import polars as pl
    import pyarrow.parquet as pq

    from dartlab.gather.edgar import allFilingsContent as mod

    _fakeFetch(monkeypatch, mod, {})
    monkeypatch.setattr(mod, "_FLUSH_ROWS", 2)
    out = mod.fillContentDay(_dayMeta(5), tmp_path / "d.parquet")
    assert out.height == 5 and set(out["fetch_status"].to_list()) == {"ok"}
    meta = pq.ParquetFile(tmp_path / "d.parquet").metadata
    assert meta.num_rows == 5 and meta.num_row_groups == 3  # 2 + 2 + 1
    stored = pl.read_parquet(tmp_path / "d.parquet")
    assert sorted(stored["accessionNo"].to_list()) == [f"a{i:03d}" for i in range(5)]
    assert stored.filter(pl.col("accessionNo") == "a002")["content_raw"][0] == "본문 http://x/2"


def test_fill_content_day_flushes_by_chars(monkeypatch, tmp_path):
    """행이 적어도 본문 글자가 한도를 넘으면 덜어 쓴다(23MB 문서 몇 건이면 행 수 한도에 닿기 전에 메모리가 찬다)."""
    import pyarrow.parquet as pq

    from dartlab.gather.edgar import allFilingsContent as mod

    _fakeFetch(monkeypatch, mod, {f"http://x/{i}": ("가" * 100, "ok") for i in range(4)})
    monkeypatch.setattr(mod, "_FLUSH_CHARS", 150)
    mod.fillContentDay(_dayMeta(4), tmp_path / "d.parquet")
    assert pq.ParquetFile(tmp_path / "d.parquet").metadata.num_row_groups == 2  # 100,100 | 100,100


def test_fill_content_day_keeps_ok_rows_and_retries_only_errors(monkeypatch, tmp_path):
    """기존 파일의 ok/no_body 는 본문 그대로 보존하고 error·신규만 다시 받는다(idempotent + diff retry)."""
    import polars as pl

    from dartlab.gather.edgar import allFilingsContent as mod

    path = tmp_path / "d.parquet"
    pl.DataFrame(
        {
            "accessionNo": ["a000", "a001", "a002"],
            "stockCode": ["AAPL"] * 3,
            "filingDate": ["20260105"] * 3,
            "content_raw": ["옛 본문", None, None],
            "fetch_status": ["ok", "error", "no_body"],
        }
    ).write_parquet(path)
    calls = _fakeFetch(monkeypatch, mod, {})
    out = mod.fillContentDay(_dayMeta(4), path)  # a003 은 신규
    assert calls == ["http://x/1", "http://x/3"]  # a000(ok)·a002(no_body)는 받지 않는다
    stored = pl.read_parquet(path).sort("accessionNo")
    assert stored["content_raw"].to_list() == ["옛 본문", "본문 http://x/1", None, "본문 http://x/3"]
    assert stored["fetch_status"].to_list() == ["ok", "ok", "no_body", "ok"]
    assert out.sort("accessionNo")["fetch_status"].to_list() == ["ok", "ok", "no_body", "ok"]


def test_fill_content_day_drops_duplicate_meta_rows(monkeypatch, tmp_path):
    """같은 accessionNo 가 메타에 둘이면 한 번만 받고 한 행만 쓴다."""
    import polars as pl

    from dartlab.gather.edgar import allFilingsContent as mod

    calls = _fakeFetch(monkeypatch, mod, {})
    meta = pl.concat([_dayMeta(2), _dayMeta(2)])
    out = mod.fillContentDay(meta, tmp_path / "d.parquet")
    assert out.height == 2 and len(calls) == 2


def test_fill_content_day_empty_meta_writes_readable_empty_file(tmp_path):
    import polars as pl

    from dartlab.gather.edgar import allFilingsContent as mod

    out = mod.fillContentDay(_dayMeta(0), tmp_path / "d.parquet")
    assert out.height == 0
    stored = pl.read_parquet(tmp_path / "d.parquet")
    assert stored.height == 0 and stored.columns == list(mod._CONTENT_COLS)


def test_fill_content_day_removes_temp_file_when_fetch_raises(monkeypatch, tmp_path):
    """수집이 예외로 끊기면 쓰다 만 임시 파일을 남기지 않고 기존 파일도 건드리지 않는다."""
    from dartlab.gather.edgar import allFilingsContent as mod

    def boom(url, *, client, reasons=None, **_):
        raise RuntimeError("중간 실패")

    monkeypatch.setattr(mod, "getFilingBody", boom)
    path = tmp_path / "out" / "d.parquet"
    with pytest.raises(RuntimeError):
        mod.fillContentDay(_dayMeta(3), path)
    assert list(path.parent.iterdir()) == []
