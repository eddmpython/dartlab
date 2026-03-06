# core

## 개요
모든 DART 공시 분석에서 공통으로 사용하는 기반 모듈.

## 파일 목록
| 파일 | 설명 |
|------|------|
| __init__.py | 공개 API |
| constants.py | 단위 스케일(UNIT_SCALE), 자산총계 키워드(ASSET_TOTAL_KEYWORDS) |
| dataLoader.py | 종목코드 → DataFrame 로딩, 기업명 추출, PERIOD_KINDS |
| notesExtractor.py | 연결재무제표 주석 섹션 추출, 번호 섹션 검색 |
| reportSelector.py | 연도별 사업보고서 선택 (원본 > 기재정정 > 첨부) |
| tableParser.py | 마크다운 테이블 파싱, 금액 파싱, 단위 정규화, 계정 추출 |

## 핫라인 설계
- `PERIOD_KINDS`: 4개 pipeline이 공유하는 기간별 보고서 종류 맵
- `loadData()`: 파일 경로 로직 1곳 집중, pipeline은 stockCode만 전달
- `extractCorpName()`: 기업명 추출 로직 1곳 집중
- `extractNotesContent()`: 주석 섹션 추출 (segment, affiliate 공유)
- `findNumberedSection()`: 번호 매긴 섹션 검색 (segment, affiliate 공유)

## 현황
- 2026-03-06: finance/에서 공통 모듈 분리
- 2026-03-06: dataLoader.py, notesExtractor.py 추가 (핫라인 설계)
