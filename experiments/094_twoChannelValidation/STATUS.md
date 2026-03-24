# 094 — 투채널 수집 검증

## 목적

OpenDART API로 직접 수집한 finance/report parquet이 GitHub Release 릴리즈 데이터와 스키마·값이 정확히 일치하는지 검증.
투채널 자동 수집 (`_ensureData()` 3단계 폴백) 흡수의 전제조건.

## 실험 목록

| # | 파일 | 목적 | 상태 |
|---|------|------|------|
| 001 | financeSchemaMatch.py | finance parquet 스키마/값 일치 검증 | 완료 |
| 002 | reportSchemaMatch.py | report parquet 스키마/값 일치 검증 | 완료 |

## 핵심 결과

### finance (001)
- BS/IS/CF/CIS/SCE 모든 재무제표: **값 100% 일치**
- 스키마: 27개 공통 컬럼 dtype 일치 (릴리즈의 `__index_level_0__`은 pandas 잔재)
- **이슈**: OFS(별도재무제표) 수집 시 `enrichFinance()`가 `fs_div=CFS` 기본값 할당 → `consolidated=False` 파라미터 반영 필요

### report (002)
- 공통 22개 apiType 중 19개 행 수 완전 일치, 값 100% 일치
- API가 5개 추가 카테고리 수집 가능 (릴리즈보다 풍부)
- 스키마: 152개 공통 컬럼 dtype 일치

### 결론
**finance/report 모두 투채널 수집 실현 가능.** OFS fs_div 버그만 수정하면 됨.
