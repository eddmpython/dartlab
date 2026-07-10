"""거울 작업대 순수성 가드 : 물질화 드라이버가 공개계약만 타는지 기계 차단 (audit).

거울 작업대(mainPlan/scenario-simulator/18 §5)는 parquet 직독·내부 리더(table.py)·Company 루프를
원천 배제한다. 이 가드는 그 규율을 사람 약속이 아니라 AST 로 강제한다.

- denylist 토큰(본질적 불완전이라 이중화): scan_parquet·read_parquet·read_csv·scan_csv·read_ipc·
  .parquet 리터럴·Company( 호출·table 내부 리더 import·_AXIS_REGISTRY 직독.
- import allowlist(완결적): 작업대 모듈은 정해진 상위 표면만 import 한다 (dartlab 루트 facade +
  reference.capability.mirror 커널 + core/polars). 새 우회 import 는 여기 없으면 RED.

대상 = src/dartlab/simulate/mirror.py (물질화 드라이버). 순수 커널(reference)은 엔진 접근 0 이라 제외.

사용:
    python -X utf8 tests/audit/workbenchPurity.py            # 리포트
    python -X utf8 tests/audit/workbenchPurity.py --check    # 위반 시 exit 2
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TARGETS = ["src/dartlab/simulate/mirror.py"]

# 데이터 우회 토큰 (문자열 등장 자체가 위반). denylist 는 불완전하므로 import allowlist 로 보강.
_DENY_TOKENS = (
    "scan_parquet",
    "read_parquet",
    "read_csv",
    "scan_csv",
    "read_ipc",
    "read_ndjson",
    ".parquet",
    "_AXIS_REGISTRY",
)
# 허용 import 접두 (allowlist = 완결적). 이 밖의 dartlab 서브패키지 import 는 우회로 간주.
_ALLOW_IMPORT_PREFIXES = (
    "dartlab.reference.capability.mirror",  # 순수 커널
    "dartlab.core",  # 하위 유틸
)
# dartlab 루트 facade 는 `import dartlab` (서브패키지 아님) 로만 허용.


def _scan(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    violations: list[str] = []

    for token in _DENY_TOKENS:
        if token in text:
            violations.append(f"denylist 토큰 '{token}' 등장 (데이터 우회)")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Company":
            violations.append(f"L{node.lineno}: Company( 호출 (per-company 루프 금지)")
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "dartlab":
                    continue  # 루트 facade 허용
                if name.startswith("dartlab.") and not name.startswith(_ALLOW_IMPORT_PREFIXES):
                    violations.append(f"L{node.lineno}: 비허용 dartlab import '{name}' (allowlist 밖)")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith("dartlab.") and not mod.startswith(_ALLOW_IMPORT_PREFIXES):
                violations.append(f"L{node.lineno}: 비허용 dartlab import '{mod}' (allowlist 밖)")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="위반 시 exit 2")
    args = parser.parse_args()

    total = 0
    for rel in _TARGETS:
        path = _REPO_ROOT / rel
        if not path.exists():
            continue
        violations = _scan(path)
        if violations:
            print(f"\n{rel}")
            for item in violations:
                print(f"  X {item}")
            total += len(violations)

    if total == 0:
        print("[workbenchPurity] OK - 작업대 드라이버 공개계약 순수 (우회 0).")
        return 0
    print(f"\n[workbenchPurity] 위반 {total} 건. 공개계약 3형태(가이드/무target/물질화)만 허용.")
    return 2 if args.check else 1


if __name__ == "__main__":
    raise SystemExit(main())
