---
id: runtime.ragPipeline
title: RAG Pipeline — chunk → retrieve → cite
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: retrieval-augmented generation pipeline SSOT — chunk → embedding → retrieve → cite 4 단계. dartlab DART 공시 본문 RAG 적용 표준. **status=drafted — searchSemantic tool 미신설 (Phase 3.B)**.
whenToUse:
  - RAG
  - retrieval-augmented
  - semantic search
  - chunk retrieve
  - 본문 RAG
inputs:
  - 사용자 query
  - corpus (section_content / 공시 본문)
outputs:
  - retrieved chunks (top-k)
  - cited refs
  - synthesis answer
toolRefs: []
knowledgeRefs:
  - runtime.embeddingSearch
  - runtime.citationFormat
  - runtime.untrustedContent
sourceRefs:
  - dartlab://skills/runtime.ragPipeline
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: limited
  localPython:
    status: limited
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - runtime.embeddingSearch
  - runtime.citationFormat
  - runtime.untrustedContent
  - engines.search
---

## 4 단계 파이프라인

### 1. Chunk

- 단위: section (DART 공시 section_content) 또는 paragraph (자체 분할).
- size: 512~1024 token (overlap 50).
- metadata: `rcept_no` + `section_title` + `corp_code` + `rcept_dt`.

### 2. Embed

- `runtime.embeddingSearch` provider 사용.
- batch 100 / cache `gather/sectionEmbedding.parquet`.

### 3. Retrieve

- query embed → cosine top-k (k=10 기본).
- filter (corp_code, rcept_dt range) 사전 적용 권장.
- MMR (max marginal relevance) 옵션 — 중복 감축.

### 4. Cite

- 각 chunk → `[docRef:<rcept_no>]` + `[tableRef:<section_id>]` 인용.
- 본문 발췌 시 untrusted wrap 마커 강행.
- `runtime.citationFormat` 4 format 중 선택.

## 강행 룰

1. 본문 발췌는 untrusted (`Ref.sourceType="external"`) — sentinel 마커.
2. 추론 결과의 모든 숫자 claim → 1 차 출처 (`Company.filings`) 재검증.
3. corpus 전체 fetch 금지 — 항상 retrieval (top-k) 경유.
4. cache miss 시 incremental embed (전체 재 embed X).

## 안티패턴

- chunk size 너무 크면 (>2048) signal-to-noise ↓.
- 같은 chunk 다회 인용 시 dedup.
- 외부 본문 wrap 누락 — prompt injection 위험.

## 기본 검증

- cache hit 율 ≥ 80% (incremental embed 정상).
- top-k 결과의 corp_code filter 정합.
- 모든 결과에 untrusted wrap 마커.
