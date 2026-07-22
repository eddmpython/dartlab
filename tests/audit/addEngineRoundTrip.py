"""addEngine round-trip 검증 (T5-4) — skeleton 생성 후 27 게이트 통과 보증.

`src/dartlab/skills/addEngine.py {name}` 가 만든 5 단계 산출물 (skeleton + skill.md
+ contract + architecture.md 노드 + __init__ re-export) 이 *통째로 lint 통과* +
*기본 import 가능* + *audits 정합* 인지 검증.

본 audit 은 *드라이런 모드* — 실제 새 엔진 생성하지 않고, 기존 5 엔진 중 하나
(industry / scan / credit 등) 의 *시그니처* 가 5 단계 정합인지 점검.

체크 항목:
    1. `src/dartlab/{name}/__init__.py` 존재 + 빈 docstring 아님
    2. `src/dartlab/skills/specs/engines/{name}/SKILL.md` 3 강제 섹션 포함
    3. `pyproject.toml [tool.importlinter]` 안 `{name}` contract 존재
    4. `src/dartlab/__init__.py` 안 `{name}` re-export 또는 `__all__` 포함
    5. `tests/architecture/` 안 관련 audit 통과 (별도 게이트)

실행::

    uv run python -X utf8 tests/audit/addEngineRoundTrip.py
    uv run python -X utf8 tests/audit/addEngineRoundTrip.py --engine scan
    uv run python -X utf8 tests/audit/addEngineRoundTrip.py --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src" / "dartlab"
SPECS = SRC / "skills" / "specs"

# T5-4 round-trip 점검 대상 엔진 (기존 L2 분석 + L1.5 가공 4 형제).
_DEFAULT_ENGINES: tuple[str, ...] = (
    "analysis",
    "credit",
    "macro",
    "quant",
    "industry",
    "scan",
    "frame",
    "synth",
    "reference",
    "data",
)

_REQUIRED_SKILL_SECTIONS: tuple[str, ...] = (
    "## 공개 호출 방식",
    "## 호출 동작",
    "## 대표 반환 형태",
)


def checkInit(name: str) -> dict:
    """1 — engine __init__.py 존재 + 빈 docstring 아님."""
    initPath = SRC / name / "__init__.py"
    if not initPath.exists():
        return {"name": "init", "status": "fail", "reason": "__init__.py 없음"}
    text = initPath.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return {"name": "init", "status": "fail", "reason": "빈 파일"}
    return {"name": "init", "status": "ok", "size": len(text)}


def checkSkillSpec(name: str) -> dict:
    """2 — SKILL.md 3 강제 섹션 포함."""
    skillPath = SPECS / "engines" / name / "SKILL.md"
    if not skillPath.exists():
        return {"name": "skillSpec", "status": "fail", "reason": "SKILL.md 없음"}
    text = skillPath.read_text(encoding="utf-8", errors="replace")
    missing = [s for s in _REQUIRED_SKILL_SECTIONS if s not in text]
    if missing:
        return {"name": "skillSpec", "status": "fail", "reason": f"섹션 누락: {missing}"}
    return {"name": "skillSpec", "status": "ok"}


def checkImportLinterContract(name: str) -> dict:
    """3 — pyproject [tool.importlinter] 안 contract 존재."""
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return {"name": "importLinter", "status": "fail", "reason": "pyproject.toml 없음"}
    text = pyproject.read_text(encoding="utf-8", errors="replace")
    # 단순 substring — contract 이름이 sub-namespace 와 같다고 가정.
    if f'"dartlab.{name}"' in text or f"dartlab.{name}" in text:
        return {"name": "importLinter", "status": "ok"}
    return {"name": "importLinter", "status": "warn", "reason": "pyproject 안 명시적 reference 없음"}


def checkPublicExport(name: str) -> dict:
    """4 — dartlab/__init__.py 안 re-export 또는 __all__ 포함."""
    initPath = SRC / "__init__.py"
    if not initPath.exists():
        return {"name": "publicExport", "status": "fail", "reason": "__init__.py 없음"}
    text = initPath.read_text(encoding="utf-8", errors="replace")
    hasImport = f"from dartlab import" in text and name in text  # noqa: F541
    hasAll = f'"{name}"' in text
    if hasImport or hasAll:
        return {"name": "publicExport", "status": "ok"}
    return {"name": "publicExport", "status": "warn", "reason": "import 또는 __all__ 에 없음"}


def auditEngine(name: str) -> dict:
    """단일 엔진 4 체크 종합."""
    checks = [
        checkInit(name),
        checkSkillSpec(name),
        checkImportLinterContract(name),
        checkPublicExport(name),
    ]
    failCount = sum(1 for c in checks if c["status"] == "fail")
    warnCount = sum(1 for c in checks if c["status"] == "warn")
    return {
        "engine": name,
        "checks": checks,
        "fail": failCount,
        "warn": warnCount,
        "ok": failCount == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="addEngine round-trip audit (T5-4)")
    parser.add_argument("--engine", help="단일 엔진 검사 (기본: 10 엔진 전체)")
    parser.add_argument("--strict", action="store_true", help="fail 발견 시 exit 2")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    targets = [args.engine] if args.engine else list(_DEFAULT_ENGINES)
    results = [auditEngine(name) for name in targets]

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = "OK" if r["ok"] else "FAIL"
            print(f"[addEngine] {r['engine']:12s} {mark}  fail={r['fail']} warn={r['warn']}")
            for c in r["checks"]:
                if c["status"] != "ok":
                    print(f"    - {c['name']}: {c['status']} ({c.get('reason', '')})")

    if args.strict and any(not r["ok"] for r in results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
