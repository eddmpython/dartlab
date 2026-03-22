# Insight 엔진 — 내부 아키텍처

## 파이프라인 흐름

```
analyze(stockCode)
  │
  ├─ buildTimeseries / buildAnnual        ← DART pivot
  ├─ calcRatios(aSeries)                  ← 재무비율 + 복합지표 (O-Score, Z'', M-Score 등)
  ├─ detectFinancialSector(aSeries)       ← 금융업 자동 탐지
  │
  ├─ 7영역 등급 산정 ─┐
  │   analyzePerformance                  │  각 영역 → InsightResult(grade, summary, risks, opportunities)
  │   analyzeProfitability                │
  │   analyzeHealth                       │
  │   analyzeCashflow                     │
  │   analyzeGovernance                   │
  │   analyzeRiskSummary                  │  ← 다른 5영역 risk 종합
  │   analyzeOpportunitySummary           │  ← 다른 5영역 opportunity 종합
  │                                       │
  ├─ runAnomalyDetection(8개 탐지기)      │
  ├─ calcDistress(ratios, anomalies)      │  ← 4축 스코어카드 + 신용등급 + 유동성
  ├─ classifyProfile(grades)              │
  └─ generateSummary(...)                 │
      ↓                                   │
  AnalysisResult                          ←┘
```

## 모듈 구조

| 파일 | 역할 |
|------|------|
| `pipeline.py` | 진입점. analyze() 오케스트레이션 |
| `grading.py` | 7영역 등급 산정 (A~F). AREAS dict가 메타데이터+로직 공존 |
| `anomaly.py` | 8개 룰 기반 이상치 탐지기 |
| `distress.py` | 4축 부실 예측 스코어카드. 모델별 해석 + 신용등급 + 유동성 |
| `detector.py` | 금융업 자동 탐지 (6개 시그널) |
| `summary.py` | 한국어 요약문 생성 + 프로파일 분류 |
| `types.py` | 데이터 타입 (ModelScore, DistressAxis, DistressResult, InsightResult 등) |
| `spec.py` | 메타데이터 선언 (AREAS, ANOMALY_DETECTORS, DISTRESS_MODELS) |

## 등급 산정 로직

각 영역은 점수제 (0~N점). 점수 → 등급 매핑:
- 점수가 높을수록 좋음
- 영역별 max 점수가 다름 (performance: 4, health: 7, governance: 4 등)
- 임계값 기반으로 A/B/C/D/F 배정
- 금융업은 별도 기준 적용 (health, profitability)

## 부실 예측 스코어카드

### 4축 가중 평균

| 축 | 가중 | 소스 |
|----|------|------|
| 정량 (quantitative) | 40% | O-Score, Z''-Score, Z-Score → 0~100 정규화 |
| 이익품질 (earningsQuality) | 20% | Beneish, Sloan, F-Score → 0~100 정규화 |
| 추세 (trend) | 30% | trendDeterioration, cccDeterioration anomaly |
| 감사 (audit) | 10% | audit, governance anomaly |

### ModelScore 패턴

각 모델은 `_interpret{Model}(rawValue) → ModelScore`를 통해:
- rawValue → zone (safe/gray/distress) 판정
- displayValue: 사람이 읽을 수 있는 값
- interpretation: 근거 기반 해석
- reference: 학술 참조

### 신용등급

overall → S&P PD 대응표 → AAA~D (10단계)

### 유동성 경보

`_calcCashRunway(ratios)`:
- 영업CF 양수 → 소진 없음
- 영업CF 음수 → 현금 / |월간 영업CF| = 소진 개월
- 영업CF 없음 → 현금 / 월간 (매출원가+판관비)

## 이상치 탐지기 (8개)

| # | 탐지기 | 카테고리 |
|---|--------|----------|
| 1 | 이익 품질 괴리 | earningsQuality |
| 2 | 운전자본 급변 | workingCapital |
| 3 | 재무구조 급변 | balanceSheetShift |
| 4 | 현금 소진 | cashBurn |
| 5 | 마진 괴리 | marginDivergence |
| 6 | 금융업 특화 | financialSector |
| 7 | 추세 악화 | trendDeterioration |
| 8 | CCC 악화 | cccDeterioration |

## spec.py 체계

```
grading.py AREAS dict    ← 로직 + 메타데이터 공존
       ↓
insight/spec.py          ← AREAS, ANOMALY_DETECTORS, DISTRESS_MODELS, DISTRESS_SCORECARD
       ↓
ai/spec.py               ← 각 엔진 spec 수집
       ↓
test_spec_integrity.py   ← CI 검증
```

## 실험 근거

실험 `084_distressModels` Phase 1~4 (10개 실험) 검증 결과 기반:
- Phase 1: 기본 4축 모델 검증
- Phase 2: 복합 점수 체계 (Beneish, Sloan, F-Score)
- Phase 3: 추세 탐지 (trendDeterioration, cccDeterioration)
- Phase 4: 백테스트 (위험/안전 종목군 분리도 검증)
