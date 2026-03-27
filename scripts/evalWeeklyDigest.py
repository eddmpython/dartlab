"""주간 eval digest — batchResults 최근 7일 분석.

Usage::

    uv run python -X utf8 scripts/evalWeeklyDigest.py
    uv run python -X utf8 scripts/evalWeeklyDigest.py --days 14
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "src" / "dartlab" / "ai" / "eval"
BATCH_DIR = EVAL_DIR / "batchResults"
REPORT_DIR = EVAL_DIR / "diagnosisReports"


def _loadBatchesInRange(days: int) -> list[tuple[Path, list[dict]]]:
    """최근 N일 배치 파일 로드."""
    cutoff = datetime.now() - timedelta(days=days)
    batches: list[tuple[Path, list[dict]]] = []

    for path in sorted(BATCH_DIR.glob("batch_*.jsonl")):
        # 파일명에서 timestamp 추출: batch_{provider}_{YYYYMMDD_HHMMSS}.jsonl
        parts = path.stem.split("_")
        if len(parts) >= 3:
            try:
                dateStr = parts[-2]  # YYYYMMDD
                fileDate = datetime.strptime(dateStr, "%Y%m%d")
                if fileDate >= cutoff:
                    results: list[dict] = []
                    with open(path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                results.append(json.loads(line))
                    if results:
                        batches.append((path, results))
            except ValueError:
                continue

    return batches


def generateDigest(days: int = 7) -> str:
    """주간 digest 생성."""
    batches = _loadBatchesInRange(days)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [f"# Eval 주간 Digest — {now}", f"기간: 최근 {days}일", ""]

    if not batches:
        lines.append("해당 기간 배치 결과 없음.")
        return "\n".join(lines)

    # 배치별 평균 overall 추이
    lines.append("## 배치별 평균 점수 추이")
    lines.append("")
    lines.append("| 배치 | 케이스 수 | 평균 overall | 최저 | 최고 |")
    lines.append("|------|---------|------------|------|------|")

    allResults: list[dict] = []
    for path, results in batches:
        overalls = [r.get("overall", 0) for r in results]
        avg = sum(overalls) / len(overalls) if overalls else 0
        minScore = min(overalls) if overalls else 0
        maxScore = max(overalls) if overalls else 0
        lines.append(f"| {path.stem} | {len(results)} | {avg:.2f} | {minScore:.2f} | {maxScore:.2f} |")
        allResults.extend(results)

    lines.append("")

    # 케이스별 집계
    caseScores: dict[str, list[float]] = {}
    for r in allResults:
        caseId = r.get("caseId", "unknown")
        caseScores.setdefault(caseId, []).append(r.get("overall", 0))

    # 개선 Top 3 (최근 점수 - 첫 점수)
    deltas: list[tuple[str, float]] = []
    for caseId, scores in caseScores.items():
        if len(scores) >= 2:
            deltas.append((caseId, scores[-1] - scores[0]))

    if deltas:
        deltas.sort(key=lambda x: x[1], reverse=True)
        lines.append("## 개선 Top 3")
        lines.append("")
        for caseId, delta in deltas[:3]:
            if delta > 0:
                lines.append(f"- {caseId}: {delta:+.2f}")
        lines.append("")

        lines.append("## 악화 Top 3")
        lines.append("")
        for caseId, delta in deltas[-3:]:
            if delta < 0:
                lines.append(f"- {caseId}: {delta:+.2f}")
        lines.append("")

    # failure 유형 집계
    failureCounts: dict[str, int] = {}
    for r in allResults:
        for ftype in r.get("failureTypes", []):
            failureCounts[ftype] = failureCounts.get(ftype, 0) + 1

    if failureCounts:
        lines.append("## Failure 유형 빈도")
        lines.append("")
        lines.append("| 유형 | 발생 횟수 |")
        lines.append("|------|---------|")
        for ftype, count in sorted(failureCounts.items(), key=lambda x: -x[1]):
            lines.append(f"| {ftype} | {count} |")
        lines.append("")

    # 우선 개선 대상
    if failureCounts:
        from dartlab.ai.eval.remediation import (
            generateRemediations,
        )

        plans = generateRemediations(failureCounts)
        if plans:
            lines.append("## 다음 주 우선 개선 대상")
            lines.append("")
            for p in plans[:3]:
                lines.append(f"- **[P{p.priority}] {p.failureType}** → `{p.targetFile}`")
                lines.append(f"  {p.description}")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="Eval 주간 digest")
    parser.add_argument("--days", type=int, default=7, help="분석 기간 (일)")
    args = parser.parse_args()

    digest = generateDigest(args.days)
    print(digest)

    # 저장
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")
    path = REPORT_DIR / f"weekly_{ts}.md"
    path.write_text(digest, encoding="utf-8")
    print(f"\nDigest 저장: {path}")


if __name__ == "__main__":
    main()
