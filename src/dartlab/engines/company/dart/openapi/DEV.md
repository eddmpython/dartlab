# DART OpenAPI 직접 클라이언트

opendartreader 대체. 극강 편의성 설계.

## 사용법

```python
from dartlab import OpenDart

d = OpenDart()                           # canonical 이름
d = OpenDart("your_key")                 # 단일 키
d = OpenDart(["key1", "key2", "key3"])   # 멀티 키 로테이션

# 호환 alias
from dartlab import Dart

# 공시 검색 — 날짜 유연 ("2024", "2024-01", "2024-1-5", "20240105", datetime)
d.filings("삼성전자")                    # 최근 1년 자동
d.filings("005930", "2024")              # 2024년 전체
d.filings("삼성전자", "2024-01", "2024-06")
d.filings(start="2024-03-14")            # 전체 시장 특정일
d.filings("삼성전자", type="A")          # 정기공시만

# 기업 정보
d.company("삼성전자")                    # 기업개황 dict
d.search("카카오", listed=True)          # 상장사 검색

# 사업보고서 28개 API
d.report("삼성전자", "배당", 2023)
d.report("005930", "직원", 2023, "Q2")

# 재무제표
d.finstate("삼성전자", 2023)             # 주요 계정
d.finstate("삼성전자", 2023, full=True)  # 전체 계정

# 지분공시
d.majorShareholders("삼성전자")
d.executiveShares("삼성전자")

# corp_code
d.corpCode("삼성전자")       # "00126380"
d.corpCodes()                # 전체 11만+ DataFrame
```

## 구조

```
openapi/
├── __init__.py      # OpenDart / Dart export
├── dart.py          # Dart facade (사용자 진입점)
├── client.py        # DartClient (멀티 키, rate limit, 자동 재시도)
├── corpCode.py      # corp_code 관리 (캐시 ~/.dartlab/corpCode.parquet)
├── collector.py     # 공시문서 수집기 (eddmpython DartDocs.py 포팅)
├── disclosure.py    # 공시검색, 기업개황 (내부)
├── saver.py         # CSV/Excel 저장 (한글 컬럼)
├── dateUtil.py      # 유연한 날짜 파싱
└── DEV.md
```

## 공시문서 수집기 (collector.py)

eddmpython의 `DartDocs.py` 수집 로직을 dartlab으로 완전 포팅. 프록시 없이 requests 기반 동기 크롤링.

### 수집 파이프라인

```
Phase 1: 공시 목록 조회 (listFilings → 정기공시 필터)
    ↓ 기존 수집분 제외 (rcept_no 중복 검사)
Phase 2: 목차 수집 (DART 공시 메인 → 하위 섹션 URL 파싱)
    ↓ _MULTI_PAGE_RE / _SINGLE_PAGE_RE 정규식
Phase 3: HTML 수집 → 텍스트 변환 (_htmlToText)
    ↓ 테이블은 마크다운으로 보존
Phase 4: parquet 저장 (원자적 교체 — .tmp → rename)
```

### 사용법

```python
from dartlab.engines.company.dart.openapi.collector import DocsCollector

collector = DocsCollector("005930")
collector.collect(quarters=8)  # 최근 8분기

# 여러 종목 순차
from dartlab.engines.company.dart.openapi.collector import collectMultiple
collectMultiple(["005930", "000660"], quarters=8)
```

### CLI

```bash
dartlab collect 005930                # 기본 8분기
dartlab collect 005930 --quarters 12  # 12분기
dartlab collect --stats               # 수집 현황 통계
```

### 주요 함수

| 함수 | 역할 |
|------|------|
| `DocsCollector.collect()` | 단일 종목 수집 (2-phase: 목차 → HTML) |
| `collectMultiple()` | 여러 종목 순차 수집 (종목 간 30~60초 대기) |
| `collectionStats()` | 수집 현황 (상장사 수 / 수집 완료 / 미수집) |
| `listUncollected()` | corp_code API 기준 미수집 종목 |
| `listUncollectedKind()` | KRX KIND 기준 미수집 종목 |

### 저장 형식

- 경로: `{dataDir}/docs/{stockCode}.parquet`
- 스키마: `corp_code, corp_name, stock_code, year, rcept_date, rcept_no, report_type, section_order, section_title, section_url, section_content`
- 증분 수집: 기존 parquet에 새 섹션만 append (rcept_no 기준 중복 제거)

### eddmpython 원본과의 차이

| 항목 | eddmpython (DartDocs.py) | dartlab (collector.py) |
|------|------------------------|----------------------|
| HTTP 엔진 | Selenium/httpx | requests (동기) |
| 프록시 | SmartProxy 지원 | 불필요 (직접 크롤링) |
| API 키 | 직접 관리 | DartClient 통합 (멀티키 로테이션) |
| 저장 | CSV/parquet | parquet 원자적 교체 |
| 진행률 | tqdm | alive_progress |
| 공시 목록 | 자체 API 호출 | `listFilings()` 재사용 |

## 설계 원칙

1. **OpenDart 클래스 하나로 모든 것** — client, corpCode 내부 숨김
2. **멀티 키 로테이션** — rate limit 초과 시 자동으로 다음 키 전환 + 재시도
3. **유연한 날짜** — "2024", "2024-01", "2024-1-5", "20240105", datetime 전부 OK
4. **스마트 기본값** — 날짜 안 주면 최근 1년, 연도 안 주면 전년
5. **데이터 없음 = 빈 DataFrame** — 013 에러 대신 빈 결과 반환
6. **기존 dartlab과 독립** — 오프라인 parquet 체계와 별개, 실시간 API 조회용

## API 키 탐색 순서

1. `OpenDart(["key1", "key2"])` — 직접 리스트
2. `OpenDart("key")` — 직접 단일
3. 환경변수 `DART_API_KEYS` (쉼표 구분)
4. 환경변수 `DART_API_KEY` (단일)

## rate limit 전략

- OpenDART 제한: 키당 분당 600회
- 기본 설정: 키당 분당 580회 (안전 마진)
- 초과(020) 시: 자동으로 다음 키 전환 → 재시도
- 모든 키 소진 시: DartApiError 발생

## 범용 패턴

`engines/{market}/openapi/` 패턴으로 EDGAR 등에도 동일 적용:
- `engines/edgar/openapi/` — SEC EDGAR API
- 각 마켓별 facade 클래스 제공 (`OpenDart`, `OpenEdgar`)
