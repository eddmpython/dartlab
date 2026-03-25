"""실험 ID: 097-002
실험명: medium severity 전체 ollama 검증

목적:
- 55개 케이스 중 medium 20건을 실제 ollama로 실행
- 001(critical+high)과 합쳐서 전체 55건 완전 커버리지 달성
- medium 케이스 특유의 약점(비기업 질문, EDGAR, 시스템 질문) 탐지

가설:
1. medium은 난이도가 낮아 PASS율 90% 이상
2. null stockCode 케이스(시스템 질문)도 정상 응답
3. EDGAR(AAPL) 케이스는 데이터 미보유로 graceful degradation

방법:
1. 001과 동일한 subprocess 격리 실행
2. 15차원 자동 채점 + failure taxonomy

결과:
- 총 20건 전부 PASS (100%)
- 평균 overall: 9.11 (가설1 PASS율 90%↑ 달성)
- 종목별: null(10.77) > 000660(10.51) > 051910(10.27) > 005930(8.75) > 035420(8.72) > AAPL(7.01)
- null stockCode 3건: 전부 10.0↑ (시스템 질문 정상 동작)
- AAPL 3건: 1건 PASS(10.03), 2건 낮은 점수(5.50) — finance/balance sheet 데이터 미보유
- 주요 failure: retrieval_failure 12건 (60%), runtime_error 3건
- 하위 3개: explainLatency(5.50), appleFinancials(5.50), appleBalanceSheet(5.50)

결론:
1. 가설1 PASS율 90%↑ → 채택 (100%)
2. 가설2 null stockCode 정상 응답 → 채택 (3건 모두 10.0↑)
3. 가설3 EDGAR graceful degradation → 부분 채택
   - appleBusiness(10.03)는 sections 기반으로 정상 응답
   - appleFinancials(5.50), appleBalanceSheet(5.50)는 finance 데이터 미보유로 runtime_error
   - EDGAR finance 데이터 연결이 핵심 개선 대상

실험일: 2026-03-25
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

# 001과 동일한 핵심 함수 재사용
from importlib.util import module_from_spec, spec_from_file_location

spec = spec_from_file_location("batch", Path(__file__).parent / "001_criticalHighBatch.py")
batch = module_from_spec(spec)
spec.loader.exec_module(batch)


def main():
    provider = "ollama"
    model = "qwen3:latest"

    cases = batch.loadCases({"medium"})
    print(f"총 {len(cases)}건 (medium)")

    groups = batch.groupByStock(cases)
    stockOrder = sorted(groups.keys(), key=lambda s: -len(groups[s]))

    outDir = Path(__file__).parent
    allResults: list[dict] = []
    for stockCode in stockOrder:
        groupCases = groups[stockCode]
        caseIds = [c["id"] for c in groupCases]
        print(f"\n{'=' * 60}")
        print(f"종목: {stockCode} ({len(groupCases)}건)")
        print(f"{'=' * 60}")

        jsonlPath = outDir / f"_group_{stockCode}.jsonl"
        results = batch.runGroupSubprocess(stockCode, caseIds, provider, model, jsonlPath)
        allResults.extend(results)
        print(f"  → {len(results)}건 완료")

    report = batch.analyze(allResults)
    print(f"\n{'=' * 60}")
    print(report)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    jsonlPath = outDir / f"medium_batch_{ts}.jsonl"
    with open(jsonlPath, "w", encoding="utf-8") as f:
        for r in allResults:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nJSONL 저장: {jsonlPath}")

    mdPath = outDir / f"medium_report_{ts}.md"
    mdPath.write_text(report, encoding="utf-8")
    print(f"리포트 저장: {mdPath}")

    # 임시 그룹 파일 정리
    for tmp in outDir.glob("_group_*.jsonl"):
        tmp.unlink()
    print("임시 파일 정리 완료")


if __name__ == "__main__":
    main()
