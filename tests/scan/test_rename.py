"""scan 결과 한글화 계약 (`scan.rename._enrichWithKorean`).

종목명 join 은 **부가 정보**다. 상장사 목록 소스를 못 받는 환경(브라우저/pyodide 는 KRX 로
나가지 못한다)에서는 0 행 프레임이 오고, 그 종목코드 컬럼 dtype 은 Null 이라 str join key 와
안 맞아 polars 가 SchemaError 를 던진다. 예전엔 그 예외가 except 목록 밖이라 scan 전체가
죽었다. 목록이 비면 join 을 건너뛰고 scan 결과를 그대로 돌려주는 것이 계약이다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan import rename as renameMod

pytestmark = [pytest.mark.unit]


def _scanResult() -> pl.DataFrame:
    """scan 축이 만들어 내는 모양(영문 컬럼 + str 종목코드)."""
    return pl.DataFrame({"stockCode": ["005930", "000660"], "revenue": [300, 200]})


def test_enrichWithKorean_emptyListing_skipsJoin(monkeypatch: pytest.MonkeyPatch) -> None:
    """목록이 0 행(Null dtype)이면 join 을 건너뛰고 결과를 보존한다 (pyodide 회귀)."""
    empty = pl.DataFrame({"종목코드": [], "종목명": []})
    assert empty.schema["종목코드"] == pl.Null  # 회귀의 전제(Null dtype)를 못 박는다
    monkeypatch.setattr(renameMod, "_COLUMN_RENAME", {"revenue": "매출액"})
    monkeypatch.setattr("dartlab._listingDispatch.listing", lambda *a, **k: empty)

    out = renameMod._enrichWithKorean(_scanResult())

    assert "종목명" not in out.columns
    assert out.height == 2
    assert "매출액" in out.columns


def test_enrichWithKorean_listingPresent_joinsName(monkeypatch: pytest.MonkeyPatch) -> None:
    """목록이 있으면 종목명을 붙이고 종목코드 바로 뒤에 놓는다."""
    listing = pl.DataFrame({"종목코드": ["005930", "000660"], "종목명": ["삼성전자", "SK하이닉스"]})
    monkeypatch.setattr(renameMod, "_COLUMN_RENAME", {"stockCode": "종목코드", "revenue": "매출액"})
    monkeypatch.setattr("dartlab._listingDispatch.listing", lambda *a, **k: listing)

    out = renameMod._enrichWithKorean(_scanResult())

    assert out.columns[:2] == ["종목코드", "종목명"]
    assert out.sort("종목코드")["종목명"].to_list() == ["SK하이닉스", "삼성전자"]


def test_enrichWithKorean_listingRaises_isSwallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """목록 조회가 터져도 scan 결과는 그대로 나온다 (종목명만 없음)."""

    def boom(*_a, **_k):
        raise RuntimeError("네트워크 없음")

    monkeypatch.setattr(renameMod, "_COLUMN_RENAME", {})
    monkeypatch.setattr("dartlab._listingDispatch.listing", boom)

    out = renameMod._enrichWithKorean(_scanResult())

    assert out.columns == ["stockCode", "revenue"]
