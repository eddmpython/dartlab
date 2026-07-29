# scan 데이터 커버리지 감사: providers·gather·panel 사업보고서 탈탈털기 판정

> 방법: 사실 기반 3 조사(providers/gather 표면·scan 소비·panel 섹션 대조) + 전문 4관점 토론(전수원칙 집행관·도메인전문가·악마의변호인·통합PM). 2026-07-07. 파일:라인 그라운딩.
> 트리거: 운영자 "전문에이전트들과 토론해서 scan이 정말 providers·gather·특히 panel 사업보고서 전 섹션을 탈탈 털어쓰는지 확인해라."

## 판정 (한 줄)

**아니다. "털 수 있는데 안 트는" 상태다.** 손-큐레이션 게이트 2개가 거의 공짜인 정형표 ~11개(임원보수·자본증권·주주 = 거버넌스·희석·부실 알파)를 자르고, 매트릭스 노트(특수관계자·영업부문)와 정성 서술이 빠져 있다. 추출 카탈로그 88개념(DART 80) 중 scan 스크리닝 노출은 약 53(실효 ~51). 단, "88 전부를 scan 축으로"가 목표가 아니라 "수치화 가능은 자동 전수, 정성은 제 집(docs/frame)으로"가 정답이다.

## 정량 사실 (3 조사 확정)

- 추출 카탈로그 = **88 개념**(DART-side 80, US-only 8). 9 카테고리: financialStatement 6·note 35·governance 8·capital 4·workforce 7·debt 6·segment 2·narrative 10·filingMeta 2. (`core/extractionCatalog/`)
- scan 노출 ≈ **53**: note 29 + 재무5표 6 + report 17 apiType + segment(salesByProduct). 실효 ~51(매트릭스 탈락).
- **손 게이트 3겹**: ① note `registered=True AND valueType∈(amount,rate)`(notes.py:89) → 35→29 ② report `SCAN_API_TYPES` 17/28 하드리스트(build.py:59) ③ panel `readNoteStatements` `~axisPath.contains("|")` depth-1 단일축만(cell.py:789) → 매트릭스 노트 셀0.
- **자기기만 신호**: notes.py:74 주석은 "카탈로그 SSOT 라 손 선별 0"이라 자칭하나 :89 술어가 text를 배제. SSOT 도출과 손 필터 부재는 별개 (술어 자체가 큐레이션). [[feedback_exhaustive_no_curation]] "등재 게이트가 아니라 사후 태그로 도태" 위반.
- **오태깅**: `salesOrder`·`rawMaterial`은 valueType=amount인데 category=narrative라 note 필터가 닿지 못함. contingencies·shareBasedComp도 구조적 수치인데 text 태깅.
- gather 측: macro 55지표 중 scan은 macroBeta로 ECOS 3개만. narrative/research/naverTheme/naverEtf/flow(외국인기관)/ownership 등 gather 축 다수 scan 미소비.

## 토론 합의 (수렴)

1. scan 은 사업보고서를 탈탈 털지 **못한다** (4관점 중 3 명시 NO, 도메인전문가 8갭으로 암묵 동의).
2. **report 17→28 de-gate** = 최고 ROI·거의 공짜(파서 이미 존재, buildReport 제네릭 분할)·최저위험. 악마의변호인도 임원보수·자본증권·주주는 "노출해야 할 진짜 갭"으로 인정.
3. **narrative 10(순수 산문)은 scan 축으로 만들면 안 됨** = 카테고리 오류. docs/search + frame/narrative 가 제 집. 전수원칙 집행관도 "억지 수치화 말고 text-verb(존재/전년diff)"라 동의.
4. **매트릭스 노트는 depth-1 필터 우회 금지** (pivot `first`가 조용히 데이터 드롭, 전 노트 개념 파괴). 전용 붕괴 추출기(salesByProduct 선례)로. 영업부문은 이미 salesByProduct 커버.
5. **도태는 census 성적표로** (빈 파일 = 정직 gap), 등재 게이트로가 아니라.

## 토론 발산 (긴장)

- 전수원칙 집행관: text 개념도 text-verb 축으로 전부 자동 등재.
- 악마의변호인: 진짜 scan 갭은 ~4개(기존 축 수치 확장), 나머지는 "scan 미노출 ≠ 갭"(제 집 있음). 80/80 목표는 [[feedback_plan_score_not_signature]] 함정.
- 통합PM: 중재 = 수치는 de-gate 자동, text는 flag 1열, 산문은 docs, 도태는 census.

## 처방: 27갭 3버킷 (통합PM 종합)

- **A. scan 수치 축 자동 등재 (~14)**: 임원보수 4·자본증권 3·주주 2(→ report de-gate) + salesOrder·productionCapacity·rawMaterial 3(정성-수치 prebuild) + 매트릭스 2(relatedParty 내부거래율 전용축·segments salesByProduct 확장).
- **B. 플래그/존재여부만 (~4)**: 자금사용 2(목적외 전용 편차)·우발부채·후속사건(존재 bool + 가능손실 금액). `define` where 에서 boolean 소비.
- **C. docs/search 라우팅 (~11)**: narrative 자유텍스트 7(businessOverview·riskFactors·mdna·rnd·majorContracts·governanceText·environment) + 정책산문(financialRiskMgmt·accountingPolicies·criticalEstimates). `crossSection=false` 태그 + frame/narrative(이미 존재) 노출, scan 축 신설 0.

## 정공법 로드맵

- **P1 (최우선·최저위험·신설 파서 0): 게이트 de-gate.** SCAN_API_TYPES 카탈로그 도출(17→28) + note `registered` 필터 제거·오태깅 valueType 교정. 노출 53→~64. 영향: `scan/builders/kr/report/build.py`·`notes.py`·`io/parquet.py`(`_REQUIRED_REPORT_FILES`는 HF 다운로드 완전성 가드로 유지, BUILD만 전수) + `tests/scan/test_prebuild_contract.py`·census baseline.
- **P2**: 매트릭스 2 전용 붕괴 추출기(salesByProduct 일반화) + 정성-수치 3 횡단 prebuild(frame/narrative 재사용).
- **P3**: 텍스트 존재 플래그(자금사용·우발부채) source="flag" 1열.
- **P4**: narrative 산문 `crossSection=false` 태그 + docs/search 라우팅 확정.

## 핵심 파일

`core/extractionCatalog/` · `scan/builders/kr/notes.py:89` · `scan/builders/kr/report/build.py:59` · `providers/dart/report/types.py:10` · `providers/dart/panel/cell.py:789` · `scan/io/parquet.py:107`(다운로드 가드, 노출 게이트 아님) · `frame/narrative.py`·`frame/inventory.py`(회사별 전수 열거, round-trip 100%) · `scan/salesByProduct.py`(매트릭스 신호 선례) · `tests/audit/extractionCoverageCensus.py`(성적표).

## 남은 결정 (운영자)

P1 은 합의·저위험·운영자 원칙(exhaustive) 직접 이행이라 즉시 착수 후보. P2~P4 는 버킷 경계(특히 A/C 사이 salesOrder 류가 scan 수치냐 docs 냐)에 도메인 판단 여지 있음. narrative 를 scan 에 넣지 않는다는 4관점 합의는 확정.

## P1 구현 완료 (2026-07-07, commit 547d7c780)

손 게이트 3겹을 카탈로그 자동 도출로 전환 + 신규 7 apiType 실소비자 배선:
- `SCAN_API_TYPES` = 카탈로그 report-surface 도출(28) - 실측 무데이터 4 = **24** (`_reportApiTypes()`). `_REQUIRED_REPORT_FILES` 빌더 파생 자동동기화. note `registered` 게이트 제거(shareBasedComp 자동편입, 30).
- 신규 축 배선: debt(채무증권), workforce(최고개인보수·미등기보수), governance(최대주주변동), capital(발행주식총수·자기주식·조달금액·목적외사용).
- **측정에 의한 도태**: 무데이터 4(hybridSecurities·contingentCapital·executivePayByType·executivePayTotal)는 전종목 실측 payload 0 → 제외(손 추측 아님).
- `latestDataRows` 헬퍼: 이벤트-데이터(공모자금·5억보수) status-only 최신연도 오탐 차단.
- 실측: 채무증권 1335·발행주식 2900·조달 905(목적외 416)·최고보수 1374·미등기 2682. scan 유닛 291+계약 pass·dartlabGuard strict PASS.

## P2 실측 판정 (2026-07-07): 매트릭스·narrative 는 안전한 cross-section 수치화 불가

버킷 A/C 의 매트릭스·정성 항목을 실 데이터로 그라운딩한 결과, **셋 다 scan 수치 축으로 안전 구현 불가하거나 이미 커버**임이 확인됐다. 억지 구현은 조용한 오답 또는 덕지덕지라 정공법상 미착수.

- **relatedParty(특수관계자, NT_D818000)**: 실 panel 셀 검사 결과 `acode=null` · `axisPath=ConsolidatedMember`(degenerate, 거래유형 축 없음) · label 일반적("기타"·"관계기업계"). segments(OperatingSegmentsMember 축 보유)와 달리 관계사매출/매입/채권을 신뢰 있게 유형화할 구조가 **원천 부재**. DART 는 구조화 특수관계자 endpoint 도 없음. 내부거래율 강제 산출 = 조용한 오답(악마의변호인 경고 확증). → 단일종목 포렌식(company/frame)이 정답.
- **narrative-numeric(수주잔고·가동률)**: `frame/narrative.extractNarrative` 는 raw 서술 블록/표를 반환(넘버 아님). 표 leaf 는 period-wide 이나 회사별 포맷 상이 → cross-company 단일 수치 추출은 fragile NLP(조용한 오답 위험). → 단일종목 read(frame/narrative, 이미 존재)가 정답.
- **segments(영업부문, NT_D871100)**: 구조화 축 보유(추출 가능)하나 **salesByProduct 축이 이미** 사업 집중도(nSegments·topSharePct·hhi·grade)를 노출 → 재구현 시 중복(덕지덕지).

결론: **P1 이 사업보고서의 안전 추출 가능 구조화 표를 전부 흡수**했고, 잔여 매트릭스·정성은 데이터 구조상 cross-section 스크리닝 부적합(단일종목 read=frame/narrative·company, 이미 존재). scan 축 신설 0 이 정공법. narrative 정량화가 꼭 필요하면 별도 회사별-표 파서 프로젝트(고위험, 조용한 오답 관리 필요)로 격리 승격해야 함(운영자 결정).

## 실측 재검증 (2026-07-08): note 축 깜깜 발견 -> 수리 -> HF 발행

트리거: 운영자 "다시 panel 파케를 탈탈 털어서 진짜 scan 이 제대로 섰나." 로컬 데이터 실측(panel 2930 + scan parquet 전수)으로 개념단위 census 재실행.

- **개념 census(88)**: LIVE 33 / DARK 30 / PANEL-ONLY(text) 14 / GAP(정직) 4 / N/A(US) 7. 구멍은 딱 하나 = **note 금액개념 30 이 전 유니버스 DARK**. 배선(builder·reader·router·catalog)은 완비인데 `scan/note/*.parquet` 이 로컬 부재 + HF 404.
- **근본원인 2겹**: ① note prebuild 는 buildScan full 모드 전용인데 full 은 11GB panel seed 조건부 + `buildNotesSafe` 가 실패를 조용히 흡수 -> 성공적 발행 사이클 미통과. ② `releaseNativeMemory` 가 posix 전용(malloc_trim), Windows 로컬 buildNotes 는 gc 뿐이라 힙 누적(1700->2490MB) 크래시 위험.
- **정공법 수리**: 300종목/샤드 fresh 프로세스로 Rust 힙 리셋하는 샤드 빌드(scratchpad, 파싱=readNoteStatements SSOT 위임 무재구현). FATAL 0 으로 30개념 전부 생성. tax 2382·relatedParty 2299·eps 2293·tangibleAsset 2226·intangibleAsset 2207 등(희소노트는 정직하게 적게: restrictedFinancial 706·shareBasedComp 878).
- **품질**: inventory 지배 account = 제품/원재료/상품/합계(정확). 통화코드 오염 0.08%(115/138719). 노트 경계 over-capture 는 기존 readNoteStatements SSOT 특성(account 명으로 분리, 제품 스크리닝 무오염). 절대금액 cross-company 순위는 단위/라벨 이질로 이 축 용도 아님(리더 가이드 명시: finance scan 이 SSOT, 후보는 Company.panel 검증).
- **end-to-end**: `scan("note","재고자산")` = 138,719행 종목명 조인. census 재실행 LIVE **33->63**, DARK **30->0**.
- **HF 발행**: `dart/scan/note/` 30개 parquet 40MB upload_folder(additive). 원격 존재 확인. 공개 scan("note") 전 유니버스 작동.
- **note 다년성**: 종목당 평균 8~11년 시계열 보유(inventory 11.0·relatedParty 10.6·receivables 10.4). note 추세 파생 축(재고 구조추세·특수관계자 급증·판관비 변화) 데이터상 feasible = 다음 강화 후보.

## 전문에이전트 3관점 토론 + 강화 (2026-07-08~09)

트리거: 운영자 "전문에이전트들과 토론해서 정말 강한지·gather 까지 탈탈 털었는지·더 강력한 scan 이 되려면 어떻게 할지 토론해서 강하게 밀어라." 3 에이전트 병렬(gather 감사·세계수준 비평·적대 검증), 코드 그라운딩.

### 토론 종합 (합의)

- **진짜 선 것**: finance·changes·report(24) = 넓고 신선(2929~2942종목). live 축(orders·ipo·earningsFlash·valuation·macroBeta)은 stub 아님, 실배선 확인.
- **과장/취약(적대)**: "전 유니버스" 는 과장. sharesOutstanding **1행(치명)**·valuation 2538/stale/PER39%결측·salesByProduct 1146·narrativeMetric 실값 633/573·note 706~2382. census 가 이 편차를 별표 없이 "LIVE" 로 셈.
- **note 파이프라인 구조취약**: full 전용 + buildNotesSafe silent-swallow + base-seed 누락 + not-required = 조용한 DARK 회귀 가능. (본 세션 수리 대상)
- **note 품질**: over-capture 가 0.08%(통화)보다 큼. 지배 account 에 합계/소계/기타 등 일반 집계라벨 혼입, tax/relatedParty 는 단위/의미 이질(경영진보수+거래잔액). reader docstring 은 정직 경고("절대금액 cross-company 금지, finance SSOT"). 리스크 = census 가 이를 clean LIVE 로 셈한 것.
- **골격 공백(3관점 공통)**: ① 시점정합 PIT(전면 부재, 모든 로더 최신기간 고정=룩어헤드) ② 가중 랭크 스코어 합성(boolean 교집합뿐) ③ 이벤트+펀더멘털 조합(축 사일로) ④ gather 수급 flow 미소비.
- **gather 사각지대 3(감사)**: (1) 투자자 수급 flow(외국인/기관/개인 순매수) 완전 미소비 = 후행 펀더멘털의 선행 짝, 데이터 완비인데 축 0. **단 저작권상 프리빌드·발행 불가 → 로컬 런타임 축으로만 노출** (2) 공시 이벤트 스트림(유상증자·자사주·합병 raw 있는데 파서 supplyContract 1종뿐) (3) 컨센서스(research)·뉴스 sentiment. (2)(3)도 재배포 저작권 확인 필요.

### 실측 정정 (에이전트 주장 반증)

강화 에이전트가 "① note temporal 은 공짜에 가까운 최대 가치"라 했으나, 실 note 시계열을 열어보니 **연도 간 scale/셀 불일치**(삼성바이오 제품재고 2022=6952억→2023=-20억→2024=6972억, 여러 종목이 특정 연도만 0). raw note 에 YoY/slope 직접 걸면 조용한 오답(missing>wrong 위반). ① 은 branch 하나가 아니라 **연도별 단위정규화 layer 가 필요한 진짜 과제**로 재판정. 따라서 안전한 최강 push 는 ②(가중 랭킹, 정규화 데이터 위)로 재조준.

### 이번 세션 구현 (강하게 밀기, commit)

- **② 가중 다팩터 랭킹** (commit 2ffd4109c, `report/fields.py`): define AST 에 리터럴 스칼라(mul/div=무차원 가중, add/sub=동일단위 오프셋; 리터럴÷필드·양변리터럴 거부로 단위대수 보호) + 단항 abs/log/clip/winsorize(유니버스 분위 절단=아웃라이어 z 지배 방어). boolean 필터 -> portfolio123 식 랭크 스크리너 승격. 실측: 산업중립 z(ROE) winsorize 가중 - z(PBR) 가중 = 종합스코어 랭킹 end-to-end(디에이피 ROE56%·PBR0.28 상위). 유닛 8 + scan 313 pass · dartlabGuard strict PASS.
- **base-seed 수리** (commit 0bf01fae8, `prebuildManifest.py`·`prebuildData.py`): SCAN_BASE_ARTIFACTS 에 note/·narrativeMetrics·salesByProduct·valuation 추가. note 조용한 DARK 회귀 근본 구멍 차단.

### 남은 로드맵 (ROI x 리스크, 운영자 결정)

**★ 수급/가격/지분 = 저작권 로컬전용 (프리빌드·HF 발행 절대 금지).** flow(외국인/기관 순매수)·price(OHLCV)·ownership 은 KRX/Naver DB권·저작권이라 HF 발행 데이터셋(CC BY 4.0)에 구울 수 없다. DART 공개데이터만 프리빌드·발행 대상. 따라서 수급을 scan 에 노출하려면 **valuation·orders 처럼 로컬 런타임 fetch 축**이어야 하며, 전종목 파케를 굽는 안은 원천 금지(가드=gather 핸들러 docstring 에 박음). "gather 탈탈"의 정답은 로컬 런타임 소비이지 발행이 아니다.

| 안 | 가치 | 데이터 | 리스크·게이트 |
|---|---|---|---|
| **flow 수급 = 로컬전용 런타임 축** (외국인/기관 순매수) | 최고(선행 팩터, 후행 보완) | gather flow 완비 | 저작권상 프리빌드·발행 금지. valuation 형 런타임 fetch 축으로만 (전종목 파케 금지). 런타임 횡단은 느려 target 소수·watchlist 한정 |
| **committed scan-output census 게이트** | 높음(DARK 가시화, 회귀 가드. 적대 #5) | 있음 | 중. `tests/audit` 신설, 유니버스 floor assert |
| **note temporal 강건화 layer** | 높음(추세 7축 해금) | 있으나 연도간 단위불일치 | 중. per-period 단위정규화 필수(실측 근거) |
| **이벤트 스트림 축**(유상증자·자사주·합병) | 높음(하드 카탈리스트) | allFilings raw 있음, 파서 1종뿐 | 중. EVENT_SCHEMAS 파서 확장 + prebuild |
| **sharesOutstanding 수리 + _ensureScanData 행수 가드** | 중(치명 1행 버그) | full seed 재빌드 | 저(코드)+데이터 재빌드 |
| **PIT as-of 축** | 최고(백테스트 전제, 룩어헤드 제거) | finance 에 rcept_dt 부재 | 높음. finance 재빌드=무승인 빌드 금지, 사전승인 게이트 |
| 백테스트/팩터수익 | 중 | PIT 선행 | simulate(L2.5) 위임(scan 신설=계층침범) |
