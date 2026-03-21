"""도구 카테고리별 등록 모듈.

register_all_defaults(company, register_fn)을 호출하면
모든 카테고리의 도구가 등록된다.
"""

from __future__ import annotations

from typing import Any, Callable


def register_all_defaults(
    company: Any | None,
    register_fn: Callable,
) -> None:
    """모든 카테고리의 도구를 등록한다."""
    from .analysis import register_analysis_tools
    from .company import register_company_tools
    from .finance import register_finance_tools
    from .openapi import register_openapi_tools
    from .scan import register_scan_tools
    from .system import register_system_tools
    from .ui import register_ui_tools

    # Global tools (company 없어도 동작)
    register_system_tools(register_fn, company=company)
    register_openapi_tools(register_fn)

    # Company-bound tools
    if company is not None:
        register_company_tools(company, register_fn)
        register_finance_tools(company, register_fn)
        register_analysis_tools(company, register_fn)
        register_ui_tools(company, register_fn)
        register_scan_tools(company, register_fn)
