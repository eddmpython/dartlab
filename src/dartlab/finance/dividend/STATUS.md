# finance/dividend

## 개요
사업보고서 "배당에 관한 사항" 섹션에서 주요 배당지표를 파싱하여 시계열 구성.

## 파일 목록
| 파일 | 설명 |
|------|------|
| __init__.py | 공개 API (dividend, DividendResult) |
| types.py | dataclass (DividendResult) |
| parser.py | 배당지표 테이블 파서 (parseDividendTable, parseAmount) |
| pipeline.py | dividend() 오케스트레이터 |

## API
```python
from dartlab.finance.dividend import dividend
result = dividend("005930")  # stockCode
result.timeSeries  # polars DataFrame (year, netIncome, eps, totalDividend, payoutRatio, dividendYield, dps, dpsPreferred)
```

## 의존
- `dartlab.core.dataLoader` — loadData, extractCorpName
- `dartlab.core.reportSelector` — selectReport

## 검증
- 실험 005_dividend 기반
- 267개 종목: 사업보고서 배당 섹션 보유 227개 → 100% 파싱 성공
- 삼성전자 24년, SK하이닉스 24년, 두산에너빌리티 17년 시계열 구성 확인
- 중복 구간 일치율 87~100%

## 현황
- 2026-03-06: 패키지 초기 구축
