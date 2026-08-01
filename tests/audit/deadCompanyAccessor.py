"""Company 에 없는 이름을 부르는 자리를 찾는다.

2026-07-28 하루에 같은 결함을 열두 번 만났다. 공개 계약을 좁히면서 옛 이름을 부르던
소비처를 같이 안 고쳤고, `getattr(company, "X", None)` 과 넓은 except 가 그 실패를 지웠다.
예외가 안 나니 어느 게이트도 못 봤고, 사용자 표면 넷이 통째로 죽은 채 초록불이었다.

    - `dartlab report` 가 빈 제목 네 개만 출력 (BS · IS · CF · ratios · insights)
    - 재무 차트 다섯이 매번 데이터 없음 예외 (IS · BS · CF · dividend)
    - 차트 spec 생성기 여덟 중 일곱이 늘 None (annual · ratioSeries · insights · dividend)
    - DCF 밸류에이션 도구가 모든 회사에서 실패 (finance · sharesOutstanding · currentPrice)

그래서 이 감사를 둔다. 회귀가 아니라 *이 계열의 재유입*을 막는 것이 목적이다.

판정 기준은 이름 하나다. `company.X` 또는 `getattr(company, "X", ...)` 로 부르는 X 가
Company 정의 어디에도 없으면 위반이다. 표면은 provider company 파일에서 정적으로 모은다
(클래스 메서드 · 클래스 변수 · `self.X =` 대입). 실행이 필요 없어 데이터 없이도 돈다.

사용법::

    python tests/audit/deadCompanyAccessor.py            # 신규 위반만 차단
    python tests/audit/deadCompanyAccessor.py --json     # 기계 판독
    python tests/audit/deadCompanyAccessor.py --update   # 현재 상태를 원장으로 저장

종료 코드: 0 신규 위반 없음 / 1 신규 위반 발견.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src" / "dartlab"
_BASELINE = _ROOT / "tests" / "audit" / "_baselines" / "deadCompanyAccessor.json"

# Company 표면을 정의하는 파일. 여기서 이름을 모은다.
_SURFACE_FILES = (
    "company.py",
    "providers/dart/company.py",
    "providers/edgar/company.py",
)

# 표면 파일 밖에서 붙는 이름. 정적 수집이 못 보는 것만 최소로 둔다.
_EXTRA_SURFACE = frozenset({"_cache", "_hintedKeys"})

# Company 가 아니라 stub/wrapper 에 실려 오는 이름. 부르는 쪽 변수명이 `company` 일 뿐이라
# 정적으로는 구분이 안 된다. 붙이는 자리를 확인하고 등재한다.
#
#   benchmark · benchmarkMode : quant/screen/axTechnical.py 가 wrapper 에 대입
#   _quant_arrays             : quant/strategy/_backtestAdvanced.py 의 로컬 _Stub 캐시
#   _strategy_start           : quant/screen/axStrategy.py 의 _StubCompany 생성 인자
#   _storyLensProducts        : story/lensProducts.py 가 같은 함수에서 setattr 로 심는다
_INJECTED_ATTRS = frozenset({"benchmark", "benchmarkMode", "_quant_arrays", "_strategy_start", "_storyLensProducts"})

# `company` / `comp` 라는 이름이 Company 가 아닌 자리. 여기서 나온 속성은 세지 않는다.
_NON_COMPANY_ATTRS = frozenset(
    {
        "get",
        "setdefault",
        "values",
        "keys",
        "items",
        "exists",
        "glob",
        "company",
    }
)

_TARGET_VARS = frozenset({"company", "comp"})


def collectSurface() -> set[str]:
    """Company 가 실제로 갖는 이름 전수 (정적)."""
    names: set[str] = set(_EXTRA_SURFACE)
    for rel in _SURFACE_FILES:
        path = _SRC / rel
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        names.add(item.name)
                    elif isinstance(item, ast.Assign):
                        names.update(t.id for t in item.targets if isinstance(t, ast.Name))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and _isSelf(target.value):
                        names.add(target.attr)
    return names


def _isSelf(node: ast.expr) -> bool:
    return isinstance(node, ast.Name) and node.id == "self"


class _Visitor(ast.NodeVisitor):
    """`company.X` 와 `getattr(company, "X", ...)` 를 모은다."""

    def __init__(self, rel: str, surface: set[str]) -> None:
        self.rel = rel
        self.surface = surface
        self.hits: list[tuple[str, str, int]] = []

    def _record(self, attr: str, lineno: int) -> None:
        if attr.startswith("__") or attr in self.surface or attr in _NON_COMPANY_ATTRS:
            return
        if attr in _INJECTED_ATTRS:
            return
        self.hits.append((attr, self.rel, lineno))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in _TARGET_VARS:
            self._record(node.attr, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id == "getattr" and len(node.args) >= 2:
            target, name = node.args[0], node.args[1]
            if (
                isinstance(target, ast.Name)
                and target.id in _TARGET_VARS
                and isinstance(name, ast.Constant)
                and isinstance(name.value, str)
            ):
                self._record(name.value, node.lineno)
        self.generic_visit(node)


def scan() -> list[dict[str, object]]:
    """전 소스에서 위반 후보를 모은다."""
    surface = collectSurface()
    found: list[dict[str, object]] = []
    for path in sorted(_SRC.rglob("*.py")):
        rel = path.relative_to(_SRC).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        visitor = _Visitor(rel, surface)
        visitor.visit(tree)
        for attr, where, lineno in visitor.hits:
            found.append({"attr": attr, "file": where, "line": lineno})
    return found


def _key(item: dict[str, object]) -> str:
    return f"{item['attr']}@{item['file']}"


def loadBaseline() -> set[str]:
    if not _BASELINE.exists():
        return set()
    data = json.loads(_BASELINE.read_text(encoding="utf-8"))
    return set(data.get("known", []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="기계 판독 출력")
    parser.add_argument("--update", action="store_true", help="현재 상태를 원장으로 저장")
    args = parser.parse_args(argv)

    found = scan()
    if args.update:
        _BASELINE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "policy": "no_new_violations",
            "note": "Company 에 없는 이름을 부르는 자리. 신규 추가만 차단한다.",
            "known": sorted({_key(item) for item in found}),
        }
        _BASELINE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[dead-company-accessor] 원장 저장 {len(payload['known'])} 건 -> {_BASELINE}")
        return 0

    baseline = loadBaseline()
    fresh = [item for item in found if _key(item) not in baseline]

    if args.json:
        print(json.dumps({"total": len(found), "new": fresh}, indent=2, ensure_ascii=False))
        return 1 if fresh else 0

    if fresh:
        print(f"[dead-company-accessor] 신규 위반 {len(fresh)} 건 (원장 {len(baseline)} 건)")
        for item in fresh:
            print(f"  {item['file']}:{item['line']}  company.{item['attr']}")
        print("\nCompany 에 없는 이름이다. 공개 계약(panel · analysis · capital 등)으로 부르거나,")
        print("정말 Company 가 아니면 변수 이름을 바꿔라. 오탐이면 --update 로 원장에 올린다.")
        return 1

    print(f"[dead-company-accessor] OK. 신규 위반 0 (원장 {len(baseline)} 건 / 현재 {len(found)} 건).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
