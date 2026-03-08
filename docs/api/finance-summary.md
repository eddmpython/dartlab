---
title: finance.summary
---

# finance.summary

요약재무정보를 시계열로 추출한다. Bridge Matching으로 계정명 변경을 자동 추적해서 시계열 연속성을 보장한다.

## property 접근

```python
c = Company("005930")

c.BS   # 재무상태표 DataFrame
c.IS   # 손익계산서 DataFrame
```

이것으로 충분하다. 아래는 파라미터를 조절하거나 Bridge Matching 결과를 확인할 때 사용한다.

## `fsSummary(period="y", ifrsOnly=True)`

```python
result = c.fsSummary()
```

### 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `period` | `str` | `"y"` | `"y"` 연간, `"q"` 분기, `"h"` 반기 |
| `ifrsOnly` | `bool` | `True` | K-IFRS 기간만 분석 |

### 반환

`AnalysisResult | None`

## AnalysisResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `nYears` | `int` | 분석 연도 수 |
| `period` | `str` | 분석 기간 |
| `FS` | `pl.DataFrame \| None` | 전체 재무제표 시계열 |
| `BS` | `pl.DataFrame \| None` | 재무상태표 |
| `IS` | `pl.DataFrame \| None` | 손익계산서 |
| `allRate` | `float \| None` | 전체 매칭률 (0.0~1.0) |
| `allMatched` | `int` | 매칭된 계정 수 |
| `allTotal` | `int` | 전체 계정 수 |
| `contRate` | `float \| None` | 최장 연속 구간 매칭률 |
| `nPairs` | `int` | 브릿지 쌍 수 |
| `nBreakpoints` | `int` | 변경점 수 |
| `nSegments` | `int` | 연속 구간 수 |
| `segments` | `list[Segment]` | 구간 목록 |
| `breakpoints` | `list[BridgeResult]` | 변경점 목록 |
| `pairResults` | `list[BridgeResult]` | 개별 브릿지 결과 |
| `yearAccounts` | `dict[str, YearAccounts]` | 연도별 계정 데이터 |

## BridgeResult

연도 간 매칭 결과. 인접한 두 연도의 계정을 어떻게 연결했는지 보여준다.

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

변경점 사이의 안정적인 연속 구간.

| 속성 | 타입 | 설명 |
|------|------|------|
| `startYear` | `str` | 시작 연도 |
| `endYear` | `str` | 종료 연도 |
| `nYears` | `int` | 연도 수 |
| `rate` | `float \| None` | 구간 평균 매칭률 |

## 사용 예제

### 기본 사용

```python
from dartlab import Company

c = Company("005930")

# property로 바로 DataFrame
print(c.BS)   # 재무상태표
print(c.IS)   # 손익계산서
```

### Bridge Matching 상세 확인

```python
result = c.fsSummary()

# 전체 통계
print(f"분석 연도: {result.nYears}년")
print(f"매칭률: {result.allRate:.1%}")
print(f"변경점: {result.nBreakpoints}개")

# 연도별 매칭 결과
for pair in result.pairResults:
    print(f"{pair.prevYear} → {pair.curYear}: {pair.rate:.1%} ({pair.matched}/{pair.total})")

# 변경점 확인
for bp in result.breakpoints:
    print(f"변경점: {bp.prevYear} → {bp.curYear} (매칭률 {bp.rate:.1%})")

# 연속 구간
for seg in result.segments:
    print(f"{seg.startYear}~{seg.endYear} ({seg.nYears}년)")
```

### 분기별 분석

```python
result = c.fsSummary(period="q")

print(result.BS)   # 분기별 재무상태표
print(result.IS)   # 분기별 손익계산서
```
