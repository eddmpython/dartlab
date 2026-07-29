"""tests/audit/cycleScan.py — 양방향 cycle 검출 단위 테스트."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parent.parent.parent
_SCRIPT = _REPO / "tests" / "audit" / "cycleScan.py"


def _loadCycleScan():
    """tests/audit/cycleScan.py 를 모듈로 동적 로드.

    `sys.modules` 등록 필수 — @dataclass 가 cls.__module__ 으로 module 을 lookup
    하기 때문 (등록 누락 시 AttributeError on dataclass decoration).
    """
    spec = importlib.util.spec_from_file_location("cycleScanMod", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_findCyclesDetectsTwoCycle():
    """A → B + B → A 양방향 → 2-cycle 1 건 검출."""
    cs = _loadCycleScan()
    graph: dict[str, set[str]] = {
        "dartlab.analysis": {"dartlab.credit"},
        "dartlab.credit": {"dartlab.analysis"},
    }
    twoCycles, longerCycles = cs._findCycles(graph)
    assert twoCycles == [("dartlab.analysis", "dartlab.credit")]
    assert longerCycles == []


def test_findCyclesIgnoresSingleDirection():
    """단방향 (A → B 만) 은 cycle 아님."""
    cs = _loadCycleScan()
    graph: dict[str, set[str]] = {
        "dartlab.analysis": {"dartlab.industry"},
        "dartlab.industry": set(),
    }
    twoCycles, longerCycles = cs._findCycles(graph)
    assert twoCycles == []
    assert longerCycles == []


def test_extractImportsFiltersDartlabOnly():
    """import 추출 — dartlab.* 1 차 패키지만, stdlib/3rd 무시."""
    cs = _loadCycleScan()
    src = (
        "import os\n"
        "import polars as pl\n"
        "from dartlab.analysis.financial import calc\n"
        "from dartlab.macro import erp\n"
        "from typing import Any\n"
    )
    result = cs._extractImports(src)
    assert result == {"dartlab.analysis", "dartlab.macro"}


def test_extractImportsCatchesLazyImport():
    """함수 내부 lazy import 도 탐지."""
    cs = _loadCycleScan()
    src = "def fetchData():\n    from dartlab.gather import marketCap\n    return marketCap\n"
    result = cs._extractImports(src)
    assert result == {"dartlab.gather"}


def test_extractImportsCatchesDynamicImportApis():
    """import_module alias와 __import__ 리터럴도 같은 import graph에 들어간다."""
    cs = _loadCycleScan()
    src = (
        "import importlib as il\n"
        "from importlib import import_module as im\n"
        'il.import_module("dartlab.credit.scoring")\n'
        'im("dartlab.macro.rates")\n'
        '__import__("dartlab.analysis.financial")\n'
    )
    assert cs._extractImports(src) == {
        "dartlab.analysis",
        "dartlab.credit",
        "dartlab.macro",
    }


def test_extractImportsTopLevelModeExcludesFunctionDynamicImport():
    """strict top-level cycle gate는 함수 내부 지연 import를 실제 실행시점대로 제외한다."""
    cs = _loadCycleScan()
    src = (
        "import importlib\n"
        'importlib.import_module("dartlab.providers.dart")\n'
        "def fetchData():\n"
        '    return importlib.import_module("dartlab.gather.entry")\n'
    )
    assert cs._extractImports(src, toplevelOnly=True) == {"dartlab.providers"}


def test_toPrimaryNormalizesDeepPath():
    """dartlab.analysis.financial.proforma → dartlab.analysis (1 차 패키지)."""
    cs = _loadCycleScan()
    assert cs._toPrimary("dartlab.analysis.financial.proforma") == "dartlab.analysis"
    assert cs._toPrimary("dartlab.credit.scoring.metrics") == "dartlab.credit"


def test_toPrimaryRejectsUnknownPackage():
    """알 수 없는 1 차 패키지 (예: dartlab.foo) 는 None."""
    cs = _loadCycleScan()
    assert cs._toPrimary("dartlab.foo.bar") is None
    assert cs._toPrimary("notdartlab.x") is None


def test_cycleBaselineMissingFailsClosed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """cycle 원장이 없으면 부채 0으로 오인하지 않는다."""
    cs = _loadCycleScan()
    monkeypatch.setattr(cs, "_baselineFile", lambda: tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError, match="cycle baseline 부재"):
        cs._loadBaseline()


def test_cycleBaselineMalformedFailsClosed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """손상된 cycle 원장을 빈 원장으로 바꾸지 않는다."""
    cs = _loadCycleScan()
    baseline = tmp_path / "cycle.json"
    baseline.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(cs, "_baselineFile", lambda: baseline)

    with pytest.raises(ValueError, match="cycle baseline 읽기 실패"):
        cs._loadBaseline()
