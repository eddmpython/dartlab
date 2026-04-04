# EDGAR 동기화 규칙

DartCompany ↔ EdgarCompany 인터페이스 동기화의 단일 규칙 문서.
데이터 소스/수집/분석 동작은 각 엔진 문서에 통합되어 있다:
- 데이터 수집/배포/freshness → `ops/data.md`
- Company namespace/notes/데이터 소스 차이 → `ops/company.md`
- scan EDGAR 11축/프리빌드 → `ops/scan.md`
- gather market 분기 → `ops/gather.md`
- analysis 통화/브릿지 → `ops/analysis.md`
- review 통화 포맷 → `ops/review.md`

## 한눈에 보기

| 항목 | 상태 |
|------|------|
| 안정성 | beta (DART core stable 이후) |
| Provider | `providers/edgar/` — CompanyProtocol 완전 구현 |
| 방어막 | `test_protocol.py::test_edgar_has_all_dart_public_methods` |
| 데이터 | HuggingFace `eddmpython/dartlab-data` (edgar/finance, edgar/docs, edgar/scan) |

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

## Universal Select Bridge

`show.py::_bridgeKoreanSnakeId()` — 한국어 계정명과 snakeId 간 자동 번역:
- `Company("AAPL").select("IS", ["매출액"])` → `sales` row 반환
- `Company("005930").select("IS", ["sales"])` → `매출액` row 반환

## toDict Bridge

`_helpers.py::toDict()` — EDGAR DataFrame의 snakeId 키를 한국어 키로 자동 변환:
- analysis 함수에서 `data.get("매출액")` 이 DART/EDGAR 양쪽에서 동작

## 통화 포맷

- `review/builders.py`: `_REVIEW_CURRENCY` — review 렌더링 시 KRW/USD 분기
- `analysis/financial/capital.py`: `_ANALYSIS_CURRENCY` — analysis 금액 포맷 분기
- `review/registry.py::buildBlocks()`: `company.currency`에서 자동 설정

## EDGAR alias 확장 (select bridge)

`show.py::_expandEdgarAliases()` — DART snakeId를 EDGAR snakeId로 확장:
- `cash_flows_from_financing` → `cash_flows_from_financing_activities`
- `capex` → `purchase_of_property_plant_and_equipment`
- analysis calc 함수에서 한국어 계정명 사용 → bridge → alias 확장 → EDGAR 매칭

`_quarterlyCols()` / `quarterlyColsFromPeriods()` — EDGAR 연간 데이터 fallback:
- DART: 2025Q4, 2025Q3... (분기)
- EDGAR: 2024, 2023... (연간)
- `"Q" in c` 매칭 실패 시 4자리 연도 컬럼으로 fallback

## 구조적 한계 (SEC 데이터 없음 — 허용된 None)

analysis 14축 중 4축에서 DART report 전용 서브키가 None:

| 축 | None 키 | 원인 | SEC 대안 |
|---|---|---|---|
| 수익구조 | segmentComposition, segmentTrend, growthContribution, concentration | DART docs `productService`/`salesOrder` topic 전용 | XBRL segment fallback 구현했지만 비표준 |
| 비용구조 | rawMaterialBreakdown | DART report `rawMaterial` API 전용 | SEC에 없음 |
| 자본배분 | treasuryStockStatus | DART report `treasuryStock` 상세 API 전용 | XBRL에 총수량만 |
| 투자효율 | investmentInOther | DART report `investedCompany` API 전용 | SEC에 없음 |

**이 4건은 SEC 공시 구조의 근본적 차이로 인한 것이며, 허용된 None이다.**
DART report는 OpenDART API가 구조화 테이블을 직접 제공하지만, SEC에는 동등한 구조화 API가 없다.

## 테스트

```bash
# 동기화 테스트
bash scripts/test-lock.sh tests/ -k "test_edgar_has_all_dart_public_methods" -v

# Protocol 적합성 전체
bash scripts/test-lock.sh tests/test_protocol.py -v

# EDGAR 전용 테스트
bash scripts/test-lock.sh tests/ -k "edgar" -v --tb=short
```
