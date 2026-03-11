# 056 사업보고서 섹션 맵 (Section Map)

## 핵심 사상

DartLab의 근원적 가치는 **"모든 것이 비교 가능"**이다.

finance 엔진이 한 일을 떠올리면:
- 270개 종목의 XBRL 계정ID가 전부 다르다 (34,249개 변형)
- 이걸 하나의 snakeId 체계로 통일했다 (accountMappings.json)
- 결과: **어떤 회사든 같은 계정명으로 수평 비교 가능**

sections도 완전히 같은 패턴을 밟는다:
- 270개 종목의 section_title이 회사마다 미세하게 다르다
- 이걸 하나의 표준 topic 체계로 통일한다 (sectionMappings.json)
- 결과: **어떤 회사든 같은 섹션명으로 수평 비교 가능**

이것이 완성되면 DartLab은 **한국 시장 사업보고서의 완전한 구조화 맵**을 보유하게 된다.
숫자(finance) + 텍스트(sections) + 실시간(report) — 세 축이 모두 같은 시간 축 위에 정렬되어,
한 회사의 모든 정보를 하나의 수평 비교 가능한 덩어리로 제공한다.

이건 단순히 "섹션 이름 통일"이 아니다.
사업보고서라는 정해진 프레임 위에서, 모든 회사의 모든 기간을 겹칠 수 있게 만드는 것이다.
사용자는 세로로 읽으면 그 연도의 전체 보고서를, 가로로 읽으면 같은 정보의 시간 변화를 본다.

---

## 1. 현황

### 완료
- sections 파이프라인: 270종목 0에러, 3,567개 기간 처리
- DataFrame 구조화: topic(행) × period(열) = 텍스트
- 사업보고서 원본 순서 보존 (majorNum + 등장순서)

### 문제점
1. **leaf title 미통일**: "회사의 법적ㆍ상업적 명칭" vs "회사의 법적, 상업적 명칭" → 별도 행
2. **table_only 누락**: 테이블 90%+ 섹션이 sections DataFrame에서 빠짐
3. **FINANCE_ENGINE_COVERED skip**: III장 재무 섹션의 텍스트 서술 부분이 사라짐
4. **소분류 표기 차이**: "(제조서비스업)사업의 개요" vs "사업의 개요" — 업종 접두사
5. **연도별 구조 변화**: 1999~2025년 사이 사업보고서 양식이 여러 번 개정됨

---

## 2. 설계

### 2-1. 데이터 구조

**parquet 원본 컬럼:**
```
section_order (int)     — 섹션 순서
section_title (str)     — "I. 회사의 개요", "1. 회사의 연혁" 등
section_content (str)   — HTML 제거된 텍스트 + 마크다운 테이블
```

**대분류 (12장) — 전 종목 동일 (DART 규정):**
```
I.    회사의 개요
II.   사업의 내용
III.  재무에 관한 사항
IV.   이사의 경영진단 및 분석의견
V.    회계감사인의 감사의견 등
VI.   이사회 등 회사의 기관에 관한 사항
VII.  주주에 관한 사항
VIII. 임원 및 직원 등에 관한 사항
IX.   계열회사 등에 관한 사항
X.    대주주 등과의 거래내용
XI.   그 밖에 투자자 보호를 위하여 필요한 사항
XII.  상세표 (부속명세서)
```

**소분류 — 회사마다 다름, 표준화 필요:**
- I장: 5종, 90%+ 커버
- II장: 25종 (업종 접두사 변형 포함), 핵심 7개가 77~92%
- III장: 10종, 핵심 8개가 68~93%
- V장: 2종이 90%+, 나머지 noise
- VI장: 3종이 90%+
- VIII장: 2종이 89~91%
- XI장: 4종이 39~90%
- XII장: 79종 (회사별 고유 상세표), 핵심 3개가 91%+

**총 고유 소분류: 176종 (270종목 최신 사업보고서 기준)**

### 2-2. 매핑 파이프라인

finance의 accountMappings.json과 동일한 패턴:

```
원본 section_title
  ↓ 대분류(로마숫자) 파싱 → chapter 결정
  ↓ 소분류(숫자) 파싱 → subNum 결정
  ↓ 접두사 제거: "(제조서비스업)", "(금융업)" 등
  ↓ 공백/특수문자 정규화: "ㆍ" → ",", 연속공백 제거
  ↓ sectionMappings.json 조회 → 표준 topicId
  ↓ 미매핑 → 원본 유지 (but 로깅)
```

**sectionMappings.json 구조:**
```json
{
  "회사의 법적ㆍ상업적 명칭": "companyLegalName",
  "회사의 법적, 상업적 명칭": "companyLegalName",
  "(제조서비스업)사업의 개요": "businessOverview",
  "사업의 개요": "businessOverview",
  ...
}
```

topicId는 camelCase 영문 (snakeId와 같은 패턴).
label은 별도 dict: `{"companyLegalName": "회사의 법적·상업적 명칭", ...}`

### 2-3. 학습 사이클 (finance와 동일)

```
1. 전종목 스캔 → 미매핑 section_title 수집
2. 빈도 분석 → 같은 의미인 변형 그룹핑
3. 자동 규칙 적용 (공백 정규화, 접두사 제거, SequenceMatcher)
4. 수동 검토 → sectionMappings.json 업데이트
5. 매핑률 측정 → 반복
```

목표: **매핑률 95%+ (finance의 97%와 유사한 수준)**

### 2-4. Company 프레임 (registry 연동)

registry.py의 DataEntry에 `chapter` 필드 추가:

```python
@dataclass(frozen=True)
class DataEntry:
    ...
    chapter: int = 0       # 사업보고서 장 번호 (I=1, II=2, ..., XII=12)
    chapterSub: int = 0    # 장 내 소분류 순서
```

매핑 예시:
| 모듈 | chapter | chapterSub |
|------|---------|------------|
| companyOverview | 1 | 1 |
| companyHistory | 1 | 2 |
| shareCapital | 1 | 4 |
| business | 2 | 1 |
| productService | 2 | 2 |
| IS/BS/CF | 3 | 2~5 |
| dividend | 3 | 6 |
| mdna | 4 | 0 |
| audit | 5 | 1 |
| boardOfDirectors | 6 | 1 |
| majorHolder | 7 | 0 |
| employee | 8 | 1 |
| executivePay | 8 | 2 |
| affiliateGroup | 9 | 0 |
| contingentLiability | 11 | 1 |
| sanction | 11 | 3 |

KRCompany.all()이 chapter → chapterSub 순서로 정렬:
```
I장: companyOverview → companyHistory → shareCapital → ...
II장: business → productService → salesOrder → rnd → ...
III장: IS → BS → CF → fsSummary → dividend → bond → ...
IV장: mdna
V장: audit → internalControl
...
```

### 2-5. sections DataFrame의 위치

sections DataFrame은 **전체 사업보고서 텍스트의 수평 비교 뷰**다.
정량 모듈(IS, dividend 등)이 "숫자를 뽑는 도구"라면,
sections는 "텍스트를 정렬하는 도구"다.

둘은 겹치지 않는다:
- 정량 모듈이 커버하는 섹션 → sections에서 "(finance/report 엔진이 정량 처리)" 표시
- 나머지 텍스트 → sections가 담당

향후: table_only 섹션도 메타데이터(테이블 헤더, 행수)를 sections에 포함할지 검토

---

## 3. 실험 계획

### 실험 001: 전종목 section_title 빈도표
- 270종목 × 전 기간 parquet에서 section_title 전수 추출
- (chapter, subNum, title) 빈도표 → 표준 후보 식별
- 연도별 양식 변화 추적 (1999→2015→2025)

### 실험 002: 자동 정규화 규칙 테스트
- 공백/특수문자 정규화
- 업종 접두사 제거: "(제조서비스업)", "(금융업)", "(보험업)" 등
- SequenceMatcher로 유사도 0.85+ 자동 그룹핑
- 자동 매핑률 측정

### 실험 003: sectionMappings.json 초안 생성
- 001/002 결과를 기반으로 매핑 테이블 자동 생성
- topicId + label 체계 확정
- 매핑률 목표: 95%+

### 실험 004: sections DataFrame 매핑 적용
- pipeline.py에서 sectionMappings.json 사용하여 leaf title 통일
- 적용 전/후 수평 매칭률 비교 (삼성전자: 현재 329행 → 목표 200행 이하)
- 전종목 재테스트

### 실험 005: registry chapter 매핑
- 각 DataEntry에 chapter/chapterSub 할당
- KRCompany.all() 정렬 검증
- guide() 출력이 사업보고서 순서와 일치하는지 확인

### 실험 006: 커버리지 측정
- 원본 section_content 총 글자수 vs sections DataFrame이 담은 글자수
- skip된 영역 + table_only 영역의 비율
- 정량 모듈과의 중복/누락 분석

---

## 4. 파일 구조

```
experiments/056_sectionMap/
├── STATUS.md                    ← 이 파일
├── 001_titleFrequency.py        ← 전종목 section_title 빈도표
├── 002_autoNormalize.py         ← 자동 정규화 규칙
├── 003_buildMappings.py         ← sectionMappings.json 생성
├── 004_applyMappings.py         ← DataFrame 적용 테스트
├── 005_registryChapter.py       ← registry chapter 매핑
└── 006_coverageMeasure.py       ← 커버리지 측정
```

**프로덕션 배치 대상:**
```
src/dartlab/engines/dart/docs/sections/
├── mapper.py          ← NEW: sectionMappings.json 기반 매핑
├── mapperData/
│   └── sectionMappings.json  ← NEW: 표준 topic 매핑 데이터
├── pipeline.py        ← 수정: mapper 적용
├── chunker.py         ← 수정: table_only/skip 전략 재검토
└── types.py           ← 유지

src/dartlab/core/
├── registry.py        ← 수정: DataEntry에 chapter 필드 추가
└── ...

src/dartlab/company.py ← 수정: all() 정렬 순서를 chapter 기반으로
```

---

## 5. 성공 기준

| 지표 | 현재 | 목표 |
|------|------|------|
| leaf title 매핑률 | 측정 안됨 | 95%+ |
| 삼성전자 topic 행 수 | 329 | ~200 (중복 통합) |
| 전종목 처리 에러 | 0 | 0 유지 |
| 사업보고서 원본 커버리지 | 측정 안됨 | 90%+ (텍스트 기준) |
| Company.all() 순서 | 모듈순 | 사업보고서 장순 |

---

## 6. 의존성

- finance 매핑 경험 (accountMappings.json, synonymLearner 패턴)
- parquet 원본 데이터 270종목
- sections 파이프라인 (완성됨)
- registry 구조 (수정 예정)

---

## 7. 실행 결과 (2026-03-11)

### 001_titleFrequency.py 완료

- 실행 파일: `experiments/056_sectionMap/001_titleFrequency.py`
- 스캔 파일 수: 270
- 총 `section_title` 행 수: 160,853
- 고유 `section_title` 수: 494
- Top10 소분류 커버리지: 23.20% (37,321 / 160,853)

핵심 관찰:
- 대분류 파싱 결과 `UNKNOWN` 비중이 큼(116,604행). 이는 로마숫자 장 제목이 아닌 하위목차(`1.`, `2.`...) 행이 다수 포함되기 때문.
- 소분류 상위 빈도는 재무/임원/주주/연혁 계열 항목에 집중.
- 다음 단계(002_autoNormalize)는 UNKNOWN 군집 정규화(접두사 제거/특수문자 통일/유사도 그룹핑)에 집중 필요.
