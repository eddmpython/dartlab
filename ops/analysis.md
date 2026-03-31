# Analysis

재무제표를 구조화된 스토리 데이터로 변환한다.
Company → Analysis → Review → AI 순서로 계층이 쌓인다.
analysis 품질이 올라가면 review와 AI 품질이 동시에 올라간다.

## 재무제표 분석 스토리

review 보고서는 이 스토리 순서를 따른다. 각 질문이 하나의 섹션이다.

### 설계 근거

전통 회계는 BS(자금조달→자산) → IS(영업→수익) → CF(현금 검증) 순서.
투자 분석(McKinsey/Damodaran/CFA)은 IS(수익구조) → BS(자본구조) → CF(현금 검증).
dartlab은 투자자 관점을 채택 — "이 회사가 뭘로 돈을 버는가"가 첫 질문.

### 10개 질문 (= review 섹션 순서)

| # | 질문 | 섹션 | 핵심 지표 |
|---|------|------|----------|
| 1 | 뭘로 돈을 버는가? | 수익구조 | 부문별 매출, 집중도, 성장률, 매출 품질 |
| 2 | 번 돈이 얼마나 남는가? | 수익성 | 매출총이익률→영업이익률→순이익률, 듀퐁 분해 |
| 3 | 남은 돈이 현금으로 들어오는가? | 현금흐름 | 영업CF/순이익, FCF, CF 패턴, 이익의 현금 전환 |
| 4 | 돈의 출처와 구조는 건전한가? | 자본/부채 | 내부유보 vs 차입, 부채비율, 이자보상, 유동성 |
| 5 | 자산을 효율적으로 쓰고 있는가? | 자산/효율 | 자산 재분류, 운전자본, CAPEX, 회전율, CCC, ROIC |
| 6 | 비용은 어떻게 쓰는가? | 비용/배분 | 원가율, 판관비율, DOL, BEP, 배당, 재투자 |
| 7 | 숫자를 종합하면? | 종합평가 | 스코어카드, Piotroski, Altman Z, 이익품질, 정합성 |
| 8 | 얼마의 가치인가? | 밸류에이션 | DCF, DDM, 상대가치, RIM, 목표주가 |
| 9 | 신뢰할 수 있는가? | 비재무 | 지배구조, 공시변화, 피어 비교 |
| 10 | 앞으로 어떻게 될 것인가? | 전망 | 매출 예측, Pro-Forma, 시나리오 |

### 현행 vs 제안 순서

현행: 수익구조→**자금조달→자산→현금**→수익성→성장→안정→효율→종합→심화→밸류→비재무→전망

제안: 수익구조→**수익성→현금흐름**→자금조달→자산/효율→비용/배분→종합→밸류→비재무→전망

핵심 변경: **수익성이 수익구조 직후로 올라오고, 현금흐름이 수익성 직후로 이동.**
"돈을 벌고 → 얼마나 남고 → 현금으로 전환되는가"의 자연스러운 흐름.

## 단일 진입점

- **`dartlab.analysis()` / `c.analysis()`** 하나로 모든 축에 접근한다
- analysis()가 가이드하고 라우팅 — 개별 calc 함수는 내부 구현
- insight는 등급 카드(보조 요약) — analysis와 역할이 다르다

## 14축 체계

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

## forecast (예측)

### 예측신호 6축

| 축 | 지표 예시 |
|------|------|
| 원자재 가격 | 구리, 알루미늄, 유가, 금속PPI, 밀, 면화 |
| 산업생산 | 반도체, 자동차, 화학, 식품, INDPRO |
| 실물수요 | 자동차판매, 내구재, 화물운송, 설비가동률 |
| 금융조건 | 금리, 하이일드 스프레드, 회사채 |
| 내수경기 | IPI, 서비스업, BSI, 아파트가격 |
| 환율 | 원/달러, 원/엔, 원/위안 |

- 143개 업종 매핑, 95.5% 커버리지
- 방향 정확도: 평균 66%, lag=1분기 선행 시 49%가 70%+
- **GDP는 영구 제외** — 기업 매출의 직접 외생변수가 아님
- 천장(62~66%)은 모델 구조로 못 뚫음 — 변수 차원 변경 필요

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
| `src/dartlab/analysis/financial/` | 14축 calc 함수 |
| `src/dartlab/analysis/financial/insight/` | grading + spec |
| `src/dartlab/analysis/financial/research/` | 리서치 (predictionSignals) |
| `src/dartlab/analysis/forecast/` | simulation, 예측 |
| `src/dartlab/analysis/valuation/` | DCF, DDM, 상대가치 |
| `src/dartlab/core/finance/exogenousAxes.py` | 6축 28개 지표 업종 매핑 |
