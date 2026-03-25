"""실험 ID: 097-001
실험명: critical+high 전체 ollama 배치 검증

목적:
- 55개 personaCases 중 critical+high 35건을 실제 ollama로 실행
- 각 갭 영역(성장성/밸류에이션/report심화/contextSlices/K-IFRS/EDGAR/금융업)이 정상 동작하는지 검증
- 약점 패턴을 자동 진단으로 발견

가설:
1. route 정확도 95% 이상
2. module 활용률 70% 이상
3. overall 평균 8.0 이상
4. false_unavailable 0건

방법:
1. 종목코드별 분할 (005930 → 000660 → 051910 → 035420 → 105560 → AAPL)
2. 각 그룹을 별도 subprocess로 실행 (Polars 메모리 완전 해제)
3. 15차원 자동 채점 + failure taxonomy 분류
4. JSONL 결과 취합 후 분석

결과:
- 총 35건 중 34건 PASS (97%), 1건 ERROR (accountant.audit.redFlags — year 컬럼 str→i32 파싱 실패)
- 평균 overall: 8.85 (목표 8.0 달성 ✓)
- route 정확도: 97% (34/35, 목표 95% 달성 ✓)
- 모듈 활용률: 60% (목표 70% 미달 ✗)
- false_unavailable: 2건 (목표 0건 미달 ✗)
- 주요 failure: retrieval_failure 19건 (54%), runtime_error 4건
- 종목별 평균: 051910(10.49) > 006400(10.23) > 105560(10.24) > 000660(9.69) > 005930(7.69)
- 005930이 가장 낮은 이유: 분기별 데이터 접근(quarterly.*) + 감사(audit) 케이스에서 약점
- 하위 5개: audit.redFlags(ERROR), quarterly.operatingProfit(4.0), quarterly.revenue(4.0), dividend.sustainability(5.5), margin.drivers(5.5)

결론:
1. 가설1 route 정확도 95%↑ → 채택 (97%)
2. 가설2 모듈 활용률 70%↑ → 기각 (60%). retrieval_failure가 19건으로 모듈 데이터를 LLM에 제대로 전달하지 못하는 경우 빈번
3. 가설3 overall 평균 8.0↑ → 채택 (8.85)
4. 가설4 false_unavailable 0건 → 기각 (2건). executivePay 등에서 데이터가 있는데도 "미제공" 응답
5. 핵심 개선 대상:
   - report.py year 컬럼 파싱 버그 (audit.redFlags ERROR 원인)
   - quarterly.* 케이스: 분기별 데이터 context 주입 부족 → finance_context.py 개선 필요
   - retrieval_failure 다발: context 조립 시 모듈 데이터가 LLM prompt에 누락되는 경로 있음

실험일: 2026-03-25
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT / "src" / "dartlab" / "engines" / "ai" / "eval"
CASES_PATH = EVAL_DIR / "personaCases.json"
OUT_DIR = Path(__file__).parent


def loadCases(severities: set[str]) -> list[dict]:
    """케이스 로드 + 필터."""
    with open(CASES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [c for c in data["cases"] if c["severity"] in severities]


def groupByStock(cases: list[dict]) -> dict[str, list[dict]]:
    """종목코드별 그룹핑."""
    groups: dict[str, list[dict]] = {}
    for c in cases:
        stock = c.get("stockCode") or "null"
        groups.setdefault(stock, []).append(c)
    return groups


def runGroupSubprocess(stockCode: str, caseIds: list[str], provider: str, model: str, outJsonl: Path) -> list[dict]:
    """별도 subprocess로 종목 그룹 실행 → Polars 메모리 완전 해제."""
    workerScript = textwrap.dedent(f"""\
        import gc, json, sys
        from pathlib import Path
        ROOT = Path(r"{ROOT}")
        sys.path.insert(0, str(ROOT / "src"))
        import dartlab
        from dartlab.engines.ai.eval import loadPersonaCases, replayCase
        dartlab.llm.configure(provider="{provider}", model="{model}")
        allCases = loadPersonaCases()
        caseIds = {caseIds!r}
        stockCode = {stockCode!r}
        outPath = Path(r"{outJsonl}")
        results = []
        for i, cid in enumerate(caseIds):
            case = next((c for c in allCases if c.id == cid), None)
            if case is None:
                print(f"  [SKIP] {{cid}}")
                continue
            print(f"  [{{i+1}}/{{len(caseIds)}}] {{case.id}}")
            print(f"    질문: {{case.question[:60]}}...")
            try:
                r = replayCase(case, provider="{provider}", model="{model}")
                routeOk = "OK" if r.structural.routeMatch >= 1.0 else "MISS"
                modUtil = f"{{r.structural.moduleUtilization:.0%}}"
                status = "PASS" if r.score.overall >= 0.6 else "FAIL"
                print(f"    [{{status}}] overall={{r.score.overall:.2f}} route={{routeOk}} modules={{modUtil}}")
                if r.score.failure_types:
                    print(f"    failures: {{r.score.failure_types}}")
                if r.answer:
                    preview = r.answer[:150].replace("\\n", " ")
                    print(f"    답변: {{preview}}...")
                results.append({{
                    "caseId": case.id,
                    "stockCode": stockCode,
                    "persona": case.persona,
                    "severity": case.severity,
                    "overall": r.score.overall,
                    "routeMatch": r.structural.routeMatch,
                    "moduleUtilization": r.structural.moduleUtilization,
                    "falseUnavailable": r.score.false_unavailable,
                    "factualAccuracy": r.score.factual_accuracy,
                    "contextDepth": r.score.context_depth,
                    "sourceCitationPrecision": r.score.source_citation_precision,
                    "dataCoverage": r.score.data_coverage,
                    "failureTypes": r.score.failure_types,
                    "answerLength": len(r.answer) if r.answer else 0,
                }})
            except Exception as e:
                print(f"    [ERROR] {{e}}")
                results.append({{"caseId": cid, "stockCode": stockCode, "overall": 0, "error": str(e)}})
            gc.collect()
        with open(outPath, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\\n")
        print(f"  → {{len(results)}}건 저장: {{outPath}}")
    """)

    print(f"\n  [subprocess 시작] {stockCode} ({len(caseIds)}건)")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", workerScript],
        capture_output=False,
        text=True,
        timeout=600,
    )

    # 결과 읽기
    results = []
    if outJsonl.exists():
        with open(outJsonl, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
    return results


def analyze(allResults: list[dict]) -> str:
    """결과 분석."""
    lines = [f"# 097-001 Eval Batch 결과 — {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]

    total = len(allResults)
    if not total:
        return "결과 없음"

    overalls = [r["overall"] for r in allResults]
    routeOks = sum(1 for r in allResults if r.get("routeMatch", 0) >= 1.0)
    modUtils = [r.get("moduleUtilization", 0) for r in allResults]
    falseUnavail = sum(1 for r in allResults if r.get("falseUnavailable", 0) < 0.5)
    passes = sum(1 for o in overalls if o >= 0.6)

    lines.append(f"## 요약 (총 {total}건)")
    lines.append("")
    lines.append("| 지표 | 값 | 목표 | 판정 |")
    lines.append("|------|-----|------|------|")
    avgOverall = sum(overalls) / total
    routePct = routeOks / total * 100
    avgMod = sum(modUtils) / total * 100
    lines.append(f"| 평균 overall | {avgOverall:.2f} | ≥8.0 | {'✓' if avgOverall >= 8.0 else '✗'} |")
    lines.append(f"| route 정확도 | {routePct:.0f}% | ≥95% | {'✓' if routePct >= 95 else '✗'} |")
    lines.append(f"| 모듈 활용률 | {avgMod:.0f}% | ≥70% | {'✓' if avgMod >= 70 else '✗'} |")
    lines.append(f"| PASS율 | {passes}/{total} ({passes / total * 100:.0f}%) | - | - |")
    lines.append(f"| false_unavailable | {falseUnavail}건 | 0건 | {'✓' if falseUnavail == 0 else '✗'} |")
    lines.append("")

    # 신규 3차원 평균
    ctxDepths = [r.get("contextDepth", 0) for r in allResults]
    citPrecs = [r.get("sourceCitationPrecision", 0) for r in allResults]
    dataCovs = [r.get("dataCoverage", 0) for r in allResults]
    lines.append("## 데이터 심도 차원")
    lines.append("")
    lines.append("| 차원 | 평균 |")
    lines.append("|------|------|")
    lines.append(f"| contextDepth | {sum(ctxDepths) / total:.2f} |")
    lines.append(f"| sourceCitationPrecision | {sum(citPrecs) / total:.2f} |")
    lines.append(f"| dataCoverage | {sum(dataCovs) / total:.2f} |")
    lines.append("")

    # failure 빈도
    failureCounts: dict[str, int] = {}
    for r in allResults:
        for ft in r.get("failureTypes", []):
            failureCounts[ft] = failureCounts.get(ft, 0) + 1

    if failureCounts:
        lines.append("## Failure 유형")
        lines.append("")
        lines.append("| 유형 | 빈도 |")
        lines.append("|------|------|")
        for ft, cnt in sorted(failureCounts.items(), key=lambda x: -x[1]):
            lines.append(f"| {ft} | {cnt} |")
        lines.append("")

    # 종목코드별
    stockGroups: dict[str, list[float]] = {}
    for r in allResults:
        sc = r.get("stockCode", "?")
        stockGroups.setdefault(sc, []).append(r["overall"])

    lines.append("## 종목코드별 평균")
    lines.append("")
    lines.append("| 종목 | 건수 | 평균 overall |")
    lines.append("|------|------|------------|")
    for sc, scores in sorted(stockGroups.items()):
        lines.append(f"| {sc} | {len(scores)} | {sum(scores) / len(scores):.2f} |")
    lines.append("")

    # 하위 5개
    ranked = sorted(allResults, key=lambda r: r["overall"])
    lines.append("## 하위 5개 케이스")
    lines.append("")
    lines.append("| 케이스 | overall | failures |")
    lines.append("|--------|---------|----------|")
    for r in ranked[:5]:
        failures = ", ".join(r.get("failureTypes", [])) or "-"
        lines.append(f"| {r['caseId']} | {r['overall']:.2f} | {failures} |")

    return "\n".join(lines)


def main():
    provider = "ollama"
    model = "qwen3:latest"

    cases = loadCases({"critical", "high"})
    print(f"총 {len(cases)}건 (critical+high)")

    groups = groupByStock(cases)
    stockOrder = sorted(groups.keys(), key=lambda s: -len(groups[s]))

    allResults: list[dict] = []
    for stockCode in stockOrder:
        groupCases = groups[stockCode]
        caseIds = [c["id"] for c in groupCases]
        print(f"\n{'=' * 60}")
        print(f"종목: {stockCode} ({len(groupCases)}건)")
        print(f"{'=' * 60}")

        jsonlPath = OUT_DIR / f"_group_{stockCode}.jsonl"
        results = runGroupSubprocess(stockCode, caseIds, provider, model, jsonlPath)
        allResults.extend(results)
        print(f"  → {len(results)}건 완료")

    # 분석
    report = analyze(allResults)
    print(f"\n{'=' * 60}")
    print(report)

    # 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    jsonlPath = OUT_DIR / f"batch_{ts}.jsonl"
    with open(jsonlPath, "w", encoding="utf-8") as f:
        for r in allResults:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nJSONL 저장: {jsonlPath}")

    mdPath = OUT_DIR / f"report_{ts}.md"
    mdPath.write_text(report, encoding="utf-8")
    print(f"리포트 저장: {mdPath}")

    # 임시 그룹 파일 정리
    for tmp in OUT_DIR.glob("_group_*.jsonl"):
        tmp.unlink()
    print("임시 파일 정리 완료")


if __name__ == "__main__":
    main()
