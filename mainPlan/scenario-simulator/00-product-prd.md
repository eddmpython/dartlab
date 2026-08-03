# 00. 경제·사업·손익·주가 시나리오 시뮬레이터 PRD

상태: 비전 PRD (v0.2 정정 헤더 부착 — 본문은 v0.1 비전, 아래 정정이 정본)
범위: 과거 분석, 미래 가정, 중첩 if 시나리오, 매출·손익·DCF·주가 민감도 시뮬레이션

> **★v0.2 정정(2026-06-13) + v0.3 구현 정합(2026-06-14) — 본문 v0.1 용어보다 우선:**
> - **제품명 = `simulate`**(verb `dartlab.simulate(code, *, scenario, horizon, asOf)`, 결정론 코어 졸업 `ac3905fd9`). 본문의 "Scenario Workbench"·"제품명 후보 3종"·§9 Phase 8 "workbench로 묶는다"는 *옛 후보·옛 Phase 서술* — 01 §3이 `simulate`로 확정(`scenario` 명사형 기각). 본문 §9 Phase 0~8은 v0.1 비전 순서지 현 구현 시퀀스(04 §4·07)가 아니다.
> - **엔진 거처 = L2.5 독립 묶음 `simulate/`**(story 동급 L3 아님, 신규 L2 아님 — 01 §3). 본문 §7.2 "L2 엔진 간 직접 import 금지"는 유효하나, simulate는 L2.5라 analysis+macro+quant 동시 결합 합법(§7.2 #9 본문 이미 반영).
> - **중심 산출물 = Play 미래 리플레이**(05). **가치평가(08)·신용(09 §4)은 simulate(mode) 뷰** — 같은 `SimulationResult`의 다른 읽기. 단일 목표가·rating 금지(reverseDCF 닻+조건부 범위). §5 주요 산출물(Environment/Assumption/Bridge/Price)은 이 단면의 화면 표면이다.
> - **★KR 전용(구현 현실 — 비전 범위):** 현 verb는 `market != "KR"`면 `ValueError`(US ticker → EDGAR, 매크로 프리셋이 KR 기준). 본문 §2 비전("경제·시장 환경")이 시사하는 cross-market 도달은 **US 프리셋·US elasticity가 없어 아직 구조적으로 KR-only**다. US 해제는 07 로드맵에 명시 phase로 두기 전까지 비전 주장이지 가용 기능 아님(01 §3·§9).
> - 현재/과거 차트 3 컴포넌트(지수·이벤트레일·백테스팅)는 현재 UI surface가 소유한다. 07은 그 surface와 시뮬레이션의 단방향 시퀀싱 브리지다. 전체 정합화와 부채 원장은 09, 현재 상태와 다음 작업은 04에 둔다.

---

## 1. 판정

요청은 명확하고 타당하다.

DartLab에는 이미 공시, 재무제표, 뉴스, 거시, 퀀트, 밸류에이션, 스토리 조합 자산이 있다. 다음 단계는 이 자산을 단순 보고서로 끝내지 않고, "과거에는 어떤 조건에서 어떤 변화가 실제로 발생했는가"와 "미래에 여러 조건이 겹치면 매출, 이익, 가치평가, 가격 범위가 어떻게 움직일 수 있는가"를 하나의 조건부 시뮬레이션 절차로 묶는 것이다.

단, 제품 표현은 엄격해야 한다. 이 기능은 매수·매도 추천, 단정적 주가 예측, 검증된 전략 생성기가 아니다. 결과는 항상 `조건`, `증거`, `가정`, `반증 조건`, `민감도 범위`로 제시한다.

---

## 2. 제품 비전

사용자는 종목을 보며 이런 질문을 한다.

1. 지금 경제와 시장 환경은 이 회사에 유리한가, 불리한가.
2. 공시, 뉴스, 지표 변화가 실제 사업 driver 중 어디에 닿는가.
3. 그 변화가 매출, 비용, 영업이익, 순이익, FCF로 얼마나 전파될 수 있는가.
4. 손익 변화가 밸류에이션과 주가 범위에 어떤 민감도를 만드는가.
5. 과거의 유사한 환경에서는 비슷한 가정이 얼마나 맞았고 어디서 틀렸는가.
6. 여러 if가 겹칠 때 가장 취약한 가정은 무엇인가.

`simulate`(시뮬레이터, verb `dartlab.simulate` — v0.2 확정)의 비전은 이 질문을 한 화면에서 다루는 것이다. 핵심 경험은 "뉴스를 읽고 감으로 판단"하는 것이 아니라, 이벤트를 사업 driver에 연결하고, driver를 손익과 가치평가로 전파하며, 마지막에 가격 민감도와 반증 조건을 동시에 확인하는 것이다.

---

## 3. 제품 원칙

1. 조건부 시뮬레이터다.  
   결과 문장은 `이렇게 된다면`으로 시작해야 한다. `앞으로 오른다`, `검증됐다`, `추천한다`는 제품 언어에서 금지한다.

2. 모든 숫자는 ref에 닿아야 한다.  
   재무제표 숫자, 가격, 지표, 날짜, 공시, 뉴스, 실행 결과는 `tableRef`, `valueRef`, `dateRef`, `webRef`, `executionRef`, `artifactRef`, `verifyRef` 중 하나 이상으로 추적 가능해야 한다.

3. 과거 replay와 미래 what-if를 섞지 않는다.  
   과거 replay는 해당 시점에 알 수 있었던 데이터만 사용한다. 미래 what-if는 현재 `asOf`와 사용자가 명시한 가정을 분리해 표시한다.

4. 결손을 0으로 대체하지 않는다.  
   결손은 `missing`, `blocked`, `partial`, `notApplicable`로 남긴다. 결손을 0으로 바꾸면 시뮬레이션이 아니라 오염된 계산이다.

5. AI는 판단 보조자이지 원천 데이터가 아니다.  
   AI는 가정 비판, 누락 탐색, 반대 시나리오, 설명 조립을 맡는다. AI가 만든 숫자는 공식 fact가 아니다.

6. 스토리와 숫자는 양방향으로 검증한다.  
   스토리가 좋으면 driver가 있어야 하고, driver가 있으면 손익과 현금흐름이 닫혀야 한다. 손익이 좋아도 현금흐름이 따라오지 않으면 flag가 올라간다.

7. 단일 base case를 금지한다.  
   최소 `bear`, `base`, `bull` 또는 `downside`, `neutral`, `upside`가 있어야 한다. 하나의 목표주가만 보여주는 화면은 만들지 않는다.

---

## 4. 핵심 사용자 흐름

### 4.1 종목에서 시작

1. 사용자가 종목을 선택한다.
2. 시스템이 `Company.panel`로 IS, BS, CF, CIS, ratios를 고정한다.
3. `Company.disclosure`, `search`, `gather.news`, `gather.macro`, `gather.price`, `industry`, `quant.marketContext`를 통해 현재 환경 snapshot을 만든다.
4. 화면은 현재 결론을 바로 말하지 않고 "시뮬레이션 가능한 driver"와 "아직 근거가 부족한 driver"를 나눈다.

### 4.2 이벤트에서 시작

1. 사용자가 뉴스, 공시, 경제지표, 원자재 가격, 환율, 금리, 수출입 지표 중 하나를 선택한다.
2. 시스템은 이벤트를 `BusinessChangeEvent`로 정규화한다.
3. 이벤트가 닿을 수 있는 driver를 제안한다.
   - 매출: 물량, 가격, mix, 환율, 세그먼트, 지역, 고객, backlog.
   - 비용: 원재료, 인건비, 물류, 감가상각, R&D, 판관비, 고정비 흡수.
   - 투자/운전자본: capex, 재고, 매출채권, 매입채무.
   - 할인율/멀티플: 금리, ERP, beta, credit spread, peer multiple.
4. 사용자는 driver별 delta, 기간, 확률 정책, 반증 조건을 입력하거나 AI 제안을 검토한다.

### 4.3 과거 replay

1. 사용자가 과거 날짜와 이벤트를 선택한다.
2. 시스템은 `decisionAt` 기준으로 당시 알 수 있었던 데이터만 재구성한다.
3. 그 시점에서 만든 가정을 실제 후속 실적, 가격, factor, macro 결과와 비교한다.
4. 결과는 적중/실패보다 "어떤 가정이 틀렸는가"를 중심으로 보여준다.

### 4.4 미래 what-if

1. 사용자가 중첩 조건을 만든다.
   - 예: 환율 +8%, 수출 물량 -5%, ASP +3%, 원재료 -7%, 금리 -50bp, peer multiple -10%.
2. 시스템은 각 조건의 적용 기간, 신뢰도, 독립성, 중복 가능성을 확인한다.
3. 손익과 FCF를 만들고, DCF/상대가치/reverse DCF를 함께 산출한다.
4. 최종 화면은 가격 범위, bridge, 민감도, 반증 조건, AI 전문가 의견을 함께 보여준다.

---

## 5. 주요 산출물

### 5.1 Environment Snapshot

현재 또는 과거 `asOf` 시점의 환경 요약이다.

- macro regime: expansion, slowdown, contraction, recovery, crisis.
- rates, FX, inflation, liquidity, credit spread, commodity.
- market index, sector index, factor returns, flow.
- 뉴스 압력: source breadth, velocity, firstSeenAt, event type, disclosure alignment.
- 회사 상태: latest financial period, margin, cash conversion, leverage, valuation band.

### 5.2 Assumption Ledger

모든 가정의 장부다.

- 가정 문장.
- 영향을 받는 driver.
- base value와 scenario value.
- 범위와 분포.
- 근거 ref.
- 반증 조건.
- 상태: fact, estimate, hypothesis, missing.
- 마지막 확인일.

### 5.3 Business Driver Bridge

이벤트가 사업 driver로 전파되는 표다.

- 물량 증가율.
- 가격 변화율.
- mix 변화.
- 환율 pass-through.
- 수주잔고 매출 전환률.
- 생산능력 또는 공급 제약.
- 고객/지역/제품 세그먼트 노출.
- 원재료, 물류, 인건비, R&D, 감가상각 driver.

### 5.4 Profit Bridge

driver가 손익계산서로 전파되는 표다.

- revenue.
- gross profit.
- operating income.
- net income.
- EPS.
- CFO, capex, FCF.
- margin bps 변화.
- one-off와 recurring 분리.
- working capital 압력.

> **★시각 문법 포인터(R8, 2026-06-20):** 시각 인코딩·바 문법(waterfall 바 누적·증감 색·결손 구간 끊김) = 08 §3.2 Bridge Waterfall 시각 명세(businessDriverBridgeBlock·profitBridgeBlock 렌더러) + 05 시각 인코딩 SSOT(미래 구간 점선·fan band σ provenance 실선/점선 가르기, 05 §3 시각 가드) 준수. 본 절은 *내용 표면*, 시각 규율은 그 두 SSOT 가 정본(중복 정의 금지).

### 5.5 Valuation Bridge

손익과 현금흐름이 가치평가로 전파되는 표다.

- FCFF DCF.
- relative valuation.
- residual income 또는 reverse DCF.
- WACC, beta, ERP, terminal growth.
- sales-to-capital, ROC, reinvestment rate.
- terminal value share.
- current price가 요구하는 implied growth, margin, ROC.

### 5.6 Price Simulation

가격 결과는 단일 목표가가 아니라 range와 bridge로 표현한다.

- P10/P50/P90 또는 bear/base/bull.
- fundamental bridge.
- factor/macro bridge.
- event shock bridge.
- overlap penalty.
- sensitivity grid.
- tripwire.
- result status: usable, usableWithGaps, blocked.

---

## 6. 화면 구성

> **★v0.4 화면 토폴로지 정정** — 아래 6.1~6.5 는 v0.1 비전 레이아웃이다(별도 워크벤치 화면 신설 0). 확정 거처 = **기존 터미널**(`ui/packages/surfaces/src/terminal/`). 각 pane 은 신설이 아니라 기존 표면 흡수: §6.1 Scenario Tree·§6.2 Assumption Ledger → 차트-스코프 인셋 + `if` 토글(05 §4); §6.3 Bridge Waterfall·§6.5 AI Expert Panel → ReportDock 탭(08 §3.2·§5, valuation 단일 모드로 시작); §6.4 Replay → PriceChart sim/Play 모드(05 §1·§8); Backtest → ReportDock backtest 모드(10, 엔진 졸업 시 추가 = 08 §5 deferred). **별도 셸·라우트·둘째 차트 인스턴스 0.** 정본 = 06 §0·§5 / 05 §8 / 08 §5. 06·05 의 "새 패널·차트 인스턴스 0" 규율이 본 절 레이아웃보다 우선. **★레이아웃 와이어프레임 포인터(R4, 2026-06-20):** 본 절 6.1~6.5 의 ASCII/프로즈 배치는 *비전 스케치*다 — 실재 컴포넌트 1:1 ASCII 와이어프레임의 정본은 **05 레이아웃 와이어프레임 SSOT**(Play 미래 리플레이의 실재 PriceChart·ReportDock·차트-스코프 인셋 토폴로지 = `ui/packages/surfaces/src/terminal/` 실제 컴포넌트 매핑)다. 본 절과 어긋나면 05 가 정본(코드-그라운드 토폴로지 우선).

### 6.1 Scenario Tree

좌측에는 scenario tree를 둔다.

- Base case.
- Macro branch.
- Business branch.
- Event branch.
- Valuation branch.
- Combined branch.

branch는 중첩 가능하지만 각 branch는 독립 가정과 공통 가정을 구분해야 한다. 같은 환율 가정을 두 번 반영하면 `overlapWarning`을 표시한다.

### 6.2 Assumption Ledger Table

중앙에는 가정 장부를 둔다.

필수 컬럼:

- assumptionId.
- category.
- claim.
- base value.
- scenario value.
- range.
- affected driver.
- evidence.
- status.
- falsifier.
- owner lens.

### 6.3 Bridge Waterfall

오른쪽 또는 상세 탭에는 bridge를 둔다.

1. 매출 bridge.
2. 영업이익 bridge.
3. FCF bridge.
4. valuation bridge.
5. price bridge.

각 bridge는 "전 단계 값", "driver 변화", "효과", "근거", "flag"를 보여준다.

> **★시각 문법 포인터(R8, 2026-06-20):** 시각 인코딩·바 문법 = 08 §3.2 Bridge Waterfall 시각 명세 + 05 시각 인코딩 SSOT 준수(§5.4 동일 — waterfall 바·증감 색·결손 끊김·미래 점선의 단일 정의처는 그 두 문서). 본 절은 배치만 기술.

### 6.4 Backtest and Replay Panel

과거 검증 탭은 다음을 보여준다.

- runSpec.
- train/test 기간.
- benchmark.
- fee/slippage.
- vintage status.
- hit/miss가 아니라 assumption error.
- realized revenue/profit/price.
- factor attribution.
- data snooping 경고.

**★ScreenerModal → PriceChart 드릴다운 동선(R23, 2026-06-20 — "경량 근사(스크린) → 정밀(딥다이브)" 단방향).** 통합 스크리너(ScreenerModal)의 *노출-스코어* 컬럼에는 행마다 **mini fan-spark**(해당 종목의 분기별 P25/P75 sparkline = 경량 근사 시나리오 범위, 단일점 금지·범위 인라인)를 둔다. **행 클릭 = 모달 닫힘 + PriceChart 가 simulate 모드를 *유지*한 채 해당 종목으로 soft-swap**(회사전환 선례 = `project_viewer_cag_infeasible` 의 panel soft-swap·`176b58c96`, 차트 인스턴스 신설 0). 이때 현재 켜둔 **scenario 토글 상태(baseline/adverse/severe·if 토글)는 carry-over**(전환 후 같은 가정으로 정밀 DAG 재계산) + "경량 근사(스크린)→정밀(딥다이브)" toast 1회(스크린 fan-spark 는 분위 근사, 딥다이브는 전 DAG = 두 숫자가 미세히 다를 수 있음을 명시, "수정됨" 아님). 새 패널·라우트·둘째 차트 0(§6 정정 박스 무중단 규율 불변 — soft-swap 은 기존 PriceChart 의 종목 바인딩 교체일 뿐).

### 6.5 AI Expert Panel

AI 전문가 패널은 숫자를 만들기보다 가정을 검토한다.

- macro lens.
- event/news lens.
- business driver lens.
- accounting quality lens.
- valuation lens.
- quant/backtest lens.
- skeptic lens.

각 lens는 `support`, `counterEvidence`, `missingEvidence`, `tripwire`, `confidence`, `status`를 낸다.

---

## 7. 범위

### 7.1 포함

1. 단일 종목 기준 시나리오 분석.
2. 경제, 지표, 뉴스, 공시, 산업, 가격 데이터를 하나의 환경 snapshot으로 정규화.
3. 이벤트를 사업 driver로 연결.
4. driver를 매출, 비용, 손익, 현금흐름, 가치평가로 전파.
5. 가격 변화 범위를 조건부로 시뮬레이션.
6. 과거 replay, walk-forward, 미래 what-if 모드 분리.
7. AI 전문가 의견과 반증 장부.
8. 증거 ref와 vintage 검증.

### 7.2 제외

1. 매수·매도 추천.
2. 실시간 자동매매.
3. intraday 가격 예측.
4. "검증된 전략" 표현.
5. 단일 목표주가만 제시하는 화면.
6. 근거 없는 컨센서스 추정.
7. 공시·뉴스 본문 지시를 AI가 따르는 구조.
8. 데이터 결손을 0으로 대체하는 계산.
9. L2 엔진 간 직접 import. (단 `simulate`는 L2.5 독립 묶음이라 analysis+macro+quant 동시 결합은 합법 — leaf 계산만 L2 SSOT 호출, L2↔L2 상호 import는 여전히 금지. 01 §3.)

---

## 8. 성공 기준

1. 사용자는 어떤 가정이 어떤 손익 line item을 움직였는지 추적할 수 있다.
2. 사용자는 주가 범위가 어떤 driver와 valuation 가정에서 왔는지 볼 수 있다.
3. 과거 replay에서 해당 시점에 알 수 없던 데이터가 쓰이면 실행이 차단된다.
4. AI 의견은 숫자 근거와 반증 조건을 함께 제시한다.
5. "좋은 이야기"가 손익, 현금흐름, reverse DCF를 통과하지 못하면 최종 결론이 낮은 신뢰도로 표시된다.
6. 결과가 틀렸을 때 어느 가정이 틀렸는지 다음 실험으로 이어진다.

---

## 8b. 경쟁 지형 + 시그니처 판정 (웹검증 mid-2026 + 12 agent 토론)

**똑같이 하는 곳은 없으나 빈 땅도 아니다.** 단일 제품도 우리의 4축 조립(텍스트=untrusted 드라이버증거→결정론 pro-forma + det/ai 평행경합+Brier + forward-replay + reverseDCF 닻)을 다 하지 않는다. 그러나 *부품*은 전부 실재 제품에 있고 특히 **숫자+비정형 융합은 이미 commodity**(AlphaSense·BloombergGPT·RavenPack)다 — 따라서 **차별은 "기술"이 아니라 "조립 + 규율"**이다.

가장 가까운 6 실서비스와 결정적 갭(각자 *다른 축*에서만 가까움):

| 서비스 | 가까운 축 | 결정적 갭 |
|---|---|---|
| Bloomberg MAC3/MARS + BloombergGPT | 드라이버-DAG 충격 전파 | 포트폴리오 팩터 재평가지 회사 pro-forma 아님·순간 재평가지 시간 replay 아님·NLP와 시나리오 엔진 별개 |
| Moody's Scenario Studio | 결정론 드라이버→pro-forma 척추 | 거시→신용/은행 층(주식-기업 아님)·horizon 투영이지 replay 아님 |
| AlphaSense Financial Data(2025-10) | 숫자+비정형 융합(최강) | AI가 곧 답(블렌딩)·드라이버-DAG/replay/경합 없음 |
| Causal / LucaNet | 드라이버-DAG + MC forward fan + 편집 레버 | 숫자 전용(텍스트0)·예산 FP&A지 주식 밸류에이션 아님 |
| FinChat.io / Fiscal.ai | 주식 밸류에이션 + 편집 DCF + AI 융합 | 단일점 DCF지 드라이버 캐스케이드 아님·AI 블렌딩·reverseDCF 척추 없음 |
| FinGPT-Forecaster | AI 예측을 벤치마크된 주장으로(에토스) | 경합할 결정론 척추 자체가 없음 |

**시그니처 판정 = `conditional-signature`(합의 61/100, KEEP 조건부).** 시그니처 한 문장 = *"텍스트=untrusted 드라이버증거 → 결정론 pro-forma 캐스케이드 → det/ai 평행(블렌딩 물리 불가) → 사후 Brier 채점, 이 4축 전체를 reverseDCF 닻 위에 얹어 '미래 성장률 얼마?'(추측)를 '시장이 박은 g/margin/ROIC가 plausible한가?'(판정)로 뒤집는 것 — 단 현재 절반이 설계지 증명이 아니다."*

- **가장 날카로운 wedge 3**: ① reverseDCF 닻을 시뮬레이터 *안에* 박은 것(컨센서스 부재=약점→priced-in 믿음 해부=강점, honesty spine과 wedge가 같은 메커니즘) ② 드라이버-DAG 충격을 회사 pro-forma 시간축까지 내림(MAC3가 못 닿는 자리, L2.5 앵커가 공짜 제공) ③ leaf-binding 앵커 + DriverRegistry의 유지보수 비대칭("데이터=카드 1줄, 코드 0" ↔ "엔진 계약 깨지면 CI red가 단일 노드 지목") = **anti-velocity 해자**(추가가 아니라 제약이라 경쟁자의 기능-출하 속도와 정반대 방향).
- **가장 큰 위협 3**: ① 텍스트/이벤트→driver 결정론 매핑 커버리지 미실증(메모리 segmentRnd 2/10·incomeExpense 66.9% 천장이 같은 데이터-부재 벽) ② 검증 루프 구조적 미완(`recordForecast`/`gate.py`/`ledger.py`/`admission.py`/`lens.py` 전부 src 부재) ③ 조립-속도 vs 규율-속도 역전(빠른 경쟁자가 4축 융합을 우리가 게이트를 다 짓기 전에 완성).
- **honest caution**: 9 흡수후보 중 5개가 이미 있거나 honesty 위반 = 토론이 발굴한 "새로움"의 절반은 환상. 융합은 commodity라 차별 못 되고, 차별을 강제하는 lint·게이트·admission이 *대부분 PRD 문구로만* 존재 → 규율이 기계 강제 안 되면 메모리가 반복 기록한 "확신오정렬"(horizonMeaning·accountStructDisambig: 검증 전 성공 주장)의 재현. **지금은 strong-signature가 아니라 "될 설계"다 — 새로움≠검증.**
- **KEEP 순서**: ① 규율 게이트 먼저(`test_simulate_leaf_binding`·`recordForecast` write-end은 코드 0줄~소량 → 조립보다 먼저 박아 anti-velocity 해자 실재화) ② 텍스트→driver 매핑 커버리지를 held-out으로 실측(design target→proven wedge 승격 단일 분기점) ③ A5(점확률)·A7(공개 리더보드) 정밀 외피는 write-end 라이브 전까지 defer/reject로 honesty spine 보호. **"미검증을 라벨하는 것이 가치지 우월 증명이 가치가 아니다"를 끝까지 지키는 조건에서만 KEEP.**

> 타사 개념 흡수(absorb-as-defer 4종 A1·A2·A4·A7 + reject 잔여 가드 A5·A6) 상세 = 02 §2.3·§2B.3 / 01 §4·§5b / 05 §4·§3 / 03 §9.3 / 04 §4(12·13). 전부 *새 기능 추가가 아니라 한계 라벨·defer-게이트*로만 흡수("깎아서 강함").

---

## 8c. ★시그니처 현실 점검 — 부정적 검토 (2026-06-20, 운영자 "억지로 넘기지 마라")

> 운영자 지시: *"억지로 넘게 하지 말고 전부 제대로 부정적 검토해라. 진짜 핵심은 DartLab의 시그니처가 될 수 있는가다."* — 이 절은 PRD-점수 상승을 시그니처 진전으로 오인하는 것을 차단하는 가드다. **결론을 먼저: 두 차례 전문가-패널 uplift(planScore 시각/분석/예측 66·79·82 → 95, 이후 16-분야 천장 추진)는 *설계 완전성*만 올렸고 시그니처 지위는 §8b의 `conditional-signature(61, 될 설계지 strong-signature 아님)`에서 1px도 움직이지 않았다.** planScore는 시그니처의 proxy가 아니다.

**1. planScore↑ ≠ 시그니처↑ (범주 오류 경계).** uplift가 닫은 것은 *문서가 재조사 없이 구현 가능한가*(planScore=설계완전성). 시그니처가 되려면 *빌드되고·실데이터로 증명되고·방어 가능*해야 한다. systemScore(실빌드)는 ~61(09 §10 fatal 4중 빌드티켓 중 1 완료) — 핵심 능력은 **아직 존재하지 않는다**(`gate.py`·`recordForecast` write-end·`mc.distribution` 노드·`ledger.py`·`lens.py`·렌더러 2개·ReportDock 전부 src 부재). 짓지 않은 건물의 완벽한 청사진은 건물이 아니다. *2 라운드의 PRD 정밀화는 필요조건이지 시그니처의 충분조건 근처도 아니다.*

**2. ★검증 못 한 천장 주장 철회.** 2차 천장 재평가(viz 99·분석 98·예측 98 도달 주장)는 세션 한도로 9 검증자 중 **1명만 실행**됐고, 그 1명(접근성)이 준 점수는 99가 아니라 **97 + 미해결 갭 3건**(SC 1.4.11 대비 기준배경 3중 드리프트로 게이트 거짓통과 가능·200% reflow AC 부재·08 waterfall a11y 포인터 의존)이었다. ⟹ **"천장 도달"은 증명된 적 없는 주장**이라 본 문서는 그것을 주장하지 않는다(확신오정렬 가드). 현 상태 = **설계 강건(~95-97, 일부 실측 미해결)·천장 미검증**.

**3. 부정적 검토 — 시그니처를 막는 3 구조 위협(PRD가 못 고치는 것):**
- **(A) 데이터-부재 벽 — 가장 깊은 부정.** 분석적으로 *구별되는* 단 하나의 움직임(텍스트/이벤트→business driver→P&L 캐스케이드)이 실측에서 약하고 *설계로 못 고친다*: segment 추출 2/10·incomeExpense 66.9% 천장·driver coverage는 대부분 섹터 단일 GDP/FX/rate 4-beta(02 §2C census가 이제 명시, 회사 고유 ≈0). "드라이버 캐스케이드"는 현실에서 *치장한 4-beta 선형맵*이다. 한국 공시 데이터가 대부분 기업의 미세 driver 분해를 *지지하지 않는다* — 이건 엔지니어링이 아니라 데이터의 벽이라 PRD 어떤 정밀화도 못 넘는다. **시그니처의 핵심 분석 움직임이 데이터에 막혀 있다.**
- **(B) 차별=규율, 능력 아님 (commodity 융합).** §8b 자인대로 4축 융합은 commodity(AlphaSense·BloombergGPT). 구별 wedge는 결국 *"우리는 불확실성에 규율 있다"*로 환원 — 이건 **가치관 포지션이지 해자가 아니다.** 자원 많은 경쟁자가 같은 규율을 채택할 수 있고, "범위 명시"는 마케팅이 어렵다(사용자는 답을 원하지 "목표가 안 드립니다 그 이유는"을 원하지 않는다). "가장 규율 있는 시나리오 도구"는 *원칙적 니치*지 넓은 시그니처가 아니다.
- **(C) 시그니처를 *증명할* 검증 루프가 정확히 미빌드·최난이도.** recordForecast write-end·models HF 배포·pooled-β admission·N분기 held-out 캘리브레이션 — 전부 다분기 실데이터 작업이고, 통과 전엔(Brier<0.25·calib MAE<0.1·skill>0 vs naive) "될 설계"다. 그리고 **실제로 돌리면 실패할 수 있다**(플랜 자인: "AI가 엔진보다 낫다는 *증명 대상*이지 전제 아님"; driver admission이 *어떤 driver도 게이트 통과 못 함*을 발견할 가능성 — factor-zoo 규율의 귀결).

**4. ★확신오정렬 트랩 — 내가 걸어 들어가던 길.** 플랜의 가장 깊은 반복 교훈은 `확신오정렬 > 정렬실패`(검증 전 성공 주장이 솔직한 실패 인정보다 나쁘다 — horizonMeaning §8·accountStructDisambig). 두 uplift 라운드는 *미빌드·미증명* 기능에 "95→98→99 거의완벽"을 표면화할 뻔했다. 운영자 "억지로 넘기지 마라"가 정확히 이걸 잡았다. 바른 수는 점수-주장을 멈추고: *설계는 강하다·시그니처는 미증명·간극은 BUILD+PROOF이며 어떤 패널도 그걸 못 닫는다.*

**5. 부정적 종합 — 시그니처가 될 수 있는가?**
- **조건부 YES, 단 PRD가 횡단 못 하는 좁은 경로로만.** 경로 = 최소 검증 척추 빌드 → 실 KR 기업에 N분기 가동 → reverseDCF-닻 위 캘리브레이션된·한계-경계된 시나리오 판정이 *실제로* well-calibrated·baseline-beating임을 실증. 이 경험적 결과가 *착지하면* "자기 한계를 실증하는 유일한 시나리오 도구"가 진짜 방어가능 시그니처가 될 수 있다(anti-velocity 해자 — 경쟁자가 속도 저하 때문에 복제 안 하는 규율).
- **그러나 셋 중 하나라도 죽일 수 있다**: (A) 데이터 벽이 driver coverage를 너무 낮춰 "캐스케이드"가 연극이 됨 / (B) 캘리브레이션·skill 게이트가 실데이터에서 *실패*(규율 엔진에 edge 없음) / (C) 범위-명시 프레임이 목표가-경쟁자 대비 너무 니치라 시장성 없음.
- **가장 가능성 높은 귀결**: 시뮬레이터는 *단일 시그니처*가 아니라 **강하고 방어가능한 *2차* 능력**(터미널의 "범위-경계된 시나리오 + reverseDCF 닻" 모드)이 된다. DartLab의 *실제* 시그니처는 이 한 분석엔진보다 **폭**(종목코드 하나 → DART·EDGAR 전체 구조화 스토리, 이미 가동 중인 본진)일 가능성이 높다.

**6. 권고(건설적).**
- PRD 점수를 시그니처 proxy로 쓰는 것 중단. 설계는 "강함/완전"에서 **동결**하고 패널-uplift 루프 중단 — 추가 패널은 시그니처 바늘을 못 움직이는 설계 숫자만 부풀린다.
- 성공 지표를 시그니처를 가르는 *유일한 것*으로 재정박: 최소 검증 척추(recordForecast + 단일 섹터 held-out 데모)를 *빌드*하고 — **어떤 driver가 admission을 통과하는가·fan이 캘리브레이션되는가**를 본다. 그 *하나의 경험적 결과*가 PRD 1000점보다 가치 있다.
- 범위-명시 원칙은 정체성으로 유지하되, 그것이 자동 시그니처가 아니라 *원칙적 니치*임을 현실로 받아들인다.

> 본 §8c 는 점수가 아니라 *진실*을 기록한다. 2026-06-20 두 uplift 라운드의 설계 산물(시각/분석/예측 절·a11y·규제관할·K-IFRS·tail risk 등)은 **플랜으로서 진짜 개선**이나 시그니처 판정은 §8b `conditional-signature(61)` 그대로다 — *빌드·증명되기 전까지.*

---

## 9. 단계별 제품 목표

### Phase 0. 비전 문서화

현재 단계다. PRD, architecture, simulation method, validation 문서를 만든다. 메인 메모리에는 경로만 남긴다.

### Phase 1. 데이터와 ref inventory

기존 `Company`, `gather`, `search`, `macro`, `analysis`, `quant`, `industry`, `story`, Damodaran recipe가 제공하는 field를 inventory한다.

완료 기준:

- 모든 후보 input field에 owner engine이 있다.
- `latestAsOf`, `source`, `provider`, `ref kind` 누락 목록이 있다.
- 결손을 0으로 대체하는 후보 경로가 표시된다.

### Phase 2. 계약과 장부 설계

`ScenarioSpec`, `RunSpec`, `VintageRef`, `AssumptionLedger`, `SimulationLedger`, `ExpertOpinionCard`를 설계한다.

완료 기준:

- historical replay와 future what-if가 같은 schema를 쓰되 mode가 분리된다.
- 각 row가 ref와 status를 가진다.
- branch 중첩과 overlap warning이 표현된다.

### Phase 3. 과거 replay 최소 실험

한 종목, 한 이벤트, 한 기간으로 replay를 만든다. 구현은 본진이 아니라 `tests/_attempts`에서 시작한다.

완료 기준:

- `decisionAt` 이후 데이터가 차단된다.
- t일 신호는 t+1 매매 가능 시점으로만 평가된다.
- 실제 결과와 assumption error가 저장된다.

### Phase 4. 손익 bridge

매출 driver, 비용 driver, working capital, capex, tax, share count가 손익과 FCF로 전파되는 bridge를 만든다.

완료 기준:

- 매출, 영업이익, 순이익, FCF가 시나리오별로 산출된다.
- 원재료/인건비/R&D/감가상각 등 비용성격 결손은 별도 flag로 남는다.
- CFO/NI, CFO/revenue, receivable growth minus revenue growth가 표시된다.

### Phase 5. valuation and price bridge

DCF, relative valuation, reverse DCF, factor/event return bridge를 통합한다.

완료 기준:

- terminal growth, WACC, terminal value share gate가 작동한다.
- 현재 가격이 요구하는 growth/margin/ROC가 보인다.
- 가격 결과는 P10/P50/P90 또는 bear/base/bull range로만 표시된다.

### Phase 6. walk-forward robustness

과거 여러 fold에서 가정 생성과 평가를 반복한다.

완료 기준:

- train/test 분리.
- fee/slippage/benchmark 기본 ON.
- DSR, PBO 또는 과최적화 경고.
- full-sample parameter selection 금지.

### Phase 7. AI 전문가 패널

AI lens가 같은 시나리오를 독립 검토한다.

완료 기준:

- 각 lens가 같은 input ref를 공유한다.
- 의견 불일치가 `DisagreementLedger`에 남는다.
- GATE 실패 시 최종 보고서가 차단되거나 `usableWithGaps`로 내려간다.

### Phase 8. 제품 화면

Scenario tree, assumption ledger, bridge waterfall, replay panel, AI expert panel을 **기존 터미널 차트(subject/sim 모드) + ReportDock 안에 통합**한다(별도 셸·워크벤치 화면 신설 없음 — §6 정정 박스·suite/01 §0).

완료 기준:

- 사용자에게 단일 예측값보다 가정과 범위가 먼저 보인다.
- 모든 숫자에 source drill-down이 있다.
- 반증 조건과 추적 지표가 남는다.
