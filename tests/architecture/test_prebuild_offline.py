"""prebuild 단계 외부 네트워크 호출 차단 가드.

`.github/scripts/prebuild/` 의 모든 스크립트는 외부 API 호출 0 이 정상. 책임 위반
(과거 사례: ``prebuildData._buildCorpProfile`` DART OpenAPI 3965 호출,
``buildMacroJson._analyze_market`` FRED/ECOS API) 가 PR 머지 전 차단되도록 다음 두 층
가드:

1. **정적 가드** (`test_prebuild_main_enforces_offline`): 각 스크립트의 ``main()``
   첫 statement 가 ``enforceOffline()`` 호출인지 AST 검증.
2. **금지 import 가드** (`test_prebuild_blocked_imports`): prebuild 스크립트가 외부
   API client 모듈을 import 하지 못하게 차단. dartlab.providers.{dart,edgar}.openapi,
   dartlab.macro.cycles.cycle (analyzeCycle), dartlab.macro.seriesFetch (fetchLatest /
   fetchYoy / fetchChangePct), 및 requests/aiohttp top-level import.

런타임 가드 (``offlineGuard.enforceOffline``) 자체의 동작은
``test_offline_guard_runtime`` 에서 검증.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PREBUILD_DIR = ROOT / ".github" / "scripts" / "prebuild"


# 사전 정의 금지 import - 외부 API 호출이 함수 진입 즉시 강제되는 모듈만.
# cache-first 모듈 (예: dartlab.gather.krx.listing 의 getKrxList - 메모리·파일·API
# 3-tier) 은 제외 - cache hit 시 통과, miss 시 socket guard 가 차단.
_FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "dartlab.providers.dart.openapi",
    "dartlab.providers.edgar.openapi",
    "dartlab.providers.edinet.openapi",
    "dartlab.macro.cycles.cycle",  # analyzeCycle → seriesFetch 경유 FRED/ECOS online 호출
    "dartlab.macro.seriesFetch",  # fetchLatest/Yoy/ChangePct → FRED/ECOS online 호출
    "dartlab.macro.forecast.forecast",  # analyzeForecast → seriesFetch 경유 online (sync 단계 책임)
    "dartlab.macro.rates.rates",  # analyzeRates → seriesFetch 경유 online (sync 단계 책임)
)

# requests / aiohttp 직접 import 금지 (HF 는 huggingface_hub 통해서만).
# httpx 는 huggingface_hub 의존성이라 제외.
_FORBIDDEN_TOP_LEVEL: tuple[str, ...] = ("requests", "aiohttp")


def _prebuildScripts() -> list[Path]:
    if not PREBUILD_DIR.exists():
        return []
    return sorted(p for p in PREBUILD_DIR.glob("*.py") if not p.name.startswith("_"))


def _findMainFunc(tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            return node
    return None


def _firstNonDocstringStmt(func: ast.FunctionDef) -> ast.stmt | None:
    body = list(func.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return body[0] if body else None


def _callsEnforceOffline(stmts: list[ast.stmt]) -> bool:
    """stmt list 안에 enforceOffline() 호출이 있는지 확인 (최대 5 stmt 까지 허용)."""
    for stmt in stmts[:5]:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name) and fn.id == "enforceOffline":
                    return True
                if isinstance(fn, ast.Attribute) and fn.attr == "enforceOffline":
                    return True
    return False


def _collectImports(tree: ast.Module) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


@pytest.mark.parametrize("scriptPath", _prebuildScripts(), ids=lambda p: p.name)
def test_prebuild_main_enforces_offline(scriptPath: Path) -> None:
    """각 prebuild 스크립트의 main() 이 진입 즉시 enforceOffline() 호출."""
    tree = ast.parse(scriptPath.read_text(encoding="utf-8"))
    mainFunc = _findMainFunc(tree)
    assert mainFunc is not None, f"{scriptPath.name}: main() 함수 없음"
    body = list(mainFunc.body)
    # docstring skip
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    assert _callsEnforceOffline(body), (
        f"{scriptPath.name}: main() 진입 5 stmt 안에 enforceOffline() 호출 필요. "
        "외부 API 호출 차단 가드 누락 - prebuild = offline only."
    )


@pytest.mark.parametrize("scriptPath", _prebuildScripts(), ids=lambda p: p.name)
def test_prebuild_blocked_imports(scriptPath: Path) -> None:
    """prebuild 스크립트가 외부 API client / fetcher 모듈 import 금지."""
    tree = ast.parse(scriptPath.read_text(encoding="utf-8"))
    imports = _collectImports(tree)
    violations: list[str] = []
    for imp in imports:
        for forbidden in _FORBIDDEN_IMPORTS:
            if imp == forbidden or imp.startswith(forbidden + "."):
                violations.append(imp)
                break
        if imp in _FORBIDDEN_TOP_LEVEL:
            violations.append(imp)
    assert not violations, (
        f"{scriptPath.name}: 외부 API import 발견: {violations}. "
        "외부 호출은 sync 단계로 옮기시오 (.github/scripts/{sync,meta}/)."
    )


def test_offline_guard_runtime() -> None:
    """런타임 가드 자체 동작 - 외부 host 차단, loopback / HF 통과."""
    import socket

    from dartlab.core.offlineGuard import OfflineViolation, enforceOffline, releaseOffline

    enforceOffline()
    try:
        # 외부 host 차단
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        with pytest.raises(OfflineViolation):
            s.connect(("opendart.fss.or.kr", 443))
        s.close()
    finally:
        releaseOffline()


def test_offline_guard_idempotent() -> None:
    """enforceOffline 중복 호출 safe."""
    from dartlab.core.offlineGuard import enforceOffline, isOfflineEnforced, releaseOffline

    enforceOffline()
    enforceOffline()
    try:
        assert isOfflineEnforced()
    finally:
        releaseOffline()
    assert not isOfflineEnforced()


def test_offline_guard_strict_blocks_hf_before_dns() -> None:
    """Strict child mode는 기본 HF 예외도 제거하고 loopback만 남긴다."""
    import socket

    from dartlab.core.offlineGuard import (
        OfflineViolation,
        enforceOffline,
        releaseOffline,
    )

    enforceOffline(strict=True)
    try:
        with pytest.raises(OfflineViolation):
            socket.getaddrinfo("huggingface.co", 443)
        assert socket.getaddrinfo("localhost", 0)
    finally:
        releaseOffline()
