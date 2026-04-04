# Scan

전 종목 횡단분석. `scan()` 단일 진입점으로 시장 전체를 한 번에. DART + EDGAR 양쪽 지원.

| 항목 | 내용 |
|------|------|
| 레이어 | L1 |
| 진입점 | `dartlab.scan()`, `c.governance()` 등 |
| 소비 | providers/(dart, edgar), core/finance, 프리빌드 parquet |
| 생산 | ai가 시장 비교에 사용, analysis와 독립 |
| 축 | DART 정식 7축 + account/ratio 등 13축, EDGAR 11축 |

## 단일 진입점

- **`dartlab.scan()`** 하나로 모든 축에 접근한다
- `c.governance()` 등은 scan 내부 view — 별도 전역 함수가 아니다
- 새 축은 `scan/` 아래 모듈로 추가한다

## 정식 7축

| 축 | 타입 | 소스 | 설명 |
|------|------|------|------|
| governance | company-bound | majorHolder, outsideDirector, executivePay, auditOpinion, minorityHolder | 지배구조 5축 100점 → A~E 등급 |
| workforce | company-bound | employee, executivePayIndividual, finance IS | 인력/급여, 인건비율, 1인당부가가치, 급여매출괴리 |
| capital | company-bound | dividend, treasuryStock, capitalChange | 주주환원 분류 (환원형/중립/희석형) |
| debt | company-bound | corporateBond, finance BS/IS | 부채 구조, ICR, 위험등급 |
| network | market-level | docs sections | 관계 네트워크 |
| signal | market-level | docs sections | 키워드 트렌드 |
| disclosureRisk | market-level | changes.parquet | 공시 변화 선행 리스크 (우발부채, 키워드, 감사변경, 계열변화, 사업전환) |

signal은 company-bound API로 연결하지 않는다 — `dartlab.signal()` market API로만 노출.

## Company 인터페이스

```python
c.governance()          # 이 회사 1행
c.governance("all")     # 전체 상장사
c.governance("market")  # 유가/코스닥 요약

# signal은 market API만
dartlab.signal()        # 전체 키워드 트렌드
dartlab.signal("AI")    # 특정 키워드 연도별
```

## scan 프리빌드 가속

종목별 parquet 2700+개 순차 스캔 → 수분. 프리빌드 합산 parquet → **17초**.

```
data/dart/scan/
├── changes.parquet     # docs 변화 전종목 5Y
├── finance.parquet     # finance 전종목 5Y
└── report/             # apiType별 12개 parquet
```

- 배포자: `dartlab collect --scan` → HF push
- 사용자: `downloadAll("scan")` (271MB) → 즉시 횡단 분석
- scan 파일 없으면 HF 자동 다운로드 시도, 실패 시 종목별 순회 fallback

## EDGAR scan (11축)

EDGAR scan은 XBRL companyfacts 기반. DART scan과 동일 인터페이스.

```python
from dartlab.scan._edgar_scan import edgarScan
df = edgarScan("profitability")   # 전종목 수익성
df = edgarScan("valuation")       # 밸류에이션
```

### EDGAR scan 축

| 축 | 지표 | 종목 수 | 상태 |
|---|------|--------|------|
| profitability | opMargin, netMargin, ROE, ROA | ~6,600 | ✅ |
| growth | revenueYoY, opYoY, niYoY | ~5,600 | ✅ |
| quality | cfToNi, accrualRatio | ~8,300 | ✅ |
| liquidity | currentRatio, quickRatio | ~4,800 | ✅ |
| efficiency | assetTurnover, CCC | ~6,100 | ✅ |
| cashflow | OCF/ICF/FCF, 패턴 분류 | ~5,700 | ✅ |
| dividendTrend | payoutRatio, 패턴 | ~4,000 | ✅ |
| capital | 배당+자사주, 분류 | ~4,800 | ✅ |
| debt | debtRatio, ICR, 위험등급 | ~7,300 | ✅ |
| valuation | EBITDA, equityMultiplier, ROE | ~16,500 | ✅ |
| audit | AuditFees, NonAuditFees | 가변 | ✅ |

### EDGAR scan 프리빌드

```
data/edgar/scan/
└── finance.parquet    # 전종목 연간 BS/IS/CF 주요 22계정
```

- 빌드: `dartlab collect --tier sp500 --scan` 또는 `buildEdgarScan(sinceYear=2021)`
- 배치 200개 단위 + 중간 파일 병합 (메모리 안전)
- DART scan 프리빌드와 동일 패턴

### DART vs EDGAR scan 갭

| 축 | DART | EDGAR | 사유 |
|---|------|-------|------|
| governance | ✅ 5축 100점 | — | DEF 14A proxy 파싱 필요 |
| workforce | ✅ | — | SEC 구조화 데이터 없음 (10-K 텍스트 제한적) |
| network | ✅ | — | SEC에 출자/계열 관계 구조화 데이터 없음 |
| signal | ✅ | — | DART 공시 키워드 트렌드 전용 |
| disclosureRisk | ✅ | — | DART changes.parquet 전용 |

## 설계 원칙

- scanner는 Company를 import하지 않는다 (역의존 방지)
- Company에서 scan 데이터는 `_ensure*()` 경유로 접근
- 스코어링/분류 로직 변경은 실험 검증 후 반영

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/scan/` | DART 축 모듈 |
| `src/dartlab/scan/_edgar_scan.py` | EDGAR 11축 scan 디스패치 |
| `src/dartlab/scan/_edgar_helpers.py` | EDGAR scan 공용 헬퍼 |
| `src/dartlab/scan/edgarBuilder.py` | EDGAR scan 프리빌드 |
| `src/dartlab/scan/network/` | 관계 네트워크 (DART 전용) |
| `src/dartlab/scan/disclosureRisk/` | 공시 변화 리스크 (DART 전용) |
| `src/dartlab/core/finance/scanAccount.py` | 범용 계정/비율 전종목 조회 |
| `src/dartlab/providers/edgar/finance/scanAccount.py` | EDGAR 계정 스캔 |
