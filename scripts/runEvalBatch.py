"""Persona eval 배치 replay — ollama/openai 대상.

Usage::

    uv run python -X utf8 scripts/runEvalBatch.py --provider ollama --model qwen3:latest
    uv run python -X utf8 scripts/runEvalBatch.py --provider ollama --severity critical,high
    uv run python -X utf8 scripts/runEvalBatch.py --provider ollama --compare latest
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = ROOT / "src" / "dartlab" / "engines" / "ai" / "eval" / "batchResults"


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval batch replay")
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default=None)
    parser.add_argument("--severity", default=None, help="comma-separated: critical,high")
    parser.add_argument("--persona", default=None, help="single persona filter")
    parser.add_argument("--compare", default=None, help="'latest' 또는 JSONL 경로")
    parser.add_argument("--diagnose", action="store_true", help="배치 후 자동 진단")
    parser.add_argument("--dry-run", action="store_true", help="케이스 목록만 출력")
    args = parser.parse_args()

    severityFilter = set(args.severity.split(",")) if args.severity else None

    # lazy import
    import dartlab
    from dartlab.engines.ai.eval import (
        loadPersonaCases,
        replaySuite,
        summarizeReplayResults,
    )

    # provider 설정
    dartlab.llm.configure(provider=args.provider, model=args.model)
    print(f"Provider: {args.provider} / {args.model or 'default'}")

    # 케이스 필터
    cases = loadPersonaCases()
    if severityFilter:
        cases = [c for c in cases if c.severity in severityFilter]
    if args.persona:
        cases = [c for c in cases if c.persona == args.persona]

    print(f"대상 케이스: {len(cases)}건")
    for c in cases:
        print(f"  [{c.severity}] {c.id}")

    if args.dry_run:
        print("\n[dry-run] 실행하지 않음")
        return

    if not cases:
        print("실행할 케이스 없음")
        return

    # replay
    print(f"\n{'=' * 50}")
    print("배치 replay 시작...")
    results = replaySuite(cases, provider=args.provider, model=args.model)
    summary = summarizeReplayResults(results)

    # 결과 출력
    print(f"\n{'=' * 50}")
    print(f"DartLab Eval Batch — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Provider: {args.provider} / {args.model or 'default'}")
    print(f"Cases: {summary['cases']}")
    print(f"{'=' * 50}")
    print(f"avgOverall:          {summary['avgOverall']:.2f}")
    print(f"avgRouteMatch:       {summary['avgRouteMatch']:.2f}")
    print(f"avgModuleUtilization: {summary['avgModuleUtilization']:.2f}")
    print(f"falseUnavailable:    {summary['falseUnavailableCases']} / {summary['cases']}")

    if summary.get("failureCounts"):
        print("\nFailure types:")
        for ftype, count in sorted(summary["failureCounts"].items()):
            print(f"  {ftype}: {count}")

    # 개별 결과
    print(f"\n{'─' * 50}")
    for r in results:
        status = "PASS" if r.score.overall >= 0.6 else "FAIL"
        routeOk = "OK" if r.structural.routeMatch >= 1.0 else "MISS"
        print(
            f"  [{status}] {r.case.id}: "
            f"overall={r.score.overall:.2f} "
            f"route={routeOk} "
            f"modules={r.structural.moduleUtilization:.0%}"
        )
        if r.errors:
            print(f"         errors: {r.errors[:100]}")

    # 결과 저장
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outPath = BATCH_DIR / f"batch_{args.provider}_{ts}.jsonl"
    with open(outPath, "w", encoding="utf-8") as f:
        for r in results:
            entry = {
                "caseId": r.case.id,
                "persona": r.case.persona,
                "severity": r.case.severity,
                "provider": args.provider,
                "model": args.model,
                "overall": r.score.overall,
                "routeMatch": r.structural.routeMatch,
                "moduleUtilization": r.structural.moduleUtilization,
                "falseUnavailable": r.score.false_unavailable,
                "factualAccuracy": r.score.factual_accuracy,
                "failureTypes": r.score.failure_types,
                "answerLength": len(r.answer) if r.answer else 0,
                "timestamp": ts,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n결과 저장: {outPath}")

    # 이전 배치와 비교
    if args.compare:
        _compareBatch(outPath, args.compare, BATCH_DIR)

    # 자동 진단
    if args.diagnose:
        _runDiagnosis(outPath, BATCH_DIR)


def _runDiagnosis(currentPath: Path, batchDir: Path) -> None:
    """배치 후 자동 진단 실행."""
    from dartlab.engines.ai.eval.diagnoser import (
        DiagnosisReport,
        findRegressions,
        findWeakTypes,
    )
    from dartlab.engines.ai.eval.remediation import (
        extractFailureCounts,
        formatAsMarkdown,
        generateRemediations,
    )

    results: list[dict] = []
    with open(currentPath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    if not results:
        return

    print(f"\n{'=' * 50}")
    print("자동 진단")
    print(f"{'=' * 50}")

    # 약점 유형
    weakTypes = findWeakTypes(results)
    if weakTypes:
        print("\n약점 유형 (하위 점수):")
        for w in weakTypes:
            failures = ", ".join(w.topFailures[:3]) or "-"
            print(f"  {w.questionType}: avg={w.avgOverall:.2f} ({w.caseCount}건) [{failures}]")

    # 회귀 탐지
    candidates = sorted(batchDir.glob("batch_*.jsonl"))
    candidates = [c for c in candidates if c != currentPath]
    if candidates:
        prevResults: list[dict] = []
        with open(candidates[-1], encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    prevResults.append(json.loads(line))
        regressions = findRegressions(results, prevResults)
        if regressions:
            print(f"\n회귀 감지: {len(regressions)}건")
            for r in regressions:
                print(f"  {r.caseId}: {r.prevOverall:.2f} → {r.currOverall:.2f} ({r.delta:+.2f})")

    # 개선 계획
    failureCounts = extractFailureCounts(results)
    if failureCounts:
        plans = generateRemediations(failureCounts)
        if plans:
            print(f"\n개선 계획: {len(plans)}건")
            for p in plans:
                print(f"  [P{p.priority}] {p.failureType} → {p.targetFile}")

    # 리포트 저장
    reportDir = batchDir.parent / "diagnosisReports"
    reportDir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    reportPath = reportDir / f"diagnosis_batch_{ts}.md"

    report = DiagnosisReport(
        weakTypes=weakTypes,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    md = report.toMarkdown()
    if failureCounts:
        plans = generateRemediations(failureCounts)
        md += "\n\n" + formatAsMarkdown(plans)

    reportPath.write_text(md, encoding="utf-8")
    print(f"\n진단 리포트: {reportPath}")


def _compareBatch(currentPath: Path, compareTarget: str, batchDir: Path) -> None:
    """이전 배치와 회귀 비교."""
    if compareTarget == "latest":
        # 현재 파일 제외 가장 최신 파일
        candidates = sorted(batchDir.glob("batch_*.jsonl"))
        candidates = [c for c in candidates if c != currentPath]
        if not candidates:
            print("\n비교 대상 없음 (첫 배치)")
            return
        prevPath = candidates[-1]
    else:
        prevPath = Path(compareTarget)
        if not prevPath.exists():
            print(f"\n비교 파일 없음: {prevPath}")
            return

    # 로드
    def _loadBatch(path: Path) -> dict[str, dict]:
        result = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                result[entry["caseId"]] = entry
        return result

    prev = _loadBatch(prevPath)
    curr = _loadBatch(currentPath)

    print(f"\n{'=' * 50}")
    print(f"Regression vs {prevPath.name}")
    print(f"{'=' * 50}")

    regressions = []
    improvements = []
    for caseId, cEntry in curr.items():
        if caseId in prev:
            pEntry = prev[caseId]
            diff = cEntry["overall"] - pEntry["overall"]
            if diff < -0.1:
                regressions.append((caseId, pEntry["overall"], cEntry["overall"], diff))
            elif diff > 0.1:
                improvements.append((caseId, pEntry["overall"], cEntry["overall"], diff))

    if regressions:
        print("\nRegressions:")
        for caseId, prev_s, curr_s, diff in regressions:
            print(f"  {caseId}: {prev_s:.2f} -> {curr_s:.2f} ({diff:+.2f})")
    else:
        print("\nNo regressions.")

    if improvements:
        print("\nImprovements:")
        for caseId, prev_s, curr_s, diff in improvements:
            print(f"  {caseId}: {prev_s:.2f} -> {curr_s:.2f} ({diff:+.2f})")


if __name__ == "__main__":
    main()
