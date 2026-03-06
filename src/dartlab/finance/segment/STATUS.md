# finance/segment

## 개요
연결재무제표 주석에서 부문별 보고(사업부문, 제품, 지역) 데이터 추출.

## 파일 목록
| 파일 | 설명 |
|------|------|
| __init__.py | 공개 API (segments, SegmentsResult, SegmentTable) |
| types.py | dataclass (SegmentsResult, SegmentTable) |
| extractor.py | core.notesExtractor re-export (하위 호환) |
| parser.py | 부문 테이블 파싱 (일반 + 횡전개) |
| pipeline.py | segments() 오케스트레이터 |

## API
```python
from dartlab.finance.segment import segments
result = segments("005930")  # stockCode
```

## 의존
- `dartlab.core.dataLoader` — loadData, extractCorpName, PERIOD_KINDS
- `dartlab.core.notesExtractor` — extractNotesContent, findNumberedSection
- `dartlab.core.reportSelector` — 보고서 선택

## 현황
- 2026-03-06: 패키지 초기 구축 (실험 002_notes 기반)
- 2026-03-06: stockCode 시그니처 전환, extractor 중복 제거 → core re-export
