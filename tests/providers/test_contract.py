"""providers Protocol contract 검증. P-트랙 룰 1 게이트 + P-PR0 isinstance runtime.

dart/edgar/edinet 3 provider 가 동일 Protocol 표면 (DocsProvider · FinanceProvider ·
FilingsProvider · MemorySafeProvider · CompanyProtocol) 만족하는지 검증.

P0.5 baseline: Protocol 일부는 아직 P1.5 에서 신설이라 미존재 시 xfail.
P1.5 이후 strict: 모든 Protocol isinstance + 메서드 시그니처 introspection 일치.
P-PR0 (2026-05-12): 실 Company 인스턴스 isinstance runtime 검증 2 함수 추가.
    baseline 모드 (현 위반 등록 + new violation 만 fail). P-PR8 strict 전환.

게이트 활성화 단계:
    P0.5: Protocol import 시도, ImportError 면 xfail (회귀 가드만). 완료
    P1.5: Protocol 신설 직후 isinstance 검증 활성. 완료 (5 Protocol 실재)
    P-PR0: Company 인스턴스와 namespace isinstance baseline 모드. 본 PR
    P-PR8: 전 contract strict (isinstanceRuntimeViolations / namespaceIsinstanceViolations 0)
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parent.parent.parent
_BASELINE = _REPO / "tests" / "audit" / "_baselines" / "providerContract.json"
_DEFERRED_PROVIDERS = {"edinet"}


def _providerScope() -> tuple[str, ...]:
    raw = os.environ.get("DARTLAB_PROVIDER_SCOPE", "dart,edgar")
    providers = tuple(p.strip() for p in raw.split(",") if p.strip())
    return providers or ("dart", "edgar")


def _loadBaseline() -> dict:
    """baseline JSON 로드. 없으면 빈 dict 라 첫 실행은 회귀 가드 noop."""
    if _BASELINE.exists():
        return json.loads(_BASELINE.read_text(encoding="utf-8"))
    return {"missingProtocols": [], "missingProviderImpls": [], "_note": "P0.5 baseline"}


def test_protocol_module_importable() -> None:
    """dartlab.core.protocols 가 import 가능해야 한다."""
    mod = importlib.import_module("dartlab.core.protocols")
    assert hasattr(mod, "CompanyProtocol"), "CompanyProtocol 부재. core/protocols.py 손상"


def test_provider_protocols_present() -> None:
    """P1.5 후 strict: DocsProvider · FinanceProvider · FilingsProvider · MemorySafeProvider 모두 존재.

    P0.5 baseline: 미존재 항목은 _baselines/providerContract.json 의 missingProtocols 에 기록.
    """
    mod = importlib.import_module("dartlab.core.protocols")
    expected = {"DocsProvider", "FinanceProvider", "FilingsProvider", "MemorySafeProvider"}
    actual = {name for name in expected if hasattr(mod, name)}
    missing = expected - actual

    baseline = _loadBaseline()
    allowed_missing = set(baseline.get("missingProtocols", []))

    new_missing = missing - allowed_missing
    assert not new_missing, (
        f"Protocol 누락 회귀: {new_missing} (baseline 외 신규). P1.5 에서 신설하거나 baseline 갱신 필요."
    )


def test_provider_company_isinstance_baseline() -> None:
    """3 provider Company 가 CompanyProtocol isinstance 만족.

    P0.5 baseline: 미만족 provider 는 _baselines/providerContract.json 의 missingProviderImpls 에 기록.
    P8 strict: 모두 만족 필수.
    """
    from dartlab.core.protocols import CompanyProtocol

    violations: list[str] = []
    details: list[str] = []
    for providerName in _providerScope():
        try:
            mod = importlib.import_module(f"dartlab.providers.{providerName}.company")
        except ImportError as error:
            violations.append(f"{providerName}: import 실패")
            details.append(f"{providerName}: import 실패 ({error})")
            continue
        if not hasattr(mod, "Company"):
            violations.append(f"{providerName}: Company class 부재")
            continue
        # 클래스 표면만 본다. 실 인스턴스 생성은 무겁고 자료 유무를 탄다.
        companyCls = mod.Company
        requiredAttrs = {"panel", "select", "trace", "filings"}
        missingAttrs = requiredAttrs - set(dir(companyCls))
        if missingAttrs:
            violations.append(f"{providerName}: {sorted(missingAttrs)} 메서드 부재")

    baseline = _loadBaseline()
    allowed = set(baseline.get("missingProviderImpls", []))
    new_violations = set(violations) - allowed
    assert not new_violations, f"Provider Company contract 회귀: {new_violations} (baseline 외 신규). {details}"


# ── P-PR0 추가: 실 인스턴스 isinstance runtime 검증 (baseline 모드) ──

_PROBE_CODES = {
    "dart": "005930",
    "edgar": "AAPL",
    "edinet": "7203",
}


def _providerProbes() -> tuple[tuple[str, str], ...]:
    return tuple((provider, _PROBE_CODES[provider]) for provider in _providerScope() if provider in _PROBE_CODES)


def _openCompany(providerName: str, stockCode: str, violations: list[str], skipped: list[str]):
    """Company 를 만들어 준다. 계약 위반과 환경 사정을 갈라 담는다.

    예전에는 생성 실패를 전부 violation 으로 적었고 그 문자열에 예외 메시지를 그대로 끼워
    넣었다. baseline 대조가 그 문자열로 이뤄지므로 메시지가 한 글자만 달라져도 "baseline 밖
    신규 위반" 이 됐다. 망 사정, 시간 초과, 속도 제한은 매번 다른 문장을 내므로 이 차단
    게이트가 무작위로 빨간불이 됐다. 실제로 CI 에서 한 번 그렇게 났고 같은 커밋을 다시 돌리니
    초록이었다.

    Protocol 적합성은 구조 성질이지 자료 유무가 아니다. 그래서 생성자 계약이 어긋난
    경우(TypeError)만 위반으로 적고, 그 밖의 실패는 건너뛴 사유로 적는다. 건너뛴 사유는
    사람이 읽도록 남기되 baseline 대조에는 넣지 않는다.

    Args:
        providerName: provider 이름.
        stockCode: 탐침용 종목코드.
        violations: 계약 위반을 담을 목록. 안정된 key 만 들어간다.
        skipped: 환경 사정으로 못 본 것을 담을 목록.

    Returns:
        Company 인스턴스. 못 만들었으면 None.
    """
    try:
        mod = importlib.import_module(f"dartlab.providers.{providerName}.company")
    except ImportError as exc:
        violations.append(f"{providerName}: import 실패")
        skipped.append(f"{providerName}: import 실패 ({type(exc).__name__}: {exc})")
        return None
    companyCls = getattr(mod, "Company", None)
    if companyCls is None:
        violations.append(f"{providerName}: Company class 부재")
        return None
    try:
        return companyCls(stockCode)
    except TypeError as exc:
        # 생성자 서명이 계약과 어긋난다. 환경이 아니라 구현 문제다.
        violations.append(f"{providerName}: 생성자 계약 위반")
        skipped.append(f"{providerName}: 생성자 계약 위반 ({exc})")
        return None
    except Exception as exc:  # noqa: BLE001 (자료·망 사정은 계약 위반이 아니다)
        skipped.append(f"{providerName}: 인스턴스 생성 불가 ({type(exc).__name__}: {exc})")
        return None


def _closeCompany(company) -> None:
    """탐침에 쓴 Company 를 닫는다. 정리 실패는 판정에 영향을 주지 않는다."""
    if hasattr(company, "__exit__"):
        try:
            company.__exit__(None, None, None)
        except Exception:  # noqa: BLE001 (cleanup silent)
            pass


def test_company_isinstance_runtime() -> None:
    """3 provider Company 인스턴스가 CompanyProtocol isinstance 를 만족한다.

    자료나 망 사정으로 인스턴스를 못 만든 provider 는 건너뛴다. 그것은 Protocol 적합성이
    아니라 환경 문제이고, 그 실패 문구를 baseline 과 대조하면 게이트가 무작위로 빨간불이
    된다. 생성자 계약이 어긋난 것만 위반으로 적는다.
    """
    from dartlab.core.protocols import CompanyProtocol

    violations: list[str] = []
    skipped: list[str] = []
    checked = 0
    for providerName, stockCode in _providerProbes():
        company = _openCompany(providerName, stockCode, violations, skipped)
        if company is None:
            continue
        try:
            checked += 1
            if not isinstance(company, CompanyProtocol):
                violations.append(f"{providerName}: isinstance(co, CompanyProtocol) == False")
        finally:
            _closeCompany(company)

    baseline = _loadBaseline()
    allowed = set(baseline.get("isinstanceRuntimeViolations", []))
    new_violations = set(violations) - allowed
    assert not new_violations, (
        f"CompanyProtocol isinstance runtime 회귀 {len(new_violations)} 건: {new_violations}. "
        "P-PR0 baseline 에 등록하거나 Company 구현 보강 필요."
    )

    baseline = _loadBaseline()
    allowed = set(baseline.get("isinstanceRuntimeViolations", []))
    new_violations = set(violations) - allowed
    assert not new_violations, (
        f"CompanyProtocol isinstance runtime 회귀 {len(new_violations)} 건: {new_violations}. "
        f"건너뛴 provider: {skipped}"
    )
    if checked == 0:
        import pytest as _pytest

        _pytest.skip(f"어느 provider 도 인스턴스를 못 만들었다: {skipped}")


def test_provider_namespaces_isinstance() -> None:
    """co.docs 와 co.finance namespace 가 각 Provider Protocol 을 만족한다.

    `test_company_isinstance_runtime` 과 같은 이유로, 자료나 망 사정으로 인스턴스를 못
    만든 provider 는 건너뛴다. 위반 key 에 예외 메시지를 끼워 넣지 않는다.
    """
    from dartlab.core.protocols import DocsProvider, FinanceProvider

    violations: list[str] = []
    skipped: list[str] = []
    checked = 0
    for providerName, stockCode in _providerProbes():
        company = _openCompany(providerName, stockCode, violations, skipped)
        if company is None:
            continue
        try:
            checked += 1
            for nsName, protocolCls in (("docs", DocsProvider), ("finance", FinanceProvider)):
                namespace = getattr(company, nsName, None)
                if namespace is None:
                    violations.append(f"{providerName}.{nsName}: namespace 부재")
                    continue
                if not isinstance(namespace, protocolCls):
                    violations.append(f"{providerName}.{nsName}: isinstance({protocolCls.__name__}) == False")
        finally:
            _closeCompany(company)

    baseline = _loadBaseline()
    allowed = set(baseline.get("namespaceIsinstanceViolations", []))
    new_violations = set(violations) - allowed
    assert not new_violations, (
        f"Namespace Protocol isinstance 회귀 {len(new_violations)} 건: {new_violations}. 건너뛴 provider: {skipped}"
    )
    if checked == 0:
        import pytest as _pytest

        _pytest.skip(f"어느 provider 도 인스턴스를 못 만들었다: {skipped}")


def test_edinet_is_deferred_by_default() -> None:
    """EDINET 은 API 통신 불가 provider 이므로 기본 strict scope 에 포함하지 않는다."""
    if "edinet" in _providerScope():
        pytest.skip("edinet 명시 scope. deferred 확인 생략")
    assert _DEFERRED_PROVIDERS == {"edinet"}


def testViolationKeysCarryNoExceptionText() -> None:
    """위반 key 에 예외 메시지를 끼워 넣으면 차단 게이트가 무작위로 빨간불이 된다.

    baseline 대조는 문자열 집합 비교다. key 에 `f"{type(exc).__name__}: {exc}"` 가 들어가면
    망 사정, 시간 초과, 속도 제한이 매번 다른 문장을 내므로 같은 코드가 실행마다 다른 판정을
    받는다. 실제로 CI 에서 이 게이트가 그렇게 빨간불이 났고 같은 커밋 재실행은 초록이었다.

    여기서 고정하는 것은 "위반 key 를 만드는 자리에 예외 값이 안 들어간다" 는 성질이다.
    사람이 읽을 상세는 assert 문구와 skipped 목록으로 따로 나간다.
    """
    import ast as _ast

    source = Path(__file__).read_text(encoding="utf-8")
    tree = _ast.parse(source)
    offenders: list[str] = []
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Call):
            continue
        target = node.func
        if not isinstance(target, _ast.Attribute) or target.attr != "append":
            continue
        if not isinstance(target.value, _ast.Name) or target.value.id != "violations":
            continue
        rendered = _ast.unparse(node)
        if "exc" in {n.id for n in _ast.walk(node) if isinstance(n, _ast.Name)}:
            offenders.append(rendered)

    assert not offenders, f"위반 key 에 예외 값이 섞였다: {offenders}"
