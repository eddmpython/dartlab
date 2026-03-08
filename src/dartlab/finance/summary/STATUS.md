# finance/summary

## 개요
DART 공시 요약재무정보에서 숫자 브릿지 매칭으로 계정명을 연도간 매핑하여 시계열 생성.

## 파일 목록
| 파일 | 설명 |
|------|------|
| __init__.py | 공개 API (fsSummary, loadYearData, 타입) |
| constants.py | 매칭 임계값, 핵심 계정 목록 |
| types.py | dataclass (AnalysisResult, Segment, BridgeResult, YearAccounts) |
| contentExtractor.py | 요약재무정보 영역 추출 (연결 우선) |
| bridgeMatcher.py | 4단계 숫자 브릿지 매칭 알고리즘 |
| segmentation.py | 전환점 탐지, 구간 분리 |
| pipeline.py | fsSummary(), loadYearData() 오케스트레이터 |

## API
```python
from dartlab.finance.summary import fsSummary
result = fsSummary("005930")  # stockCode
```

## 의존
- `dartlab.core.dataLoader` — loadData, extractCorpName, PERIOD_KINDS
- `dartlab.core.reportSelector` — 보고서 선택
- `dartlab.core.tableParser` — 테이블 파싱, 금액/단위 처리

## 검증
- 실험 001~006 기반, 158개 기업 구간 내 97.7%, 오매칭 0.07%

## 현황
- 2026-03-06: 패키지 초기 구축 (004_fullPipeline.py 기반)
- 2026-03-06: core/ 분리 (공통 모듈), finance/summary/ 재배치
- 2026-03-06: stockCode 시그니처 전환, core 유틸 사용
