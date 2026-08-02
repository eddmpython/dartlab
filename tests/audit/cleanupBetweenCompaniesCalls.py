"""M8: 다중 회사 loop 진입점에서 cleanupBetweenCompanies 호출 누락 검출.

heuristic AST 분석:
  - `for <var> in <iter>:` 패턴 검출
  - <var> 이름 (or <iter> 이름) 이 stockCodes/codes/tickers/parquetFiles 같은
    회사 시퀀스 가능성
  - loop body 안 ``loadData()`` / ``Company()`` 같은 회사별 무거운 호출 존재
  - loop body 안 ``cleanupBetweenCompanies(`` 호출 부재

세 조건 모두 만족 시 violation. baseline (``_baselines/cleanupCalls.json``) 외만 fail.

회피:
  - loop body 안 ``cleanupBetweenCompanies(label=...)`` 1 줄 추가
  - 또는 ``with Company(code) as c:`` 사용 (__exit__ 가 자동 호출 — 룰 11)
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_BASELINE = _REPO / "tests" / "audit" / "_baselines" / "cleanupCalls.json"
_SCAN_ROOTS = ("src/dartlab",)

_LOOP_VAR_HINTS = ("code", "ticker", "cik", "stock")  # 변수명 substring
_LOOP_ITER_HINTS = ("Codes", "codes", "Tickers", "tickers", "ciks")  # iterator 이름 substring
_HEAVY_CALLS = ("loadData", "Company", "_buildFinanceSeries")  # 회사별 무거운 호출


class _AuditVisitor(ast.NodeVisitor):
    """for loop 안 cleanup 호출 검출."""

    def __init__(self, rel: str) -> None:
        self.rel = rel
        self.violations: list[str] = []

    def visit_For(self, node: ast.For) -> None:
        if self._isCompanyLoop(node) and self._hasHeavyCall(node) and not self._hasCleanup(node):
            self.violations.append(f"{self.rel}:{node.lineno}")
        self.generic_visit(node)

    def _isCompanyLoop(self, node: ast.For) -> bool:
        # target 변수명 hint
        if isinstance(node.target, ast.Name):
            name = node.target.id.lower()
            if any(h in name for h in _LOOP_VAR_HINTS):
                return True
        # iter 이름 hint
        if isinstance(node.iter, ast.Name):
            if any(h in node.iter.id for h in _LOOP_ITER_HINTS):
                return True
        # iter 가 attribute / method call 면 source ast.unparse
        try:
            src = ast.unparse(node.iter)
        except Exception:  # noqa: BLE001
            return False
        return any(h in src for h in _LOOP_ITER_HINTS)

    def _hasHeavyCall(self, node: ast.For) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                callee = child.func
                if isinstance(callee, ast.Name) and callee.id in _HEAVY_CALLS:
                    return True
                if isinstance(callee, ast.Attribute) and callee.attr in _HEAVY_CALLS:
                    return True
        return False

    def _hasCleanup(self, node: ast.For) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                callee = child.func
                if isinstance(callee, ast.Name) and callee.id == "cleanupBetweenCompanies":
                    return True
                if isinstance(callee, ast.Attribute) and callee.attr == "cleanupBetweenCompanies":
                    return True
                # with Company(...) as c: 패턴 — __exit__ 가 자동 호출 (룰 11)
                if isinstance(callee, ast.Name) and callee.id == "Company":
                    # with 안에서 호출되는지 확인
                    pass
        # with statement 안 Company 사용도 안전
        for child in ast.walk(node):
            if isinstance(child, ast.With):
                for item in child.items:
                    if isinstance(item.context_expr, ast.Call):
                        f = item.context_expr.func
                        if isinstance(f, ast.Name) and f.id == "Company":
                            return True
                        if isinstance(f, ast.Attribute) and f.attr == "Company":
                            return True
                        if (
                            isinstance(f, ast.Call)
                            and isinstance(f.func, ast.Name)
                            and f.func.id == "getattr"
                            and len(f.args) >= 2
                            and isinstance(f.args[1], ast.Constant)
                            and f.args[1].value == "Company"
                        ):
                            return True
        return False


def _scanFile(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, OSError, SyntaxError):
        return []
    rel = str(path.relative_to(_REPO).as_posix())
    visitor = _AuditVisitor(rel)
    visitor.visit(tree)
    return visitor.violations


def _scanAll() -> list[str]:
    out: list[str] = []
    for root in _SCAN_ROOTS:
        for p in (_REPO / root).rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            out.extend(_scanFile(p))
    return sorted(out)


def _loadBaseline() -> set[str]:
    if _BASELINE.exists():
        return set(json.loads(_BASELINE.read_text(encoding="utf-8")).get("violations", []))
    return set()


def main() -> int:
    """audit 실행. baseline 외 violation 있으면 exit 1.

    Returns:
        exit code (0 = clean, 1 = 회귀).

    Raises:
        없음.

    Example:
        >>> main()
    """
    violations = set(_scanAll())
    allowed = _loadBaseline()
    new = violations - allowed
    if new:
        print("[cleanupCalls] 회귀 위반:")
        for v in sorted(new):
            print(f"  {v}")
        print(f"\n총 {len(new)} 건. cleanupBetweenCompanies() 호출 또는")
        print("with Company(code) as c: context manager 사용.")
        return 1
    print(f"[cleanupCalls] OK ({len(violations)} 알려진 violation, 회귀 0).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
