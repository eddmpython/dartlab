"""Unified Data Workbench 계층 순수성 가드.

작업대는 owner의 공개 callable과 metadata provider를 조율할 뿐 parquet, Company 루프,
simulate, story, AI를 직접 소비하지 않는다. owner package의 dataProduct.py도 data를 역참조하지 않는다.

사용:
    python -X utf8 tests/audit/workbenchPurity.py            # 리포트
    python -X utf8 tests/audit/workbenchPurity.py --check    # 위반 시 exit 2
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_ROOT = _REPO_ROOT / "src/dartlab/dataHub"
_OWNER_PRODUCTS = tuple((_REPO_ROOT / "src/dartlab").glob("*/dataProduct.py"))

# 데이터 우회 토큰 (문자열 등장 자체가 위반). denylist 는 불완전하므로 import allowlist 로 보강.
_DENY_TOKENS = (
    "scan_parquet",
    "read_parquet",
    "read_csv",
    "scan_csv",
    "read_ipc",
    "read_ndjson",
    ".parquet",
    "dartlab.simulate",
    "dartlab.story",
    "dartlab.ai",
)
# 허용 import 접두. lower owner 실행은 root facade 또는 descriptor의 동적 callable만 탄다.
_ALLOW_IMPORT_PREFIXES = (
    "dartlab.dataHub",
    "dartlab.reference",
    "dartlab.core",
)
# dartlab 루트 facade 는 `import dartlab` (서브패키지 아님) 로만 허용.


def _isAllowedImport(name: str) -> bool:
    return any(name == prefix or name.startswith(f"{prefix}.") for prefix in _ALLOW_IMPORT_PREFIXES)


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
                if name.startswith("dartlab.") and not _isAllowedImport(name):
                    violations.append(f"L{node.lineno}: 비허용 dartlab import '{name}' (allowlist 밖)")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith("dartlab.") and not _isAllowedImport(mod):
                violations.append(f"L{node.lineno}: 비허용 dartlab import '{mod}' (allowlist 밖)")
    return violations


def _scanOwnerProduct(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            if name == "dartlab.dataHub" or name.startswith("dartlab.dataHub."):
                violations.append(f"L{node.lineno}: owner metadata가 data를 역참조함")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="위반 시 exit 2")
    args = parser.parse_args()

    total = 0
    targets = tuple(sorted(_DATA_ROOT.glob("*.py")))
    for path in targets:
        violations = _scan(path)
        if violations:
            print(f"\n{path.relative_to(_REPO_ROOT)}")
            for item in violations:
                print(f"  X {item}")
            total += len(violations)
    for path in _OWNER_PRODUCTS:
        violations = _scanOwnerProduct(path)
        if violations:
            print(f"\n{path.relative_to(_REPO_ROOT)}")
            for item in violations:
                print(f"  X {item}")
            total += len(violations)

    if total == 0:
        print("[workbenchPurity] OK - data 계층 역전과 원천 직독 0.")
        return 0
    print(f"\n[workbenchPurity] 위반 {total} 건. data는 owner 공개계약만 소비해야 합니다.")
    return 2 if args.check else 1


if __name__ == "__main__":
    raise SystemExit(main())
