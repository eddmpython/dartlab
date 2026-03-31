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
    root = Path(__file__).resolve().parents[1]
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
    root = Path(__file__).resolve().parents[1]
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
        "docs/api/overview.md",
        "docs/getting-started/quickstart.md",
        "docs/stability.md",
        "docs/changelog.md",
    ]
    banned = ["USCompany", "KRCompany", "DartCompany", "EdgarCompany", "c.docs()"]

    for target in targets:
        text = _read(target)
        for pattern in banned:
            assert pattern not in text, f"{target} contains legacy public reference: {pattern}"


def test_export_module_does_not_depend_on_root_company_internals():
    text = _read("src/dartlab/export/excel.py")
    assert "from dartlab.company import _ALL_PROPERTIES" not in text
    assert "from dartlab.providers.dart.company import listExportModules" in text
