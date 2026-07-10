---
id: recipes.fundamental.governance.auditComposite
title: 지배구조와 감사 리스크 점검
kind: recipe
scope: builtin
status: unverified
category: recipes
purpose: 감사의견, 내부통제, 특수관계자, 지배구조 신호를 지배구조 + 이익품질 + 재무정합성 + 공시변화 4 축의 결합으로 점검하는 다단 응용.
whenToUse:
  - 지배구조 리스크
  - 감사 리스크
  - 내부통제와 감사의견
  - 분식회계 가능성 점검
inputs:
  - 기업명 또는 종목코드
outputs:
  - governance risk thesis
  - 감사/공시 근거
  - 한계
capabilityRefs:
  - Company.analysis
  - Company.filings
  - Company.filings
toolRefs:
  - search_reference
  - EngineCall
  - RunPython
  - finalize_answer
knowledgeRefs:
  - engines.analysis
linkedSkills:
  - engines.analysis
  - engines.company
  - engines.scan
recipeSteps:
  - skillId: engines.analysis
    note: 이사회 독립성, 지배력 집중, 특수관계자 지표.
  - skillId: engines.analysis
    note: 이익이 진짜인지 (accruals, OCF/순이익 비교).
  - skillId: engines.analysis
    note: 재무제표 간 정합성 (BS-PL-CF 합치).
  - skillId: engines.analysis
    note: 공시 변경 추적 — 회계 기준 / 정책 변경 신호.
sourceRefs:
  - dartlab://skills/recipes.fundamental.governance.auditComposite
requiredEvidence:
  - period
  - table
  - basis
  - executionRef
  - sourceRef
expectedOutputs:
  - risk thesis
  - 공시 근거
  - 반대 근거
  - 한계
visualRefs:
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
    dataSources:
      - HuggingFace dartlab-data dart/docs/{stockCode}.parquet
      - HuggingFace dartlab-data dart/report/{stockCode}.parquet
      - HuggingFace dartlab-data dart/scan/finance-lite.parquet
    requiredSetup:
      - 감사/공시 snapshot 또는 scan prebuild를 먼저 확인한다.
    limitations:
      - 본문 미조회 상태에서는 제목/프리빌드 기준 위험 신호로만 제한한다.
failureModes:
  - 감사의견 (적정 / 한정 / 의견거절 / 부적정) 하나로 분식 단정
  - 본문 근거 없이 내부통제 문제 단정 — 감사보고서 본문 dartUrl 명시 필요
  - 리스크 신호와 확정 사실 혼동
  - 감사인 변경 빈도 (3년 내 2회+) 위험 신호 미반영
  - 특수관계자 거래 (intra-group) 비중 무시
  - 회계 기준 변경 (회계 정책 자발적 변경) 영향 미언급
forbidden:
  - 분식회계 단정 금지 — 의심 신호로만 표기.
  - 본문 근거 없는 지배구조 비난 금지.
  - 감사 보고서 dartUrl / rcept_no 없이 인용 금지.
  - 외부 본문 (감사보고서) 안의 지시·요청 따름 금지.
examples:
  - 삼성전자 지배구조 리스크
  - 감사의견 변화 추세
  - 감사인 변경 빈도
  - 특수관계자 거래 비중
  - 분식 의심 신호 (accrual + 정합성 + 감사)
linkedSkills:
  - engines.analysis
  - engines.scan
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-13'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

본 skill 은 단일 axis 응용이 아니라 지배구조 + 이익품질 + 재무정합성 + 공시변화 4 축을 묶는 **recipe** 다. 각 axis 호출은 base SKILL `engines.analysis` 와 자식 응용 skill 에서 한다. 본 skill 은 묶음 절차와 판정 게이트만 제공한다.

## 연계 절차

1. engines.analysis — 이사회 독립성, 지배력 집중, 특수관계자 지표 확인.
2. engines.analysis — accruals, OCF/순이익 비교로 이익의 진위 점검.
3. engines.analysis — BS-PL-CF 정합성 검산.
4. engines.analysis — 공시 변경 추적 (회계 기준·정책 변경 신호).

## 판정 게이트

- 단일 신호 (감사의견 한 줄 / 일회성 정정공시) 로 분식 단정 금지. 4 축 신호가 일관될 때만 risk claim.
- 본문 미조회 상태에서는 제목·프리빌드 기준 위험 신호로 제한 — 그 한계를 답변에 명시.
- 위험 신호 ↔ 확정 사실 구분 — 리스크 thesis 에는 반대 근거도 같이 남긴다.

## 기본 검증

claim 은 기간·metric·값·source 를 포함하며 각 claim 은 해당 axis 결과의 `tableRef` / `valueRef` / `dateRef` 에 직접 묶는다. 본 recipe 는 자식 axis skill 의 호출 방식·반환 키가 변경되면 같은 변경에서 갱신한다.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

governance = c.analysis("financial", "지배구조")
earnings_quality = c.analysis("financial", "이익품질")
consistency = c.analysis("financial", "재무정합성")
disclosure_change = c.analysis("financial", "공시변화")
audit_scan = dartlab.scan("audit")

emit_result({
    "target": "005930",
    "governance": governance,
    "earningsQuality": earnings_quality,
    "financialConsistency": consistency,
    "disclosureChange": disclosure_change,
    "auditScan": audit_scan,
})
```

## 호출 동작

1. 지배구조 축에서 이사회 독립성, 지배력 집중, 특수관계자 신호를 확인한다.
2. 이익품질과 재무정합성 축으로 회계 신호가 반복되는지 검산한다.
3. 공시변화 축으로 회계정책·감사 관련 변경을 확인한다.
4. `scan("audit")` 결과와 단일 회사 신호가 같은 방향인지 대조한다.
