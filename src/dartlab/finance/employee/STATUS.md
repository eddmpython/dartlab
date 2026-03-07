# finance/employee — 직원 현황 분석

## 기능
사업보고서 "직원 등의 현황" 섹션에서 핵심 지표 시계열 추출.

## API
```python
from dartlab.finance.employee import employee, EmployeeResult

result = employee("005930")  # -> EmployeeResult | None
```

## EmployeeResult
| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 시계열 기간 수 |
| timeSeries | pl.DataFrame | 연도별 직원 데이터 |

## timeSeries 컬럼
| 컬럼 | 설명 | 단위 |
|------|------|------|
| year | 사업연도 | int |
| totalEmployees | 총 직원수 | 명 |
| avgTenure | 평균근속연수 | 년 |
| totalSalary | 연간급여총액 | 백만원 (종목마다 다를 수 있음) |
| avgSalary | 1인평균급여 | 백만원 (종목마다 다를 수 있음) |

## 파싱 성공률
- 267종목 기준 99.1% (사업보고서 보유 229종목 중 227건)
- 실패 2건은 데이터 수집 문제 (파서 문제 0건)
- 리츠/스팩 직원 0명은 None 반환

## 파싱 전략
1. 합계 행 (합 계/합계) 에서 셀 인덱스 기반 추출
2. 표준 구조 [6,7,8,9] → shifted [5,6,7,8] → 변형 [2,7,8,9] 순차 시도
3. avgSalary 없는 데이터는 신뢰 부족으로 필터링

## 주의사항
- 급여 단위가 종목/연도마다 다를 수 있음 (백만원 vs 천원)
- 2015년 이전 보고서는 테이블 구조 차이로 파싱 불가능한 경우 있음
- 리츠, 스팩 등 직원 없는 기업은 None 반환

## 실험
- experiments/006_employee/ (001~005)
