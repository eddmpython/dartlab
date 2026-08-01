---
id: engines.credit.methodology
title: Credit Methodology — 등급 결정 사상·알고리즘·audit SSOT
category: engines
kind: curated
status: observed
purpose: dartlab credit 엔진의 등급 결정 사상 · 알고리즘 · audit 규칙 SSOT. 공시 재무제표 + 주석 + 사업보고서 + 시장 데이터 로 정량 신용등급 산출 (신평사 비공개 면담 0).
sourceRefs:
  - dartlab://skills/engines.credit.methodology
knowledgeRefs:
  - engines.credit
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
whenToUse:
  - dartlab credit 등급 결정 사상 확인
  - 7 축 가중치 audit
  - 신평사 등급 차이 분석
---

## 엔진 역할

dartlab 은 공시 데이터만으로 재현 가능한 독립 신용분석을 수행한다. 신평사의 비공개 면담 없이도, 공시 재무제표 + 주석 + 사업보고서 + 시장 데이터로 제도권에 준하는 정량 신용등급을 산출하고, 그 과정을 100% 투명하게 공개한다.

본 sub-spec 은 등급 결정 사상 · 알고리즘 · audit 규칙 SSOT. 외부 사용자 API 는 `engines.credit` SKILL 참조.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 1. 무인자 → 가이드 DataFrame (axis | label | description | example)
print(c.credit())

# 2. 종합 등급
c.credit("등급")                # → dict (grade, healthScore, score, ...)
c.credit("등급", detail=True)   # 7 축 narrative + 지표 시계열 풀

# 3. 축별 분석
c.credit("채무상환")            # 한글 alias
c.credit("repayment")           # 영문 alias

# 4. 신용 관점 리포트 (story 엔진이 조립)
c.story(type="credit")          # 신용 섹션 narrative + 등급 + 지표 시계열
```

다른 분석 엔진 (analysis / macro / quant / scan) 도 동일 패턴 — 무인자 → 가이드, "축이름" → 분석.

## 호출 동작

| 항목 | 내용 |
|------|------|
| 레이어 | L2 (analysis / scan / notes / gather 소비) |
| 진입점 | `c.credit()` · `c.credit("등급")` · `c.credit("채무상환")` |
| 소비 | Company 전체 (finance · notes · docs · report) · scan · gather — analysis 와 독립 |
| 생산 | 신용분석 보고서 · 등급 이력 · audit 결과 · 정례 보고서 |
| 핵심 | 재현 가능성 + 투명성 + 지속 발전 |

## 사상 — 왜 독립 신용분석인가

**제도권 신평사 한계**:
- 발행자 지불 (issuer-paid) 모델 → 이해충돌
- 방법론 핵심 파라미터 비공개 → 블랙박스
- 2008 금융위기 — 서브프라임 MBS 에 AAA 부여 → 신뢰 실추
- 한국 — 3 사 과점, 등급 인플레이션 논란

**dartlab 의 답**:
- 투자자 지불도 발행자 지불도 아닌 **오픈소스** → 이해충돌 구조적 제거
- 모든 파라미터 · 가중치 · 기준표 100% 공개 → 누구든 재현 가능
- 코드가 곧 방법론 → 코드 읽으면 등급 근거 이해
- 공시 데이터만 사용 → 비공개 정보 없이도 동작

## 철학 5 대 원칙

### 1. 재현 가능성 (Reproducibility)

같은 입력 → 같은 등급. 예외 없음.

- 모든 계산 결정론적 (deterministic) — 랜덤 요소 없음
- 입력 — 공시 재무제표 + 주석 + 사업보고서 + 시장 데이터 (모두 공개)
- 누구든 `dartlab.credit("005930")` 실행하면 같은 등급
- 정성 조정도 코드화된 규칙으로만 — "분석가 판단" 블랙박스 없음

### 2. 투명성 (Transparency)

등급 모든 근거 공개.

- 등급 보고서에 모든 축 점수 · 지표값 · 기준표 명시
- "왜 이 등급인가" 완전한 답
- 신평사 등급과 다르면 **왜 다른지** 근거 명시 (동의/비동의)
- 방법론 변경 시 변경 사유 + 영향 받는 기업 목록 공개

### 3. 보수주의 (Conservatism)

의심스러우면 낮게.

- 데이터 없으면 None (추정 금지) — 그 축 점수에서 제외 + "미평가" 명시
- 캡티브 금융 (현대차) · 지주사 (LG) 등 구조적 왜곡은 감지하되 상향 조정하지 않음
- 정량 확인 불가 "계열 지원" · "정부 보증" 등급에 반영하지 않음
- 대신 보고서에 "정량 등급 BB+ / 계열 지원 감안 시 AA 가능성" 형태로 병기

### 4. 지속 발전 (Continuous Improvement)

audit 가 엔진을 발전시킨다.

- 매 보고서 발행 후 실제 등급과 대조 → 오차 원인 분석 → 엔진 개선
- 부도 사건 발생 시 dartlab 이 사전 포착했는지 역추적
- 등급 전이 매트릭스 장기 축적 → 모델 정확도 실증
- 방법론 버전 관리 (v1.0 → v1.1 → ...) — 버전별 정확도 추적

### 5. 독립성 (Independence)

dartlab 신용등급은 dartlab 만의 판단.

- 신평사 등급을 "정답" 으로 보지 않음 — 참고 only
- 신평사와 다를 수 있고, 다를 때 왜 다른지 설명
- "신평사가 AA 라서 우리도 AA" — 금지. 모든 등급 자체 산출
- 일치율은 "정확도" 가 아니라 "상관관계"

## 등급 체계 — dartlab Credit Rating (dCR)

### 등급 구조 (20 단계 + eCR + Outlook)

```
투자적격:  dCR-AAA, dCR-AA+, dCR-AA, dCR-AA-, dCR-A+, dCR-A, dCR-A-,
          dCR-BBB+, dCR-BBB, dCR-BBB-
투기등급:  dCR-BB+, dCR-BB, dCR-BB-, dCR-B+, dCR-B, dCR-B-
부실:      dCR-CCC, dCR-CC, dCR-C, dCR-D
```

- `dCR-` prefix 로 제도권 등급과 구분 (규제 리스크 회피)
- 현금흐름등급 eCR-1 (최상) ~ eCR-6 (최하) 별도 부여
- 등급 전망 — 안정적 / 긍정적 / 부정적

### PD Calibration 근거

dCR 의 등급-부도확률 (PD) 매핑은 KIS (한국기업평가) 1998-2024 실측 부도율 + S&P Global Default Study (1981-2024) 교차 참조.

| 등급 | dartlab PD(1Y) | 참고 — KIS 실측 | 참고 — S&P 글로벌 |
|------|:---:|:---:|:---:|
| AAA | 0.00% | 0.00% | 0.00% |
| AA+ | 0.01% | ~0.02% | ~0.02% |
| AA | 0.02% | ~0.03% | ~0.03% |
| AA- | 0.03% | ~0.04% | ~0.04% |
| A+ | 0.04% | ~0.05% | ~0.05% |
| A | 0.06% | ~0.06% | ~0.06% |
| A- | 0.08% | ~0.08% | ~0.07% |
| BBB+ | 0.15% | ~0.12% | ~0.13% |
| BBB | 0.25% | ~0.20% | ~0.22% |
| BBB- | 0.40% | ~0.35% | ~0.32% |
| BB+ | 0.75% | ~0.60% | ~0.53% |
| BB | 1.50% | ~1.20% | ~0.93% |
| B | 7.00% | ~5.50% | ~3.72% |

**방법론**:
- 투자적격 (AAA~BBB-) — KIS 장기 실측. 한국 시장은 AAA/AA 기업 실제 부도 경험 0 건 가까워 이론 PD 매우 낮음.
- 투기등급 (BB~D) — 한국 시장은 S&P 글로벌 대비 부도율 높은 경향. 보수 설정.
- CHS 모델 (Campbell 2008) PD 산출은 등급 보정용 only, 등급-PD 매핑과 별개 동작.

### 4 Layer 등급 결정 파이프라인

```
[Layer 1] 오리지널 정보 수집 — credit 엔진이 직접 수행
    │
    ├── 재무제표 원본 (BS/IS/CF) ← company.select()
    ├── 주석 상세 (차입금/충당부채/리스/부문/원가) ← company.notes
    ├── 구조화 감사의견 (adt_opinion + 회계연도 + 접수번호) ← company._report.audit
    ├── 사업보고서 텍스트 (사업내용/우발부채) ← company.panel()
    ├── 시장 데이터 (주가/변동성/시가총액) ← gather
    ├── 거시지표 (금리/스프레드/환율) ← gather.macro
    └── 횡단 비교 (업종 내 순위) ← scan
    │
    ▼
[Layer 2] 7 축 정량 스코어링
    │
    ├── 축 1: 채무상환능력 (25%) — FFO/총차입금 · Debt/EBITDA · FOCF/Debt · EBITDA/이자비용 · 만기구조
    ├── 축 2: 자본 구조 (20%) — 부채비율 · 차입금의존도 · 순차입금/EBITDA · 금융자회사 분리
    ├── 축 3: 유동성 (15%) — 유동비율 · 현금비율 · 단기차입금비중 · 만기 1년 내 비율
    ├── 축 4: 현금흐름 (15%) — OCF/매출 · FCF/매출 · OCF/총차입금 · CF 패턴 · eCR
    ├── 축 5: 사업 안정성 (10%) — 매출 CV · 이익 CV · 매출 규모 · 부문 HHI · 영업이익률 추세
    ├── 축 6: 재무 신뢰성 (10%) — Anomaly Score · Beneish M-Score · 감사의견
    └── 축 7: 공시 리스크 (5%) — 우발부채 만성화 · 키워드 (횡령/배임/과징금) · 감사 구조
    │
    ▼
[Layer 3] 3-Track 분기 + 업종 조정 + 시계열 안정화
    │
    ├── 3-Track 분기 (v4.0)
    │   ├── Track A — 일반기업 (7 축) — isFinancial=False, isHolding=False
    │   ├── Track B — 금융업 회계 프록시 진단 — isFinancial=True
    │   │   ├── 장부자본·ROA·금융수익·대손상각비·현금성자산 관측값만 공개
    │   │   ├── 유동성은 LCR/NSFR·ALM·haircut·우발유출을 대체하지 않는 비채점 진단
    │   │   └── 은행/보험/증권/금융지주/기타금융 유형별 calibration 전 grade·PD·outlook 비발행
    │   └── Track C — 지주사 (7 축 재가중) — isHolding=True
    │       └── 채무상환 (15%) / 자본구조 (25%) / 나머지 동일
    │
    ├── 업종별 기준표 적용 (11 개 IndustryGroup 세분화)
    ├── OFS 블렌딩 — 별도재무제표로 캡티브/지주 연결 왜곡 보정
    │   ├── 연결 50% + 별도 50% (별도가 10 점+ 양호하면 35:65)
    │   └── 축 1 (채무상환) + 축 2 (자본구조) + 축 4 (현금흐름) 에 적용
    ├── 축 1 압축 — captive/holding/cyclical: 20 초과분 40% 감쇄
    ├── 3 개년 가중이동평균 (등급 급변동 방지)
    └── CHS 시장 보정 — Campbell (2008) 부도확률 모델
        ├── PD 비대칭 — 극안전 (-5) → 투자적격 (상향만) → 위험 (하향만)
        └── AA 이상 하향 보호 (max +1)
    │
    ▼
[Layer 4] Notch Adjustment + 등급 결정 + 보고서 생성
    │
    ├── Notch Adjustment (정성 대리 신호, v4.0)
    │   ├── 1. 매출 50조+ → +3 notch / 10조+ → +1
    │   ├── 2. 공기업 (한전 등) → +3
    │   ├── 3. 캡티브 별도 D/EBITDA < 3x → +2
    │   ├── 4. 지주 별도 부채비율 < 100% → +2
    │   ├── 5. CAPEX 집약 OCF 양수 → +1
    │   ├── 6. 시가총액 30 조+ → +3 / 10 조+ → +1
    │   ├── 7. 연속 5 기 영업흑자 → +1
    │   ├── 규모별 cap — 대형 7 / 중형 4 / 소형 2 (v5.0)
    │   └── score ≤ 10 미적용, score ≤ 19 cap 4
    │
    ├── 종합 점수 → dCR-등급 매핑 (20 단계)
    ├── divergenceExplanation — 괴리 원인 자동 설명 (v4.0)
    ├── 등급 보고서 생성 (12 섹션, v5.0)
    ├── 신평사 등급 대조 (동의/비동의 + 근거)
    └── 등급 이력 기록 + 전이 매트릭스 업데이트
```

## 4 규칙

### 규칙 1 — 의존성 없음 (오리지널 정보)

credit 엔진은 다른 analysis calc 함수를 호출하지 않는다.

- `company.select()` · `company.notes` · `company.panel()` · `company.finance.ratios` 로 원본 데이터 직접 접근.
- `calcLeverageTrend()` · `calcDistressScore()` 등 기존 calc 호출 금지.
- 이유 — 신용분석 지표 정의/계산은 신용분석 맥락에 최적화. 같은 지표라도 ICR 등 신용분석 ICR (등급 결정용) 와 stability ICR (추세 관찰용) 차이.
- 예외 — `company.finance.ratios` 의 부실 모델 점수 (Z-Score / O-Score / Beneish) 참조 허용. 이미 L0 검증된 순수 수치.

### 규칙 2 — 신용분석 특화 (재구현)

기존 엔진의 좋은 것을 참고하되 신용분석 맥락에 맞게 재구현.

| 기존 기능 | 신용분석 특화 | 차이 |
|-----------|------------------|------|
| `stability.calcCoverageTrend` | credit 자체 ICR | 이자비용 정의 — 리스이자 포함 |
| `capital.calcLiquidity` | credit 자체 유동성 | notes.borrowings 1 년내 만기 포함 |
| `crossStatement.calcAnomalyScore` | credit 자체 신뢰성 점수 | 감사의견 + 공시리스크 통합 |
| `scan.governance` | credit 자체 거버넌스 | 등급 조정 맥락 (±notch) |
| `cashflow.calcCashFlowOverview` | credit 자체 CF 등급 | eCR 체계 (신평사 대응) |

### 규칙 3 — dartlab 만의 체계

차별화 5 요소:
1. **완전 투명** — 코드 = 방법론. 파라미터 · 가중치 · 기준표 100% 공개
2. **재현 가능** — 같은 코드 + 데이터 → 같은 등급. 예외 없음
3. **공시 깊이 활용** — 주석 12 항목 + 사업보고서 텍스트 + 공시변화 신호
4. **횡단 비교 내장** — scan 으로 전종목 대비 상대 위치 자동
5. **보수주의** — 정량 불가 영역 등급에 반영하지 않되, 보고서에 명시

**dCR vs 신평사 등급 관계** — dCR 은 정량 기반 독립 등급. 신평사는 정량 + 정성 (면담 · 산업 전문성) 종합. 둘이 다를 수 있고, 다른 것이 정상. "신평사보다 정확하다" 가 아닌 "다른 관점에서 본다" 가 dartlab 포지션.

**공기업 / 계열 지원 처리** — 정량 등급에 반영하지 않음. 보고서에 별도 섹션:

```
[정량 등급] dCR-BB+ (점수 34.5)
[구조적 지원 참고] 정부 100% 출자 공기업 — 제도권 등급 AAA
[dartlab 판단] 정량 기준 BB+, 자체 재무건전성은 투기등급 수준.
               정부 지원을 고려한 제도권 등급과 6 notch 차이.
               정부 지원 제거 시 실질 신용위험은 정량 등급에 가깝다.
```

### 규칙 4 — 문서 관리 + 운영 수칙

보고서 체계 5 종:
1. **개별 기업 보고서** — `data/credit/reports/{종목코드}.md` (등급 + 7 축 + 신평사 대조 + 근거)
2. **등급 이력** — `data/credit/history/{종목코드}.json`
3. **audit 기록** — `data/credit/audit/{종목코드}.md`
4. **전이 매트릭스** — `data/credit/transition.json`
5. **정례 보고서** — `data/credit/periodic/`

**등급 변경 프로세스**:
- 정기 리뷰 — 사업보고서 공시 시 (연 1회)
- 이벤트 트리거 — 분기 실적 급변 (50%+) / 유동성 위기 / 감사의견 비적정 / 대규모 M&A / disclosureRisk
- 등급 변경 시 — 변경 등급 + 사유 + 이전 비교 + 핵심 변동 지표

**audit 규칙** — 매 보고서 발행 시 반드시 audit. 발간 = 검증 + 보완 루프.

audit 단계 8:
1. 보고서 직접 읽기 (처음부터 끝까지)
2. 서사 품질 검증 (narrative.py 생성 문장 자연스러움 · ICR 999배 같은 무의미 수치)
3. 지표 정합성 (7 축 지표가 원본 재무제표와 일치)
4. 신평사 대조 (KIS/KR/NICE 공개 등급, ±2 notch 이내 정상, ±3~4 원인 분석, ±5 이상 모델 재검토)
5. 동의/비동의 (수치 근거 제시)
6. 코드 보완 (narrative.py · engine.py · thresholds.py · AI 프롬프트)
7. 재발간
8. audit 기록

**audit 없이 발간하지 않는다. audit 없이 commit 하지 않는다.**

**방법론 버전 관리** — v1.0 → v1.1 → ... 버전별 영향 받는 기업 수 + 등급 변동 통계 공개. 이전 버전으로도 재현 가능하도록 버전별 파라미터 보존.

### 금융업 발행 경계

- 공통 재무제표의 장부자본/총자산은 CET1·K-ICS·NCR이 아니며 금융업 공통 자본적정성 점수로 쓰지 않는다.
- 현금/총자산과 일반 유동비율은 은행 LCR·NSFR, 보험 ALM/유동성 스트레스, 증권 haircut·채무보증 조정 유동성을 대체하지 않는다.
- BS만 있는 더 최신 기간 대신 BS·IS가 함께 있는 최신 공통기간을 진단 기준으로 쓰고 `requestedAsOf`/`assessmentAsOf`/`freshnessGap`을 공개한다.
- 결측 자산건전성·유동성을 총자산 규모나 중립값으로 대체하지 않는다. 관측 0과 결측 `None`을 구분한다.
- 금융업 결과는 `assessmentStatus="diagnostic_only"`, `grade=None`, `pdEstimate=None`, `outlook="N/A"`이다.
- 향후 금융 등급 발행은 하위유형 확정, 유형별 규제지표의 핵심 4축 전부 관측, 총 관측 coverage 85% 이상, 동일 시점 정렬을 모두 충족해야 한다. PD는 별도 out-of-time calibration 전까지 비발행한다.

## 대표 반환 형태

### 보고서 구조 (12 섹션, v5.0)

| 섹션 | 내용 | 데이터 소스 |
|------|------|-----------|
| 1. 등급 요약 | 등급 · 건전도 · PD · eCR · 전망 · 업종 | engine.py |
| 2. 기업 개요 | 업종 · 주요사업 · 부문구성 · 시장지위 | calcCompanyProfile + segments + rank |
| 3. 재무 하이라이트 | 매출/이익/EBITDA 전년비 + 추세 + 차입금 구성 | metricsHistory + narrative |
| 4. 등급 근거 | AI 해석 (산업 맥락 + 인과 체인) | AI ask() |
| 5. 7 축/금융 진단 상세 | 비금융 축별 서사 또는 금융 비채점 회계 프록시 | narrative + diagnostic metrics |
| 6. 재무 요약 5 개년 | 핵심 지표 시계열 | metricsHistory |
| 7. 등급 전망 | 상향/하향 트리거 자동 생성 | 조건부 로직 |
| 8. 신평사 대조 | 동의/비동의 + notch 차이 | audit.py |
| **9. 등급 괴리 분석** | **왜 다른지 자동 설명** | **divergenceExplanation** |
| **10. Notch Adjustment 상세** | **적용된 규칙과 이유** | **notchAdjustment.reasons** |
| **11. 별도재무제표 비교** | **연결 vs 별도 핵심 지표** | **separateMetrics** |
| 12. 면책 | 방법론 버전 + 면책 사항 | 정적 |

**dartlab 만의 차별 섹션 (9~11)**:
- **9. divergenceExplanation** — 신평사와의 등급 차이를 정량 근거로 자동 설명
- **10. Notch Adjustment** — 정성 대리 신호 (규모 · 시장지위 · 경영안정성) 등급 반영
- **11. 별도재무제표** — 연결 재무 왜곡 (캡티브 금융 / 자회사 부채) 별도와 비교

### review 5-7 신용평가 섹션 (review publisher 통합)

```
1. 등급 요약 (건전도 바 + 8 핵심 지표)
2. Executive Summary (hook 문장 + 인과 체인 서사)
3. 재무 하이라이트 (6 지표 + YoY)
4. 사업 분석 (기업 개요 + 부문별 매출 + HHI)
5. 등급 근거 상세 (인과 서사 + Mermaid 흐름도 + 강점/약점)
6. 재무 분석 (비금융 7 축 게이지 또는 금융 비채점 진단)
7. 5 개년 재무 시계열
8+. 등급 전망 / 신평사 대조 / 등급 괴리 / Notch / 별도재무 / 면책
```

빈 섹션 자동 스킵, 번호 연속.

신규 블록:
- `creditNarrative` — 7 축 서사 (severity별 strong / adequate / weak / critical)
- `creditAudit` — 외부 신평사 등급 + notch 차이 + 동의/비동의 근거

기존 16 개 credit 보고서 `blog/04-credit-reports/` 보존 (아카이브). 신규 `blog/05-company-reports/` review 형식.

## 검증 (v4.0~v5.0)

| 표본 | 적중률 | 비고 |
|------|--------|------|
| 30 개사 (대기업) | **87%** (26/30) | 정확일치 10 개+ |
| 50 개사 (중대형) | **82%** (41/50) | |
| 79 개사 (전체) | **70%** (55/79) | v5.0 과대평가 수정 후 재측정 예정 |

**괴리 분석**:
- 정량 한계 3 — 삼성SDI · 고려아연 · 현대제철. FCF 음수 / CAPEX 집약 → 외부 등급 "미래 성장성" 정성 반영.
- 금융 한계 1 — KB금융. AAA 는 "시스템적 중요 은행" 정성. 정량만으로 AAA 불가.
- 주가 일시 1 — SKT. CHS 주가 급락 보정으로 하향 → 보호 규칙으로 복원.

## 방법론 기반 — 세계 참조점

| 참조 | dartlab 적용 | 차별점 |
|------|-------------|--------|
| **S&P** | 7 축 (Business + Financial Risk) | S&P 정성 50%. dartlab 은 정성 대리 신호로 근사 |
| **Moody's** | 선형보간 scoring (breakpoint) | Moody's 비공개. dartlab 코드 100% 공개 |
| **KIS / 한기평** | PD 캘리브레이션 (한국 실측 1998-2025) | 한국 시장 특화. 20 단계 매핑 |
| **Campbell (2008)** | CHS 부도확률 모델 (8 변수 logit) | 주가 신호 통합. 재무 + 시장 하이브리드 |

**dartlab 만의 고유 접근 4**:
1. **OFS 블렌딩** — 별도재무제표로 캡티브/지주 연결 왜곡 보정. 어떤 무료 프레임워크도 하지 않음.
2. **정성 대리 신호** — 시가총액 (시장 지위) · 연속 흑자 (경영 역량) 정량 추출. 정량 ↔ 정성 간극 축소.
3. **divergenceExplanation** — "왜 다른지" 자동 설명. 블랙박스 아닌 투명한 차이 공개.
4. **코드 = 방법론** — 코드 공개하면 방법론 100% 재현. 별도 논문 불필요.

## 코드 구조

```
src/dartlab/credit/
├── __init__.py           # credit() 단일 진입점 + 7 축 select 체계
├── engine.py             # 등급 산출 메인 파이프라인
├── metrics.py            # 7 축 정량 지표 산출 (오리지널)
├── narrative.py          # 7 축 서사 생성 (조건부 해석 문장)
├── audit.py              # 신평사 대조 + 동의/비동의
├── history.py            # 등급 이력 JSON + 전이 매트릭스
├── scorecard.py          # 점수→등급 매핑 (core 재수출)
└── thresholds.py         # 업종별 기준표 (core 재수출)

blog/04-credit-reports/   # 공개 발간 (블로그 카테고리, GitHub Pages)
├── _registry.json
├── {순번}-{slug}/index.md

data/credit/              # 내부 데이터 (git 미추적)
├── history/ · audit/ · external_grades.json · transition.json · periodic/
```

### SSOT 헬퍼 위임

`credit/metrics.py` 의 `_toDict` / `_annualCols` 는 `analysis/financial/_helpers.py` 의 `toDictBySnakeId` / `annualColsFromPeriods` 를 alias 위임 (Plan v9 P0). credit 은 analysis calc 함수는 호출하지 않지만, 데이터 변환 헬퍼는 SSOT 단일 경로 사용.

## 관련 코드 (소비 대상)

| 경로 | 역할 | credit 활용 |
|------|------|------------------|
| `company.select("BS/IS/CF")` | 재무제표 원본 | 7 축 지표 산출 |
| `company.notes.*` | 주석 12 항목 | 차입금만기 / 충당부채 / 부문 / 리스 |
| `company._report.audit` | DART 구조화 감사 API | 명시 감사의견 / 감사인 / 접수번호 |
| `company.panel(topic)` | 사업보고서 텍스트 | 우발부채 / 사업내용 |
| `company.finance.ratios` | 부실 모델 점수 | Z-Score / O-Score / Beneish 참조 |
| `company.sector` | 업종 분류 | 기준표 선택 |
| `gather.price` | 주가/변동성 | CHS 모델 · 시가총액 |
| `gather.macro` | 거시지표 | 금리 / 스프레드 |
| `scan.*` | 횡단 비교 | 업종 내 순위 |

## 장기 로드맵

### Phase 1 (완료) — 정량 엔진 v1~v2
- 7 축 정량 스코어링 + 업종별 기준표 (11)
- TTM 환산 + 이자비용 CF fallback
- 30 개사 53~57%

### Phase 2 (완료) — 3-Track + Notch + OFS (v3~v4)
- Track A/B/C 분기
- Notch Adjustment 7 규칙
- CHS 시장 보정 + OFS 블렌딩
- 79 개사 70%, 대기업 87%

### Phase 3 (진행 중) — 방법론 정립 + 보고서 완성 (v5)
- 12 섹션 보고서
- divergenceExplanation
- 방법론 문서 정비 (본 sub-spec)
- 50 개사 배치 발간

### Phase 4 (계획) — 텍스트 분석 도입 + 시장 데이터 확장
- 사업보고서 "사업의 내용" NLP 분석
- 위험 공시 품질 측정 (특이성 / 끈기성)
- 경영진 투명성 점수
- 시장 데이터 확장 — 보고서에 회사채 스프레드 (ECOS/FRED) 삽입 검토. credit 실행 중 gather("macro") 호출은 메모리 부담 + API 의존이라 보류. 시장 스프레드는 등급 산출에는 미사용하되, 보고서 보충 정보로 향후 추가.

### Phase 5 — 공개 + 신뢰 구축
- dartlab.io 등급 조회 페이지
- 정례 보고서 유튜브 공개
- 등급 전이 매트릭스 / 부도율 통계 공개
- 커뮤니티 피드백 → 방법론 개선 루프

## 발간 규칙

- 정기 발간 — 사업보고서 공시 후 2 주 이내
- 이벤트 발간 — 등급 변경 시 즉시
- 정례 보고서 — 월 1 회 전체 등급 변동 요약 (`data/credit/periodic/`)
- 저장 경로 — `blog/05-company-reports/{순번}-{slug}/index.md` (review publisher)
- 발간 명령 . `dartlab.Company("005930").story(type="credit")` 로 신용 관점 리포트를 조립한다
- 레거시 — `blog/04-credit-reports/` 아카이브 (16 개)

## 변경 이력

| 날짜 | 버전 | 변경 | 퀄리티 |
|------|------|------|--------|
| 2026-04-01 | v1.0 | 초기 엔진 — 5 축, 20 단계, 8 개사 검증 | 50/100 |
| 2026-04-01 | v1.0 | 정밀도 강화 — 6 축 + 업종세분화 + 사이클/캡티브 | 55/100 |
| 2026-04-01 | v1.0 | credit 독립 엔진 — 7 축, 사상/규칙/audit | 60/100 |
| 2026-04-01 | v1.0 | 발간 체계 — narrative+audit+publisher+3 개사 | 62/100 |
| 2026-04-01 | v1.0 | audit 보완 — 무차입표현, 유동성모순, 섹션번호 | 65/100 |
| 2026-04-02 | v1.0 | 세계 수준 강화 — 기업개요 + 추세 + 차입금구성 + 부문 | 75/100 |
| 2026-04-02 | v1.0 | AI 연동 — 프롬프트 등록, detail 에 서사 포함 | 75/100 |
| 2026-05-12 | v5.0 | `analysis/CREDIT.md` → 본 sub-spec 통합 (Skill OS 운영 SSOT 승격) | 75/100 |

## 기본 검증

- 호출 결과는 `tableRef` · `valueRef` · `dateRef` · `executionRef` 로 ref 남긴다.
- 7 축 가중치 변경 시 본 메서드 spec + engines.credit SKILL.md 동시 갱신.
- 외부 신평사 등급 비교 시 시점·표본·정성 요소 차이 답변에 명시.

