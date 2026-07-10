---
id: recipes.fundamental.quality.earningsQualityCheck
title: 이익 quality 점검 (발생주의 + 현금흐름 + 재무정합성)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 회사 발표 이익의 quality 를 발생주의 vs 현금흐름 괴리 + 재무 항목 정합성 + 일회성 비중 3 축으로 점검하는 절차. 트리거 — '이익 quality 점검', '발생주의 vs 현금흐름', '일회성 비중'.
whenToUse:
  - 이익 quality
  - 분식 회계 가능성
  - 일회성 손익
  - 발생주의 현금주의 괴리
  - 재무 정합성
  - 매출채권 급증
  - 영업이익 신뢰성
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
  - 분식 가능성 단정 금지 — 점수 + 시나리오 + 출처 동반.
  - 일회성 손익 비중 명시 없이 영업이익 추세 단정 금지.
  - CFO / 영업이익 비율 한 지표만으로 quality 단정 금지.
  - 분기 한 번의 정합성 깨짐을 영구 패턴으로 단정 금지 — 시계열 (8Q+) 동반.
failureModes:
  - 일회성 손익 (자산매각 / 평가이익 / 환산이익 / 소송충당) 분리 누락
  - CFO / 영업이익 비율의 산업별 정상 수준 차이 무시"
  - 매출채권 회전율 / 재고 회전율 정의 차이 (평균 vs 기말) 모호
  - BS / IS / CF 시계열 정합성 윈도우 (4Q vs 8Q) 임의 선택"
  - 회계 기준 변경 (정책 자발적 변경) 시점 영향 미보정
examples:
  - 삼성전자 일회성 비중 + 발생주의 + 정합성
  - 매출채권 급증 + 매출 성장 비교
  - CFO / 영업이익 0.7 미만 의심 신호
  - 분식 가능성 점수 + 시나리오
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

c = dartlab.Company("005930")

quality = c.analysis("financial", "이익품질")
cashflow = c.analysis("financial", "현금흐름")
consistency = c.analysis("financial", "재무정합성")
bs = c.panel("BS")
is_df = c.panel("IS")
```

## 호출 동작

발표 이익 → 일회성 vs 경상 분리 → 매출채권·재고 변동률 vs 매출 성장 → 영업이익 vs CFO 괴리 → 재무 항목 시계열 정합성 종합.

1. 회사 진입
2. analysis("financial", "이익품질") — 일회성 비중 + 발생주의 신호
3. analysis("financial", "현금흐름") — CFO / 영업이익 비율
4. analysis("financial", "재무정합성") — BS·IS·CF 시계열 일관성
5. show("BS") + show("IS") — 매출채권·재고·매출 raw

## 대표 반환 형태

- `tableRef` 3 개 (quality 표 + cashflow 표 + consistency 표)
- `valueRef` 5+ (일회성 비중 % / CFO/OP / 매출채권 회전율 / 재고 회전율 / quality 점수)
- `dateRef` 1 개

## 연계 절차

1. engines.company — 회사 진입
2. engines.analysis — 일회성·발생주의
3. engines.analysis — CFO·FCF·배당 충당
4. engines.analysis — 시계열 정합성

## 기본 검증

- 일회성 손익 비중 (%) 명시 — 자산매각·평가이익·환산이익·소송충당 분리.
- CFO / 영업이익 비율이 0.7 이하면 quality 의심 신호 명시.
- 매출채권 급증 + 매출 성장 &lt; 매출채권 성장 패턴 점검.
- "분식 가능성" 단정 X — 점수 + 시나리오 + 출처.
