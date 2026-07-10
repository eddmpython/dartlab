---
id: recipes.fundamental.dividend.thesis
title: 배당 thesis (자본배분 + 현금흐름 quality + 배당 정책)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 회사의 배당 매력도를 자본배분 의지 + 현금흐름 quality + 과거 배당 정책 3 축으로 평가하는 절차. 트리거 — '배당 매력도', '배당 정책', '배당 thesis'.
whenToUse:
  - 배당 매력 평가
  - 배당주 분석
  - 주주환원 thesis
  - 자사주 매입 분석
  - 배당 지속 가능성
  - 배당 성장률
linkedSkills:
  - engines.company
  - recipes.fundamental.dividend.capitalReturn
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
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.tableBackedChart"
  - "engines.viz.kpiRibbon"
visualGuidance:
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "종합 보고서 첫 화면은 engines.viz.kpiRibbon으로 KPI 4~8개만 묶고 각 카드에 period·evidenceRef를 붙인다."

forbidden:
  - 배당수익률 (dividend yield) 단일 지표만으로 매력도 단정 금지 — payout + FCF 커버리지 동반.
  - 배당성향 (payout ratio) 분모 (EPS vs FCF) 명시 없이 단정 금지.
  - 자사주 매입 vs 소각 동치 처리 금지 — 소각만 EPS 영구 제거.
  - 단년도 배당으로 지속 가능성 단정 금지 — 5 년 시계열 동반.
failureModes:
  - 배당수익률 산정의 주가 기준일 모호 (당일 vs 평균)
  - 일회성 자사주 매입을 반복 정책으로 단정
  - 외환 매출 비중 큰 회사의 환율 영향 + 배당 정책 미반영
  - 외국인 보유 비중 변화에 따른 배당 압력 미고려
  - 분기 배당 vs 연 배당 빈도 차이 무시
examples:
  - 삼성전자 배당 thesis (3 축)
  - 배당수익률 + payout + FCF
  - 자사주 매입 / 소각 영향 분리
  - 5 년 환원 추세 + 지속 가능성
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

dividend = dartlab.scan("dividendTrend")
capital = c.analysis("financial", "자본배분")
cashflow = c.analysis("financial", "현금흐름")
return_axis = c.analysis("financial", "배당주주환원")
```

## 호출 동작

배당 정책 raw 데이터 → 자본배분 우선순위 (배당 vs CAPEX vs 자사주) → 현금흐름 quality (FCF / 배당 충당 비율) → 주주환원 시계열 종합.

1. 회사 진입
2. show("dividend") — 과거 배당 정책 시계열 + 배당성향
3. analysis("financial", "자본배분") — 자본배분 의지 점수
4. analysis("financial", "현금흐름") — FCF / 배당 충당 비율
5. analysis("financial", "배당주주환원") — 주주환원 종합 (있으면)

## 대표 반환 형태

- `tableRef` 3+ 개 (dividend 정책 + 자본배분 + 현금흐름)
- `valueRef` 4+ (배당성향 % / FCF / 배당지급액 / payout ratio / DPS 성장률)
- `dateRef` 1 개

## 연계 절차

1. engines.company — 회사 진입
2. recipes.fundamental.dividend.capitalReturn — 배당·자사주 종합
3. engines.analysis — 자본배분 의지
4. engines.analysis — FCF 가 배당 충당 가능 여부

## 기본 검증

- 배당성향 (%) + DPS 성장률 (%) 명시.
- FCF 가 배당 지급액의 몇 배인지 (충당 배수) 명시.
- 자사주 매입이 있으면 배당 + 자사주 합산 주주환원율 함께.
- "배당 지속 가능" 같은 단정 X — 과거 N 년 + 가정 + 시나리오 명시.
