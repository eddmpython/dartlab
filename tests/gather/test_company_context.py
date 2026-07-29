"""Company context manager + RSS 회수 검증 — P-트랙 룰 11 게이트.

`with Company(c) as c:` 종료 시 BoundedCache evict + RSS 회수.
P7 에서 dart/edgar/edinet Company.__enter__/__exit__ 구현 후 strict 전환.

P0.5 baseline: __enter__/__exit__ 미구현 시 xfail 처리.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parent.parent.parent
_BASELINE = _REPO / "scripts" / "audit" / "_baselines" / "companyContext.json"


def _providerScope() -> tuple[str, ...]:
    raw = os.environ.get("DARTLAB_PROVIDER_SCOPE", "dart,edgar")
    providers = tuple(p.strip() for p in raw.split(",") if p.strip())
    return providers or ("dart", "edgar")


def _loadBaseline() -> dict:
    if _BASELINE.exists():
        return json.loads(_BASELINE.read_text(encoding="utf-8"))
    return {"missingContextManagers": [], "_note": "P0.5 baseline"}


def test_protocol_has_enter_exit() -> None:
    """CompanyProtocol 이 __enter__/__exit__ 정의 — P1.5 후 strict.

    P0.5 baseline: 미정의면 baseline 기록.
    """
    from dartlab.core.protocols import CompanyProtocol

    baseline = _loadBaseline()
    allowed = set(baseline.get("missingContextManagers", []))

    missing: list[str] = []
    if not hasattr(CompanyProtocol, "__enter__"):
        missing.append("CompanyProtocol.__enter__")
    if not hasattr(CompanyProtocol, "__exit__"):
        missing.append("CompanyProtocol.__exit__")

    new_missing = set(missing) - allowed
    assert not new_missing, f"Context manager 누락 회귀: {new_missing}. P1.5 에서 추가."


def test_provider_companies_have_context_manager() -> None:
    """dart/edgar/edinet Company 가 context manager 지원.

    P7 에서 신설. baseline: 현재 미지원 provider 기록.
    """
    baseline = _loadBaseline()
    allowed = set(baseline.get("missingContextManagers", []))

    missing: list[str] = []
    for providerName in _providerScope():
        try:
            mod = importlib.import_module(f"dartlab.providers.{providerName}.company")
            CompanyCls = getattr(mod, "Company", None)
            if CompanyCls is None:
                missing.append(f"{providerName}: Company class 부재")
                continue
            if not hasattr(CompanyCls, "__enter__"):
                missing.append(f"{providerName}: Company.__enter__")
            if not hasattr(CompanyCls, "__exit__"):
                missing.append(f"{providerName}: Company.__exit__")
        except ImportError as exc:
            missing.append(f"{providerName}: import 실패 — {exc}")

    new_missing = set(missing) - allowed
    assert not new_missing, f"Company context manager 누락 회귀: {new_missing}. P7 에서 추가."


@pytest.mark.parametrize("providerName", ["dart", "edgar", "edinet"])
def test_provider_company_rejects_nested_memory_scope(providerName: str) -> None:
    """동일 Company 재진입이 watcher 참조를 덮어쓰지 않고 즉시 실패한다."""
    from dartlab.core.memory import MemoryScope, OomTripwire

    mod = importlib.import_module(f"dartlab.providers.{providerName}.company")
    CompanyCls = mod.Company
    company = CompanyCls.__new__(CompanyCls)
    scope = MemoryScope(OomTripwire(intervalSec=0.01, sampler=lambda: 0.0))
    company._memoryScope = scope

    assert CompanyCls.__enter__(company) is company
    try:
        with pytest.raises(RuntimeError, match="중첩"):
            CompanyCls.__enter__(company)
        assert company._memoryScope is scope
        assert scope.active
    finally:
        scope.exit(cleanup=lambda: None, bodyError=None)


@pytest.mark.skip(reason="P7 후 활성 — Company.__enter__/__exit__ 구현 후 RSS 회수 검증")
def test_rss_recovered_after_context_exit() -> None:
    """`with Company(c):` 종료 후 RSS 가 회수되는지 검증.

    P7 에서 활성. RSS 측정 + 회수 임계 (<100 MB delta).
    """
    pass
