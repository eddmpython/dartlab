# 052_capitalChanges — 자본변동표(SCE) 파싱

## 현황

SCE(Statement of Changes in Equity) 데이터를 finance 엔진에 추가하기 위한 실험.

## 실험 목록

| # | 파일 | 상태 | 요약 |
|---|------|------|------|
| 001 | 001_sceStructure.py | 완료 | SCE 구조 탐색 — 93.5% 보유, 행(변동사유)×열(자본항목) 매트릭스 |
| 002 | 002_detailNormalize.py | 완료 | 정규화+매핑 — 변동사유 97.8%, 자본항목 ~99%+, 32종 snakeId + 13종 자본항목 |
| 003 | 003_pivotPrototype.py | 완료 | 피벗 동작 — 2형태(매트릭스/시계열), 기초+변동=기말 정합 검증, 6사 테스트 |
| 004 | 004_fullValidation.py | 완료 | 전종목 검증 — 성공률 93.5%, 정합성 median 3.39%, 핵심 3항목 ~100% |
| 005 | (프로덕션 배치) | 완료 | sceMapper.py + pivot.py + company.py + 테스트 12개 통과 |

## 핵심 발견

- SCE는 BS/IS/CF와 **완전히 다른 구조** — 같은 계정이 자본항목별로 반복
- `account_nm` = 변동사유 (기초자본, 배당, 당기순이익, 자기주식취득 등)
- `account_detail` = 자본항목 계층 (파이프 구분: 자본금|이익잉여금|기타자본)
- 회사별 계정명 변동 심함 (34~82개) → 동의어 정리 필요
- `[member]` vs `[구성요소]` 표기 불일치 → 정규화 필요
- 27.4% account_id가 `-표준계정코드 미사용-` → account_nm 기반 매핑 필수

### 002 실험 핵심 결과

- **2-tier 매핑 전략**: dict 정확 매칭(250+개) + fallback 패턴 매칭(80+개) → 97.8%
- **공백 제거 정규화**: 추가 0.1%p 효과
- **표준 변동사유 32종** (핵심 15개가 85%+ 커버)
- **표준 자본항목 13종** — 피벗 가능한 안정적 열 집합
- **미매핑 2.2%** = long tail (보통주 전환, 자사주펀드, 임의적립금 이입 등) → 'other' fallback

### 003 실험 핵심 결과

- **2가지 출력 형태**: matrix[year][cause][detail] / series["SCE"]["cause__detail"] = [v1, v2, ...]
- **기초+변동=기말 검증**: 4Q 데이터에서 정합 (2023 삼성전자 차=0원)
- **배당 부호 불일치**: DART 원본에서 일부 연도 양수/음수 혼재 (프로덕션에서 처리 필요)
- **maxQ 전략**: 각 연도에서 가장 높은 분기 보고서만 사용

### 004 실험 핵심 결과

- **피벗 성공률**: 93.5% (2,564/2,743), 실패 0건
- **기초+변동=기말 정합성**: median 3.39%, 80.8%가 10% 이내
- **핵심 커버율**: ending_equity/net_income 100%, beginning_equity 99.9%
- **자본항목**: retained_earnings 100%, share_capital 99.8%, other_equity 96.2%

### 005 프로덕션 배치 결과

- **sceMapper.py**: CAUSE_SYNONYMS(250+) + CAUSE_FALLBACK_PATTERNS(80+) + DETAIL_MAP(40+) + fallback 패턴
- **pivot.py**: `buildSceMatrix()`, `buildSceAnnual()`, `_buildSceMatrixFromDf()`, `_sceMatrixToSeries()`
- **company.py**: `c.sceMatrix` (매트릭스), `c.sce` (시계열) 프로퍼티
- **__init__.py**: `buildSceMatrix`, `buildSceAnnual` 공개 API 추가
- **테스트**: `test_sceFinance.py` — mapper 7개 + pivot 5개 = 12개 전부 통과

## 과제 이력

- [x] 002: account_detail 정규화 + 변동사유 매핑 (97.8% 달성)
- [x] 003: 피벗 프로토타입 (매트릭스/시계열, 6사 검증)
- [x] 004: 전종목 검증 — 성공률 93.5%, 정합성 median 3.39%
- [x] 005: 프로덕션 배치 — sceMapper.py + pivot.py + company.py + 테스트 12개 통과
