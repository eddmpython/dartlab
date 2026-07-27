"""매출 예측 앙상블의 네 소스가 실제로 도는지에 대한 회귀.

문서는 시계열, 컨센서스, 세그먼트, 수주잔고 네 소스를 합쳐 예측한다고 밝히는데, 뒤의 둘이
호출되는 순간 죽고 있었다.

수주잔고 소스는 `BacklogSignal` 을 TYPE_CHECKING 안에서만 들여와서, 결과를 만드는 줄에서
NameError 가 났다. 모듈 수준 `__getattr__` 은 함수 안의 전역 이름 조회를 대신해 주지 않는다.
게다가 그 자리를 감싼 except 가 (TypeError, ValueError, KeyError) 라 NameError 를 안 잡아서
호출자에게 그대로 터졌다.

세그먼트 소스는 `forecastMetric` 을 `revenueForecast` 파사드에서 찾았는데 그 파사드는 이
함수를 재내보내지 않는다. 진짜 거처는 `_forecastMetric` 이고 `forecast` 파사드가 내보낸다.
그래서 AttributeError 로 죽었다.

둘 다 조용한 결손이 아니라 예외였다. 그런데도 오래 남아 있었다는 것은 이 두 소스가 실린
경로를 아무도 실행해 보지 않았다는 뜻이다. 그래서 여기서는 결과 모양이 아니라 "부르면
값이 나온다"를 고정한다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.analysis.forecast import _revenueForecastSegments as segments

pytestmark = [pytest.mark.unit]


def _orderFrame() -> pl.DataFrame:
    return pl.DataFrame({"label": ["수주잔고"], "2024": [500.0], "2023": [450.0]})


def _salesFrame() -> pl.DataFrame:
    return pl.DataFrame({"label": ["매출"], "2024": [200.0], "2023": [180.0]})


def _segmentFrame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "부문": ["반도체", "디스플레이"],
            "2024": [1000.0, 400.0],
            "2023": [900.0, 380.0],
            "2022": [800.0, 350.0],
            "2021": [700.0, 330.0],
        }
    )


def testBacklogSourceReturnsASignal() -> None:
    """결함의 핵심이다. 부르면 NameError 가 아니라 값이 나와야 한다."""

    signal = segments._computeBacklogSignal(_orderFrame(), _salesFrame(), sectorKey="건설")

    assert signal is not None
    assert signal.backlogRevenueRatio == pytest.approx(2.5)
    assert signal.sectorsApplicable is True


def testBacklogTypeIsImportableAtRuntime() -> None:
    """TYPE_CHECKING 안에만 두면 실행 시점에 이름이 없다."""

    assert segments.BacklogSignal is not None
    assert segments.SegmentForecast is not None


def testBacklogStillReturnsNoneOnMissingInput() -> None:
    """살리느라 결손 처리를 잃으면 안 된다."""

    assert segments._computeBacklogSignal(None, _salesFrame()) is None
    assert segments._computeBacklogSignal(_orderFrame(), None) is None


def testSegmentSourceReturnsForecasts() -> None:
    """세그먼트 소스도 부르면 값이 나와야 한다."""

    result = segments._extractSegmentForecasts(_segmentFrame(), horizon=3)

    assert len(result) == 2
    assert [item.name for item in result] == ["반도체", "디스플레이"]
    assert all(len(item.projected) == 3 for item in result)


def testSegmentSharesAreDescending() -> None:
    """비중 내림차순 정렬은 문서가 약속한 성질이다."""

    result = segments._extractSegmentForecasts(_segmentFrame(), horizon=3)

    shares = [item.shareOfRevenue for item in result]
    assert shares == sorted(shares, reverse=True)


def testSegmentSourceHandlesMissingInput() -> None:
    """입력이 없으면 빈 목록이다. 예외가 아니다."""

    assert segments._extractSegmentForecasts(None) == []


def testForecastMetricProxyResolvesToTheRealImplementation() -> None:
    """프록시가 엉뚱한 파사드를 가리키면 호출 순간 죽는다."""

    from dartlab.analysis.forecast._forecastMetric import forecastMetric as impl

    assert segments.forecastMetric is not impl
    assert callable(segments.forecastMetric)
