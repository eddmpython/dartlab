# Analysis 엔진 — 기업분석 방법론 체계

> 이 문서는 analysis 엔진의 철학, 구조, 방법론 체계를 기록한다.
> 토론을 통해 점진적으로 확정한다.

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

## 4. 8대 영역 상세

(상세 방법론은 research/DEV.md에 기록)

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

## 7. Company 부착 (현재 — 마이그레이션 시 경로 변경 필요)

| 모듈 | Company 노출 | 타입 |
|------|-------------|------|
| sector | `c.sector`, `c.sectorParams` | property |
| insight | `c.insights` | property |
| rank | `c.rank` | property |
| esg | `c.esg` | property |
| supply | `c.supply` | property |
| event | `c.eventStudy()` | method |
| watch | `c.watch()` | method |
| analyst | 별도 `Analyst()` 클래스 | standalone |
| peer | `c.peers`, `c.peerConsensus` | property |
| research | 별도 `research()` 함수 | standalone |

모든 부착은 lazy import — Company 초기화 시 로드되지 않음.

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
