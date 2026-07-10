"""축 선언 커버리지 부채 원장 : capability 반사가 엔진 선언을 버리지 않는지 + 손테이블 완결성.

거울 작업대(mainPlan/scenario-simulator/18)의 자동흡수는 "축 엔트리의 선언 필드를 소비측이 읽을 수
있다"에 의존한다. 이 게이트는 그 선언이 조용히 사라지는 회귀를 막는다. 세 부채를 baseline 원장으로
동결한다 (도태는 측정, 125/125 강요 안 함).

1. **축수 동결**: 엔진별 축 수는 축소만 알린다. scan 축이 통째로 사라지면 RED (scan/__init__ ->
   scan/router 이전으로 scan 축이 누락됐던 사건류의 재발 가드).
2. **declared 미보유 축소만**: declared 를 못 실은 축 집합은 baseline 대비 늘면 RED. 줄면(선언 보강)
   baseline 갱신 대상. 현재 0 이라 어떤 미선언 등장도 회귀.
3. **손테이블 완결성**: 새 엔진 등록은 두 손테이블(_AXIS_REGISTRIES · _CALLABLE_MODULE_MAP)에
   손편집이 필요하다(addEngine.py 미접촉). 둘의 불일치를 baseline 으로 동결해 새 불일치를 막는다
   (현재 credit·gather 가 _CALLABLE_MODULE_MAP 에 누락된 부채가 baseline 에 박제된다).

사용:
    python -X utf8 tests/audit/axisDeclaredCoverage.py            # 리포트
    python -X utf8 tests/audit/axisDeclaredCoverage.py --check    # CI: baseline 초과 회귀 시 exit 2
    python -X utf8 tests/audit/axisDeclaredCoverage.py --write-baseline
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASELINE = _REPO_ROOT / "tests" / "audit" / "_baselines" / "axisDeclaredCoverage.json"


def _callableModuleEngines() -> list[str]:
    """_CALLABLE_MODULE_MAP(builder.py 함수 지역 상수)에 등록된 엔진. 소스에서 정적 추출."""
    import dartlab.reference.capability.builder as builder

    src = inspect.getsource(builder)
    match = re.search(r"_CALLABLE_MODULE_MAP\s*=\s*\{(.*?)\}", src, re.DOTALL)
    return re.findall(r'"(\w+)":', match.group(1)) if match else []


def _survey() -> dict:
    """현재 상태 실측 → {axisCounts, undeclared, handTableMismatch}."""
    from dartlab.reference.capability import loadCapabilities
    from dartlab.reference.capability.builder import _AXIS_REGISTRIES

    caps = loadCapabilities()
    axisCounts: dict[str, int] = {}
    undeclared: list[str] = []
    for key, entry in caps.items():
        if not (isinstance(entry, dict) and str(entry.get("kind", "")).endswith("_axis")):
            continue
        engine = key.split(".", 1)[0]
        axisCounts[engine] = axisCounts.get(engine, 0) + 1
        if not entry.get("declared"):
            undeclared.append(key)

    regEngines = {prefix for prefix, _, _ in _AXIS_REGISTRIES}
    callableEngines = set(_callableModuleEngines())
    # 축 보유 엔진인데 _CALLABLE_MODULE_MAP 에 없는 것 = 새 엔진 등록 시 놓치기 쉬운 손편집
    mismatch = sorted(regEngines - callableEngines)
    return {
        "axisCounts": dict(sorted(axisCounts.items())),
        "undeclared": sorted(undeclared),
        "handTableMismatch": mismatch,
    }


def _loadBaseline() -> dict:
    if not _BASELINE.exists():
        raise SystemExit(f"[axisDeclaredCoverage] baseline 부재: {_BASELINE}. --write-baseline 로 박제 후 재실행.")
    return json.loads(_BASELINE.read_text(encoding="utf-8"))


def _writeBaseline(state: dict) -> None:
    _BASELINE.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[axisDeclaredCoverage] baseline 박제 -> {_BASELINE}")
    print(
        f"  축수 {sum(state['axisCounts'].values())} | 미선언 {len(state['undeclared'])} | 손테이블 불일치 {state['handTableMismatch']}"
    )


def _diff(state: dict, base: dict) -> list[str]:
    """baseline 대비 회귀만 수집 (개선 방향은 통과)."""
    reg: list[str] = []
    for engine, baseCount in base["axisCounts"].items():
        now = state["axisCounts"].get(engine, 0)
        if now < baseCount:
            reg.append(f"축수 감소 {engine}: {baseCount} -> {now} (엔진/축 탈락 = 회귀)")
    newUndeclared = sorted(set(state["undeclared"]) - set(base["undeclared"]))
    for key in newUndeclared:
        reg.append(f"신규 미선언 축: {key} (declared 를 못 실음 = 선언 버려짐)")
    newMismatch = sorted(set(state["handTableMismatch"]) - set(base["handTableMismatch"]))
    for engine in newMismatch:
        reg.append(f"신규 손테이블 불일치: {engine} 가 _CALLABLE_MODULE_MAP 누락")
    return reg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="baseline 초과 회귀 시 exit 2 (CI 배선용)")
    parser.add_argument("--write-baseline", action="store_true", help="현재 상태를 baseline 박제")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    state = _survey()
    if args.write_baseline:
        _writeBaseline(state)
        return 0

    total = sum(state["axisCounts"].values())
    declared = total - len(state["undeclared"])
    if not args.quiet:
        print("=" * 72)
        print("축 선언 커버리지 부채 원장")
        print("=" * 72)
        print(f"축수 {total} | declared {declared}/{total} | 손테이블 불일치 {state['handTableMismatch']}")
        for engine, count in state["axisCounts"].items():
            print(f"  {engine:9s} {count:3d}축")

    if args.check:
        base = _loadBaseline()
        regressions = _diff(state, base)
        if regressions:
            print(f"\n[axisDeclaredCoverage] 회귀 {len(regressions)} 건 (baseline 초과):")
            for item in regressions:
                print(f"  X {item}")
            print("\n개선이면 --write-baseline 로 원장 갱신. 회귀면 선언 복원.")
            return 2
        # baseline 이 실제보다 나쁜 상태(개선됨)면 알림 (원장 갱신 권장, 실패 아님)
        if (
            len(state["undeclared"]) < len(base["undeclared"])
            or state["handTableMismatch"] != base["handTableMismatch"]
        ):
            print("\n[axisDeclaredCoverage] 개선 감지 - --write-baseline 로 원장 조이기 권장.")
        print("\n[axisDeclaredCoverage] 회귀 0 건 OK.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
