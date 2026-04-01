"""Rich + HTML 데이터 표시 도구."""

from __future__ import annotations

from dartlab.display.notebook import htmlDistress, htmlFinance, htmlInsight, interactiveTable
from dartlab.display.richCompany import renderCompany
from dartlab.display.richFrame import renderFinance, show
from dartlab.display.richIndex import renderIndex, showIndex
from dartlab.display.richInsight import renderInsight
from dartlab.display.richRatio import renderRatio, showRatio

__all__ = [
    "htmlDistress",
    "htmlFinance",
    "htmlInsight",
    "interactiveTable",
    "renderCompany",
    "renderFinance",
    "renderIndex",
    "renderInsight",
    "renderRatio",
    "show",
    "showIndex",
    "showRatio",
]
