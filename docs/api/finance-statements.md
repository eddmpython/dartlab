---
title: finance.statements
---

# finance.statements

연결재무제표를 재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)로 분리해서 시계열로 추출한다.

## `statements(stockCode, ifrsOnly=True, period="y")`

```python
from dartlab.finance.statements import statements

result = statements("005930")
```

### 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `stockCode` | `str` | | 종목코드 |
| `ifrsOnly` | `bool` | `True` | K-IFRS 기간만 |
| `period` | `str` | `"y"` | `"y"` 연간, `"q"` 분기, `"h"` 반기 |

### 반환

`StatementsResult | None`

## StatementsResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `period` | `str` | 분석 기간 |
| `nYears` | `int` | 연도 수 |
| `BS` | `pl.DataFrame \| None` | 재무상태표 |
| `IS` | `pl.DataFrame \| None` | 손익계산서 |
| `CF` | `pl.DataFrame \| None` | 현금흐름표 |

## 사용 예제

```python
from dartlab import Company

c = Company("005930")
result = c.statements()

print(result.BS)  # 자산, 부채, 자본 상세 항목
print(result.IS)  # 매출, 비용, 이익 상세 항목
print(result.CF)  # 영업/투자/재무 현금흐름
```
