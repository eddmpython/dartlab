"""import 방향 검증 — 하위 레이어가 상위 레이어를 import하면 실패."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "dartlab"

# 레이어 정의: 숫자가 낮을수록 하위 (의존 대상)
LAYERS = {
    "dartlab.core": 0,
    "dartlab.providers": 1,
    "dartlab.gather": 1,
    "dartlab.market": 1,
    "dartlab.analysis": 2,
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
    """문자열 기반 lazy import 패턴 추출."""
    text = filePath.read_text(encoding="utf-8")
    pattern = re.compile(r"""(?:from\s+|import\s+)(dartlab\.[a-zA-Z0-9_.]+)""")
    return pattern.findall(text)


# ── Company facade lazy import는 의도적 설계 (편의성 프로퍼티) ──
_FACADE_PATTERNS = {
    # dart/edgar Company → analysis (lazy property: insights, sector, rank, ...)
    ("dartlab.providers.dart.company", "dartlab.analysis"),
    ("dartlab.providers.edgar.company", "dartlab.analysis"),
    # dart/edgar Company → ai (lazy: ask, chat)
    ("dartlab.providers.dart.company", "dartlab.ai"),
    ("dartlab.providers.edgar.company", "dartlab.ai"),
    # dart/_finance_helpers → sector.types (sector 코드 참조)
    ("dartlab.providers.dart._finance_helpers", "dartlab.analysis"),
    # scan/network → rank/screen (벤치마크 데이터 참조)
    ("dartlab.providers.dart.scan", "dartlab.analysis"),
    # market → analysis (향후)
    ("dartlab.market", "dartlab.analysis"),
}

# ── 알려진 인프라 역방향 의존 (리팩토링에서 순차 해소) ──
_KNOWN_VIOLATIONS = {
    # core/ → providers (L0→L1)
    ("dartlab.core.plugins", "dartlab.providers"),
    ("dartlab.core.plugins", "dartlab.ai"),
    ("dartlab.core.dataLoader", "dartlab.providers"),
    ("dartlab.core.guidance", "dartlab.providers"),
    ("dartlab.core.resolve", "dartlab.gather"),
    ("dartlab.core", "dartlab.gather"),  # core/__init__ → listing
    # core/ → ai (L0→L3)
    ("dartlab.core.ai", "dartlab.ai"),
    # core/ → providers (L0→L1)
    ("dartlab.core.docs.diff", "dartlab.providers"),
    ("dartlab.core.docs.diff", "dartlab.market"),
    ("dartlab.core.finance.currency", "dartlab.gather"),
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
