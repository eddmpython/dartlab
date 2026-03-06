# dartlab API 스팩

## 공통 규칙

- 모든 pipeline 함수는 `stockCode: str` (6자리 종목코드)를 첫 번째 인자로 받는다
- 내부에서 `core.loadData(stockCode)` → DataFrame 로딩
- 반환 타입은 각 모듈의 Result dataclass 또는 None (데이터 부족 시)
- 모든 Result는 `corpName`, `nYears`, `period` 필드를 공통으로 가진다

## finance.summary

```python
from dartlab.finance.summary import analyze

result = analyze("005930")
result = analyze("005930", ifrsOnly=True, period="y")
```

### analyze(stockCode, ifrsOnly=True, period="y") -> AnalysisResult | None

요약재무정보 시계열 추출 + 브릿지 매칭 + 전환점 탐지.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| ifrsOnly | bool | True | K-IFRS 이후(2011~)만 분석 |
| period | str | "y" | "y" (연간) \| "q" (분기) \| "h" (반기) |

### AnalysisResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 기간 수 |
| period | str | "y" \| "q" \| "h" |
| allRate | float \| None | 전체 매칭률 |
| contRate | float \| None | 연속 구간 매칭률 |
| segments | list[Segment] | 구간 목록 |
| breakpoints | list[BridgeResult] | 전환점 목록 |
| FS | DataFrame \| None | 전체 재무제표 |
| BS | DataFrame \| None | 재무상태표 |
| IS | DataFrame \| None | 손익계산서 |

## finance.statements

```python
from dartlab.finance.statements import statements

result = statements("005930")
result = statements("005930", ifrsOnly=True, period="y")
```

### statements(stockCode, ifrsOnly=True, period="y") -> StatementsResult | None

연결재무제표에서 BS, IS, CF 시계열 DataFrame 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| ifrsOnly | bool | True | K-IFRS 이후(2011~)만 |
| period | str | "y" | "y" \| "q" \| "h" |

### StatementsResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 기간 수 |
| period | str | "y" \| "q" \| "h" |
| BS | DataFrame \| None | 재무상태표 |
| IS | DataFrame \| None | 손익계산서 |
| CF | DataFrame \| None | 현금흐름표 |

## finance.segment

```python
from dartlab.finance.segment import segments

result = segments("005930")
result = segments("005930", period="y")
```

### segments(stockCode, period="y") -> SegmentsResult | None

연결재무제표 주석에서 부문별 보고 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| period | str | "y" | "y" \| "q" \| "h" |

### SegmentsResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| period | str | "y" \| "q" \| "h" |
| tables | dict[str, list[SegmentTable]] | {year: [tables]} |
| revenue | DataFrame \| None | 부문별 매출 시계열 |

## finance.affiliate

```python
from dartlab.finance.affiliate import affiliates

result = affiliates("005930")
result = affiliates("005930", period="y")
```

### affiliates(stockCode, period="y") -> AffiliatesResult | None

연결재무제표 주석에서 관계기업/공동기업 투자 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| period | str | "y" | "y" \| "q" \| "h" |

### AffiliatesResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| period | str | "y" \| "q" \| "h" |
| profiles | dict[str, list[AffiliateProfile]] | {year: [profiles]} |
| movements | dict[str, list[AffiliateMovement]] | {year: [movements]} |
| movementDf | DataFrame \| None | 기업별 변동 시계열 |
