"""G1 게이트: browser-as-server 엔드포인트는 전부 async def 여야 한다.

sync `def` 엔드포인트는 Starlette 가 `anyio.to_thread` 로 돌린다. pyodide 는 스레드를 못 띄워
`RuntimeError: can't start new thread` 로 죽는다(실측). 그래서 `dartlab.webapi.browserApi` 의
`@app.get`/`@app.post` 데코레이트 함수는 반드시 AsyncFunctionDef 여야 한다.

dartlab 을 import 하지 않는다(AST 정적 검사만). 설계: mainPlan/browser-as-server-ssot/02 G1.

실행: uv run python -X utf8 tests/audit/browserApiAsync.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[2] / "src" / "dartlab" / "webapi" / "browserApi.py"
_ROUTE_DECORATORS = {"get", "post", "put", "delete", "patch"}


def _isRouteDecorator(node: ast.expr) -> bool:
    """@app.get(...) / @router.post(...) 형태인지."""
    call = node if isinstance(node, ast.Call) else None
    func = call.func if call else node
    return isinstance(func, ast.Attribute) and func.attr in _ROUTE_DECORATORS


def findSyncEndpoints(source: str) -> list[str]:
    """route 데코레이터가 붙은 sync def 엔드포인트 이름 목록(위반)."""
    tree = ast.parse(source)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and any(_isRouteDecorator(d) for d in node.decorator_list):
            violations.append(f"{node.name} (line {node.lineno})")
    return violations


def main() -> int:
    if not _TARGET.exists():
        print(f"[browserApiAsync] 대상 없음: {_TARGET}")
        return 0
    violations = findSyncEndpoints(_TARGET.read_text(encoding="utf-8"))
    if violations:
        print("[browserApiAsync] FAIL: sync def 엔드포인트(브라우저에서 can't start new thread):")
        for v in violations:
            print(f"  - {v}")
        print("  -> async def 로 바꿔라. dartlab 호출은 async 함수 안에서 직접(스레드 안 씀).")
        return 1
    print("[browserApiAsync] PASS: 모든 엔드포인트 async.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
