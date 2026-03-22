# 085_mertonEngine — Merton/KMV 구조 모형 + 5축 스코어카드

## 요약

Merton (1974) 구조 모형을 dartlab 부실 예측에 도입.
시장 기반 D2D(Distance to Default) + PD(Default Probability)로
기존 4축 회계 기반 스코어카드를 5축으로 확장.

## 실험 현황

| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | mertonSolver | **완료** | 6개 프로필 모두 수렴 (3~6회). D2D: 0.94~6.66 |
| 002 | volatilityCalc | **완료** | 합성 데이터 검증 OK. yfinance pyarrow 이슈 확인. |
| 003 | fiveAxisScorecard | **완료** | 조기 경보 검증: 회계 AAA + D2D 0.8 → 5축 BBB watch |
| 004 | sectorBenchmarkD2D | **완료** | 10개 섹터 D2D 벤치마크 도출. 유틸(6.0) 최고, 에너지(2.9) 최저 |

## 엔진 흡수

- `engines/common/finance/merton.py` — Merton 솔버 + 변동성 계산 (신규)
- `engines/analysis/insight/distress.py` — 5축 확장, Merton 해석/정규화
- `engines/analysis/insight/types.py` — MarketDataForDistress 추가
- `engines/analysis/insight/pipeline.py` — marketData 파라미터 + Merton 흐름
- `engines/analysis/insight/benchmark.py` — SectorBenchmark D2D 필드 + 초기값
- `engines/analysis/insight/spec.py` — Merton 등록, 5축 메타
