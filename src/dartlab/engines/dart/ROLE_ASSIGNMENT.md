# Company 데이터 소스 역할 배정

## 원칙

1. **finance가 최강** — XBRL 정규화, snakeId 통일, 회사간 비교 가능
2. **report가 차강** — DART API 정형 데이터, 22개 apiType
3. **docs는 보완** — finance/report가 못 하는 것만 (장기 히스토리, 서술형, 주석 상세)

## 역할 배정표

### A. 재무제표 → finance (변경)

현재 `c.BS/IS/CF`는 docs의 `statements` 모듈 사용.
docs IS는 실제로 **CIS(포괄손익계산서)를 반환** — 매출액/영업이익 없음.

| property | 현재 소스 | 변경 소스 | 이유 |
|----------|----------|----------|------|
| `c.BS` | docs statements | **finance buildAnnual** | snakeId 정규화, 회사간 비교 |
| `c.IS` | docs statements (CIS!) | **finance buildAnnual** | docs는 CIS 반환, 매출/영업이익 없음 |
| `c.CF` | docs statements | **finance buildAnnual** | snakeId 정규화 |

구현: finance annual series의 BS/IS/CF를 DataFrame으로 변환 (snakeId → 한글명, 연도별 컬럼)

### B. 정기보고서 데이터 → report 우선 (변경)

현재 `c.dividend`, `c.employee` 등은 docs 파싱 사용.
report 엔진이 5개 pivot만 있고, Company 레벨에서는 `c.report.*`로만 접근 가능.

| property | 현재 소스 | 변경 소스 | 이유 |
|----------|----------|----------|------|
| `c.dividend` | docs dividend | **report pivotDividend** | API 정형 > HTML 파싱 |
| `c.employee` | docs employee | **report pivotEmployee** | API 정형 > HTML 파싱 |
| `c.majorHolder` | docs majorHolder | **report pivotMajorHolder** | API 정형 > HTML 파싱 |
| `c.executive` | docs executive | **report pivotExecutive** | API 정형 > HTML 파싱 |
| `c.audit` | docs audit | **report pivotAudit** | API 정형 > HTML 파싱 |

fallback: report 없으면 docs로 fallback (`self._hasReport` 체크)

### C. report 신규 등록 (17개 추가)

현재 pivot 없는 17개 apiType도 `extractAnnual`로 DataFrame 제공.
Company에서 바로 접근 가능하게.

| property | apiType | 설명 |
|----------|---------|------|
| `c.report.majorHolderChange` | majorHolderChange | 최대주주 변동 이력 |
| `c.report.minorityHolder` | minorityHolder | 소액주주 현황 |
| `c.report.outsideDirector` | outsideDirector | 사외이사 현황 |
| `c.report.stockTotal` | stockTotal | 주식 총수 현황 |
| `c.report.executivePayAllTotal` | executivePayAllTotal | 임원보수 전체 |
| `c.report.executivePayIndividual` | executivePayIndividual | 임원보수 개인별 |
| `c.report.topPay` | topPay | 5억+ 개인별 보수 |
| `c.report.unregisteredExecutivePay` | unregisteredExecutivePay | 미등기임원 보수 |
| `c.report.capitalChange` | capitalChange | 증자/감자 현황 |
| `c.report.treasuryStock` | treasuryStock | 자기주식 현황 |
| `c.report.publicOfferingUsage` | publicOfferingUsage | 공모자금 사용 |
| `c.report.privateOfferingUsage` | privateOfferingUsage | 사모자금 사용 |
| `c.report.investedCompany` | investedCompany | 타법인 출자 |
| `c.report.corporateBond` | corporateBond | 회사채 미상환 |
| `c.report.shortTermBond` | shortTermBond | 단기사채 미상환 |
| `c.report.auditContract` | auditContract | 감사용역 체결 |
| `c.report.nonAuditContract` | nonAuditContract | 비감사용역 계약 |

구현: `_ReportAccessor`에 `__getattr__` 추가 → 미리 정의 안 된 apiType은 `extractAnnual` 자동 호출

### D. docs 고유 (변경 없음)

finance/report로 대체 불가능한 docs 고유 데이터:

#### D-1. 서술형 (disclosure)
| property | 모듈 | 설명 |
|----------|------|------|
| `c.business` | business | 사업의 내용 텍스트 |
| `c.overview` | companyOverview | 회사 정량 개요 |
| `c.mdna` | mdna | MD&A 서술 |
| `c.rawMaterial` | rawMaterial | 원재료/설비/시설투자 |

#### D-2. K-IFRS 주석
| property | 모듈 | 설명 |
|----------|------|------|
| `c.notes.receivables` | notesDetail | 매출채권 주석 |
| `c.notes.inventory` | notesDetail | 재고자산 주석 |
| `c.notes.tangibleAsset` | tangibleAsset | 유형자산 변동표 |
| `c.notes.intangibleAsset` | notesDetail | 무형자산 주석 |
| `c.notes.investmentProperty` | notesDetail | 투자부동산 주석 |
| `c.notes.affiliates` | affiliate | 관계기업 주석 |
| `c.notes.borrowings` | notesDetail | 차입금 주석 |
| `c.notes.provisions` | notesDetail | 충당부채 주석 |
| `c.notes.eps` | notesDetail | 주당이익 주석 |
| `c.notes.lease` | notesDetail | 리스 주석 |
| `c.notes.segments` | segment | 부문정보 주석 |
| `c.notes.costByNature` | costByNature | 비용성격별분류 주석 |

#### D-3. 복합 구조 (HTML에서만 추출 가능)
| property | 모듈 | 설명 |
|----------|------|------|
| `c.holderOverview` | majorHolder | 5%+ 주주 + 소액주주 + 의결권 |
| `c.contingentLiability` | contingentLiability | 채무보증 + 소송 |
| `c.relatedPartyTx` | relatedPartyTx | 관계자 매출/매입/보증 |
| `c.riskDerivative` | riskDerivative | 환/금리 리스크 + 파생상품 |
| `c.segments` | segment | 부문별 매출 시계열 |
| `c.costByNature` (신규) | costByNature | 비용 성격별 분류 시계열 |
| `c.tangibleAsset` (신규) | tangibleAsset | 유형자산 변동표 |

#### D-4. 기타 docs 고유
| property | 모듈 | 설명 |
|----------|------|------|
| `c.subsidiary` | subsidiary | 종속회사 투자 (report investedCompany와 범위 다름) |
| `c.bond` | bond | 채무증권 (report corporateBond보다 상세) |
| `c.shareCapital` | shareCapital | 주식 현황 (report stockTotal보다 상세) |
| `c.capitalChange` | capitalChange | 자본금 변동 (report capitalChange보다 상세) |
| `c.boardOfDirectors` | boardOfDirectors | 이사회 구성/활동 |
| `c.internalControl` | internalControl | 내부회계관리 |
| `c.auditSystem` | auditSystem | 감사위원회 |
| `c.affiliateGroup` | affiliateGroup | 계열회사 현황 |
| `c.affiliate` | affiliate | 관계기업 투자 변동 |
| `c.investmentInOther` | investmentInOther | 타법인 출자 |
| `c.fundraising` | fundraising | 증자/감자 이력 |
| `c.productService` | productService | 주요 제품/서비스 |
| `c.salesOrder` | salesOrder | 매출/수주 |
| `c.rnd` | rnd | R&D 비용 |
| `c.sanction` | sanction | 제재 현황 |
| `c.articlesOfIncorporation` | articlesOfIncorporation | 정관 |
| `c.otherFinance` | otherFinance | 대손충당금/재고 |
| `c.companyHistory` | companyHistory | 회사 연혁 |
| `c.shareholderMeeting` | shareholderMeeting | 주주총회 |
| `c.companyOverviewDetail` | companyOverviewDetail | 설립일/상장일/대표이사 등 |

### E. finance 전용 (변경 없음)

| property | 함수 | 설명 |
|----------|------|------|
| `c.timeseries` | buildTimeseries("CFS") | 분기별 standalone |
| `c.annual` | buildAnnual("CFS") | 연도별 |
| `c.cumulative` | buildCumulative("CFS") | 분기별 누적 |
| `c.sceMatrix` | buildSceMatrix("CFS") | SCE 매트릭스 |
| `c.sce` | buildSceAnnual("CFS") | SCE 시계열 |
| `c.ratios` | calcRatios | 재무비율 (TTM) |
| `c.ratioSeries` | calcRatioSeries | 비율 연도별 시계열 |
| `c.getTimeseries(period, fsDivPref)` | 유연 접근 | |
| `c.getRatios(fsDivPref)` | 유연 접근 | |

### F. L2 분석 (변경 없음)

| property | 엔진 | 설명 |
|----------|------|------|
| `c.sector` | sector | WICS 섹터 분류 |
| `c.sectorParams` | sector | 섹터별 파라미터 |
| `c.rank` | rank | 시장/섹터 순위 |
| `c.insights` | insight | 7영역 등급 분석 |

## 구현 계획

### 1단계: c.BS/IS/CF를 finance로 변경
- `_financeToDataFrame(series, years, sjDiv)` 헬퍼 작성
- snakeId → 한글명 변환 (AccountMapper.labelMap())
- 연도별 컬럼 구조 유지 (기존 docs 출력과 호환)
- finance 없으면 docs fallback

### 2단계: c.dividend 등 5개를 report 우선으로 변경
- report pivot 결과에서 primary DataFrame 추출
- report 없으면 docs fallback
- _ReportAccessor의 기존 5개 pivot은 그대로 유지

### 3단계: _ReportAccessor에 22개 apiType 자동 접근 추가
- `__getattr__`로 미등록 apiType은 extractAnnual 자동 호출
- 기존 5개 pivot property는 우선

### 4단계: docs 고유 모듈 누락 property 추가
- `c.tangibleAsset` (신규)
- `c.costByNature` (신규)
- `c.fsSummary()` 메서드는 유지 (파라미터 있음)

### 5단계: registry 업데이트
- BS/IS/CF의 category를 "report" → "finance"로 변경
- requires를 "docs" → "finance"로 변경
- docs fallback 정보 추가
