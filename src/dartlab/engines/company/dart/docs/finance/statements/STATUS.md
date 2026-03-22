# finance/statements

## 개요
연결재무제표(BS, IS, CF)를 개별 제표로 분리하여 시계열 DataFrame 추출.

## 파일 목록
| 파일 | 설명 |
|------|------|
| __init__.py | 공개 API (statements, StatementsResult) |
| types.py | dataclass (StatementsResult) |
| extractor.py | 연결재무제표 섹션 추출, 개별 제표 분리 |
| pipeline.py | statements() 오케스트레이터 |

## API
```python
from dartlab.finance.statements import statements
result = statements("005930")  # stockCode
```

## 의존
- `dartlab.core.dataLoader` — loadData, extractCorpName, PERIOD_KINDS
- `dartlab.core.reportSelector` — 보고서 선택
- `dartlab.core.tableParser` — 테이블 파싱, 금액/단위 처리

## 현황
- 2026-03-06: 패키지 초기 구축
- 2026-03-06: stockCode 시그니처 전환, nPeriods→nYears 통일
- 2026-03-06: splitStatements 중복키 버그 수정 (뒤에 나온 게 우선)
