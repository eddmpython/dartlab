---
id: recipes.fundamental.credit.debtStructureAudit
title: 부채 구조 audit (만기 + 이자보상 + peer 횡단)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 회사 부채 구조를 만기 분포 + 이자보상배율 + peer 횡단 비교 + 신용 등급 4 축으로 종합 audit 하는 절차. 트리거 — '부채 구조 audit', '만기 분포', '이자보상배율', '신용 등급 횡단'.
whenToUse:
  - 부채 구조
  - 만기 구조
  - 이자보상배율
  - 부채 audit
  - debt structure
  - 부채 만기
  - 단기 장기 부채
linkedSkills:
  - engines.company
  - engines.scan
  - engines.analysis
  - engines.credit
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
  - "engines.viz.scenarioVisuals"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - 부채비율 한 지표만으로 신용 위험 단정 금지 — 만기 분포 + 이자보상 동반.
  - 단기 / 장기 부채 구분 명시 없이 부채 audit 결론 금지.
  - 이자보상배율 단일 시점 결과로 부채 상환 능력 단정 금지.
  - peer 산업 / size 차이 무시한 부채 ratio 단순 비교 금지.
failureModes:
  - 부채 정의 (총부채 vs 이자부 부채) 차이로 비율 변동
  - 단기 부채의 roll-over 가정 명시 없이 만기 위험 단정"
  - 이자보상배율 (EBIT / 이자비용) 의 EBIT 정의 차이"
  - 외화 부채 비중 + 환율 변동 효과 미반영
  - peer 산업 (자본집약 vs 자본경량) 정상 부채 수준 차이 무시
examples:
  - 삼성전자 부채 만기 분포 + 이자보상
  - 부채 구조 + peer 횡단 (4 대 금융지주)
  - 이자보상배율 시계열 + 5 년 평균
  - 신용 등급 변화 + 부채 audit
gap:
  primary:
    - scan
    - analysis
  secondary:
    - credit
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

debt = dartlab.scan("debt")
debt_peer = dartlab.scan("debt")
financing = c.analysis("financial", "자금조달")
credit = c.credit()
```

## 호출 동작

부채 구성 + 만기 구조 + 이자보상배율 → peer 횡단 → 자본조달 종합 → 신용 등급.

1. 회사 진입
2. debt() — 회사 부채 구조 (총차입금 / 단기 / 장기 / ICR)
3. debt("all") — peer 횡단 부채 비교
4. analysis("financial", "자금조달") — 자본조달 의지 + 만기 구조
5. credit() — dCR 등급

## 대표 반환 형태

- `tableRef` 3 개 (debt + peer + financing)
- `valueRef` 5+ (총차입금 / 차입금의존도 / ICR / dCR 등급 / OCF/부채)
- `dateRef` 1 개

## 연계 절차

1. engines.company — 회사 진입
2. engines.scan — 부채 구조 + peer 횡단
3. engines.analysis — 자본조달 종합
4. engines.credit — dCR 등급

## 기본 검증

- 부채비율 (%) + 차입금의존도 (%) + ICR (배) 명시.
- 만기 구조 (단기 / 장기 비율) 명시.
- "안전" 단정 X — 위험등급 (안전/주의/경고/위험) 함께.
