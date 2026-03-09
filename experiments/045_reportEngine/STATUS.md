# 045_reportEngine 실험 현황

## 목적
OpenDART 정기보고서 API 응답 parquet에서 구조화된 데이터를 추출하는 reportEngine 설계

## 데이터 구조
- 153개 wide-format 컬럼 (apiType별로 사용 컬럼이 다르고 나머지 null)
- 22개 apiType (모든 종목 동일)
- 2015~2026 시계열
- 모든 값이 String (숫자도 문자열)

## 실험 결과

### 001_exploreSchema — 완료
- 22개 apiType 모든 종목 동일 확인
- apiType별 유효 컬럼 종목간 100% 일치
- 숫자형/문자형 분류 완료

### 002_extractAndClean — 완료
- `extract(stockCode, apiType)` 범용 함수 검증
- null 컬럼 자동 제거 동작 확인
- `tryNumeric()` 숫자 변환 + STR_OVERRIDES로 오탐 방지

### 003_timeseriesPivot — 완료
- dividend/employee/majorHolder 시계열 피벗 성공
- 삼성전자 기준: DPS 722→732원, 직원 19만→26만, 최대주주 지분 20.15%

### 004_crossValidation — 완료 (10개 종목)
- **핵심 발견:**
  1. 배당은 Q4(사업보고서) 기준으로 추출해야 함 (Q2는 대부분 "-")
  2. employee는 Q2(반기보고서) 기준이 가장 풍부
  3. majorHolder "계" 소계행 없는 종목 존재 (신한지주) → 개별 합산 fallback
  4. 지주회사 employee는 본사 인원만

## 엔진 설계 방향

```
engines/reportEngine/
├── __init__.py       # 공개 API
├── extract.py        # 범용 extract + tryNumeric
├── types.py          # apiType 정의 + 컬럼 매핑
└── pivot.py          # apiType별 시계열 피벗 (dividend, employee, majorHolder 등)
```

핵심 패턴:
- `extract(stockCode, apiType)` → 깔끔한 DataFrame (null 컬럼 제거 + 숫자 변환)
- apiType별 특화 피벗 함수 (배당은 Q4, employee는 Q2 등)
- Company 클래스에서 docsParser fallback으로 활용

## apiType → 분기 기준 매핑
| apiType | 기준 분기 | 이유 |
|---|---|---|
| dividend | Q4 (사업보고서) | Q2는 "-" |
| employee | Q2 (반기보고서) | 연간 합산 데이터 |
| majorHolder | Q2 (반기보고서) | 가장 풍부 |
| executive | Q2 (반기보고서) | 가장 풍부 |
| auditOpinion | Q4 (사업보고서) | 연간감사 |
| stockTotal | Q2 (반기보고서) | 가장 풍부 |
