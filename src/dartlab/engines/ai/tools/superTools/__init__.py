"""Super Tool 등록 — 101개 도구를 7개 dispatcher로 통합.

각 Super Tool은 action enum 파라미터로 내부 도구를 라우팅한다.
기존 defaults/*.py의 함수 로직은 그대로 재사용.
"""

from __future__ import annotations

from typing import Any, Callable

from .analyze import registerAnalyzeTool
from .chart import registerChartTool
from .explore import registerExploreTool
from .finance import registerFinanceTool
from .market import registerMarketTool
from .openapi import registerOpenapiTool
from .system import registerSystemTool


def registerSuperTools(company: Any | None, registerTool: Callable) -> None:
    """7개 Super Tool을 등록한다."""
    # Global tools (company 없어도 동작)
    registerSystemTool(registerTool, company=company)
    registerMarketTool(registerTool)
    registerOpenapiTool(registerTool)

    # Company-bound tools
    if company is not None:
        registerExploreTool(company, registerTool)
        registerFinanceTool(company, registerTool)
        registerAnalyzeTool(company, registerTool)
        registerChartTool(company, registerTool)
