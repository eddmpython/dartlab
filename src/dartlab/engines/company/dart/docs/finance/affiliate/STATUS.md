# finance/affiliate

## 개요
연결재무제표 주석에서 관계기업/공동기업 투자 데이터(지분 현황, 변동 내역) 추출.

## 파일 목록
| 파일 | 설명 |
|------|------|
| __init__.py | 공개 API (affiliates, AffiliatesResult, AffiliateProfile, AffiliateMovement) |
| types.py | dataclass (AffiliatesResult, AffiliateProfile, AffiliateMovement) |
| extractor.py | 마크다운 테이블 행 추출 (parseTableRows) |
| parser.py | 프로필/변동 파싱 (일반 + 횡전개) |
| pipeline.py | affiliates() 오케스트레이터 |

## API
```python
from dartlab.finance.affiliate import affiliates
result = affiliates("005930")  # stockCode
```

## 의존
- `dartlab.core.dataLoader` — loadData, extractCorpName, PERIOD_KINDS
- `dartlab.core.notesExtractor` — extractNotesContent, findNumberedSection
- `dartlab.core.reportSelector` — 보고서 선택

## 현황
- 2026-03-06: 패키지 초기 구축 (실험 003_subsidiaries 기반, 횡전개 지원)
- 2026-03-06: stockCode 시그니처 전환, extractor 중복 제거
