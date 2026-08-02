"""M8: cleanupBetweenCompaniesCalls audit 검증.

dartlab 의 다중 회사 loop 진입점에서 cleanupBetweenCompanies() 호출
또는 with Company(code) as c: 패턴 부재 시 violation 검출.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _import_audit():
    """audit 모듈 동적 import."""
    import importlib.util

    repo = Path(__file__).resolve().parent.parent.parent
    scriptPath = repo / "tests" / "audit" / "cleanupBetweenCompaniesCalls.py"
    spec = importlib.util.spec_from_file_location("cleanupBetweenCompaniesCalls", scriptPath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runVisitor(source: str) -> list[str]:
    """source 코드에 audit visitor 실행 → violations 반환 (rel 은 fake)."""
    mod = _import_audit()
    visitor = mod._AuditVisitor("fake.py")
    visitor.visit(ast.parse(textwrap.dedent(source)))
    return visitor.violations


def test_audit_runs_clean_on_repo():
    """현 repo audit OK — baseline 외 회귀 0."""
    mod = _import_audit()
    rc = mod.main()
    assert rc == 0


def test_violation_detected_when_cleanup_missing():
    """다중 회사 loop + heavy call + cleanup 부재 → violation."""
    src = """
    def update(stockCodes):
        for code in stockCodes:
            loadData(code, "finance")
    """
    violations = _runVisitor(src)
    assert len(violations) == 1


def test_no_violation_when_cleanup_present():
    """다중 회사 loop + cleanup 호출 → violation 0."""
    src = """
    def update(stockCodes):
        for code in stockCodes:
            loadData(code, "finance")
            cleanupBetweenCompanies(label=code)
    """
    violations = _runVisitor(src)
    assert violations == []


def test_no_violation_when_with_company_used():
    """with Company(code) as c: 패턴 — __exit__ 가 자동 cleanup → violation 0."""
    src = """
    def update(codes):
        for code in codes:
            with Company(code) as c:
                c.panel("IS")
    """
    violations = _runVisitor(src)
    assert violations == []


def test_no_violation_when_lazy_company_context_used():
    """lazy 공개 진입점의 context manager 도 __exit__ cleanup 으로 인정."""
    src = """
    def update(codes):
        for code in codes:
            with getattr(dartlab, "Company")(code) as company:
                company._buildFinanceSeries(freq="Q")
    """
    violations = _runVisitor(src)
    assert violations == []


def test_no_violation_when_loop_var_not_company_hint():
    """변수명 hint 없음 (예: `for i in range(10):`) → 검출 안 함."""
    src = """
    def stuff():
        for i in range(10):
            print(i)
    """
    violations = _runVisitor(src)
    assert violations == []
