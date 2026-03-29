# Analysis 엔진 — 기업분석 방법론 체계

> 이 문서는 analysis 엔진의 철학, 구조, 방법론 체계를 기록한다.
> 개발 이론적립 과정을 통해 점진적으로 확정한다.

---

## 1. 현황 진단

### dartlab 핵심 가치 (확정)
- **sections** — 사업보고서 수평화, 기간 비교
- **데이터** — DART/EDGAR 재무제표, 공시 원문
- **scan** — 2700개 종목 스크리닝

analysis/는 이 위에 올라가는 **해석 레이어**다.
README에서 실험적 기능으로 소개 중. 아직 안정화 전이므로 지금이 구조를 바로잡을 적기.

### 문제
- 철학 없이 기능별로 10개 엔진이 쌓였다
- 기업분석 방법론 체계와 매핑되지 않는 폴더 구조
- 엔진 명칭이 실제 역할과 안 맞음 (research, analyst)
- 8대 영역이라는 축 없이 기능을 나열만 했다

---

## 2. 기업분석 방법론 8대 영역

Palepu-Healy 4단계를 기본 골격으로, CFA/McKinsey/S&P/PE 실사 체계를 교차하여 확장.

```
기업분석(Corporate Analysis)
│
├─ [1] 전략/사업 분석 (Strategy & Business Analysis)
│     사업모델, 경쟁우위, 경영진, 지배구조, ESG, 공시 텍스트
│
├─ [2] 회계/공시 분석 (Accounting & Disclosure Analysis)
│     회계정책, 이익의 질, 공시 품질, 적기경보(Red Flags)
│
├─ [3] 재무분석 (Financial Analysis)
│     비율, 공통형, 추세, 지수, 현금흐름, 분해(DuPont/세그먼트), 부실예측
│
├─ [4] 전망분석 (Prospective Analysis)
│     재무제표 추정, 성장 모델링, 시나리오/민감도 분석
│
├─ [5] 가치평가 (Valuation)
│     DCF, 멀티플, SOTP, 자산기반
│
├─ [6] 리스크 분석 (Risk Analysis)
│     재무 리스크, 사업 리스크, 시장 리스크, 신용평가
│
├─ [7] 비교분석 (Comparative Analysis)
│     피어, 섹터 벤치마크, 글로벌, 시계열 자기비교, 이벤트
│
└─ [8] 경제/산업 분석 (Macro & Industry Analysis)
      거시경제, 산업 사이클, 규제, 기술 변화
```

### 분석 흐름
```
[8] 경제/산업 (외부 환경, Top-down 출발점)
    ↓
[1] 전략/사업 (이 기업은 무엇이고, 왜 돈을 버는가)
    ↓
[2] 회계/공시 (숫자를 믿을 수 있는가)
    ↓
[3] 재무분석 (과거에 무엇이 일어났는가)
    ↓
[4] 전망분석 (앞으로 무엇이 일어날 것인가)
    ↓
[5] 가치평가 (그래서 이 기업의 가치는 얼마인가)
    ↓
[6] 리스크 (무엇이 잘못될 수 있는가)

    ↔ [7] 비교분석 (모든 단계에 횡단 적용)
```

### 관통 축 (렌즈)

| 축 | 설명 |
|---|---|
| 정량 vs 정성 | 숫자 기반 vs 판단/서술 기반 |
| 내부 vs 외부 | 기업 내부 데이터 vs 외부 환경 |
| 과거 vs 미래 | 실적 기반 vs 추정 기반 |
| 절대 vs 상대 | 기업 단독 vs 비교 |
| 재무 vs 비재무 | 재무제표 기반 vs 비재무 정보 |

---

## 3. 새 폴더 구조 (확정)

```
analysis/
├── strategy/       # [1] 전략/사업 분석
├── accounting/     # [2] 회계/공시 분석
├── financial/      # [3] 재무분석
├── forecast/       # [4] 전망분석
├── valuation/      # [5] 가치평가
├── risk/           # [6] 리스크 분석
├── comparative/    # [7] 비교분석
└── macro/          # [8] 경제/산업 분석
```

8대 영역 = 8개 폴더. 향후 영역 추가 시 방법론적 근거 필요.

### 기존 → 신규 이전 매핑

| 기존 엔진 | → 새 위치 | 이유 |
|-----------|----------|------|
| research/ (narrative, scoring, orchestrator) | **financial/** | 재무제표 서술 분석이 본질 |
| insight/ (10영역 등급) | **financial/** | 재무 비율 기반 등급 산출 |
| analyst/ (밸류에이션) | **valuation/** | "애널리스트"가 아니라 "가치평가" |
| peer/ (피어 매핑) | **comparative/** | 기업간 비교 |
| sector/ (WICS 분류) | **comparative/** | 섹터 분류 = 비교의 기준축 |
| rank/ (시장 순위) | **comparative/** | 시장 내 상대 위치 |
| event/ (이벤트 스터디) | **comparative/** | 이벤트 전후 비교 |
| esg/ | **strategy/** | ESG = 전략/사업 분석 하위 |
| supply/ (공급망) | **strategy/** | 가치사슬/공급망 = 사업 분석 |
| watch/ (공시 변화) | **미확정** | accounting? strategy? |

### gather/는 별도 엔진
gather/는 데이터 수집 엔진이지 분석 엔진이 아니다. 현재 위치(L2) 유지.

---

## 4. 기업분석 전체 목차 (Skeleton)

바텀업 분석의 흐름: **사업 이해 → 숫자 검증 → 재무 분석 → 비교 → 추정 → 가치 → 리스크**

```
기업분석 전체 목차
│
├─ Part 1. 사업을 먼저 본다                              → strategy/ + macro/
│   ├─ 1-1. 이 회사는 무엇으로 돈을 버는가 (수익 구조)
│   ├─ 1-2. 돈을 어디서 조달하는가 (자금 구조)
│   ├─ 1-3. 조달한 돈으로 뭘 준비했는가 (자산 구조)
│   ├─ 1-4. 실제로 현금은 어떻게 흘렀는가 (현금흐름)
│   ├─ 1-5. 경쟁에서 이길 수 있는가 (경쟁 우위)
│   ├─ 1-6. 산업은 어떤 국면인가 (산업 사이클)
│   └─ 1-7. 경영진은 신뢰할 수 있는가 (지배구조/ESG)
│
├─ Part 2. 숫자를 검증한다                               → accounting/
│   ├─ 2-1. 회계 정책이 보수적인가 (이익의 질)
│   ├─ 2-2. 공시에서 무엇이 바뀌었는가 (변화 감지)
│   ├─ 2-3. 이상 신호는 없는가 (Red Flags)
│   └─ 2-4. 재무제표 3표를 읽는다 (BS/IS/CF 기본)
│
├─ Part 3. 재무를 분석한다                               → financial/
│   ├─ 3-1. 수익성 — 남기는 힘 (마진, ROE, DuPont)
│   ├─ 3-2. 안정성 — 버티는 힘 (부채, 유동성, 이자보상)
│   ├─ 3-3. 현금흐름 — 실제 돈의 흐름 (영업CF, FCF, 현금전환)
│   ├─ 3-4. 성장성 — 커지는 힘 (매출/이익 성장, CAGR)
│   ├─ 3-5. 효율성 — 자산을 돌리는 힘 (회전율, CCC)
│   └─ 3-6. 종합 등급 — 전체 건강 진단 (Insight 10영역)
│
├─ Part 4. 같은 업종과 비교한다                          → comparative/
│   ├─ 4-1. 누구와 비교할 것인가 (Peer 선정)
│   ├─ 4-2. 업종 안에서 어디에 서 있는가 (순위/벤치마크)
│   └─ 4-3. 다른 나라 같은 업종은 (글로벌 비교)
│
├─ Part 5. 미래를 추정한다                               → forecast/
│   ├─ 5-1. 매출은 어디로 가는가 (Top-line 추정)
│   ├─ 5-2. 이익은 어떻게 변하는가 (마진 시나리오)
│   ├─ 5-3. 최악의 경우는 (스트레스 테스트)
│   └─ 5-4. Pro Forma 재무제표 (추정 3표)
│
├─ Part 6. 가치를 매긴다                                 → valuation/
│   ├─ 6-1. 현금흐름 할인 (DCF)
│   ├─ 6-2. 시장이 매기는 값 (멀티플)
│   ├─ 6-3. 배당으로 보는 가치 (DDM)
│   └─ 6-4. 종합 — 목표가와 투자의견
│
└─ Part 7. 리스크를 점검한다                             → risk/
    ├─ 7-1. 재무 리스크 (부실 예측, 신용등급)
    ├─ 7-2. 사업 리스크 (집중도, 규제, 기술변화)
    ├─ 7-3. 시장 리스크 (변동성, 베타, VaR)
    └─ 7-4. 통합 리스크 스코어카드
```

### 목차 원칙
- **순서 = 사고의 흐름**: 사업 이해가 먼저, 숫자 판단은 나중
- **유연성**: 항목 추가/순서 변경 가능. Part/세부 번호는 가이드일 뿐 강제 아님
- **1항목 = 1블로그 + 1기능**: 각 항목이 블로그 글 하나와 dartlab 기능 하나에 대응

### 구현 현황

| Part | 영역 | 상태 | 비고 |
|------|------|------|------|
| 1. 사업 | strategy/ | **1-1~1-4 구현 완료** | 수익구조 + 자금구조 + 자산구조 + 현금흐름 + ESG + Supply |
| 2. 검증 | accounting/ | Watch + Signal만 | 이익의 질, Red Flags 없음 |
| 3. 재무 | financial/ | **완성도 높음** | 10영역 등급 + 부실 예측 + 종합 리포트 |
| 4. 비교 | comparative/ | 구현됨 | Peer/Sector/Rank/Event |
| 5. 전망 | forecast/ | 구현됨 | OLS/시나리오/ProForma |
| 6. 가치 | valuation/ | 구현됨 | DCF/DDM/멀티플/멀티소스 |
| 7. 리스크 | risk/ | 비어있음 | insight에 흡수된 상태 |

### analysis() 14축 구현 현황 (2026-03-28 확정)

`analysis()` callable class가 strategy/ 14축을 통합 진입점으로 노출.
`src/dartlab/analysis/strategy/__init__.py`의 `_AXIS_REGISTRY`가 source of truth.

| partId | 축 | calc 함수 수 | 모듈 | 상태 |
|--------|-----|-------------|------|------|
| 1-1 | 수익구조 | 8 | strategy/revenue.py | 구현 완료 |
| 1-2 | 자금조달 | 9 | strategy/capital.py | 구현 완료 |
| 1-3 | 자산구조 | 4 | strategy/asset.py | 구현 완료 |
| 1-4 | 현금흐름 | 3 | strategy/cashflow.py | 구현 완료 |
| 2-1 | 수익성 | 5 | strategy/profitability.py | 구현 완료 (듀퐁5요소 + 마진워터폴 추가) |
| 2-2 | 성장성 | 4 | strategy/growthAnalysis.py | 구현 완료 (SGR+갭 추가) |
| 2-3 | 안정성 | 6 | strategy/stability.py | 구현 완료 (앙상블 + 부채만기 추가) |
| 2-4 | 효율성 | 3 | strategy/efficiency.py | 구현 완료 |
| 2-5 | 종합평가 | 3 | strategy/scorecard.py | 구현 완료 |
| 3-1 | 이익품질 | 4 | strategy/earningsQuality.py | 구현 완료 |
| 3-2 | 비용구조 | 4 | strategy/costStructure.py | 구현 완료 |
| 3-3 | 자본배분 | 5 | strategy/capitalAllocation.py | 구현 완료 |
| 3-4 | 투자효율 | 4 | strategy/investmentAnalysis.py | 구현 완료 |
| 3-5 | 재무정합성 | 5 | strategy/crossStatement.py + taxAnalysis.py | 구현 완료 |

### 4계층 관계

```
scan()       시장 전체 횡단 (13축)     -- 종목 간 비교/스크리닝
analysis()   단일 종목 심층 (14축)     -- 재무제표 완전 분석
c.review()   analysis -> 구조화 보고서  -- 블록-템플릿 파이프라인
c.reviewer() review + AI 해석          -- 섹션별 종합의견
```

- scan/analysis/review/reviewer 어느 하나를 수정하면 README 해당 섹션도 즉시 동기화
- analysis 축 추가/제거 시 `_AXIS_REGISTRY` + README 테이블 + 이 DEV.md 동시 반영

---

## 5. 실무 프레임워크 매핑

| 실무 체계 | 기업분석 영역 매핑 |
|----------|-------------------|
| 증권사 리포트 | 기업개요→[1], 산업→[8], 실적→[3]+[7.4], 추정→[4], 밸류→[5], 리스크→[6] |
| McKinsey Valuation | 가치창출원칙→[3] ROIC, 재구성→[2]+[3.5], 미래→[4], DCF→[5] |
| S&P/Moody's | 사업위험→[1]+[8], 재무위험→[3]+[6], 수정요소→[1.3]+[1.4] |
| PE 실사 | 재무DD→[2]+[3], 상업DD→[1]+[8], 법률/세무DD→[6.5] |
| CFA FSA | [2]+[3] 전체 |
| CFA Equity | [1]+[4]+[5]+[7] 통합 |

---

## 6. 공통 패턴

모든 모듈은 다음 구조를 따른다:

```
analysis/{영역}/
├── __init__.py      # public API export
├── spec.py          # 메타데이터 (buildSpec())
├── types.py         # 타입 정의
└── [로직 파일들]
```

---

## 7. Company 부착

| 진입점 | Company 노출 | 설명 |
|--------|-------------|------|
| **analysis** | `c.analysis()`, `c.analysis("축")` | 14축 재무분석 (method) |
| **review** | `c.review()`, `c.review("섹션")` | 구조화 보고서 (method) |
| **reviewer** | `c.reviewer()`, `c.reviewer(guide="...")` | review + AI 해석 (method) |
| sector | `c.sector`, `c.sectorParams` | property |
| insight | `c.insights` | property |
| rank | `c.rank` | property |
| esg | `c.esg` | property |
| supply | `c.supply` | property |
| event | `c.eventStudy()` | method |
| watch | `c.watch()` | method |
| peer | `c.peers`, `c.peerConsensus` | property |

모든 부착은 lazy import -- Company 초기화 시 로드되지 않음.

### 루트 공개 API

```python
dartlab.analysis()                    # 14축 가이드
dartlab.analysis("수익구조", c)        # 삼성전자 수익구조 분석
dartlab.scan()                        # 13축 가이드
```

`dartlab.analysis`는 `dartlab.__init__.py`의 `__getattr__`에서 lazy 생성 (scan과 동일 패턴).

---

## 8. 토론 기록

### 2026-03-26 — analysis 구조 재설계

**문제 인식:**
- analysis/ 10개 엔진이 철학 없이 기능별로 쌓였다
- 기업분석 방법론 8대 영역과 매핑이 안 된다
- 엔진 명칭이 실제 역할과 안 맞음 (research ≠ 조사, analyst ≠ 전체 분석)

**결정:**
1. 기업분석 8대 영역 체계 확립 (Palepu-Healy + CFA + McKinsey + S&P + PE 교차)
2. analysis/ 폴더를 8대 영역 기반으로 재편 (8개 폴더)
3. 기존 10개 엔진을 새 8개 영역에 이전
4. 지금이 적기 — README에서 이미 불안정 명시, 안정화 전

**핵심 판단:**
- gather/는 수집 엔진이지 분석 엔진이 아니다 → 별도 유지
- analyst는 가치평가를 하는 엔진이지 "애널리스트"가 아니다 → valuation/
- research는 재무제표 서술 분석이지 "리서치"가 아니다 → financial/
- 기존 기능을 억지로 끼워맞추지 않고, 백지에서 8대 영역 위에 재배치

**미확정:**
- watch/의 정확한 이전 위치
- insight/를 financial/ 안에 통합할 때의 구체적 구조
- narrative(서술 생성)가 financial/ 안인가, 8대 영역 위의 통합 레이어인가
- 각 영역별 공개 API 설계
- 마이그레이션 실행 순서와 호환성 전략

### 2026-03-26 — 장기 청사진 수립

**결정:**
- 기업분석 전체 목차(Skeleton) 7 Part, 25개 항목 확정 (§4 참조)
- 바텀업 흐름: 사업 → 검증 → 재무 → 비교 → 추정 → 가치 → 리스크
- 블로그-기능 사이클: 1항목 = 1블로그 + 1dartlab 기능
- Wave 1(사업을 먼저 본다)부터 시작 — 현재 가장 약한 strategy/ 강화

**Part 1 "자본의 여정" 도입:**
- 사용자 제안: "재무제표 볼 때 자금조달 구조에서 시작 → 뭘 준비했고 → 돈을 어떻게 버는지"
- 조사 결과: McKinsey ROIC + Penman Reformulation + DuPont 역순 읽기와 일치
- 주류(Palepu-Healy, CFA, Buffett)는 사업 이해에서 시작 → Part 1 "사업을 먼저 본다" 유지
- 1-1(수익 구조) 뒤에 1-2(자금) → 1-3(자산) → 1-4(현금흐름) "자본의 여정" 흐름 삽입
- Part 1이 5항목 → 7항목으로 확장

---

## 9. 블로그-기능 사이클

### 구조

```
목차 항목 선택 → 블로그 글 작성 → 대응 기능 구현 → 블로그에 코드 예시 추가 → 다음 항목
```

### 시리즈

- **시리즈명**: `corporate-analysis` (기업분석 방법론)
- **카테고리**: `03-financial-interpretation`
- 각 블로그 글: 개념 설명 → 공시에서 어디를 보는가 → dartlab으로 어떻게 확인하는가
- 기능이 먼저 구현된 후 블로그에서 참조 (블로그가 기능보다 먼저 나가지 않음)

### 기능-목차 매핑

| 목차 | 영역 | 필요한 작업 |
|------|------|-----------|
| 1-1 수익 구조 | strategy/ | **상세: `strategy/_01_revenueStructure.md`** |
| 1-2 자금 구조 | strategy/ | 자본 구조(부채/자본 비중), 조달원 분석 |
| 1-3 자산 구조 | strategy/ | 투하자본 구성, 유무형자산 비중, CAPEX 패턴 |
| 1-4 현금흐름 | strategy/ | CF 3구간, FCF, 이익의 현금 뒷받침, CF 패턴 |
| 1-5 경쟁 우위 | strategy/ | 경쟁 포지셔닝, 진입장벽, 마진 지속성 |
| 1-6 산업 사이클 | macro/ | gather/fred 활용, 산업 단계 판별 |
| 1-7 지배구조/ESG | strategy/ | 현재 수준 유지 (esg/ 이미 있음) |
| 2-1 이익의 질 | accounting/ | Beneish M-Score 분리, accrual quality |
| 2-3 Red Flags | accounting/ | 감사 의견, 정정 공시, 이상 패턴 종합 |
| 3-1~3-6 재무분석 | financial/ | 기존 insight/ 세분화 노출 |
| 7-1~7-4 리스크 | risk/ | insight의 risk/distress를 risk/로 분리 독립 |

---

## 10. 실행 우선순위

| Wave | Part | 이유 |
|------|------|------|
| **Wave 1** | Part 1 — 사업을 먼저 본다 | 바텀업의 출발점. 현재 가장 약함 |
| **Wave 2** | Part 2 — 숫자를 검증한다 | 사업 이해 후 자연스러운 다음 단계 |
| **Wave 3** | Part 3 — 재무를 분석한다 | 이미 구현 높음. 블로그 대응 위주 |
| **Wave 4** | Part 4-6 — 비교/추정/가치 | 기능 있음. 블로그 연동 |
| **Wave 5** | Part 7 — 리스크 | risk/ 독립화 |

---

## 11. 데이터 접근 규칙

> analysis/의 모든 코드는 이 규칙을 따른다. 접근은 무조건 쉬워야 한다.

### 데이터 3계층

| 계층 | 대상 | 접근 방식 |
|------|------|----------|
| **원본** | sections에 있는 모든 것 (BS/IS/CF/segments/report topics 등) | `company.select(topic)` 경유 |
| **파생 편의** | 원본에서 계산된 속성 (ratios, sector, insights 등) | 직접 접근 OK |
| **외부** | sections에 없는 것 (주가, 컨센서스, 수급, 거시, 뉴스) | gather 경유, analyze 함수에서만 |

### 함수 2계층

**calc 함수** (개별 계산: `calcSegmentComposition`, `calcLiquidity` 등)
- `company.select(topic)` ✅ 기본 경로 — sections에 모든 게 있으니 웬만하면 이걸 쓴다
- `company.finance.ratios` ✅ (파생 편의)
- `company.finance.ratioSeries` ✅ (파생 편의 — 시계열)
- `company.sector`, `company.corpName` ✅ (메타)
- `company.report.*` / `company.docs.*` — 직접 접근 가능하나, select 경유가 기본
- `from dartlab.gather import` ❌

**analyze 함수** (종합 파이프라인: `pipeline.analyze()`, `Analyst.report()` 등)
- calc의 모든 것 + gather + Series 허용
- gather는 DI(의존성 주입) 패턴

### 허용/금지 요약

| 접근 | calc | analyze | 이유 |
|------|------|---------|------|
| `company.select("IS", ["매출액"])` | ✅ | ✅ | 원본 — 기본 경로 |
| `company.select("segments")` | ✅ | ✅ | 원본 — 기본 경로 |
| `company.finance.ratios.roe` | ✅ | ✅ | 파생 편의 |
| `company.finance.ratioSeries` | ✅ | ✅ | 파생 편의 (시계열) |
| `company.sector` | ✅ | ✅ | 메타 |
| `company.report.audit` | ⚠️ | ✅ | 접근 가능하나 select("audit") 권장 |
| `company.docs.sections` | ⚠️ | ✅ | 접근 가능하나 select 경유 권장 |
| `from dartlab.gather import Gather` | ❌ | ✅ | 외부 데이터 |
| `buildAnnual(stockCode)` (Series) | ❌ | ✅ | analyze 내부 구현 |

### 확장 규칙

select로 원본 접근이 안 되는 데이터가 필요하면:
- show()에 topic 추가
- 기존 topic의 sub-topic 추가
- **새 래퍼/헬퍼 함수를 만들지 않는다. 하위 레이어(show/sections)를 확장한다.**

---

## 12. review 테이블 규칙

### 컬럼은 무조건 시계열

review에 등장하는 모든 TableBlock의 **컬럼은 기간(period)**이다. 행이 항목, 열이 시간.

```
올바른 형태:
              2025Q4    2024Q4    2023Q4    2022Q4    2021Q4
자본총계      23.6조    21.6조    19.9조    17.2조    15.2조
이익잉여금    12.1조    12.8조    12.3조    10.5조     8.5조

금지하는 형태:
항목          값
자본총계      23.6조
이익잉여금    12.1조
```

이유:
- dartlab의 핵심 철학은 **기간 비교**다. 스냅샷 한 장은 의미가 없다.
- sections가 topic x period 수평화인 것과 같은 원리.
- 사용자가 "이 숫자가 늘었나 줄었나"를 테이블에서 바로 읽을 수 있어야 한다.

### 적용 범위
- calc 함수의 반환값: history/timeline은 `[{period, ...}, ...]` 형태로 시계열 포함
- builders.py의 TableBlock 생성: 행=항목, 열=기간으로 피벗
- MetricBlock은 최신 스냅샷 OK — 테이블이 아니라 요약 지표이므로 예외

---

## 13. 재무제표분석 강화 기록 (2026-03-29)

### 배경

analysis 14축의 재무분석 영역(수익성/성장성/안정성/투자효율)에 6개 기능을 시도.
기능 동작 여부가 아니라 **분석에 실제 도움이 되는가**를 5개 섹터(제조/자동차/IT/금융/바이오)로 검증.

### 검증 대상

삼성전자(005930), 현대차(005380), NAVER(035420), 미래에셋증권(006800), 셀트리온(068270)

### 현재 배치된 기능 (5개)

| 기능 | 모듈 | 판단 근거 |
|------|------|----------|
| **듀퐁 5요소 분해** | profitability.py | 3/5에서 interestBurden 편차 >5%p. NAVER 0.49(금융비용이 수익 절반 잠식), 셀트리온 1.254(이자수익이 오히려 플러스), 미래에셋 0.906. 제조업(삼성/현대)은 3요소와 거의 동일 — IT/금융/바이오에서 가치 |
| **마진 워터폴** | profitability.py | 매출→순이익 각 단계의 비율(%) 분해. NAVER: 영업19%→세전9% 급락이 즉시 보임. 숫자 나열로는 못 잡는 패턴을 직관적으로 제공 |
| **SGR + 갭** | growthAnalysis.py | SGR(=ROE x 유보율) 단독은 곱셈일 뿐 — 실제 매출성장률과의 gap을 추가하여 가치 확보. 삼성 gap +19.8%p(외부자본 필요), 현대 0.0(균형), 미래에셋 +48.8%p(급격한 외형 확장) |
| **부실예측 앙상블** | stability.py | Altman Z/Z'', Ohlson O, Springate S, Zmijewski X 다수결. 현대차: Z-Score 단독은 "위험"이나 앙상블은 "주의"(O-Score, X-Score가 safe) — 단일 모델 오판 보정 |
| **부채 만기 구조** | stability.py | 단기/장기 차입금 비율 + 차환리스크. 업종별 계정 3단 fallback(단기차입금→차입부채→유동금융부채). 셀트리온: 단기 95%, 차환리스크 6.87배 — 부채비율만으로는 절대 못 잡는 위험 |

### 시도 후 제거한 기능 (1개)

| 기능 | 이유 |
|------|------|
| **동적 WACC 추정** | CoD(차입비용률): IS에 `이자비용` 별도 계정이 없는 기업이 대부분. `금융비용`은 환차손/파생손실 포함이라 순수 Kd 추정 불가. 삼성 17%, NAVER 15.6% → 비현실적. 6% clamp 적용해도 3/5가 fallback 5%. CoE: Beta=1.0 고정이라 기업 간 차이 없음. **핵심값(Kd, Beta) 모두 fallback이면 "동적"이라 부를 수 없다.** 품질 게이트 5번 위반. ROIC 단독으로 변경, EVA도 NOPAT+투하자본으로 단순화 |

### WACC 제거 시 연쇄 수정

- `calcRoicTimeline`: spread/wacc 필드 제거, ROIC만 반환
- `calcEvaTimeline`: WACC 의존 제거, NOPAT + 투하자본 + nopatReturn만 반환
- `calcInvestmentFlags`: "ROIC < WACC" 플래그 → "ROIC 3년 연속 저수익" 플래그로 변경
- `scorecard._calcInvestmentGrade`: spread 기반 → ROIC 절대값 기반(>15 A, >10 B, >5 C, >0 D, F)
- `_estimateWacc`, `_fetchRiskFreeRate`, `_getRiskFreeRate` 전체 제거

### Kd 추정 시도 과정 (참고)

1. **1차**: `금융비용` / 총차입금 → 삼성 17%, NAVER 15.6% (금융비용에 비이자 항목 포함)
2. **2차**: `이자비용` 우선, `금융비용` fallback → 대부분 기업의 IS에 이자비용 별도 계정 없음
3. **3차**: `금융비용` 소스에 6% 상한 clamp → 상한에 걸리면 오히려 fallback과 동일
4. **결론**: 한국 K-IFRS 공시 구조에서 순수 이자비용을 안정적으로 추출할 수 없음. `interestCoverage`도 None인 경우 다수. 향후 Beta/Kd를 실제로 구할 수 있을 때(gather 확장, 주가 기반 Beta) 재도입 검토

### 스토리 기반 재설계 (2026-03-29 후반)

**문제**: 2-1(수익성)~2-4(효율성)가 전부 `getRatioSeries()` → `buildTimeline()` 래핑.
비율 수치만 나열할 뿐 원본 금액이 없어서, 스토리(규모감 + 방향 + 3표 교차)를 볼 수 없었다.
1-1~1-4(revenue, capital, asset, cashflow)는 이미 `company.select()` 기반 스토리 패턴.

**해결**: 4개 모듈 전부 `company.select("IS"/"BS"/"CF", [...])` + `toDict()` 패턴으로 재설계.

| 모듈 | Before | After |
|------|--------|-------|
| **profitability.py** | ratioSeries로 margin% 나열 | select("IS") 원본 금액 + 마진 + YoY. 듀퐁은 IS+BS에서 직접 계산 |
| **growthAnalysis.py** | ratioSeries로 성장률 나열 | select("IS")+select("BS") 금액 + YoY + CAGR. SGR도 select 기반 |
| **efficiency.py** | ratioSeries로 회전율 나열 | select("IS")+select("BS") 매출채권/재고/매입채무 금액 + 회전율 + CCC |
| **stability.py** | ratioSeries로 비율 나열 | select("BS") 부채/자본/현금 금액 + 비율. Z-Score BS/IS에서 직접 5변수 계산 |

**추가 수정**:
- `toDict()` 호출 시 `maxPeriods` 제한 제거 — 분기 전용 기업(셀트리온 등)에서 Q4가 부족해지는 문제 해결
- `calcDistressScore`: 시가총액(X4) 없을 때 Altman Z'' (4변수) 자동 fallback
- `calcStabilityFlags`: 부채 3기 연속 증가 플래그 추가

**5섹터 검증 결과** (삼성/현대/NAVER/셀트리온/미래에셋):
- 5기 시계열 확보 (분기 전용 기업 포함)
- 금액 기반으로 규모감 확인 가능: 삼성 매출 93.8조, 현대 46.8조
- 교차 분석 가능: 삼성 SGR gap +19.8%p(성장이 내부 역량 초과), 현대 영업률 3기 연속 하락 + Z-Score 회색
- unit 1051 passed, 0 failed

### 품질 게이트

이 작업에서 확립한 analysis calc 함수 배치 기준 (메모리에도 기록):

1. 숫자가 나온다 != 분석에 도움이 된다
2. 최소 3개 이상 다른 업종으로 검증
3. "이 숫자가 있으면 없을 때 대비 어떤 판단이 달라지는가?" 답 못 하면 불필요
4. 데이터 부족 시 포기가 아니라 해결책 탐색
5. fallback이 핵심값이면 가치 없음 — 제거하거나 개선
