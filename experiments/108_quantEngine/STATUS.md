# 108 — quantEngine (tradix 퀀트 엔진 dartlab 통합)

## 목적

tradix 벡터화 지표(45개) + 신호(9개)를 dartlab에 이식하고,
시장 지수/기업 주가 기반 거시+기업 분석 파이프라인 구축.

## 실험 목록

| 파일 | 상태 | 내용 | 핵심 결과 |
|---|---|---|---|
| 001_indicatorTest.py | 완료 | tradix 지표 → dartlab gather 연결 | 계산 6.5ms, 5종목 정상 |
| 002_analyzerProto.py | 완료 | 종합 판단 프로토타입 | RSI+SMA → 강세/중립/약세 분류 |
| 003_scanIntegration.py | 완료 | scan 횡단 100종목 | 재무양호+강세 11종목 발견 |
| 004_marketIndex.py | 완료 | 시장 지수 수집 + 상대강도 | 네이버 KOSPI 0.1s, 베타 R²=0.75 |
| 005_priceAnalysis.py | 완료 | 주가+재무 교차 | CAPM 기대수익 산출, macroBeta 대체 |

## 흡수 완료

- `src/dartlab/quant/` — L1 독립 엔진 (45지표, 9신호, analyzer)
- `dartlab.quant("005930")` → 종합 판단
- `Company.quant()` → Company 연결
- EDGAR 동기화 테스트 PASSED

## 추가 흡수 대기 (실험 004, 005 기반)

1. **gather 시장 지수 심볼**: `gather("price", "KOSPI")` — 네이버 KOSPI/KOSDAQ 직접 지원 확인
2. **quant 상대강도 + 베타**: 종목 vs 시장 RSI 차이, OLS 실측 베타
3. **CAPM → analysis/valuation 연결**: 실측 베타 → 기대수익률 → 할인율 파라미터

## 현황

- 2026-04-01 실험 5건 모두 완료
