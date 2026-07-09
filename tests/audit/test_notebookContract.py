"""노트북 공개 계약 게이트의 계약.

게이트가 무엇을 잡고 무엇을 놔 두는지 못 박는다. 이 테스트가 없으면 게이트가 조용히
무력화돼도(예: 계약 집합이 빈 set 으로 로드) 아무도 모른다. 2026-07-09 ``c.audit()``
노출 사건이 재발하지 않게 하는 것이 목적이다.
"""

from __future__ import annotations

import pytest

from tests.audit.notebookContract import _loadContract, collect, scanSource

pytestmark = [pytest.mark.unit]


@pytest.fixture(scope="module")
def contract() -> tuple[set[str], set[str]]:
    return _loadContract()


def test_loadContract_readsRealSsot(contract: tuple[set[str], set[str]]) -> None:
    """계약 집합이 실제 spec/__all__ 에서 온다 (빈 set 으로 무력화되면 게이트가 죽는다)."""
    companyMethods, rootPublic = contract
    assert {"panel", "select", "analysis", "credit", "story"} <= companyMethods
    assert {"Company", "scan", "macro"} <= rootPublic
    # 미등재 내부 메서드는 계약에 없어야 한다.
    assert "audit" not in companyMethods
    assert "filings" not in companyMethods


def test_scanSource_flagsUnregisteredCompanyMethod(contract: tuple[set[str], set[str]]) -> None:
    """``c.audit()`` 처럼 capabilityRefs 미등재 메서드는 잡힌다."""
    assert scanSource("c.audit()", *contract) == ["Company.audit"]
    assert scanSource("c.filings().head(10)", *contract) == ["Company.filings"]


def test_scanSource_flagsContractBypass(contract: tuple[set[str], set[str]]) -> None:
    """accessor 우회 진입점은 ``__all__`` 여부와 무관하게 금지."""
    assert scanSource("dartlab.getDefaultGather()", *contract) == ["dartlab.getDefaultGather"]


def test_scanSource_allowsContractCalls(contract: tuple[set[str], set[str]]) -> None:
    """공개 계약 호출은 통과한다 (오탐이 있으면 저자가 게이트를 끈다)."""
    src = (
        "import dartlab\n"
        'c = dartlab.Company("005930")\n'
        'c.panel("IS")\n'
        'c.select("IS", ["매출액"], freq="Y")\n'
        'dartlab.scan("ratio", "roe")\n'
        'dartlab.macro("금리")\n'
    )
    assert scanSource(src, *contract) == []


def test_scanSource_allowsPlainAttributes(contract: tuple[set[str], set[str]]) -> None:
    """호출이 아닌 값 접근(회사명·시장)은 계약 검사 대상이 아니다."""
    assert scanSource("c.corpName\nc.market", *contract) == []


def test_scanSource_ignoresJupyterMagics(contract: tuple[set[str], set[str]]) -> None:
    """`%pip install` · `!cmd` 는 파이썬 문법이 아니라 무시한다 (SyntaxError 로 죽지 않는다)."""
    assert scanSource('%pip install -q dartlab\nimport dartlab\nc.panel("IS")', *contract) == []


def test_scanSource_syntaxErrorIsNotAViolation(contract: tuple[set[str], set[str]]) -> None:
    """문법 검증은 validateNotebooks 담당. 여기서 SyntaxError 로 죽으면 안 된다."""
    assert scanSource("this is not python(((", *contract) == []


def test_collect_baselineIsNotEmpty() -> None:
    """지금 repo 에 실제 위반이 남아 있다(부채 원장 대상). 0 이면 스캔 대상이 사라진 것."""
    current = collect()
    assert current, "노트북 스캔 대상이 하나도 안 잡혔다. _targets() 경로가 깨졌는지 확인하라."
