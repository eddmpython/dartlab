# Tutorials 현황

## 개요
단계별 튜토리얼 문서. `notebooks/tutorials/`의 Jupyter 노트북과 1:1 매칭하며, 현재 공개 서사는 `Company -> sections -> show -> trace`를 기준으로 정리한다.

## 파일 목록

| 파일 | 제목 | 노트북 | 상태 |
|------|------|--------|------|
| index.md | 튜토리얼 인덱스 | - | 완료 |
| 01_quickstart.md | 첫 분석 (sections, show, trace) | 01_quickstart.ipynb | 완료 |
| 02_financial.md | 재무 심화 (배당, 직원, Notes) | 02_financial.ipynb | 완료 |
| 03_disclosure.md | 공시 텍스트 (사업, MD&A, 개요) | 03_disclosure.ipynb | 완료 |
| 04_advanced.md | 고급 분석 (Notes, 거버넌스, 비교) | 04_advanced.ipynb | 완료 |

## 규칙
- 파일명: `XX_camelCase.md` (번호 접두사 + camelCase)
- 번호 접두사는 빌드 시 자동 제거됨 (01_quickstart → tutorials/quickstart)
- 각 문서에 Colab 배지 포함
- `notebooks/tutorials/`와 1:1 매칭 유지
- 현행 공개 흐름은 `sections -> show -> trace`
