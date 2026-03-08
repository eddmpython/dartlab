---
title: finance.statements
---

# finance.statements

연결재무제표를 재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)로 분리해서 시계열로 추출한다.

## property 접근

```python
c = Company("005930")

c.BS   # 재무상태표
c.IS   # 손익계산서
c.CF   # 현금흐름표
```

> `c.BS`와 `c.IS`는 `fsSummary` 모듈(요약재무정보)에서 추출한다. `c.CF`는 `statements` 모듈에서 추출한다. 요약재무정보에는 현금흐름표가 없기 때문이다.

## get()으로 전체 접근

```python
result = c.get("statements")

result.BS    # 재무상태표 — 자산, 부채, 자본 상세 항목
result.IS    # 손익계산서 — 매출, 비용, 이익 상세 항목
result.CF    # 현금흐름표 — 영업/투자/재무 활동
```

### 파라미터

`get()`에 `period` 파라미터를 넘길 수 있다.

```python
result = c.get("statements", period="q")   # 분기별
result = c.get("statements", period="h")   # 반기별
```

| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `period` | `str` | `"y"` | `"y"` 연간, `"q"` 분기, `"h"` 반기 |
| `ifrsOnly` | `bool` | `True` | K-IFRS 기간만 |

## StatementsResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `period` | `str` | 분석 기간 |
| `nYears` | `int` | 연도 수 |
| `BS` | `pl.DataFrame \| None` | 재무상태표 |
| `IS` | `pl.DataFrame \| None` | 손익계산서 |
| `CF` | `pl.DataFrame \| None` | 현금흐름표 |

## BS vs IS 차이 (fsSummary vs statements)

| | fsSummary (c.BS, c.IS) | statements |
|-----|------------------------|------------|
| 소스 | 요약재무정보 | 연결재무제표 본문 |
| 항목 수 | 20~30개 핵심 항목 | 50~200개 상세 항목 |
| Bridge Matching | 적용 | 미적용 |
| 현금흐름표 | 없음 | 있음 (CF) |
| 시계열 연속성 | 우수 (자동 추적) | 원문 그대로 |
| 용도 | 시계열 트렌드 분석 | 상세 항목 확인 |

일반적으로 시계열 분석은 `c.BS`, `c.IS` (fsSummary)를, 상세 항목 확인은 `c.get("statements")`를 사용한다.

## 사용 예제

```python
from dartlab import Company

c = Company("005930")

# 재무상태표 — 주요 항목
print(c.BS)
# account | 2015 | 2016 | ... | 2024
# 자산총계
# 유동자산
# 비유동자산
# 부채총계
# 자본총계

# 현금흐름표
print(c.CF)
# account | 2015 | 2016 | ... | 2024
# 영업활동 현금흐름
# 투자활동 현금흐름
# 재무활동 현금흐름

# 분기별 상세
result = c.get("statements", period="q")
print(result.IS)   # 분기별 손익계산서 상세 항목
```
