"""tools.chart 모듈 테스트 — plotly 필요."""

import importlib.util

import polars as pl
import pytest

pytestmark = pytest.mark.unit

HAS_PLOTLY = importlib.util.find_spec("plotly") is not None

requires_plotly = pytest.mark.skipif(not HAS_PLOTLY, reason="plotly not installed")


@requires_plotly
class TestAutoNumericCols:
    def test_basic(self):
        from dartlab.tools.chart import _auto_numeric_cols

        df = pl.DataFrame(
            {
                "year": [2023],
                "revenue": [100],
                "name": ["A"],
                "ratio": [0.5],
            }
        )
        cols = _auto_numeric_cols(df, exclude=["year"])
        assert "revenue" in cols
        assert "ratio" in cols
        assert "year" not in cols
        assert "name" not in cols


@requires_plotly
class TestLine:
    def test_basic(self):
        from dartlab.tools.chart import line

        df = pl.DataFrame({"year": [2021, 2022, 2023], "revenue": [100, 120, 150]})
        fig = line(df, y=["revenue"])
        assert len(fig.data) == 1
        assert fig.data[0].name == "revenue"

    def test_missing_x(self):
        from dartlab.tools.chart import line

        df = pl.DataFrame({"v": [1, 2, 3]})
        with pytest.raises(ValueError, match="'year' 컬럼"):
            line(df)

    def test_auto_y(self):
        from dartlab.tools.chart import line

        df = pl.DataFrame(
            {
                "year": [2021, 2022],
                "a": [10, 20],
                "b": [30, 40],
                "name": ["x", "y"],
            }
        )
        fig = line(df)
        # a, b만 trace로 추가 (name은 문자열)
        assert len(fig.data) == 2


@requires_plotly
class TestBar:
    def test_basic(self):
        from dartlab.tools.chart import bar

        df = pl.DataFrame({"year": [2021, 2022], "revenue": [100, 120]})
        fig = bar(df, y=["revenue"])
        assert len(fig.data) == 1

    def test_stacked(self):
        from dartlab.tools.chart import bar

        df = pl.DataFrame({"year": [2021, 2022], "a": [10, 20], "b": [30, 40]})
        fig = bar(df, y=["a", "b"], stacked=True)
        assert fig.layout.barmode == "stack"


@requires_plotly
class TestPie:
    def test_basic(self):
        from dartlab.tools.chart import pie

        df = pl.DataFrame({"name": ["A", "B", "C"], "value": [10, 20, 30]})
        fig = pie(df, names="name", values="value")
        assert len(fig.data) == 1
        assert fig.data[0].labels == ("A", "B", "C")


@requires_plotly
class TestWaterfall:
    def test_basic(self):
        from dartlab.tools.chart import waterfall

        labels = ["매출", "원가", "판관비", "영업이익"]
        values = [1000, -600, -200, 200]
        fig = waterfall(labels, values)
        assert len(fig.data) == 1
        # 마지막이 total, 나머지 relative
        measures = list(fig.data[0].measure)
        assert measures[-1] == "total"
        assert all(m == "relative" for m in measures[:-1])
