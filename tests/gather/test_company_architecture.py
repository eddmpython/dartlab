"""Company 레이어 구조 테스트."""

import pytest

pytestmark = pytest.mark.unit

from pathlib import Path

import dartlab
import dartlab.providers.dart as dart_engine
import dartlab.providers.edgar as edgar_engine
from dartlab import Company
from dartlab.providers.dart import Company as DartEngineCompany
from dartlab.providers.edgar import Company as EdgarEngineCompany


def _read(relpath: str) -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / relpath).read_text(encoding="utf-8")


def test_root_facade_exports_exist():
    assert callable(Company)
    assert not hasattr(dartlab, "Compare")
    assert not hasattr(dartlab, "KRCompany")
    assert not hasattr(dartlab, "USCompany")


def test_engine_exports_exist():
    assert callable(DartEngineCompany)
    assert callable(EdgarEngineCompany)
    assert not hasattr(dart_engine, "Compare")
    assert not hasattr(edgar_engine, "Compare")


def test_report_api_surface_is_28():
    from dartlab.providers.dart.report.types import API_TYPES

    assert len(API_TYPES) == 28


def test_engine_modules_do_not_import_root_company_or_compare():
    targets = [
        "src/dartlab/providers/dart/company.py",
        "src/dartlab/providers/edgar/company.py",
    ]
    banned = [
        "from dartlab.company import",
        "import dartlab.company",
        "from dartlab.compare import",
        "import dartlab.compare",
        "from dartlab.usCompany import",
        "import dartlab.usCompany",
    ]

    for target in targets:
        text = _read(target)
        for pattern in banned:
            assert pattern not in text, f"{target} contains banned import: {pattern}"


def test_compare_modules_are_removed():
    root = Path(__file__).resolve().parents[2]
    targets = [
        "src/dartlab/compare.py",
        "src/dartlab/providers/dart/compare.py",
        "src/dartlab/providers/edgar/compare.py",
    ]
    for target in targets:
        assert not (root / target).exists(), f"{target} should be removed"


def test_public_docs_do_not_reference_legacy_company_names():
    targets = [
        "README.md",
        "src/dartlab/skills/specs/start/dartlabSkillOs.md",
        "src/dartlab/skills/specs/start/quickStart.md",
        "src/dartlab/skills/specs/operation/stability.md",
        "src/dartlab/skills/specs/operation/apiContract.md",
    ]
    banned = ["USCompany", "KRCompany", "DartCompany", "EdgarCompany", "c.docs()"]

    for target in targets:
        text = _read(target)
        for pattern in banned:
            assert pattern not in text, f"{target} contains legacy public reference: {pattern}"


def test_export_module_does_not_depend_on_root_company_internals():
    text = _read("src/dartlab/viz/export/excel.py")
    assert "from dartlab.company import _ALL_PROPERTIES" not in text
    # viz 는 providers 를 직접 import 하지 않는다. 이것이 이 테스트가 지키는 불변식이다.
    #
    # 예전에는 그 위임을 `FinanceDocAccessor` seam 이 맡았고 이 테스트가 그 이름의 존재를
    # 함께 요구했다. 그런데 그 seam 은 등록 대상 목록이 비어 언제나 None 을 돌려주는
    # 죽은 뼈대였고, 소비자의 첫 분기가 실행되지 않는 코드로 남아 있었다. seam 을 걷어낸
    # 지금 지켜야 할 것은 방향뿐이라 이름 조건은 뺀다. 특정 우회 장치의 존재가 아니라
    # 계층 방향이 계약이다.
    assert "from dartlab.providers" not in text
    assert "import dartlab.providers" not in text


def test_ai_owned_helpers_do_not_live_in_src_root():
    repo_root = Path(__file__).resolve().parents[2]
    forbidden = [
        "src/dartlab/" + "ai_" + "backup",
        "src/dartlab/tools",
        "src/dartlab/table",
        "src/dartlab/knowledge",
        "src/dartlab/audit",
        "src/dartlab/display",
        "src/dartlab/export",
        # Cut 2.5 환원 — capability/settings/guide 는 core 또는 사용처로 흡수됐으므로 top-level 재출현 금지
        "src/dartlab/capability",
        "src/dartlab/settings",
        "src/dartlab/guide",
    ]
    for rel in forbidden:
        assert not (repo_root / rel).exists(), f"retired root package still exists: {rel}"

    expected = [
        "src/dartlab/skills",
        "src/dartlab/ai/tools",
        "src/dartlab/ai/workbench",
        "src/dartlab/reference/capability/registry.py",
        "src/dartlab/reference/capability/search.py",
        "src/dartlab/reference/capability/analysisGraph.py",
        "src/dartlab/reference/capability/builder.py",
        "src/dartlab/core/credentials.py",
        "src/dartlab/synth/axisGuide.py",
        "src/dartlab/viz/display",
        "src/dartlab/viz/export",
    ]
    for rel in expected:
        assert (repo_root / rel).exists(), f"canonical package missing: {rel}"


def test_core_does_not_own_retired_subpackages():
    """Core 정리 작업으로 폐기된 하위 디렉토리/모듈이 다시 생기지 않도록 차단.

    architecture.md 의 L0 정의: 환경/자격증명·데이터 로더·교차 도메인 헬퍼·
    가이드 안내·유틸·프로토콜은 OK. AI provider config (ai/settings),
    도메인 분석 (finance), CLI 통합 wrapper 는 core 가 아니다.
    """
    repo_root = Path(__file__).resolve().parents[2]
    forbidden_dirs = [
        "src/dartlab/core/ai",
        "src/dartlab/core/finance",
    ]
    for rel in forbidden_dirs:
        assert not (repo_root / rel).exists(), f"core must not own product layer: {rel}"

    forbidden_imports = [
        "dartlab.core.ai",
        # 'dartlab.core.finance' 자체는 폐기 — single underscore prefix 으로 정확 매칭
        # (financeDocAccessor 같은 정상 모듈명이 substring 으로 잡히지 않게).
        "dartlab.core.finance.",
        "dartlab.core.finance ",
        "from dartlab.core.finance import",
        # CLI 통합 wrapper 는 cli/services/errors 로 이관됨 (Cut 2.5b 후)
        "dartlab.core.integration",
        # guide 패키지 자체가 폐기됨 (Cut 2.5b)
        "dartlab.guide",
        # plugins 는 plugin 개발자 entry-point — top-level dartlab.plugins 가 SSOT (Cut 4)
        "dartlab.core.plugins",
        # capability 5 파일은 core/capability/ 서브디렉토리로 묶임 — flat 재출현 차단
        "dartlab.core.capabilities",
        "dartlab.core.search_capabilities",
        "dartlab.core.analysisGraph",
        "dartlab.core._generated",
    ]
    self_files = {"plugins.py"}  # 본인 파일은 docstring self-인용 허용
    for py_file in (repo_root / "src").rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_imports:
            # self-인용 (본인 파일 docstring) 은 forbidden 아님 — import 만 차단
            if py_file.name in self_files and pattern.startswith("dartlab.core.plugins"):
                continue
            assert pattern not in text, f"{py_file} contains retired core import: {pattern}"
