# EDGAR 모듈 통합 기획서

## 1. 개요

### 목적
- DART 시스템과 동일한 아키텍처로 SEC EDGAR 데이터 처리
- 기존 연구 자산(investwings/edgarData) 활용 및 발전
- 한국(DART) + 미국(EDGAR) 재무데이터 통합 분석 기반 구축

### 현재 상태

| 항목 | DART (eddmpython) | EDGAR (investwings) |
|------|-------------------|---------------------|
| 상태 | Production Ready | Research Phase |
| 버전 | v7 (standardMapping) | V22 Hybrid Ensemble |
| 매핑 커버리지 | 95%+ (learnedSynonyms) | 85-95% |
| 저장소 | core/dart/ | 별도 프로젝트 |

---

## 2. 아키텍처 비교

### 2.1 수집 계층 (getData)

```
DART (v2)                          EDGAR (V3)
─────────────────────────────────────────────────────────
DartBase.py                        edgarBulk.py
├─ CorpCollector (회사별)          ├─ Bulk Download (전체)
├─ ApiCollector (API별)            ├─ Dataset Download (분기별)
└─ Rate Limiter (10 req/sec)       └─ CIK-based Storage

수집 방식:
- DART: API 호출 → 회사별 parquet
- EDGAR: Bulk ZIP → 전체 parquet + Dataset TSV → 분기별 parquet
```

**차이점 및 통합 방안:**
- DART는 실시간 API 중심, EDGAR는 배치 다운로드 중심
- 통합: `EdgarCollector` 기반 클래스 + `BulkDownloader`, `DatasetDownloader` 구현

### 2.2 매핑 계층 (Account Mapping)

```
DART                               EDGAR
─────────────────────────────────────────────────────────
standardAccounts.json (13,227)     accountMapping.parquet
├─ code, korName, snakeId          ├─ tag, standardAccount
├─ level, industry                 ├─ displayAccount, korean
└─ statementKind                   └─ level, line, parent

learnedSynonyms.json (3,400+)      customTags/*.py
└─ stdAccountNm → snakeId          └─ company-specific overrides

sortOrder.json                     PRE Dataset (inpth)
└─ BS/IS/CF 순서 정의              └─ hierarchy reconstruction
```

**핵심 차이:**
- DART: 표준계정코드 기반 + 동의어 학습
- EDGAR: XBRL 태그 기반 + Hybrid Ensemble 매칭

**통합 방안:**
```
새로운 통합 매핑 시스템:
├─ standardAccounts.json (EDGAR용)
│   ├─ code: XBRL Tag 또는 표준코드
│   ├─ korName: 한글명
│   ├─ engName: 영문명
│   ├─ snakeId: 표준식별자
│   └─ statementKind: BS/IS/CF
│
├─ learnedSynonyms.json
│   └─ plabel/tag → snakeId 매핑
│
└─ sortOrder.json
    └─ 재무제표 순서 정의
```

### 2.3 검색 계층 (searchDart → searchEdgar)

```
DART (DartSearch)                  EDGAR (edgarBulk.getFacts)
─────────────────────────────────────────────────────────
dart.finance.getTimeseries()       getFactsTimeSeries(ticker)
dart.finance.byAccount()           (미구현)
dart.finance.ranking()             (미구현)
dart.finance.growth()              (미구현)
dart.finance.search()              (미구현)
```

**통합 목표:**
```python
# 목표 API
edgar = EdgarSearch()
edgar.finance.getTimeseries("AAPL")
edgar.finance.byAccount("total_assets")
edgar.finance.ranking(account="revenue", year=2024)
edgar.finance.growth("AAPL", years=5)
```

---

## 3. 마이그레이션 계획

### Phase 1: 기반 구조 (2주)

```
core/edgar/
├─ __init__.py                    # Lazy imports
├─ config.py                      # 설정, 컬럼 매핑
│
├─ getEdgar/
│   ├─ v1/
│   │   ├─ EdgarBase.py          # 기본 수집기 클래스
│   │   ├─ EdgarFinance.py       # 재무데이터 수집
│   │   ├─ bulkDownloader.py     # Bulk ZIP 다운로드
│   │   ├─ datasetDownloader.py  # Dataset 다운로드
│   │   ├─ ticker.py             # Ticker/CIK 매핑
│   │   └─ config.py             # API 엔드포인트
│   └─ __init__.py
│
└─ searchEdgar/
    ├─ __init__.py               # EdgarSearch facade
    └─ finance/
        ├─ __init__.py
        ├─ standardAccounts.json  # EDGAR 표준계정
        ├─ learnedSynonyms.json   # 학습된 동의어
        ├─ sortOrder.json         # 재무제표 순서
        └─ v1/
            └─ search.py          # 기본 검색
```

### Phase 2: 수집 모듈 (2주)

**이관 대상 (investwings → eddmpython):**

| 원본 파일 | 대상 파일 | 비고 |
|-----------|-----------|------|
| edgarBulk.py | getEdgar/v1/EdgarFinance.py | 핵심 로직 |
| bulksData.py | getEdgar/v1/bulkDownloader.py | Bulk 다운로드 |
| datasetsData.py | getEdgar/v1/datasetDownloader.py | Dataset 다운로드 |
| tickersData.py | getEdgar/v1/ticker.py | Ticker 관리 |
| edgarApiConfig.py | getEdgar/v1/config.py | API 설정 |

**개선 사항:**
- Rate Limiter 추가 (SEC 10 req/sec 제한)
- Progress Callback 지원
- 에러 핸들링 표준화

### Phase 3: 매핑 시스템 (3주)

**3.1 표준계정 정의**

```json
// searchEdgar/finance/standardAccounts.json
{
  "_metadata": {
    "source": "SEC XBRL US-GAAP Taxonomy + Custom Research",
    "totalAccounts": 500,
    "statementMapping": {
      "BS": "Balance Sheet",
      "IS": "Income Statement",
      "CF": "Cash Flow Statement",
      "OTH": "Other"
    }
  },
  "accounts": [
    {
      "code": "Assets",
      "korName": "자산총계",
      "engName": "Total Assets",
      "snakeId": "total_assets",
      "level": 1,
      "statementKind": "BS",
      "commonTags": ["Assets", "TotalAssets", "AssetsTotal"]
    },
    {
      "code": "Revenue",
      "korName": "매출액",
      "engName": "Revenue",
      "snakeId": "revenue",
      "level": 1,
      "statementKind": "IS",
      "commonTags": ["Revenue", "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"]
    }
  ]
}
```

**3.2 동의어 학습 시스템**

```python
# searchEdgar/finance/v1/synonymLearner.py
class SynonymLearner:
    def analyzeCompany(self, ticker: str) -> dict:
        """회사별 미매핑 태그 분석"""

    def generateSuggestions(self, tag: str, plabel: str) -> list:
        """매핑 후보 제안"""

    def saveSynonyms(self):
        """학습 결과 저장"""
```

**3.3 Hybrid Ensemble 통합**

```python
# searchEdgar/finance/v1/standardMapping.py
class StandardMapper:
    def __init__(self):
        self.standardAccounts = self._loadStandardAccounts()
        self.learnedSynonyms = self._loadLearnedSynonyms()

    def map(self, tag: str, plabel: str, stmt: str) -> MappingResult:
        """
        매핑 우선순위:
        1. 표준계정 직접 매칭 (commonTags)
        2. 학습된 동의어 매칭
        3. Hybrid Ensemble (Token + Fuzzy + Keyword)
        4. 미매핑 (None)
        """
```

### Phase 4: 검색 API (2주)

```python
# searchEdgar/finance/v1/search.py
class FinanceSearch:
    def getTimeseries(
        self,
        ticker: str,
        statements: list = ["BS", "IS", "CF"],
        periods: int = 20
    ) -> pl.DataFrame:
        """시계열 재무데이터 조회"""

    def byAccount(
        self,
        snakeId: str,
        tickers: list = None,
        year: int = None
    ) -> pl.DataFrame:
        """특정 계정 크로스 비교"""

    def ranking(
        self,
        snakeId: str,
        year: int,
        ascending: bool = False,
        limit: int = 100
    ) -> pl.DataFrame:
        """계정별 랭킹"""

    def growth(
        self,
        ticker: str,
        snakeId: str,
        years: int = 5
    ) -> pl.DataFrame:
        """성장률 분석"""
```

---

## 4. 데이터 저장 구조

```
data/edgarData/
├─ finance/
│   └─ {cik}.parquet             # 회사별 원시 데이터
├─ datasets/
│   ├─ sub/
│   │   └─ {quarter}.parquet     # 제출 메타데이터
│   ├─ pre/
│   │   └─ {quarter}.parquet     # 표시 계층
│   ├─ tag/
│   │   └─ {quarter}.parquet     # 태그 정의
│   └─ num/
│       └─ {quarter}.parquet     # 수치 데이터
├─ tickers/
│   └─ companyTickers.parquet    # Ticker-CIK 매핑
└─ cache/
    ├─ prepared.parquet          # 정규화된 캐시
    └─ standardized.parquet      # 표준화된 캐시
```

---

## 5. 주요 고려사항

### 5.1 DART vs EDGAR 차이점

| 항목 | DART | EDGAR |
|------|------|-------|
| 식별자 | stockCode (6자리) | CIK (10자리) |
| 회계기준 | K-IFRS | US-GAAP / IFRS |
| 기간 표기 | bsns_year + reprt_code | fy + fp |
| 계정 체계 | 표준계정코드 (13,227) | XBRL Taxonomy (수만개) |
| 계층 구조 | 명시적 (level) | PRE inpth로 재구성 |
| API 제한 | 10 req/sec | 10 req/sec |

### 5.2 통합 인터페이스

```python
# 목표: 통합 사용 예시
from core.dart import DartSearch
from core.edgar import EdgarSearch

dart = DartSearch()
edgar = EdgarSearch()

# 동일한 API 패턴
samsung = dart.finance.getTimeseries("005930")
apple = edgar.finance.getTimeseries("AAPL")

# 크로스 비교 가능
# (표준화된 snakeId 사용)
```

### 5.3 기술 스택

- **DataFrame**: Polars (성능)
- **저장**: Parquet (압축 + 스키마)
- **캐시**: JSON + Parquet 하이브리드
- **API**: SEC EDGAR REST API
- **동시성**: asyncio + aiohttp (선택적)

---

## 6. 실행 계획

### 6.1 우선순위

```
[P0] 필수 - Phase 1, 2
├─ 기반 구조 생성
├─ 수집 모듈 이관
└─ 기본 데이터 파이프라인

[P1] 중요 - Phase 3
├─ 표준계정 정의
├─ 동의어 학습 시스템
└─ Hybrid Ensemble 매핑

[P2] 확장 - Phase 4
├─ 검색 API
├─ UI 통합
└─ 크로스 분석 기능
```

### 6.2 이관 대상 파일 목록

```
investwings/getData/edgarData/ → eddmpython/core/edgar/

1. func/edgarBulk.py
2. func/bulksData.py
3. func/datasetsData.py
4. func/edgarCall.py
5. func/tickersData.py
6. edgarApiConfig.py
7. func/mapping/createTagMapping.py
8. func/mapping/accountMapping.parquet
9. func/mapping/customTags/

참고 문서:
- func/계정계층시스템테스트/Edgar_XBRL_Standardization_Research_Report.md
- func/계정계층시스템테스트/PRD.md
```

---

## 7. 예상 결과물

### 7.1 디렉토리 구조 (최종)

```
core/edgar/
├─ __init__.py
├─ config.py
│
├─ getEdgar/
│   ├─ __init__.py
│   └─ v1/
│       ├─ Edgar.py              # 통합 인터페이스
│       ├─ EdgarBase.py          # 기본 클래스
│       ├─ EdgarFinance.py       # 재무 수집
│       ├─ bulkDownloader.py     # Bulk 다운로드
│       ├─ datasetDownloader.py  # Dataset 다운로드
│       ├─ ticker.py             # Ticker 관리
│       ├─ config.py             # API 설정
│       └─ utils.py              # 유틸리티
│
└─ searchEdgar/
    ├─ __init__.py               # EdgarSearch facade
    ├─ finance/
    │   ├─ __init__.py
    │   ├─ standardAccounts.json
    │   ├─ learnedSynonyms.json
    │   ├─ sortOrder.json
    │   ├─ _dataLoader.py
    │   └─ v1/
    │       ├─ search.py
    │       ├─ standardMapping.py
    │       ├─ synonymLearner.py
    │       └─ hierarchy.py
    └─ docs/                      # SEC Filing 문서 검색 (향후)
```

### 7.2 기대 효과

1. **코드 재사용**: DART 아키텍처 패턴 활용
2. **일관성**: 동일한 API 인터페이스
3. **확장성**: 다른 국가 데이터 추가 용이
4. **분석**: 한미 기업 비교 분석 가능

---

## 8. 구현 완료 현황 (2026-01-22)

### ✅ Phase 1-4 완료

**구현된 디렉토리 구조:**
```
core/edgar/
├─ __init__.py                    # EdgarSearch lazy import
├─ config.py                      # SEC API 설정, 컬럼 매핑
├─ PLANNING.md                    # 기획서 (본 문서)
│
├─ getEdgar/                      # 데이터 수집 모듈
│   ├─ __init__.py
│   └─ v1/
│       ├─ __init__.py
│       ├─ ticker.py              # TickerManager (Ticker/CIK 매핑)
│       ├─ bulkDownloader.py      # BulkDownloader (companyfacts.zip)
│       ├─ datasetDownloader.py   # DatasetDownloader (분기별 SUB/PRE/TAG/NUM)
│       └─ edgarFinance.py        # EdgarFinance (통합 수집 인터페이스)
│
└─ searchEdgar/                   # 데이터 검색 모듈
    ├─ __init__.py                # EdgarSearch facade
    └─ finance/
        ├─ __init__.py
        ├─ standardAccounts.json  # US-GAAP 기반 표준계정 (75개)
        ├─ learnedSynonyms.json   # 학습된 동의어 (초기)
        ├─ sortOrder.json         # BS/IS/CF 계정 순서
        └─ v1/
            ├─ __init__.py
            ├─ search.py          # FinanceSearch (시계열, byAccount 등)
            ├─ standardMapping.py # StandardMapper (태그→표준계정)
            └─ synonymLearner.py  # SynonymLearner (동의어 학습)
```

### 표준계정 설계 (standardAccounts.json)

**직접 설계한 US-GAAP 표준계정:**
- BS (Balance Sheet): 35개 계정
- IS (Income Statement): 20개 계정
- CF (Cash Flow): 20개 계정
- 총 75개 핵심 계정 + commonTags 매핑

**구조:**
```json
{
  "code": "BS001",
  "stmt": "BS",
  "snakeId": "total_assets",
  "korName": "자산총계",
  "engName": "Total Assets",
  "level": 1,
  "line": 100,
  "parent": null,
  "commonTags": ["Assets"]
}
```

### 매핑 시스템 (StandardMapper)

**매핑 우선순위:**
1. `mapByTag`: commonTags 직접 매칭 (confidence: 1.0)
2. `mapByPlabel`: 학습된 plabel 매칭 (confidence: 0.85)
3. `mapByFuzzy`: Token + Fuzzy 매칭 (confidence: 0.65+)
4. 미매핑: source="unmapped" (confidence: 0.0)

### 동의어 학습 시스템 (SynonymLearner)

**기능:**
- `analyzeUnmapped()`: 미매핑 태그 분석
- `suggestMapping()`: 매핑 후보 제안 (Fuzzy 기반)
- `learnFromAnalysis()`: 자동 학습 (minConfidence 이상)
- `addTagMapping()` / `addPlabelMapping()`: 수동 추가

### 사용 예시

```python
from core.edgar import EdgarSearch

edgar = EdgarSearch()

# 시계열 재무데이터
timeseries = edgar.finance.getTimeseries("AAPL")

# 특정 계정 크로스 비교
assets = edgar.finance.byAccount("total_assets", tickers=["AAPL", "MSFT"])

# 미매핑 분석
unmapped = edgar.finance.getUnmappedTimeseries("AAPL")
```

### 다음 단계

1. **데이터 수집**: `BulkDownloader.download()` 실행하여 벌크 데이터 확보
2. **동의어 학습**: 주요 기업 분석 후 `learnedSynonyms.json` 확장
3. **UI 통합**: dartWings처럼 edgarWings 페이지 구현
4. **크로스 분석**: DART + EDGAR 통합 비교 기능

---

## 9. 결론

### 상태: ✅ 기본 구현 완료

**완료 항목:**
1. 기반 구조 (config, __init__)
2. 수집 모듈 (ticker, bulkDownloader, datasetDownloader, edgarFinance)
3. 표준계정 설계 (75개 US-GAAP 계정)
4. 매핑 시스템 (StandardMapper)
5. 동의어 학습 (SynonymLearner)
6. 검색 API (FinanceSearch)

**다음 우선순위:**
1. 벌크 데이터 다운로드 테스트
2. 실제 데이터로 매핑 커버리지 측정
3. 미매핑 태그 학습으로 커버리지 향상
