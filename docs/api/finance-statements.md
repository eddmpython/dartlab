---
title: finance.statements
---

# finance.statements

연결재무제표를 재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)로 분리해서 시계열로 추출한다. `Company`의 기본 공개 흐름은 `sections -> show -> trace`지만, 상세 재무 계정을 직접 다루려면 `finance.statements` 계층으로 내려간다. 요약재무정보보다 **상세한 항목**(50~200개)을 원문 그대로 제공한다.

## 사용법

### Company shortcut

```python
c = dartlab.Company("005930")

c.BS   # 재무상태표
c.IS   # 손익계산서
c.CF   # 현금흐름표
```

### `get()`으로 전체 접근

```python
result = c.get("statements")

result.BS    # 재무상태표 — 자산, 부채, 자본 상세 항목
result.IS    # 손익계산서 — 매출, 비용, 이익 상세 항목
result.CF    # 현금흐름표 — 영업/투자/재무 활동
```

### 분기별·반기별

```python
result = c.get("statements", period="q")   # 분기별
result = c.get("statements", period="h")   # 반기별
```

---

## 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `period` | `str` | `"y"` | `"y"` 연간, `"q"` 분기, `"h"` 반기 |
| `ifrsOnly` | `bool` | `True` | K-IFRS 기간만 |

---

## StatementsResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `period` | `str` | 분석 기간 |
| `nYears` | `int` | 연도 수 |
| `BS` | `pl.DataFrame \| None` | 재무상태표 |
| `IS` | `pl.DataFrame \| None` | 손익계산서 |
| `CF` | `pl.DataFrame \| None` | 현금흐름표 |

---

## fsSummary vs statements 비교

두 모듈은 같은 재무제표를 다른 소스에서 추출한다. 용도에 따라 선택한다.

| | fsSummary (`c.fsSummary()`) | statements (`c.get("statements")`) |
|-----|------------------------|------------|
| **소스** | 요약재무정보 | 연결재무제표 본문 |
| **항목 수** | 20~30개 핵심 항목 | 50~200개 상세 항목 |
| **Bridge Matching** | 적용 (계정명 변경 자동 추적) | 미적용 (원문 그대로) |
| **현금흐름표** | 없음 | 있음 (CF) |
| **시계열 연속성** | 우수 (자동 추적) | 원문 의존 |
| **용도** | 장기 트렌드 분석 | 상세 항목 확인 |

> **일반 규칙**: 공개 board에서는 `c.show("BS")`로 시작한다. 더 상세한 계정 분해가 목적이면 `c.BS`, `c.CF`, `c.get("statements")`, `c.fsSummary()` 같은 finance 계층으로 내려간다.

---

## 사용 예제

### 재무상태표 — 주요 항목

```python
import dartlab

c = dartlab.Company("005930")

print(c.BS)
# account         | 2015       | 2016       | ... | 2024
# 자산총계        | 262,174,324| 261,381,064| ... | ...
# 유동자산        | 124,140,661| 134,506,949| ... | ...
#   현금및현금성자산| 22,636,744| 32,111,442| ... | ...
#   매출채권       | 25,168,026| 24,348,622| ... | ...
# 비유동자산      | 138,033,663| 126,874,115| ... | ...
# 부채총계        | 63,119,716| 54,704,095| ... | ...
# 자본총계        | 199,054,608| 206,676,969| ... | ...
```

### 현금흐름표

```python
print(c.CF)
# account                 | 2015        | 2016        | ...
# 영업활동 현금흐름        | 40,061,761 | 47,386,037  | ...
# 투자활동 현금흐름        | -28,017,281| -26,252,505 | ...
# 재무활동 현금흐름        | -10,740,937| -9,756,700  | ...
```

### 분기별 상세

```python
result = c.get("statements", period="q")
print(result.IS)
# account  | 2023Q1 | 2023Q2 | 2023Q3 | 2023Q4 | 2024Q1 | ...

print(result.CF)
# account  | 2023Q1 | 2023Q2 | 2023Q3 | 2023Q4 | 2024Q1 | ...
```

### 재무제표 없는 항목 확인

```python
result = c.get("statements")
print(f"BS 항목 수: {result.BS.height if result.BS is not None else 0}")
print(f"IS 항목 수: {result.IS.height if result.IS is not None else 0}")
print(f"CF 항목 수: {result.CF.height if result.CF is not None else 0}")
```

