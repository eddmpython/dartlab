"""dartlabGuard.py 얇은 pytest 접점."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = REPO_ROOT / "tests" / "audit"
if str(AUDIT_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDIT_ROOT))

from guard.indexer import (  # noqa: E402
    CALLER_OWNED_IMPORT,
    DISCOVERY_IMPORT,
    DYNAMIC_IMPORT,
    DYNAMIC_UNKNOWN,
    EAGER_PHASE,
    LAZY_PHASE,
    TYPE_ONLY_PHASE,
    GuardIndexError,
    ImportRecord,
    ModuleRecord,
    buildIndex,
    extractImports,
    indexFile,
    reverseImportClosure,
    selectImpactedTestTargets,
)
from guard.rules import checkCoreImportBoundary  # noqa: E402


def testGuardIndexCapturesDynamicImportsAndExecutionPhase() -> None:
    """Guard Index가 동적 대상과 eager/lazy/type-only phase를 숨기지 않는다."""
    tree = ast.parse(
        """
import importlib as il
from importlib import import_module as im
from dartlab.core.pluginDiscovery import discoverOnce
from typing import TYPE_CHECKING

KNOWN = ("dartlab.providers.dart.build", "dartlab.gather.entry")
il.import_module("dartlab.analysis")
im("dartlab.scan.io")
__import__("dartlab.story")
discoverOnce(__name__, KNOWN)

if TYPE_CHECKING:
    im("dartlab.quant")

class EagerClass:
    provider = im("dartlab.industry")

def eagerDefault(provider=im("dartlab.frame")):
    return provider

if True:
    def conditionalLazy():
        return im("dartlab.credit")

def lazy(target):
    return il.import_module(target)
"""
    )
    dynamic = [item for item in extractImports(tree) if item.kind != "static"]
    assert {(item.module, item.kind, item.phase) for item in dynamic} == {
        ("dartlab.analysis", DYNAMIC_IMPORT, EAGER_PHASE),
        ("dartlab.scan.io", DYNAMIC_IMPORT, EAGER_PHASE),
        ("dartlab.story", DYNAMIC_IMPORT, EAGER_PHASE),
        ("dartlab.providers.dart.build", DISCOVERY_IMPORT, EAGER_PHASE),
        ("dartlab.gather.entry", DISCOVERY_IMPORT, EAGER_PHASE),
        ("dartlab.quant", DYNAMIC_IMPORT, TYPE_ONLY_PHASE),
        ("dartlab.industry", DYNAMIC_IMPORT, EAGER_PHASE),
        ("dartlab.frame", DYNAMIC_IMPORT, EAGER_PHASE),
        ("dartlab.credit", DYNAMIC_IMPORT, LAZY_PHASE),
        (DYNAMIC_UNKNOWN, DYNAMIC_IMPORT, LAZY_PHASE),
    }
    assert all(item.isTopLevel == (item.phase == EAGER_PHASE) for item in dynamic)


def testCoreBoundaryAllowsOnlyApprovedCallerOwnedGenericLoader() -> None:
    """L0 concrete 대상과 임의 caller-owned 표식을 막고 승인된 generic loader만 허용한다."""
    record = ModuleRecord(
        path="src/dartlab/core/example.py",
        module="dartlab.core.example",
        topPackage="core",
        layer=0.0,
        imports=(
            ImportRecord(
                module="dartlab.gather.entry",
                topPackage="gather",
                line=10,
                isTopLevel=False,
                kind=DISCOVERY_IMPORT,
                phase=LAZY_PHASE,
            ),
            ImportRecord(
                module="dartlab.providers.dart.company",
                topPackage="providers",
                line=20,
                isTopLevel=False,
                kind=DYNAMIC_IMPORT,
                phase=LAZY_PHASE,
            ),
            ImportRecord(
                module=DYNAMIC_UNKNOWN,
                topPackage=None,
                line=30,
                isTopLevel=False,
                kind=DYNAMIC_IMPORT,
                phase=LAZY_PHASE,
            ),
            ImportRecord(
                module=DYNAMIC_UNKNOWN,
                topPackage=None,
                line=40,
                isTopLevel=False,
                kind=CALLER_OWNED_IMPORT,
                phase=LAZY_PHASE,
            ),
        ),
    )
    violations = checkCoreImportBoundary([record])
    assert [(item.rule, item.line) for item in violations] == [
        ("architecture.coreUpperImport", 10),
        ("architecture.coreUpperImport", 20),
        ("architecture.coreUnresolvedDynamicImport", 30),
        ("architecture.coreUnresolvedDynamicImport", 40),
    ]

    approved = ModuleRecord(
        path="src/dartlab/core/plugins.py",
        module="dartlab.core.plugins",
        topPackage="core",
        layer=0.0,
        imports=(
            ImportRecord(
                module=DYNAMIC_UNKNOWN,
                topPackage=None,
                line=50,
                isTopLevel=False,
                kind=CALLER_OWNED_IMPORT,
                phase=LAZY_PHASE,
            ),
        ),
    )
    assert checkCoreImportBoundary([approved]) == []


def testGuardIndexFailsClosedOnMalformedSource(tmp_path: Path) -> None:
    """구문이 깨진 source를 빈 import 목록으로 오인하지 않는다."""
    srcRoot = tmp_path / "src"
    source = srcRoot / "dartlab" / "core" / "broken.py"
    source.parent.mkdir(parents=True)
    source.write_text("def broken(:\n", encoding="utf-8")

    try:
        indexFile(tmp_path, srcRoot, source)
    except GuardIndexError as exc:
        assert "SyntaxError" in str(exc)
    else:
        raise AssertionError("malformed source가 Guard Index를 통과했습니다")


def testGuardIndexReverseClosureKeepsKnownTransitiveChain() -> None:
    """Regression for #103: core 변경이 analysis를 거쳐 story까지 전파된다."""
    records = [
        ModuleRecord("src/dartlab/core/base.py", "dartlab.core.base", "core", 0.0, ()),
        ModuleRecord(
            "src/dartlab/analysis/calc.py",
            "dartlab.analysis.calc",
            "analysis",
            2.0,
            (ImportRecord("dartlab.core.base", "core", 1, True, "static", EAGER_PHASE),),
        ),
        ModuleRecord(
            "src/dartlab/story/report.py",
            "dartlab.story.report",
            "story",
            3.0,
            (ImportRecord("dartlab.analysis.calc", "analysis", 1, True, "static", EAGER_PHASE),),
        ),
    ]

    assert reverseImportClosure(records, {"dartlab.core.base"}) == {
        "dartlab.core.base",
        "dartlab.analysis.calc",
        "dartlab.story.report",
    }


def testGuardIndexReverseClosureStopsAtUnchangedTopPackageFacade() -> None:
    """Regression for #103: 하위 provider 변경이 공개 facade를 통해 전수로 팽창하지 않는다."""

    records = [
        ModuleRecord("src/dartlab/gather/gov/govApi.py", "dartlab.gather.gov.govApi", "gather", 1.0, ()),
        ModuleRecord(
            "src/dartlab/gather/gov/__init__.py",
            "dartlab.gather.gov",
            "gather",
            1.0,
            (ImportRecord("dartlab.gather.gov.govApi", "gather", 1, True, "static", EAGER_PHASE),),
        ),
        ModuleRecord(
            "src/dartlab/gather/__init__.py",
            "dartlab.gather",
            "gather",
            1.0,
            (ImportRecord("dartlab.gather.gov", "gather", 1, True, "static", EAGER_PHASE),),
        ),
        ModuleRecord(
            "src/dartlab/analysis/unrelated.py",
            "dartlab.analysis.unrelated",
            "analysis",
            2.0,
            (ImportRecord("dartlab.gather", "gather", 1, True, "static", EAGER_PHASE),),
        ),
    ]

    assert reverseImportClosure(records, {"dartlab.gather.gov.govApi"}) == {
        "dartlab.gather.gov.govApi",
        "dartlab.gather.gov",
        "dartlab.gather",
    }


def testGuardIndexSelectionUsesDeepestMirrorBelowFacade(tmp_path: Path) -> None:
    """Regression for #103: gov 변경은 tests/gather 전체가 아니라 gov mirror만 고른다."""
    (tmp_path / "tests/gather/gov").mkdir(parents=True)
    records = [
        ModuleRecord("src/dartlab/gather/gov/govApi.py", "dartlab.gather.gov.govApi", "gather", 1.0, ()),
        ModuleRecord(
            "src/dartlab/gather/gov/__init__.py",
            "dartlab.gather.gov",
            "gather",
            1.0,
            (ImportRecord("dartlab.gather.gov.govApi", "gather", 1, True, "static", EAGER_PHASE),),
        ),
        ModuleRecord(
            "src/dartlab/gather/__init__.py",
            "dartlab.gather",
            "gather",
            1.0,
            (ImportRecord("dartlab.gather.gov", "gather", 1, True, "static", EAGER_PHASE),),
        ),
    ]

    selected = selectImpactedTestTargets(tmp_path, ["src/dartlab/gather/gov/govApi.py"], records=records)
    assert selected["targets"] == ["tests/gather/gov"]


def testGuardIndexTestSelectionUsesMirrorDirectoriesAndFailsClosed(tmp_path: Path) -> None:
    """Regression for #103: 영향 package mirror를 고르고 공용 계약 변경은 전수로 올린다."""
    (tmp_path / "tests/analysis").mkdir(parents=True)
    (tmp_path / "tests/story").mkdir(parents=True)
    records = [
        ModuleRecord("src/dartlab/analysis/calc.py", "dartlab.analysis.calc", "analysis", 2.0, ()),
        ModuleRecord(
            "src/dartlab/story/report.py",
            "dartlab.story.report",
            "story",
            3.0,
            (ImportRecord("dartlab.analysis.calc", "analysis", 1, True, "static", EAGER_PHASE),),
        ),
    ]

    selected = selectImpactedTestTargets(tmp_path, ["src/dartlab/analysis/calc.py"], records=records)
    assert selected["mode"] == "selected"
    assert selected["targets"] == ["tests/analysis", "tests/story"]

    full = selectImpactedTestTargets(tmp_path, ["tests/conftest.py"], records=records)
    assert full["mode"] == "full"
    assert full["targets"] == ["tests/"]


def testActualCoreHasNoConcreteUpperImport() -> None:
    """실제 L0 graph에 정적·동적 concrete 상향 edge가 없어야 한다."""
    violations = checkCoreImportBoundary(buildIndex(REPO_ROOT))
    assert violations == []


def testActualCompositionBootstrapTableIsFullyIndexed() -> None:
    """composition 선언 표의 concrete 대상이 import graph에서 빠지지 않아야 한다."""
    records = buildIndex(REPO_ROOT)
    composition = next(record for record in records if record.module == "dartlab.composition")
    indexedTargets = {item.module for item in composition.imports if item.kind == DISCOVERY_IMPORT}
    from dartlab.composition import _MODULE_BOOTSTRAPS

    declaredTargets = {module for modules in _MODULE_BOOTSTRAPS.values() for module in modules}
    assert indexedTargets == declaredTargets


def testDartlabGuardStrictJson() -> None:
    """Guard strict JSON 결과가 pass 여야 한다."""
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "tests/audit/dartlabGuard.py",
            "strict",
            "--scope",
            "l0-l15",
            "--providers",
            "dart,edgar",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "pass"
    active = payload["baseline"]["activeKnownViolations"]
    protected = payload["baseline"]["protectedCompanyFacadeDebt"]
    expectedActiveKeys = {
        "architecture.lazyUpperImport:lazy:src/dartlab/gather/accessors.py:company",
        "architecture.lazyUpperImport:lazy:src/dartlab/providers/dart/builder/scanAggregator.py:scan",
        "architecture.lazyUpperImport:lazy:src/dartlab/providers/dart/finance/scanAccount.py:scan",
        "architecture.lazyUpperImport:lazy:src/dartlab/providers/edgar/finance/terminalStmt.py:viz",
    }
    assert {item["baselineKey"] for item in active} == expectedActiveKeys
    assert payload["summary"]["activeKnownDebt"] == len(active)
    assert payload["summary"]["protectedCompanyFacadeDebt"] == len(protected)
    assert protected
    assert all("/company.py" not in item["path"] for item in active)
    assert all(item["path"].endswith("/company.py") for item in protected)
