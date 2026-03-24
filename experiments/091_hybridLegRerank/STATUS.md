# 091 Hybrid LegRerank

## 목표
- `088_sectionsLegIndex` 위에 `top-K rerank`를 얹어 실제 품질 개선이 있는지 빠르게 검증한다.
- dense retrieval 없이 `structure-first + rerank only`가 safe2에서 실용적인지 본다.

## 실험 구성
- `001_contextualPrefixBench.py` — contextual prefix BM25 비교
- `002_legRerankBench.py` — `LegIndex only` vs `LegIndex + rerank`
- `003_bundleApplyBench.py` — `hybridSearchEvidence(stockCode, query)` 적용형 bundle 검증

## 결과
- `001_contextualPrefixBench.py`
  - `caseCount 20`
  - prefixed contextual BM25가 기존 contextual BM25 대비 `hit@3 0.05 -> 0.1`, `mrr@10 0.0675 -> 0.0850`, `goldRecall@10 0.15 -> 0.2`
  - latency 증가는 작음: `46.15ms -> 47.84ms`
- `002_legRerankBench.py`
  - `LegIndex only`: `hit@5 0.65`, `requiredFactCoverage 0.6667`, `medianLatencyMs 70.6481`
  - `LegIndex + rerank`: `hit@5 0.7`, `requiredFactCoverage 0.6083`, `medianLatencyMs 34290.6811`
  - `peakMemoryMb 4205.57`, `accepted False`
- `003_bundleApplyBench.py`
  - `hybridSearchEvidence(stockCode, query)` callable 구현 완료
  - bundle benchmark: `requiredFactCoverage 0.5238`, `avgStitchedTables 2.2857`, `avgChangePairs 1.4286`
  - `medianLatencyMs 31741.5278`, `peakMemoryMb 3869.2`
  - demo query 4건 모두 실질 bundle 생성 확인

## 현재 판단
- 이번 턴의 winner는 `001_contextualPrefixBench.py`다.
- 현재 `bge-reranker-v2-m3` 기반 `LegIndex + rerank`는 DartLab의 속도/메모리 조건에서 명확히 reject다.
- 따라서 바로 채택할 성과물은 `prefix 규칙`이고, `hybridSearchEvidence` shape는 유지하되 reranker는 더 가벼운 전략으로 교체해야 한다.
