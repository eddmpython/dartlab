"""dartlab.gather.domains.krx mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.domains.krx`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.krx")


class _Response:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class _Client:
    def __init__(self, data=None, error: Exception | None = None):
        self._data = data
        self._error = error

    async def get(self, url):
        if self._error is not None:
            raise self._error
        return _Response(self._data)


def test_fetchSectorInfo_reports_actual_partial_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Naver 장애 시 KIND 부분 결과만 명시하고 전멸은 typed failure로 전달한다."""
    from dartlab.gather.domains import krx
    from dartlab.gather.types import SourceUnavailableError

    monkeypatch.setattr(krx, "_getKindSector", lambda code: "반도체")
    monkeypatch.setattr(krx, "_getKindMarket", lambda code: "코스피")
    partial = asyncio.run(krx.fetchSectorInfo("005930", _Client(error=SourceUnavailableError("naver down"))))

    assert partial is not None
    assert partial.source == "kind"
    assert partial.sectorName == "반도체"
    assert partial.industryCode == ""

    monkeypatch.setattr(krx, "_getKindSector", lambda code: "")
    monkeypatch.setattr(krx, "_getKindMarket", lambda code: "")
    with pytest.raises(SourceUnavailableError, match="공급자를 사용할 수 없습니다"):
        asyncio.run(krx.fetchSectorInfo("005930", _Client(error=SourceUnavailableError("naver down"))))


def test_fetchSectorInfo_uses_naver_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Naver만 정보를 제공하면 source를 kind+naver로 과장하지 않는다."""
    from dartlab.gather.domains import krx

    monkeypatch.setattr(krx, "_getKindSector", lambda code: "")
    monkeypatch.setattr(krx, "_getKindMarket", lambda code: "")

    async def fakeIndustryName(code, client):
        return "반도체"

    monkeypatch.setattr(krx, "_getIndustryName", fakeIndustryName)
    result = asyncio.run(
        krx.fetchSectorInfo(
            "005930",
            _Client({"industryCode": "278", "stockExchangeType": {"nameKor": "코스피"}}),
        )
    )

    assert result is not None
    assert result.source == "naver"
    assert result.industryCode == "278"


def test_fetchIndustryPeers_rejects_malformed_provider_value() -> None:
    """malformed 시총은 0으로 위장하지 않고 source failure로 전달한다."""
    from dartlab.gather.domains import krx
    from dartlab.gather.types import SourceUnavailableError

    payload = {
        "stocks": [
            {
                "itemCode": "005930",
                "stockName": "삼성전자",
                "closePrice": "not-a-number",
                "marketValue": "100",
            }
        ]
    }
    with pytest.raises(SourceUnavailableError, match="응답 해석 실패"):
        asyncio.run(krx.fetchIndustryPeers("278", _Client(payload)))
