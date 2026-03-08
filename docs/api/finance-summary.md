---
title: finance.summary
---

# finance.summary

요약재무정보를 시계열로 추출한다. Bridge Matching으로 계정명 변경을 자동 추적한다.

## `fsSummary(stockCode, ifrsOnly=True, period="y")`

```python
from dartlab.finance.summary import fsSummary

result = fsSummary("005930")
```

### 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `stockCode` | `str` | | 종목코드 (6자리) |
| `ifrsOnly` | `bool` | `True` | K-IFRS 기간만 분석 |
| `period` | `str` | `"y"` | `"y"` 연간, `"q"` 분기, `"h"` 반기 |

### 반환

`AnalysisResult | None`

## AnalysisResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `nYears` | `int` | 분석 연도 수 |
| `nPairs` | `int` | 브릿지 쌍 수 |
| `nBreakpoints` | `int` | 변경점 수 |
| `nSegments` | `int` | 연속 구간 수 |
| `allRate` | `float \| None` | 전체 매칭률 |
| `allMatched` | `int` | 전체 매칭된 계정 수 |
| `allTotal` | `int` | 전체 계정 수 |
| `contRate` | `float \| None` | 최장 연속 구간 매칭률 |
| `segments` | `list[Segment]` | 구간 목록 |
| `breakpoints` | `list[BridgeResult]` | 변경점 목록 |
| `pairResults` | `list[BridgeResult]` | 개별 브릿지 결과 |
| `yearAccounts` | `dict[str, YearAccounts]` | 연도별 계정 데이터 |
| `period` | `str` | 분석 기간 |
| `FS` | `pl.DataFrame \| None` | 전체 재무제표 시계열 |
| `BS` | `pl.DataFrame \| None` | 재무상태표 |
| `IS` | `pl.DataFrame \| None` | 손익계산서 |

## BridgeResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `curYear` | `str` | 당기 |
| `prevYear` | `str` | 전기 |
| `rate` | `float` | 매칭률 |
| `matched` | `int` | 매칭된 계정 수 |
| `total` | `int` | 전체 계정 수 |
| `yearGap` | `int` | 연도 차이 |
| `pairs` | `dict[str, str]` | 매칭 쌍 (당기계정 → 전기계정) |

## Segment

| 속성 | 타입 | 설명 |
|------|------|------|
| `startYear` | `str` | 시작 연도 |
| `endYear` | `str` | 종료 연도 |
| `nYears` | `int` | 연도 수 |
| `rate` | `float \| None` | 구간 평균 매칭률 |

## 사용 예제

```python
from dartlab import Company

c = Company("005930")
result = c.fsSummary()

# DataFrame 출력
print(result.FS)

# 브릿지 결과
for pair in result.pairResults:
    print(f"{pair.prevYear} → {pair.curYear}: {pair.rate:.1%}")

# 변경점 확인
for bp in result.breakpoints:
    print(f"변경점: {bp.prevYear} → {bp.curYear}")
```
