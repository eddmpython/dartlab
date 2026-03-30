"""코드 품질 게이트 — radon 복잡도 + vulture 죽은 코드 자동 검사.

사용법:
    python scripts/qualityGate.py                    # 전체 검사
    python scripts/qualityGate.py --changed-only     # git 변경 파일만 (pre-commit용)
    python scripts/qualityGate.py --baseline-update  # 현재 수치를 baseline으로 저장
    python scripts/qualityGate.py --record           # 히스토리에 현재 수치 기록

규칙:
    1. 신규/변경 함수: 복잡도 D(25) 초과 금지
    2. 전체 E/F 함수 수: baseline 이하 유지 (늘어나면 실패)
    3. vulture 죽은 코드: 90% confidence 이상 경고
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BASELINE_PATH = _ROOT / "scripts" / "qualityBaseline.json"
_HISTORY_PATH = _ROOT / "scripts" / "qualityHistory.jsonl"
_SRC = str(_ROOT / "src" / "dartlab")

# ── baseline ────────────────────────────────────────────────────

_DEFAULT_BASELINE = {
    "ef_count": 125,
    "cdef_count": 767,
    "vulture_count": 13,
}


def _loadBaseline() -> dict:
    if _BASELINE_PATH.exists():
        return json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
    return dict(_DEFAULT_BASELINE)


def _saveBaseline(data: dict) -> None:
    _BASELINE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"baseline 저장: {_BASELINE_PATH}")


# ── 히스토리 ────────────────────────────────────────────────────


def _getGitCommit() -> str:
    """현재 git commit hash (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        return result.stdout.strip() or "unknown"
    except FileNotFoundError:
        return "unknown"


def _recordHistory(
    efCount: int, cdefCount: int, vultureCount: int, totalFiles: int = 0, totalFunctions: int = 0, totalLines: int = 0
) -> None:
    """qualityHistory.jsonl에 한 줄 추가."""
    record = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "commit": _getGitCommit(),
        "ef": efCount,
        "cdef": cdefCount,
        "vulture": vultureCount,
        "files": totalFiles,
        "functions": totalFunctions,
        "lines": totalLines,
    }
    with open(_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(
        f"히스토리 기록: {record['date']} commit={record['commit']} E/F={efCount} C+={cdefCount} vulture={vultureCount}"
    )


def _showHistory() -> None:
    """히스토리 출력."""
    if not _HISTORY_PATH.exists():
        print("히스토리 없음")
        return
    records = []
    for line in _HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    if not records:
        print("히스토리 없음")
        return

    print(f"\n{'날짜':>12} {'커밋':>8} {'E/F':>5} {'C+':>5} {'죽은코드':>8} {'파일':>6} {'함수':>6} {'줄':>8}")
    print("-" * 70)
    for r in records[-20:]:  # 최근 20건
        print(
            f"{r['date']:>12} {r['commit']:>8} {r['ef']:>5} {r['cdef']:>5} "
            f"{r['vulture']:>8} {r.get('files', '-'):>6} {r.get('functions', '-'):>6} "
            f"{r.get('lines', '-'):>8}"
        )


# ── radon 복잡도 ────────────────────────────────────────────────


def _runRadon(paths: list[str]) -> list[dict]:
    """radon cc 실행 → 파싱된 결과 리스트."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", *paths, "-j", "-nc"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    if not result.stdout.strip():
        return []

    items = []
    data = json.loads(result.stdout)
    for filepath, blocks in data.items():
        for block in blocks:
            items.append(
                {
                    "file": filepath,
                    "name": block.get("name", "?"),
                    "lineno": block.get("lineno", 0),
                    "complexity": block.get("complexity", 0),
                    "rank": block.get("rank", "?"),
                }
            )
    return items


def _checkComplexity(paths: list[str], changedOnly: bool = False) -> list[str]:
    """복잡도 검사. 위반 메시지 리스트 반환."""
    items = _runRadon(paths)
    errors = []

    if changedOnly:
        # 변경 파일만: D(25) 초과 금지
        for item in items:
            if item["complexity"] > 25:
                errors.append(
                    f"  {item['file']}:{item['lineno']} "
                    f"{item['name']} (복잡도 {item['complexity']}, {item['rank']}등급) "
                    f"— 25 이하로 줄여야 합니다"
                )
    else:
        # 전체: E/F 카운트가 baseline 이하인지
        baseline = _loadBaseline()
        efCount = sum(1 for i in items if i["rank"] in ("E", "F"))
        maxEf = baseline.get("ef_count", _DEFAULT_BASELINE["ef_count"])

        if efCount > maxEf:
            errors.append(f"  E/F 등급 함수: {efCount}개 (baseline {maxEf}개 초과)")
            newOnes = [i for i in items if i["rank"] in ("E", "F")]
            newOnes.sort(key=lambda x: -x["complexity"])
            for item in newOnes[:10]:
                errors.append(
                    f"    {item['file']}:{item['lineno']} {item['name']} ({item['rank']}, 복잡도 {item['complexity']})"
                )

        print(f"복잡도: E/F {efCount}개 (baseline {maxEf}개)")

    return errors


# ── vulture 죽은 코드 ───────────────────────────────────────────


def _runVulture(paths: list[str]) -> list[str]:
    """vulture 실행 → 결과 라인 리스트."""
    result = subprocess.run(
        [sys.executable, "-m", "vulture", *paths, "--min-confidence", "90"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
    return lines


def _checkDeadCode(paths: list[str]) -> list[str]:
    """죽은 코드 검사. 경고 메시지 리스트."""
    findings = _runVulture(paths)
    baseline = _loadBaseline()
    maxCount = baseline.get("vulture_count", _DEFAULT_BASELINE["vulture_count"])

    print(f"죽은 코드: {len(findings)}건 (baseline {maxCount}건)")

    if len(findings) > maxCount:
        warnings = [f"  vulture: {len(findings)}건 (baseline {maxCount}건 초과)"]
        for line in findings[:15]:
            warnings.append(f"    {line}")
        return warnings
    return []


# ── git 변경 파일 ───────────────────────────────────────────────


def _getChangedPythonFiles() -> list[str]:
    """staged + unstaged 변경된 .py 파일."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    staged = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "--cached"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    allFiles = set(result.stdout.splitlines() + staged.stdout.splitlines())
    pyFiles = [f for f in allFiles if f.endswith(".py") and f.startswith("src/dartlab/")]
    return pyFiles


# ── main ────────────────────────────────────────────────────────


def _countSource() -> dict:
    """소스 파일/함수/줄 수 카운트."""
    import ast as _ast

    srcPath = Path(_SRC)
    files = 0
    functions = 0
    lines = 0
    for f in srcPath.rglob("*.py"):
        rel = str(f.relative_to(srcPath))
        if "_reference" in rel or "__pycache__" in rel:
            continue
        files += 1
        try:
            source = f.read_text(encoding="utf-8", errors="replace")
            lines += len(source.splitlines())
            tree = _ast.parse(source)
            functions += sum(1 for n in _ast.walk(tree) if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)))
        except (SyntaxError, UnicodeDecodeError):
            pass
    return {"files": files, "functions": functions, "lines": lines}


def main() -> int:
    args = sys.argv[1:]
    changedOnly = "--changed-only" in args
    baselineUpdate = "--baseline-update" in args
    record = "--record" in args
    showHist = "--history" in args

    if showHist:
        _showHistory()
        return 0

    if baselineUpdate:
        items = _runRadon([_SRC])
        efCount = sum(1 for i in items if i["rank"] in ("E", "F"))
        cdefCount = sum(1 for i in items if i["rank"] in ("C", "D", "E", "F"))
        vultureCount = len(_runVulture([_SRC]))
        _saveBaseline(
            {
                "ef_count": efCount,
                "cdef_count": cdefCount,
                "vulture_count": vultureCount,
            }
        )
        print(f"E/F: {efCount}, C+: {cdefCount}, vulture: {vultureCount}")
        return 0

    if record:
        items = _runRadon([_SRC])
        efCount = sum(1 for i in items if i["rank"] in ("E", "F"))
        cdefCount = sum(1 for i in items if i["rank"] in ("C", "D", "E", "F"))
        vultureCount = len(_runVulture([_SRC]))
        counts = _countSource()
        _recordHistory(efCount, cdefCount, vultureCount, counts["files"], counts["functions"], counts["lines"])
        return 0

    if changedOnly:
        paths = _getChangedPythonFiles()
        if not paths:
            print("변경된 Python 파일 없음 — skip")
            return 0
        print(f"변경 파일 {len(paths)}개 검사...")
    else:
        paths = [_SRC]
        print("전체 소스 검사...")

    errors = []
    errors.extend(_checkComplexity(paths, changedOnly=changedOnly))

    if not changedOnly:
        errors.extend(_checkDeadCode(paths))

    if errors:
        print("\n[품질 게이트 실패]")
        for e in errors:
            print(e)
        return 1

    print("\n[품질 게이트 통과]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
