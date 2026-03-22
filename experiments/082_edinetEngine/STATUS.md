# 082_edinetEngine — EDINET(일본) 엔진 실험

## 목표
DART/EDGAR와 동일한 아키텍처로 일본 EDINET 전자공시 엔진 구축.
데이터수집 → sections 수평화 → 재무 정규화 파이프라인 완성.

## 현재 상태
- 엔진 스캐폴딩 완료 (`engines/edinet/` — 15개 파일)
- **mapper.py 대규모 확장 완료** (edinet-mcp taxonomy.yaml 161개 필드 전량 흡수)
  - CORE_MAP: **328개** (165 고유 snakeId) — IS 42 + BS 79 + CF 40 + 기존
  - ID_SYNONYMS: **115개** (J-GAAP/IFRS/US-GAAP 3중 변형 통합)
  - ACCOUNT_NAME_SYNONYMS: **198개** (일본어 계정명 동의어)
  - 19/19 매핑 테스트 통과
- sectionMappings.json: 46개 section→topicId
- API 키 미발급 (일본 IP 지역 제한) → 오프라인 실험 진행 중

## 실험 목록

| # | 파일 | 상태 | 요약 |
|---|------|------|------|
| 002 | xbrlTaxonomy.py | **완료** | DART↔EDINET 계정 공유분 분석 |
| 003 | taxonomyCoverage.py | **완료** | edinet-xbrl 131개 element 매핑 커버리지 측정 |
| 001 | edinetApiExplore.py | 대기 | API v2 응답 구조 파악 (키 필요) |
| 004 | accountTaxonomy.py | 대기 | J-GAAP prefix/계정 코드 분석 (키 필요) |
| 005 | initialCoreMap.py | 대기 | 실제 데이터 기반 CORE_MAP 검증 (키 필요) |
| 006 | mappingRate.py | 대기 | 실제 데이터 매핑률 측정 (키 필요) |
| 007 | sectionMapping.py | 대기 | section→topicId 매핑률 (키 필요) |

## 주요 발견

### 실험 002: DART↔EDGAR snakeId 교집합
- DART 5,539개 vs EDGAR 187개 → 교집합 46개만
- 네이밍 차이가 주 원인 (EDGAR_TO_DART_ALIASES 같은 alias 레이어 필요)

### EDINET 고유 snakeId (DART/EDGAR에 없음)
- `ordinary_income` — 経常利益 (J-GAAP 고유)
- `extraordinary_income/loss` — 特別利益/損失 (J-GAAP 고유)
- `net_assets` — 純資産 (J-GAAP: 自己資本+少数株主持分)
- `book_value_per_share`, `dividend_per_share`, `net_profit_parent`

### taxonomy.yaml 흡수 (2026-03-22)
- 출처: [ajtgjmdjp/edinet-mcp](https://github.com/ajtgjmdjp/edinet-mcp) taxonomy.yaml
- IS 42개 + BS 79개 + CF 40개 = **161개 필드**, **233개 XBRL element 변형**
- J-GAAP / IFRS / US-GAAP 3중 변형을 하나의 snakeId로 통합
- BS 세부 계정 대폭 추가: PPE 내역(건물/구축물/기계/토지 등), 재고 내역, 투자 내역
- CF 세부 항목 40개 전량 포함: 유형자산 취득/매각, 차입/상환, 배당금 등

### 다음 필요 작업
1. EDINET API 키 발급 (일본 VPN 필요) → 실제 데이터 수집
2. 수집된 데이터로 매핑률 측정 (실험 005~006)
3. sections 수평화 검증 (실험 007)

## 의존성
- EDINET API 키 등록: https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1 (Azure AD B2C, 일본 IP만 접속 가능)
- 환경변수: `EDINET_API_KEY`
