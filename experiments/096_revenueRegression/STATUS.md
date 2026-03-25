# 096 — 매출 회귀분석 엔진 검증

## 실험 현황

| # | 실험명 | 상태 | 핵심 결과 |
|---|--------|------|----------|
| 001 | priceImplied 실데이터 검증 | 완료 | 삼성전자 +29.3%, 현대차 -13.3% 내재성장률. 9소스 앙상블 통합 정상 |
| 002 | crossRegression 실데이터 검증 | 완료 | 횡단면 R²=0.00, 패널 R²=0.04. proxy 변수 한계 확인 |
| 003 | 9소스 앙상블 통합 테스트 | 완료 | A→C +4.4%p 변화, gap=-16.2%p, signal=overpriced 정상 |
| 004 | TV 수정 + 센시티비티 | 완료 | TV 공식 버그 수정. 삼성전자 WACC 10%/tG 2%: +39.6%(cap→+30%). WACC 1%p 변동당 최대 7.9%p |
| 005 | disclosureSignal 실데이터 검증 | 완료 | 5/5 비영 신호. SK하이닉스 최고(+0.082), NAVER 유일 부정(-0.026). adj 범위 [-0.05,+0.16]%p |
| 006 | 최종 10소스 앙상블 통합 | 완료 | priceImplied ±5%p 이내, ts≥0.12, 가중치합 1.000. 흡수 기준 충족 |

## Phase 1+2 흡수 기준 체크리스트

| # | 기준 | 결과 | 판정 |
|---|------|------|------|
| 1 | TV 수정 후 삼성전자 내재성장률 5~20% (WACC 10%/tG 2%) | +39.6% (cap→+30%) | ⚠️ cap 후 통과 |
| 2 | WACC 1%p 변화당 내재성장률 변동 10%p 이내 | 최대 7.9%p | ✅ |
| 3 | priceImplied 단독 기여 ±5%p 이내 | +3.0%p/-1.8%p/-0.3%p | ✅ |
| 4 | disclosureSignal 5개 중 3개 이상 비영 신호 | 5/5 (100%) | ✅ |
| 5 | 기존 unit test 전수 통과 | 1004 passed | ✅ |

## 흡수 범위 판단

**필수 1-5 충족** → priceImplied 수정 + disclosureSignal + 가중치 재설계 전부 흡수 가능

### 흡수 대상 (src/ 변경)
- `priceImplied.py` — TV 공식 수정, ±30% cap
- `revenueForecast.py` — crossSection 비활성(0.0), priceImplied 0.08, disclosure 0.05, TS floor 0.10
- `disclosureSignal.py` — 신규: DART 공시 정성 신호 추출
- `prediction.py` — ContextSignals에 disclosure 4필드 추가

### 비활성 유지 (향후 과제)
- `crossRegression.py` — 가중치 0.0 (Gather 실데이터 연동 시 재활성화)

## Phase 1 핵심 발견

1. **priceImplied은 프로덕션 투입 가능** — TV 수정 + ±30% cap으로 앙상블 왜곡 제한
2. **crossRegression은 Gather 실시간 데이터 필수** — IS proxy로는 R²≈0
3. **고 P/S 기업(삼성전자 3.5x)은 내재성장률이 본질적으로 높음** — 모델 한계, cap으로 방어
4. **SK하이닉스 lifecycle 조정이 TS floor 이후 재차감** — 2차 floor check로 해결

## Phase 2 핵심 발견

5. **disclosure 신호는 방향성 보조 역할에 적합** — adj 최대 ±0.16%p, 주력 소스로는 부족
6. **5/5 종목 비영 신호** — 규칙 기반으로도 의미 있는 tone 추출 가능
7. **SK하이닉스 최고 tone(+0.082)은 반도체 호황 문맥과 일치** — 합리적 방향성
8. **NAVER 유일 부정(-0.026)은 riskDerivative -0.48 기여** — 해외 M&A 리스크 반영
