"""stale top-level import lint — `from dartlab import X` / `import dartlab as Y` 잔존 검출.

F6 (PEP 562 lazy facade) 의 종료 조건은 src/ 내부에서 top-level dartlab 모듈 경유
import 가 0 인 것. lazy facade 로 빠진 후 어떤 모듈이 `from dartlab import Company`
하면 facade `_CallableModule.__getattr__` 재진입 → 정적 chain 차단 효과가 무효화.

정공법: 서브패키지 직접 import. `from dartlab.company import Company`,
`from dartlab.config import ...`, `from dartlab.providers.dart import OpenDart` 등.

검사 대상:
    src/dartlab/ 내부 모든 .py (자기 자신인 src/dartlab/__init__.py 제외).
    skills/ 같은 *.md 는 무시 (실제 import 가 아님).

스킬·문서 안 예시 코드는 사용자용 — 정상. 본 lint 의 관심은 패키지 내부.

실행::

    uv run python -X utf8 tests/audit/staleImports.py            # 보고
    uv run python -X utf8 tests/audit/staleImports.py --strict   # 위반 ≥ 1 → exit 2

종료 코드:
    0 — 잔존 0 (또는 --strict 미지정)
    2 — 잔존 ≥ 1 + --strict
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src" / "dartlab"

# 잡고 싶은 패턴:
#   from dartlab import Company
#   from dartlab import Company, config
#   from dartlab import (Company, config)
#   import dartlab as _dl
#   import dartlab
# 단, `from dartlab.xxx import ...` (서브패키지 직접) 는 정상.
# 선두 공백은 [ \t]* (줄-로컬) — `\s*` 는 `\n` 도 매칭해 빈 줄 위의 indented import 를
# cross-line 으로 잡아 line 번호·col-0 판정을 오염시킨다(잠재 버그, debt-honesty P1-2 에서 발견).
_RE_FROM_TOP = re.compile(r"^[ \t]*from\s+dartlab\s+import\s+(.+?)(?:\s*#.*)?$", re.MULTILINE)
_RE_IMPORT_TOP = re.compile(r"^[ \t]*import\s+dartlab(?:\s+as\s+\w+)?(?:\s*#.*)?\s*$", re.MULTILINE)

# 면제 — facade 본체 + 의도된 entry 모듈.
_EXEMPT_FILES: tuple[str, ...] = (
    "src/dartlab/__init__.py",  # facade 본체
    "src/dartlab/_aiEntries.py",  # F6.1 ask/templates/saveTemplate 본체
    "src/dartlab/server/__init__.py",  # server 가 dartlab 전체를 노출하는 facade
    "src/dartlab/api.py",  # 공개 API 단축 모듈 (필요 시 별도 정리)
    # RunPython sandbox 는 사용자 코드 globals 에 dartlab top-level 을 노출하는
    # 의도된 facade entry — 본문 안 ``import dartlab`` 은 sandbox 환경 구성.
    "src/dartlab/ai/tools/runPython.py",
    # LLM prompt 텍스트 안 사용자용 코드 예시 (markdown 코드 블록) — 실제
    # 패키지 내부 import 가 아니라 사용자에게 보여주는 권장 사용법.
    "src/dartlab/ai/workbench/prompts.py",
    # 스킬 spec 템플릿 생성기 — 본문 ``import dartlab`` 은 emit 하는 .md 템플릿의
    # ```python 예시 코드 (실제 import 아님, prompts.py 와 동류). (debt-honesty P1-2)
    "src/dartlab/skills/addAxis.py",
    "src/dartlab/skills/addEngine.py",
)


def _normPath(p: Path) -> str:
    return p.relative_to(_REPO_ROOT).as_posix()


def _isExempt(file: Path) -> bool:
    rel = _normPath(file)
    return rel in _EXEMPT_FILES


def _findStale(file: Path) -> list[tuple[int, str, bool]]:
    """파일 안 stale top-level dartlab import 위치/스니펫/모듈레벨여부 반환.

    ``moduleLevel`` = col-0 import (진짜 F6 위반 — facade 정적 chain 무효화).
    indented import 는 함수-local lazy (sandbox / cycle-break 의도) — 정보용.
    """
    try:
        source = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    # 정규식은 docstring 안의 사용 예시도 import 로 셌다. 실제로 `providers/{dart,edgar}/
    # openapi/__init__.py` 두 항목은 모듈 docstring 3 번째 줄의 예제였다. AST 는 문법
    # 구조를 보므로 문자열 안의 같은 문구를 import 로 오인하지 않는다.
    out: list[tuple[int, str, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module != "dartlab" or (node.level or 0) > 0:
                continue
            names = ", ".join(
                alias.name if alias.asname is None else f"{alias.name} as {alias.asname}" for alias in node.names
            )
            snippet = f"from dartlab import {names}"
        elif isinstance(node, ast.Import):
            aliases = [alias for alias in node.names if alias.name == "dartlab"]
            if not aliases:
                continue
            alias = aliases[0]
            snippet = "import dartlab" if alias.asname is None else f"import dartlab as {alias.asname}"
        else:
            continue
        out.append((node.lineno, snippet, node.col_offset == 0))
    return out


def _scan() -> tuple[dict[str, list[tuple[int, str]]], int]:
    """src/dartlab/ 전수. (module-level {파일: [(line, snippet)]}, function-local 총수).

    module-level(col-0) 만 F6 위반 — function-local lazy 는 의도된 패턴이라 분리 집계.
    """
    moduleLevel: dict[str, list[tuple[int, str]]] = defaultdict(list)
    funcLocal = 0
    for f in _SRC.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        if _isExempt(f):
            continue
        for line, snippet, isModule in _findStale(f):
            if isModule:
                moduleLevel[_normPath(f)].append((line, snippet))
            else:
                funcLocal += 1
    return dict(moduleLevel), funcLocal


_BASELINE = _REPO_ROOT / "tests" / "audit" / "_baselines" / "staleImports.json"


def _baselineKeys(results: dict[str, list[tuple[int, str]]]) -> set[str]:
    """module-level 위반을 line 무관 ``relpath::snippet`` 키 set 으로 (line 이동 견고)."""
    return {f"{rel}::{snippet}" for rel, items in results.items() for _line, snippet in items}


def _loadBaseline() -> set[str]:
    if not _BASELINE.exists():
        raise SystemExit(f"[staleImports] baseline 부재: {_BASELINE}. --write-baseline 로 박제 후 재실행.")
    import json

    return set(json.loads(_BASELINE.read_text(encoding="utf-8-sig")).get("violations", []))


def _writeBaseline(results: dict[str, list[tuple[int, str]]]) -> None:
    import json

    _BASELINE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "violations": sorted(_baselineKeys(results)),
        "_note": (
            "module-level(col-0) stale top-level dartlab import 알려진 사이트 (relpath::snippet). "
            "function-local lazy(sandbox/cycle-break)는 제외 — 의도된 패턴. 본 목록은 ratchet "
            "부채(신규 col-0 차단·목표 0, server/skills.add* codemod 후 축소). (debt-honesty P1-2)"
        ),
    }
    _BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[staleImports] baseline 박제 → {_BASELINE} ({len(payload['violations'])} module-level 사이트)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="module-level 잔존 ≥ 1 → exit 2 (baseline 무시)")
    parser.add_argument(
        "--check", action="store_true", help="baseline 대비 신규 module-level 잔존 ≥ 1 → exit 2 (CI 배선용)"
    )
    parser.add_argument("--write-baseline", action="store_true", help="현재 module-level 잔존을 baseline 박제")
    parser.add_argument("--quiet", action="store_true", help="violations 만 출력")
    args = parser.parse_args()

    results, funcLocal = _scan()
    total = sum(len(v) for v in results.values())

    if args.write_baseline:
        _writeBaseline(results)
        return 0

    if not args.quiet:
        print("=" * 72)
        print("stale top-level dartlab import lint (module-level=col-0 만 위반)")
        print("=" * 72)

    if results:
        for relPath in sorted(results):
            print(f"\n{relPath}")
            for line, snippet in results[relPath]:
                print(f"  L{line}  {snippet}")
        if not args.quiet:
            print(
                f"\nmodule-level 잔존: {total} 건 ({len(results)} 파일) · function-local(의도된 lazy): {funcLocal} 건"
            )
            print("→ 서브패키지 직접 import 로 변환. 예: `from dartlab.company import Company`.")
    elif not args.quiet:
        print(f"\nmodule-level 잔존 0 건 OK — F6 종료 조건 충족. (function-local lazy {funcLocal} 건은 의도)")

    if args.check:
        new = sorted(_baselineKeys(results) - _loadBaseline())
        if new:
            print(f"\n[staleImports] 신규 module-level stale import {len(new)} 건 (baseline 초과 = 회귀):")
            for item in new:
                print(f"  + {item}")
            return 2
        return 0
    if args.strict and total > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
