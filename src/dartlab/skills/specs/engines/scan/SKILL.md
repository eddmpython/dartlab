---
id: engines.scan
title: Scan
kind: curated
scope: builtin
status: observed
category: engines
purpose: Scan 엔진은 시장/유니버스 횡단면에서 후보를 발굴하고 순위를 계산하는 실행 스킬이다. 트리거 — '스캔', '종목 발굴', '후보 추출', '랭킹'.
whenToUse:
  - Scan
  - scan
  - 스크리닝
  - 저평가 종목
  - 전종목 비교
  - 재무비율 횡단면
  - 공시리스크
  - 배당추이
  - 퀄리티 스캔
  - 조건형 screen
inputs:
  - axis
  - target 또는 preset
  - universe
  - spec
  - metric/account/ratio
outputs:
  - guide DataFrame
  - ranking/filter DataFrame
  - candidate evidence table
capabilityRefs:
  - scan
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.data.foundation
  - engines.analysis
sourceRefs:
  - dartlab://skills/engines.scan
requiredEvidence:
  - universe
  - datasetAsOf
  - filter
  - formula
  - table
  - executionRef
  - sourceRef
expectedOutputs:
  - 선택한 scan axis
  - 공개 호출
  - 필터/계산식
  - 후보 evidence table
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
      - prebuilt snapshot과 Pyodide 포함 데이터 범위에 따라 일부 axis가 제한될 수 있다.
failureModes:
  - universe와 기준일 없이 후보를 나열함
  - ranking table 없이 회사명 bullet만 제시함
  - account/ratio primitive와 screen preset을 혼동함
  - scan 후보를 심층 analysis 검증 없이 투자 결론으로 확정함
forbidden:
  - universe, 필터, 계산식, 기준일, table ref 없이 후보 발굴을 완료했다고 말하지 않는다.
  - 결손값을 0으로 대체하지 않는다.
  - 단일 기업 심층 해석을 scan에서 끝내지 않는다. 후보 발굴 뒤 analysis/credit/quant로 검증한다.
  - 공개 API 호출법, guide 축, 반환 형태가 바뀌었는데 이 skill을 갱신하지 않은 상태로 완료 처리하지 않는다.
examples:
  - 저평가 퀄리티 종목 찾기
  - 배당 증가 종목 스크리닝
  - 공시리스크 상위 종목 확인
  - ROE 전 종목 횡단 비교
  - 매출 상위 100 개 회사 발굴
  - 신용 위험 상위 100 개 스크리닝
procedure:
  - dartlab.scan() 으로 22 축 가이드 DataFrame 확인.
  - axis 선택 (account · ratio · screen · valuation · quality · governance 등).
  - dartlab.scan(axis, target?, universe=..., spec=...) 호출.
  - 결과의 ranking · universe · datasetAsOf · filter · formula · executionRef 묶음.
  - 후보 발굴 후 단일 종목 심층 검증은 engines.analysis · engines.credit · engines.quant.
linkedSkills:
  - engines.scan.ratio
  - engines.scan.screen
  - engines.analysis
  - engines.credit
  - engines.quant
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

`scan`은 여러 기업을 한 번에 훑어 후보를 찾는 **L1.5 횡단 엔진**이다. L1 (company · gather) 위에서 전체 종목 universe 를 스캔해 ranking · filter · candidate evidence table 을 만든다. 단일 종목 심층 분석은 L2 (analysis · credit · macro · quant · industry) 의 책임. 질문의 단위가 "삼성전자를 분석해줘"이면 `Company`/`analysis`가 우선이고, "조건에 맞는 종목을 찾아줘", "전종목에서 상위 기업을 골라줘"이면 `scan`이 우선이다.

`account`와 `ratio`는 primitive다. 복합 투자 질문은 `screen` preset/spec 또는 `quality`, `valuation`, `growth`, `profitability` 같은 축으로 시작하고, 최종 판단은 후보별 `analysis`, `credit`, `quant`로 검증한다.

## 공개 호출 방식

```python
import dartlab

# 전체 스캔 축 가이드
guide = dartlab.scan()

# 축 실행
quality = dartlab.scan("quality")
valuation = dartlab.scan("valuation")
cashflow = dartlab.scan("cashflow")

# primitive
revenue = dartlab.scan("account", "매출액")
roe = dartlab.scan("ratio", "roe")
inventory = dartlab.scan("note", "재고자산")   # 주석 lineitem 횡단 (재고 세분·리스·법인세 등)

# 조건형 스크리닝
fields = dartlab.scan("fields", "roe")
value = dartlab.scan("screen", "value")
custom = dartlab.scan("screen", spec={"filters": []})

# 파생 필드 조합 (spec.define): 순현금 = 현금 - 단기차입, 저부채 교차
safe = dartlab.scan("screen", spec={
    "define": {"netCash": {"op": "sub",
        "left": "finance.account.cash_and_cash_equivalents",
        "right": "finance.account.shortterm_borrowings"}},
    "where": [{"field": "@netCash", "op": ">", "value": 0},
              {"field": "finance.ratio.debtRatio", "op": "<", "value": 30}],
    "sort": {"field": "@netCash", "desc": True}})

# 시계열(연간 격자) + 상대(업종 횡단) 파생: 꾸준한 흑자 · 성장 · 업종내 상위
comp = dartlab.scan("screen", spec={
    "define": {
        "opMin3y":     {"op": "min",  "field": "finance.account.operating_profit", "years": 3},
        "salesCagr3y": {"op": "cagr", "field": "finance.account.sales", "years": 3},
        "roeIndPct":   {"op": "percentile", "field": "finance.ratio.roe", "by": "industry"}},
    "where": [{"field": "@opMin3y", "op": ">", "value": 0},        # 3년 연속 흑자
              {"field": "@salesCagr3y", "op": ">", "value": 0.05}, # 매출 CAGR 5%+
              {"field": "@roeIndPct", "op": ">", "value": 80}],    # 업종내 ROE 상위 20%
    "sort": {"field": "@roeIndPct", "desc": True}})
# 저장 스크린으로 등재된 실증본: dartlab.scan("screen", "resilientCompounders")
```

**define 노드 문법 (폐쇄 vocabulary, 문자열 eval 없음, 단위 전파)**

| 종류 | op | 노드 형태 | 결과 단위 |
|---|---|---|---|
| 산술 | add / sub / mul / div | `{op, left, right}` (필드키·@참조) | 단위대수 (div 동일단위→배, 0나눗셈→null) |
| 패스스루 | (없음) | `{field}` | 원 필드 단위 |
| 시계열 | mean / min / max | `{op, field, years}` (연간 격자 축약) | 원 필드 단위 |
| 시계열 | yoy | `{op, field}` (최근 2년) | 배 (무차원 성장) |
| 시계열 | cagr | `{op, field, years}` (양 끝 양수 필요) | 배 |
| 시계열 | slope | `{op, field, years}` (OLS, null 무시) | 원 필드 단위/년 |
| 상대 | percentile | `{op, field, by?}` (0~100) | 백분위 |
| 상대 | zscore | `{op, field, by?}` ((v-평균)/표준편차) | 표준편차 |

- 시계열 `field` 는 `finance.account.*` · `finance.ratio.*` 원천만 (연간 격자 보유). valuation/krx/note 는 ValueError.
- 상대 `field` 는 원천 필드 또는 `@파생참조`. `by` 생략=전체 유니버스, `by:"industry"`=업종(dartlab.listing 업종) 횡단. 단독 업종·표준편차 0 은 null.
- `@name` 은 define 선언 후 어디서나 (where·select·sort·다른 define) 참조. 위상정렬로 의존 자동 해소, 순환·미정의는 즉시 ValueError.

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

22 axis 횡단 스크리닝에서 다음 4 룰 강행 — 메모리 압박 + refs 0 회귀 차단.

1. **1 차 도구는 EngineCall 강제**. `EngineCall(apiRef="scan", args={"axis": "ratio", "metric": "roe"})` 양식. RunPython 으로 전 종목 parquet 직접 로드 금지 — Polars Rust 힙 누수 (Company 1 개 ≈ 200~500MB) 로 OOM 가능.
2. **개별 종목 분석 질문에 scan 호출 금지** — "삼성전자 수익성" 처럼 단일 기업이면 `Company.panel`/`Company.analysis` 사용. scan 은 *여러 종목 후보 찾기* 한정.
3. **scan 결과 후보 → 상위 N (보통 10~20) 만 다음 단계로 전달**. 전종목 결과 그대로 답변 본문 dump 금지.
4. **본문 숫자에 `[datasetRef:...]` + `[tableRef:...]` inline 표기 필수** — 스캔 결과는 prebuild 시점 (asOf) 변동 큼.

## 호출 동작

무인자 `dartlab.scan()`은 실행 가능한 스캔 축 가이드 DataFrame을 반환한다. 특정 axis를 주면 해당 유니버스의 prebuilt parquet 또는 provider scan 함수를 읽어 DataFrame을 반환한다.

`account`와 `ratio`는 전종목 단일 계정/비율 시계열을 조회하는 원자 축이다. `fields`는 조건형 screen에 넣을 필드를 찾는 축이고, `screen`은 preset 또는 spec 기반 조건식을 실행한다.

데이터가 없거나 snapshot이 제한되면 값을 추정하지 않는다. 빈 DataFrame, 결손 컬럼, 제한 메시지, 기준일 누락을 그대로 드러내고 필요한 수집/필드 확인 경로를 말한다.

## 전체 축/메서드 목록

| axis | label | group | 대표 호출 |
| --- | --- | --- | --- |
| governance | 거버넌스 | DART | `dartlab.scan("governance")` |
| workforce | 인력/급여 | DART | `dartlab.scan("workforce")` |
| capital | 주주환원 | DART+EDGAR | `dartlab.scan("capital")` |
| debt | 부채구조 | DART+EDGAR | `dartlab.scan("debt")` |
| account | 계정 | DART+EDGAR | `dartlab.scan("account", "매출액")` |
| ratio | 비율 | DART+EDGAR | `dartlab.scan("ratio", "roe")` |
| note | 주석 | DART | `dartlab.scan("note", "재고자산")` |
| network | 네트워크 | DART | `dartlab.scan("network")` |
| cashflow | 현금흐름 | financial | `dartlab.scan("cashflow")` |
| audit | 감사리스크 | DART | `dartlab.scan("audit")` |
| insider | 내부자지분 | DART | `dartlab.scan("insider")` |
| quality | 이익의 질 | financial | `dartlab.scan("quality")` |
| liquidity | 유동성 | financial | `dartlab.scan("liquidity")` |
| growth | 성장성 | financial | `dartlab.scan("growth")` |
| profitability | 수익성 | financial | `dartlab.scan("profitability")` |
| efficiency | 효율성 | financial | `dartlab.scan("efficiency")` |
| valuation | 밸류에이션 | financial | `dartlab.scan("valuation")` |
| dividendTrend | 배당추이 | financial | `dartlab.scan("dividendTrend")` |
| macroBeta | 거시베타 | DART | `dartlab.scan("macroBeta")` |
| fields | 필드카탈로그 | DART | `dartlab.scan("fields", "roe")` |
| screen | 스크리닝 | DART | `dartlab.scan("screen", "value")` |
| disclosureRisk | 공시리스크 | DART | `dartlab.scan("disclosureRisk")` |
| orders | 신규수주 | DART | `dartlab.scan("orders")` |
| ipo | 신규상장 | DART | `dartlab.scan("ipo")` |
| salesByProduct | 사업부문 매출구성 | DART | `dartlab.scan("salesByProduct")` |
| narrativeMetric | 서술표 지표 | DART | `dartlab.scan("narrativeMetric")` |

## 대표 반환 형태

가이드 호출은 DataFrame을 반환한다.

```text
dartlab.scan()
-> DataFrame
   axis, label, group, description, example, apiKey
```

축 실행도 대부분 DataFrame을 반환한다. 축마다 세부 컬럼은 다르지만 후보 발굴 답변에는 최소 다음 성격의 필드가 있어야 한다.

```text
stockCode/ticker, corpName/name, market/universe, latestAsOf/asOf,
metric/value/score, rank, basis/source, flags
```

`screen`은 조건식과 통과 여부, `account`/`ratio`는 계정명 또는 ratio id, 기간별 값, 기준일을 포함해야 한다. ranking/filter 결과를 말할 때는 원값과 rank를 함께 제시한다.

## axis-specific 회피 (회귀 가드)

각 axis 의 sub-spec 본문은 base SKILL.md 의 axis 표에 흡수됨 (2026-05-18 Phase C-2 정리). standalone 유지: `engines.scan.undervaluedQuality` · `crossSectionStockScreen` · `krxIndexStrength` (preset spec / cross-section recipe).

| axis | axis-specific 회피 |
| --- | --- |
| account | snake_id 임의 추측 X (scanAccountList 또는 normalizeColumn 으로 정확 매칭); 단일 계정 (매출액만) 으로 비율 추정 X (비율은 ratio axis) |
| audit | 감사의견 (한정/거절/부적정) 만으로 *분식* 단정 X; 감사인 변경과 *지배구조 위험* 단순 인과 X |
| capital | 자사주 매입 vs 소각 동치 처리 X; 유상증자 빈도와 *위험* 단순 인과 X (사용처 capex/부채상환 확인) |
| cashflow | 8 종 현금흐름 패턴 분류 (Healthy/Growing/Distressed/Mature/...) 명시 없이 *위험* 단정 X; capex 음수 vs 양수 의미 회사별 다름 — 부호 임의 해석 X |
| debt | 부채비율 단일 metric 으로 *위험* 단정 X (ICR + OCF/부채 교차); 사채 1 년 만기 비중 무시 X |
| disclosureRisk | 공시 변화 신호와 확정 사실 혼동 X; 단일 신호로 *위험* 단정 X (5+ 신호 종합) |
| orders | book-to-bill 상위 그대로 추천 X (micro-cap 잡음 — 매출 규모·계약건수 필터 필수); momentum 극단치(직전TTM 0 근처)를 추세 단정 X; amountSuspect 값 신뢰 X (값-정합 위반) |
| ipo | `[발행조건확정]` 을 6 섹션 기대 X (CORRECTION doc, FULL 신고서를 봐야); chainOk/financialsOk False 발행사 값 신뢰 X (항등식 위반); 적용 PER 를 절대 고/저평가로 단정 X (발행사 선택 비교군 기준) |
| salesByProduct | read-time panel 파싱 X (prebuild consolidation SSOT); 부문 절대매출 비교 X (단위-불변 mix 지표만: 비중·HHI·다각화등급) |
| narrativeMetric | 사업보고서 서술 표에서 뽑은 수주잔고·가동률을 감사받은 재무수치와 동급 취급 X (비표준 서술 항목); 저신뢰(confidence 낮음)·부재 지표를 값으로 인용 X (정직 gap 그대로 표기) |
| dividendTrend | 5 패턴 (연속증가/안정/감소/시작/중단) 명시 없이 단정 X; 배당 지속가능성 검증 없이 추세만 인용 X |
| efficiency | 자산회전 / 재고회전 / 매출채권회전 분류 명시; CCC 분리 식 (DSO + DIO - DPO) 명시 |
| fields | 필드 카탈로그 결과를 *데이터 자체* 로 인용 X (메타데이터); finance/report/docs/krx 4 source 분리 명시 |
| governance | 최대주주 지분율만으로 *경영권 안정* 단정 X; 사외이사 비율을 산업 평균 비교 없이 답변 X |
| growth | 6 종 패턴 (Acceleration/Steady/Deceleration/Cyclical/Recovery/Decline) 명시 없이 *고성장* 단정 X; 단일 분기 YoY 로 성장 단정 X (4 분기 평균 또는 CAGR); 사이클 회사 cycle peak/trough 영향 미고려 X |
| insider | 임원 거래를 매수=긍정 / 매도=부정 단순 신호 X; 자사주 보유와 임원 개인 거래 혼동 X |
| liquidity | 금융사 (은행·보험) 에 일반 유동비율 적용 X (LCR · NSFR 별도); 유동비율 단일 metric 으로 단정 X (당좌비율 + 사채만기 교차) |
| macroBeta | 회귀 추정 기간 명시; p-value 낮은 베타를 결론에 사용 X |
| network | 출자 사슬 단계 명시; 계열사 내부거래 비중 무시한 *독립* 회사 답변 X |
| note | 노트 항목 절대금액 cross-company 비교 X (단위·통화 이질, 항목/기간 비율·추세로); `account`(정규화명)로 회사 간 동일 항목 join (label 은 회사별 표기차); 다축 matrix 주석(세그먼트·특수관계자)은 대상 아님 (단일축 lineitem 만); value 는 raw, `valueNum` 파생으로 스크리닝 |
| profitability | 산업 분기 무시한 통합 랭킹 X (제조 vs 금융 ROE 직접 비교); 결손 종목 (재무제표 미공시) 을 0 으로 채워 랭킹 하단 배치 X |
| quality | accrual ratio 임계값 (산업 평균 대비) 명시; 단일 분기 OCF/NI 로 이익품질 단정 X (4 분기 평균) |
| ratio | 비율 정의 (분자/분모) 명시; 산업별 비율 차이 무시한 통합 랭킹 X |
| screen | 멀티팩터 spec 의 가중치 / 임계값 명시; preset 결과를 *맞춤형* 으로 단정 X; `spec.define` 로 계정간 파생(순현금·ICR 등, 폐쇄 vocabulary add/sub/mul/div, 단위 인식) + 시계열(mean/min/max/yoy/cagr/slope 연간 격자) + 상대(percentile/zscore, `by:"industry"` 업종 횡단) 표현 가능, `@name` 은 define 선언 후 참조; 파생 필드가 희소계정(interest_expenses 등) 기반이면 유니버스 축소 인지; note lineitem 은 `note.<concept>@<항목명>` 주소 |
| valuation | 단일 멀티플 (PER 만) 로 *저평가* 단정 X (PBR/PSR 교차 검증); 적자 회사에 PER 적용 X (PSR/EV-Sales 권장); 산업 분기 무시 통합 PER 랭킹 X |
| workforce | 직원수 / 평균급여 / 인건비율 분류 명시; CEO/임원 보수와 평균 직원 보수 동치 처리 X |

**공통 forbidden** (모든 axis): universe/필터/계산식/기준일 명시 없이 후보 발굴 X · 결손값을 0 으로 대체 X · 단일 기업 심층 해석을 scan 으로 X (analysis/credit/quant 후속).

## evidence 기준

후보 발굴 결과에는 `universe`, `datasetAsOf`, `filter`, `formula`, `table`, `executionRef`가 필요하다. 최종 답변은 회사명만 나열하지 말고 evidence table을 포함한다.

## EngineCall (agent 경로) args 매핑

agent (ai/mcp/server) 가 본 엔진을 호출할 때는 `EngineCall(apiRef="scan", args={...})` 양식. dartlab.scan() 의 positional 인자를 args dict 의 key 로 변환:

| `dartlab.scan(...)` | `EngineCall(apiRef="scan", args=...)` |
| --- | --- |
| `dartlab.scan("growth")` | `{"axis": "growth"}` |
| `dartlab.scan("account", "매출액")` | `{"axis": "account", "target": "매출액"}` |
| `dartlab.scan("ratio", "roe")` | `{"axis": "ratio", "target": "roe"}` |
| `dartlab.scan("screen", "value")` | `{"axis": "screen", "target": "value"}` |
| `dartlab.scan("screen", spec={"filters": [...]})` | `{"axis": "screen", "spec": {"filters": [...]}}` |

**guard** — axis 와 target 을 점 표기로 합쳐 `apiRef="scan.ratio.roe"` 호출 금지 (`unknown_api_ref` 차단). args 안에 분리.

## 산업/섹터 질문 ("반도체 어때?" 류) 처리

"반도체", "2 차전지", "자동차" 같은 산업 keyword 가 질문에 있으면:

1. **industry 엔진 우선** — `dartlab.industry("반도체")` 또는 `c.industry()` 가 산업 라이프사이클 단계 (도입·성장·성숙·재도약·쇠퇴) + 밸류체인 노드 + 동종 종목 list 반환.
2. **scan 으로 횡단면 비교** — 같은 industryHint 안에서 `dartlab.scan(axis, universe={"industryHint": "반도체"})` 또는 결과 DataFrame 의 `industryName` 컬럼 필터.
3. 답변에는 산업 라이프사이클 단계 + 공정/세부 분류 (전공정 FAB · 후공정 패키징 · 테스트 · 설계 · 소재 · 장비) 별 ranking 둘 다.

단일 종목 답변에 부착되는 `industryBadge` (Company.panel 응답) 는 같은 산업 종목 peers list 를 자동 포함 — 별도 industry 호출 없이 peer 후보 즉시 사용 가능.

## universe default

- `universe` 미지정 → KR 전종목 (KOSPI + KOSDAQ + KONEX 등 dartlab 수집 범위).
- 미국 시장 한정 질문이면 `universe="US"` 또는 `market="US"`.
- 산업 한정 → `universe={"industryHint": "반도체"}`.
- 사용자 지정 종목 list → `universe={"stockCodes": ["005930", "000660"]}`.

기준일 (`datasetAsOf`) 은 결과 DataFrame 의 컬럼으로 반환. 답변에 그대로 인용 — 데이터 freshness 명시.

## 기본 실행 순서

1. 질문이 후보 발굴인지 단일 기업 분석인지 산업 횡단인지 구분.
2. 후보 발굴이면 `dartlab.scan()`으로 axis 확인.
3. primitive (`account`/`ratio`) vs preset (`screen`) vs financial axis (`growth`/`profitability`/`quality`/...) 선택.
4. `dartlab.scan(axis, target/spec)` 또는 `EngineCall(apiRef="scan", args={"axis": ..., "target": ...})` 호출.
5. 기준일, 유니버스, 필터, 계산식, rank 검산.
6. 상위 후보는 `Company(...).analysis()`, `credit`, `quant` 로 심층 검증.

## 기본 검증

스킬은 공개 실행 문서다. `dartlab.scan()`의 guide 축, 공개 호출, 대표 반환 컬럼이 바뀌면 이 파일과 관련 응용 스킬을 같은 변경에서 갱신한다.


---

# 흡수된 sub-spec 본문 (Phase D, 2026-05-18)

## (흡수) engines.scan.crossSectionStockScreen 본문

## 절차

- RuntimeDatasetCatalog에서 KRX 가격 또는 종목 데이터셋 후보를 찾는다.
- `InspectDataset`으로 종목코드, 종목명, 날짜, 가격/거래대금/등락률 컬럼을 확인한다.
- `RunPython`으로 동일 기준의 횡단면 ranking 표를 만든다. 표에는 종목 식별자, 종목명, 기준일, 비교 시작일 또는 기간, ranking metric, rank가 있어야 한다.
- ranking 또는 “찾아줘” 유형의 결과는 답변 prose보다 table ref와 필요 시 CSV artifact가 우선이다. 산출물 ref가 없으면 후보 발굴을 완료한 것으로 보지 않는다.
- 최종 답변 본문에는 입력/유니버스, 필터, 계산식/지표, 결과 섹션을 두고 markdown evidence table을 렌더링한다.
- 상위 N개 숫자 claim은 ranking table/value ref에 직접 묶고, 기준일·기간·universe·metric을 답변에 함께 밝힌다.
- 후보 표가 2개 이상이고 동일 metric이 있으면 compile_visual로 요약 차트를 만들 수 있지만, chart는 table ref 이후에만 만든다.

## 공개 호출 방식

- `dartlab.scan()`
- `dartlab.scan("fields")`
- `dartlab.scan("ratio", universe="KR")`
- `dartlab.scan("account", account="revenue")`

## 호출 동작

- 시장/유니버스 횡단면에서 필터, 순위, peer 위치를 계산한다. 단일 종목 원자료 확인은 Company가 우선이다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- ranking/filter DataFrame을 반환한다. 핵심 컬럼은 universe, asOf/latestAsOf, stockCode/ticker, name, metric, value, rank, basis다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.

## (흡수) engines.scan.krxIndexStrength 본문

## 절차

- RuntimeDatasetCatalog에서 KRX 지수 데이터셋 후보를 찾는다.
- `InspectDataset`으로 날짜 컬럼, 지수명 컬럼, 가격/등락률 컬럼, 최신 관측일을 확인한다.
- `RunPython`으로 최신일 기준 비교 가능한 지수별 수익률 또는 등락률 표를 계산한다.
- 강세 판단은 기준일, 기간, universe, metric이 모두 있는 표를 근거로 제한한다.
- visual은 지수별 비교 표가 있을 때만 만든다.

## 공개 호출 방식

- `dartlab.scan()`
- `dartlab.scan("fields")`
- `dartlab.scan("ratio", universe="KR")`
- `dartlab.scan("account", account="revenue")`

## 호출 동작

- 시장/유니버스 횡단면에서 필터, 순위, peer 위치를 계산한다. 단일 종목 원자료 확인은 Company가 우선이다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- ranking/filter DataFrame을 반환한다. 핵심 컬럼은 universe, asOf/latestAsOf, stockCode/ticker, name, metric, value, rank, basis다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.

## (흡수) engines.scan.undervaluedQuality 본문

## 절차

- `engines.scan` 기본 skill로 가능한 횡단면 축을 확인한다.
- valuation metric과 profitability metric이 같은 universe와 기준일에서 있는지 확인한다.
- `RunPython`으로 후보 표를 만들고 value metric만 아니라 profitability 보조 지표를 같이 둔다.
- 최종 답변은 입력/유니버스, 필터, 계산식/지표, 결과를 명시하고 후보별 valuation/profitability evidence table을 본문에 렌더링한다.
- 낮은 valuation은 후보 조건이지 최종 투자 판단이 아니라고 한계를 남긴다.

## 공개 호출 방식

- `dartlab.scan()`
- `dartlab.scan("fields")`
- `dartlab.scan("ratio", universe="KR")`
- `dartlab.scan("account", account="revenue")`

## 호출 동작

- 시장/유니버스 횡단면에서 필터, 순위, peer 위치를 계산한다. 단일 종목 원자료 확인은 Company가 우선이다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- ranking/filter DataFrame을 반환한다. 핵심 컬럼은 universe, asOf/latestAsOf, stockCode/ticker, name, metric, value, rank, basis다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.
