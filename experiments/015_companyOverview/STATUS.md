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

총 267종목 → 파싱 성공 227 / 실패 40 (사업보고서 미보유)

| 필드 | 성공 | 비율 | 비고 |
|------|------|------|------|
| isVenture | 227 | 100.0% | 전 종목 |
| founded | 212 | 93.4% | 15종목 원문에 없음 |
| address | 204 | 89.9% | 23종목 서술형 미매칭 |
| homepage | 204 | 89.9% | address와 동일 범위 |
| listedDate | 200 | 88.1% | 27종목 원문에 없음 |
| subsidiaryCount | 52 | 22.9% | 합계 표 있는 종목만 |
| creditRatings | 49 | 21.6% | 신용등급 보유 기업만 |
| isSME | 34 | 15.0% | 해당 항목 있는 종목만 |

creditRatings 검증:
- 삼성전자: Moody's Aa2, S&P AA- ✓
- SK하이닉스: 국내 AA×3, Moody's Baa2, S&P BBB, Fitch BBB ✓
- 유진증권: A2+×3사 ✓
- 신한지주: AAA×3사 ✓
- 등급 설명표 오탐 제거 ✓

address 검증: 30종목 샘플 오탐 0건

## 확정 로직

`parseOverview(text: str) -> dict`

주요 설계:
- address: 7패턴 fallback (표, 괄호, 공백변형, 본점소재지, 따옴표 서술)
- homepage: 6패턴 fallback (URL, 표, 괄호, www)
- subsidiaryCount: 합계 표(기말값) 우선 → 서술 fallback
- creditRatings: 등급 설명표 컷오프 → 범위표기 제거 → 서술문 → 현등급표 → 이력 최신행
- founded: 설립일자 키워드 → 서술형 "YYYY년 M월 D일 설립" fallback

## 배치 준비 완료
