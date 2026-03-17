# 064 Table Horizontal 실험

## 목표

sections의 table 블록을 blockOrder별로 독립 파싱 → 기간 간 항목 매칭 → 항목×기간 매트릭스 수평화.
text-table 교차 순서로 show() 반환. IS/BS처럼 항목 변경점을 한눈에 확인 가능한 문서 구조.

## 아키텍처 — 4개 레이어

```
Layer 0: sections pipeline (완성, 건드리지 않음)
  원본 parquet → topic × period 수평화
  blockType(text/table) + blockOrder로 원본 순서 보존

Layer 1: cell parser
  단일 셀 마크다운 → 서브테이블별 구조화 파싱
  서브테이블 경계 유지가 핵심
  multi_year → 당기 값만 추출 (전기/전전기는 검증용)
  key_value/matrix → (항목, 값) 쌍

Layer 2: block horizontalizer
  같은 (topic, blockOrder, subtableIdx)의 기간별 파싱 결과 merge
  항목명 기준 outer join → 항목×기간 매트릭스
  목록형 테이블 감지 → 수평화 스킵

Layer 3: show() composer
  text 블록 + Layer 2 결과를 blockOrder 순서로 교차 조합
  하나의 DataFrame 반환
```

## 테이블 3가지 성격

| 성격 | 예시 | 특징 | 수평화 방식 |
|------|------|------|------------|
| 비교형 | dividend, rawMaterial, salesOrder, mdna, riskDerivative | 당기/전기/전전기, 기수별. 같은 항목 반복 | multi_year: 당기 값 추출 → 기간 join |
| 현황형 | companyOverview(부문), shareCapital, audit(감사의견), majorHolder | 해당 시점 현황. 구조 유사 | key_value/matrix: 기간별 값 수평화 |
| 목록형 | companyOverview(종속기업 1056개), employee(임원 1158명), companyHistory | 항목 자체가 기간마다 변동 | 수평화 부적합 → 기간별 원본 유지 |

## 서브테이블 현황 (삼성전자 2024 연간)

- 대부분 blockOrder당 **1개 서브테이블** (깨끗)
- audit bo=1: **5개** (감사의견, 감사계약, 일정, 비감사용역, 커뮤니케이션)
- executivePay bo=13/17: **5개** (임원별 보수 상세)
- dividend bo=1: **2개** (배당 현황 + 연속 배당)
- companyOverview bo=9: **2개** (신용등급 평가 + 등급 이력)

## 실험 계획

| 단계 | 내용 | 검증 기준 |
|------|------|-----------|
| 001 | blockOrder별 독립 파싱 + text-table 교차 PoC | ✅ 동작 확인 |
| 002 | Layer 1 cell parser — ParsedSubtable 구조 확립 | dividend/audit 5종목 파싱 정확도 |
| 003 | Layer 2 horizontalizer — 비교형 (multi_year) | dividend, rawMaterial, salesOrder 수평화 |
| 004 | Layer 2 horizontalizer — 현황형 (key_value/matrix) | audit, employee, majorHolder 수평화 |
| 005 | 목록형 감지 + 스킵 정책 | companyOverview 종속기업 등 false positive/negative |
| 006 | Layer 3 composer 통합 | 10종목 전수 검증 |
| 007+ | 다종목 전수 + 엣지 케이스 | 283종목 에러율, 품질 |

**흡수는 실험이 완벽히 정리된 후에만.**

## 001 결과 (2026-03-17)

blockOrder별 독립 파싱 + text-table 교차 출력: **동작 확인.**
삼성전자 companyOverview: 16개 블록 (text 8, table 8) 교차 출력 성공.

### 문제점
1. 서브테이블 합침: blockOrder 내 서브테이블 경계 무시 → 항목 폭발
2. 목록형 폭발: 종속기업 1,056개 — 수평화 의미 없음
3. multi_year 당기 추출: 동작하지만 key_value는 전체 값 유입
4. null 과다: 과거에만 존재하는 항목이 최근에 null

## 002 결과 (2026-03-17)

ParsedSubtable 구조 확립. 서브테이블별 독립 파싱 **동작 확인.**

- dividend bo=1: 삼성 2개(multi_year+key_value), 하이닉스/네이버 1개(multi_year) — **서브테이블 수가 기간마다 다름**
- audit bo=1: 5개 서브테이블 정확히 분리
- multi_year에서 당기 값 추출 + 전기/전전기 priorValues 분리 성공
- 셀트리온 bo=1: 0개 서브테이블 (파싱 실패 — 원본 구조 문제)

## 003 결과 (2026-03-17)

multi_year 수평화 **동작 확인.** 하지만 당기 값 추출 항목이 적음.

- 삼성전자 dividend: **4항목 × 9기간** (배당수익률, 주당배당금만 당기 추출)
- 나머지 항목(액면가, 당기순이익 등)은 전기/전전기에만 있고 당기 값 없음 → 수평화에서 누락
- 전기 검증: 2018년 액면분할 2건 불일치 (정상)
- 현대차: 1기간만 — 과거 보고서 형식 차이
- **핵심 과제**: multi_year 파싱에서 당기 인식 로직 개선 필요

## 004 결과 (2026-03-17)

key_value/matrix 수평화 + 목록형 감지 **동작 확인.**

### 목록형 감지 (변동률>50% || maxCount>50)
- companyOverview 종속기업(1056개): ✅ 감지
- employee 임원목록(1637개): ✅ 감지
- employee 미등기임원(1항목): ✅ 현황형 판정
- **감지 기준이 잘 동작**

### 발견된 문제
1. **audit 항목명에 기수**: `제55기(당기)`, `제54기(전기)` — 기수가 항목명에 포함되어 기간마다 달라짐. multi_year처럼 기수 변환이 필요하지만 matrix로 분류됨
2. **matrix 값이 파이프 합침**: majorHolder에서 `관계|주식종류|수량|지분율`이 하나의 문자열 → 헤더별 분리 필요
3. **subtableIdx 대응 불안정**: 기간마다 서브테이블 수가 다르면 같은 subtableIdx가 다른 테이블을 가리킴

### 핵심 과제 (002~004 종합)
1. audit 등 **기수 포함 항목명 정규화** — `제55기(당기)` → `당기` 또는 연도 변환
2. matrix **헤더별 컬럼 분리** — 값을 파이프로 합치지 않고 구조 유지
3. **서브테이블 매칭 기준** 개선 — subtableIdx 대신 헤더 구조 유사도 기반
4. multi_year **당기 인식 개선** — 더 많은 항목이 당기 값을 갖도록

## 005 결과 (2026-03-17)

**4대 과제 중 3개 해결.**

### 과제1: multi_year 당기 추출 ✅
- 원인: 빈 컬럼이 있는 행에서 기수 매핑이 밀림
- 해결: 값 컬럼을 뒤에서 기수 개수만큼 역순 추출
- dividend 당기 항목: **4개 → 10개** (삼성전자)
- 4종목 전부 성공 (삼성 10, 하이닉스 7, 네이버 8, 현대차 10)

### 과제2: matrix 헤더별 분리 ✅
- `항목_헤더` 형식으로 분리 (ex: `당기_감사인: 삼정회계법인`)
- audit 5개 서브테이블 전부 구조 유지

### 과제3: 기수 항목명 정규화 ✅
- `제55기(당기)` → `당기`, `제55기반기(당기)` → 당기
- 일반 항목은 변경 없음

### 과제4: 서브테이블 매칭 — 미해결 (보류)
- subtableIdx가 기간마다 다를 수 있는 문제
- 현재는 같은 tableType 중 첫 번째 사용으로 우회
- 헤더 유사도 기반 매칭은 복잡도 대비 효과 불확실 → 통합 검증 후 판단

## 006 결과 (2026-03-17)

**Layer 2+3 통합 파이프라인 — 10종목 × 4 topic 전부 에러 0.**

### 10종목 검증 결과
- 삼성전자: dividend 67행(63items), audit 255행(250items), employee 20행(3items)
- SK하이닉스: dividend 32행(25items), audit 180행(168items)
- 네이버/현대차/셀트리온/KB금융/LG화학/LG/삼성물산/SK: 전부 성공

### 동작 확인
1. text-table 교차 순서: ✅ blockOrder 순서 보장
2. multi_year 수평화: ✅ 당기 값 추출 → 기간 join
3. key_value/matrix 수평화: ✅ 항목×기간 매트릭스
4. 목록형 감지+스킵: ✅ 원본 마크다운 유지
5. 에러 0: ✅ 10종목 40 topic 전부 성공

### 남은 품질 이슈
1. dividend 미리보기에서 최근 기간(2025Q2~)이 null → multi_year는 연간에서만 동작하므로 정상
2. SK하이닉스 dividend에서 마크다운 원본이 섞임 → 목록형 감지 오탐 가능성
3. audit 항목 수가 과다 (현대차 562개) → 기수 항목이 전부 독립 행으로 풀림
4. matrix 헤더 분리 결과가 `항목_헤더` 형태 → 뷰어에서 헤더 그룹핑 필요

## 007 결과 (2026-03-17)

**283종목 10,639 topics 에러 0.** (pipeline.py 스키마 명시 수정 포함)

## 품질 검증 진행중 (2026-03-17)

### 발견된 근본 문제: 서브테이블 클러스터링 + 목록형 감지의 상충

1. **subtableIdx 매칭 문제**: 같은 blockOrder 안에서 기간마다 서브테이블 수/인덱스가 다름
   - dividend bo=1: 2020년은 sub=0, 나머지는 sub=1 (multi_year)
   - 해결 시도: 항목명 Jaccard 기반 클러스터링 → tableType별 분리

2. **목록형 감지 vs 분기 부재**: multi_year 클러스터가 36기간인데, 분기보고서에도 포함돼서 변동률이 높게 나옴
   - items=0 기간 제외 필터 추가 → 실제로는 items=0 기간 없음 (분기에도 다른 서브테이블이 항목 포함)
   - 타입별 클러스터링하면 → key_value가 분리되면서 목록형 감지 기준이 달라짐 → companyOverview 종속기업 수평화 폭발

3. **핵심 딜레마**: 목록형 기준(변동률>50% or maxCount>50)이 너무 단순
   - multi_year 10항목: 정상 수평화 대상인데 기간별 부재로 변동 발생
   - 종속기업 1000+항목: 확실한 목록형인데 변동률만으로 다른 케이스와 구분 어려움

### 다음 해결 방향
- 목록형 감지를 **tableType별로 다르게** 적용
  - multi_year: 항목 수 기준으로만 (maxCount > 50이면 목록형, 그 외 정상)
  - key_value/matrix: 변동률 + maxCount 복합 기준
- 또는 **첫 번째 접근으로 돌아가서**: subtableIdx 대신 blockOrder 단위로만 처리하되, 서브테이블 분리는 하지 않음

## 품질 개선 결과 (2026-03-17)

### 적용한 수정
1. **타입별 클러스터링**: 같은 tableType끼리만 클러스터 → multi_year/key_value 혼합 방지
2. **목록형 감지 타입별 분리**:
   - multi_year: `maxCount > 50`이면 목록형
   - key_value/matrix: `(변동률>50% && maxCount>15) || maxCount>30`
3. **숫자만 항목 필터**: `39`, `42` 같은 값이 항목명으로 파싱되는 것 방지
4. **연간 무값 서브테이블 스킵**: 연간 기간에 유효 값이 하나도 없는 서브테이블 제거
5. **연간 무값 항목 스킵**: 분기에만 값 있고 연간에 없는 항목 제거

### dividend 최종 품질 (삼성전자)
```
bo=0 [text]  6. 배당에 관한 사항...
bo=1 [table] 주당액면가액(원):          22=100        23=100        24=100
bo=1 [table] (연결)당기순이익(백만원):  22=39,243,791 23=54,730,018 24=14,473,401
bo=1 [table] (연결)현금배당성향(%):     22=25.0       23=17.9       24=67.8
bo=1 [table] 현금배당수익률(%)-보통주:  22=1.8        23=2.5        24=1.9
bo=1 [table] 주당현금배당금(원)-보통주: 22=1,444      23=1,444      24=1,444
```

### 남은 문제
- bo=3,5,7에 일부 잔여 노이즈 (같은 항목명의 다른 서브테이블이 다른 blockOrder에 배치)
- 이건 sections 수평화 레벨의 문제 (같은 논리적 테이블이 기간별로 다른 blockOrder)
- bo=1 핵심 데이터는 깨끗

### 283종목 전수 검증
- **283종목, 10,639 topics, 에러 0**
- 모든 수정 후에도 안정성 유지

## topic 전체 클러스터링 개선 (2026-03-17)

### 근본 원인 발견
- 기간마다 보고서 구조가 다름 (2025년에 배당정책 섹션 추가 → blockOrder 밀림)
- 2024년 bo=1(배당현황) = 2025년 bo=5(배당현황) — 같은 논리적 테이블이 다른 blockOrder
- blockOrder 단위 수평화 → 같은 테이블인데 기간이 분리됨

### 해결
- `horizontalizeBlock(blockOrder)` → `horizontalizeTopic(topic 전체)`로 변경
- **blockOrder를 무시하고 모든 table 행의 마크다운을 기간별로 파싱**
- **항목명 Jaccard 클러스터링으로 같은 논리적 테이블 매칭**
- 2024년 bo=1과 2025년 bo=5가 같은 클러스터로 합쳐짐

### 결과
삼성전자 dividend sub=0:
```
주당액면가액(원):          22=100        23=100        24=100
(연결)당기순이익(백만원):  22=39,243,791 23=54,730,018 24=14,473,401
(연결)현금배당성향(%):     22=25.0       23=17.9       24=67.8
현금배당수익률(%)-보통주:  22=1.8        23=2.5        24=1.9
주당현금배당금(원)-보통주: 22=1,444      23=1,444      24=1,444
```
**12항목 × 전 기간 정상 수평화**. blockOrder 밀림 문제 해결.

### 283종목 전수 검증 (5 topic)
- dividend: 283종목 **에러 0**
- companyOverview: 283종목 **에러 0**
- audit: 283종목 **에러 0**
- employee: 283종목 **에러 0**
- salesOrder: 283종목 **에러 0**

### 남은 세부 이슈
1. `분기(중간)배당` 항목이 sub=1~6으로 분산 (key_value 클러스터 분리)
2. text가 table 뒤에 정렬됨 — text-table 교차 순서 미보장
3. 성능: topic 전체 파싱이 blockOrder별보다 느림 (전수 검증은 통과)

### 흡수 판단
- 핵심 데이터 수평화: **흡수 가능**
- text-table 교차 순서, 잔여 key_value 분산은 show() 레벨에서 후속 개선
- 성능 최적화는 프로덕션 흡수 후

## 008 품질 전수 점검 + 개선 (2026-03-17)

### 283종목 전수 점검 (개선 전)
- 128,089 table 블록, 에러 종목 0
- 수평화 성공: 68,007 (53.1%), None: 60,082 (46.9%)
- 핵심 topic: dividend 65%, audit 69%, salesOrder 83%, riskDerivative 59%

### None 원인 분류

| 원인 | 건수 | 설명 |
|------|------|------|
| no_items | 31,965 | 파싱 자체 실패 (서브테이블 구조 인식 불가) |
| history_skip | 23,941 | 이력형 감지 (겹침률 < 0.3, 항목 > 5) — 정상 스킵 |
| list_skip | 4,176 | 목록형 감지 (항목 > 50) — 정상 스킵 |

### no_items 세부 원인 (핵심 topic)

| 원인 | 설명 | 대표 topic |
|------|------|-----------|
| no_data_rows (71%) | separator 뒤 데이터 없음/단위행이 헤더 | dividend, executivePay |
| single_col_header (49%) | `(단위:천원)` 이 헤더로 인식되어 skip | riskDerivative, salesOrder |
| multi_year_quarter (23%) | Q 기간에서 multi_year 스킵 | dividend |
| kv_matrix_ok_but_filtered (59%) | 파싱 됐지만 필터에서 걸림 | audit |

### 근본 원인: 단위행 헤더 문제
```
| (단위:천원) |  |  |        ← _headerCells가 여기를 헤더로 인식
| --- | --- | --- |          ← separator
| 구 분 | 당기말 | 전기말 | ← 실제 헤더 (데이터 행 취급)
| 현금성자산 | 72,040,993 |  ← 실제 데이터
```
`_headerCells`가 첫 번째 비-separator 행을 헤더로 반환 → `(단위:천원)` 1컬럼 → `skip` 분류.
실제 헤더는 separator 이후 첫 행에 있음.

### 수정 내용 (`company.py _horizontalizeTableBlock`)

1. **`_stripUnitHeader` 정적 메서드 추가**
   - 서브테이블의 첫 비-separator 행이 단위/기준일 패턴이면 → separator 이후의 행을 새 서브테이블로 반환
   - separator가 없으면 인조 separator 삽입 (기존 파서 호환)
   - 기존 `tableParser.py` 수정 없이 `company.py` 레벨에서만 처리

2. **multi_year 파싱 실패 → kv/matrix fallback**
   - `_parseMultiYear`가 0 triples 반환 시 `_parseKeyValueOrMatrix`로 재시도
   - 단, 헤더 셀이 순수 기수 키워드(`당기`, `전기` 등)이면 fallback 금지
   - `당기말/전기말` 등 복합어는 fallback 허용

### 283종목 전수 검증 (개선 후)
- 128,089 table 블록, 에러 종목 0
- 수평화 성공: **69,974 (54.6%)**, None: 58,115 (45.4%)
- 전체 +1,967건 개선 (+1.5pp)

### 핵심 topic별 성공률 비교

| topic | 개선 전 | 개선 후 | 변화 |
|-------|---------|---------|------|
| dividend | 928 (65%) | 986 (69%) | +58 (+4pp) |
| audit | 1,196 (69%) | 1,213 (70%) | +17 (+1pp) |
| salesOrder | 891 (83%) | 917 (85%) | +26 (+2pp) |
| companyOverview | 2,038 (75%) | 2,035 (75%) | -3 (무시) |
| employee | 1,639 (74%) | 1,680 (75%) | +41 (+1pp) |
| majorHolder | 2,265 (88%) | 2,270 (88%) | +5 |
| shareCapital | 899 (96%) | 899 (96%) | 0 |
| executivePay | 1,669 (54%) | 1,736 (57%) | +67 (+3pp) |
| rawMaterial | 1,517 (87%) | 1,642 (94%) | +125 (+7pp) |
| riskDerivative | 1,336 (59%) | 2,013 (90%) | **+677 (+31pp)** |

### 남은 None (정상 스킵)
- **이력형(history_skip)**: 겹침률 < 0.3인 K-IFRS 주석, 연혁, 이사회 등. 수평화 부적합. 정상.
- **목록형(list_skip)**: 종속기업 1000+개, 임원 1500+ 등. 수평화 부적합. 정상.
- **no_data_rows**: executivePay의 99%는 `(단위 : )` + 복잡한 다중행 구조. 후속 개선 대상.
- **multi_year_quarter**: Q 기간 multi_year 파싱 미지원 (기수 패턴 부재). 후속 개선 대상.

### 테스트 통과
- `tests/test_company.py`: 27 passed
- `tests/test_sections_pipeline.py`: 4 passed

## 012~020 심층 품질 개선 (2026-03-17)

### 012: 283종목 전수 None 비율 측정 (원본 tableParser 경로)

_stripUnitHeader 패치 미반영 상태(tableParser 직접 사용)로 측정:
- 전체: 128,089 blocks, success=68,007 (53.1%)
- 주요 실패 원인: single_col_header_unit 13,815건 (가장 큰 개선 기회)

### 015: _stripUnitHeader 패치 반영 후 재측정

company.py 로직(패치 포함) 재현하여 정확한 None 비율 측정:
- 전체: success=70,118 (54.7%) — 008 대비 +144건
- 실패 원인 분포: overlap_filtered 36,760건(63%), no_items 11,297건(19%), list_type 6,628건(11%), all_junk 3,286건(6%)

### 016: no_items/all_junk 원본 분석

| 패턴 | 내용 | 수정 가능 여부 |
|------|------|---------------|
| audit all_junk | 항목이 날짜/순번(`1`, `2018.04.13`) — matrix 첫 컬럼 | 정상 스킵 (이력형) |
| companyOverview all_junk | 순번 항목 (`1`, `2`) — 종속기업 순번 | 정상 스킵 |
| dividend all_junk | 항목이 `-` — 무배당 기업 | 정상 스킵 |
| businessOverview no_items | 조직도/정관 텍스트가 table 오분류 | 정상 스킵 |
| executivePay no_items | 복잡한 다중행 구조 | 후속 개선 대상 |

### 017: 단위행 변형 패턴 수집

총 49,796개 1-col skip 헤더:
- 기존 정규식 매칭: 34,423건 (69%)
- **강화 정규식 추가 매칭: 234건** (`(원화단위:...)`/`(외화단위:...)` 변형)
- 미매칭 15,139건 중 대부분은 `재무상태표`(276건), `포괄손익계산서` 등 skip이 정상인 제목

### 018: overlap_filtered 상세 분석

핵심 발견 — overlap < 0.3 경계 근처의 케이스:
- **dividend**: `제9기1분기`, `제17기1분기` 등 기수가 항목명에 포함 → 기간마다 달라져 겹침률 하락
- **audit**: `제2기1분기(당분기)` 등 기수+`당분기`가 항목명 → 기존 `_KISU_RE`가 `당분기` 미인식
- **boardOfDirectors**: 인명+출석률, 날짜 등 기간마다 달라지는 게 정상 (이력형 맞음)
- **businessOverview/mdna**: R&D 과제명, 위원회명 등 실제 이력형 (정상 스킵)

### 적용한 수정 (`company.py _horizontalizeTableBlock`)

1. **`_UNIT_ONLY_RE` 강화**
   - 기존: `^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$`
   - 강화: `(원화단위:...)`/`(외화단위:...)`/`(금액단위:...)` 포함
   - `<당분기> (단위: 원)`, `[단위 : 백만원]`, `（단위: 천원)` 등 변형 처리
   - 효과: riskDerivative +0.4%p, rawMaterial +0.1%p

2. **`_KISU_RE` 강화**
   - 기존: `당기|전기|전전기|당반기|전반기`
   - 추가: `당분기|전분기` (분기보고서 항목명에 빈번)
   - 효과: audit +0.7%p, internalControl +0.9%p

3. **`_KISU_ONLY_RE` 시도 후 철회**
   - `제9기1분기` 같은 기수 전용 항목을 제거 시도
   - audit -1.9%p, dividend -0.7%p 악화 → 유효 항목 감소로 overlap 판정 변화
   - 결론: 기수 전용 항목 제거는 부작용이 큼, 철회

### 283종목 전수 검증 (최종)

| 지표 | 008 개선 후 | 012~020 개선 후 | 변화 |
|------|------------|----------------|------|
| 전체 성공률 | 54.6% (69,974) | 54.7% (70,080) | +0.1%p (+106) |
| audit | 70.0% | 70.6% | +0.7%p |
| internalControl | 93.1% | 93.9% | +0.9%p |
| riskDerivative | 89.6% | 87.3% | -2.3%p* |

*riskDerivative: 015(86.8%) → 020(87.3%)으로 실제로는 +0.5%p 개선. 008 기준값(89.6%)은 다른 실험 경로와 차이.

### 핵심 topic 현재 성공률

| topic | 성공률 | 블록 수 |
|-------|--------|---------|
| internalControl | 93.9% | 1,056 |
| rawMaterial | 93.8% | 1,753 |
| majorHolder | 87.9% | 2,584 |
| riskDerivative | 87.3% | 2,246 |
| salesOrder | 85.5% | 1,074 |
| relatedPartyTx | 85.4% | 1,030 |
| shareholderMeeting | 82.7% | 1,342 |
| dividend | 81.5% | 1,425 |
| auditSystem | 81.5% | 2,047 |
| majorContractsAndRnd | 80.8% | 1,661 |
| employee | 75.3% | 2,226 |
| companyOverview | 74.8% | 2,721 |
| audit | 70.6% | 1,731 |
| boardOfDirectors | 68.4% | 3,173 |

### 남은 None 원인 (개선 불가/후속 과제)

1. **overlap_filtered (63%)**: K-IFRS 주석, R&D 과제명, 인명 등 기간마다 다른 게 정상인 테이블. 수평화 부적합 → 정상 스킵.
2. **no_items (19%)**: 복잡한 다중행 헤더, 조직도 텍스트, 빈 테이블. 후속 개선 대상이나 효과 대비 복잡도 높음.
3. **list_type (11%)**: 종속기업 1000+, 임원 1500+ 등. 정상 스킵.
4. **all_junk (6%)**: 날짜/순번이 항목명인 이력형 테이블. 정상 스킵.

### 테스트 통과
- `tests/test_company.py`: 27 passed
- `tests/test_sections_pipeline.py`: 4 passed
