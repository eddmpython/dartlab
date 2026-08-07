"""AI 엔진 boundary lint — graph 강박 회귀 패턴 감지.

룰 (memory/engineering.md 7절):
- 본체는 ai/agent.py (runAgent — chat-native + LLM 자율 tool calling)
- WorkbenchLoop 는 옵션 sub-agent — agent_gateway.py / kernel.py 만 직접 호출
- 새 5 패스 패턴 모듈 / *Loop / *Graph 클래스 추가 금지
- "graph 강제" / "verify 강제" / "회귀 가드" 같은 자기 인식 단어 등장 시 검토(advisory)

검사 2 등급 (debt-honesty P1-1 — 유령 가드 → 실 강제):
- **구조적 4 검사** (WorkbenchLoop 직접호출 · 새 workbench 모듈 · *Loop/*Graph/*Kernel 클래스 ·
  5 패스 노드 식별자) = AST/구조 기반 FP-0 → ``--strict`` 로 강제, ``tests/run.py`` 배선.
- **keyword advisory** (한국어 자기인식 구절 substring) = legit 주석에서 FP 불가피 → 검토만, 차단 X.

Usage:
    uv run python -X utf8 tests/audit/checkAgentBoundary.py
    uv run python -X utf8 tests/audit/checkAgentBoundary.py --strict   # 구조적 위반 시 exit 1 (advisory 무관)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "dartlab"

# WorkbenchLoop 직접 호출 허용 파일 (agentGateway / kernel / RunWorkbench 도구 / workbench 내부).
# ⚠ 경로는 실제 파일명과 일치해야 한다 — agent_gateway.py 는 agentGateway.py 로 camelCase
# rename 됐는데 allowlist 가 stale 이라 legit 호출이 FP 됐었다 (debt-honesty P1-1 정정).
_ALLOWED_WORKBENCH_CALLERS = {
    SRC / "server" / "agentGateway.py",
    SRC / "ai" / "kernel.py",
    SRC / "ai" / "tools" / "runWorkbench.py",  # RunWorkbench 도구 = WorkbenchLoop 의 sanctioned 러너
}

# workbench 모듈에 *기존* 파일들. 새 파일 추가 시 경고.
_KNOWN_WORKBENCH_FILES = {
    "__init__.py",
    "SSOT.md",
    "brief.py",
    "chatNative.py",
    "compose.py",
    "critique.py",
    "gate.py",
    "harvest.py",
    "heuristic.py",
    "intent.py",
    "loop.py",
    "passes.py",
    "prompts.py",
    "runner.py",
    "scratchpad.py",
    "state.py",
    "targets.py",
    "work.py",
}

# 새 코드에 등장하면 검토 필요한 자기 인식 단어.
_REGRESSION_KEYWORDS = (
    "graph 강제",
    "verify 강제",
    "5 패스 강제",
    "6 막 강제",
    "회귀 가드",
    "anti-pattern",
    # T11-5 확장 — 5 패스 노드 이름이 새 클래스/함수 식별자로 등장하면 회귀.
    # 본 audit 은 자기 자신 (checkAgentBoundary.py) + workbench 기존 모듈은 skip.
    "requiredEvidence 강제",
    "GATE 차단",
    "BRIEF 노드",
    "WORK 노드",
    "CRITIQUE 노드",
    "COMPOSE 노드",
    "HARVEST 노드",
    "노드 그래프 강제",
    "workbench 본체화",
)

# T11-5 — 5 패스 노드 이름이 *class 또는 def 식별자* 로 등장하면 차단.
# 본 매트릭스는 AST 가 아닌 단순 substring 매치라 false-positive 가능 — workbench/
# 기존 모듈은 _KNOWN_WORKBENCH_FILES 로 skip.
_FIVE_PASS_NODE_NAMES: tuple[str, ...] = (
    "class BriefNode",
    "class WorkNode",
    "class CritiqueNode",
    "class ComposeNode",
    "class GateNode",
    "class HarvestNode",
    "def runBriefPass",
    "def runWorkPass",
    "def runCritiquePass",
    "def runComposePass",
    "def runGatePass",
    "def runHarvestPass",
)


def _check_workbench_direct_calls(violations: list[str]) -> None:
    """`WorkbenchLoop()` 직접 호출 — 허용 파일 외 발견 시 경고."""
    for path in SRC.rglob("*.py"):
        if path.resolve() in {p.resolve() for p in _ALLOWED_WORKBENCH_CALLERS}:
            continue
        if "workbench" in str(path).replace("\\", "/").split("dartlab/", 1)[-1]:
            # workbench 디렉터리 내부는 정당
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if "WorkbenchLoop()" in stripped and not stripped.startswith(("#", "import", "from")):
                rel = path.relative_to(ROOT)
                violations.append(
                    f"{rel}:{line_no} — WorkbenchLoop() 직접 호출. agent.py runAgent / ai.kernel.ask 사용 권장."
                )


def _check_new_workbench_modules(violations: list[str]) -> None:
    """workbench/ 안의 *새 모듈* 감지 — 5 패스 패턴 회귀 가능성."""
    workbench_dir = SRC / "ai" / "workbench"
    if not workbench_dir.is_dir():
        return
    for path in workbench_dir.iterdir():
        if not path.is_file():
            continue
        if path.name in _KNOWN_WORKBENCH_FILES:
            continue
        rel = path.relative_to(ROOT)
        violations.append(f"{rel} — 새 workbench 모듈. 5 패스 패턴 회귀 가능성. memory/engineering.md 7절 검토.")


def _check_new_loop_classes(violations: list[str]) -> None:
    """ai/ 안 *Loop / *Graph / *Kernel 클래스 새로 추가 감지.

    범위 = ai/ 한정 — ai/ 밖 graph 자료구조(*AI 강박과 무관*)는 제외.
    """
    ai_dir = SRC / "ai"
    if not ai_dir.is_dir():
        return
    for path in ai_dir.rglob("*.py"):
        if "workbench" in str(path).replace("\\", "/"):
            continue
        if "providers" in str(path).replace("\\", "/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped.startswith("class "):
                continue
            class_name = stripped.split(":", 1)[0].split("(", 1)[0].replace("class ", "").strip()
            if class_name.endswith(("Loop", "Graph", "Kernel")) and class_name != "WorkbenchLoop":
                rel = path.relative_to(ROOT)
                violations.append(
                    f"{rel}:{line_no} — class {class_name} (Loop/Graph/Kernel 패턴). graph 강박 회귀 가능성."
                )


def _check_regression_keywords(violations: list[str]) -> None:
    """자기 인식 단어 등장 — 새 graph 패턴 추가 시 자주 함께 등장."""
    for path in SRC.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        # 룰 인용 / system prompt 인용 / 회귀 방지 docstring 은 허용.
        if "feedback_no_graph_regression" in text or "회귀 방지" in text or "DARTLAB_CHAT_SYSTEM" in text:
            continue
        for keyword in _REGRESSION_KEYWORDS:
            if keyword in text:
                rel = path.relative_to(ROOT)
                violations.append(f"{rel} — '{keyword}' 표현 발견. memory/engineering.md 7절 검토.")
                break


def _check_five_pass_node_identifiers(violations: list[str]) -> None:
    """T11-5 — 5 패스 노드 이름이 새 class/def 식별자로 등장하면 차단.

    Range: src/dartlab/ai/ 안 (workbench 기존 모듈 제외 — 자기 자신 보호).
    매트릭스: _FIVE_PASS_NODE_NAMES (12 패턴, class Brief/Work/...Node + def runXxxPass).
    """
    aiDir = SRC / "ai"
    if not aiDir.is_dir():
        return
    for path in aiDir.rglob("*.py"):
        if "workbench" in str(path).replace("\\", "/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # 자기 인식 docstring 인용 허용 (본 audit 처럼).
        if "_FIVE_PASS_NODE_NAMES" in text or "feedback_no_graph_regression" in text:
            continue
        for pattern in _FIVE_PASS_NODE_NAMES:
            if pattern in text:
                rel = path.relative_to(ROOT)
                violations.append(
                    f"{rel} — '{pattern}' 식별자 추가 (5 패스 노드 회귀). memory/engineering.md 7절 검토."
                )
                break


def main() -> int:
    # 구조적 위반(strict, FP-0) vs advisory(fuzzy 한국어 구절, 검토용) 분리.
    # _check_regression_keywords 는 '회귀 가드'·'GATE 차단' 같은 한국어 구절을 substring 매치라
    # legit 주석에서 FP 가 불가피 → strict 차단 불가. 구조적 4 검사만 --strict 로 강제한다.
    structural: list[str] = []
    advisory: list[str] = []
    _check_workbench_direct_calls(structural)
    _check_new_workbench_modules(structural)
    _check_new_loop_classes(structural)
    _check_five_pass_node_identifiers(structural)
    _check_regression_keywords(advisory)

    strict = "--strict" in sys.argv

    if advisory:
        print(f"[agent-boundary] advisory(검토 권장, fuzzy) {len(advisory)} 건:")
        for v in advisory:
            print(f"  ~ {v}")
        print()

    if structural:
        print(f"[agent-boundary] 구조적 위반 {len(structural)} 건:")
        for v in structural:
            print(f"  - {v}")
        print("\n룰 본문: memory/engineering.md 7절")
        return 1 if strict else 0

    print("[agent-boundary] OK — 구조적 룰 통과 (advisory 는 검토만, 차단 아님).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
