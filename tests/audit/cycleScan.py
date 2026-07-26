"""모듈 import 사이클 검출 — 양방향 cycle 만 차단 (단방향 허용).

정책 SSOT: src/dartlab/skills/specs/operation/architecture.md

import-linter 의 layers contract 가 동급 sibling 단방향 허용을 깔끔히 표현하지
못해 별도 보조 도구로 양방향 cycle 만 검출한다. AST 로 lazy import (함수 내부
import) 까지 추적하여 import-linter 가 놓치는 케이스 보완.

검사 대상:
    src/dartlab/ 안 모든 .py 파일의 dartlab.* 1 차 패키지 import
    (dartlab.analysis.X.Y → dartlab.macro.Z 는 dartlab.analysis → dartlab.macro edge).

Self-loop (같은 패키지 내부 import) 는 무시.
양방향 (A → B, B → A 동시 존재) 만 cycle 로 보고. 3+ 모듈 cycle 은 networkx 사용 시 추가 검출.

실행:
    python -X utf8 tests/audit/cycleScan.py                       # 전수 검사 (lazy 포함, 경고 모드)
    python -X utf8 tests/audit/cycleScan.py --strict              # 전수 검사, cycle ≥1 시 exit 2
    python -X utf8 tests/audit/cycleScan.py --strict-toplevel     # top-level import 만 strict (lazy 면제)

--strict-toplevel 의미:
    함수/클래스 내부 lazy import 는 런타임 시점이 다르므로 양방향 import 가 있어도
    실제 import cycle 가 아니다. CI 게이트에 적합 (false positive 회피).

종료 코드:
    0 — cycle 0 건 (또는 --strict 미지정)
    2 — cycle ≥ 1 건 (--strict 또는 --strict-toplevel)
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "dartlab"


# dartlab 1 차 패키지 (dartlab.<X> 단위 노드)
def _discoverPrimaryPackages() -> tuple[str, ...]:
    """`src/dartlab/` 직속 1 차 패키지를 실제 트리에서 뽑는다.

    손으로 적은 목록은 실재하지 않는 이름(dashboard, mappers, search, ui)을 남기고
    실재하는 패키지(dataHub, frame, reference, simulate, synth, webapi)를 빠뜨린 채
    오래 방치됐다. 목록에 없는 패키지는 노드가 되지 않으므로 그 안의 cycle 은 아예
    보이지 않는다. 트리에서 뽑으면 그 표류가 구조적으로 불가능해진다.
    """

    names: set[str] = set()
    for child in SRC.iterdir():
        if child.name.startswith(("_", ".")) or child.name == "__pycache__":
            continue
        if child.is_dir() and (child / "__init__.py").exists():
            names.add(child.name)
        elif child.suffix == ".py" and child.stem != "__init__":
            names.add(child.stem)
    return tuple(sorted(names))


PRIMARY_PACKAGES: tuple[str, ...] = _discoverPrimaryPackages()


def _modulePath(p: Path) -> str | None:
    """src/dartlab/<X>/Y/Z.py → 'dartlab.X' (1 차 패키지 단위) 변환."""
    try:
        rel = p.resolve().relative_to(SRC).with_suffix("").as_posix()
    except ValueError:
        return None
    parts = rel.split("/")
    if not parts:
        return None
    head = parts[0]
    if head not in PRIMARY_PACKAGES:
        return None
    return f"dartlab.{head}"


def _toPrimary(modName: str) -> str | None:
    """import target 문자열에서 dartlab.<X> 1 차 패키지만 추출."""
    if not modName.startswith("dartlab."):
        return None
    parts = modName.split(".")
    if len(parts) < 2:
        return None
    head = parts[1]
    if head not in PRIMARY_PACKAGES:
        return None
    return f"dartlab.{head}"


def _extractImports(source: str, *, toplevelOnly: bool = False) -> set[str]:
    """AST 에서 dartlab.* 1 차 패키지 set 추출.

    toplevelOnly=False (기본): 전수 — top-level + lazy (함수 내부) import 모두.
    toplevelOnly=True: top-level (모듈 직속) 만. 함수/클래스 내부 import 면제.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    out: set[str] = set()

    if toplevelOnly:
        # 모듈 직속 노드만 순회 (ast.walk 대신 tree.body)
        for node in tree.body:
            _addImports(node, out)
            # if 블록 — TYPE_CHECKING (런타임 실행 X) 만 면제, 나머지는 추적
            if isinstance(node, ast.If):
                if _isTypeCheckingGuard(node.test):
                    continue
                for inner in ast.walk(node):
                    _addImports(inner, out)
        return out

    for node in ast.walk(tree):
        _addImports(node, out)
    return out


def _isTypeCheckingGuard(test: ast.expr) -> bool:
    """if TYPE_CHECKING / typing.TYPE_CHECKING 분기 식별."""
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
        return True
    return False


def _addImports(node: ast.AST, out: set[str]) -> None:
    """단일 노드에서 dartlab.* import 추출 후 set 에 추가."""
    if isinstance(node, ast.Import):
        for alias in node.names:
            pkg = _toPrimary(alias.name)
            if pkg:
                out.add(pkg)
    elif isinstance(node, ast.ImportFrom):
        if node.level and node.level > 0:
            return
        mod = node.module or ""
        pkg = _toPrimary(mod)
        if pkg:
            out.add(pkg)


def _buildGraph(*, toplevelOnly: bool = False) -> dict[str, set[str]]:
    """src/dartlab 전수 스캔 → {srcPkg: {dstPkg, ...}} edge 그래프."""
    graph: dict[str, set[str]] = defaultdict(set)
    for py in SRC.rglob("*.py"):
        if py.name.startswith("_generated"):
            continue
        src = _modulePath(py)
        if not src:
            continue
        try:
            source = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for dst in _extractImports(source, toplevelOnly=toplevelOnly):
            if dst == src:
                continue
            graph[src].add(dst)
    return graph


def _findCycles(graph: dict[str, set[str]]) -> tuple[list[tuple[str, str]], list[tuple[str, ...]]]:
    """양방향 cycle (2-cycle) + 3+ 모듈 cycle 추출. 3+ 는 sorted-key dedup."""
    twoCycles: set[tuple[str, str]] = set()
    for src, dsts in graph.items():
        for dst in dsts:
            if src in graph.get(dst, set()):
                pair = tuple(sorted([src, dst]))
                twoCycles.add(pair)
    longerSet: set[tuple[str, ...]] = set()
    try:
        import networkx as nx

        G = nx.DiGraph()
        for src, dsts in graph.items():
            for dst in dsts:
                G.add_edge(src, dst)
        for cyc in nx.simple_cycles(G):
            if len(cyc) > 2:
                longerSet.add(tuple(sorted(cyc)))
    except ImportError:
        pass
    return sorted(twoCycles), sorted(longerSet)


def _print2Cycles(cycles: list[tuple[str, str]]) -> None:
    """2-cycle (양방향 cycle) 출력 — 진짜 차단 대상."""
    for a, b in cycles:
        print(f"  - 2-cycle: {a} <-> {b}")


def _printLongerCycles(cycles: list[tuple[str, ...]], maxShow: int = 10) -> None:
    """3+ 모듈 cycle — 상위 maxShow 만 표시 (정보성). 보통 2-cycle 의 합성."""
    if not cycles:
        return
    print(f"\n  3+ 모듈 cycle {len(cycles)} 종 (상위 {min(maxShow, len(cycles))} 만 표시):")
    for cyc in cycles[:maxShow]:
        print(f"  - {len(cyc)}-cycle: {' -> '.join(cyc)} -> {cyc[0]}")
    if len(cycles) > maxShow:
        print(f"  ... ({len(cycles) - maxShow} 종 추가, 2-cycle 해소 시 대부분 자동 정리)")


def _baselineFile() -> Path:
    """T9-3 baseline 위치."""
    return Path(__file__).resolve().parent / "_baselines" / "cycleScan.json"


def _loadBaseline() -> dict:
    """T9-3 — baseline JSON 로드. 형식: {twoCycleCount, longerCycleCount, measuredAt}."""
    import json as _json

    path = _baselineFile()
    if not path.exists():
        return {}
    try:
        return _json.loads(path.read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError):
        return {}


def _cycleKey(cycle: tuple[str, ...]) -> str:
    """cycle 을 방향 무관 안정 키로 만든다. 시작점이 달라도 같은 cycle 은 같은 키다."""

    return " <-> ".join(sorted(cycle))


def _saveBaseline(twoCycles: list[tuple[str, ...]], longerCount: int) -> None:
    """현재 2-cycle 목록과 longer 개수를 baseline 으로 저장한다.

    이전 형식은 2-cycle 도 개수만 적었다. 그래서 하나가 사라지고 다른 하나가 생기면
    개수가 같아 아예 보이지 않았고, 늘어나도 어느 것이 새로 생긴 것인지 답할 수
    없었다. 목록으로 적으면 신규 cycle 을 이름으로 지목할 수 있다.
    """

    import datetime as _dt
    import json as _json

    path = _baselineFile()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "_note": (
            "양방향 cycle 부채 원장. 여기 적힌 것 밖의 새 2-cycle 은 차단된다. "
            "항목을 지우려면 한쪽 import 를 하위 계층으로 강등하거나 위임으로 끊는다."
        ),
        "twoCycles": sorted(_cycleKey(cycle) for cycle in twoCycles),
        "longerCycleCount": longerCount,
        "measuredAt": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    path.write_text(_json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: list[str]) -> int:
    """엔트리포인트 — CLI 옵션 파싱 후 _buildGraph + _findCycles 실행.

    T9-3 — `--update-baseline` 옵션 추가. baseline 대비 신규 cycle 증가 시 strict
    모드에서 차단. 현재 cycle 5+140 → baseline 부채 원장 후 monthly 정리.
    """
    toplevelOnly = "--strict-toplevel" in argv
    strict = "--strict" in argv or toplevelOnly
    updateBaseline = "--update-baseline" in argv

    graph = _buildGraph(toplevelOnly=toplevelOnly)
    twoCycles, longerCycles = _findCycles(graph)
    mode = "top-level only" if toplevelOnly else "전수 (lazy 포함)"

    if updateBaseline:
        _saveBaseline(twoCycles, len(longerCycles))
        print(f"[cycle-scan] baseline 갱신. 2-cycle {len(twoCycles)} / longer {len(longerCycles)}")
        return 0

    if not twoCycles and not longerCycles:
        print(f"[cycle-scan/{mode}] OK — {len(graph)} 패키지 분석, cycle 0 건.")
        return 0
    print(f"[cycle-scan/{mode}] 양방향 cycle (2-cycle) {len(twoCycles)} 건 — 차단 대상:")
    _print2Cycles(twoCycles)
    _printLongerCycles(longerCycles)

    # T9-3 — baseline 비교
    baseline = _loadBaseline()
    freshCycles: list[str] = []
    if baseline and not toplevelOnly:
        allowed = set(baseline.get("twoCycles", ()))
        current = {_cycleKey(cycle) for cycle in twoCycles}
        freshCycles = sorted(current - allowed)
        longerDelta = len(longerCycles) - baseline.get("longerCycleCount", 0)
        print(f"\n[cycle-scan] baseline 밖 신규 2-cycle {len(freshCycles)} / longer {longerDelta:+d}")
        for item in sorted(allowed - current):
            print(f"  해소됨: {item} (baseline 에서 지워도 된다)")
        for item in freshCycles:
            print(f"  신규 차단: {item}")

    print(
        "\n정책 SSOT: src/dartlab/skills/specs/operation/architecture.md\n"
        "  - 상하 단방향: L0 ← L1 ← L1.5 ← L2 ← L3 ← L4\n"
        "  - 동급 단방향 허용\n"
        "  - 양방향 cycle 절대금지\n"
        "해소: 한쪽 import 를 story 위임 또는 core 강등 후 재실행."
    )
    # 신규 2-cycle 은 baseline 유무와 무관하게 차단한다. 예전에는 늘어나도 WARN 만
    # 찍고 0 을 돌려줘 아무도 모르는 채 누적됐다.
    if freshCycles:
        return 1
    return 2 if strict else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
