---
title: finance.summary
---

# finance.summary

요약재무정보를 시계열로 추출한다. **Bridge Matching**으로 계정명 변경을 자동 추적해서 시계열 연속성을 보장한다.

## 사용법

### property 접근 (간편)

```python
c = dartlab.Company("005930")

c.BS   # 재무상태표 DataFrame
c.IS   # 손익계산서 DataFrame
```

> 대부분의 경우 이것으로 충분하다. 아래는 Bridge Matching 분석 결과를 확인하거나 분기별 데이터가 필요할 때 사용한다.

### fsSummary() 메서드 (상세)

```python
result = c.fsSummary()
result = c.fsSummary(period="q")           # 분기별
result = c.fsSummary(period="h")           # 반기별
result = c.fsSummary(ifrsOnly=False)       # K-GAAP 포함
```

---

## 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `period` | `str` | `"y"` | `"y"` 연간, `"q"` 분기, `"h"` 반기 |
| `ifrsOnly` | `bool` | `True` | K-IFRS 기간만 분석 (2011~) |

### period 값

| 값 | 의미 | 포함 보고서 | 열 형식 |
|-----|------|------------|---------|
| `"y"` | 연간 | 사업보고서 | `2020`, `2021`, ... |
| `"q"` | 분기별 | 1분기 + 반기 + 3분기 + 사업 | `2020Q1`, `2020Q2`, ... |
| `"h"` | 반기별 | 반기 + 사업 | `2020H1`, `2020H2`, ... |

### 반환

`AnalysisResult | None`

---

## AnalysisResult

Bridge Matching 분석의 전체 결과를 담는 객체.

### 주요 속성

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `nYears` | `int` | 분석 연도 수 |
| `period` | `str` | 분석 기간 (`"y"`, `"q"`, `"h"`) |

### 재무제표 DataFrame

| 속성 | 타입 | 설명 |
|------|------|------|
| `FS` | `pl.DataFrame \| None` | BS + IS 통합 시계열 |
| `BS` | `pl.DataFrame \| None` | 재무상태표 |
| `IS` | `pl.DataFrame \| None` | 손익계산서 |

### Bridge Matching 통계

| 속성 | 타입 | 설명 |
|------|------|------|
| `allRate` | `float \| None` | 전체 매칭률 (0.0~1.0) |
| `allMatched` | `int` | 매칭된 계정 수 |
| `allTotal` | `int` | 전체 계정 수 |
| `contRate` | `float \| None` | 최장 연속 구간 매칭률 |
| `nPairs` | `int` | 브릿지 쌍 수 |
| `nBreakpoints` | `int` | 변경점(breakpoint) 수 |
| `nSegments` | `int` | 연속 구간(segment) 수 |

### 상세 데이터

| 속성 | 타입 | 설명 |
|------|------|------|
| `segments` | `list[Segment]` | 연속 구간 목록 |
| `breakpoints` | `list[BridgeResult]` | 변경점 목록 |
| `pairResults` | `list[BridgeResult]` | 연도별 매칭 결과 |
| `yearAccounts` | `dict[str, YearAccounts]` | 연도별 계정 데이터 |

---

## BridgeResult

인접한 두 연도의 계정 매칭 결과. 어떤 계정이 어떻게 연결되었는지 확인할 수 있다.

| 속성 | 타입 | 설명 |
|------|------|------|
| `curYear` | `str` | 당기 (예: `"2024"`) |
| `prevYear` | `str` | 전기 (예: `"2023"`) |
| `rate` | `float` | 매칭률 |
| `matched` | `int` | 매칭된 계정 수 |
| `total` | `int` | 전체 계정 수 |
| `yearGap` | `int` | 연도 차이 |
| `pairs` | `dict[str, str]` | 매칭 쌍 (당기계정명 → 전기계정명) |

---

## Segment

변경점 사이의 안정적인 연속 구간. 계정 체계가 일관되게 유지된 기간을 나타낸다.

| 속성 | 타입 | 설명 |
|------|------|------|
| `startYear` | `str` | 시작 연도 |
| `endYear` | `str` | 종료 연도 |
| `nYears` | `int` | 연도 수 |
| `rate` | `float \| None` | 구간 평균 매칭률 |

---

## Bridge Matching 이해

DART 공시의 요약재무정보는 매년 계정명이 미세하게 바뀔 수 있다. Bridge Matching은 금액과 명칭 유사도를 조합해서 같은 계정을 자동으로 추적한다.

### 4단계 매칭 과정

```
2022                    2023                    2024
매출액 ──────────────── 매출액 ──────────────── 수익(매출액)
영업이익 ────────────── 영업이익 ────────────── 영업이익
당기순이익 ──────────── 당기순이익 ──────────── 당기순이익(손실)
```

1. **정확 매칭**: 금액이 동일한 계정 연결 (허용 오차 0.5 이내)
2. **재작성 매칭**: 금액 오차 5% 이내 + 명칭 유사도 80% 이상
3. **명칭 변경 매칭**: 금액 오차 5% 이내 + 명칭 유사도 60% 이상
4. **특수 항목 매칭**: 주당이익(EPS) 등 소수점 단위 항목

### 변경점(breakpoint) 탐지

매칭률이 85% 이하로 떨어지면 변경점으로 판정하고 구간을 분리한다. 기업 합병, 연결/별도 전환, 대규모 구조 변경이 일어난 시점을 자동으로 찾아낸다.

> Bridge Matching 알고리즘의 자세한 설명은 [Bridge Matching](../user-guide/bridge-matching)을 참고한다.

---

## 사용 예제

### 기본 사용

```python
import dartlab

c = dartlab.Company("005930")

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
print(f"연속 구간: {result.nSegments}개")
```

### 연도별 매칭 결과

```python
for pair in result.pairResults:
    print(f"{pair.prevYear} → {pair.curYear}: {pair.rate:.1%} ({pair.matched}/{pair.total})")
```

### 변경점 확인

```python
for bp in result.breakpoints:
    print(f"변경점: {bp.prevYear} → {bp.curYear} (매칭률 {bp.rate:.1%})")
    # 어떤 계정이 바뀌었는지
    for cur, prev in bp.pairs.items():
        if cur != prev:
            print(f"  {prev} → {cur}")
```

### 연속 구간

```python
for seg in result.segments:
    print(f"{seg.startYear}~{seg.endYear} ({seg.nYears}년, 매칭률 {seg.rate:.1%})")
```

### 분기별 분석

```python
result = c.fsSummary(period="q")

print(result.BS)   # 분기별 재무상태표
# account | 2020Q1 | 2020Q2 | 2020Q3 | 2020Q4 | 2021Q1 | ...

print(result.IS)   # 분기별 손익계산서
```

### BS + IS 통합 시계열

```python
result = c.fsSummary()
print(result.FS)   # 재무상태표 + 손익계산서 한 DataFrame
```

