"""import 방향 검증 — 하위 레이어가 상위 레이어를 import하면 실패."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent / "src" / "dartlab"

# 레이어 정의: 숫자가 낮을수록 하위 (의존 대상)
LAYERS = {
    "dartlab.core": 0,
    "dartlab.providers": 1,
    "dartlab.gather": 1,
    "dartlab.scan": 1,
    "dartlab.frame": 1,
    "dartlab.reference": 1,
    "dartlab.synth": 1,
    "dartlab.analysis": 2,
    "dartlab.credit": 2,
    "dartlab.industry": 2,
    "dartlab.macro": 2,
    "dartlab.quant": 2,
    "dartlab.data": 2,
    "dartlab.simulate": 2,  # L2.5 시나리오/작업대 (다중 L2 결합 합법, L2_PEERS 미소속). 등록 시 신규 위반 0 실측.
    "dartlab.ai": 3,
}


def _getLayer(modulePath: str) -> int | None:
    """모듈 경로에서 레이어 번호 반환. 매핑 외 모듈은 None."""
    for prefix, level in sorted(LAYERS.items(), key=lambda x: -len(x[0])):
        if modulePath.startswith(prefix):
            return level
    return None


def _fileToModule(filePath: Path) -> str:
    """파일 경로 → 모듈 경로."""
    rel = filePath.relative_to(SRC.parent)
    parts = rel.with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _extractImports(filePath: Path) -> list[str]:
    """AST로 import 대상 모듈 추출."""
    try:
        tree = ast.parse(filePath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("dartlab"):
                modules.append(node.module)
    return modules


def _extractLazyImports(filePath: Path) -> list[str]:
    """AST 기반 lazy import 패턴 추출."""
    try:
        tree = ast.parse(filePath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    modules: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callName = _callName(node.func)
        if callName not in {"importlib.import_module", "import_module", "__import__"}:
            continue
        if not node.args:
            continue
        firstArg = node.args[0]
        if isinstance(firstArg, ast.Constant) and isinstance(firstArg.value, str):
            if firstArg.value.startswith("dartlab"):
                modules.append(firstArg.value)
    return modules


def _callName(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _callName(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


# ── Company public facade lazy import는 의도적 설계 ──
_FACADE_PATTERNS = {
    # dart/edgar Company → L2/L3 engines.
    # provider 내부 구현 의존이 아니라 public Company surface의 dual-access facade다.
    ("dartlab.providers.dart.company", "dartlab.analysis"),
    ("dartlab.providers.edgar.company", "dartlab.analysis"),
    ("dartlab.providers.dart.company", "dartlab.credit"),
    ("dartlab.providers.edgar.company", "dartlab.credit"),
    ("dartlab.providers.dart.company", "dartlab.industry.calcs.companyCalcs"),
    ("dartlab.providers.dart.company", "dartlab.macro"),
    ("dartlab.providers.edgar.company", "dartlab.macro"),
    ("dartlab.providers.dart.company", "dartlab.quant"),
    ("dartlab.providers.edgar.company", "dartlab.quant"),
    ("dartlab.providers.dart.company", "dartlab.ai"),
    ("dartlab.providers.edgar.company", "dartlab.ai"),
    # Company.simulate() dual-access facade → simulate.run.runScenario (L2.5, analysis/credit/quant 와 동형)
    ("dartlab.providers.dart.company", "dartlab.simulate"),
    ("dartlab.providers.edgar.company", "dartlab.simulate"),
    # dart/_finance_helpers → sector.types (sector 코드 참조)
    ("dartlab.providers.dart.financeMappers", "dartlab.analysis"),
    # scan/network → rank/screen (벤치마크 데이터 참조)
    ("dartlab.providers.dart.scan", "dartlab.analysis"),
    # market → analysis (향후)
    ("dartlab.scan", "dartlab.analysis"),
}

# ── 알려진 인프라 역방향 의존 (리팩토링에서 순차 해소) ──
_KNOWN_VIOLATIONS = {
    # core/protocols → providers (L0→L1) — docstring doctest 예시 (>>> from dartlab.providers.dart import Company)
    # AST import 0건, regex lazy-import 가 doctest 줄을 잡는 false positive
    ("dartlab.core.protocols", "dartlab.providers"),
    # core/ → providers (L0→L1)
    ("dartlab.core.dataLoader", "dartlab.providers"),
    ("dartlab.frame.resolve", "dartlab.gather"),
    ("dartlab.core", "dartlab.gather"),  # core/__init__ → listing
    # core/ → providers (L0→L1)
    ("dartlab.providers._common.diff", "dartlab.providers"),
    ("dartlab.providers._common.diff", "dartlab.scan"),
    # core/search → providers (L0→L1) — 수집 디렉토리/파일 참조
    ("dartlab.providers.dart.search", "dartlab.providers"),
    # core/finance → scan (L0→L1) — lazy import (함수 내부)
    ("dartlab.quant.bottomUpBeta", "dartlab.scan"),
    ("dartlab.macro.rates.impliedERP", "dartlab.scan"),
    # analysis → ai (L2→L3) — lazy import (storyValidation → KnowledgeDB 조회)
    ("dartlab.analysis.financial.storyValidation", "dartlab.ai"),
    # core/credentials → providers — DART API 키 관리 lazy import
    ("dartlab.core.credentials", "dartlab.providers"),
    # core/credentials → ai.settings — provider 카탈로그/secret store/profile 조회 lazy import
    ("dartlab.core.credentials", "dartlab.ai"),
    # core/messaging → ai.settings — apiKeyMissingHint·onKeyRequired·promptKeyIfMissing lazy import
    ("dartlab.core.messaging", "dartlab.ai"),
    # core/messaging → providers (L0→L1) — hasDartApiKey 확인 lazy import
    ("dartlab.core.messaging", "dartlab.providers"),
    # providers/dart/finance/spec → analysis/financial/ratios (L1→L2)
    # — finance.ratios re-export wrapper는 제거했고 spec의 분석 타입 참조만 남았다.
    ("dartlab.providers.dart.finance.spec", "dartlab.analysis"),
    # providers/dart/{_docsIndex,_financeBuilders} + providers/edgar/_finance_accessor →
    # analysis/financial/ratios (L1→L2). ratios 가 L2 로 이주됐는데 L1 facade backend
    # 가 그 결과 타입 (RatioResult dataclass) 을 import — 큰 레포 표준상 결과 dataclass
    # 는 review 통과해야 하지만 facade backend 의 cache/render 보조라 호출처 정리는
    # S8 으로 미룸. 그때 풀 예정.
    ("dartlab.providers.dart.builder.financeStatementBuilder", "dartlab.analysis"),
    ("dartlab.providers.edgar.accessor.financeAccessor", "dartlab.analysis"),
}


def _isFacadeImport(sourceModule: str, importedModule: str) -> bool:
    """Company facade의 lazy import는 의도적 설계."""
    for srcPrefix, impPrefix in _FACADE_PATTERNS:
        if sourceModule.startswith(srcPrefix) and importedModule.startswith(impPrefix):
            return True
    return False


def _isKnownViolation(sourceModule: str, importedModule: str) -> bool:
    for srcPrefix, impPrefix in _KNOWN_VIOLATIONS:
        if sourceModule.startswith(srcPrefix) and importedModule.startswith(impPrefix):
            return True
    return False


def _collectViolations() -> list[tuple[str, str, int, int]]:
    """모든 .py 파일을 스캔하여 역방향 import 위반 수집."""
    violations = []

    for pyFile in SRC.rglob("*.py"):
        if "__pycache__" in str(pyFile):
            continue

        sourceModule = _fileToModule(pyFile)
        sourceLayer = _getLayer(sourceModule)
        if sourceLayer is None:
            continue

        allImports = set(_extractImports(pyFile) + _extractLazyImports(pyFile))

        for imp in allImports:
            impLayer = _getLayer(imp)
            if impLayer is not None and impLayer > sourceLayer:
                if _isFacadeImport(sourceModule, imp):
                    continue
                if not _isKnownViolation(sourceModule, imp):
                    violations.append((sourceModule, imp, sourceLayer, impLayer))

    return violations


@pytest.mark.unit
def test_noReverseImports():
    """하위 레이어가 상위 레이어를 import하면 실패."""
    violations = _collectViolations()

    if violations:
        lines = [f"  {src} (L{sl}) → {imp} (L{il})" for src, imp, sl, il in violations]
        pytest.fail(f"역방향 import {len(violations)}건 발견:\n" + "\n".join(lines))
