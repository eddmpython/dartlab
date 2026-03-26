"""Eval 자동 진단 CLI — 커버리지 갭·회귀·코드 영향 분석.

Usage::

    uv run python -X utf8 scripts/evalDiagnose.py --mode coverage
    uv run python -X utf8 scripts/evalDiagnose.py --mode regression
    uv run python -X utf8 scripts/evalDiagnose.py --mode impact
    uv run python -X utf8 scripts/evalDiagnose.py --mode full
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "src" / "dartlab" / "engines" / "ai" / "eval"
BATCH_DIR = EVAL_DIR / "batchResults"
CASES_PATH = EVAL_DIR / "personaCases.json"
REPORT_DIR = EVAL_DIR / "diagnosisReports"


def _latestBatch() -> Path | None:
    """최신 배치 결과 JSONL."""
    candidates = sorted(BATCH_DIR.glob("batch_*.jsonl"))
    return candidates[-1] if candidates else None


def _previousBatch(current: Path) -> Path | None:
    """현재 제외 직전 배치."""
    candidates = sorted(BATCH_DIR.glob("batch_*.jsonl"))
    candidates = [c for c in candidates if c != current]
    return candidates[-1] if candidates else None


def _gitChangedFiles() -> list[str]:
    """최근 커밋에서 변경된 파일 목록."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except (FileNotFoundError, subprocess.SubprocessError):
        return []


def _loadCases() -> list[dict]:
    """personaCases.json 로드."""
    if not CASES_PATH.exists():
        return []
    with open(CASES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cases", data) if isinstance(data, dict) else data


def _saveReport(report: str, mode: str) -> Path:
    """진단 리포트 저장."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"diagnosis_{mode}_{ts}.md"
    path.write_text(report, encoding="utf-8")
    return path


def runCoverage() -> str:
    """커버리지 갭 분석."""
    from dartlab.ai.eval.diagnoser import DiagnosisReport, findCoverageGaps

    cases = _loadCases()
    if not cases:
        return "케이스 파일 없음"

    gaps = findCoverageGaps(cases)
    report = DiagnosisReport(
        coverageGaps=gaps,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    return report.toMarkdown()


def runRegression() -> str:
    """회귀 탐지."""
    from dartlab.ai.eval.diagnoser import (
        DiagnosisReport,
        findRegressions,
        findWeakTypes,
    )

    latest = _latestBatch()
    if not latest:
        return "배치 결과 없음"

    results: list[dict] = []
    with open(latest, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    report = DiagnosisReport(
        weakTypes=findWeakTypes(results),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    prev = _previousBatch(latest)
    if prev:
        prevResults: list[dict] = []
        with open(prev, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    prevResults.append(json.loads(line))
        report.regressions = findRegressions(results, prevResults)

    return report.toMarkdown()


def runImpact() -> str:
    """git diff → 영향 케이스 매핑."""
    from dartlab.ai.eval.diagnoser import mapCodeImpact

    changedFiles = _gitChangedFiles()
    if not changedFiles:
        return "변경 파일 없음"

    cases = _loadCases()
    impacted = mapCodeImpact(changedFiles, cases)

    lines = [
        f"# 코드 변경 영향 분석 — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"변경 파일: {len(changedFiles)}개",
        "",
    ]
    for f in changedFiles:
        lines.append(f"- `{f}`")
    lines.append("")

    if impacted:
        lines.append(f"## 영향받는 케이스: {len(impacted)}개")
        lines.append("")
        for caseId in impacted:
            lines.append(f"- {caseId}")
    else:
        lines.append("영향받는 케이스 없음.")

    return "\n".join(lines)


def runFull() -> str:
    """전체 진단."""
    from dartlab.ai.eval.diagnoser import diagnoseFull

    latest = _latestBatch()
    prev = _previousBatch(latest) if latest else None

    report = diagnoseFull(
        batchPath=latest,
        previousBatchPath=prev,
        casesPath=CASES_PATH if CASES_PATH.exists() else None,
    )

    # 코드 영향 추가
    changedFiles = _gitChangedFiles()
    if changedFiles:
        from dartlab.ai.eval.diagnoser import mapCodeImpact

        cases = _loadCases()
        impacted = mapCodeImpact(changedFiles, cases)
        md = report.toMarkdown()
        if impacted:
            md += f"\n## 코드 변경 영향\n\n변경 파일 {len(changedFiles)}개 → 영향 케이스 {len(impacted)}개\n"
            for caseId in impacted[:10]:
                md += f"- {caseId}\n"
            if len(impacted) > 10:
                md += f"- ... 외 {len(impacted) - 10}개\n"
        return md

    return report.toMarkdown()


def main() -> None:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="Eval 자동 진단")
    parser.add_argument(
        "--mode",
        choices=["coverage", "regression", "impact", "full"],
        default="full",
        help="진단 모드",
    )
    parser.add_argument("--save", action="store_true", help="리포트 파일 저장")
    args = parser.parse_args()

    runners = {
        "coverage": runCoverage,
        "regression": runRegression,
        "impact": runImpact,
        "full": runFull,
    }

    print(f"진단 모드: {args.mode}")
    print(f"{'=' * 50}\n")

    result = runners[args.mode]()
    print(result)

    if args.save:
        path = _saveReport(result, args.mode)
        print(f"\n리포트 저장: {path}")


if __name__ == "__main__":
    main()
