# 015_companyOverview — 회사의 개요 추출 실험

## 목표
- "I. 회사의 개요" → "1. 회사의 개요" 섹션에서 정량 데이터 추출
- 설립일, 본사주소, 홈페이지, 신용등급, 종속기업 수, 중소기업 여부 등
- 전 종목 커버리지 확인 + 품질 검증

## 실험 스크립트

| 파일 | 내용 | 상태 |
|------|------|------|
| 001_sectionSurvey.py | 전 종목 section_title 패턴 전수조사 | 완료 |
| 002_parseFields.py | 정량 필드 파싱 로직 개발 + 다종목 테스트 | 완료 |
| 003_fullCoverage.py | 전 종목 파싱 커버리지 테스트 | 완료 |

## 실험 결과

### 001 — 섹션 전수조사
- 267개 중 229개 사업보고서 보유
- 226/229: "1. 회사의 개요" 있음 (98.7%)
- 3개 없음: 009150, 316140, 393970

### 002 — 파싱 로직 개발

추출 필드 8개:
- `founded`: 설립일자 (YYYY-MM-DD)
- `address`: 본사 주소
- `homepage`: 홈페이지 URL
- `subsidiaryCount`: 종속기업 수 (합계 표 → 서술 fallback)
- `isSME`: 중소기업 해당 여부
- `isVenture`: 벤처기업 해당 여부
- `creditRatings`: 신용등급 [{agency, grade}]
- `listedDate`: 상장일 (YYYY-MM-DD)

제거한 필드:
- `isMidCap`: 전 종목 0건 — 공시에 항목 없음

개선 이력:

| 라운드 | 개선 내용 |
|--------|-----------|
| 1차 | isSME 오매칭, address "," 오탐, creditRatings 대량 중복 수정 |
| 2차 | address 7패턴 (표/괄호/공백/본점소재지), homepage 6패턴 추가 |
| 3차 | subsidiaryCount 합계 표 파싱, creditRatings 설명표 제외+범위표기 제거+서술문 우선+현등급 요약표 |

### 003 — 전 종목 최종 커버리지

총 267종목 → 파싱 성공 227 / None 40 (사업보고서 미보유)

| 필드 | 성공 | Missing | Failed | 비고 |
|------|------|---------|--------|------|
| isSME | 227 | 0 | 0 | 전 종목 100% |
| isVenture | 227 | 0 | 0 | 전 종목 100% |
| subsidiaryCount | 220 | 0 | 7 | 합계 표 + 0건 처리 포함 |
| founded | 212 | 15 | 0 | 원문에 없는 종목만 missing |
| address | 204 | 12 | 11 | 7패턴 fallback |
| homepage | 204 | 13 | 10 | 6패턴 fallback |
| listedDate | 200 | 0 | 27 | 원문 형식 다양 |
| creditRatings | 102 | 69 | 56 | 신용등급 보유+파싱 가능 기업 |

missing/failed 구분:
- missing: 원문에 해당 항목 자체가 없는 필드 (예: "해당사항 없음")
- failed: 항목은 있지만 파싱 실패한 필드

creditRatings 검증:
- 삼성전자: Moody's Aa2, S&P AA- ✓
- SK하이닉스: 국내 AA×3, Moody's Baa2, S&P BBB, Fitch BBB ✓
- NAVER: 한국기업평가 AA+, 한국신용평가 AA+ ✓
- 신한지주: AAA×3사 ✓
- 등급 설명표 오탐 제거 ✓

address 검증: 30종목 샘플 오탐 0건

## 확정 로직

`parseOverview(text: str) -> dict`

주요 설계:
- address: 7패턴 fallback (표, 괄호, 공백변형, 본점소재지, 따옴표 서술)
- homepage: 6패턴 fallback (URL, 표, 괄호, www)
- subsidiaryCount: 합계 표(기말값) 우선 → 전부 대시(0건) → 서술 fallback
- creditRatings: 섹션경계 컷오프 → 해당없음 감지 → 등급 설명표 컷오프 → 범위표기 제거 → (Stable)/부정적 제거 → 날짜 정규화 → 서술문 → 현등급표 → 이력 최신행
- isSME: 다중 파이프 테이블 형식 지원 (`| 여부 | | 미해당 |`)
- founded: 설립일자 키워드 → 서술형 "YYYY년 M월 D일 설립" fallback
- 지원 신용평가 기관: 한국신용평가, 한국기업평가, NICE/나이스신용평가, 서울신용평가, 한국평가데이터, 한국기업데이터, 나이스디앤비, Moody's, S&P, Fitch, 한기평, 한신평, NICE신평

## 배치 완료

- `src/dartlab/finance/companyOverview/` 패키지 생성
- `Company.overview()` 메서드 추가
- `finance/__init__.py` 전 모듈(15개) 등록
- `API_SPEC.md` 업데이트
