"""providers/dart/accessor/profileAccessor.py mirror smoke — P6."""

from types import SimpleNamespace

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    import dartlab.providers.dart.accessor.profileAccessor  # noqa: F401


@pytest.mark.parametrize("period, expectedPeriods", [(None, ["2025Q4", "2024Q4"]), ("2024-Q4", ["2024Q4"])])
def testTracePanelUsesAllPopulatedRows(monkeypatch, period, expectedPeriods):
    from dartlab.providers.dart.accessor.profileAccessor import _ProfileAccessor

    panel = pl.DataFrame(
        {
            "sectionLeaf": ["사업의 내용", "사업의 내용", "다른 항목"],
            "2025Q4": [None, "최신 본문", "무관"],
            "2024Q4": ["과거 본문", "", None],
        }
    )
    monkeypatch.setattr(_ProfileAccessor, "facts", property(lambda self: None))
    accessor = _ProfileAccessor(SimpleNamespace(panel=panel))
    result = accessor.trace("사업의 내용", period=period)
    assert result["primarySource"] == "panel"
    assert result["fallbackSources"] == []
    assert result["availableSources"][0]["periods"] == expectedPeriods
    assert result["availableSources"][0]["rows"] == len(expectedPeriods)
    assert result["selectedPayloadRef"] == f"panel-text:사업의 내용:{expectedPeriods[0]}"
    assert accessor.trace("사업의 내용", period="2023Q4") is None
    assert accessor.trace("없는 topic") is None
