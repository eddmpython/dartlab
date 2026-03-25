# 096 — 매출 회귀분석 엔진 검증

## 실험 현황

| # | 실험명 | 상태 | 핵심 결과 |
|---|--------|------|----------|
| 001 | priceImplied 실데이터 검증 | 완료 | 삼성전자 +29.3%, 현대차 -13.3% 내재성장률. 9소스 앙상블 통합 정상 |
| 002 | crossRegression 실데이터 검증 | 완료 | 횡단면 R²=0.00, 패널 R²=0.04. proxy 변수 한계 확인 |
| 003 | 9소스 앙상블 통합 테스트 | 완료 | A→C +4.4%p 변화, gap=-16.2%p, signal=overpriced 정상 |

## Phase 1 엔진 구현 현황

### 완료
- `priceImplied.py` — DCF 역산으로 시장 내재 매출 성장률 산출
- `crossRegression.py` — 횡단면/패널 회귀 + JSON 모델 캐시
- `forecast.py` — `_olsMulti()` 다변량 OLS (순수 Python)
- `revenueForecast.py` — 9소스 앙상블 (priceImplied 0.10 + crossSection 0.12)

### 핵심 발견
1. **priceImplied은 프로덕션 투입 가능** — 수렴 안정, 경계 처리 양호
2. **crossRegression은 Gather 실시간 데이터 필수** — IS proxy로는 R²≈0
3. **revenueGrowthLag(-0.18)은 유의** — 매출 성장률 평균회귀 효과 존재
4. **금융업(KB금융, 신한지주, 삼성생명, 하나금융지주)은 sales 시계열 없음** — 별도 처리 필요
5. **naver API 장 마감 후 시가총액 null** — yahoo_direct 또는 shares×price fallback 필요

### 미결 과제
- 실제 Gather 데이터(PER/PBR/시가총액/외국인비율)로 crossRegression 재검증
- WACC 센시티비티 테이블 (priceImplied 결과가 가정에 민감)
- 기존 단위 테스트 전수 통과 확인
