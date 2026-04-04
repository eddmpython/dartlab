# Macro

시장 레벨 매크로 분석 엔진. Company 없이 경제 환경을 해석한다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `dartlab.macro()` |
| 소비 | gather(L1) — FRED/ECOS, scan finance.parquet |
| 생산 | ai(L3)가 매크로 환경 판단에 소비 |
| 축 | 11축: 사이클, 금리, 자산, 심리, 유동성, 예측, 위기, 재고, 기업집계, 교역, 종합 |

## 설계 원칙

- **Company 불필요** — 종목코드 없이 동작
- **macro ↛ analysis** — 같은 L2지만 상호 import 금지. 해석 조합은 AI(L3)의 몫
- **외부 통계 라이브러리 없음** — Hamilton RS, Kalman DFM, Nelson-Siegel 전부 numpy 직접 구현
- 3계층: L0(core/finance 순수함수) → L1(gather 수집) → L2(macro 분석축)

## API

```python
import dartlab

dartlab.macro()                       # 가이드 (축 목록)
dartlab.macro("사이클")               # 경제 사이클 4국면
dartlab.macro("금리")                 # 금리 + 고용 + 물가
dartlab.macro("자산")                 # 5대 자산 + Cu/Au
dartlab.macro("심리")                 # 공포탐욕 + ISM
dartlab.macro("유동성")               # M2 + 연준 B/S
dartlab.macro("예측")                 # LEI + 침체확률 + Hamilton + Nowcast
dartlab.macro("위기")                 # Credit-to-GDP + Minsky/Koo/Fisher
dartlab.macro("재고")                 # ISM 재고순환
dartlab.macro("기업집계")             # 전종목 이익/Ponzi/레버리지
dartlab.macro("교역", market="KR")    # 교역조건 + 수출이익
dartlab.macro("종합")                 # 10축 + 40전략 대시보드
```

---

## 축별 가이드

### 사이클 (cycle) — 투자 의사결정의 출발점

4국면 판별: 확장 → 둔화 → 침체 → 회복

**왜 보는가**: 4국면이 자산배분의 기본 뼈대. 확장기에는 주식, 침체기에는 채권.

**어떻게 읽는가**:
- `phase`: 핵심. expansion/slowdown/contraction/recovery
- `confidence`: low일 때가 가장 중요 — 전환기라는 뜻
- `transition`: 전환 시퀀스 감지되면 국면 전환 임박
- `sectorStrategy`: 업종별 overweight/neutral/underweight

**무엇을 주의하는가**:
- HY 스프레드 + 장단기차가 **동시에** 악화 → 침체 신호 강화
- VIX 단독 급등은 일시적 충격일 수 있음 — 스프레드와 함께 봐야 함
- KR 시장은 CLI(경기선행지수)에 의존 — 미국보다 신호가 느림

**데이터**: FRED — BAMLH0A0HYM2, T10Y2Y, VIXCLS, GOLDAMGBD228NLBM, T10YIE, CPIAUCSL. ECOS(KR) — CLI, USDKRW

---

### 금리 (rates) — 정책과 시장의 줄다리기

금리 방향 + 고용/물가 + DKW 분해 + BEI/실질금리 4분면

**왜 보는가**: 금리는 모든 자산 가격의 할인율. 금리 방향이 바뀌면 모든 것이 바뀐다.

**어떻게 읽는가**:
- `outlook.direction`: cut/hold/hike — 가장 중요한 방향
- `expectation.spread2yFf`: 2Y-FF 스프레드. 음수면 시장이 인하 기대
- `decomposition`: DKW 분해(US만) — 명목 = 실질 + BEI + 기간프리미엄
- `employment.state`: strong이면 금리 인상 여력, weak이면 인하 압력
- `inflation.state`: hot이면 인상 불가피, cool이면 인하 가능

**무엇을 주의하는가**:
- 고용이 strong인데 물가가 hot → 스태그플레이션 아닌지 확인
- 2Y-FF 스프레드가 장기간 음수 → 시장과 연준의 괴리 확대 → 변동성 증가
- KR은 DKW 분해 불가(TIPS 없음) — 기준금리 + 국고채 스프레드로 대체

**데이터**: FRED — FEDFUNDS, DGS2, DGS10, DFII10, T10YIE, UNRATE, CPI. ECOS(KR) — BASE_RATE, CPI

---

### 자산 (assets) — 시장이 말하는 것

5대 자산 신호 + 금 3요인 + Cu/Au ratio + BEI/실질금리 4분면

**왜 보는가**: 자산 가격 자체가 경제의 투표. 금이 급등하면 불안, 구리가 급등하면 성장 기대.

**어떻게 읽는가**:
- `assets`: 각 자산의 방향 + 해석
- `goldDrivers`: 금 가격의 3요인 — 실질금리, 달러, 안전자산 수요 중 뭐가 지배적인지
- `copperGold`: Cu/Au ratio — 상승이면 산업수요 확대 기대, 하락이면 안전자산 선호
- `vixRegime`: VIX 구간 — panic(>40)이면 분할매수 3차, fear(>25)이면 1차

**무엇을 주의하는가**:
- Cu/Au ratio와 10Y 국채 수익률은 역사적으로 강한 상관 — 괴리 시 주의
- 금 3요인 중 "안전자산 효과"가 지배적이면 위기 징후
- VIX 30 이상 지속은 드뭄 — 대부분 매수 기회 (단, 50 이상은 시스템 리스크)

**데이터**: FRED — DGS2, DGS10, DFII10, VIXCLS, DTWEXBGS, GOLDAMGBD228NLBM, PCOPPUSDM

---

### 심리 (sentiment) — 군중의 반대편

공포탐욕 0-100 + ISM 자산배분 바로미터

**왜 보는가**: 극단적 심리는 역방향 신호. 극단공포에 사고 극단탐욕에 경계.

**어떻게 읽는가**:
- `fearGreed.score`: 0-100. <25 극단공포(매수 기회), >75 극단탐욕(차익 실현)
- `fearGreed.components`: 4요소 중 어디서 공포/탐욕이 오는지
- `ismAllocation`: ISM >55면 risk-on, <50이면 risk-off (투자전략 13)
- `vixRegime.buySignal`: 0/1/2/3 분할매수 차수

**무엇을 주의하는가**:
- 공포탐욕 단독으로 투자 결정 금지 — 반드시 사이클/위기 축과 교차 확인
- ISM 자산배분은 제조업 기반 — 서비스업 경기와 괴리 가능
- KR 시장은 심리 지표 제한적

**데이터**: FRED — VIXCLS, SP500, BAMLH0A0HYM2, GOLDAMGBD228NLBM

---

### 유동성 (liquidity) — 돈이 어디로 흐르는가

M2 + 연준 B/S + 신용스프레드 + 설비투자 압력

**왜 보는가**: "돈이 풀리면 자산 오르고, 돈이 마르면 자산 내린다." 유동성이 자산 가격의 최종 결정자.

**어떻게 읽는가**:
- `regime`: abundant(풍부)/normal/tight(긴축)
- `score`: -3~+3. 양수 = 풍부, 음수 = 긴축
- `capexPressure`: HY 스프레드 변화 → 기업 설비투자 방향 (투자전략 32)
- `signals`: 어떤 지표가 풍부/긴축을 결정하는지

**무엇을 주의하는가**:
- M2 증가 + 연준 QE = 자산 상승의 연료. 반대로 QT + M2 수축 = 하락 압력
- HY 스프레드 500bp 이상 + 확대 추세 = 설비투자 축소 → 경기 하방
- 역레포 감소는 유동성 방출 — 하지만 미국 전용 지표

**데이터**: FRED — M2SL, WALCL, BAMLH0A0HYM2, BAMLC0A0CM, RRPONTSYD

---

### 예측 (forecast) — 앞으로 어떻게 되나

LEI + Cleveland Fed 침체확률 + Sahm Rule + Hamilton RS + GDP Nowcast

**왜 보는가**: 사이클이 "지금 어디인가"라면 예측은 "앞으로 어디로 가는가".

**어떻게 읽는가**:
- `recessionProb.probability`: 0-1. >0.3이면 경계, >0.5이면 높음
- `lei.signal`: expansion/caution/recession_warning
- `hamiltonRegime`: 현재 국면 + 확률. contractionProb > 0.5면 침체 진입 가능성
- `nowcast`: GDP 실시간 추정 + 신뢰도
- `sahmRule`: ≥0.5%p면 침체 신호 발동 (2024년 false positive 주의)

**핵심 원리**:
- Cleveland Fed 프로빗: 10Y-3M 스프레드 → Φ(α+βx) — 지난 8번 미국 침체 전부 예측
- Hamilton RS: GDP 성장률의 2-regime Markov Switching — EM 알고리즘으로 추정
- GDP Nowcast: 6개 월간 지표에서 Dynamic Factor 추출 → Kalman 필터로 GDP 추정
- Sahm Rule: 실업률 3M 이동평균 - 12M 최저. ≥0.5%p면 침체

**무엇을 주의하는가**:
- 프로빗은 리드타임 6-18개월 편차 — "곧 침체"가 아니라 "1년 내 침체 가능"
- Hamilton RS는 사후 판별에 강하지만 실시간 전환점은 2-3분기 지연
- Sahm Rule 2024년 0.57%p 도달했으나 실제 침체 없음 — 단독 의존 금지
- GDP Nowcast는 6개 지표 중 결측이 많으면 신뢰도 하락

**데이터**: FRED — T10Y3M, AWHMAN, ICSA, NAPMNOI, PERMIT, SP500, INDPRO, PAYEMS, RSAFS. ECOS(KR) — CLI, CCI, CLI_LAG

---

### 위기 (crisis) — 구조적 불균형 감지

Credit-to-GDP gap + GHS 위기예측 + Minsky 5단계 + Koo BSR + Fisher 부채디플레

**왜 보는가**: 사이클은 정상적 경기순환. 위기는 구조적 불균형에서 온다. 2008년 같은 사건은 사이클이 아니라 위기.

**어떻게 읽는가**:
- `creditGap.gap`: Credit-to-GDP 트렌드 이탈. >10%p면 BIS 최고 경고
- `creditGap.ccybBuffer`: 바젤III 경기대응완충자본 0-2.5%
- `ghsScore.crisisProb`: 3년 내 금융위기 확률. 정상 ~7%, 위험 ~40%
- `minskyPhase`: displacement → boom → overtrading → discredit → revulsion
- `kooRecession.isBSR`: True면 대차대조표 침체 — 재정 확대 필수
- `fisherDeflation.risk`: high면 부채-디플레이션 악순환 위험
- `recessionDashboard`: 프로빗+LEI+ISM+신용+스프레드 종합

**핵심 원리**:
- BIS Credit-to-GDP gap: 단측 HP 필터(λ=400,000)로 트렌드 추출 → 실제와의 괴리
- GHS: 3년간 신용 팽창 + 자산가격 급등 동시 → 위기 확률 급등 (42개국 1950-2016 실증)
- Minsky: 안정이 불안정을 낳는다 — 호황기 리스크 축적이 위기의 원인
- Koo: 민간이 저금리에도 차입 안 하고 부채 상환 → 정부 재정이 유일한 해법
- Fisher: 과잉 부채 → 디스트레스 매각 → 물가 하락 → 실질 부채 증가 → 악순환

**무엇을 주의하는가**:
- Credit-to-GDP는 분기 데이터라 반응 느림 — 선행지표가 아니라 확인 지표
- GHS는 3년 창이라 "지금 당장"의 위기는 감지 못함 — HY 스프레드(유동성 축)로 보완
- Minsky "과열" 판정 후 바로 공황이 아님 — 과열은 수년 지속 가능
- KR 부동산 스트레스: Ponzi비율 32.8% + 레버리지 88.6%(2025) — 경계

**데이터**: FRED — TCMDO, GDP, SP500, VIXCLS, DTWEXBGS, BAMLH0A0HYM2, TDSP. ECOS(KR) — CREDIT_TOTAL, GDP, CPI

---

### 재고 (inventory) — 경기 전환의 첫 신호

ISM 재고순환 4국면 + 자산배분 바로미터

**왜 보는가**: 재고순환(Kitchin 3-4년)은 경기 전환의 가장 빠른 신호. 재고가 바닥나면 생산이 늘고, 넘치면 감산.

**어떻게 읽는가**:
- `inventoryPhase`: active_restock(적극보충, 회복) → passive_restock(수동보충, 확장) → active_destock(적극감축, 수축) → passive_destock(수동감축, 바닥)
- `ismBarometer`: ISM >55 강한확장, 50-55 확장, <50 수축, <45 심각수축
- `ismBarometer.rateImplication`: ISM <55 + 하락 추세면 "인상종결 가능" (투자전략 34)
- `ismAllocation`: 자산배분 입장 — risk-on / neutral / risk-off (투자전략 13)

**무엇을 주의하는가**:
- ISM은 제조업 전용 — 서비스업 경기와 괴리 가능 (미국 GDP의 70%가 서비스업)
- KR은 ISM 없음 — 광공업생산 + BSI로 프록시. 정확도 낮음
- 재고순환 "바닥"은 매수 기회지만, 위기 축이 "공황"이면 기다려야 함

**데이터**: FRED — NAPM, NAPMNOI, NAPMII, NEWORDER, BUSINV. ECOS(KR) — MANUFACTURING, BSI_ALL

---

### 기업집계 (corporate) — Bloomberg 없이 bottom-up 매크로

전종목 재무제표 집계 → 이익사이클, Ponzi비율, 레버리지사이클

**왜 보는가**: 거시경제는 결국 기업의 합. 전종목 영업이익이 줄면 경기가 나빠지고 있다는 직접 증거.

**어떻게 읽는가**:
- `earningsCycle`: 전종목 영업이익 합계 YoY. >10% 확장, <-10% 수축
- `ponziRatio`: ICR<1 기업 비중. >30%면 시스템 취약, >40%면 위기 수준
- `leverageCycle`: 부채비율 중간값. 상승 추세면 레버리지 축적

**실측 결과 (2025년 DART 2745종목)**:
- 이익 사이클: 2023 -30.9%(반도체 불황) → 2024 +38.6%(회복) → 2025 -19.5%(재하락)
- Ponzi 비율: 2021 16.8% → 2025 32.8% (상장기업 1/3이 영업이익으로 이자 미충당)
- 레버리지: 2023 70.4% → 2025 88.6% (급등)

**무엇을 주의하는가**:
- scan/finance.parquet 필요 — `dartlab collect --scan`으로 수집
- 연결재무제표 4분기(연간) 데이터만 사용 — 분기 빈도 미지원
- 금융업(은행/보험) 제외 필요 — ICR 구조가 다름

**데이터**: scan/finance.parquet (DART 2745종목 / EDGAR 6600+종목)

---

### 교역 (trade) — 한국 경제의 바로미터

교역조건 + 대용치 + 수출이익 선행 + 양국 선행지수 (KR 시장 전용)

**왜 보는가**: 한국 GDP의 40%+가 수출. 교역조건은 한국 경제의 가장 빠른 선행지표.

**어떻게 읽는가**:
- `termsOfTrade`: 수출물가/수입물가 비율. 상승 = 수출 환경 개선
- `totProxy`: 환율상승률 - 유가상승률 (투자전략 12). 양수면 수출 유리
- `exportProfit`: 교역조건 + 수출량 조합 → 수출기업 이익 선행 (투자전략 31)
- `leadingRelativeStrength`: US LEI vs KR CLI → 환율 방향 (투자전략 14)
- `usConsumptionLink`: 미국 소매판매 → 한국 주가 (투자전략 5)

**무엇을 주의하는가**:
- US 시장에서는 대부분 null — KR 전용
- 교역조건 대용치는 단순 근사 — 실제 교역조건과 방향은 같지만 수준은 다름
- 환율 전가율(pass-through)은 업종마다 다름 — 수출비중이 높은 업종에서 유효

**데이터**: ECOS — EXPORT_PRICE, IMPORT_PRICE, EXPORT, USDKRW, CLI. FRED — DCOILWTICO, RSAFS

---

### 종합 (summary) — 10축을 하나로

10축 종합 점수 + 40개 투자전략 대시보드

**왜 보는가**: 개별 축을 하나하나 보기 어려울 때 전체 그림을 한 번에.

**어떻게 읽는가**:
- `overall`: favorable/neutral/unfavorable
- `score`: 점수 (양수=우호적, 음수=비우호적)
- `reasons`: 점수에 기여한 근거 목록
- `contributions`: 축별 점수 기여도
- `strategies`: 40개 전략 활성/비활성 + 방향 + 강도

**무엇을 주의하는가**:
- 종합 점수는 참고용 — 개별 축의 세부 신호가 더 중요
- 전략이 bullish로 많으면 낙관적 환경, bearish로 많으면 방어적
- 부분 축 실패(데이터 없음)해도 나머지로 종합 — 전체 점수가 희석될 수 있음

---

## 축 조합 가이드 — 실전 시나리오

| 질문 | 보는 축 | 판단 기준 |
|------|---------|----------|
| "경기 침체가 오나?" | forecast + cycle + crisis | 프로빗 >30% + 둔화/침체 + Minsky 과열 이후 |
| "금리는 어떻게 되나?" | rates + forecast + liquidity | 인하기대(2Y-FF 음수) + LEI 하락 + 유동성 긴축 |
| "한국 수출은?" | trade + inventory + corporate | ToT 악화 + 적극감축 + 이익수축 |
| "지금 주식 사도 되나?" | sentiment + cycle + crisis | F&G <25 + 회복기 + 위기점수 낮음 |
| "금융위기 가능성?" | crisis + liquidity + corporate | Gap>10 + GHS>50 + Ponzi>30% |
| "환율 방향은?" | trade + assets + rates | 양국 선행지수 + 달러인덱스 + 금리차 |
| "설비투자 전망?" | liquidity + inventory + corporate | HY 스프레드 하락 + ISM 확장 + 이익 확장 |

---

## 40개 투자전략 대시보드

summary 축의 `strategies`에서 40개 전략의 활성 여부를 실시간 판별.

### 경기순환 (A)

| # | 전략 | 축 | 핵심 | 활성 조건 |
|---|------|------|------|----------|
| 1 | 금리 = 전기비 성장률 | forecast+rates | 성장률 모멘텀이 금리 방향을 결정 | rates.outlook.direction 존재 |
| 6 | 실물투자 → 경기변동 | cycle | 사이클 4국면 자체가 답 | cycle.phase 존재 |
| 7 | 재고흐름 → 서프라이즈 | inventory | 재고순환 국면이 기업 실적 서프라이즈 결정 | inventoryPhase 존재 |
| 8 | 재고순환 → 주가예측 | inventory | 신규수주/재고 비율 상승 = 주가 상승 | inventoryPhase 존재 |
| 9 | 침체탈출 = 정부지출 | cycle | 회복기에 정부지출이 촉매 | phase == "recovery" |
| 16 | 전기비성장률 = 선행+후행 | forecast | LEI + 후행지수 모멘텀 합 ≈ GDP 근사 | lei.signal 존재 |

### 선행지수/교역조건 (B)

| # | 전략 | 축 | 핵심 | 활성 조건 |
|---|------|------|------|----------|
| 5 | 한국주가 ≈ 미국소비 | trade | US 소매판매 YoY → KOSPI 방향 | usRetailYoy 존재 |
| 10 | 한국주가 = 수출기업 | trade | 수출이익 선행 → KOSPI | exportProfit.signal 존재 |
| 11 | 교역조건 = 최선행 | trade | ToT 모멘텀이 가장 빠른 선행지표 | termsOfTrade.direction 존재 |
| 12 | ToT대용치 = 환율-유가 | trade | 환율YoY - 유가YoY | totProxy.value 존재 |
| 14 | 양국 선행지수 → 환율 | trade | US LEI - KR CLI 상대강도 | leadingRelativeStrength 존재 |
| 15 | 후행상승 + 120일선 반등 | forecast | 후행지수 모멘텀 > 0 | lagMomentum > 0 |
| 31 | ToT대용치 → 수출이익 | trade | 교역조건 개선 → 수출기업 이익 2-3분기 선행 | exportProfit.signal 존재 |

### 금리/통화정책 (C)

| # | 전략 | 축 | 핵심 | 활성 조건 |
|---|------|------|------|----------|
| 4 | 금리 = 미래 인플레 | rates | BEI 추세가 금리 방향 결정 | inflation.state 존재 |
| 17 | 고용지표 주목 | rates | 비농업고용/실업률이 금리의 핵심 입력 | employment.state 존재 |
| 19 | 통화정책 = 투자 마일스톤 | rates | 인상→인하 전환이 자산배분 전환점 | outlook.direction 존재 |
| 20 | 금리정책 전후 장단기차 | rates | 인상 말기 = 역전, 인하 초기 = 가팔라짐 | spread2yFf 존재 |
| 22 | 물가과열 → 긴축 → 선행하락 | rates+forecast | CPI 과열 → 연준 인상 → LEI 하락 체인 | inflation.state == "hot" |
| 28 | 금리상승 = 경기회복 전제 | rates+cycle | 경기 회복 없는 금리 상승은 경고 | rate_dir + phase 교차 |
| 30 | 장단기차 → CLI 선행 | rates+forecast | Yield Curve 기울기가 경기선행지수에 선행 | spread2yFf 존재 |
| 34 | ISM<55 → 인상종결 | inventory+rates | ISM 55 하회 + 하락 추세 = 금리인상 마무리 | rateImplication == "hike_end" |
| 37 | 산업생산+물가 → 금리 | rates+cycle | 산업생산 YoY + CPI YoY 동반 상승 → 금리 상승 | inflation + phase 교차 |
| 40 | 금융업주가 ← 장단기차 | rates | 장단기차 확대 → 금융업(은행) 유리 | spread2yFf > 0.5 |

### 환율/달러 (D)

| # | 전략 | 축 | 핵심 | 활성 조건 |
|---|------|------|------|----------|
| 3 | GDP 상대강도 → 환율 | trade | US-KR 성장률 차이 → 원/달러 방향 | fxDirection 존재 |
| 23 | 달러하락 → 신흥국 | assets+crisis | DXY 3m 하락 → EM 자산 유리 | dxyChange3m < -2 |
| 24 | 달러강세 → 미국국채 | assets+crisis | DXY 3m 상승 → UST 유리 | dxyChange3m > 2 |
| 25 | 달러↔금 대체 | assets | 달러 약세 → 금 상승 (역상관) | goldDrivers.dollarEffect 존재 |
| 27 | 원/달러 하락 → 내수주 | trade | 원화 강세기에 내수 소비주 유리 | fxYoy < -3 |
| 38 | 금융위험 → 달러상승 | crisis+assets | VIX 급등 → 안전자산 달러 수요 | dollarSafeHaven.status == "active" |

### 물가/신용 (F)

| # | 전략 | 축 | 핵심 | 활성 조건 |
|---|------|------|------|----------|
| 13 | ISM = 자산배분 바로미터 | inventory | ISM >55 risk-on, <50 risk-off | ismAllocation.stance 존재 |
| 18 | 한국물가 = 환율+유가 | trade | USDKRW YoY×0.06 + WTI YoY×0.03 = CPI 압력 | fxYoy + oilYoy 존재 |
| 32 | 신용스프레드 = 설비투자 압력 | crisis | HY 확대 → 기업 자금조달비용 증가 → CAPEX 축소 | capexPressure 존재 |
| 33 | 공급과잉 → 도산 | inventory+crisis | 적극감축 + HY 긴축 = 기업 도산 위험 | destock + tightening |
| 35 | 국내신용위험 ↔ CPI | crisis | 한국 CPI 상승 → 신용위험 확대 | krCreditRisk.cpiYoy 존재 |
| 36 | 중국 통화 → 원자재 | assets | Cu/Au ratio로 중국 수요 프록시 | copperGold.implication 존재 |

---

## 방법론 + 학술 근거

| 방법론 | 논문 | 구현 | 정확도/한계 |
|--------|------|------|-----------|
| Cleveland Fed 프로빗 | Estrella & Mishkin (1996) | `clevelandProbit()` | 지난 8번 침체 전부 예측. 리드타임 6-18개월 편차 |
| Hamilton Regime Switching | Hamilton (1989) | `hamiltonRegime()` — EM+김스무더 | 사후 판별 정확. 실시간 전환점 2-3분기 지연 |
| GDP Nowcasting (DFM) | Banbura, Giannone, Reichlin (2011) | `gdpNowcast()` — Kalman+EM | NY Fed 방식. 결측 처리 가능 |
| Nelson-Siegel | Nelson & Siegel (1987) | `nelsonSiegel()` — gridλ+OLS | 3팩터로 곡선 95% 설명 |
| Sahm Rule | Sahm (2019) | `sahmRule()` | 2024년 false positive. 단독 의존 금지 |
| BIS Credit-to-GDP gap | Borio & Drehmann (2014) | `creditToGDPGap()` — 단측HP | Basel III 공식. 분기라 느림 |
| GHS 위기예측 | Greenwood-Hanson-Shleifer (2022 JoF) | `ghsCrisisScore()` | 42개국 1950-2016. 3년 창 |
| Minsky 5단계 | Kindleberger-Minsky | `minskyPhase()` | 정성→정량 변환. 판별 임계값 검증 필요 |
| Koo BSR | Koo (2009) | `kooBalanceSheetRecession()` | 일본 1990년대 설명력 높음 |
| Fisher Debt-Deflation | Fisher (1933) | `fisherDebtDeflation()` | DSR+CPI+NPL 조합 |
| Kitchin 재고순환 | Kitchin (1923) | `classifyInventoryPhase()` | 3-4년 주기. ISM 기반 |
| Cu/Au Ratio | 실증 연구 다수 | `copperGoldRatio()` | 10Y 수익률과 상관. 2024년 이후 약화 보고 |

**모든 방법론은 numpy만으로 직접 구현. 외부 통계 라이브러리 없음.**

---

## L0 순수 함수 (41개)

| 파일 | 함수 수 | 주요 함수 |
|------|--------|---------|
| macroCycle.py | 11 | classifyCycle, interpretAssets, copperGoldRatio, realRateRegime |
| regimeSwitching.py | 4 | clevelandProbit, conferenceBoardLEI, sahmRule, hamiltonRegime |
| nowcast.py | 1+4 | gdpNowcast (Kalman필터+스무더+EM 내부) |
| yieldCurve.py | 1 | nelsonSiegel |
| sentiment.py | 6 | calcFearGreedProxy, ismAssetAllocation, krInflationModel |
| liquidity.py | 2 | classifyLiquidityRegime, capexPressure |
| crisisDetector.py | 7 | creditToGDPGap, ghsCrisisScore, minskyPhase, kooRecession, fisherDebt |
| inventoryCycle.py | 2 | classifyInventoryPhase, ismBarometer |
| termsOfTrade.py | 4 | calcToT, totProxy, exportProfitLeading |
| corporateAggregate.py | 3 | aggregateEarningsCycle, ponziRatio, leverageCycle |
| strategyRules.py | 1 | evaluateStrategies (40개 전략) |

---

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/macro/` | 11축 + 종합 (12개 모듈) |
| `src/dartlab/core/finance/*.py` | L0 순수함수 (11개 파일, 41개 함수) |
| `src/dartlab/gather/fred/catalog.py` | FRED ~77개 시리즈 |
| `src/dartlab/gather/ecos/catalog.py` | ECOS ~53개 지표 |
