---
id: runtime.multimodal
title: Multimodal Input — chart image + PDF OCR
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: 차트 이미지 / PDF 표 OCR 입력 처리 패턴. Claude vision API wrapper SSOT. **status=drafted — parseChart tool 미신설 (Phase 3.B)**. 외부 본문 untrusted 적용 + JSON schema 추출 표준.
whenToUse:
  - multimodal
  - 차트 이미지
  - PDF OCR
  - vision API
  - 이미지 → JSON
inputs:
  - image (PNG/JPG/PDF)
  - 추출 schema (JSON)
outputs:
  - parsed data (JSON)
  - untrusted wrap 마커
toolRefs: []
knowledgeRefs:
  - runtime.untrustedContent
  - runtime.toolComposition
sourceRefs:
  - dartlab://skills/runtime.multimodal
requiredEvidence:
  - skillRef
  - executionRef
  - sourceRef
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
  - runtime.untrustedContent
  - runtime.toolComposition
---

## 표준 인터페이스

```python
def parseChart(
    image: bytes | str,             # path 또는 base64
    schema: dict,                   # 추출 JSON schema
    sourceUrl: str = "",            # 원본 URL (untrusted wrap 용)
) -> dict:
    """차트/표 이미지 → JSON 추출. 결과 자동 wrapExternalInResult."""
```

## 사용 패턴

```python
# 1. 차트 이미지 → 데이터
result = parseChart(
    "chart.png",
    schema={"type": "object", "properties": {
        "xAxis": {"type": "array"},
        "yAxis": {"type": "array"},
        "series": {"type": "array"}
    }},
    sourceUrl="https://example.com/report.pdf",
)
# → {"data": {...}, "wrap": "[EXTERNAL CONTENT START — untrusted ...]"}

# 2. PDF 표 OCR
table = parseChart("table.pdf", schema={"type": "array"}, sourceUrl=...)
```

## 강행 룰

1. 결과는 항상 untrusted (`Ref.sourceType="external"`) — sentinel 마커 자동.
2. 추출 schema 강행 — free-form text 금지 (prompt injection 차단).
3. 본문 안 숫자 claim → 1 차 출처 검증 (PDF 본문 직접 확인).
4. 이미지 URL fetch 시 도메인 화이트리스트 (선택).

## 안티패턴

- schema 없이 호출 (free-form 결과 = injection 위험 ↑).
- 결과 wrap 누락.
- vision 결과 단독 신뢰 (1 차 출처 검증 없음).

## 기본 검증

- 모든 결과 wrap 마커 존재.
- JSON schema validation pass.
- sourceUrl 누락 시 ValueError.
