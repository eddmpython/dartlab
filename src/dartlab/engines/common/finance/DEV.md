# finance — 재무 분석 엔진 아키텍처 (v3)

## 모듈 구조

```
engines/common/finance/
├── extract.py         # 시계열 값 추출 (getTTM, getLatest, getAnnualValues)
├── ratios.py          # 재무비율 계산 (수익성, 안정성, 밸류에이션)
├── valuation.py       # 내재가치 (DCF, DDM, 상대가치)
├── forecast.py        # 단일 지표 예측 + 시나리오 + 민감도
├── simulation.py      # 매크로 경제 시나리오 시뮬레이션
├── proforma.py        # 3-Statement Pro-Forma 재무제표 (v3: IS 구조 감지)
├── prediction.py      # Context Signal Fusion — 맥락 기반 확률 재가중
├── pricetarget.py     # 확률 가중 주가 목표가 (v3: MC WACC 수정)
└── __init__.py        # 전체 re-export
```

## 6-Layer 통합 예측 체인 (v3)

```
Layer 1: Adaptive Ratio Engine            Layer 2: Context Signal Fusion
  과거 N년 → 최근 가중 + 트렌드     →      insight 등급 (10영역 A~F)
  IQR 이상치 제거                            diff 변화율 (공시 텍스트)
  비율 경로 (연도별 점진 변화)               rank 순위 (sizeClass)
                                             → 시나리오 확률 동적 재가중

Layer 3: IS 구조 감지 [v3 NEW]            Layer 4: Smart 3-Statement
  GP - SGA ≈ OP → dep_in_sga=True           IS → BS → CF 연결
  K-IFRS D&A 이중 차감 자동 방지             Cash = plug (BS 균형 보장)
  영업이익률 크로스체크 경고                  현금 음수 → 자동 차입 + BS 재균형
                                             업종별 β → WACC

Layer 5: Multi-Noise Monte Carlo          Layer 6: Narrative Integration (AI)
  5변수 noise: growth/margin/wacc/capex/tax   ContextSignals.reasoning → LLM에게 전달
  sizeClass별 σ 차등 (Small 1.5x, Large 0.8x) LLM이 사업보고서 원문과 교차 검증
  NWC 변동 반영 FCF, dep_in_sga 연동
  → P10~P90 분포
```

## 모듈별 설계 결정

### simulation.py — 매크로 경제 시뮬레이션

**3-Layer 구조**:
1. `MacroScenario`: GDP/금리/환율/CPI 3년 경로
2. `SectorElasticity`: 15개 한국 업종별 β (GDP, FX, 마진, NIM)
3. `CompanySimulation`: 기업 실적 → 시나리오 적용

**사전 정의 시나리오**:
- baseline (현추세), adverse (경기침체), china_slowdown, rate_hike, semiconductor_down

### proforma.py — 3-Statement Pro-Forma (v3)

**v2 Adaptive Ratio** (`_weighted_ratio`):
- 정적 중위값 대신 최근 가중 평균 + 트렌드 기울기
- 가중치: [0.05, 0.10, 0.15, 0.25, 0.45] (최근 데이터에 높은 가중)
- IQR 기반 이상치 제거 (Q1-1.5×IQR ~ Q3+1.5×IQR)
- 트렌드: (후반 평균 - 전반 평균) / 데이터 수
- `HistoricalRatios.trends`: 비율별 연간 트렌드 (예: gross_margin=+0.5)

**비율 경로 적용** (`build_proforma`):
```python
yr_margin = base_margin + trend × year_index  # 트렌드 반영
yr_margin = clamp(yr_margin, floor, ceiling)   # 업종 범위 제한
```

**v3 K-IFRS IS 구조 자동 감지** (`dep_in_sga`):

K-IFRS 기업에는 2가지 IS 구조가 존재:

| 유형 | IS 구조 | 예시 |
|------|---------|------|
| SGA 포함형 | OP = GP - SGA (D&A가 SGA 내 포함) | 삼성전자, SK하이닉스 |
| D&A 별도형 | OP = GP - SGA - D&A (D&A 독립 보고) | LG화학 |

**감지 로직**:
1. 최근 3년 GP, SGA, OP 데이터 비교
2. `|GP - SGA - OP| / 매출 < 2%` → SGA 포함형 (dep_in_sga=True)
3. 3년 중 2년 이상 일치 시 확정
4. `HistoricalRatios.dep_in_sga` 플래그로 저장

**적용**:
```python
if ratios.dep_in_sga:
    op = gp - sga           # D&A 별도 차감 안 함
else:
    op = gp - sga - dep     # D&A 별도 차감
ebitda = op + dep           # EBITDA는 항상 OP + D&A
```

**영업이익률 크로스체크**: 기준연도 대비 예측 1년차 OP margin 차이 > 5%p면 경고

**v2 자동 차입** (현금 음수 시):
1. Cash plug이 음수 → shortfall 계산
2. 50:50 단기/장기 차입 분배
3. 추가 이자비용 → IS 재계산 (NI, Tax, Div)
4. 자본 재계산 → BS 재균형
5. 최대 3회 반복 (이자→순이익→자본 감소 사이클 수렴)

**v2 β WACC** (`compute_company_wacc`):
- `sector_params.discountRate` 있으면 우선 사용
- `sector_elasticity.revenue_to_gdp`를 equity β proxy로 사용
- β clamp: 0.5~2.5

### prediction.py — Context Signal Fusion [NEW]

**`ContextSignals` 데이터**:
| 신호 | 소스 | 기본값 |
|------|------|--------|
| insight_grades | insight 엔진 10영역 | {} |
| diff_change_rate | docs.diff() | 0.0 |
| risk_change_rate | 리스크 topic 변화율 | 0.0 |
| size_class | rank 엔진 | "Mid" |
| sector_cyclicality | SectorElasticity | "moderate" |
| growth_rank_pct | rank 엔진 | 50.0 |

**확률 조정 규칙** (투명, 설명 가능):

| # | 조건 | 조정 | 근거 |
|---|------|------|------|
| 1 | profitability D/F | adverse +5%p, baseline -5%p | 수익성 악화 |
| 2 | health D/F | adverse +5%p, baseline -5%p | 부채 과다 |
| 3 | risk_change > 60% | adverse +5%p, baseline -5%p | 리스크 급변 |
| 4 | opportunity A | baseline +5%p, adverse -3%p | 긍정 기회 |
| 5 | cyclicality high | rate_hike +3%p, baseline -3%p | 경기민감 |
| 6 | cyclicality defensive | baseline +5%p, adverse -3%p | 방어적 |
| 7 | growth top 20% | baseline +3%p | 성장 모멘텀 |
| 8 | cashflow D/F | adverse +3%p | 현금흐름 위험 |

**MC Noise Config** (sizeClass별 σ):

| 변수 | base_σ | Small | Mid | Large |
|------|--------|-------|-----|-------|
| growth | 1.5 | ×1.5 | ×1.0 | ×0.8 |
| margin | 2.5 | ×1.3 | ×1.0 | ×0.9 |
| wacc | 0.8 | ×1.5 | ×1.0 | ×0.7 |
| capex | 1.0 | ×1.2 | ×1.0 | ×0.9 |
| tax | 1.0 | ×1.0 | ×1.0 | ×1.0 |

### pricetarget.py — 확률 가중 주가 목표가 (v3)

**시나리오별 확률** (기본값, context_signals로 재가중):
| 시나리오 | 기본 확률 | 비고 |
|---------|----------|------|
| baseline | 40% | 현추세 |
| rate_hike | 20% | 금리 인상 |
| china_slowdown | 15% | 수출 의존 |
| semiconductor_down | 15% | 비반도체 → baseline에 재배분 |
| adverse | 10% | 극단 |

**DCF Fallback**:
- FCF 양수 → Gordon Growth Model (PV_FCF + PV_TV)
- FCF 음수 (CAPEX 집약) → EBITDA × exit multiple (6~15x), **FCF PV 무시**

**v2 Multi-Noise MC** (v3: WACC 수정 + dep_in_sga 연동):
- 5변수 동시 noise: growth, margin, wacc, capex, tax
- NWC 변동 반영: FCF = NI + D&A - ΔNWC - CAPEX
- sizeClass별 σ 차등 (prediction.py의 NOISE_CONFIG 사용)
- v3: dep_in_sga=True이면 MC에서도 D&A 별도 차감 생략
- v3: MC WACC 하한 수정 (3.0 → 0.03, 소수점 단위 통일)

**투자 신호**:
```
strong_buy:  upside > 30% AND P10 > current
buy:         upside > 15%
hold:        -15% ≤ upside ≤ 15%
sell:        upside < -15%
strong_sell: upside < -30% AND P90 < current
```

## AI 도구 등록

| 도구 | 함수 | v3 변경 |
|------|------|---------|
| `proforma_forecast` | `build_proforma` | v2: Adaptive Ratio + 자동 차입, v3: IS 구조 감지 |
| `price_target` | `compute_price_target` | v2: ContextSignals + MC, v3: MC WACC 수정 + dep_in_sga |
| `economic_forecast` | `simulate_all_scenarios` | — |
| `monte_carlo` | `monte_carlo_forecast` | — |
| `stress_test` | `stress_test` | — |

## 설계 원칙

1. **외부 의존성 제로**: `random`, `math` 모듈만 (numpy/scipy 불필요)
2. **2-Tier 준수**: 계산은 엔진, LLM은 해석만
3. **투명성**: 모든 확률 조정에 reasoning 첨부 (블랙박스 금지)
4. **메모리 안전**: 전체 <200KB (proforma ~100KB + prediction ~50KB + MC ~40KB)
5. **하위호환**: `compute_price_target()` 서명 유지, signals는 optional
6. **기존 엔진 재사용**: insight, diff, rank, sector 직접 참조

## 테스트

```bash
# proforma 단위 테스트 (50개)
bash scripts/test-lock.sh tests/test_proforma.py -v --tb=short

# prediction 단위 테스트 (19개)
bash scripts/test-lock.sh tests/test_prediction.py -v --tb=short

# pricetarget 단위 테스트 (31개)
bash scripts/test-lock.sh tests/test_pricetarget.py -v --tb=short

# 기존 regression (valuation + simulation: 52개)
bash scripts/test-lock.sh tests/test_valuation.py tests/test_simulation.py -m "unit" -v --tb=short
```

총 152개 unit 테스트 (v3: proforma 50 + prediction 19 + pricetarget 31 + valuation/simulation 52).

## 부실 예측 모델 (distress)

실험 `084_distressModels` (10개 실험, 2026-03-22)에서 검증 후 엔진에 흡수.

### ratios.py — 4개 부실 모델 추가

| 모델 | 필드 | 수식 | 판정 기준 |
|------|------|------|----------|
| **Ohlson O-Score** | `ohlsonOScore`, `ohlsonProbability` | 9변수 로지스틱 (1980) | P(부도) > 10% 주의, > 20% 위험 |
| **Altman Z''-Score** | `altmanZppScore` | 4변수, Sales/TA 제거 (1995) | < 1.1 부실, 1.1~2.6 회색, > 2.6 안전 |
| **Springate S-Score** | `springateSScore` | 4변수 Z-Score 변형 (1978) | < 0.862 부실 (한국: cutoff 하향 필요) |
| **Zmijewski X-Score** | `zmijewskiXScore` | 3변수 프로빗 (1984) | > 0 부실 (금융업 왜곡 주의) |

기존: Altman Z-Score, Piotroski F-Score, Beneish M-Score, Sloan Accrual Ratio.

### anomaly.py — 2개 탐지기 추가

| 탐지기 | 카테고리 | 설명 |
|--------|----------|------|
| `detectTrendDeterioration` | `trendDeterioration` | 연속적자, 영업CF적자, ICR<1, 부채비율 상승 |
| `detectCCCDeterioration` | `cccDeterioration` | CCC 3기+ 연속 확대 (금융업 제외) |

기존 6개 + 신규 2개 = 총 8개 탐지기.

### insight/distress.py — 4축 복합 스코어카드 (신규)

```
calcDistress(ratios, anomalies, isFinancial) → DistressResult

4축 가중 평균:
- quantitative (40%): O-Score, Z''-Score, Z-Score 정규화
- earningsQuality (20%): Beneish, Sloan, F-Score
- trend (30%): trendDeterioration + cccDeterioration anomaly
- audit (10%): 감사의견 anomaly

레벨: safe(<15), watch(<30), warning(<50), danger(<70), critical(≥70)
```

`AnalysisResult.distress` 필드로 접근. pipeline.analyze()에서 자동 계산.

### grading.py — health 영역 강화

- O-Score P(부도) > 10% → warning, > 20% → danger 플래그
- Z''-Score < 1.1 → danger, < 2.6 → warning, > 5 → safe 보너스
- 기존 부채비율/유동비율 판정에 부실 모델 신호 합산

### 업종 보정 (실험 검증 결과)

| 업종 | 보정 내용 |
|------|----------|
| **금융업** | Z-Score 불가, X-Score 왜곡, ICR<1 구조적, CCC 비적용 → detector.py 자동 감지 |
| **지주회사** | DSO 극단값 (9000+일), 부채비율 500%+ → DSO/CCC/부채비율 비적용 |
| **바이오** | DIO 극단값 (987일) → DIO 별도 기준 필요 |
| **반도체** | CCC 구조적 장기 (222일) → 업종 벤치마크 대비 판단 |

### 실험 근거

| # | 실험 | 검증 결과 |
|---|------|----------|
| 001 | O-Score | 20/20 커버, P(부도) 0.02%~19.4%. 금융업 포함 범용 최적 |
| 002 | X-Score + Springate | X: 금융업 왜곡. Springate: 한국 과잉탐지 80% |
| 003 | Taffler + Z'' | Taffler: 한국 변별력 부족. Z'': 금융업 전수 커버 |
| 004 | 앙상블 | safe(8), watch(2), warning(7), danger(3) |
| 005 | 감사 Red Flag | 빅4 순환교체 11건, 보수급변 3건, 소송 90건 |
| 006 | 시계열 악화 | 38건 패턴. 위메이드 5기 연속적자, SK ICR<1 7기 |
| 007 | CCC | 8/20 CCC 확대. 업종 이상값 발견 |
| 008 | 5축 스코어카드 | safe(10), watch(7), warning(3) |
| 009 | 텍스트 감성 | 금융업 부정어 1.63배. 보조지표 |
| 010 | Backtesting | 안전군 safe 88%, 위험군 danger 38% |

## 알려진 제한사항

1. ~~**SGA 과대**: K-IFRS에서 R&D가 SGA에 포함된 기업은 영업이익이 과소 추정~~ → **v3에서 해결** (`dep_in_sga` 자동 감지로 D&A 이중 차감 방지)
2. **D&A 누락**: DART 시계열에 감가상각 전용 키가 없으면 CAPEX × 80% 추정.
3. **rank 미연결**: 일부 기업에서 rank/sizeClass가 아직 Company에 미노출 → "Mid" 기본값 사용.
4. **diff 미연결**: docs.diff()가 실패하는 기업은 변화율 0으로 fallback.
5. **주가 데이터**: market API에서 현재가/주식수 자동 조회 가능하나, 없으면 수동 입력 필요.
6. **SGA 트렌드 영향**: SGA/매출 트렌드가 상승세(+1%p/yr+)인 기업은 5년차 영업이익률이 크게 하락할 수 있음. SGA 성격(R&D vs 순수 판관비) 구분은 불가.

## "세상에 없는" 이유

1. **Adaptive Ratio**: 과거 트렌드 자동 반영 + 업종 범위 클램프 (Bloomberg도 정적 가정만)
2. **Context Signal Fusion**: 인사이트 등급 + 공시 변화율 + 시장 순위 → 시나리오 확률 재가중 (어떤 오픈소스에도 없음)
3. **Smart 3-Statement**: 현금 음수 시 자동 차입 + 이자비용 연쇄 조정 (오픈소스에 없음)
4. **K-IFRS IS 구조 감지**: SGA 포함형/D&A 별도형 자동 판별 → 이중 차감 방지 (오픈소스에 없음)
5. **Multi-Noise MC**: 5개 변수 동시 noise + 기업 규모별 σ 차등 (오픈소스에 없음)
6. **DART 네이티브**: K-IFRS 34,000+ 계정 매핑 + 한국 매크로 + 15개 업종 β
7. **투명성**: 모든 조정에 reasoning 첨부 — 블랙박스가 아닌 "설명 가능한 예측"
