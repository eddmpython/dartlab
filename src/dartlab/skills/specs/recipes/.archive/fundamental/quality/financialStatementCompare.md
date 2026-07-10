---
id: recipes.fundamental.quality.financialStatementCompare
title: 두 회사 재무제표 비교 (peer + show + 분해)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 두 회사의 재무제표를 같은 기준 기간에서 비교하고 핵심 차이를 분해해 평가하는 절차. 트리거 — '재무제표 비교', '두 회사 차이', '회사 간 비교'.
whenToUse:
  - 두 회사 재무제표 비교
  - A 와 B 비교
  - 회사 vs 회사
  - peer 비교
  - 동종 비교
  - 종목 비교
linkedSkills:
  - engines.company
  - engines.analysis
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.financialStructureCharts"
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - 한쪽 회사 수치만으로 우열 단정 금지 — 양쪽 같은 기간 정렬.
  - 같은 산업 / 같은 단계 비교 기준 명시 없이 결론 금지.
  - 일회성 손익 (M&A / 매각) 정상화 없이 단순 비교 금지.
  - 외환 매출 비중 다른 회사 환율 영향 분리 없이 비교 금지.
failureModes:
  - 같은 분기 (Q1 vs Q1) 정렬 누락
  - 연결 vs 별도 회계 scope 혼용
  - 시총 격차 (1 조 vs 10 조) 큰 비교의 size 효과 무시
  - 산업 sub-segment (반도체 메모리 vs 비메모리) 구분 없는 단순 peer
  - 회계 정책 변경 시점 차이 무시
examples:
  - 삼성전자 vs SK하이닉스 분기 비교
  - 신한 vs KB 같은 분기 ROE
  - 일회성 정상화 후 비교
  - 외환 영향 분리 후 비교
lastUpdated: '2026-05-13'
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
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 공개 호출 방식

```python
import dartlab

# 두 회사 진입 (sequential — 메모리 안전)
left = dartlab.Company("005930")    # 삼성전자
right = dartlab.Company("000660")   # SK하이닉스

# 같은 기간 재무제표 + ROE 분해
left_bs = left.panel("BS")
right_bs = right.panel("BS")
left_roe = left.analysis("financial", "수익성")
right_roe = right.analysis("financial", "수익성")
```

## 호출 동작

각 회사는 sequential 로 로드한다 (CLAUDE.md 메모리 안전 규칙: Company 동시 3 개 이상 로드 금지). 비교는 같은 분기 기준으로 정렬한다.

1. 두 회사 식별 (종목코드 또는 회사명)
2. 각 회사 `show("BS")` 와 `show("IS")` — 같은 분기로 정렬
3. ROE DuPont 분해를 두 회사 동일 axis 로 호출
4. 비교 표 생성 — markdown table 본문 노출

## 대표 반환 형태

- `tableRef` 4 개 (두 회사 × BS + IS)
- `valueRef` 6+ 개 (양사 ROE 구성 요소)
- `dateRef` 1 개 (양사 공통 분기)
- 답변 본문 안 markdown evidence table (양사 핵심 항목 5~10 행)

## 연계 절차

1. engines.company — 첫 회사 진입 + show("BS") + show("IS")
2. engines.company — 둘째 회사 진입 + show("BS") + show("IS")
3. engines.analysis — 양사 같은 기간 정렬 + 핵심 차이
4. engines.analysis — 양사 ROE DuPont 분해
5. engines.analysis — 양사 자본구조 비교 (선택)

## 기본 검증

- 양사 비교는 같은 분기·같은 단위 (조원) 기준.
- 답변 본문에 markdown evidence table 필수 — bullet 만 X.
- 차이 해석 시 절대값과 함께 비율 (배·%pt) 함께.
- 연결/별도 구분 명시 (양사 모두 연결 또는 모두 별도).
