# 095 — viewerDocument 뷰어 데이터 레이어

## 목표
sections 수평화 DataFrame → GUI가 바로 렌더링할 수 있는 비교 문서 dict 변환.
신구대조표 패턴 — 기간간 추가/삭제/변경을 블록 단위로 표현.

## 실험 목록

| # | 파일 | 목적 | 상태 |
|---|------|------|------|
| 001 | viewerDocumentProto.py | viewerDocument() 기본 동작 검증 | 완료 — 채택 |
| 002 | qualityValidation.py | 품질 개선 4건 검증 | 완료 — 채택 |

## 001 결과 요약

- 삼성전자 businessOverview: 162블록, modified 70, added 3, removed 1
- **성능**: 381.6ms (목표 500ms PASS)
- **diff 품질**: 숫자 변경("30→75"), 표현 변경("또한→아울러") 정확 포착
- **테이블**: 셀 단위 diff 정확 ("26,331→42,522")
- **JSON**: 161,988bytes 직렬화 성공
- **결론**: 엔진 흡수 준비 완료

## 002 결과 요약

- **개선 1 (path 상속)**: 테이블 35개 전부 path 채워짐 — PASS
- **개선 3 (자동 기간)**: 2025Q3 → 2024Q3 자동 선택 — PASS
- **개선 4 (접기 힌트)**: foldable 0개 (heading 때문에 연속 3개 미만 — 정상)
- **개선 5 (트리 구조)**: depth/parentId 전 블록 할당, orphan 0 — PASS
- **성능**: 356.3ms (Diff_Timeout=0.05 적용, 2100ms→356ms 6배 개선) — PASS
- **JSON**: 187,918bytes 직렬화 성공
- **결론**: 엔진 흡수 준비 완료
