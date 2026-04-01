# Analysis

회사는 스토리가 있다. 재무제표를 그 스토리의 구조화된 데이터로 변환한다.
숫자의 나열이 아니라, 인과로 연결된 서사가 분석의 목표다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `dartlab.analysis()`, `c.analysis()` |
| 소비 | Company(finance, docs, report), gather(price, macro) |
| 생산 | review, ai가 analysis 결과를 소비 |
| 축 | 14축 재무분석 + forecast + valuation, 6막 인과 구조 |

Company → Analysis → Review → AI 순서로 계층이 쌓인다.
analysis 품질이 올라가면 review와 AI 품질이 동시에 올라간다.

## 엔진 독립 규칙

- **analysis는 credit을 참조하지 않는다.** 신용평가 지표가 필요하면 analysis 자체 체계로 만든다.
- **credit도 analysis를 소비하지 않는다.** 재무 비율이 필요하면 Company(finance)에서 직접 가져온다.
- **analysis와 credit은 같은 레이어(L2)에서 독립적으로 존재한다.** 서로의 결과를 import하지 않는다.
- **review가 조합한다.** review에서 analysis 블록과 credit 블록을 성격별로 블록식으로 조합하여 보고서를 구성한다.
- **import 방향**: Company(L0/L1) → analysis(L2), Company(L0/L1) → credit(L2). analysis ↛ credit, credit ↛ analysis.

## 재무제표 분석 스토리 — 6막 구조

review 보고서는 이 6막 순서를 따른다. **앞 막이 뒷 막의 원인.**
6개 프레임워크(Damodaran/McKinsey/Buffett/Lynch/애널리스트/HBS) 조사 결과의 공통 구조.

### 6막

```
제1막: "이 회사는 뭘 하는가" (사업 이해)
  → 한 문장 정의 + 매출 구성 + 시장 위치 + 성장 추세
  → Damodaran: "Every valuation starts with a story"
  → 축: 수익구조, 성장성

제2막: "얼마나 잘 하는가" (수익성 + 원천)
  → 마진 계단(매출총이익→영업이익→순이익) + ROIC Tree + 비용구조
  → McKinsey: "가치 창출은 ROIC와 Growth 두 축"
  → 인과: 1막의 사업 특성이 2막의 마진 수준을 결정
  → 축: 수익성, 비용구조

제3막: "현금이 실제로 도는가" (현금 전환)
  → OCF 분해(NI+감가상각+운전자본) + FCF + CCC + 이익품질
  → Buffett: "영업CF > 순이익이면 이익이 진짜"
  → 인과: 2막의 이익이 3막에서 현금으로 전환되는가?
  → 축: 현금흐름, 이익품질

제4막: "자본 구조는 안전한가" (안정성)
  → 부채/이자/유동성 + 1년 내 상환 부담
  → 인과: 3막의 FCF가 부채 상환을 감당할 수 있는가?
  → 축: 자금조달, 안정성, **신용평가**

제5막: "번 돈을 어떻게 쓰는가" (자본배분)
  → 배당/자사주/재투자 + ROIC vs WACC + 자산 효율
  → Buffett: "유보이익 $1당 시가총액 $1 이상 증가해야"
  → 인과: 4막의 안전한 자본 안에서 가치를 창출하는 배분인가?
  → 축: 자산구조, 효율성, 투자효율, 자본배분, 재무정합성, 종합평가

제6막: "앞으로 어떻게 될 것인가" (전망 + 가치)
  → 매출 예측 + DCF/상대가치 + 리스크 + 지배구조
  → Damodaran: narrative → numbers → value
  → 인과: 1~5막 전체가 6막의 가치 판단을 뒷받침
  → 축: 가치평가, 지배구조, 공시변화, 비교분석, 매출전망
```

### 막 간 인과 연결

| 연결 | 문장 예시 |
|------|---------|
| 1막→2막 | "DX(51%)가 마진 21%의 주 원인" |
| 2막→3막 | "이익 19.6조 중 현금 28.8조 전환 (감가상각 21.5조 덕)" |
| 3막→4막 | "FCF 15조로 부채 상환 충분, 이자보상 88배" |
| 4막→5막 | "순현금이므로 배당 확대 여력 충분" |
| 5막→6막 | "ROIC > WACC이므로 재투자가 가치 창출" |

이 연결은 `review/narrative.py`의 `buildActTransition()`이 자동 생성.

### 왜 스토리인가

비율 대시보드는 숫자를 보여주지만 "왜"를 말하지 않는다.
ROE 12%가 좋은지 나쁜지는 그 회사의 사업 구조(1막), 마진 원천(2막), 현금 전환(3막)을 모르면 판단할 수 없다.
6막 구조는 이 맥락을 제공한다 — 각 막이 다음 막의 원인이므로, 어디서 문제가 시작됐는지 역추적할 수 있다.
분석이 스토리텔링이어야 하는 이유: 사람은 숫자가 아니라 이야기를 기억한다.

### 학술 근거

| 프레임워크 | 핵심 기여 | 6막 대응 |
|-----------|---------|---------|
| Damodaran | narrative → numbers → value | 전체 구조 |
| McKinsey | ROIC = Margin × Turnover, ROIC Tree | 2막 |
| Buffett/Munger | Moat 판별, OCF > NI | 2막+3막 |
| Peter Lynch | 종목 분류(성장/가치/턴어라운드), PEG | 1막+6막 |
| 애널리스트 | what → how well → why → forecast → value | 전체 흐름 |
| HBS 케이스 | Common-size → Trend → Ratio → DuPont → CF → Synthesis | 전체 방법론 |

## 스토리 기반 분석 사상

### 핵심 원칙

**모든 기업에는 고유한 스토리가 있다. 모든 기업을 같은 방식으로 분석할 수 없다.**

- analysis는 **도구**다 — 14축 calc 함수는 재무제표에서 숫자를 뽑는 도구
- review는 **스토리를 조합**한다 — 기업의 스토리에 맞는 도구를 골라서 조립
- 같은 도구라도 기업에 따라 **순서, 강조, 해석**이 달라야 한다

### 스토리 템플릿 체계

기업의 스토리 유형에 따라 review가 다른 템플릿을 적용한다.
템플릿은 6막 구조를 기반으로 하되, **각 막에서 어떤 축을 강조하고 어떤 인과를 부각하는지**가 달라진다.

| 템플릿 | 대표 기업 | 핵심 스토리 | 강조 축 |
|--------|---------|-----------|---------|
| 사이클 | 삼성전자, SK하이닉스 | 업황 사이클이 전부 | 부문별 마진 변동, CAPEX 사이클, 재고 |
| 프랜차이즈 | BGF리테일, 코웨이 | 안정 수익 + 현금 기계 | 마진 안정성, OCF/NI, 배당 지속성 |
| 턴어라운드 | 현대건설, 두산에너빌 | 적자→흑자 전환 | 이자보상, 부채 추이, 영업이익 전환점 |
| 성장 | 삼양식품, 코스맥스 | 고성장 + 마진 확대 | 매출 CAGR, 마진 추세, ROIC Tree |
| 자본집약 | 대한항공, 한국전력 | 설비 의존 + 감가상각 | CAPEX/감가상각, 자산회전, FCF |
| 지주 | CJ, 한화, GS | 자회사 포트폴리오 | 지분법손익, 영업외 분해, 자본배분 |
| 현금부자 | 삼성전자(BS), 크래프톤 | 현금 쌓임 + 배분 이슈 | FLEV, 순현금, 배당성향, 자사주 |

### 템플릿 결정 로직

기업 데이터에서 자동 판별:
- **사이클**: 이익 변동계수 > 0.5 + 업종(반도체/화학/조선)
- **프랜차이즈**: 마진 변동계수 < 0.1 + CCC 마이너스 또는 안정
- **턴어라운드**: 최근 3년 내 적자→흑자 전환
- **성장**: 매출 3Y CAGR > 15%
- **자본집약**: 유형자산/총자산 > 40%
- **지주**: 비영업자산 > 40% 또는 지분법손익/순이익 > 30%
- **현금부자**: 순현금 + 현금/자산 > 20%

하나의 기업이 여러 템플릿에 해당할 수 있다 (예: 삼성전자 = 사이클 + 자본집약 + 현금부자).

### analysis audit과의 연결

audit의 목적이 확장된다:
1. 기존: **엔진 오류 찾기** (오탐 수정)
2. 추가: **기업의 스토리 발견** → 어떤 템플릿이 맞는지 판단
3. 추가: **템플릿 개선** → audit에서 발견한 패턴으로 템플릿 보강
4. 추가: **인과 연결 검증** → 막 전환 문장이 실제 데이터와 맞는지

audit 파일 구조도 확장:
```
1. review 전문: c.review().toMarkdown() 그대로
2. AI 분석: 이 기업의 스토리는 무엇인가. 어떤 템플릿이 맞는가.
3. 엔진 개선: 이 스토리를 더 잘 전달하려면 뭐가 빠졌는가.
4. 템플릿 피드백: 현재 템플릿이 이 기업에 맞는가. 뭘 바꿔야 하는가.
```

### 체계 강화 규칙 (강제)

- **템플릿/체계 변경 시 반드시 실제 기업 audit으로 검증** — 최소 3개 기업
- 검증 없이 템플릿을 만들지 않는다
- "좋아 보이니까" 추가하지 않는다. "실제로 분석력이 올라가는가?"를 audit으로 확인 후 반영
- 실효성 없는 함수는 제거한다. 학술적으로 맞지만 실무 임팩트가 불분명한 것은 audit 판단 후 유지/제거
- 6막 구조, 막 전환 문장, ROIC Tree 등 변경 시 삼성전자 + 대우건설 + 1개 이상에서 검증

## 단일 진입점

- **`dartlab.analysis()` / `c.analysis()`** 하나로 모든 축에 접근한다
- analysis()가 가이드하고 라우팅 — 개별 calc 함수는 내부 구현
- insight는 등급 카드(보조 요약) — analysis와 역할이 다르다

## 15축 체계

| Part | 축 | 설명 | 항목 | calc 파일 |
|------|------|------|------|-----------|
| 1-1 | 수익구조 | 매출 구성 | 8 | revenueStructure.py |
| 1-2 | 자금조달 | 자금 출처 | 9 | fundingStructure.py |
| 1-3 | 자산구조 | 자산 구성 | 4 | assetStructure.py |
| 1-4 | 현금흐름 | 현금 흐름 | 3 | cashFlowStructure.py |
| 2-1 | 수익성 | 이익률 | 4 | profitability.py |
| 2-2 | 성장성 | 성장률 | 3 | growthAnalysis.py |
| 2-3 | 안정성 | 재무건전성 | 4 | stability.py |
| 2-4 | 효율성 | 자산 효율 | 3 | efficiency.py |
| 2-5 | 종합평가 | 재무건강 | 3 | scorecard.py |
| 3-1 | 이익품질 | 발생액/현금 | 4 | earningsQuality.py |
| 3-2 | 비용구조 | 비용 행태 | 4 | costStructure.py |
| 3-3 | 자본배분 | 현금 배분 | 5 | capitalAllocation.py |
| 3-4 | 투자효율 | 투자 가치 | 4 | investmentEfficiency.py |
| 3-5 | 재무정합성 | 재무제표 일치 | 5 | financialConsistency.py |
| 3-6 | **신용평가** | **20단계 등급** | **6** | **creditRating.py** |

## 6대 설계 규칙

1. **각 calc 함수는 독립적** — 다른 calc 함수를 호출하지 않는다
2. **각 단계는 자기 범위만 담당** — 단계 간 의존 없음
3. **속도가 생명** — 외부 API 호출 최소화
4. **시계열 테이블 필수** — 최소 5개 기간
5. **basePeriod 기준점** — 모든 calc에 basePeriod 파라미터
6. **기본 도구 = select()** — finance(IS/BS/CF) + docs + report 동일 패턴

## 품질 게이트

- calc 함수는 **3개 섹터 이상**에서 검증 후 배치
- fallback이 가치 없으면 제거 (None 반환이 나음)
- 금융업(은행/증권/보험) IS/BS 구조 미지원 — 장기 과제

## 재무제표 극한 활용 (갭 매트릭스)

9개 학술/실무 방법론 조사 결과. 현재 구현 수준과 빠진 것.

### 구현 수준 매트릭스

| 방법론 | 구현율 | 핵심 갭 |
|--------|--------|---------|
| Penman Reformulated FS | 60% | RNOA, FLEV/SPREAD 분해 없음 |
| Richardson 발생액 3계층 | 30% | BS 기반 WCACC/LTOACC/FINACC 분리 없음 |
| Mohanram G-Score | 0% | 성장주 전용 스코어 부재 |
| DuPont 확장 | 50% | RNOA 기반 분해, 업종 조정 없음 |
| CF 품질 분석 | 40% | Core OCF 조정, Maintenance CAPEX 분리 없음 |
| BS 자산 재분류 | 70% | NFO, 이연법인세 분류, 초과현금 분리 없음 |
| SCE 활용 | 20% | OCI 분해, Dirty Surplus 없음 |
| 세그먼트 심화 | 50% | 부문별 마진/ROIC, SOTP 밸류에이션 없음 |
| 3표 교차 검증 | 50% | BS-CF 연결, Articulation Check 없음 |

### 재무제표 직접 읽기 (비율 아닌 원본 활용) — 빠진 것

| 영역 | 빠진 분석 | 데이터 위치 |
|------|----------|-----------|
| IS | 판관비 하위 분해 (인건비/광고/R&D/임차료) | sections 주석 |
| IS | 영업외손익 분해 (이자/환차/지분법/처분) | IS finance_income/cost, 지분법손익 |
| IS | 매출원가 분해 (원재료/노무/경비) | sections 제조원가명세서 |
| CF | 영업CF 내부 분해 (비현금+운전자본 항목별) | CF 개별 조정항목 |
| CF | 투자CF 상세 (금융자산/관계기업 개별) | CF |
| BS | 부채 상세 (선수금/충당부채/리스부채 개별) | BS |
| BS | 자본 항목 분해 (자본금/잉여금/OCI 개별) | BS + SCE |
| 전체 | 계정별 CAGR 비교 (절대값 장기 추세) | IS/BS/CF 전체 |
| 전체 | BS-CF 정합성 (PPE/현금/자본 Articulation) | BS + CF |

### 구현 로드맵

**Phase 1 — 즉시** (데이터 있음, 나누기만 추가):
1. Penman RNOA + FLEV/SPREAD → `profitability.py`
2. Richardson 3계층 발생액 → `earningsQuality.py`
3. BS-CF Articulation Check → `crossStatement.py`

**Phase 2 — 재무제표 직접 읽기** (select()로 접근 가능):
4. 영업CF 내부 분해 → `cashflow.py`
5. 영업외손익 분해 → `earningsQuality.py`
6. 부채 상세 분해 → `stability.py`
7. 절대값 CAGR 비교 → `growthAnalysis.py`

**Phase 3 — 데이터 확장** (sections 파싱 연동 필요):
8. 판관비/매출원가 하위 분해
9. SCE 기반 OCI 분해
10. 부문별 영업이익/마진
11. Mohanram G-Score

### 학술 근거

- Penman: Nissim & Penman (2001), Penman FSA&SV 5e
- Richardson: Richardson et al. (2005) — Accrual Reliability, Earnings Persistence
- Mohanram: Mohanram (2005) — G-Score for Growth Stocks
- Soliman: Soliman (2008) — Industry-Adjusted DuPont
- CF 품질: Mulford & Comiskey (2005) — Creative Cash Flow Reporting

## forecast (예측)

**모든 것은 예측 가능하다.** 매출, 이익, 현금흐름, 배당 — 완벽한 정확도는 불가능하지만 방향과 범위는 추정할 수 있다. 예측하지 않으면 가치평가도 없고, 투자 판단도 없다. forecast 엔진은 이 전제에서 출발한다.

현재 구현: 매출 방향 예측 (72~78% 정확도). 향후 확장: 이익 예측, 현금흐름 예측, 배당 예측.

### 매출 방향 예측엔진 (calcRevenueDirection)

**방법론**: 모멘텀 + 업종별 베이즈 사후확률 갱신

```
1. 사전확률: 업종별 모멘텀 지속률 (40개 업종, 4800건+ 실측)
   - 식품/유지: 88.6% (안정 성장, 모멘텀 매우 강)
   - 철강/건설: 74~76% (경기 민감 사이클)
   - 반도체: 66.5% (사이클 급변)
   - 통신장비/영화: 59~61% (모멘텀 약)
   - 미등록 업종: 72.1% (전체 평균 fallback)
2. 갱신1: 2연속 같은 방향 → 확률 상승
3. 갱신2: 영업이익률 수준에 따라 연속적 갱신 (마진 21%와 1%를 차등)
4. 갱신3: OLS 외생변수 일치/불일치 → 갱신
5. 감쇠: 신호 간 독립성 위반 보정 (damping=0.3)
6. 보정: 원시 확률을 실측 기반 재보정 (shrinkage=0.6)
→ probability: 0.0~1.0 연속 확률값 반환
```

**핵심: confirms 이진 카운트 → 베이즈 연속 확률**
- 이전: 마진 21%와 마진 0.5%를 같은 "marginAgree=True"로 처리
- 지금: 마진 21% → 강한 갱신(P↑), 마진 0.5% → 거의 갱신 없음
- 이전: 모든 기업 prior 72.1% 동일
- 지금: 식품 기업 prior 88.6%, 반도체 prior 66.5% — 업종 특성 반영

**검증 수치** (walk-forward, 과적합 불가):

| 조건 | 정확도 | 관측치 | 커버리지 |
|------|--------|--------|---------|
| 모멘텀 단독 | 72.1% | 4825건 | 100% |
| 2연속 모멘텀 | 74.7% | 360건 | 69% |
| 모멘텀+영업이익률 일치 | 76.1% | 3660건 | 76% |
| 모멘텀+OLS 일치 | 77.7% | 355건 | 68% |

**확률 출력 예시**:
| 기업 | 방향 | 확률 | 신뢰도 | streak | 마진 | OLS |
|------|------|------|--------|--------|------|-----|
| 삼성전자 | up | 82.2% | very_high | 3 | 21% | 일치 |
| 현대제철 | down | 74.3% | high | 1 | 1% | 불일치 |

**확률의 의미**: 방향 정확도 자체를 올리지는 않는다 (72%는 72%). 하지만:
- AI가 "82% 확률로 매출 상승 예상"이라고 구체적으로 말할 수 있다
- P < 65%이면 "예측 불확실"로 명시 → 사용자가 추가 조사
- 기업 간 비교 시 확률 순위 정렬 가능
- 연속 값이라 **임계값 조정**으로 정밀도/재현율 트레이드오프 가능

**학술 근거**:
- 나이브 베이즈 + 감쇠: van Calster et al. (2021) — 소표본 과적합 방지
- M4/M5 Competition: 단순 방법 > 복잡한 ML (100,000 시계열)
- Sloan 1996: 이익 지속성 → 모멘텀의 이론적 기반
- PEAD: 실적 방향 지속 효과

**시도했지만 효과 없던 것**:
- Logistic Regression (+0.8%p) — 모델 구조 변경 무의미
- 한국 PPI 13개 추가 — 하락 (가격 < 생산량)
- 11신호 다수결 앙상블 (61%) — static 신호 = 상수 바이어스
- 후보 풀 확대 — 과적합 변수 선택
- 재고/매출 비율 — 전환점 예측에 1%p 차이 (무효)
- GDP — **영구 제외** (기업 매출의 직접 외생변수가 아님)

**정확도를 올리려면 새 데이터가 필요**:
- 네이버 데이터랩 검색량 (API 키 필요, B2C 20~30%)
- 관세청 품목별 수출 (API 키 필요, 수출 업종 40~50%)
- 컨센서스 리비전 시계열 (네이버 미제공, FnGuide 유료)

### 외생변수 6축 (OLS 확인용)

| 축 | 지표 예시 |
|------|------|
| 원자재 가격 | 구리, 알루미늄, 유가, 금속PPI, 밀, 면화 |
| 산업생산 | 반도체, 자동차, 화학, 식품, INDPRO, 배터리PPI |
| 실물수요 | 자동차판매, 내구재, 화물운송, 설비가동률, BSI |
| 금융조건 | 금리, 하이일드 스프레드, 회사채 |
| 내수경기 | IPI, 서비스업, BSI 내수/수출, 아파트가격 |
| 환율 | 원/달러, 원/엔, 원/위안 |

- 143개 업종 매핑, 95.5% 커버리지, `exogenousAxes.py`
- 적응형 변수 선택: 매핑 후보 + 범용 후보에서 상관도 상위 3개
- `productIndex.parquet`: 2444종목 공시 제품 텍스트 (0.3MB)
- OLS 단독은 62~66% 천장 — "확인자" 역할만 (독립 예측자 아님)

### 추가 탐색 결과

| 방향 | 결과 | 상태 |
|------|------|------|
| 횡단면 ML (Chen 2022) | 모멘텀+마진이 이미 76% → ML 추가 이득 불분명 | 장기 검토 |
| 관세청 수출입 HS코드 | API 키 필요 | 보류 |
| 공시 tone (키워드) | preview 200자 한계 | 보류 |
| Google Trends | 한국 점유율 낮음 | 제외 |
| 피어 선행 | Frankel 2025: spillover 약함 | 제외 |

### valuation (가치평가)

- DCF, DDM, 상대가치
- CAPM WACC, DPS, PEG, NAV, Forward PBR, Normalized DCF

## Spec 체계

```
grading.py AREAS dict    ← 로직 + 메타데이터 공존 (label, description, metrics, grade_fn)
       ↓
insight/spec.py          ← AREAS에서 추출·가공
       ↓
ai/spec.py               ← 각 엔진 spec 수집 (summary / detail depth)
       ↓
test_spec_integrity.py   ← 누락/불일치 검증 (CI 강제)
```

## Audit 학습 체계

audit 파일(`data/dart/auditAnalysis/{종목코드}.md`)은 반드시 아래 3섹션 구조를 따른다:

1. **review 전문**: `c.review().toMarkdown()` 출력을 그대로 붙인다. 편집하지 않는다.
2. **AI 분석**: review를 읽고 분석가 관점으로 직접 해석. 핵심 스토리, 수치 교차검증, 업종 맥락, 내 관점.
3. **엔진 개선 사항**: 치명/보완/표현 분류. 숫자 오류, null 누락, 왜곡된 지표 등.

- `[OK]` 찍고 "양호" 쓰는 건 audit이 아니다
- review 전문 없이 요약만 쓰는 것도 audit이 아니다
- 이 구조를 따르지 않은 파일은 재작성

## 데이터 매핑

- accountMappings.json 등 매핑 변경은 **실험 검증 후** 반영한다
- total_equity = `EquityAttributableToOwnersOfParent`, equity_including_nci = `Equity`

## 예측에서 영구 제외된 것

| 항목 | 이유 |
|------|------|
| 소셜미디어 감성 | 47.6% = 랜덤 이하 |
| GDP beta | 개별 기업에 무효 (Fed 2024) |
| 주가내재 역산 | 순환논리 |

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/analysis/financial/` | 15축 calc 함수 |
| `src/dartlab/analysis/financial/creditRating.py` | 신용평가 6 calc (등급/eCR/시계열/플래그) |
| `src/dartlab/analysis/financial/insight/` | grading + spec |
| `src/dartlab/analysis/financial/research/` | 리서치 (predictionSignals) |
| `src/dartlab/analysis/forecast/` | simulation, 예측 |
| `src/dartlab/analysis/valuation/` | DCF, DDM, 상대가치 |
| `src/dartlab/core/finance/creditScorecard.py` | 20단계 등급 산출 순수 로직 |
| `src/dartlab/core/finance/sectorThresholds.py` | 업종별 등급 기준표 (11개 대분류) |
| `src/dartlab/core/finance/chsModel.py` | CHS 하이브리드 부도확률 모델 |
| `src/dartlab/core/finance/exogenousAxes.py` | 6축 28개 지표 업종 매핑 |
