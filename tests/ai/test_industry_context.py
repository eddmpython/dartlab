"""업종 내 위치가 첫 조회부터 붙는지 지키는 회귀 테스트.

배경. 처음에는 계산을 배경으로만 돌리고 즉시 None 을 돌려줬다. 실측(2026-08-06) 결과
조회를 여러 번 하는 질문은 위치가 붙었고 조회 한 번짜리 질문은 그냥 빠졌다. 판단 기준이
그 턴에서 조회를 몇 번 했느냐에 좌우된 것이다. 여기서 지키는 것은 세 가지다.

1. 첫 조회에서도 값이 붙는다.
2. 남의 느린 배경 작업에 이 조회가 묶이지 않는다.
3. 상한을 넘기면 답을 막지 않고 위치 없이 내보낸다.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import pytest

import dartlab.ai.tools.industryContext as industryContext
from dartlab.ai.runtime.probeCache import backgroundRefresher


class _Company:
    """종목코드만 있는 최소 대역."""

    def __init__(self, stockCode: str) -> None:
        self.stockCode = stockCode


@pytest.fixture(autouse=True)
def _clearCache() -> Any:
    """케이스마다 캐시를 비운다. 앞 케이스 값이 뒤로 새면 판정이 무의미하다."""
    industryContext._SECTOR_CACHE.clear()
    yield
    industryContext._SECTOR_CACHE.clear()


def _metrics() -> dict[str, Any]:
    return {"peerCount": 117, "opmPercentile": 100.0, "opmMedian": 4.1}


def test첫조회에서값이붙는다() -> None:
    """조회 한 번짜리 질문도 판단 기준을 받아야 한다. 이게 실측으로 깨졌던 지점이다."""
    with patch("dartlab.industry.calcs.companyCalcs.calcSectorMetrics", return_value=_metrics()):
        got = industryContext.getSectorPosition(_Company("005930"))
    assert got is not None
    assert got["peerCount"] == 117


def test두번째조회는캐시에서즉시온다() -> None:
    """같은 회사를 다시 물어도 다시 재지 않는다. 재계산은 초 단위 비용이다."""
    company = _Company("005930")
    with patch("dartlab.industry.calcs.companyCalcs.calcSectorMetrics", return_value=_metrics()) as calc:
        industryContext.getSectorPosition(company)
        started = time.perf_counter()
        again = industryContext.getSectorPosition(company)
    assert again is not None
    assert calc.call_count == 1
    assert time.perf_counter() - started < 0.5


def test남의느린작업에묶이지않는다() -> None:
    """실행기 전체를 기다리면 무관한 probe 가 조회를 인질로 잡는다."""
    backgroundRefresher().submit("느린무관작업", lambda: time.sleep(20))
    with patch("dartlab.industry.calcs.companyCalcs.calcSectorMetrics", return_value=_metrics()):
        started = time.perf_counter()
        got = industryContext.getSectorPosition(_Company("000660"))
        elapsed = time.perf_counter() - started
    assert got is not None
    assert elapsed < 5.0


def test상한을넘기면답을막지않는다(monkeypatch: pytest.MonkeyPatch) -> None:
    """느린 것보다 없는 것이 낫다. 위치가 답변을 지연시키는 주범이 되면 안 된다."""
    monkeypatch.setattr(industryContext, "_SECTOR_WAIT_SECONDS", 0.3)
    with patch(
        "dartlab.industry.calcs.companyCalcs.calcSectorMetrics",
        side_effect=lambda _c: time.sleep(5),
    ):
        started = time.perf_counter()
        got = industryContext.getSectorPosition(_Company("035720"))
        elapsed = time.perf_counter() - started
    assert got is None
    assert elapsed < 2.0


def test실패도기억한다() -> None:
    """데이터 없는 회사마다 매 조회가 다시 재려 들면 그게 진짜 지연이다."""
    company = _Company("999999")
    with patch(
        "dartlab.industry.calcs.companyCalcs.calcSectorMetrics",
        side_effect=RuntimeError("업종 매핑 없음"),
    ) as calc:
        assert industryContext.getSectorPosition(company) is None
        assert industryContext.getSectorPosition(company) is None
    assert calc.call_count == 1


def test종목코드없으면재지않는다() -> None:
    """종목코드가 없으면 잴 대상이 없다. 빈 키로 캐시를 오염시키지 않는다."""
    with patch("dartlab.industry.calcs.companyCalcs.calcSectorMetrics") as calc:
        assert industryContext.getSectorPosition(_Company("")) is None
    calc.assert_not_called()
