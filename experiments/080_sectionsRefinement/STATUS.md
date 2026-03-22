# 080 sections 파이프라인 고도화

## 목표
sections 파이프라인의 3개 가성비 높은 개선점을 실험 검증 후 패키지에 적용한다.

## 개선 항목

| # | 항목 | 영향도 | 난이도 | 상태 |
|---|------|--------|--------|------|
| 1 | tableParser merged cell carry-forward | 높음 | 낮음 | 대기 |
| 2 | heading level 4→6단계 세분화 | 높음 | 낮음 | 대기 |
| 3 | noise/temporal 필터 확장 | 중간 | 낮음 | 대기 |

## 실험 파일

| 파일 | 설명 | 상태 |
|------|------|------|
| 001_mergedCellCarryForward.py | merged cell 빈 첫컬럼 행 복구 검증 | 대기 |
| 002_headingLevelRefinement.py | 6단계 heading level 검증 | 대기 |
| 003_noiseTemporalFilter.py | noise/temporal 필터 확장 검증 | 대기 |
| 004_combinedValidation.py | 283종목 통합 regression | 대기 |
| 005_needlemanWunschDiff.py | NW vs difflib 단락 정렬 비교 | **완료** |

## 실험 결과 요약

### 005 NW vs difflib (2026-03-20)
- 293건, 10종목, 234,914단락
- NW 평균 유사도 88.1 vs difflib 85.1 → **NW +3.0**, 승률 76.8%
- 고품질 매칭 +7.9%, consolidatedNotes(주석)에서 최대 +54.8
- 1000+ 단락에서는 difflib이 우위 → banded NW 필요
- **결론**: 50~500단락 텍스트 diff에 NW 적용 권장
