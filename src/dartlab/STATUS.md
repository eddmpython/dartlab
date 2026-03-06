# src/dartlab

## 개요
DART 공시 데이터 활용 라이브러리.

## 구조
```
dartlab/
├── core/                    # 공통 기반 (보고서 선택, 테이블 파싱)
├── finance/                 # 재무제표
│   ├── summary/             # 요약재무정보 시계열 추출
│   ├── statements/          # 연결재무제표 (BS, IS, CF)
│   └── segment/             # 부문별 보고 (주석)
# governance/                # 향후: 지배구조
# audit/                     # 향후: 감사의견
# text/                      # 향후: 공시 텍스트 분석
```

## 현황
- 2026-03-06: core/ + finance/summary/ 초기 구축
- 2026-03-06: finance/statements/ 추가
- 2026-03-06: finance/segment/ 추가 — 부문별 보고 파싱 (실험 002_notes 기반)
