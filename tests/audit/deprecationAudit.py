#!/usr/bin/env python3
"""deprecation 거버넌스 가드 — DEPRECATION.md(T8-1) 약속의 실 구현.

DEPRECATION.md 는 "``tests/audit/deprecationAudit.py`` 가 PR 차단" 이라 단언해 왔으나
오랫동안 파일이 *부재*했다 (가장 순수한 유령 가드 — 존재하지 않는 가드가 강제한다고
문서가 약속). 본 파일이 그 약속을 실재화한다 (debt-honesty P1-3).

검사 2 종::

  A. raw stdlib ``DeprecationWarning`` 금지 (ratchet)
     dartlab 의 deprecation 은 *사용자에게 보이는* ``DartlabDeprecationWarning``
     (FutureWarning 하위) / ``warnDeprecated`` / ``@deprecated`` 를 써야 한다. raw
     ``warnings.warn(..., DeprecationWarning, ...)`` 는 사용자에게 숨겨져 "언제 무엇이
     사라지는지 미리 알림" 거버넌스를 침묵시킨다. 현재 알려진 사이트는 baseline 동결 —
     *신규만 차단* (ratchet, 목표 0). baseline 항목은 ``relpath::qualname``.

  B. ``@deprecated(...)`` 데코레이터 ↔ DEPRECATION.md 항목 강제
     데코가 붙은 심볼은 DEPRECATION.md 본문에 항목이 있어야 한다 (DEPRECATION.md §자동검증 1).

실행::

    uv run python -X utf8 tests/audit/deprecationAudit.py             # check (기본)
    uv run python -X utf8 tests/audit/deprecationAudit.py --write-baseline

종료 코드::

    0   깨끗 (또는 신규 위반 0)
    1   신규 raw DeprecationWarning 또는 미문서화 @deprecated
    2   baseline / DEPRECATION.md 부재 (구성 오류)
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parents[2]
_SRC = _REPO / "src" / "dartlab"
_BASELINE = _REPO / "tests" / "audit" / "_baselines" / "deprecationAudit.json"
_DEPRECATION_MD = _REPO / "DEPRECATION.md"


class _Visitor(ast.NodeVisitor):
    """파일 1 개에서 raw DeprecationWarning warn 호출 + @deprecated 데코 수집."""

    def __init__(self, relpath: str) -> None:
        self.relpath = relpath
        self._stack: list[str] = []
        self.rawWarns: set[str] = set()  # relpath::qualname
        self.deprecatedSymbols: set[str] = set()  # @deprecated 가 붙은 심볼명

    def _qual(self) -> str:
        return ".".join(self._stack) if self._stack else "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def _visitFunc(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for deco in node.decorator_list:
            if self._isDeprecatedDeco(deco):
                self.deprecatedSymbols.add(node.name)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    visit_FunctionDef = _visitFunc  # type: ignore[assignment]
    visit_AsyncFunctionDef = _visitFunc  # type: ignore[assignment]

    @staticmethod
    def _isDeprecatedDeco(deco: ast.expr) -> bool:
        target = deco.func if isinstance(deco, ast.Call) else deco
        if isinstance(target, ast.Name):
            return target.id == "deprecated"
        if isinstance(target, ast.Attribute):
            return target.attr == "deprecated"
        return False

    def visit_Call(self, node: ast.Call) -> None:
        if self._isWarningsWarn(node) and self._hasRawDeprecationWarning(node):
            self.rawWarns.add(f"{self.relpath}::{self._qual()}")
        self.generic_visit(node)

    @staticmethod
    def _isWarningsWarn(node: ast.Call) -> bool:
        func = node.func
        return (
            isinstance(func, ast.Attribute)
            and func.attr == "warn"
            and isinstance(func.value, ast.Name)
            and func.value.id == "warnings"
        )

    @staticmethod
    def _hasRawDeprecationWarning(node: ast.Call) -> bool:
        cands: list[ast.expr] = list(node.args)
        cands.extend(kw.value for kw in node.keywords if kw.arg == "category")
        return any(isinstance(a, ast.Name) and a.id == "DeprecationWarning" for a in cands)


def _scan() -> tuple[set[str], set[str]]:
    """src/dartlab 전수 — (raw DeprecationWarning qualname set, @deprecated 심볼 set)."""
    rawWarns: set[str] = set()
    decos: set[str] = set()
    for path in _SRC.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        relpath = path.relative_to(_SRC).as_posix()
        visitor = _Visitor(relpath)
        visitor.visit(tree)
        rawWarns |= visitor.rawWarns
        decos |= visitor.deprecatedSymbols
    return rawWarns, decos


def _loadBaseline() -> set[str]:
    if not _BASELINE.exists():
        raise SystemExit(f"[deprecationAudit] baseline 부재: {_BASELINE}. --write-baseline 로 박제 후 재실행.")
    data = json.loads(_BASELINE.read_text(encoding="utf-8-sig"))
    return set(data.get("violations", []))


def _writeBaseline(rawWarns: set[str]) -> None:
    _BASELINE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "violations": sorted(rawWarns),
        "_note": (
            "raw stdlib DeprecationWarning 가 쓰인 알려진 사이트 (relpath::qualname). "
            "dartlab 은 DartlabDeprecationWarning/warnDeprecated/@deprecated 를 써야 한다 — "
            "본 목록은 ratchet 부채(신규 차단·목표 0). 이관 시 항목 제거. (debt-honesty P1-3)"
        ),
    }
    _BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[deprecationAudit] baseline 박제 → {_BASELINE} ({len(rawWarns)} 사이트)")


def _checkDocumented(decos: set[str]) -> list[str]:
    """@deprecated 심볼이 DEPRECATION.md 에 항목으로 있는지 — 없으면 위반 목록."""
    if not decos:
        return []
    if not _DEPRECATION_MD.exists():
        raise SystemExit(f"[deprecationAudit] DEPRECATION.md 부재: {_DEPRECATION_MD}")
    doc = _DEPRECATION_MD.read_text(encoding="utf-8")
    return [sym for sym in sorted(decos) if sym not in doc]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="deprecation 거버넌스 가드 (DEPRECATION.md T8-1 실 구현).")
    parser.add_argument(
        "--write-baseline", action="store_true", help="현재 raw DeprecationWarning 사이트를 baseline 박제"
    )
    args = parser.parse_args(argv)

    rawWarns, decos = _scan()

    if args.write_baseline:
        _writeBaseline(rawWarns)
        return 0

    baseline = _loadBaseline()
    newRaw = sorted(rawWarns - baseline)
    undocumented = _checkDocumented(decos)

    if not newRaw and not undocumented:
        # `@deprecated` 가 0 이면 문서화 검사는 아무것도 보지 않은 것이다. 그것을
        # "전부 문서화" 로 적으면 검사가 돌아간 것처럼 읽힌다. 실제로 이 저장소는
        # `warnDeprecated` 와 `@deprecated` 를 쓰는 곳이 아직 없어서 그 검사가 한 번도
        # 평가된 적이 없고, 아홉 개 폐기 예고에는 제거 버전도 붙어 있지 않다.
        documented = (
            f"@deprecated {len(decos)} 전부 문서화" if decos else "@deprecated 0 건이라 문서화 검사는 대상 없음"
        )
        print(f"[deprecationAudit] 통과. raw DeprecationWarning {len(rawWarns)} (전부 baseline), {documented}.")
        return 0

    if newRaw:
        print(
            f"[deprecationAudit] 신규 raw stdlib DeprecationWarning {len(newRaw)} 건 — DartlabDeprecationWarning/warnDeprecated 사용:"
        )
        for item in newRaw:
            print(f"  + {item}")
    if undocumented:
        print(f"[deprecationAudit] @deprecated 미문서화 {len(undocumented)} 건 — DEPRECATION.md 항목 추가:")
        for item in undocumented:
            print(f"  + {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
