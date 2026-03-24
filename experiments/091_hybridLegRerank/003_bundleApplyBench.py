"""
실험 ID: 091-003
실험명: hybrid bundle apply bench

목적:
- `hybridSearchEvidence(stockCode, query)` 형태의 실험용 결과물을 만든다.
- retrieval 숫자뿐 아니라 AI가 바로 쓸 수 있는 bundle 계층이 실제로 더 나아지는지 본다.

가설:
1. `LegIndex + rerank` 결과를 `UnderstandingBundle`로 묶으면 summary/change 계열 fact coverage가 더 좋아질 수 있다.
2. demo query에서도 gist/evidence/stitchedTables/changePairs가 모두 실질적으로 채워질 수 있다.

방법:
1. `safe2` sampleUnits를 종목별로 로드하고 per-stock index를 만든다.
2. `hybridSearchEvidence(stockCode, query)`로 reranked hit를 만들고 bundle로 조립한다.
3. summary/change benchmark case와 고정 demo query set에서 bundle 품질을 측정한다.

결과 (실험 후 작성):
- codes: `005930`, `000660`
- caseCount: `7`
- requiredFactCoverage: `0.5238`
- citationCoverage: `1.0`
- avgStitchedTables: `2.2857`
- avgChangePairs: `1.4286`
- medianLatencyMs: `31741.5278`
- peakMemoryMb: `3869.2`
- demo query 4건 모두 `gist/evidence/stitchedTables/changePairs`가 실제로 채워졌다

결론:
- `hybridSearchEvidence(stockCode, query)` callable 자체는 만들 수 있었고, bundle 결과도 형식상 유효했다.
- 하지만 현재 reranker 경로는 품질 개선보다 비용이 훨씬 커서 적용형 결과물로 채택할 수 없다.
- 이번 파일의 의미는 “출력 shape는 가능”을 확인한 것이고, 실제 채택은 더 가벼운 rerank 전략으로 다시 가야 한다.

실험일: 2026-03-23
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SAFE_CODES = ["005930"]
PREFERRED_CODES = ["005930", "000660"]
LAST_N = 12
_unitModule = None
_reranker = None
_stockCache: dict[str, tuple[Any, Any]] = {}


def loadUnitModule():
    global _unitModule
    if _unitModule is not None:
        return _unitModule
    path = Path(__file__).resolve().parents[1] / "088_sectionsLegIndex" / "001_unitSchema.py"
    spec = importlib.util.spec_from_file_location("leg088bundle", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _unitModule = module
    return module


def selectedCodes() -> list[str]:
    raw = os.getenv("LEGRERANK_CODES", "").strip()
    if raw:
        return [code.strip() for code in raw.split(",") if code.strip()]
    outputDir = Path(__file__).resolve().parents[1] / "088_sectionsLegIndex" / "output" / "benchmarkCorpus"
    cacheReady = all((outputDir / f"{code}.last{LAST_N}.parquet").exists() for code in PREFERRED_CODES)
    return PREFERRED_CODES if cacheReady else SAFE_CODES


def loadReranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    mod = loadUnitModule()
    bench = mod.loadBenchModule()
    mod.check_memory_and_gc("091:bundle:beforeReranker")
    _reranker = bench.load_reranker()
    return _reranker


def loadStockArtifacts(stockCode: str):
    cached = _stockCache.get(stockCode)
    if cached is not None:
        return cached
    mod = loadUnitModule()
    unitDf = mod.loadSampleUnits([stockCode])
    if unitDf is None:
        mod.runUnitSchemaExperiment()
        unitDf = mod.loadSampleUnits([stockCode])
    assert unitDf is not None
    indexData = mod.buildLegIndex(unitDf)
    _stockCache[stockCode] = (unitDf, indexData)
    return _stockCache[stockCode]


def hybridSearchEvidence(stockCode: str, query: str, topK: int = 10, rerankK: int = 30):
    mod = loadUnitModule()
    reranker = loadReranker()
    unitDf, indexData = loadStockArtifacts(stockCode)
    queryLegs, hits = mod.searchLegIndexWithRerank(
        indexData,
        unitDf,
        query,
        reranker=reranker,
        topK=topK,
        rerankK=rerankK,
    )
    return mod.buildUnderstandingBundleFromHits(unitDf, indexData, queryLegs, hits)


def runBundleApplyExperiment() -> dict[str, Any]:
    mod = loadUnitModule()
    codes = selectedCodes()
    unitDf = mod.loadSampleUnits(codes)
    if unitDf is None:
        mod.runUnitSchemaExperiment()
        unitDf = mod.loadSampleUnits(codes)
    assert unitDf is not None

    _bench, _corpus, cases, _caseMap = mod.benchmarkCasesForUnits(unitDf, codes=codes, lastN=LAST_N)
    targetCases = [case for case in cases if case.taskType in {"summary", "change"}]
    requiredCoverageScores: list[float] = []
    citationCoverageScores: list[float] = []
    stitchedTableCounts: list[int] = []
    changePairCounts: list[int] = []
    latenciesMs: list[float] = []

    for case in targetCases:
        t0 = time.perf_counter()
        bundle = hybridSearchEvidence(case.stockCode, case.question, topK=10, rerankK=30)
        latenciesMs.append((time.perf_counter() - t0) * 1000)
        combinedEvidence = " ".join(item["displayText"] for item in bundle.evidenceUnits).lower()
        if case.requiredFacts:
            matched = sum(1 for fact in case.requiredFacts if fact.lower() in combinedEvidence)
            requiredCoverageScores.append(matched / len(case.requiredFacts))
        else:
            requiredCoverageScores.append(1.0)
        citationCoverageScores.append(1.0 if bundle.evidenceUnits else 0.0)
        stitchedTableCounts.append(len(bundle.stitchedTables))
        changePairCounts.append(len(bundle.changePairs))

    demoQueries = [
        ("005930", "삼성전자 최신 사업 개요 변화 근거를 찾아줘"),
        ("005930", "삼성전자 배당 정책 표와 관련 근거를 찾아줘"),
        ("005930", "삼성전자 최대주주 변동 근거를 찾아줘"),
        ("000660", "SK하이닉스 원재료 조달 구조와 변화 근거를 찾아줘"),
    ]
    demos = []
    for stockCode, query in demoQueries:
        bundle = hybridSearchEvidence(stockCode, query, topK=8, rerankK=30)
        demos.append(
            {
                "stockCode": stockCode,
                "query": query,
                "gist": bundle.gist,
                "evidenceCount": len(bundle.evidenceUnits),
                "stitchedTables": len(bundle.stitchedTables),
                "changePairs": len(bundle.changePairs),
                "topEvidence": bundle.evidenceUnits[0]["displayText"] if bundle.evidenceUnits else "",
            }
        )

    summary = {
        "codes": codes,
        "caseCount": len(targetCases),
        "requiredFactCoverage": round(sum(requiredCoverageScores) / max(len(requiredCoverageScores), 1), 4),
        "citationCoverage": round(sum(citationCoverageScores) / max(len(citationCoverageScores), 1), 4),
        "avgStitchedTables": round(sum(stitchedTableCounts) / max(len(stitchedTableCounts), 1), 4),
        "avgChangePairs": round(sum(changePairCounts) / max(len(changePairCounts), 1), 4),
        "medianLatencyMs": round(sum(latenciesMs) / max(len(latenciesMs), 1), 4),
        "peakMemoryMb": round(loadUnitModule().get_memory_mb(), 2),
        "demos": demos,
    }
    outputDir = Path(__file__).resolve().parent / "output"
    outputDir.mkdir(parents=True, exist_ok=True)
    (outputDir / "bundleApply.summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = runBundleApplyExperiment()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
