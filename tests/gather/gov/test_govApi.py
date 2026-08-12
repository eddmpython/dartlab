"""gov(공공데이터포털) raw fetch + normalize 계약 — 순수 변환 오프라인 검증."""

from __future__ import annotations

import httpx
import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_marketGroupFromIdxCsf_prefix_rule():
    """idxCsf 접두 → MARKET_GROUP (테마지수·미지값은 KRX fallback)."""
    from dartlab.gather.gov.govApi import _marketGroupFromIdxCsf

    assert _marketGroupFromIdxCsf("KOSPI시리즈") == "KOSPI"
    assert _marketGroupFromIdxCsf("KOSDAQ시리즈") == "KOSDAQ"
    assert _marketGroupFromIdxCsf("KRX시리즈") == "KRX"
    assert _marketGroupFromIdxCsf("테마지수") == "KRX"
    assert _marketGroupFromIdxCsf(None) == "KRX"


def test_normalizeGovIndexFrame_to_krx_schema():
    """gov 지수 raw → KRX 13-col 지수 schema + MARKET_GROUP 파생."""
    from dartlab.gather.gov.govApi import normalizeGovIndexFrame

    raw = pl.DataFrame(
        [
            {
                "basDt": "20260605",
                "idxNm": "코스피 200",
                "idxCsf": "KOSPI시리즈",
                "clpr": 1297.02,
                "mkp": 1323.25,
                "hipr": 1338.13,
                "lopr": 1278.65,
                "vs": -82.54,
                "fltRt": -5.98,
                "trqu": 199470293,
                "trPrc": 44729607853977,
                "lstgMrktTotAmt": 6231443094675910,
            }
        ]
    )
    out = normalizeGovIndexFrame(raw)
    assert out.columns == [
        "BAS_DD",
        "MARKET_GROUP",
        "IDX_CLSS",
        "IDX_NM",
        "CLSPRC_IDX",
        "OPNPRC_IDX",
        "HGPRC_IDX",
        "LWPRC_IDX",
        "CMPPREVDD_IDX",
        "FLUC_RT",
        "ACC_TRDVOL",
        "ACC_TRDVAL",
        "MKTCAP",
    ]
    row = out.row(0, named=True)
    assert row["MARKET_GROUP"] == "KOSPI"
    assert row["IDX_NM"] == "코스피 200"
    assert row["CLSPRC_IDX"] == 1297.02
    assert out.schema["MKTCAP"] == pl.Int64


def test_normalizeGovToKrxRaw_to_15col():
    """gov 전종목 bydd → KRX 15-col raw + ISU_CD=6자리 단축코드 (krx·전 소비자 공통)."""
    from dartlab.gather.gov.govApi import normalizeGovToKrxRaw

    raw = pl.DataFrame(
        [
            {
                "basDt": "20260605",
                "srtnCd": "005930",
                "itmsNm": "삼성전자",
                "mrktCtg": "KOSPI",
                "mkp": 333500,
                "hipr": 343000,
                "lopr": 325000,
                "clpr": 329000,
                "vs": -22500,
                "fltRt": -6.4,
                "trqu": 33725012,
                "trPrc": 11191087320641,
                "mrktTotAmt": 1923425662032000,
                "lstgStCnt": 5846278608,
            }
        ]
    )
    out = normalizeGovToKrxRaw(raw)
    row = out.row(0, named=True)
    assert row["ISU_CD"] == "005930"
    assert row["ISU_NM"] == "삼성전자"
    assert row["TDD_CLSPRC"] == 329000
    assert "SECT_TP_NM" in out.columns
    assert out.schema["TDD_CLSPRC"] == pl.Int64
    assert out.schema["FLUC_RT"] == pl.Float64


def test_normalizeGovFrame_to_company_std():
    """gov raw → 회사 표준 schema (date/stockCode/close...)."""
    from dartlab.gather.gov.govApi import normalizeGovFrame

    raw = pl.DataFrame(
        [{"basDt": "20260605", "srtnCd": "005930", "itmsNm": "삼성전자", "mrktCtg": "KOSPI", "clpr": 329000.0}]
    )
    out = normalizeGovFrame(raw)
    row = out.row(0, named=True)
    assert row["date"] == "20260605"
    assert row["stockCode"] == "005930"
    assert row["close"] == 329000.0


def test_normalize_empty_input_safe():
    """빈/컬럼 누락 입력은 예외 없이 빈 DataFrame."""
    from dartlab.gather.gov.govApi import normalizeGovIndexFrame, normalizeGovToKrxRaw

    assert normalizeGovIndexFrame(pl.DataFrame()).is_empty()
    assert normalizeGovToKrxRaw(pl.DataFrame()).is_empty()


def _govResponse(*, totalCount: int, rows: list[dict]) -> dict:
    return {
        "response": {
            "body": {
                "totalCount": totalCount,
                "items": {"item": rows},
            }
        }
    }


def test_fetchGovBydd_rejects_silent_page_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.gov import govApi

    monkeypatch.setattr(
        govApi,
        "_get",
        lambda *args, **kwargs: _govResponse(totalCount=3, rows=[{"basDt": "20260101", "srtnCd": "000001"}]),
    )

    with pytest.raises(RuntimeError, match="페이지 상한"):
        govApi.fetchGovBydd("20260101", apiKey="key", numOfRows=1, maxPages=1)


@pytest.mark.parametrize("name", ["fetchGovStock", "fetchGovBydd", "fetchGovIndex"])
def test_gov_fetch_rejects_invalid_paging(name: str) -> None:
    from dartlab.gather.gov import govApi

    fetch = getattr(govApi, name)
    firstArg = "005930" if name == "fetchGovStock" else "20260101"

    with pytest.raises(ValueError, match="maxPages"):
        fetch(firstArg, apiKey="key", maxPages=0)


def test_fetchGovBydd_requires_totalCount(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.gov import govApi

    monkeypatch.setattr(
        govApi,
        "_get",
        lambda *args, **kwargs: {"response": {"body": {"items": {"item": [{"basDt": "20260101"}]}}}},
    )

    with pytest.raises(ValueError, match="totalCount"):
        govApi.fetchGovBydd("20260101", apiKey="key")


class _SequenceClient:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = 0

    def get(self, *_args, **_kwargs):
        self.calls += 1
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return result


def _response(status: int, payload: dict | None = None, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload or {},
        headers=headers,
        request=httpx.Request("GET", "https://apis.data.go.kr/example"),
    )


def test_get_retries_connect_timeout_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.gov import govApi

    client = _SequenceClient(
        [
            httpx.ConnectTimeout("first"),
            httpx.ConnectTimeout("second"),
            _response(200, {"ok": True}),
        ]
    )
    waits: list[float] = []
    monkeypatch.setattr(govApi.time, "sleep", waits.append)
    monkeypatch.setenv("DARTLAB_GOV_RETRY_ATTEMPTS", "3")

    assert govApi._get({}, apiKey="key", client=client) == {"ok": True}
    assert client.calls == 3
    assert waits == [2.0, 5.0]


def test_get_does_not_retry_fatal_400(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.gov import govApi

    client = _SequenceClient([_response(400)])
    monkeypatch.setattr(govApi.time, "sleep", lambda _wait: pytest.fail("400은 재시도하면 안 됩니다"))

    with pytest.raises(httpx.HTTPStatusError):
        govApi._get({}, apiKey="key", client=client)
    assert client.calls == 1


def test_get_honors_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.gov import govApi

    client = _SequenceClient([_response(429, headers={"Retry-After": "7"}), _response(200, {"ok": True})])
    waits: list[float] = []
    monkeypatch.setattr(govApi.time, "sleep", waits.append)

    assert govApi._get({}, apiKey="key", client=client) == {"ok": True}
    assert waits == [7.0]
