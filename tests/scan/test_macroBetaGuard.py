"""scan macroBeta 의 거시지표 결측 처리 계약.

세 지표(gdp·rate·fx)를 모두 쓰는 회귀라 하나만 비어도 전 종목이 탈락한다. 예전에는
`any` 로 검사해서 셋 중 하나만 있어도 통과했고, 그래서 호출부의 경고가 안 울린 채
조용히 빈 표만 나왔다. 실측 예로 ECOS manifest 의 GDP 가 status ok 인데 관측 0 행이라,
금리와 환율이 멀쩡한데도 `scan("macroBeta")` 가 전종목 빈 표를 냈다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_loadMacroForScan_returnsNoneWhenAnyIndicatorEmpty(monkeypatch):
    """지표 하나가 통째로 비면 None 을 돌려줘 호출부 경고가 울린다."""
    import polars as pl

    from dartlab.scan import macroBeta

    def fakeLoad(indicatorId, source="ecos"):
        if indicatorId == "GDP":
            return pl.DataFrame({"date": [], "value": []})
        return pl.DataFrame({"date": ["2024-12-31", "2023-12-31"], "value": [1.0, 2.0]})

    def fakeAlign(df, periodCols):
        return pl.DataFrame({"value": [1.0] * len(periodCols)})

    monkeypatch.setattr("dartlab.gather.transforms.macro.loadMacroParquet", fakeLoad)
    monkeypatch.setattr("dartlab.gather.transforms.macro.alignToFinancialPeriods", fakeAlign)

    assert macroBeta._loadMacroForScan(["2024A", "2023A", "2022A", "2021A"]) is None


def test_loadMacroForScan_returnsDictWhenAllPresent(monkeypatch):
    """세 지표가 다 있으면 그대로 돌려준다."""
    import polars as pl

    from dartlab.scan import macroBeta

    def fakeLoad(indicatorId, source="ecos"):
        return pl.DataFrame({"date": ["2024-12-31"], "value": [1.0]})

    def fakeAlign(df, periodCols):
        return pl.DataFrame({"value": [1.0] * len(periodCols)})

    monkeypatch.setattr("dartlab.gather.transforms.macro.loadMacroParquet", fakeLoad)
    monkeypatch.setattr("dartlab.gather.transforms.macro.alignToFinancialPeriods", fakeAlign)

    result = macroBeta._loadMacroForScan(["2024A", "2023A"])

    assert result is not None
    assert set(result) == {"gdp", "rate", "fx"}
