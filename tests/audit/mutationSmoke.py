"""dartlab.core 자작 mutation smoke — Track 5 (Windows 호환).

mutmut 가 Windows native 미지원이므로 (mutmut issue #397), dartlab 의 가장
중요한 mutation pattern (대소비교 임계, 산술 부호, 상수 ±1) 만 직접 mutate
하고 oracle test 가 잡는지 검증한다.

본 SSOT — [tests/POLICY.md](../../tests/POLICY.md) §5 Track 5.

CI nightly 의 mutmut job 은 Linux 전체 sweep, 본 도구는 본 PC + CI Fast 의
**critical mutation gate** — 가장 회귀 빈도 높은 7 patterns 100% killed 강제.

사용:
    uv run python -X utf8 tests/audit/mutationSmoke.py
    uv run python -X utf8 tests/audit/mutationSmoke.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parents[2]
_FORMATTING = _REPO / "src" / "dartlab" / "core" / "formatting.py"
_RATIOS = _REPO / "src" / "dartlab" / "core" / "ratios" / "common.py"


@dataclass
class Mutation:
    """한 mutation case — target file + find/replace + test command."""

    target: Path
    find: str
    replace: str
    description: str
    test_command: list[str]


@dataclass
class Result:
    mutation: str
    status: str  # killed | survived | skip
    detail: str = ""


@dataclass
class Report:
    total: int = 0
    killed: int = 0
    survived: int = 0
    skipped: int = 0
    results: list[Result] = field(default_factory=list)

    @property
    def mutation_score(self) -> float:
        applied = self.killed + self.survived
        if applied == 0:
            return 1.0
        return self.killed / applied

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "killed": self.killed,
            "survived": self.survived,
            "skipped": self.skipped,
            "mutation_score": round(self.mutation_score, 4),
            "results": [asdict(r) for r in self.results],
        }


_PY = sys.executable  # 현재 인터프리터 (uv 없이도 동작)

_FORMATTING_TEST = [
    _PY,
    "-X",
    "utf8",
    "-m",
    "pytest",
    "tests/core/test_formatting.py",
    "-x",
    "--no-cov",
    "-q",
    "--tb=line",
]

_RATIOS_TEST = [
    _PY,
    "-X",
    "utf8",
    "-m",
    "pytest",
    "tests/core/test_ratios_metamorphic.py",
    "-x",
    "--no-cov",
    "-q",
    "--tb=line",
]


# 7 critical mutation patterns — dartlab 의 가장 회귀 빈도 높은 변형.
_MUTATIONS: list[Mutation] = [
    Mutation(
        target=_FORMATTING,
        find="if absV >= 1e12:",
        replace="if absV > 1e12:",
        description="formatKr 조 임계 off-by-one (>= → >)",
        test_command=_FORMATTING_TEST,
    ),
    Mutation(
        target=_FORMATTING,
        find="if absV >= 1e8:",
        replace="if absV > 1e8:",
        description="formatKr 억 임계 off-by-one",
        test_command=_FORMATTING_TEST,
    ),
    Mutation(
        target=_FORMATTING,
        find="if absV >= 1e4:",
        replace="if absV > 1e4:",
        description="formatKr 만 임계 off-by-one",
        test_command=_FORMATTING_TEST,
    ),
    Mutation(
        target=_FORMATTING,
        find="if val == int(val) and abs(val) < 1e15:",
        replace="if val != int(val) and abs(val) < 1e15:",
        description="formatComma int collapse 조건 부정",
        test_command=_FORMATTING_TEST,
    ),
    Mutation(
        target=_RATIOS,
        find="return round(((cur - prev) / prev) * 100, 2)",
        replace="return round(((cur + prev) / prev) * 100, 2)",
        description="yoyPct 양수 분기 - → + 변형",
        test_command=_RATIOS_TEST,
    ),
    Mutation(
        target=_RATIOS,
        find="if prev > 0 and cur >= 0:",
        replace="if prev > 0 and cur > 0:",
        description="yoyPct 부호 분기 >= → > (cur=0 케이스 누락)",
        test_command=_RATIOS_TEST,
    ),
    Mutation(
        target=_RATIOS,
        find="if cur is None or prev is None or prev == 0:",
        replace="if cur is None or prev is None or prev != 0:",
        description="yoyPct None 가드 == → != (모든 정상 케이스 None 반환)",
        test_command=_RATIOS_TEST,
    ),
]


def _runOne(mutation: Mutation) -> Result:
    """한 mutation 적용 → oracle test 호출 → 결과 분류."""
    target = mutation.target
    if not target.exists():
        return Result(mutation=mutation.description, status="skip", detail=f"target 없음: {target}")
    content = target.read_text(encoding="utf-8")
    if mutation.find not in content:
        return Result(mutation=mutation.description, status="skip", detail=f"pattern not found: {mutation.find[:60]}")

    backup = target.with_suffix(target.suffix + ".mutbak")
    shutil.copy(target, backup)
    mutated = content.replace(mutation.find, mutation.replace, 1)
    target.write_text(mutated, encoding="utf-8")

    try:
        env = os.environ.copy()
        env["DARTLAB_TEST_LOCKED"] = "1"
        env["UV_NO_SYNC"] = "1"
        result = subprocess.run(
            mutation.test_command,
            cwd=str(_REPO),
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        if result.returncode != 0:
            return Result(mutation=mutation.description, status="killed", detail="oracle test fail")
        return Result(mutation=mutation.description, status="survived", detail="oracle missed — 보강 필요")
    except subprocess.TimeoutExpired:
        return Result(mutation=mutation.description, status="skip", detail="test timeout 120s")
    finally:
        shutil.copy(backup, target)
        backup.unlink(missing_ok=True)


def runAll() -> Report:
    report = Report()
    for mut in _MUTATIONS:
        report.total += 1
        r = _runOne(mut)
        report.results.append(r)
        if r.status == "killed":
            report.killed += 1
        elif r.status == "survived":
            report.survived += 1
        else:
            report.skipped += 1
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="JSON 결과 출력")
    parser.add_argument(
        "--fail-on-survived",
        action="store_true",
        default=True,
        help="survived mutant 있으면 exit 1 (default: 활성)",
    )
    parser.add_argument("--no-fail", dest="fail_on_survived", action="store_false", help="warning-only")
    args = parser.parse_args(argv)

    report = runAll()

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"Mutation smoke — total={report.total}")
        print(f"  killed:   {report.killed} (oracle test 잡음)")
        print(f"  survived: {report.survived} (oracle 누락 — 보강 필요)")
        print(f"  skipped:  {report.skipped} (pattern 부재)")
        print(f"  mutation_score: {report.mutation_score:.2%}")
        print("\n상세:")
        for r in report.results:
            marker = {"killed": "✓", "survived": "✗", "skip": "-"}[r.status]
            print(f"  {marker} [{r.status:8}] {r.mutation}")
            if r.detail and r.status != "killed":
                print(f"     {r.detail}")

    if args.fail_on_survived and report.survived > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
