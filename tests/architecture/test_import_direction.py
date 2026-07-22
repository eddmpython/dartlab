"""4 계층 단방향 import 검사 (역방향 금지 강제).

룰: L0 ← L1 ← L1.5 ← L2 ← L3 ← L4. 역방향 import 0.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "dartlab"

LAYER_OF: dict[str, float] = {
    "core": 0.0,
    "gather": 1.0,
    "providers": 1.0,
    "scan": 1.5,
    "frame": 1.5,
    "synth": 1.5,
    "reference": 1.5,
    "analysis": 2.0,
    "macro": 2.0,
    "quant": 2.0,
    "industry": 2.0,
    "credit": 2.0,
    "data": 2.5,
    "simulate": 2.5,
    "story": 3.0,
    "ai": 4.0,
    "mcp": 4.0,
}
# sink 헬퍼 — CLAUDE.md "표현/전송 헬퍼: 모든 계층 결과를 다른 매체로". 호출 방향 룰 예외.
# 어디서도 import 가능 (L0~L3 → viz/cli/server/channel OK). 단 sink 끼리 cross 는 별 룰 미적용.
# pipeline = 수집 오케스트레이션 sink (gather fetch + providers build 합법 조합, 패키지밖 sync 정공 대체).
SINK_HELPERS = {"viz", "cli", "server", "channel", "pipeline"}
STRICT_L0_L15 = {
    "core",
    "gather",
    "providers",
    "scan",
    "frame",
    "synth",
    "reference",
}


def _assertRealSourceRoot() -> None:
    assert ROOT.exists(), f"dartlab source root not found: {ROOT}"
    assert any(ROOT.rglob("*.py")), f"dartlab source root has no Python files: {ROOT}"


def _topLevel(modName: str) -> str | None:
    """dartlab.X.Y → X (top-level package)."""
    parts = modName.split(".")
    if len(parts) >= 2 and parts[0] == "dartlab":
        return parts[1]
    return None


def test_import_direction_downward_only() -> None:
    """상위 계층이 하위만 import — 역방향 0 건."""
    _assertRealSourceRoot()
    violations: list[str] = []
    for ownerName, ownerLayer in LAYER_OF.items():
        ownerDir = ROOT / ownerName
        if not ownerDir.exists():
            continue
        for pyFile in ownerDir.rglob("*.py"):
            # lazy DI import (di.py) known exception
            if pyFile.name == "di.py":
                continue
            try:
                tree = ast.parse(pyFile.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            # module-level imports 만 검사 — function body 안 lazy import 는 cycle 회피
            # 의도된 패턴 (Company facade → analysis 등) 이라 통과시킨다.
            for node in tree.body:
                names: list[str] = []
                if isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                elif isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                for n in names:
                    target = _topLevel(n)
                    if target is None or target in SINK_HELPERS or target not in LAYER_OF:
                        continue
                    targetLayer = LAYER_OF[target]
                    if targetLayer > ownerLayer:
                        rel = pyFile.relative_to(ROOT.parent.parent)
                        violations.append(f"{rel}:{node.lineno}: L{ownerLayer} {ownerName} → L{targetLayer} {target}")
    # baseline 300 → 0 도달 (D1~D5 완료):
    #   D1: dataLoader/dataConfig/loaders → core 복귀
    #   D2: show.py → providers, reference/providers → core/providers
    #   D3: SINK helpers (viz/cli/server/channel) 검사 제외
    #   D4: reference/mappers/{common,parserMapper,notesMapper,scanner} → providers/mappers,
    #        reference/mappers/engine → core/mapperEngine,
    #        reference/htmlRenderer → core, reference/viewer → providers,
    #        reference/docs/diff → providers/docs
    #   D5: module-level imports 만 검사 (lazy import 는 Company facade 패턴 허용),
    #        frame/market → core (모든 엔진 SSOT)
    BASELINE = 0
    assert len(violations) <= BASELINE, f"역방향 import 신규 위반 ({len(violations)} > {BASELINE}):\n" + "\n".join(
        violations[:20]
    )


def test_l0_l15_import_direction_strict() -> None:
    """L0~L1.5 완료 게이트 — 상위 계층 직접 import 금지."""
    _assertRealSourceRoot()
    violations: list[str] = []
    for ownerName in STRICT_L0_L15:
        ownerLayer = LAYER_OF[ownerName]
        ownerDir = ROOT / ownerName
        if not ownerDir.exists():
            continue
        for pyFile in ownerDir.rglob("*.py"):
            if pyFile.name == "di.py":
                continue
            try:
                tree = ast.parse(pyFile.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in tree.body:
                names: list[str] = []
                if isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                elif isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                for n in names:
                    target = _topLevel(n)
                    if target is None or target in SINK_HELPERS or target not in LAYER_OF:
                        continue
                    targetLayer = LAYER_OF[target]
                    if targetLayer > ownerLayer:
                        rel = pyFile.relative_to(ROOT.parent.parent)
                        violations.append(f"{rel}:{node.lineno}: L{ownerLayer} {ownerName} → L{targetLayer} {target}")
    assert not violations, "L0~L1.5 import direction 위반:\n" + "\n".join(violations[:30])
