# 071_sectionsCompare — sections 기반 기업간 비교 실험

## 목표
sections를 직접 비교하여 기업간 비교의 가능성 탐색 + 뷰어 소비까지 기획

## 종목 4쌍
| 쌍 | A | B | 목적 |
|---|---|---|---|
| 동종대기업 | 005930 삼성전자 | 000660 SK하이닉스 | 핵심 비교 |
| 대/중소 | 005930 | 000020 동화약품 | 규모 차이 |
| 관계회사 | 005930 | 006400 삼성SDI | 그룹 내 |
| 이업종 | 005930 | 005380 현대차 | 업종 차이 한계 |

## 실험 현황

| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | topic coverage 비교 | **완료** | Jaccard 0.92~0.98, finance/report 100% 일치 |
| 002 | finance 수치 비교 | **완료** | ratio 35/35 100% 호환, 기간 39/39 100%, 핵심 계정 100% |
| 003 | 텍스트 비교 | **완료** | 키워드 비교 유의미 (동종 642개 공통), similarity 낮음 (0.04~0.18) |
| 004 | 테이블 항목 비교 | **완료** | finance Jac=0.47, report Jac=0.30, docs Jac=0.06, ratios 1.000 |
| 005 | 뷰어 소비 기획 | **완료** | payload 5.6KB, 엔드포인트 3개, UI 4개로 충분 |
| 006 | 파이프라인 프로파일링 | **완료** | 3대 병목: DF조립(35%) ≈ expand(34%) > topicRows(21%), 단일 지배 병목 없음 |
| 007 | 파이프라인 최적화 | **완료** | _rowCadenceMeta 86% 단축, 삼성전자 전체 23% 단축 (3.2s→2.4s), 66 테스트 통과 |

## 핵심 결론

### sections 기반 기업간 비교 — **실현 가능**

1. **topic 정렬 해결됨**: 업종/규모 불문 Jaccard 0.92+ (sectionMappings.json 덕분)
2. **finance 비교 즉시 가능**: ratio 100% 호환, 핵심 계정 100% 존재, 기간 100% 교집합
3. **텍스트 비교는 키워드 중심**: SequenceMatcher 부적합, 키워드 클라우드가 인사이트 제공
4. **docs table 비교 어려움**: 원본 markdown이라 항목명 정규화 없이 비교 불가 (Jac 0.06)
5. **payload 매우 가벼움**: 5.6KB (500KB 목표의 1%)

### 비교 뷰어 최소 구현 범위

**데이터 레이어**: Company API 위 얇은 래퍼 (별도 Compare 클래스 불필요할 수 있음)
- `c.topics` 교집합 → topic coverage
- `c.ratios` 나란히 → finance 비교
- `c.sections` text body → 키워드 추출

**서버**: 엔드포인트 3개
- `/api/compare/{codeA}/{codeB}/overview` — 랜딩
- `/api/compare/{codeA}/{codeB}/finance` — 재무 비교
- `/api/compare/{codeA}/{codeB}/topic/{topic}` — topic 상세

**UI**: 컴포넌트 4개
- CompareHeader, CompareFinance, CompareTopicGrid, CompareTopicDetail

## 엔진 흡수 판정

| 기준 | 결과 | 판정 |
|------|------|------|
| 동종 topic coverage 70%+ | 97.9% | **통과** |
| finance 교집합 90%+ | ratio 100%, 핵심 계정 100% | **통과** |
| payload 500KB 이하 | 5.6KB | **통과** |
| 3개+ topic 수치 비교 유의미 | ratio 34개 항목 side-by-side | **통과** |
| 뷰어 소비 구조 명확 | 3 엔드포인트 + 4 컴포넌트 | **통과** |

→ **모든 기준 통과. `engines/common/compare.py` 구현 검토 가능.**

## 다음 단계 (제안)

1. `engines/common/compare.py` — 비교 함수 3개 (overview/finance/topicDetail)
2. `server/__init__.py` — 엔드포인트 3개 추가
3. `ui/src/lib/components/Compare*.svelte` — UI 4개 컴포넌트
4. WS-1(UI) / WS-2(서버) 워크스트림에서 각각 구현

실험일: 2026-03-19
