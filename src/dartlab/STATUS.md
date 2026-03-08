# src/dartlab

## 개요
DART 공시 데이터 활용 라이브러리. 종목코드 기반 API.

## 구조
```
dartlab/
├── core/                    # 공통 기반 (데이터 로딩, 보고서 선택, 테이블 파싱, 주석 추출)
├── finance/                 # 재무제표
│   ├── summary/             # 요약재무정보 시계열 추출
│   ├── statements/          # 연결재무제표 (BS, IS, CF)
│   ├── segment/             # 부문별 보고 (주석)
│   └── affiliate/           # 관계기업·공동기업 (주석)
# governance/                # 향후: 지배구조
# audit/                     # 향후: 감사의견
# text/                      # 향후: 공시 텍스트 분석
```

## API 요약
```python
from dartlab.finance.summary import fsSummary
from dartlab.finance.statements import statements
from dartlab.finance.segment import segments
from dartlab.finance.affiliate import affiliates

result = fsSummary("005930")     # 요약재무정보 시계열
result = statements("005930")    # BS, IS, CF
result = segments("005930")      # 부문별 보고
result = affiliates("005930")    # 관계기업 투자
```

## 현황
- 2026-03-06: core/ + finance/summary/ 초기 구축
- 2026-03-06: finance/statements/ 추가
- 2026-03-06: finance/segment/ 추가
- 2026-03-06: finance/affiliate/ 추가
- 2026-03-06: 전체 패키지 개선 — stockCode 시그니처, 핫라인 설계, API_SPEC.md
