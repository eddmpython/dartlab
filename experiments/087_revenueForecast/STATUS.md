# 087 — 매출액 예측 엔진

## 목표
gather 엔진의 컨센서스 데이터를 활용한 매출 예측 앙상블 구축.

## 산출물
- `src/dartlab/engines/gather/types.py` — `RevenueConsensus` 타입 추가, `DomainConfig` jitter 필드
- `src/dartlab/engines/gather/domains/naver.py` — `fetch_revenue_consensus()` 추가
- `src/dartlab/engines/gather/__init__.py` — `Gather.revenue_consensus()` 메서드 추가
- `src/dartlab/engines/gather/http.py` — 랜덤 지터 도입 (도메인별 차등)
- `src/dartlab/engines/common/finance/revenue_forecast.py` — 매출 예측 엔진 v2 (4소스 앙상블)
- `src/dartlab/engines/common/finance/forecast.py` — Structural Break 감지 (`_detect_structural_break`)
- `src/dartlab/engines/ai/tools/defaults/finance.py` — `forecast_revenue` tool 등록
- `src/dartlab/engines/ai/runtime/agent.py` — 성장성/종합 라우팅에 forecast_revenue 추가
- `src/dartlab/engines/ai/conversation/templates/analysis_rules.py` — 예측 보정 규칙 추가

## v1 → v2 변경 요약

| 항목 | v1 | v2 |
|------|----|----|
| 소스 | 3 (시계열+컨센+매크로) | 4 (+ROIC 내재 성장) |
| 매크로 범위 | 산업재만 | β≥0.8 전체 섹터 (12개) |
| 라이프사이클 | 없음 | 4단계 분류 (high_growth/mature/transition/decline) |
| Structural Break | 없음 | Chow Test 기반 감지 |
| 결과 스키마 | 도메인별 상이 가능 | 불변 (projected=horizon, weights 합=1.0) |
| market 파라미터 | 없음 | KR/US/JP (컨센서스 소스 라우팅) |
| ai_context | 없음 | 라이프사이클, ROIC, 괴리, 불확실성 플래그 |
| 스크래핑 안전성 | 결정론적 대기 | 도메인별 랜덤 지터 (naver 0.5~2.0초) |
| AI tool | 없음 | forecast_revenue tool 등록 |
| 보정 규칙 | 없음 | FORECAST_OVERLAY_RULES |

## 실험 결과

### 001 — 앙상블 백테스트 (2026-03-22)

27개 종목, 시계열 only vs 앙상블(시계열+컨센서스) 비교.

| 지표 | 시계열 only | 앙상블 | 차이 |
|------|-----------|--------|------|
| MAE (성장률 %p) | 18.9 | 13.2 | -30.3% |
| 방향성 정확도 | 33.3% | 66.7% | +33.3%p |

**가설 1 채택**: 방향성 +33.3%p (기준 5%p)
**가설 2 채택**: MAE -30.3% (기준 10%)

앙상블 우위 섹터: IT/반도체, 게임, 산업재, 바이오
앙상블 열위 섹터: 2차전지, 비철금속 (컨센서스 과대추정)

### v2 단일 기업 검증 (2026-03-22)

삼성전자(005930) v2 엔진 검증:

- **4소스 앙상블**: timeseries(18%) + consensus(64%) + roic(18%)
- **ROIC 내재 성장**: ROIC 5.7% × 재투자율(캡 150%) = 8.5%
- **라이프사이클**: transition (sign_changes=2, CAGR 4.3%)
- **Structural Break**: 39분기 → 11분기로 분할 감지
- **스키마 assertion**: projected.len=horizon, growth_rates.len=horizon, weights합=1.0 모두 통과
- **기존 unit 테스트**: 873 passed, 0 failures

## 향후 과제
- 역성장 기업 감지 로직 (컨센서스와 시계열 방향 불일치 시 경고)
- proforma.py 연결 (매출 예측 → 3-Statement 자동 생성)
- v1 vs v2 27사 비교 백테스트 (002 실험)
- AI 보정 E2E 테스트 (tool calling provider에서 forecast_revenue 호출)
