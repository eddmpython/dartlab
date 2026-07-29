"""Phase D — GDELT GKG parser + market filter + slot iterator 단위 테스트.

network-free unit test — httpx mock 으로 GKG CSV bytes 주입.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone

import polars as pl
import pytest

from dartlab.gather.sources import gdelt
from dartlab.gather.types import SourceUnavailableError

pytestmark = pytest.mark.unit


def _gkgCsvBytes(rows: list[list[str]]) -> bytes:
    """27-컬럼 tab-separated CSV bytes 빌드."""
    lines = ["\t".join(row) for row in rows]
    return ("\n".join(lines)).encode("utf-8")


def _zipBytes(csvBytes: bytes) -> bytes:
    """CSV bytes → ZIP bytes (in-memory)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("20260527120000.gkg.csv", csvBytes)
    return buf.getvalue()


def test_tone_to_sentiment_thresholds() -> None:
    assert gdelt._toneToSentiment(0.0) == (0.0, "neutral")
    s, lab = gdelt._toneToSentiment(5.0)
    assert s == 0.5 and lab == "pos"
    s, lab = gdelt._toneToSentiment(-3.0)
    assert s == -0.3 and lab == "neg"
    # clamp
    s, _ = gdelt._toneToSentiment(15.0)
    assert s == 1.0


def test_domain_to_market_mapping() -> None:
    assert gdelt._domainToMarket("yna.co.kr") == "KR"
    assert gdelt._domainToMarket("nikkei.jp") == "JP"
    assert gdelt._domainToMarket("xinhuanet.com.cn") == "CN"
    assert gdelt._domainToMarket("nytimes.com") == "US"
    assert gdelt._domainToMarket("aljazeera.qa") == "GLOBAL"


def test_parse_v2tone() -> None:
    assert gdelt._parseV2Tone("3.5,5.2,1.7,6.9,8.1,1.2,250") == 3.5
    assert gdelt._parseV2Tone("") == 0.0
    assert gdelt._parseV2Tone("invalid") == 0.0


def test_parse_v2themes_topn() -> None:
    raw = "ECON_BANKRUPTCY,123;ECON_INFLATION,456;ECON_BANKRUPTCY,789;ECON_TAX,999"
    themes = gdelt._parseV2Themes(raw, topN=3)
    assert themes == ["ECON_BANKRUPTCY", "ECON_INFLATION", "ECON_TAX"]


def test_iter_gdelt_slots_step() -> None:
    start = datetime(2026, 5, 27, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 27, 23, 45, tzinfo=timezone.utc)
    slots15 = gdelt.iterGdeltSlots(start, end, stepMinutes=15)
    assert len(slots15) == 96
    slots360 = gdelt.iterGdeltSlots(start, end, stepMinutes=360)
    assert len(slots360) == 4


def test_fetch_gdelt_gkg_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """httpx mock — KR + US row 1 개씩 + filter 동작."""
    row_kr = [
        "rec1",
        "20260527120000",
        "WEB",
        "yna.co.kr",
        "https://yna.co.kr/article1",
        "",
        "",
        "",
        "ECON_RATE,100;POLITIC,200",
        "",
        "",
        "",
        "",
        "",
        "",
        "2.5,3.0,0.5,3.5,4.0,1.0,150",  # V2Tone
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "ko;ko",
        "",
    ]
    row_us = [
        "rec2",
        "20260527120000",
        "WEB",
        "nytimes.com",
        "https://nytimes.com/article1",
        "",
        "",
        "",
        "ECON_BANKRUPTCY,100",
        "",
        "",
        "",
        "",
        "",
        "",
        "-4.0,1.0,5.0,6.0,3.0,0.5,200",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "en;en",
        "",
    ]
    csvBytes = _gkgCsvBytes([row_kr, row_us])
    zipped = _zipBytes(csvBytes)

    class FakeResp:
        status_code = 200
        content = zipped

        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return FakeResp()

    import httpx as _httpx

    monkeypatch.setattr(_httpx, "Client", FakeClient)

    df = gdelt.fetchGdeltGkg(datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc))
    assert df.height == 2
    assert set(df["market"].to_list()) == {"KR", "US"}
    assert df.filter(pl.col("market") == "KR")["sentiment_score"][0] == 0.25
    assert df.filter(pl.col("market") == "US")["sentiment_label"][0] == "neg"


def test_fetch_gdelt_market_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """markets=['US'] 필터 시 KR row 제외."""
    row_kr = [
        "rec1",
        "20260527120000",
        "WEB",
        "yna.co.kr",
        "https://yna.co.kr/a",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "0.0,0.0,0.0,0.0,0.0,0.0,100",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "ko;ko",
        "",
    ]
    row_us = row_kr.copy()
    row_us[3] = "nytimes.com"
    row_us[4] = "https://nytimes.com/b"

    zipped = _zipBytes(_gkgCsvBytes([row_kr, row_us]))

    class FakeResp:
        status_code = 200
        content = zipped

        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return FakeResp()

    import httpx as _httpx

    monkeypatch.setattr(_httpx, "Client", FakeClient)

    df = gdelt.fetchGdeltGkg(datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc), markets=["US"])
    assert df.height == 1
    assert df["market"][0] == "US"


def test_fetch_gdelt_404_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """404 (슬롯 미존재) 시 빈 DataFrame + schema 유지."""

    class FakeResp:
        status_code = 404
        content = b""

        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return FakeResp()

    import httpx as _httpx

    monkeypatch.setattr(_httpx, "Client", FakeClient)

    df = gdelt.fetchGdeltGkg(datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc))
    assert df.height == 0
    assert "sentiment_score" in df.columns
    assert "description" in df.columns  # canonical 17컬럼 통일


def test_fetch_gdelt_transport_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """슬롯 공급 장애는 정상 0행으로 위장하지 않는다."""
    import httpx as _httpx

    upstream = OSError("network down")

    class FakeClient:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            raise upstream

    monkeypatch.setattr(_httpx, "Client", FakeClient)

    with pytest.raises(SourceUnavailableError, match="GDELT GKG") as excInfo:
        gdelt.fetchGdeltGkg(datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc))
    assert excInfo.value.__cause__ is upstream


def test_fetch_gdelt_corrupt_zip_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """깨진 ZIP은 빈 슬롯이 아니라 artifact 오류다."""
    import httpx as _httpx

    class FakeResp:
        status_code = 200
        content = b"not zip"

        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return FakeResp()

    monkeypatch.setattr(_httpx, "Client", FakeClient)

    with pytest.raises(SourceUnavailableError, match="ZIP"):
        gdelt.fetchGdeltGkg(datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc))


# ── GDELT DOC 2.0 (질의 기반 뉴스) — sync 별도빌드에서 gather 로 환원 ────────────────


def test_fetch_gdelt_doc_empty_input() -> None:
    out = gdelt.fetchGdeltDoc({})
    assert isinstance(out, pl.DataFrame)
    assert out.height == 0


def test_fetch_gdelt_doc_parses_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    """DOC API 응답 → naver 호환 archive df(+__code). online fetch=gather SSOT 회귀 가드."""
    import httpx as _httpx

    article = {
        "url": "https://news.example.com/a",
        "title": "삼성전자 신제품 발표",
        "seendate": "20260115T120000Z",
        "domain": "news.example.com",
    }

    class _Resp:
        status_code = 200

        def json(self):
            return {"articles": [article]}

    class _Client:
        def __init__(self, *a, **k): ...

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(_httpx, "Client", _Client)
    monkeypatch.setattr(gdelt.time, "sleep", lambda *_a, **_k: None)  # perQuery sleep 즉시

    df = gdelt.fetchGdeltDoc({"삼성전자": "005930"}, years=1)
    assert df.height == 1
    row = df.row(0, named=True)
    assert row["title"] == "삼성전자 신제품 발표"
    assert row["__code"] == "005930"
    assert row["market"] == "KR"
    assert row["query"] == "삼성전자"
    assert row["description"] == ""  # DOC 트랙은 스니펫 없음


def test_fetch_gdelt_doc_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """DOC 질의 장애는 회사별 정상 무결과로 강등하지 않는다."""
    import httpx as _httpx

    class _Resp:
        status_code = 503

    class _Client:
        def __init__(self, *a, **k): ...

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(_httpx, "Client", _Client)
    monkeypatch.setattr(gdelt.time, "sleep", lambda *_a, **_k: None)

    with pytest.raises(SourceUnavailableError, match="status=503"):
        gdelt.fetchGdeltDoc({"삼성전자": "005930"}, years=1)
