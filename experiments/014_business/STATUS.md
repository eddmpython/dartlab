# 014_business — 사업의 내용 추출 실험

## 목표
- "II. 사업의 내용" 섹션에서 사업개요, 주요제품 등 하위 섹션 추출
- 연도별 변경 탐지 (diff 기반)
- 전 종목 커버리지 확인

## 실험 스크립트

| 파일 | 내용 | 상태 |
|------|------|------|
| 001_sectionPatterns.py | 전 종목 section_title 패턴 전수조사 | 완료 |
| 002_sectionExtract.py | 섹션 추출 로직 (하위분리/통합 양쪽) | 완료 |
| 003_diffChanges.py | 연도별 변경률 계산 + diff 원문 | 완료 |
| 004_fullCoverage.py | 전 종목 추출 커버리지 테스트 | 완료 |

## 사전 조사 결과

### 섹션 패턴
- 229개 종목 중 226개: II.사업의내용 + 하위섹션 둘 다 있음
- 3개 종목: 둘 다 없음 (삼성전기, 우리금융지주, 대진첨단소재)
- 160개 종목: 표준 7개 하위 섹션 패턴

### 표준 하위 섹션 (160종목)
1. 사업의 개요
2. 주요 제품 및 서비스
3. 원재료 및 생산설비
4. 매출 및 수주상황
5. 위험관리 및 파생거래
6. 주요계약 및 연구개발활동
7. 기타 참고사항

### 변형 패턴
- 금융업: `1. (금융업)사업의 개요`, `5. 재무건전성 등 기타 참고사항`
- 복합업종: `(제조서비스업)` + `(금융업)` 접두사
- 연도별 변화: 삼성전자 2010~2021은 통합, 2022~ 분리

### 연도별 변경 탐지
- difflib.SequenceMatcher로 변경률 계산 가능
- 변경률 >30%면 유의미한 변화 시점
- AI 없이 "뭐가 바뀌었는지 요약"은 한계 → diff 원문 제공

## 실험 결과

### 001 — 전 종목 패턴 전수조사
- 267개 중 229개 사업보고서 보유
- 226개: II.사업의내용 + 하위섹션 둘 다 있음
- 3개: 둘 다 없음

### 002 — 섹션 추출 로직
- 2가지 경로: 하위섹션 직접 매칭 / 통합 텍스트 번호 분리
- `splitByNumber` 수정: 순차 번호 추적으로 본문 내 번호목록 오탐 해결
- 금융업 `재무건전성`, 복합업종 `(제조서비스업)/(금융업)` 접두사 처리

### 003 — 연도별 변경 탐지
- 5개 종목 테스트 (삼성전자, SK하이닉스, 대교, 현대차, 동화약품)
- 변경률 >30% 시점 자동 탐지 → diff 원문 출력
- 삼성전자 2021→2022: 섹션 분리 시점 (구조 변경)

### 004 — 전 종목 커버리지
- 229/267 성공 (85.8%), 38개 실패 (사업보고서 없음)
- 섹션별 추출률: overview 95%+, products 90%+, materials 85%+
- 섹션 0개 종목: 3개 (통합 텍스트에서 번호 패턴 못 찾은 경우)

## 확정 로직
- `extractSections(stockCode)` → `{year, sections: {key: {title, chars, preview}}}`
- `splitByNumber(text)` → 순차 번호 추적 방식
- `classifySection(title)` → SECTION_KEYS 기반 분류
- 변경 탐지: `difflib.SequenceMatcher.ratio()` + `unified_diff`

## 패키지 배치 완료

`src/dartlab/finance/business/` — 4개 파일

| 파일 | 내용 |
|------|------|
| types.py | BusinessSection, BusinessChange, BusinessResult |
| parser.py | extractFromSubSections, extractFromUnified, splitByNumber, computeChanges |
| pipeline.py | business(stockCode) → BusinessResult \| None |
| __init__.py | export |

### 전 종목 검증 결과
- 227/267 성공 (Result 반환)
- 40개 None (사업보고서 미보유)
- **오류 0개**
- 섹션 1~2개: 20개 (금융업, 리츠, 스팩)
