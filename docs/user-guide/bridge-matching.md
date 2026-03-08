---
title: Bridge Matching
---

# Bridge Matching

## 문제

DART 공시의 요약재무정보는 매년 계정명이 미세하게 바뀐다.

- K-IFRS 개정으로 계정명 변경 ("매출액" → "수익(매출액)")
- 회사의 자체적인 표기 변경 ("당기순이익" → "당기순이익(손실)")
- 연결/별도 전환 시 계정 구조 변동

단순 계정명 매칭으로는 시계열이 끊긴다. Bridge Matching은 금액과 명칭 유사도를 조합해서 같은 계정을 자동으로 추적한다.

## 4단계 매칭

```
2022                    2023                    2024
매출액 ──────────────── 매출액 ──────────────── 수익(매출액)
영업이익 ────────────── 영업이익 ────────────── 영업이익
당기순이익 ──────────── 당기순이익 ──────────── 당기순이익(손실)
```

1. **정확 매칭**: 금액이 동일한 계정을 연결 (허용 오차 0.5 이내)
2. **재작성 매칭**: 금액 오차 5% 이내 + 명칭 유사도 80% 이상
3. **명칭 변경 매칭**: 금액 오차 5% 이내 + 명칭 유사도 60% 이상
4. **특수 항목 매칭**: 주당이익(EPS) 등 소수점 단위 항목

## 변경점 탐지

매칭률이 85% 이하로 떨어지면 전환점(breakpoint)으로 판정하고 구간을 분리한다. 기업 합병, 연결/별도 전환, 대규모 구조 변경이 일어난 시점을 자동으로 찾아낸다.

## 사용법

property로 접근하면 Bridge Matching이 자동 적용된 결과를 받는다.

```python
from dartlab import Company

c = Company("005930")

# property — Bridge Matching 적용된 DataFrame
c.BS   # 재무상태표
c.IS   # 손익계산서
```

Bridge Matching 상세 결과를 확인하려면 `fsSummary()`를 직접 호출한다.

```python
result = c.fsSummary()

# 전체 통계
print(f"분석 연도: {result.nYears}년")
print(f"전체 매칭률: {result.allRate:.1%}")
print(f"구간 수: {result.nSegments}")
print(f"변경점 수: {result.nBreakpoints}")

# 구간별 정보
for seg in result.segments:
    print(f"  {seg.startYear}~{seg.endYear}: {seg.nYears}년, 매칭률 {seg.rate:.1%}")

# 개별 브릿지 결과
for pair in result.pairResults:
    print(f"  {pair.prevYear} → {pair.curYear}: {pair.matched}/{pair.total} ({pair.rate:.1%})")

# 변경점
for bp in result.breakpoints:
    print(f"  변경점: {bp.prevYear} → {bp.curYear} (매칭률 {bp.rate:.1%})")
```

## 분기별 분석

연간뿐 아니라 분기/반기 데이터에도 적용된다. 분기 데이터는 누적값에서 개별 분기를 역산한다.

```python
result = c.fsSummary(period="q")  # 분기별
result = c.fsSummary(period="h")  # 반기별
```

분기별 분석에서는 Bridge Matching 대신 직접 매칭을 사용한다 (동일 연도 내 계정명이 동일하므로).

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

## 핵심 상수

| 상수 | 값 | 설명 |
|------|-----|------|
| `BREAKPOINT_THRESHOLD` | 0.85 | 변경점 판단 임계값 |
| `EXACT_MATCH_TOLERANCE` | 0.5 | 정확 매칭 허용 오차 |
| `RESTATEMENT_NAME_SIMILARITY` | 0.8 | 재작성 매칭 명칭 유사도 |
| `RESTATEMENT_AMOUNT_TOLERANCE` | 0.05 | 재작성 매칭 금액 오차 |
| `NAME_CHANGE_SIMILARITY` | 0.6 | 명칭 변경 매칭 유사도 |
| `NAME_CHANGE_AMOUNT_TOLERANCE` | 0.05 | 명칭 변경 매칭 금액 오차 |
