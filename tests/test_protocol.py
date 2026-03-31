"""Protocol 적합성 테스트 — DART/EDGAR Company가 CompanyProtocol을 만족하는지 검증.

2가지 검증:
1. CompanyProtocol/DocsProtocol/FinanceProtocol 멤버 구조적 적합성
2. DartCompany↔EdgarCompany public 메소드 동기화 (EXEMPT 목록 외 전부 일치해야 함)
"""

import inspect

import pytest

from dartlab.core.protocols import CompanyProtocol, DocsProtocol, FinanceProtocol
from tests.conftest import SAMSUNG, requires_samsung

pytestmark = pytest.mark.integration


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
    from dartlab.providers.dart.company import Company

    members = _get_protocol_required_members(CompanyProtocol)
    missing = _class_has_all_members(Company, members)
    assert not missing, f"DART Company missing: {missing}"


def test_edgar_company_class_has_all_protocol_members():
    from dartlab.providers.edgar.company import Company

    members = _get_protocol_required_members(CompanyProtocol)
    missing = _class_has_all_members(Company, members)
    assert not missing, f"EDGAR Company missing: {missing}"


def test_dart_docs_class_has_all_protocol_members():
    from dartlab.providers.dart._docs_accessor import _DocsAccessor

    members = _get_protocol_required_members(DocsProtocol)
    missing = _class_has_all_members(_DocsAccessor, members)
    assert not missing, f"DART _DocsAccessor missing: {missing}"


def test_edgar_docs_class_has_all_protocol_members():
    from dartlab.providers.edgar.company import _DocsAccessor

    members = _get_protocol_required_members(DocsProtocol)
    missing = _class_has_all_members(_DocsAccessor, members)
    assert not missing, f"EDGAR _DocsAccessor missing: {missing}"


def test_dart_finance_class_has_all_protocol_members():
    from dartlab.providers.dart._finance_accessor import _FinanceAccessor

    members = _get_protocol_required_members(FinanceProtocol)
    missing = _class_has_all_members(_FinanceAccessor, members)
    assert not missing, f"DART _FinanceAccessor missing: {missing}"


def test_edgar_finance_class_has_all_protocol_members():
    from dartlab.providers.edgar.company import _FinanceAccessor

    members = _get_protocol_required_members(FinanceProtocol)
    missing = _class_has_all_members(_FinanceAccessor, members)
    assert not missing, f"EDGAR _FinanceAccessor missing: {missing}"


# ── 인스턴스 검증 (데이터 필요) ──


@requires_samsung
def test_dart_company_isinstance_protocol():
    from dartlab.providers.dart.company import Company

    c = Company(SAMSUNG)
    assert isinstance(c, CompanyProtocol)


@requires_samsung
def test_dart_docs_isinstance_protocol():
    from dartlab.providers.dart.company import Company

    c = Company(SAMSUNG)
    assert isinstance(c.docs, DocsProtocol)


@requires_samsung
def test_dart_finance_isinstance_protocol():
    from dartlab.providers.dart.company import Company

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
    from dartlab.providers.edgar.company import Company

    c = Company("AAPL")
    assert isinstance(c, CompanyProtocol)


@requires_samsung
def test_facade_company_isinstance_protocol():
    from dartlab import Company

    c = Company(SAMSUNG)
    assert isinstance(c, CompanyProtocol)


# ── DartCompany ↔ EdgarCompany public 메소드 동기화 검증 ──
# 이 테스트가 실패하면: EdgarCompany에 메소드를 추가하거나, EXEMPT에 등록해야 한다.
# EXEMPT에 등록하려면 "이 메소드는 DART 전용이다"라는 의식적 결정이 필요하다.

# DART 전용으로 의식적으로 제외한 메소드 (사유 주석 필수)
_DART_ONLY_EXEMPT: set[str] = {
    # ── 데이터 소스 구조 차이 (DART는 로컬 parquet, EDGAR는 on-demand API) ──
    "rawDocs",  # DART 로컬 docs parquet 직접 접근
    "rawFinance",  # DART 로컬 finance parquet 직접 접근
    "rawReport",  # DART 로컬 report parquet 직접 접근
    "update",  # DART 증분 수집 (EDGAR는 on-demand API)
    "status",  # DART 데이터 freshness 상태
    # ── DART report 전용 (EDGAR에 동등한 구조화 데이터 없음) ──
    "network",  # DART 출자/계열 관계 (SEC 미지원)
    # ── 한국 시장 전용 (KRX 기반) ──
    "codeName",  # 종목코드→회사명 (DART listing)
    "resolve",  # 종목코드/회사명 해석 (DART listing)
    "search",  # 회사명 검색 (DART listing)
    "listing",  # 전체 상장사 목록 (DART listing)
    "topicSummaries",  # topic 요약 (DART docs 전용 구조)
    "sector",  # KRX 섹터 벤치마크 (US 별도 인프라 필요)
    "sectorParams",  # KRX 섹터 파라미터
    # ── 데이터 구조 차이 (DART XBRL vs EDGAR XBRL 형태 상이) ──
    "sceMatrix",  # DART SCE matrix (EDGAR SCE 구조 다름)
}


@pytest.mark.unit
def test_edgar_has_all_dart_public_methods():
    """DartCompany에 있는 public 메소드는 EdgarCompany에도 있어야 한다.

    이 테스트가 실패하면 두 가지 중 하나를 해야 한다:
    1. EdgarCompany에 해당 메소드를 구현한다.
    2. _DART_ONLY_EXEMPT에 사유와 함께 등록한다.
    """
    from dartlab.providers.dart.company import Company as Dart
    from dartlab.providers.edgar.company import Company as Edgar

    dart_public = {m for m in dir(Dart) if not m.startswith("_")}
    edgar_public = {m for m in dir(Edgar) if not m.startswith("_")}
    missing = dart_public - edgar_public - _DART_ONLY_EXEMPT
    assert not missing, (
        f"EdgarCompany에 {len(missing)}개 메소드 누락: {sorted(missing)}\n"
        f"→ EdgarCompany에 구현하거나, test_protocol.py의 _DART_ONLY_EXEMPT에 사유와 함께 등록하세요."
    )
