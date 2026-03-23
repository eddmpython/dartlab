# 088 Sections LegIndex

## 목적

- `sections` 전체를 AI 친화적인 `UnderstandingUnit`로 재인덱싱한다.
- 목표는 chunk 검색이 아니라 `구조 + 기간 + 테이블 행` 중심 검색이다.
- `DART`만 대상으로 먼저 검증하고, public API 흡수 전까지는 실험 계층에만 둔다.

## 실험 파일

| 파일 | 상태 | 내용 |
|------|------|------|
| `001_unitSchema.py` | 완료 | 6종목 79,576 units materialize, build 125.7888s, 메모리 경고 큼 |
| `002_legIndexBuild.py` | 완료 | 79,576 units 기준 6-leg index build 7.2009s |
| `003_queryCompiler.py` | 완료 | 샘플 질의 4건에서 topic/time/table/change 분해 확인 |
| `004_tableStitchBench.py` | 완료 | precision 0.9568, recall 0.1678, numeric alignment 0.77 |
| `005_retrievalBench.py` | 완료 | safe2(005930) 기준 LegIndex hit@5 0.8889, BM25 대비 우위 확인 |
| `006_understandingBundleBench.py` | 완료 | safe(005930) 기준 bundle fact coverage 0.5556 |
| `007_universeStress.py` | 완료 | safe default는 sample2 + sample6Cached, stress8은 2.2GB로 제외 |

## 핵심 계약

- `UnderstandingUnit`
  - 필수 필드: `stockCode`, `topic`, `period`, `periodLane`, `blockType`, `sourceBlockOrder`, `blockOrder`, `textNodeType`, `textPathKey`, `textSemanticPathKey`, `textComparablePathKey`, `semanticTopic`, `detailTopic`, `rowFingerprint`, `tableFingerprint`, `payloadText`, `displayText`, `priority`, `neighborIds`
- `LegIndex`
  - `topicLeg`, `structureLeg`, `timeLeg`, `tableLeg`, `entityLeg`, `changeLeg`
- `QueryLegs`
  - 자연어 질문을 6개 leg token set으로 분해
- `UnderstandingBundle`
  - `queryIntent`, `gist`, `breadcrumbs`, `evidenceUnits`, `stitchedTables`, `changePairs`, `scoreBreakdown`

## 메모

- query 시점에는 `Company()`나 `retrievalBlocks/contextSlices`를 다시 만들지 않는다.
- 실험용 artifact는 `output/` 아래에 materialize한다.
- benchmark 원본은 `experiments/069_companyTextAnalysis/001_goldBenchmark.py`를 재사용한다.
- `005` 기본값은 `safe2`다. `D2_bge_dense`, `H2_contextual_plus_bge`는 이 장비에서 메모리 비용이 커서 기본 실행에서 제외했다.
- `005/006` wrapper는 `output/benchmarkCorpus/` cache가 있으면 자동으로 `005930,000660` 2종목을 기본값으로 사용하고, 없으면 `005930` 1종목으로 내려간다.
- `007`은 기본적으로 `sample2`, `sample6Cached`만 돈다. exploratory `stress8`은 peak memory 2223.32MB를 기록해 정식 기본 경로에서 뺐다.
- `005/006`은 `output/benchmarkCorpus/*.parquet` cache를 도입했다. 첫 build는 RSS가 약 `1.98GB`까지 올라가지만, cache-backed rerun은 `loadData(...,docs)` 경고 없이 실행된다.

## 핵심 결과

- `001`: 6종목에서 `79,576` units, `text 23,160`, `table 56,416`, `fallback 199`
- `002`: `topic 61`, `structure 11,857`, `table 57,491`, `entity 36,821` tokens
- `003`: `topic 4/4`, `latest 1/1`, `change 1/1`, `table 2/2`
- `004`: row stitch `precision 0.9568`, `recall 0.1678`
- `005`: safe retrieval에서 LegIndex `hit@5 0.8889`, `mrr@10 0.7593`, `requiredFactCoverage 0.6852`, `medianLatency 48.3954ms`
- `006`: bundle `requiredFactCoverage 0.5556`, `avgStitchedTables 2.6667`, `avgChangePairs 1.6667`
- `007`: `sample2 peak 1275.2MB`, `sample6Cached peak 1500.75MB`

## Cache-Backed 2-Code

- codes: `005930`, `000660`
- `005`: LegIndex `hit@5 0.65`, `mrr@10 0.4963`, `requiredFactCoverage 0.6667`, `medianLatency 74.3235ms`
- `006`: bundle `requiredFactCoverage 0.6667`, `avgStitchedTables 2.8571`, `avgChangePairs 1.8571`
- memory: 첫 cache build는 benchmark corpus build 중 RSS가 `1.98GB`까지 상승
- rerun: cache 재사용 시 `loadData(...,docs)` 메모리 경고 없이 재실행 가능
