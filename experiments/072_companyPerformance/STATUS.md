# 072 Company 속도 최적화

## 목표
Company 워크플로우 6.84s → 최대한 절감. 기능 변경 0, 테스트 803개 전부 통과.

## 결과 요약

| 실험 | 대상 | before | after | 배율 | 판정 |
|---|---|---|---|---|---|
| 001 | availableApiTypes 캐시 | 0.25s/call | 0.000001s (2회차+) | 200,000x | **채택** |
| 002 | _indexDocsRows Polars native | 0.65s | 0.019s | 34x | **채택** |
| 003 | sectionsDiff hash 벡터화 | 0.55s | 0.09s | 6.1x | **채택** |
| 004 | _comparablePathInfo lru_cache | 3.05s | 2.96s | 1.0x | 기각 |
| 005 | _splitContentBlocks 최적화 | 2.74s | 3.04s | 0.9x | 기각 |
| 006 | sections dict 조립 | — | — | 전체 2.9% | 기각 |
| 007 | profile.facts docsBlocks 벡터화 | 0.66s | 0.008s | 80.6x | **채택** |

## 채택 적용 내역

1. **001**: `_report_accessor.py` — `availableApiTypes` 프로퍼티에 `_cache["_availableApiTypes"]` 추가
2. **002**: `company.py` — `_indexDocsRows` iter_rows → unique(maintain_order=True) + group_by agg
3. **003**: `diff.py` — `sectionsDiff` md5+iter_rows → Polars hash()+to_list() 벡터화, hashlib 제거
4. **007**: `_profile_accessor.py` — docsBlocks iter_rows → Polars select/with_columns/coalesce 벡터화

## 기각 사유

- **004**: _comparablePathInfo 자체 비용이 너무 작아 lru_cache 오버헤드와 상쇄
- **005**: 현재 구현이 이미 최적. 추가 flag 배열 생성이 역효과
- **006**: dict 조립은 전체의 2.9%(0.08s)에 불과. 진짜 병목은 텍스트 파싱(97%)

## 종합 효과

| 연산 | 이전 | 이후 | 절감 |
|---|---|---|---|
| availableApiTypes (2회차+) | 0.25s | ~0s | -0.25s |
| _indexDocsRows | 0.65s | 0.02s | -0.63s |
| sectionsDiff | 0.55s | 0.09s | -0.46s |
| profile.facts (docs 부분) | 0.66s | 0.008s | -0.65s |
| **합계** | **2.11s** | **0.12s** | **-1.99s** |

sections 파이프라인(2.7s)은 Python 문자열 처리 자체의 한계 → Rust 마이그레이션 대상.

## 테스트
- 803 passed, 1 skipped (test_affiliate.py는 network 리네이밍 미완 — 별도 이슈)
