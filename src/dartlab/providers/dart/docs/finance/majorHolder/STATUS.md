# finance/majorHolder — 주주 현황 분석

## 기능
사업보고서 "주주에 관한 사항" 섹션에서 주주 데이터 추출.

### 1. majorHolder — 최대주주 + 특수관계인 시계열
### 2. holderOverview — 5% 이상 주주 + 소액주주 + 의결권 현황

## API
```python
from dartlab.finance.majorHolder import majorHolder, holderOverview

result = majorHolder("005930")        # -> MajorHolderResult | None
overview = holderOverview("005930")    # -> HolderOverview | None
```

## MajorHolderResult
| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 시계열 기간 수 |
| majorHolder | str \| None | 최대주주명 (최신) |
| majorRatio | float \| None | 최대주주 보통주 지분율 |
| totalRatio | float \| None | 특수관계인 포함 전체 지분율 |
| holders | list[Holder] | 최신 연도 특수관계인 목록 |
| timeSeries | pl.DataFrame | 연도별 최대주주/지분율 추이 |

## HolderOverview
| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| year | int \| None | 기준 사업연도 |
| bigHolders | list[BigHolder] | 5% 이상 주주 목록 |
| minority | Minority \| None | 소액주주 현황 |
| voting | VotingRights \| None | 의결권 현황 |

### BigHolder
| 필드 | 설명 |
|------|------|
| name | 주주명 |
| shares | 소유주식수 |
| ratio | 지분율 (%) |

### Minority
| 필드 | 설명 |
|------|------|
| holders | 소액주주 수 |
| totalHolders | 전체 주주 수 |
| holderPct | 소액주주 비율 (%) |
| shares | 소액주주 보유 주식수 |
| totalShares | 총 발행주식수 |
| sharePct | 소액주주 주식 비율 (%) |

### VotingRights
| 필드 | 설명 |
|------|------|
| issuedCommon/Pref | 발행주식총수 (보통주/우선주) |
| noVoteCommon/Pref | 의결권 없는 주식수 |
| excludedCommon/Pref | 정관에 의한 배제 |
| restrictedCommon/Pref | 법률에 의한 제한 |
| restoredCommon/Pref | 의결권 부활 |
| votableCommon/Pref | 의결권 행사 가능 주식수 |

## 파싱 성공률 (267종목)
| 항목 | 성공 | 실패 | 미해당 | 성공률 |
|------|------|------|--------|--------|
| 최대주주(majorHolder) | 227 | 0 | 40 | 100% |
| 5% 이상 주주 | 217 | 0 | 50 | 100% |
| 소액주주 | 214 | 0 | 53 | 100% |
| 의결권 | 223 | 0 | 44 | 100% |

## 파싱 전략

### majorHolder
1. "VII. 주주에 관한 사항"에서 "성 명 | 관 계" 헤더 탐지
2. 8-cell 데이터행에서 이름, 관계, 주식종류, 기초/기말 주식수/지분율 추출
3. "본인" 또는 "최대주주" 관계를 최대주주로 식별

### 5% 이상 주주
1. "5% 이상 주주" 키워드로 섹션 탐지
2. `| 5% 이상 주주 | 주주명 | 소유주식수 | 지분율 | 비고 |` 구조 파싱
3. 이후 행은 `| 주주명 | 주식수 | 지분율 |`

### 소액주주
1. "소액주주" 키워드로 섹션 탐지
2. `| 소액주주 | 주주수 | 전체주주수 | 비율 | 소액주식수 | 총발행주식수 | 비율 |` 단일행

### 의결권
1. "의결권 현황" 키워드로 섹션 탐지 (주주총회 섹션)
2. `| 구분 | 주식의 종류 | 주식수 | 비고 |` 구조
3. A(발행주식총수) ~ F(행사가능) 항목별 보통주/우선주 분리 추출

## 주의사항
- 2015년 이전 보고서는 테이블 구조 차이로 지분율 오류 가능
- "의결권있는 주식" (띄어쓰기 없음) 포맷도 처리
- 스팩/비상장사는 5% 이상 주주/소액주주가 없을 수 있음

## 실험
- experiments/007_majorHolder/ (001~004) — 최대주주 파서 개발
- experiments/012_majorHolderDeep/ (001~005) — 5%주주/소액주주/의결권 추가
