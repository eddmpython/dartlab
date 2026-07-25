---
id: engines.analysis
title: Analysis
kind: curated
scope: builtin
status: observed
category: engines
purpose: Analysis 엔진은 단일 기업의 재무제표, 가치평가, 지배구조, 전망, 기업 단위 매크로 민감도를 22개 분석 축으로 읽는 실행 스킬이다. 트리거 — '재무 분석', '가치평가', '지배구조 점검', '전망'.
whenToUse:
  - Analysis
  - analysis
  - 기업 재무제표 분석
  - 수익구조
  - 자금조달
  - 자산구조
  - 현금흐름
  - 수익성
  - 성장성
  - 안정성
  - 효율성
  - 종합평가
  - 이익품질
  - 비용구조
  - 자본배분
  - 투자효율
  - 재무정합성
  - 가치평가
  - 지배구조
  - 공시변화
  - 비교분석
  - 매출전망
  - 예측신호
  - 매크로민감도
  - 밸류에이션밴드
inputs:
  - Company 객체 또는 종목코드
  - group 또는 axis
  - 세부 분석 축
  - 기준 기간
  - 비교/가정/오버라이드
outputs:
  - 분석 축 가이드 DataFrame
  - 계산 항목 가이드 DataFrame
  - 축별 분석 dict
  - tableRef/valueRef/dateRef/executionRef
  - story/report handoff
capabilityRefs:
  - analysis
  - Company.analysis
  - Company.panel
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.data.foundation
  - engines.story
sourceRefs:
  - dartlab://skills/engines.analysis
requiredEvidence:
  - target
  - period
  - metric
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 선택한 분석 축
  - 실제 공개 호출
  - 대표 반환 형태
  - 검증한 근거와 제한
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
    notes:
      - 실제 실행 가능 여부는 연결된 Company 데이터 snapshot과 capability 지원 범위를 따른다.
failureModes:
  - axis 가이드를 확인하지 않고 과거 스킬명이나 삭제된 문서 경로로 이동함
  - 결손값을 0으로 대체해 수익성/현금흐름/안정성 판단을 왜곡함
  - analysis 안에서 다른 L2 엔진 (credit · macro · quant · industry) 결과 또는 L1.5 (scan) · L3 조합기 (story) 를 직접 import 해 결합함
  - 스킬의 공개 호출 방식과 실제 공개 API가 어긋난 상태로 방치함
forbidden:
  - 근거 없는 숫자를 만들지 않는다.
  - 결손값을 0으로 대체하지 않는다.
  - analysis 엔진에서 다른 L2 엔진 (credit · macro · quant · industry) 또는 L1.5 (scan) · L3 조합기 (story) 를 직접 import 하지 않는다 — 결합은 story 가 단독으로 담당.
  - 시장 레벨 매크로 해석을 analysis가 담당한다고 설명하지 않는다.
  - 공개 API 호출법, 반환 형태, 오류/제한 동작이 바뀌었는데 이 skill을 갱신하지 않은 상태로 완료 처리하지 않는다.
examples:
  - 삼성전자 수익성 분석
  - 기업 현금흐름과 이익품질 점검
  - 가치평가 축으로 적정가 범위 확인
  - 매출전망과 예측신호 확인
  - Company.analysis 호출법
  - 22 분석 축 가이드 확인
  - 기업 매크로 민감도 측정
procedure:
  - dartlab.Company(code) 또는 c.analysis() 로 22 축 가이드 DataFrame 확인.
  - group (financial · valuation · forecast · governance) 과 axis 선택.
  - c.analysis(group, axis) 또는 dartlab.analysis(...) 호출.
  - 결과의 tableRef · valueRef · dateRef · executionRef 검증 후 답변에 묶음.
  - 다른 L2 (credit · macro · quant · industry) · L1.5 (scan) · L3 조합기 (story) 와 직접 결합하지 않는다 — 결합은 story 가 담당.
linkedSkills:
  - engines.company
  - engines.analysis.cashflow
  - engines.analysis.valuation
  - engines.story
  - engines.credit
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-07'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`analysis`는 단일 기업을 재무제표의 인과 구조로 읽는 L2 엔진이다. 이 엔진은 매출과 비용, 자산과 부채, 현금흐름, 수익성, 성장성, 안정성, 효율성, 가치평가, 지배구조, 전망 신호를 축별로 계산하고 해석한다.

담당하는 질문은 "이 회사는 무엇으로 돈을 벌고, 그 돈은 진짜 현금으로 남고, 그 성장은 지속 가능하며, 지금 가격은 어느 정도인가"이다. 시장 전체 매크로 전망은 `engines.macro`, 신용등급/부도위험 중심 평가는 `engines.credit`, 여러 종목을 찾는 작업은 `engines.scan`, 최종 보고서 조합은 `engines.story`가 담당한다.

## 공개 호출 방식

기본 호출은 `Company.analysis()`이다. 축을 모르면 먼저 가이드를 보고, 축을 알면 group과 axis를 지정한다.

```python
import dartlab

c = dartlab.Company("005930")

# 1. 전체 분석 축 가이드
guide = c.analysis()

# 2. 그룹 가이드 또는 그룹 내 계산 항목 확인
financial = c.analysis("financial")

# 3. 특정 분석 축 실행
profitability = c.analysis("financial", "수익성")
cashflow = c.analysis("financial", "현금흐름")
valuation = c.analysis("valuation", "가치평가")
forecast = c.analysis("forecast", "매출전망")

# 4. 축 이름만으로 실행 가능한 경우
profitability = c.analysis("수익성")

# 5. 모듈 함수형 호출 — Company 객체는 company= keyword (positional 3 번째 안 받음)
profitability = dartlab.analysis("financial", "수익성", company=c)
valuation = dartlab.analysis("valuation", "가치평가", company=c)
# stockCode 단독 호출도 가능
profitability = dartlab.analysis("financial", "수익성", stockCode="005930")
```

노트북이나 MCP에서 사람이 따라 할 때도 같은 순서로 쓴다. 먼저 `c.analysis()`로 가능한 축을 확인하고, 그 다음 실제 축을 호출한다.

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

22 axis 질문 (수익성·밸류에이션·안정성·효율성·종합평가·이익품질·자본배분·성장성 등) 에서 다음 4 룰은 강행이다 — 위반 시 refs=0 회귀로 답변 품질 65 점 이하 하락.

1. **1 차 도구는 EngineCall 강제**. axis 명이 질문에 있거나 22 axis 가이드 표에 매칭되면 `EngineCall(apiRef="Company.analysis", args={...})` 또는 `EngineCall(apiRef="Company.panel", args={...})` 가 첫 호출. **RunPython 직접 ratio 계산은 engine 호출 결과가 부재할 때만 fallback** — 처음부터 raw 계산 금지.

   이유: EngineCall 결과 dict 는 `@tagConfidence` 데코레이터로 `tableRef`·`valueRef`·`dateRef`·`executionRef` 자동 발급. RunPython 은 raw eval — refs 0 발급. 답변 본문 인용 가치체인이 깨진다.

2. **본문 안 모든 숫자에는 inline ref 표기 필수**. 형식: `13.07% [ref:vr_...]` 또는 `[tableRef: tr_...]`. ref 없는 숫자는 답변에 적지 않거나 "EngineCall 재시도 필요" 명시.

3. **dataAsOf 확인 → 답변 첫 줄 명시**. 결과 dict 의 `dataAsOf` 가 stale (3 분기 이상 전) 이면 "현재 시점 단정 X — dataAsOf 기준" 명시.

4. **flags / assumptions / freshness 누락 시 답변 보류**. 결과의 `flags` 가 non-empty 면 "데이터 제한" 으로 답변에 인용. assumptions 가 있는 축 (valuation 등) 은 항상 본문에 노출.

## 분기 추세가 필요한 경우 (axis 22 종은 연간 한정)

`Company.analysis(axis=...)` 의 22 axis 분석은 **연간 시계열 기반**. analyzeProfitability 등 내부 함수는 `aSeries: dict` (annual series) 만 받는다. 즉 "최근 분기 수익성 어땠어 / Q1 회복 신호 있어" 류 질문은 engine 의 axis 함수 단독으로 답할 수 없다.

조합 패턴:

```python
# 1. 분기 raw (show 는 freq='Q' 지원)
isQ = c.panel("IS", freq="Q")  # 분기 손익
bsQ = c.panel("BS", freq="Q")  # 분기 재무상태

# 2. 연간 axis 분석 (grade + 임계값 + 추세)
profit = c.analysis("financial", "수익성")  # 연간 grade A~F + DuPont

# 3. ai 가 1+2 결합해 narrative — 연간 grade + 분기 최신 추세 동시 인용
```

agent EngineCall 양식:

```python
# 분기 raw
EngineCall(apiRef="Company.panel", args={"stockCode": "005930", "stmt": "IS", "freq": "Q"})
EngineCall(apiRef="Company.panel", args={"stockCode": "005930", "stmt": "BS", "freq": "Q"})

# 연간 axis
EngineCall(apiRef="Company.analysis", args={"stockCode": "005930", "group": "financial", "axis": "수익성"})
```

분기-축 통합은 engine 미지원 — 3 호출 결과를 ai 가 답변에 직접 엮는다. panel 결과의 `tableRef`·`valueRef` 와 analysis 결과의 `executionRef` 가 함께 발급되어 refs 가치체인 유지.

## 호출 동작

`axis`가 없으면 실행 가능한 분석 축 가이드 DataFrame을 반환한다. 이 가이드는 사람이 어떤 축을 골라야 하는지 보여주는 공개 메뉴다.

`group`만 주면 해당 그룹의 축 또는 계산 항목 가이드를 반환한다. 회사 객체가 없는 함수형 호출에서는 계산 목록을 탐색하는 용도로 쓰이고, 회사 객체가 있는 호출에서는 해당 회사 기준으로 축 실행을 준비한다.

`group`과 `axis`가 함께 있거나 축 이름만 들어오면 해당 축을 실행한다. 엔진은 `Company`가 가진 재무제표, 시계열, 공시/시장 데이터 snapshot, 내부 계산 registry를 읽고 축별 계산을 수행한다.

데이터가 충분하면 축별 분석 dict를 반환한다. 데이터가 부족하면 결손을 0으로 채우지 않고, `flags`, `assumptions`, `dataAsOf`, 빈 history, null 값, 제한 메시지 등으로 표현한다. 호출한 group 또는 axis가 없으면 사용 가능한 group/axis를 확인할 수 있는 오류를 낸다.

`analysis`는 다른 L2 엔진 (`credit` · `macro` · `quant` · `industry`) 을 내부에서 import 해 조합하지 않으며, L1.5 (`scan`) · L3 조합기 (`story`) 도 직접 사용하지 않는다. 필요한 원천 데이터는 `Company` (L1) / core (L0) 계층에서 직접 읽고, 최종 조합은 `story` 가 단독으로 짊어진다 (L2 끼리의 import 가 만드는 순환참조 방지).

## 분석 축 전체

| group | axis | 담당 질문 | 대표 호출 | items |
| --- | --- | --- | --- | --- |
| financial | 수익구조 | 이 회사는 무엇으로 돈을 버는가 | `c.analysis("financial", "수익구조")` | 8 |
| financial | 자금조달 | 돈을 어디서 조달하는가 | `c.analysis("financial", "자금조달")` | 9 |
| financial | 자산구조 | 조달한 돈으로 뭘 준비했는가 | `c.analysis("financial", "자산구조")` | 4 |
| financial | 현금흐름 | 실제로 현금은 어떻게 흘렀는가 | `c.analysis("financial", "현금흐름")` | 4 |
| financial | 수익성 | 이 회사는 얼마나 잘 벌고 있는가 | `c.analysis("financial", "수익성")` | 6 |
| financial | 성장성 | 이 회사는 얼마나 빨리 성장하는가 | `c.analysis("financial", "성장성")` | 5 |
| financial | 안정성 | 이 회사는 망하지 않는가 | `c.analysis("financial", "안정성")` | 6 |
| financial | 효율성 | 이 회사는 자산을 잘 굴리는가 | `c.analysis("financial", "효율성")` | 2 |
| financial | 종합평가 | 재무 상태를 한마디로 본다 | `c.analysis("financial", "종합평가")` | 3 |
| financial | 이익품질 | 이익이 진짜인가 | `c.analysis("financial", "이익품질")` | 7 |
| financial | 비용구조 | 비용이 어떻게 움직이는가 | `c.analysis("financial", "비용구조")` | 5 |
| financial | 자본배분 | 번 돈을 어디에 쓰는가 | `c.analysis("financial", "자본배분")` | 7 |
| financial | 투자효율 | 투자가 가치를 만드는가 | `c.analysis("financial", "투자효율")` | 5 |
| financial | 재무정합성 | 재무제표가 서로 맞는가 | `c.analysis("financial", "재무정합성")` | 6 |
| valuation | 가치평가 | 이 회사의 적정 가치는 얼마인가 | `c.analysis("valuation", "가치평가")` | 14 |
| governance | 지배구조 | 이 회사의 주인은 누구이며 감시는 작동하는가 | `c.analysis("governance", "지배구조")` | 8 |
| governance | 공시변화 | 이 회사의 공시가 뭐가 달라졌는가 | `c.analysis("governance", "공시변화")` | 4 |
| governance | 비교분석 | 이 회사는 시장에서 어디에 서 있는가 | `c.analysis("governance", "비교분석")` | 3 |
| forecast | 매출전망 | 이 회사의 매출은 어디로 가며 재무는 어떻게 변하는가 | `c.analysis("forecast", "매출전망")` | 8 |
| forecast | 예측신호 | 이 회사의 실적은 어디로 향하는가 | `c.analysis("forecast", "예측신호")` | 15 |
| macro | 매크로민감도 | 이 회사의 매출은 어떤 매크로 변수에 민감한가 | `c.analysis("macro", "매크로민감도")` | 1 |
| macro | 밸류에이션밴드 | PER/PBR이 과거 대비 어디에 있는가 | `c.analysis("macro", "밸류에이션밴드")` | 1 |

## 대표 반환 형태

전체 가이드 호출은 DataFrame을 반환한다.

```text
c.analysis()
-> DataFrame
   axis, description, example, group, items, apiKey
```

특정 축 실행은 dict를 반환한다. 공통적으로 다음 계열을 확인한다.

```text
c.analysis("financial", "수익성")
-> dict
   items: 축별 계산 항목과 결과
   history: 기간별 핵심 값
   displayHints: 표/차트 표시 힌트
   turningPoints: 변곡점 또는 변화 감지 결과
   dataAsOf: 데이터 기준일과 snapshot 정보
   assumptions: 계산 가정과 제한
   flags: 결손, 이상치, 비교 불가, 제한 상태
   _summary: 사람이 읽을 요약
   tableRef/valueRef/dateRef/executionRef: 근거 연결용 참조
```

축별 dict에는 공통 키 외에 전용 블록이 붙을 수 있다. 예를 들어 수익성은 매출총이익률, 영업이익률, 순이익률, ROE/ROA 흐름을 포함하고, 현금흐름은 영업/투자/재무 현금흐름과 잉여현금흐름을 포함한다. 안정성은 부채비율, 유동성, 이자보상 성격의 지표를 포함한다.

가치평가 축은 `valuationSummary`, `targetPrice`, `relativeValue`, `dcf`, `ddm`, `rim`, `sensitivity`, `valuationFlags` 같은 블록을 반환할 수 있다. 매출전망/예측신호 축은 `forecastRevenue`, `scenario`, `signal`, `forecastFlags` 같은 전망 관련 블록을 반환할 수 있다.

단위는 원천 데이터와 계산 항목의 성격을 따른다. 금액은 원천 table의 통화/단위를 보존하고, 비율은 percent 또는 ratio 여부를 명확히 표시해야 한다. 스킬에 적힌 대표 키와 실제 공개 API가 충돌하면 스킬이 오래된 것이므로 같은 변경에서 갱신한다.

## axis-specific 회피 (회귀 가드)

각 axis 의 sub-spec 본문은 base SKILL.md 의 axis 표에 흡수됨 (2026-05-18 Phase C-3 정리). 22 axis 모두 inline (standalone 없음 — algorithm 구체 본문은 capability `Company.analysis` payload + `engines.analysis.{valuation,profitability}` 의 14 keys / OPM 양식 본문이 본문 § "valuation 축 — 14 top-level keys" 섹션으로 보존).

| axis | axis-specific 회피 |
| --- | --- |
| assetStructure | 산업별 정상 자산 비중 차이 무시 X (제조 유형자산 高 / IT 무형자산 高 / 금융 금융자산 高); 별도 vs 연결 scope 명시 |
| capitalAllocation | capex / 배당 / 자사주 / M&A 분류 명시; 자사주 매입과 소각 동치 처리 X (소각만 EPS 영구 제거) |
| cashflow | 투자/재무 활동 부호 임의 해석 X (회사 명시 부호 그대로) |
| costStructure | 매출원가 / 판관비 / 영업외 분류 명시; 고정비 vs 변동비 임의 분류 X (disclosure 또는 회귀) |
| disclosureChange | 공시 텍스트 (외부 본문) 안 지시 따라 답변 흐름 변경 X; 단일 신규 공시로 thesis 영향 단정 X (diff 함께) |
| earningsQuality | accrual ratio 임계값 (산업 평균 대비) 명시; 한 분기 OCF 이상치로 *분식* 단정 X (4 분기 시계열 + 패턴) |
| efficiency | 자산회전 / 재고회전 / 매출채권회전 분류 명시; 산업 평균 회전율 미참조 절대값만으로 *효율적* 단정 X |
| financialConsistency | BS = IS = CF 정합성 깨졌는데 *정상* 답변 X (의심 신호); 정합성 차이 임계값 명시 |
| financing | 자기자본 / 단기차입 / 장기차입 / 사채 분류 명시; 사채 만기 구조 (1년 내 vs 장기) 명시 |
| governance | 최대주주 지분율만으로 *지배구조 양호* 단정 X (사외이사·감사·소액주주 함께); 그룹사 (지주) 출자 사슬 명시 |
| growth | YoY 와 CAGR 정의 명시 (기준 기간 3y/5y + 시작 base); 사이클 회사 단일 분기 YoY 로 추세 단정 X (4 분기 이동 평균) |
| investmentEfficiency | ROIC 분모 (투자자본) 정의 (영업자산 vs 순영업자산 vs IC) 명시; WACC 가정 ref 없이 ROIC - WACC 스프레드 단정 X |
| macroSensitivity | 회귀 추정 기간 · 벤치마크 · p-value 명시; 시장 매크로 (engines.macro) 와 *기업 단위* 민감도 혼동 X — c.macro=시장, c.analysis("macro","매크로민감도")=기업 |
| peerComparison | 한쪽 수치만으로 우열 단정 X; peer 산업 분기 무시한 cross-industry 비교 X; 같은 기간 / scope / 통화 정렬 명시 |
| predictionSignal | 단일 신호로 *상승/하락* 단정 X (5+ 신호 종합); 신호 정확도 (hit ratio) 명시 |
| profitability | ROE 분모 (평균자본 vs 기말자본) 정의 명시; stale 기간 (3 분기 전) 을 *현재* 단정 X (dataAsOf 명시); 다중 종목 비교는 **`PeerCompareN` 1 회** 권장 (Company.panel N 회 X) |
| revenueForecast | 매출 전망 가정 (수량 · 단가 · mix · 환율) 분리 명시; 단일 시나리오 (best case 만) X (base/upside/downside 3 시나리오) |
| revenueStructure | 사업부별 / 지역별 / 제품별 매출 분리 명시; 외화 매출 비중 명시 (환율 변동 영향 별도) |
| scorecard | 5 영역 (수익성·안정성·성장성·효율성·현금흐름) 가중치 명시; 등급 (A-F) 임계값을 산업 평균 미참조 적용 X |
| stability | 금융사 (은행·보험) 에 일반 부채비율 적용 X (BIS · LCR 별도); 부채비율 단일 metric 으로 위험 단정 X (ICR + OCF/부채 교차); 우발부채 (off-balance) 명시 |
| valuation | DCF 가정 ref 없이 적정가 단정 X; 산업별 멀티플 차이 명시 (제조 PER vs 금융 PBR vs 바이오 PSR); 단일 멀티플 (PER) 만으로 결론 X (DCF + 멀티플 + RIM 교차). 14 keys 양식은 본문 § "valuation 축 — 14 top-level keys" 참조 |
| valuationBand | 5y / 10y range 명시 없이 *밴드 상단/하단* 답변 X; 산업 평균 멀티플과 historical 밴드 동일시 X |

**공통 forbidden** (모든 axis): 숫자 없는 수익성 판단 X · 결손값을 0 으로 대체 X · 단일 종목 분석을 scan/screen 으로 바꾸기 X.

## valuation 축 — 14 top-level keys (기존 engines.analysis.valuation)

`c.analysis("valuation", "가치평가")` 1 회 결과 dict 의 핵심 키 (값 그대로 인용, 추가 호출 X):

| key | 의미 |
| --- | --- |
| `dcfValuation` | DCF (`perShareValue` · `enterpriseValue` · `discountRate` · `growthRateInitial` · `terminalGrowth` · `fcfProjections[5]` · `marginOfSafety`) |
| `relativeValuation` | 멀티플 (`sectorMultiples` · `currentMultiples` · `impliedValues` · `premiumDiscount` · `consensusValue` · `warnings`) |
| `residualIncome` | RIM (`perShareValue` · `bps` · `costOfEquity`) |
| `ddmValuation` | DDM (`perShareValue` · `dps` · `dividendGrowth` · `discountRate`) |
| `priceTarget` | 시나리오 (`weightedTarget` · `percentiles` p10/p25/p50/p75/p90 · `expectedValue` · `upside` · `signal` (strong_sell/sell/hold/buy/strong_buy) · `scenarios[]`) |
| `valuationSynthesis` | 종합 (`fairValueRange` · `verdict` (고평가/저평가/적정) · `weightedFairValue` · `modelWeights` · `estimates[]` · `companyType` (growth/cyclical/value/...)) |
| `plausibilityBand` | peer 위치 (`growthPercentile` · `marginPercentile` · `band` (within/above/below) · `peerStats`) |
| `lifeCycle` | (`phase` matureGrowth/matureStable/decline/... · `phaseConfidence` · `modelHint` (dcf/ddm/relative)) |
| `sensitivity` | WACC × 영구성장률 표 |
| `reverseImplied` | 역산 (`impliedGrowthRate` 현재가가 함의하는 성장률) |
| `cashFlowConsistency` | OCF/순이익 비율 |
| `valuationFlags` · `valuationSins` | 가치평가 경고 |
| `storyPrecedents` | 유사 종목 선례 |
| `assumptions` | (`wacc` · `terminalGrowth` · `growthRates` · `confidence` · `primaryModel`) |

답변 양식 7 단: 결론 (verdict + weightedFairValue) → 4 방법론 표 → 시나리오 가격 (priceTarget.percentiles) → DCF 정규화 경고 (mid-cycle FCF) → plausibility band peer percentile → lifeCycle modelHint → 한계.

## EngineCall (agent 경로) args 매핑

agent (ai/mcp/server) 가 본 엔진을 호출할 때는 `EngineCall(apiRef="Company.analysis", args={...})` 양식. positional 인자를 args dict 의 key 로 변환:

| `c.analysis(...)` | `EngineCall(apiRef="Company.analysis", args=...)` |
| --- | --- |
| `c.analysis()` (가이드) | `{"stockCode": "005930"}` (axis 생략 → 가이드) |
| `c.analysis("financial")` (그룹) | `{"stockCode": "005930", "group": "financial"}` |
| `c.analysis("financial", "수익성")` | `{"stockCode": "005930", "group": "financial", "axis": "수익성"}` |
| `c.analysis("수익성")` (축만) | `{"stockCode": "005930", "axis": "수익성"}` |

**guard** — group 과 axis 를 점 표기로 합쳐 `apiRef="analysis.financial.profitability"` 호출 금지. `apiRef="Company.analysis"` 고정 + args 에 분리.

## Company.panel vs Company.analysis — 어느 쪽?

| 질문 | 권장 |
| --- | --- |
| "2025Q4 매출 / 영업이익 / 순이익 알려줘" — 원자료 인용 | `Company.panel("IS")` |
| "이 회사 수익성 어때 / 개선됐어?" — 인과 해석 | `Company.analysis("financial", "수익성")` |
| 7 축 신용 약점 분해 | `Company.panel("IS").data.dcrBadge.axes` (자동 부착, 추가 호출 불필요) |
| 산업 라이프사이클 / peers | `Company.panel(...).data.industryBadge` (자동 부착) |
| DCF / 멀티플 / 적정가 | `Company.analysis("valuation", "가치평가")` |

**핵심 차이** — `Company.panel` 는 *원자료 + 자동 부착 badge (dcrBadge / industryBadge)*, `Company.analysis` 는 *해석 결과 (assumptions · narrative · history)*. 단순 숫자 조회면 panel, 해석/근거 chain 이 필요하면 analysis. 단일 종목 신용 질문은 panel 1 회만으로 7 축 분해 완성 — analysis credit 또는 EngineCall("credit") 추가 불필요.

## 축 선택 규칙

수익구조, 비용구조, 이익품질, 현금흐름처럼 재무제표 안에서 인과를 읽는 질문은 `financial` 그룹을 쓴다.

적정가, 멀티플, DCF/DDM/RIM, 목표가 범위는 `valuation` 그룹을 쓴다. 단, 가치평가 결과를 말할 때는 수익성, 성장성, 현금흐름, 자본배분의 근거를 같이 확인한다.

주주, 이사회, 공시 변화, 동종 비교는 `governance` 그룹을 쓴다. 업종 전체 구조 분석은 `engines.industry`, 보고서 문장 조합은 `engines.story`로 넘긴다.

매출 전망과 실적 방향은 `forecast` 그룹을 쓴다. 시장 전체 금리/환율/물가 전망은 `engines.macro`가 담당하고, analysis의 `macro` 그룹은 기업 단위 민감도와 밴드 확인에 한정한다.

여러 종목을 조건으로 찾는 일은 `analysis`가 아니라 `engines.scan`이 담당한다. scan으로 후보를 찾고, 각 후보를 `analysis`로 깊게 읽는다.

## 기본 실행 순서

1. 대상 기업을 확정한다: `c = dartlab.Company("005930")`.
2. 축이 불명확하면 `c.analysis()`로 전체 가이드를 확인한다.
3. 질문 성격에 맞는 group/axis를 고른다.
4. 실제 축을 호출한다: `c.analysis("financial", "수익성")`.
5. `history`, `items`, `flags`, `assumptions`, `dataAsOf`를 먼저 확인한다.
6. 숫자를 말할 때 `tableRef`, `valueRef`, `dateRef`, `executionRef`를 연결한다.
7. 여러 축을 보고서로 엮을 때는 `story`가 조합한다.

## 기본 검증

분석 결과는 최소한 대상, 기간, 지표명, 값, 단위, 기준일을 함께 확인한다. 기간 비교가 필요한 축은 전년동기, 전기, 최근 3년/5년 흐름 중 어떤 기준을 썼는지 밝혀야 한다.

결손값, 음수 전환, 회계 기준 변경, 사업 분할/합병, 상장 기간 부족, 데이터 snapshot 제한은 정상 값처럼 포장하지 않는다. 계산이 제한되면 `flags`와 `assumptions`를 결과의 일부로 취급한다.

스킬은 공개 실행 문서다. `Company.analysis()` 또는 `dartlab.analysis()`의 호출 방식, 대표 반환 키, 오류/제한 동작이 바뀌면 이 파일과 관련 응용 스킬을 같은 변경에서 갱신해야 한다.
