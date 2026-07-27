"""스크리너 프리셋 호출 가능성 회귀.

`scanScreen(None)` 이 사용자에게 여덟 프리셋을 목록으로 제시하는데, 그중 둘이 호출하면
매번 예외였다. `cycle_defensive` 는 존재하지 않는 축 이름 'dividend' 를 불렀고, `all` 은
형제와 다른 컬럼명을 내는 `_screenRisk` 결과에서 '종목코드' 를 찾다가 죽었다.

목록에 있는데 부르면 죽는 것은 목록이 거짓말을 하는 것이다. 여기서 고정하는 것은
"제시된 프리셋은 전부 부를 수 있다" 하나다.

실제 데이터를 읽는 프리셋이라 축 로더를 가짜로 갈아 끼우고 배선만 본다.
"""

from __future__ import annotations

import polars as pl
import pytest

import dartlab.scan.screen as screen


def _fakeAxis(name: str) -> pl.DataFrame:
    """각 축이 실제로 내는 컬럼 모양만 흉내 낸다. 값은 판정에 쓰이지 않아도 된다."""

    base = {"종목코드": ["005930", "000660"], "종목명": ["삼성전자", "SK하이닉스"]}
    # 각 축이 스크리너에서 실제로 읽는 컬럼만 채운다. 하나라도 빠지면 배선이 아니라
    # 이 fixture 가 실패하므로, 컬럼 목록 자체가 배선 계약의 기록이 된다.
    columns = {
        "profitability": {"등급": ["우수", "양호"], "ROE": [15.0, 9.0]},
        "quality": {"등급": ["우수", "양호"]},
        "debt": {"위험등급": ["안전", "관찰"]},
        "audit": {"위험등급": ["안전", "관찰"]},
        "liquidity": {"등급": ["우수", "양호"]},
        "efficiency": {"등급": ["우수", "양호"]},
        "growth": {"등급": ["고성장", "성장"], "매출CAGR": [25.0, 12.0]},
        "valuation": {"PBR": [0.5, 1.2], "PER": [8.0, 14.0]},
        "dividendTrend": {"패턴": ["연속증가", "안정"], "DPS성장": [10.0, 3.0], "배당수익률": [2.5, 1.8]},
        "macroBeta": {"gdpBeta": [1.4, 0.3]},
    }
    return pl.DataFrame({**base, **columns.get(name, {})})


@pytest.fixture(autouse=True)
def stubAxes(monkeypatch: pytest.MonkeyPatch) -> None:
    """실제 prebuild 를 읽지 않고 배선만 검사한다."""

    monkeypatch.setattr(screen, "_loadAxis", _fakeAxis)


def testEveryAdvertisedPresetIsCallable() -> None:
    """목록에 제시한 프리셋은 전부 불릴 수 있어야 한다."""

    for key in screen._PRESETS:
        assert key in screen._DISPATCH, key
        result = screen._DISPATCH[key]()
        assert isinstance(result, pl.DataFrame), key


def testCycleDefensiveUsesAnAxisThatExists() -> None:
    """존재하지 않는 축 이름을 부르면 매 호출 ValueError 였다."""

    result = screen._DISPATCH["cycle_defensive"]()

    assert isinstance(result, pl.DataFrame)


def testAllPresetCombinesTheOthersWithoutAColumnMismatch() -> None:
    """형제와 컬럼명이 어긋나면 통합 프리셋이 죽는다."""

    result = screen._DISPATCH["all"]()

    assert isinstance(result, pl.DataFrame)


def testRiskPresetEmitsTheSameKeyColumnAsItsSiblings() -> None:
    """종목 키 컬럼 이름이 프리셋마다 다르면 조합할 수 없다."""

    result = screen._screenRisk()

    if not result.is_empty():
        assert "종목코드" in result.columns
        assert "stockCode" not in result.columns


def testPresetListAndDispatchAgree() -> None:
    """제시 목록과 실행 표가 어긋나면 어느 한쪽이 거짓이 된다."""

    assert set(screen._PRESETS) == set(screen._DISPATCH)
