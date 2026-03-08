---
title: Bridge Matching
---

# Bridge Matching

## 문제

DART 공시의 요약재무정보는 매년 계정명이 미세하게 바뀐다.

- K-IFRS 개정으로 계정명 변경 ("매출액" → "수익(매출액)")
- 회사의 자체적인 표기 변경 ("당기순이익" → "당기순이익(손실)")
- 연결/별도 전환 시 계정 구조 변동

단순 계정명 매칭으로는 시계열이 끊긴다. Bridge Matching은 **금액과 명칭 유사도를 조합**해서 같은 계정을 자동으로 추적한다.

---

## 4단계 매칭

```
2022                    2023                    2024
매출액 ──────────────── 매출액 ──────────────── 수익(매출액)
영업이익 ────────────── 영업이익 ────────────── 영업이익
당기순이익 ──────────── 당기순이익 ──────────── 당기순이익(손실)
```

### 1단계: 정확 매칭

금액이 동일한 계정을 연결한다. 허용 오차 0.5 이내.

> 동일 연도의 전기 값과 당기 값이 같으면 같은 계정으로 판단하는 가장 확실한 방법이다.

### 2단계: 재작성 매칭

금액 오차 5% 이내 + 명칭 유사도 80% 이상.

> 재작성(restatement)으로 과거 금액이 소급 조정된 경우. 예: 기준서 변경으로 비교 재무제표의 금액이 변경.

### 3단계: 명칭 변경 매칭

금액 오차 5% 이내 + 명칭 유사도 60% 이상.

> 계정 명칭이 바뀌었지만 실질적으로 같은 항목인 경우. 예: "매출액" → "수익(매출액)"

### 4단계: 특수 항목 매칭

주당이익(EPS) 등 소수점 단위 항목을 별도 처리한다.

> 일반 계정은 백만원 단위이지만, EPS는 원 단위이므로 별도의 매칭 로직이 필요하다.

---

## 변경점 탐지

매칭률이 **85% 이하**로 떨어지면 전환점(breakpoint)으로 판정하고 구간을 분리한다.

변경점이 발생하는 대표적인 상황:

| 상황 | 설명 |
|------|------|
| 기업 합병 | 합병 전후 재무제표 구조가 완전히 달라짐 |
| 연결/별도 전환 | 연결 → 별도 또는 별도 → 연결로 전환 |
| 대규모 사업 재편 | 사업부 분할·양도로 계정 구조 변동 |
| K-IFRS 주요 개정 | IFRS 16(리스), IFRS 17(보험) 등 대폭 개정 |

---

## 사용법

### property 접근 (자동 적용)

property로 접근하면 Bridge Matching이 자동 적용된 결과를 받는다.

```python
from dartlab import Company

c = Company("005930")

# property — Bridge Matching 적용된 DataFrame
c.BS   # 재무상태표
c.IS   # 손익계산서
```

### fsSummary() — Bridge Matching 상세 확인

Bridge Matching 상세 결과를 확인하려면 `fsSummary()`를 직접 호출한다.

```python
result = c.fsSummary()

# 전체 통계
print(f"분석 연도: {result.nYears}년")
print(f"전체 매칭률: {result.allRate:.1%}")
print(f"구간 수: {result.nSegments}")
print(f"변경점 수: {result.nBreakpoints}")
```

### 구간별 정보

```python
for seg in result.segments:
    print(f"  {seg.startYear}~{seg.endYear}: {seg.nYears}년, 매칭률 {seg.rate:.1%}")
```

### 개별 브릿지 결과

```python
for pair in result.pairResults:
    print(f"  {pair.prevYear} → {pair.curYear}: {pair.matched}/{pair.total} ({pair.rate:.1%})")
```

### 변경점 확인

```python
for bp in result.breakpoints:
    print(f"  변경점: {bp.prevYear} → {bp.curYear} (매칭률 {bp.rate:.1%})")
    # 변경된 계정 확인
    for cur, prev in bp.pairs.items():
        if cur != prev:
            print(f"    {prev} → {cur}")
```

---

## 분기별 분석

연간뿐 아니라 분기/반기 데이터에도 적용된다. 분기 데이터는 누적값에서 개별 분기를 역산한다.

```python
result = c.fsSummary(period="q")  # 분기별
result = c.fsSummary(period="h")  # 반기별
```

분기별 분석에서는 Bridge Matching 대신 직접 매칭을 사용한다 (동일 연도 내 계정명이 동일하므로).

---

## 핵심 계정

시계열 연속성을 우선 보장하는 계정들이다.

| 계정 | 재무제표 | 의미 |
|------|---------|------|
| 매출액 | IS | 수익 규모 |
| 영업이익 | IS | 본업 수익성 |
| 당기순이익 | IS | 최종 수익 |
| 자산총계 | BS | 기업 규모 |
| 부채총계 | BS | 차입 규모 |
| 자본총계 | BS | 순자산 |

---

## 핵심 상수

| 상수 | 값 | 설명 |
|------|-----|------|
| `BREAKPOINT_THRESHOLD` | 0.85 | 변경점 판단 임계값 |
| `EXACT_MATCH_TOLERANCE` | 0.5 | 정확 매칭 허용 오차 |
| `RESTATEMENT_NAME_SIMILARITY` | 0.8 | 재작성 매칭 명칭 유사도 |
| `RESTATEMENT_AMOUNT_TOLERANCE` | 0.05 | 재작성 매칭 금액 오차 (5%) |
| `NAME_CHANGE_SIMILARITY` | 0.6 | 명칭 변경 매칭 유사도 |
| `NAME_CHANGE_AMOUNT_TOLERANCE` | 0.05 | 명칭 변경 매칭 금액 오차 (5%) |

---

## 결과 객체

### AnalysisResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `allRate` | `float` | 전체 매칭률 |
| `nBreakpoints` | `int` | 변경점 수 |
| `nSegments` | `int` | 연속 구간 수 |
| `segments` | `list[Segment]` | 구간 목록 |
| `breakpoints` | `list[BridgeResult]` | 변경점 목록 |
| `pairResults` | `list[BridgeResult]` | 연도별 매칭 결과 |
| `BS` | `pl.DataFrame` | 재무상태표 |
| `IS` | `pl.DataFrame` | 손익계산서 |
| `FS` | `pl.DataFrame` | 통합 시계열 |

### BridgeResult

| 속성 | 타입 | 설명 |
|------|------|------|
| `curYear` | `str` | 당기 |
| `prevYear` | `str` | 전기 |
| `rate` | `float` | 매칭률 |
| `matched` | `int` | 매칭된 계정 수 |
| `total` | `int` | 전체 계정 수 |
| `pairs` | `dict[str, str]` | 매칭 쌍 |

### Segment

| 속성 | 타입 | 설명 |
|------|------|------|
| `startYear` | `str` | 시작 연도 |
| `endYear` | `str` | 종료 연도 |
| `nYears` | `int` | 연도 수 |
| `rate` | `float` | 구간 평균 매칭률 |

> 상세한 API 정보는 [finance.summary](../api/finance-summary)를 참고한다.
