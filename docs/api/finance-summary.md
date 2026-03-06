# Finance Summary API

## `analyze(path)`

DART 공시 Parquet 파일에서 요약재무정보를 시계열로 추출한다.

### 파라미터

| 이름 | 타입 | 설명 |
|------|------|------|
| `path` | `str \| Path` | Parquet 파일 경로 |

### 반환

`AnalysisResult` 객체

### 사용 예제

```python
from dartlab.finance.summary import analyze

result = analyze("data/docsData/005930.parquet")
print(result.dataframe)
```

---

## `AnalysisResult`

분석 결과를 담는 데이터 클래스.

### 속성

| 이름 | 타입 | 설명 |
|------|------|------|
| `dataframe` | `polars.DataFrame` | 계정명 × 연도 시계열 |
| `years` | `list[YearAccounts]` | 연도별 계정 데이터 |
| `bridges` | `list[BridgeResult]` | 연도 간 브릿지 매칭 결과 |

---

## `YearAccounts`

개별 연도의 계정 데이터.

### 속성

| 이름 | 타입 | 설명 |
|------|------|------|
| `period` | `str` | 사업연도 (예: "2023") |
| `accounts` | `dict[str, int]` | 계정명 → 금액 |

---

## `BridgeResult`

연도 간 계정 매칭 결과.

### 속성

| 이름 | 타입 | 설명 |
|------|------|------|
| `fromPeriod` | `str` | 시작 연도 |
| `toPeriod` | `str` | 종료 연도 |
| `matchCount` | `int` | 매칭된 계정 수 |

---

## 상수

### `CORE_ACCOUNTS`

핵심 계정 목록. 시계열 연속성을 우선 보장하는 계정들.

### `BREAKPOINT_THRESHOLD`

변경점 판단 임계값. 매칭률이 이 값 아래로 떨어지면 breakpoint로 판단.
