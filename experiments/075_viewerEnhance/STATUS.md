# 075_viewerEnhance — 공시 뷰어 강화 데이터 레이어 검증

## 목표
기존 scan/insight/diff/sections 파이프라인 출력을 뷰어에서 효과적으로 소비하기 위한
데이터 변환/조합/연결 방법을 검증한다. UI 코드를 직접 수정하지 않고 데이터 레이어에서
가능성을 확인한다.

## 073과의 차이
- 073: scan 엔진의 **데이터 추출/등급 산출** 검증 (report parquet 전수 스캔)
- 075: scan 결과 + insight + diff + sections를 **뷰어에서 소비하는 형태** 검증

## 진행 상황 (v2 — non-period 버그 수정 후 전체 재검증 완료)

### 공통 수정
- non-period 컬럼 필터를 하드코딩 set → 정규식 `^\d{4}(Q[1-4])?$`로 교체
- 모든 실험에서 메타 컬럼 오염 완전 제거

### scan 계열
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | scanDashboardPayload | ✅ 완료 | 3사 11/11영역 유효, null 0, JSON 3.3~3.9KB. InsightResult 호환 변환 완전 가능. insight.governance와 scan_governance 관점 분리 |
| 004 | scanPositionMap | ✅ 완료 | 10사 모두 3축+ percentile 산출. governance 정규분포, workforce/debt 극우편향. **로딩 266초 → 캐시 필수**. capital 이산변수 → 레이더 부적합 |

### diff 계열
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 002 | multiPeriodDiffMatrix | ✅ v2 완료 | text-only 필터 추가. 서술형 핫 토픽 정확 식별: rawMaterial, fundraising, salesOrder 등. HeatmapSpec 15×19~39 |
| 005 | timelineDiffStream | ✅ v2 완료 | 매칭률 89.8~97.8% (v1: 83~87%). 삼성 258행×40기간, LG에너지 93행×20기간. 현대차 2022Q1→2022 31.8% = 구조 대개편 시점 |

### cross-reference 계열
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 003 | textFinanceBridge | ✅ v2 완료 | 10사 추출 631개, 매칭 342개, **전체 매칭률 54.2%**, 평균 오차 1.89%. 매출액 0.0~0.07% 정확 매칭. 연간→Q4 변환이 핵심 |
| 006 | crossTopicMention | ✅ v2 완료 | 5사 avg_degree 4.7~5.9 (v1: 6.2~8.2, 메타 오염 제거). 허브: fsSummary/businessOverview 5/5사 |

## 종합 판단

### 즉시 흡수 가능 (채택)
1. **001 scan 대시보드 payload** — InsightDashboard에 scan 4축 영역 추가
2. **002 diff 매트릭스** — topic 변화 히트맵 (text-only 모드 포함)
3. **003 텍스트-재무 교차** — 텍스트 금액 → finance 계정 자동 연결 (54.2%, 오차 1.89%)
4. **006 topic 그래프** — "관련 topic" 자동 추천 (RELATED_TOPICS 대체)

### 조건부 흡수 (개선 필요)
5. **004 시장 위치 맵** — percentile 유효하나 266초 로딩 → 서버 캐시 구조 필요
6. **005 타임라인 스트림** — 매칭률 우수(89.8~97.8%)하나 행수 과다 → 핵심 slot 필터 필요
