# 빠른 시작

## 요약 재무정보 시계열 추출

DartLab의 핵심 기능은 DART 공시에서 요약재무정보를 시계열로 추출하는 것이다.

### 기본 사용법

```python
from dartlab.finance.summary import analyze

result = analyze("data/docsData/005930.parquet")
```

### 결과 탐색

```python
# 전체 시계열 — Polars DataFrame
print(result.dataframe)
# shape: (N, M) — 행은 계정명, 열은 연도
```

### 개별 연도 접근

```python
for year in result.years:
    print(f"{year.period}: {len(year.accounts)}개 계정")
```

### 브릿지 매칭

연도 간 계정명이 변경되더라도 Bridge Matching으로 자동 연결한다.

```python
for bridge in result.bridges:
    print(f"{bridge.fromPeriod} → {bridge.toPeriod}: {bridge.matchCount}개 매칭")
```

## 다음 단계

- [API 레퍼런스](../api/finance-summary.md) — 전체 API 문서
- [사용 가이드](../user-guide/bridge-matching.md) — Bridge Matching 상세 설명
