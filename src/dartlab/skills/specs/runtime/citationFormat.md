---
id: runtime.citationFormat
title: Citation Format — evidence ref 표준 format
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: dartlab 답변 안 evidence ref 인용 표준 format — markdown footnote / JSON-LD / Anthropic Citations API 호환 변환. workbenchEvidenceFlow SSOT 의 ref 형태 → 사용자 보기 좋은 format.
whenToUse:
  - citation format
  - 인용 format
  - evidence ref
  - markdown footnote
  - JSON-LD
inputs:
  - evidence refs (workbenchEvidenceFlow)
outputs:
  - markdown citation
  - JSON-LD
  - inline tableRef / dateRef
toolRefs:
  - EvidenceGate
knowledgeRefs:
  - runtime.workbenchEvidenceFlow
sourceRefs:
  - dartlab://skills/runtime.citationFormat
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
linkedSkills:
  - runtime.workbenchEvidenceFlow
  - runtime.untrustedContent
---

## 4 format

### 1. Inline ref (기본)

```
영업이익 21% [valueRef:opMargin@005930@2024Q3] (출처 [tableRef:dartlab.is.005930.2024Q3])
```

- `[valueRef:<axis>@<target>@<period>]` — 숫자 인용
- `[tableRef:<table_id>]` — 표 인용
- `[dateRef:<YYYY-MM-DD>]` — 시점 명시
- `[docRef:<rcept_no>]` — 공시 본문

### 2. Markdown footnote

```
영업이익 21%[^1] 도달.

[^1]: 출처: DART 005930 2024Q3 IS — `dartlab.Company("005930").panel("IS", freq="Q")` 결과의 operating_profit / sales 비율
```

### 3. JSON-LD (외부 통합)

```json
{
  "@context": "https://schema.org",
  "@type": "Claim",
  "value": 0.21,
  "unit": "%",
  "source": {
    "@type": "Dataset",
    "name": "DART 005930 IS Q3 2024",
    "url": "dartlab://company/005930/is/2024Q3"
  },
  "executionRef": "20260528-001",
  "skillRef": "engines.analysis.profitability"
}
```

### 4. Anthropic Citations API 호환

```json
{
  "content": "영업이익 21%",
  "citations": [{
    "type": "char_location",
    "cited_text": "operating_profit / sales = 0.21",
    "document_index": 0,
    "start_char_index": 0,
    "end_char_index": 33
  }]
}
```

## 강행 룰

1. 모든 숫자 claim → inline ref 강행.
2. 외부 본문 인용 → untrusted wrap 마커 + sourceRef 동행.
3. footnote / JSON-LD 는 사용자 요청 시 변환.

## 기본 검증

ref 형식 자동 검증 — `EvidenceGate` 가 ref 누락 시 답변 거부. format 변환은 별 도구 (`SaveArtifact` 측).
