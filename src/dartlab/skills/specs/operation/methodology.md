---
id: operation.methodology
title: 검증 방법론 (credit · forecast · search · ai)
kind: curated
scope: builtin
status: observed
category: operation
purpose: dartlab 분석 엔진이 주장하는 수치의 근거와 한계를 공개한다. credit · forecast · search · ai 각 엔진의 검증 방법, 표본 구성, 정확도 정의, 시도했지만 효과 없던 접근까지 투명하게 기록한다.
whenToUse:
  - dartlab 정확도 주장 근거 확인
  - credit / forecast / search / ai 검증 표본 확인
  - 정량 모델의 한계와 비-적중 케이스 분석
  - 외부 사용자가 신뢰성 평가
  - 시도했지만 효과 없던 접근 (negative results) 확인
inputs:
  - 검증할 엔진 (credit · forecast · search · ai)
  - 표본 정의
outputs:
  - 적중률 / precision / 정확도
  - 한계 명시
  - 재현 가능한 코드 경로
toolRefs:
  - operation.stability
  - operation.testing
sourceRefs:
  - dartlab://skills/operation.methodology
  - https://github.com/eddmpython/dartlab
requiredEvidence:
  - 표본 구성
  - 적중 정의
  - 한계 명시
  - executionRef
  - sourceRef
expectedOutputs:
  - 엔진별 검증 결과
  - 비-적중 원인 분석
  - 재현 코드 위치
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
    status: supported
procedure:
  - 검증할 엔진 결정 (credit · forecast · search · ai).
  - 해당 엔진의 표본과 적중 정의 확인.
  - 정확도 / 적중률 수치 인용 시 한계와 함께 명시.
  - 재현 필요시 코드 경로 (`tests/` 또는 `src/dartlab/{engine}/`) 직접 확인.
failureModes:
  - 적중률만 인용하고 한계 또는 비-적중 원인 누락
  - 표본 정의 없이 정확도 단정
  - 정량 모델 한계 영역 (FCF 음수 · 정성 요소) 을 정량으로 답변
forbidden:
  - 표본 정의 없이 정확도 수치를 단정하지 않는다.
  - 외부 신용평가의 정성 요소 (시스템적 중요성 등) 를 정량 모델이 100% 일치한다고 주장하지 않는다.
  - 비-적중 케이스를 숨기지 않는다.
examples:
  - dartlab 신용 분석 정확도 근거
  - 매출 예측 정확도 어떻게 측정하나
  - 공시 검색이 임베딩 없이 왜 95% 인가
  - AI 도구 선택 검증 결과
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-06"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

dartlab 분석 엔진이 주장하는 수치의 근거. 각 엔진이 무엇을 · 어떻게 · 얼마나 검증했는지 투명하게 공개한다.

## Credit — 독립 신용분석

### 방법

외부 신용평가사 (한국기업평가 · NICE신용평가 · 한국신용평가) 등급과 dartlab dCR 등급을 비교. **적중**은 동일 등급 또는 ±1 노치 이내.

### 표본

| 표본 | 적중률 | 비고 |
|---|---|---|
| 30 개사 (대기업) | **87%** (26/30) | 정확 일치 10 개+ |
| 50 개사 (중대형) | **82%** (41/50) | |
| 79 개사 (전체) | **70%** (55/79) | v5.0 과대평가 수정 후 재측정 예정 |

### 비-적중 원인 분석

- **정량 한계 (3 개)**: 삼성SDI · 고려아연 · 현대제철 — FCF 음수 / CAPEX 집약 기업. 외부 등급은 "미래 성장성" 을 정성으로 반영하지만, dartlab 은 정량만 사용한다.
- **금융 한계 (1 개)**: KB금융 — AAA 는 "시스템적 중요 은행" 정성 반영. 정량만으로 AAA 도달 불가.
- **주가 일시 (1 개)**: SKT — CHS 주가 급락 보정으로 하향됐다가 보호 규칙으로 복원.

### 한계

- 외부 등급 자체가 정성을 포함하므로 정량 모델이 100% 일치 불가.
- 금융업 (은행 · 증권 · 보험) 은 재무제표 구조가 달라 별도 트랙. 정성 요소 (시스템적 중요성) 미반영.
- 표본 79 개사는 한국 상장사 중 신평 등급 존재 기업. 비등급 기업 검증 불가.

## Forecast — 매출 방향 예측

### 방법

Walk-forward 검증. 과거 데이터로 다음 분기 매출 방향 (상승 / 하락) 예측 → 실제 결과와 비교. **각 시점에서 과거 데이터만으로 예측**하므로 과적합 불가능 구조.

### 수치

| 조건 | 정확도 | 관측치 | 커버리지 |
|---|---|---|---|
| 모멘텀 단독 | 72.1% | 4,825 건 | 100% |
| 2 연속 모멘텀 | 74.7% | 360 건 | 69% |
| 모멘텀 + 영업이익률 일치 | 76.1% | 3,660 건 | 76% |
| 모멘텀 + OLS 일치 | 77.7% | 355 건 | 68% |

### 방법론 핵심

- **사전확률**: 40 개 업종별 모멘텀 지속률 (4,800 건+ 실측에서 도출).
- **베이즈 갱신**: 2 연속 모멘텀, 영업이익률 수준, OLS 외생변수 일치/불일치로 순차 갱신.
- **감쇠**: 신호 간 독립성 위반 보정 (damping=0.3).
- **재보정**: 원시 확률을 실측 기반 재보정 (shrinkage=0.6).

### 시도했지만 효과 없던 것

| 시도 | 결과 | 판단 |
|---|---|---|
| Logistic Regression | +0.8%p | 모델 구조 변경 무의미 |
| 한국 PPI 13 개 추가 | 하락 | 가격 &lt; 생산량 (가격 영향이 생산량 영향보다 약함) |
| 11 신호 다수결 앙상블 | 61% | static 신호 = 상수 바이어스 |
| GDP | 기업 매출의 직접 외생변수 아님 | 영구 제외 |

### 정확도를 올리려면 새 데이터가 필요

현재 방법론 내에서의 개선은 천장에 도달. 추가 개선은 새 데이터 소스 (검색량 · 관세청 수출입 · 컨센서스 리비전) 에 의존.

### 학술 근거

- 나이브 베이즈 + 감쇠: van Calster et al. (2021) — 소표본 과적합 방지.
- M4/M5 Competition: 단순 방법 > 복잡한 ML (100,000 시계열).
- Sloan 1996: 이익 지속성 → 모멘텀의 이론적 기반.

## Search — 공시 원문 검색 (beta)

> 인덱스 신선도 한계 — 매일 증분 자동화 미완성. 단일 종목 공시는 `Company.filings` / `liveFilings` 권장.

### 방법

20 개 테스트 쿼리 (공식 용어 + 비공식 표현 혼합) 에 대해 상위 5 건의 관련성을 수작업 평가.

### 수치

| 방법 | precision@5 | cold start | 속도 |
|---|---|---|---|
| **dartlab (Ngram + BM25F)** | **95%** | **0ms** | **1ms** |
| Trigram 단독 | 88% | 0ms | 1ms |
| 임베딩 (ko-sroberta) | 83% | 12,700ms | 58ms |
| BM25 (FTS) | 71% | 0ms | 14ms |

대규모 (400 만 문서) 검증: 인덱스 빌드 218 초, 검색 140ms.

### 왜 임베딩 없이 되는가

DART 공시는 법적 정형 문서다. 공시 유형이 257 개로 고정되고, 용어가 법률로 규정되어 같은 의미를 다른 단어로 표현하지 않는다. 따라서 단어 자체가 의미를 완전히 표현하고, ngram 정확 매칭이 의미 유사도 기반 검색보다 정밀하다.

## AI — 적극적 분석가

### 방법

60 개 이상의 실제 분석 질문을 AI 에게 던지고, 첫 시도에 올바른 도구 선택 + 유의미한 해석을 생성하는지 확인.

### 수치

- 도구 선택 정확도: 95%+ (첫 시도 성공).
- 검증 질문 유형: 개별 기업 분석 · 매크로 환경 · 시장 비교/순위 · 데이터 직접 조회 · 실시간 이슈.

### 한계

- 평가 셋이 개발자 본인이 구성하고 평가. 독립 제3자 평가가 아님.
- "유의미한 해석" 의 기준이 주관적. 정량적 해석 품질 지표는 아직 없음.
- provider 별 (gemini · groq · cerebras 등) 성능 차이는 별도 체계적 비교 미실시.

## 공통 원칙

- **코드가 곧 방법론**: 모든 검증 로직은 코드로 재현 가능.
- **실패도 기록**: 시도했지만 효과 없던 접근을 명시 기록.
- **한계를 숨기지 않는다**: 정량 모델의 구조적 한계 · 표본 제약 · 주관적 평가 기준을 공개.

## 다음 단계

- [operation.stability](/skills/operation.stability) — API tier 와 deprecation 정책.
- [operation.testing](/skills/operation.testing) — 테스트 규칙.
- [engines.credit](/skills/engines.credit) — 신용 분석 엔진 (creditRisk 응용 포함).
- [engines.analysis](/skills/engines.analysis) — 분석 엔진 (revenueForecast axis 포함).
