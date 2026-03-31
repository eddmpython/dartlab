# EDGAR 엔진 운영 규칙

## 한눈에 보기

| 항목 | 상태 |
|------|------|
| 안정성 | beta (DART core stable 이후) |
| Provider | `providers/edgar/` — CompanyProtocol 완전 구현 |
| 방어막 | `test_protocol.py::test_edgar_has_all_dart_public_methods` |
| 데이터 | HuggingFace `eddmpython/dartlab-data` (edgar/finance, edgar/docs) |

## 핵심 규칙: DartCompany ↔ EdgarCompany 동기화

1. **DartCompany에 public 메소드를 추가하면 EdgarCompany에도 추가한다.**
2. DART 전용 메소드는 `test_protocol.py`의 `_DART_ONLY_EXEMPT`에 **사유 주석과 함께** 등록한다.
3. `_DART_ONLY_EXEMPT` 등록 없이 DART에만 메소드를 추가하면 테스트가 실패한다.

## EXEMPT 등록 기준

EXEMPT에 등록할 수 있는 경우:
- **데이터 소스 구조 차이**: DART 로컬 parquet vs EDGAR on-demand API (`rawDocs`, `update` 등)
- **한국 시장 전용**: KRX listing 기반 기능 (`codeName`, `resolve`, `search`, `listing`)
- **DART report 전용 구조화 데이터**: SEC에 동등한 구조가 없는 경우 (`network`)

EXEMPT에 **등록하면 안 되는** 경우:
- 범용 분석 기능 (analysis, review, forecast, valuation)
- CompanyProtocol 필수 메소드
- 사용자 대면 메소드 (ask, chat, review, insights)

## EDGAR와 DART의 데이터 소스 차이

| 영역 | DART | EDGAR |
|------|------|-------|
| 재무제표 (BS/IS/CF) | 로컬 parquet (K-IFRS) | on-demand API (US-GAAP XBRL) |
| 공시 문서 | 로컬 parquet (HTML 파싱) | on-demand API (10-K/10-Q 파싱) |
| 정기보고서 (report) | 28 apiType (구조화 테이블) | **없음** — 10-K item에서 비정형 추출 |
| 계정명 | 한국어 (계정명 컬럼) | snakeId (account 컬럼) |
| 통화 | KRW (조/억 포맷) | USD ($B/$M 포맷) |
| 시가총액/주가 | Naver → Yahoo fallback | Yahoo → FMP fallback |

## Universal Select Bridge

`show.py::_bridgeKoreanSnakeId()` — 한국어 계정명과 snakeId 간 자동 번역:
- `Company("AAPL").select("IS", ["매출액"])` → `sales` row 반환
- `Company("005930").select("IS", ["sales"])` → `매출액` row 반환
- 혼합 쿼리도 지원

## toDict Bridge

`_helpers.py::toDict()` — EDGAR DataFrame의 snakeId 키를 한국어 키로 자동 변환:
- analysis 함수에서 `data.get("매출액")` 이 DART/EDGAR 양쪽에서 동작

## 통화 포맷

- `review/builders.py`: `_REVIEW_CURRENCY` — review 렌더링 시 KRW/USD 분기
- `analysis/financial/capital.py`: `_ANALYSIS_CURRENCY` — analysis 금액 포맷 분기
- `review/registry.py::buildBlocks()`: `company.currency`에서 자동 설정

## 테스트

```bash
# 동기화 테스트
bash scripts/test-lock.sh tests/ -k "test_edgar_has_all_dart_public_methods" -v

# Protocol 적합성 전체
bash scripts/test-lock.sh tests/test_protocol.py -v

# EDGAR 전용 테스트
bash scripts/test-lock.sh tests/ -k "edgar" -v --tb=short
```
