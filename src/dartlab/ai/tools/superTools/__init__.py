"""Super Tool 등록 -- dartlab 축 1:1 대응 dispatcher 통합.

4축 정렬: scan, analysis, review + 데이터/외부 도구.
기존 market/analyze는 호환 shim으로 유지.
"""

from __future__ import annotations

from typing import Any, Callable

from .analysis import registerAnalysisTool
from .chart import registerChartTool
from .explore import registerExploreTool
from .finance import registerFinanceTool
from .gather import registerGatherTool
from .openapi import registerOpenapiTool
from .research import registerResearchTool
from .review import registerReviewTool
from .scan import registerScanTool
from .system import registerSystemTool


def registerSuperTools(company: Any | None, registerTool: Callable) -> None:
    """10개 Super Tool을 등록한다."""
    # Global tools (company 없어도 동작)
    registerSystemTool(registerTool, company=company)
    registerScanTool(registerTool)
    registerGatherTool(registerTool)
    registerOpenapiTool(registerTool)
    registerResearchTool(registerTool, company=company)

    # Company-bound tools
    if company is not None:
        registerExploreTool(company, registerTool)
        registerFinanceTool(company, registerTool)
        registerAnalysisTool(company, registerTool)
        registerReviewTool(company, registerTool)
        registerChartTool(company, registerTool)
