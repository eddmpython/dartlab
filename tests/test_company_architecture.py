"""Company/Compare 레이어 구조 테스트."""

from pathlib import Path

from dartlab import Compare, Company
from dartlab.engines.dart import Compare as EngineDartCompare
from dartlab.engines.dart import Company as EngineDartCompany
from dartlab.engines.edgar import Compare as EngineEdgarCompare
from dartlab.engines.edgar import Company as EngineEdgarCompany


def _read(relpath: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / relpath).read_text(encoding="utf-8")


def test_root_facade_exports_exist():
    assert callable(Company)
    assert callable(Compare)


def test_engine_exports_exist():
    assert callable(EngineDartCompany)
    assert callable(EngineEdgarCompany)
    assert callable(EngineDartCompare)
    assert callable(EngineEdgarCompare)


def test_report_api_surface_is_28():
    from dartlab.engines.dart.report.types import API_TYPES

    assert len(API_TYPES) == 28


def test_engine_modules_do_not_import_root_company_or_compare():
    targets = [
        "src/dartlab/engines/dart/company.py",
        "src/dartlab/engines/dart/compare.py",
        "src/dartlab/engines/edgar/company.py",
        "src/dartlab/engines/edgar/compare.py",
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


def test_public_docs_do_not_reference_legacy_company_names():
    targets = [
        "README.md",
        "src/dartlab/API_SPEC.md",
        "docs/api/overview.md",
        "docs/getting-started/quickstart.md",
        "docs/tutorials/01_quickstart.md",
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
    assert "from dartlab.engines.dart.company import listExportModules" in text
