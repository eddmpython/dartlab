# dartlab API 스펙

## 개요

DART 공시 요약재무제표에서 숫자 브릿지 매칭으로 계정명을 연도간 매핑하여 재무제표 시계열을 생성한다.

## 함수

### fsSummary

```python
dartlab.fsSummary(
    source: str | Path | pl.DataFrame,
    ifrsOnly: bool = True,
) -> AnalysisResult | None
```

단일 기업의 DART 공시 데이터를 분석하여 연도별 재무제표 매칭 결과를 반환한다.

**파라미터:**
- `source`: parquet 파일 경로 또는 polars DataFrame
- `ifrsOnly`: True면 K-IFRS 이후(2011~)만 분석 (기본값: True)

**반환값:**
- `AnalysisResult`: 분석 결과. 데이터 부족(2년 미만) 시 `None`

**사용 예제:**
```python
import dartlab

result = dartlab.fsSummary("data/docsData/005930.parquet")
print(f"{result.corpName}: {result.nYears}년, 매칭률 {result.allRate:.1%}")
print(f"구간 수: {result.nSegments}, 전환점: {result.nBreakpoints}")

for seg in result.segments:
    print(f"  {seg.startYear}~{seg.endYear}: {seg.rate:.1%}")
```

---

### loadYearData

```python
dartlab.loadYearData(
    df: pl.DataFrame,
) -> dict[str, YearAccounts]
```

parquet DataFrame에서 연도별 계정 데이터를 추출한다.

**파라미터:**
- `df`: DART 공시 데이터 polars DataFrame

**반환값:**
- `dict[str, YearAccounts]`: 연도를 키로 하는 계정 데이터 딕셔너리

**사용 예제:**
```python
import polars as pl
import dartlab

df = pl.read_parquet("data/docsData/005930.parquet")
yearData = dartlab.loadYearData(df)

for year, ya in sorted(yearData.items(), reverse=True):
    print(f"{year}: {len(ya.accounts)}개 계정")
    for name, amounts in list(ya.accounts.items())[:3]:
        print(f"  {name}: {amounts}")
```

## 타입

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    corpName: str | None
    nYears: int
    nPairs: int
    nBreakpoints: int
    nSegments: int
    allRate: float | None
    allMatched: int
    allTotal: int
    contRate: float | None
    contMatched: int
    contTotal: int
    segments: list[Segment]
    breakpoints: list[BridgeResult]
    pairResults: list[BridgeResult]
    yearAccounts: dict[str, YearAccounts]
```

| 필드 | 설명 |
|------|------|
| corpName | 기업명 (DataFrame의 corp_name 컬럼) |
| nYears | 분석 대상 연도 수 |
| nPairs | 연도 쌍 수 (nYears - 1) |
| nBreakpoints | 전환점 수 |
| nSegments | 연속 구간 수 |
| allRate | 전체 매칭률 |
| allMatched / allTotal | 전체 매칭/전체 대상 수 |
| contRate | 연속 연도(gap=1) 매칭률 |
| contMatched / contTotal | 연속 연도 매칭/대상 수 |
| segments | 구간별 통계 |
| breakpoints | 전환점 목록 |
| pairResults | 연도 쌍별 매칭 결과 |
| yearAccounts | 연도별 추출된 계정 데이터 |

### Segment

```python
@dataclass
class Segment:
    startYear: str
    endYear: str
    nYears: int
    matched: int
    total: int
    rate: float | None
```

### BridgeResult

```python
@dataclass
class BridgeResult:
    curYear: str
    prevYear: str
    rate: float
    matched: int
    total: int
    yearGap: int
    pairs: dict[str, str]
```

| 필드 | 설명 |
|------|------|
| pairs | {당해년도 계정명: 전년도 계정명} 매핑 |
| yearGap | 연도 간격 (보통 1, 갭 있으면 2+) |

### YearAccounts

```python
@dataclass
class YearAccounts:
    year: str
    accounts: dict[str, list[float | None]]
    order: list[str]
```

| 필드 | 설명 |
|------|------|
| accounts | {계정명: [당기, 전기, 전전기, ...]} |
| order | 계정 순서 (테이블 등장 순) |

## 상수

| 상수 | 값 | 설명 |
|------|-----|------|
| BREAKPOINT_THRESHOLD | 0.85 | 전환점 판정 임계값 |
| CORE_ACCOUNTS | 10개 계정 | 핵심 계정 목록 |

## 매칭 알고리즘 (4단계)

1. **정확 매칭**: N년 전기 금액 == N-1년 당기 금액 (차이 < 0.5)
2. **재작성 보정**: 이름 유사도 0.8+ 금액 차이 5% 이내
3. **명칭변경 보정**: 이름 유사도 0.6+ 금액 차이 5% 이내
4. **특수항목**: EPS, 회사수 등 이름 강제 매칭

## 입력 데이터 요구사항

polars DataFrame 또는 parquet 파일. 필수 컬럼:

| 컬럼 | 타입 | 설명 |
|------|------|------|
| year | str | 사업연도 |
| report_type | str | 보고서 유형 ("사업보고서" 포함) |
| rcept_date | str | 접수일 |
| section_title | str | 섹션 제목 |
| section_content | str | 섹션 내용 (마크다운) |

선택 컬럼:
| 컬럼 | 타입 | 설명 |
|------|------|------|
| corp_name | str | 기업명 (AnalysisResult.corpName에 사용) |
