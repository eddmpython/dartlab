"""Protocol 적합성 테스트 — DART/EDGAR Company가 CompanyProtocol을 만족하는지 검증."""

import inspect

import pytest

from dartlab.engines.common.protocols import CompanyProtocol, DocsProtocol, FinanceProtocol
from tests.conftest import SAMSUNG, requires_samsung


def _get_protocol_required_members(proto) -> set[str]:
    """Protocol이 요구하는 멤버 이름 추출."""
    return set(proto.__protocol_attrs__)


def _class_has_all_members(cls, members: set[str]) -> list[str]:
    """클래스가 모든 멤버를 가졌는지 확인. 누락된 멤버 목록 반환."""
    missing = []
    for name in members:
        if not hasattr(cls, name):
            # __init__에서 할당되는 instance attribute 확인
            init_src = inspect.getsource(cls.__init__)
            if f"self.{name}" not in init_src:
                missing.append(name)
    return missing


# ── 구조적 검증 (데이터 불필요) ──


def test_dart_company_class_has_all_protocol_members():
    from dartlab.engines.company.dart.company import Company

    members = _get_protocol_required_members(CompanyProtocol)
    missing = _class_has_all_members(Company, members)
    assert not missing, f"DART Company missing: {missing}"


def test_edgar_company_class_has_all_protocol_members():
    from dartlab.engines.company.edgar.company import Company

    members = _get_protocol_required_members(CompanyProtocol)
    missing = _class_has_all_members(Company, members)
    assert not missing, f"EDGAR Company missing: {missing}"


def test_dart_docs_class_has_all_protocol_members():
    from dartlab.engines.company.dart.company import _DocsAccessor

    members = _get_protocol_required_members(DocsProtocol)
    missing = _class_has_all_members(_DocsAccessor, members)
    assert not missing, f"DART _DocsAccessor missing: {missing}"


def test_edgar_docs_class_has_all_protocol_members():
    from dartlab.engines.company.edgar.company import _DocsAccessor

    members = _get_protocol_required_members(DocsProtocol)
    missing = _class_has_all_members(_DocsAccessor, members)
    assert not missing, f"EDGAR _DocsAccessor missing: {missing}"


def test_dart_finance_class_has_all_protocol_members():
    from dartlab.engines.company.dart.company import _FinanceAccessor

    members = _get_protocol_required_members(FinanceProtocol)
    missing = _class_has_all_members(_FinanceAccessor, members)
    assert not missing, f"DART _FinanceAccessor missing: {missing}"


def test_edgar_finance_class_has_all_protocol_members():
    from dartlab.engines.company.edgar.company import _FinanceAccessor

    members = _get_protocol_required_members(FinanceProtocol)
    missing = _class_has_all_members(_FinanceAccessor, members)
    assert not missing, f"EDGAR _FinanceAccessor missing: {missing}"


# ── 인스턴스 검증 (데이터 필요) ──


@requires_samsung
def test_dart_company_isinstance_protocol():
    from dartlab.engines.company.dart.company import Company

    c = Company(SAMSUNG)
    assert isinstance(c, CompanyProtocol)


@requires_samsung
def test_dart_docs_isinstance_protocol():
    from dartlab.engines.company.dart.company import Company

    c = Company(SAMSUNG)
    assert isinstance(c.docs, DocsProtocol)


@requires_samsung
def test_dart_finance_isinstance_protocol():
    from dartlab.engines.company.dart.company import Company

    c = Company(SAMSUNG)
    assert isinstance(c.finance, FinanceProtocol)


@pytest.mark.skipif(
    not __import__("dartlab.core.dataLoader", fromlist=["_dataDir"])
    ._dataDir("edgar")
    .joinpath("AAPL.parquet")
    .exists(),
    reason="EDGAR parquet 데이터 없음",
)
def test_edgar_company_isinstance_protocol():
    from dartlab.engines.company.edgar.company import Company

    c = Company("AAPL")
    assert isinstance(c, CompanyProtocol)


@requires_samsung
def test_facade_company_isinstance_protocol():
    from dartlab import Company

    c = Company(SAMSUNG)
    assert isinstance(c, CompanyProtocol)
