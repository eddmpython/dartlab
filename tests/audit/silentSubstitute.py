"""실패를 조용히 데이터로 바꾸는 자리 lint.

`checkSilentFail.py` 는 2026-04-19 사고 class 인 "파일 부재 시 빈 값" 만 본다. 그런데
라이브러리에서 실제로 지배적인 침묵 패턴은 다른 모양이다. 잡아 놓고 대체값을 흘려보내면
호출자는 실패를 데이터로 받는다. 잘못된 값과 "값 없음" 이 구분되지 않고, 원인은
traceback 째로 사라진다.

세 모양을 본다. 처음에는 첫째만 봤는데, 일곱 계층 전수 검토에서 나머지 둘이 같은 무게로
반복해 나왔다.

1. 넓은 catch 가 `return None` / `return {}` / `return 0` 으로 대체값을 돌려주는 것.
2. `except ...: renewed = False` 처럼 이름에 상수를 꽂고 흐름을 잇는 것. 일시적 오류와
   진짜 실패가 같은 값이 되어 읽는 쪽이 둘을 구분할 수 없다.
3. 모으는 반복문 안에서 `except ...: continue` 로 실패한 항목을 건너뛰는 것. 결과 목록만
   보면 그 항목이 원래 없었는지 처리하다 실패했는지 알 수 없다. 스무 검사가 전부 예외로
   죽어도 "20개 전부 통과" 가 찍히던 사고가 정확히 이 모양이었다.

2 번과 3 번은 좁은 except 도 대상이다. 좁게 잡았다는 것이 원인을 버려도 된다는 뜻은 아니다.

이 가드가 요구하는 것은 흐름 변경이 아니라 기록이다. 같은 자리에서 원인을 한 줄
남기면(로거 호출 또는 `recordFailure`) 통과한다. 그래서 baseline 을 줄이는 작업이
동작을 바꾸지 않는다.

키는 `상대경로::함수명` 이라 줄 이동에 흔들리지 않는다. 한 함수 안의 여러 handler 는
한 항목으로 접힌다.

사용법::

    uv run python -X utf8 tests/audit/silentSubstitute.py
    uv run python -X utf8 tests/audit/silentSubstitute.py --update-baseline
    uv run python -X utf8 tests/audit/silentSubstitute.py --strict

종료 코드: 0 통과 / 1 baseline 밖 신규 위반
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
_DEFAULT_TARGET = _REPO / "src" / "dartlab"
_BASELINE = _REPO / "tests" / "audit" / "_baselines" / "silentSubstitute.json"

_BROAD_NAMES = frozenset({"Exception", "BaseException"})
_LOG_METHODS = frozenset({"debug", "info", "warning", "warn", "error", "exception", "critical"})
_LOG_FUNCTIONS = frozenset({"recordFailure", "recordDuration"})


def _handlerIsBroad(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    parts = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    for part in parts:
        name = getattr(part, "id", None) or getattr(part, "attr", None)
        if name in _BROAD_NAMES:
            return True
    return False


def _isSubstituteValue(node: ast.expr) -> bool:
    """호출자가 데이터로 오인할 수 있는 대체값인지 판정한다."""

    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Dict):
        return not node.keys
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return not node.elts
    if isinstance(node, ast.Call):
        name = getattr(node.func, "id", None)
        return name in {"dict", "list", "set", "tuple"} and not node.args and not node.keywords
    return False


def _recordsCause(handler: ast.ExceptHandler) -> bool:
    """handler 안에서 원인을 한 줄이라도 남기는지 확인한다."""

    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "attr", None) in _LOG_METHODS:
            return True
        if getattr(node.func, "id", None) in _LOG_FUNCTIONS:
            return True
    return False


def _isSilentSubstitute(handler: ast.ExceptHandler) -> bool:
    if not _handlerIsBroad(handler) or _recordsCause(handler):
        return False
    body = [stmt for stmt in handler.body if not isinstance(stmt, ast.Pass)]
    if not body:
        return False
    return all(
        isinstance(stmt, ast.Return) and stmt.value is not None and _isSubstituteValue(stmt.value) for stmt in body
    )


def _isSilentAssign(handler: ast.ExceptHandler) -> bool:
    """실패했을 때 이름에 상수를 꽂고 흐름을 잇는 자리인지 본다.

    `return` 만 보던 규칙이 놓치던 모양이다. `except ...: renewed = False` 처럼 쓰면
    일시적 오류와 진짜 실패가 같은 값이 되고, 그 이름을 읽는 쪽은 둘을 구분할 수 없다.
    좁은 except 도 대상이다. 좁게 잡았다는 것이 원인을 버려도 된다는 뜻은 아니다.
    """
    if _recordsCause(handler):
        return False
    body = [stmt for stmt in handler.body if not isinstance(stmt, ast.Pass)]
    if not body:
        return False
    return all(isinstance(stmt, ast.Assign) and _isSubstituteValue(stmt.value) for stmt in body)


def _isSilentLoopSkip(handler: ast.ExceptHandler, loopHandlerIds: set[int]) -> bool:
    """모으는 반복문 안에서 실패한 항목을 소리 없이 건너뛰는 자리인지 본다.

    결과 목록만 보면 그 항목이 원래 없었는지 처리하다 실패했는지 알 수 없다. 스무 검사가
    전부 예외로 죽어도 "전부 통과" 가 찍히던 사고가 정확히 이 모양이었다.
    """
    if id(handler) not in loopHandlerIds or _recordsCause(handler):
        return False
    body = [stmt for stmt in handler.body if not isinstance(stmt, ast.Pass)]
    return bool(body) and all(isinstance(stmt, ast.Continue) for stmt in body)


def _handlersInsideLoops(tree: ast.AST) -> set[int]:
    """반복문 몸통 안에 있는 handler 의 id 집합."""
    inside: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.ExceptHandler):
                inside.add(id(child))
    return inside


def _scan(target: Path) -> list[str]:
    found: set[str] = set()
    for path in sorted(target.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        relative = path.relative_to(_REPO).as_posix()
        loopHandlerIds = _handlersInsideLoops(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for inner in ast.walk(node):
                if not isinstance(inner, ast.ExceptHandler):
                    continue
                if _isSilentSubstitute(inner) or _isSilentAssign(inner) or _isSilentLoopSkip(inner, loopHandlerIds):
                    found.add(f"{relative}::{node.name}")
                    break
    return sorted(found)


def _loadBaseline(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("violations", []))


def main() -> int:
    """대체값 침묵 자리를 세고 baseline 밖 신규 위반만 실패로 올린다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=str(_DEFAULT_TARGET.relative_to(_REPO).as_posix()))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--baseline", default=None)
    args = parser.parse_args()

    baselinePath = (_REPO / args.baseline).resolve() if args.baseline else _BASELINE
    target = (_REPO / args.target).resolve()
    if not target.exists():
        print(f"ERROR: target 부재 ({target})", file=sys.stderr)
        return 1

    violations = _scan(target)
    print(f"=== silent substitute audit: {args.target} ===")
    print(f"실패를 원인 없이 대체값으로 바꾸는 함수: {len(violations)} 개")

    if args.update_baseline:
        baselinePath.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "_note": (
                "광범위 catch 가 원인을 버리고 대체값을 반환하는 자리 부채 원장. 항목을 "
                "지우려면 흐름을 바꾸지 말고 같은 자리에 원인 한 줄을 남기면 된다. "
                "줄이는 방향으로만 갱신한다."
            ),
            "violations": violations,
        }
        baselinePath.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"baseline 갱신: {baselinePath.relative_to(_REPO)}")
        return 0

    allowed = set(_loadBaseline(baselinePath))
    fresh = violations if args.strict else [item for item in violations if item not in allowed]

    if fresh:
        label = "STRICT" if args.strict else "baseline 외 신규"
        print(f"\n=== {label} 위반 {len(fresh)} 건 ===")
        for item in fresh[:30]:
            print(f"  {item}")
        if len(fresh) > 30:
            print(f"  ... 외 {len(fresh) - 30} 건")
        print("\n같은 자리에 원인 한 줄을 남기면 통과한다. 흐름은 바꾸지 않아도 된다.")
        return 1

    print("\n=== baseline 안 통과 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
