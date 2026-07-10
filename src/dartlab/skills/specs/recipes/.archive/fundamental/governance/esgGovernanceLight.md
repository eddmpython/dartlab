---
id: recipes.fundamental.governance.esgGovernanceLight
title: ESG light 점검 (지배구조 + 감사 + 종업원 + 환경 신호)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 정식 ESG 데이터 부재 시 dartlab 보유 신호 (지배구조 + 감사 + 종업원 + 자본배분 일관성) 만으로 가벼운 ESG audit 을 만드는 절차. 트리거 — 'ESG light', '거버넌스 audit', 'ESG 데이터 부재 시'.
whenToUse:
  - ESG 분석
  - 지속가능성
  - 사회 책임
  - light ESG
  - ESG 점검
  - 비재무 audit
linkedSkills:
  - engines.company
  - engines.analysis
  - recipes.fundamental.governance.auditComposite
  - engines.scan
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
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - 정식 ESG 데이터 부재 시에도 신호로만 표기 — 정식 점수 단정 금지.
  - 지배구조 + 감사 + 종업원 + 자본배분 4 축 중 1~2 만 보고 ESG 단정 금지.
  - 외부 ESG 평가사 (MSCI / 한국기업평가) 점수와 1:1 비교 금지.
  - 환경 (E) 데이터 부재 시 사회 / 거버넌스만으로 ESG 종합 단정 금지.
failureModes:
  - 환경 (E) 신호의 dartlab 부재로 ESG 의 "S + G" 만 평가
  - 종업원 (workforce) 데이터의 시점 / 빈도 차이"
  - 지배구조 신호의 KR 특수성 (오너 / 재벌) 반영 한계
  - 자본배분 일관성과 ESG 직접 매핑 모호"
  - 단일 분기 신호로 영구 ESG 등급 단정
examples:
  - 삼성전자 ESG light 점검
  - 지배구조 + 감사 + 종업원 결합
  - 자본배분 + ESG 신호
  - 정식 ESG 부재 시 light audit
gap:
  primary:
    - analysis
    - scan
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

governance = c.analysis("financial", "지배구조")
gov_audit = c.analysis("financial", "지배구조감사")
workforce = dartlab.scan("workforce")
consistency = c.analysis("financial", "재무정합성")
```

## 호출 동작

지배구조 + 감사 신호 + 종업원 (인력 안정성·인건비 비중) + 재무 정합성 4 축. 정식 ESG 데이터 부재 — 보조 신호로 light audit.

1. 회사 진입
2. analysis("financial", "지배구조") — G 영역
3. analysis("financial", "지배구조감사") — G 보조 (감사·분식 신호)
4. workforce() — S 영역 보조 (인력 변화·인건비)
5. analysis("financial", "재무정합성") — 일관성

## 대표 반환 형태

- `tableRef` 3+ 개
- `valueRef` 5+ (지배구조 점수 / 감사 신호 / 인력 변화 / 일관성)
- `dateRef` 1 개

## 연계 절차

1. engines.company — 회사 진입
2. engines.analysis — G 종합
3. recipes.fundamental.governance.auditComposite — 감사 신호
4. engines.scan — S 보조 (인력)
5. engines.analysis — 일관성

## 기본 검증

- "ESG 우수" 단정 X — light audit 임을 명시.
- 환경 (E) 영역은 dartlab 직접 데이터 없음 — 명시.
- G 종합 점수 + 보조 신호 (감사·인력) 함께.
