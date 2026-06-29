# IPO 공모 신고서 분석 — PRD (전문가 토론 + 실측 + 우수성 평가 박제)

> 출처: GitHub Discussion #70 (zias7039, 2026-06-26) "증권신고서 기반 IPO 수요예측 핵심 데이터 요약".
> 기획 방식: 실측(probe1~4) + 전문 에이전트 4인 아키텍처 토론(입장→토론→종합→적대비판→최종) + 5렌즈 우수성 평가(운영·UI/UX·엔진혁신·속도·프로덕트).
> 상태: **기획 확정·미착수**. 우수성 평가 반영 개정본(v2). 운영자 결정 5건 대기. order-flow-scan·professional-report-engine 동급 활성.
> ★이름 정정: "수요예측 요약"→**"공모 신고서 분석"**. 수요예측 *결과변수*(기관 경쟁률·의무보유확약·확정공모가 밴드내 위치)는 사후공시라 본 트랙의 6카테고리(사전 신고서)에 없음 → **카테고리7 후속트랙**으로 분리(§0.1).

---

## 0. 결론 먼저

요청자는 IPO 증권신고서(지분증권) 원문에서 **6개 카테고리**(공모개요·공모일정·밸류에이션·유통가능물량·재무3개년·리스크)를 구조화 표 + **원문근거 링크**로 보여달라 함. 우선순위: 공모일정 → 공모가/시총 → 비교기업/PER → 멀티플 → 할인율 → 유통비율 → 최근실적.

**핵심 결정: 새 top-level 엔진을 만들지 않고 검증된 3곳에 분산 배치하며, 데이터는 런타임 SSOT(allFilings content_raw) 직독을 기본·강제로 한다.** 전부 `tests/_attempts/ipo/` 인큐베이터에서 졸업 후 본진(`order-flow-scan` 동형 라이프사이클).

### 0.1 제품·시장 정의 (평가 mustFix#3 — 가치제안 공백 보강)
- **1차 타겟 × 결정 순간**: 청약 D-2~D-day의 **개인투자자**가 "이 IPO 청약에 들어갈까"를 판단하는 순간. (2차: 상장 직후 오버행 회피 판단.)
- **대안 대비 우위**: 38커뮤니케이션·증권사 리포트가 *구조적으로 못 주는* 두 가지 — ① **신고서 원문 표 1클릭 대조**(검증가능성, dartlab ref-검증 철학) ② **사람 라벨 0의 corp_cls 기계 ground-truth로 IPO 자동 포착**(운영비 0). 단순 요약표(공모가·일정·재무3개년)는 38커뮤니케이션이 이미 무료 제공 = table-stakes → 우위는 위 2개에 건다.
- **이름-내용 정합**: 본 트랙은 *사전 신고서 분석*이다. 수요예측 **결과변수**(기관 경쟁률·의무보유확약 비율·밴드내 확정공모가 = 청약 직전 최강 신호)는 정정신고서/발행조건확정/증권발행실적보고서에 나오는 **사후공시** → **카테고리7 후속트랙**으로 명시. 동일 `corp_cls=="E"` 회사의 후속 rcept(정정·발행조건확정)를 같은 런타임 직독으로 잡으면 아키텍처 재발명 0.

---

## 1. 실측 결과 (실제 DART 데이터, 2026-06-28)

| 측정 | 결과 |
|---|---|
| 증권신고서(지분증권) 분량 | 9개월 531건(전체) / 초판 88건. zip = **단일 XML**(dart4.xsd, 277KB~4.7MB) → 수집기 "largest 1개" 리스크 **없음** |
| 섹션 검출 | 진짜 IPO 1건(기도산업, 62만자·table 1014개)에서 **6개 카테고리 앵커 전부 ✓**. 밸류에이션이 유상증자보다 오히려 풍부(평가 섹션 본격적) |
| 테이블 값 추출 | dart4.xsd `<TABLE>` 라벨셀→인접값셀 매핑으로 실값 추출 성공(모집주식수 17,790,000주·청약기일 2026-07-14). 단 정관 조문 노이즈 혼입, **다중표·라벨충돌("적용 PER" 반복)에서 오추출** |
| flat regex | get_text 평문 정규식 숫자 추출 **전부 실패** → `<TABLE>` 구조인식 파싱 강제 |

### ★ 결정적 정정 1 — 토론 표본 오류를 실측이 바로잡음
토론 1차는 "초판 67건"을 IPO 모집단으로 가정했으나, **이는 `corpClass="Y"/"K"`(이미 상장된 시장) 필터 결과 = 전부 유상증자/DR**(SK하이닉스 DR·계양전기 주주배정). **진짜 신규상장 IPO는 상장 전이라 `corp_cls="E"(기타)`에 있고, `corp_cls=E`의 21건(스팩 1 + 일반 20)은 전부 `stock_code` 빈값**이었다.

→ **기계 ground-truth 확정**: `corp_cls=="E" AND stock_code==""` = 신규상장 IPO. `corp_cls∈{Y,K}`(stock_code 보유) = 유상증자/DR. **사람 라벨도, KRX 상장마스터 조인도 불필요.** 적대비판이 P0의 가장 약한 고리로 지목한 "판별 게이트 분모 미정"이 이 실측으로 해소됨. (이게 우수성 평가에서 **유일하게 "증명된 진짜 혁신"**으로 인정된 항목.)

### ★ 정정 2 — buildReportModel emitter는 이미 존재 (우수성 평가 fatal-flaw, 직접 검증 완료)
v1 PRD는 "Python `buildReportModel` emitter 미존재(TS만, P1a만 완료)"를 D3·P4 블로커로 반복 전제했으나 **거짓**. 직접 검증: `src/dartlab/story/report.py:161 buildReportModel(company, perspective, *, basePeriod)` 가 `044daf6dd "P2 buildReportModel emitter — Story→계약 ReportModel(thesis-led)"` 로 실재, `ce678311c "P2 thesis 빌더 격상"` 까지 진행. professional-report-engine은 **P2 진행 중**(P1a만 아님). v1 작성 시점이 emitter 커밋 직전이라 첫 토론의 Glob이 0건이었던 것.
→ **P4 블로커 재정의**: "emitter 부재"가 아니라 "기존 `buildReportModel`은 finance 시계열 전용(calcDFV de-gate 경로)이라, IPO는 별 데이터원·별 perspective 분기 builder가 필요". 운영자결정3(줄세우기) 전제도 이에 맞춰 변경(§5).

---

## 2. 동형 선례 (재발명 0)

- **`src/dartlab/scan/orders.py`** (신규수주 book-to-bill): allFilings `report_nm` 필터 → content_raw 직독 파싱(fetch 0) → 집계, **베이크 없음 런타임 직독**. ★단 `allFilingsCollector.loadDay`(:684)는 **캐시·컬럼 projection 0의 통짜 `read_parquet`** — orders가 "단일판매" 일별다수라 전수적재가 불가피한 케이스. IPO는 9개월 21건 극희소라 같은 패턴 무비판 차용 금지(§4 P3 성능 척추).
- **`src/dartlab/providers/dart/eventDisclosure.py`**: 수시공시 본문 파서 — `EVENT_SCHEMAS` 선언 레지스트리(라벨패턴→필드), `htmlTableParser.flattenTableCells`+`parseAmount` 위임. IPO 파서의 형제 위치. **단 KRX 폼은 "라벨 고정 채워넣기 폼"이라 선언 1엔트리로 끝나지만, 증권신고서는 자유서식이라 그대로 복사하면 실패**(D1·§4 P1/P2).
- **`core/dataConfig.py` line 55-61 `brokerageReports`**: "본문 0 — 제목·URL·발간일·종목만 public publish, 링크아웃". **퍼블릭 publish 합법성의 진짜 선례**(finance 동형 아님).
- **professional-report-engine**: story를 `ReportModel`(TypedDict) SSOT로 대개조 중, **P2(buildReportModel emitter + thesis 빌더) 진행**. 계약 `ui/packages/contracts/src/reportModel.ts`(:28 `excerpt` 블록 = rceptNo+sourceType:'dart' 슬롯, #70 원문근거 요건). Python emitter `story/report.py::buildReportModel` 실재·Company 배선(`company.py:2860`). ★단 `landing/src/lib/report/build.ts`에 excerpt/rceptNo/content_raw 렌더 배선 0건(grep) — 계약 슬롯은 있으나 실렌더 미배선.

---

## 3. 결정 D1–D5 (우수성 평가 반영)

### D1 — 엔진 신설 기각, 3곳 분산
새 `src/dartlab/ipo/` top-level 엔진 **신설 금지**(engine-add 5게이트 비용·import 복잡화·find-SSOT-improve 위반=사본 엔진).
- **(a) 단건 파서 + IPO 판별기 = `src/dartlab/providers/dart/securitiesRegistration.py`** (eventDisclosure 형제, L1). `IPO_SECTION_SCHEMAS` 6카테고리 선언. **`_extractField` 단순 라벨→인접셀 그대로 복사 금지** — 다중표·라벨충돌 오추출(실측 확인). **2단 구조**: 6섹션 경계 앵커링 → 섹션 내부 표만 파싱 + **반복 라벨은 표 단위 그룹핑**(비교기업 "적용 PER" N회 대응). ★섹션 분할은 라벨충돌의 *필요조건이지 충분조건 아님*(`_extractField`가 first-match 휴리스틱이라 섹션 좁혀도 동일 라벨 N개 잔존 → 표 단위 그룹핑 필수).
  - **P0 판별 보조 신호(평가 niceToHave)**: 스팩·이전상장 경계를 `corp_name` "스팩|기업인수목적" 문자열 매칭에만 의존 금지 — 보조 구조신호 병기(스팩 = 신주인수권증서/주주배정 부재 + 공모자금 신탁 조항, 이전상장 = corp_cls 변화 이력). 회사명에 "스팩" 없는 SPAC 오분류 방지.
- **(b) 횡단 소비(2차) = `src/dartlab/scan/ipo.py`(scanIpo)** — orders.py 동형, `scan/router.py` `_AxisEntry` 1엔트리 "ipo" 등록, 공개 `dartlab.scan("ipo")`. **1차 아님** — 단건 deep(6카테고리 표)이 scan의 wide 1행/사 격자와 본질 불일치. 횡단 출력 스키마 미정의 → **실수요 확인 후 착수(필수 아님)**.
- **(c) 단건 리포트 조립 = story builder(L3)** — D3.

공개 verb: 단건 = providers/Company, 횡단 = `scan("ipo")`.

### D2 — 2단 SSOT, publish는 brokerageReports 동형
- **1단(기본·강제) = 런타임 직독.** orders.py 패턴 — `loadDay` 순회 → `report_nm "증권신고서"` + `corp_cls="E"` 필터 → content_raw 직독 → 파서 위임 → 집계. **별도 ipo.parquet 베이크 0.** content_raw 원문은 PRIVATE HF 유지. src/Python·MCP·터미널 소비는 전부 여기.
- **2단(조건부·후행) = brokerageReports 동형 메타 publish.** 합법 경로는 finance 동형이 아니라 **본문 절대 제외·메타만·링크아웃**.
  - **PUBLIC 대상 = 카테고리1·2(공모개요 확정수치·공모일정)뿐** — 발행사가 확정 기재한 사실 메타(공모가밴드·주식수·청약/납입/상장일). rceptNo 링크아웃 동반.
  - **PUBLIC 영구 제외 = 카테고리3(밸류 적용PER·비교기업·할인율)·6(리스크 투자위험 excerpt)** — 본문성 데이터(원문 수치/문장). 터미널 PRIVATE 직독 + `scan("ipo")` 공개계약에만.
  - ★단 **시각 티저용 "구조 메타"(수치 없는 윤곽: 비교기업 *개수*·축 범위·리스크 칩 *개수*)는 PUBLIC 허용 후보** — D4 블러/티저 차등용. 비교기업 *이름*이 본문성인지 메타인지 = 운영자 판정 1건(§5 결정6 신설).
  - 카테고리4·5(유통물량·재무3개년)는 파싱 졸업 후 재평가.
- content_raw 원문 전체 퍼블릭 베이크 절대 금지(SSOT 우회 + PRIVATE 누출). 미검증 상태 publish 금지.

### D3 — 같은 ReportModel chassis, 다른 builder, 다른 데이터원 + IPO 고유 시각문법
- 별도 report MODEL 신설 기각(사본·find-SSOT-improve 위반). 6카테고리 → 기존 18블록 매핑(재무=`table`+`bars`/`line`, 원문근거=`excerpt` 블록 rceptNo+sourceType).
- ★**IPO 고유 시각 primitive 4개 신설(평가 mustFix#5 — UI/UX 최대결함 해소)**. 6카테고리를 정적 표로 평탄화하면 IPO의 시간성·물량동학·상대가치가 죽는다. `ReportModel` 어휘에 **IPO 전용 type 네임스페이스**(블록 어휘 비대화 격리)로 선언:
  - `offeringTimeline` — 수요예측→청약→납입→환불→상장 D-day 가로 타임라인(오늘 마커, 청약 D-3 강조, **현재상태 배지** 수요예측중/청약중 D-2/청약마감/상장완료).
  - `overhangWaterfall` — 상장직후 유통가능물량 → 1/3/6개월 보호예수 해제 누적 워터폴.
  - `peerMultipleChart` — 비교기업 PER 점분포 + 공모가 적용멀티플 마커 + 할인율 화살표.
  - `lockupCalendar` — 보호예수 해제일 월 캘린더(오버행 경보색).
  - 모두 optional/graceful-skip. P4-P5 비용이라 인큐베이터(P0~P2) 무영향, 단 **지금 PRD에 명시**해 D3 매핑이 "IPO 고유 시각문법 0"으로 굳지 않게 함.
- ★**원문근거 deep-link(평가 niceToHave)**: `excerpt` 슬롯 존재(계약만, build.ts 렌더 0건)를 실제 사양으로 승격 — 파서가 P1-P2에서 아는 `sectionAnchor/tableIdx/cellPath` 좌표를 `excerpt.deepLink`에 실어 "공모가 38,000원[출처]"의 [출처]가 DART 원문 해당 표로 직행(62만자 문서에 첫화면 던지면 출처추적 실패). DART 뷰어 표단위 anchor 지원 여부 실측 1건(미지원 시 섹션 단위 격하·천장 인정).
- ★**고저평가 = 단정 판정 회피, "발행사 비교군 좌표화"**: `verdict` 단정("고/저평가") 대신 `build.ts` `peerCompareTable`·`industryStats`(실측 존재 :258/:1343) 재사용해 *발행사가 고른 비교군이 업종분포 어디에 박혔나* 병치 → 투자판단 단정 리스크 회피 + 타 서비스 못하는 고유 우위. 단 industryStats(상장사 기준) vs IPO 비교군(미상장) 정의 정합성 실측 필요.
- IPO는 perspective(같은 회사 다른 렌즈) 아니라 다른 report TYPE — **상장 전 발행사는 finance 시계열 패널 없음**(재무3개년은 신고서 본문 표에서만, finance.parquet 조인 불가).

### D4 — 새 report type "ipo", PUBLIC은 메타 + 시각 티저 차등
- /report 5관점(earningsPower·…)은 finance-lens 시계열 전용(build.ts excerpt/rceptNo/content_raw 참조 0건) → IPO는 새 perspective 아님, **새 report type "ipo".**
- PUBLIC 노출 = D2대로 **카테고리1·2 메타만**(brokerageReports 동형, 브라우저 직독 ssr=false, pyodide 불필요).
- ★**정직표기 = 텍스트 한 줄이 아니라 시각 티저 차등(평가 mustFix#5)**: PUBLIC /report에서 밸류·리스크를 빈자리로 숨기지 말고 `peerMultipleChart`의 **축·비교기업 윤곽은 렌더하되 공모가 마커·할인율·수치만 블러/잠금 오버레이 + 터미널 전체보기 CTA**. 리스크도 칩 *개수*(투자위험 14건)는 PUBLIC, 본문 excerpt만 PRIVATE. terminal_concept "정직은 시각으로" 적용 — "메타만 publish"가 빈약함이 아닌 *의도된 깊이 차등*으로 읽힘.
- ★**시의성 = UX 1급 시민**: 상단 현재상태 배지(`offeringTimeline`) + **데이터 신선도 스탬프**(기준시점·청약일 명시)로 cron publish 지연 리스크를 숨기지 않고 정직 노출.

### D5 — 5 phase, IPO판별을 파싱 앞에, 게이트는 기계 ground-truth + 성능 척추
전부 `tests/_attempts/ipo/`에서 개념확립→실측→모듈화→데모→9섹션 docstring 확정 후 src/ 본진(order-flow-scan 동형). **측정 안 된 점수로 다음 단계 진입 금지(planScore≠시그니처).**

---

## 4. Phasing (졸업게이트 정량지표)

**P0 — IPO 판별기 (providers, _attempts/ipo). garbage-in 0번 게이트.**
- deliverable: `securitiesRegistration.classifyIpo()` — **1차 신호 = `corp_cls=="E" AND stock_code==""`**(실측 확정, 사람 라벨 불필요), 보조 = 신주인수권증서/주주배정 부재·신탁조항(스팩)·corp_cls 변화이력(이전상장). 스팩 별도 태그.
- 게이트: corp_cls 기계 ground-truth 대비 — corp_cls E 21건 전수 IPO 판정·Y/K 67건 전수 비-IPO에서 **오분류 0**(SK하이닉스·계양전기 자동 비-IPO). 경계(코넥스→코스닥 이전상장·재상장)만 운영자 소수 라벨.

**P1 — 6섹션 경계 앵커링 (providers, _attempts/ipo).**
- deliverable: 섹션 앵커 검출기. ★**텍스트 변형 매칭 금지, dart4.xsd 노드 경로/role 구조 앵커링**(평가 niceToHave, feedback_xml_native_truth 정합) — "공모개요"vs"공모의 개요" 정규식 누적이 아니라 XML 구조로. 발행사 수 비례 비대화 방지·발행공시 일반화 보장.
- 게이트: IPO 통과분에서 6섹션 앵커 검출률≥0.95, 섹션밖 노이즈(정관조문) 혼입 0. ★앵커 사전 엔트리 수 추적(비대화=덕지덕지 신호). dart4.xsd 섹션구조 발행사 간 안정성은 P1 선행 실측(가설 미검증 — 불안정 시 조기 노출이 정직한 결론).

**P2 — 카테고리별 파서 (providers, _attempts/ipo).**
- deliverable: `securitiesRegistration.parseIpoProspectus()` + **폼 고정성 실측 docstring** + README. ★출력 dict에 `sectionAnchor/tableIdx/cellPath` 좌표 보존(D3 deep-link용, 파싱 시 이미 알므로 저비용). ★**채널 일반화 negative probe**: 증권신고서(채무증권) 1건을 같은 6섹션 앵커링에 통과시켜 어느 섹션이 깨지나 측정 → IPO 전용 휴리스틱인가 발행공시 클래스 메커니즘인가 조기 판정.
- ★**게이트 = 카테고리별 내적 항등식 프레임워크(평가 mustFix#4 — truth proxy 격상)**. self-redundancy를 단일 트릭에서 검증 프레임워크로:
  - 카테고리1: 공모가×주식수 ≈ 예상시총 (닫힘 확실).
  - 카테고리4(유통): Σ유통가능 + Σ보호예수 ≈ 총발행주식수 (합산 항등식, 닫힘 확실).
  - 카테고리3(밸류): 비교기업PER×주당순익×(1−할인율) ≈ 주당평가가액 (단 발행사별 PER/PBR/EV-EBITDA 혼용 → 닫히는 섹션만 게이트화).
  - 카테고리5(재무): 매출−비용 부호 일관성.
  - truth = 위 항등식 1차 + 소수 사람 스폿체크. flat regex 실패 → `<TABLE>` 구조파싱 강제. 정확도 목표: 공모개요·일정 ≥0.95 박제 가능, 밸류·유통·리스크 목표는 **폼 고정성 실측 후 박제(미박제 placeholder)**. 67건 바스켓 아닌 **전수(통과분 전체) 검증 필수**(concatenation garbage 가드).

**P3 — scan("ipo") 횡단 + src 본진 졸업 (scan L1.5, 조건부).**
- ★**성능 척추(평가 mustFix#2 — 시의성=latency 전환)**:
  - **인덱스-퍼스트**: `loadDay` 통짜 `read_parquet`(:684, 캐시·projection 0) 대신 `report_nm·corp_cls·stock_code` 컬럼만 projection → 21건으로 좁힌 뒤 그 rcept_no만 content_raw **지연 로드**(521→21, 본문 적재 25배 감축). orders의 "35초"는 신호 밀도가 정반대라 무비판 차용 금지.
  - **시의성 SLA**: "신규 신고서 접수→직독 가능" end-to-end 지연(수집 cadence + 콜드 다운로드 + 62만자·1014표 lxml p95)을 **청약 D-N 안에 드는가**로 측정. 이게 제품 가치가설의 생사선.
- 게이트: 위 성능 SLA + orders 동형 데모 + 9섹션 docstring 5점 + dartlabGuard l0-l15 신규위반 0 + publicApiCoverage(`publicApiScenarios.yml` 등록) + structureMirror. **횡단 출력 스키마 실수요 확인 후 — 필수 아님.**

**P4 — story builder 결합 (story L3).**
- ★**emitter 실재 확인(정정 2)**: `buildReportModel` 존재·배선 완료 → **블로커는 "emitter 부재"가 아니라 "기존 emitter가 finance 시계열 전용이라 IPO 별 데이터원·별 perspective 분기 builder 필요"**. `builders/ipo.py` 추가. 6카테고리→18블록 + IPO 4대 시각 primitive(D3). no-graph: emitter는 함수, 고정노드/5패스 금지.
- 게이트: P2 게이트 선행 + checkAgentBoundary/no-graph 회귀 0 + 렌더 눈검수. professional-report-engine 대개조(P2/P3 진행 중)와 이중변경 충돌 회피 위해 줄세움(§5 결정3).

**P5 — 퍼블릭 publish + /report 메타노출 (별도 운영자 결정).**
- **카테고리1·2(공모개요·일정 메타) + 시각 티저용 구조 메타(수치 없는 윤곽)만** brokerageReports 동형 PUBLIC publish. 밸류·리스크 수치/본문 PUBLIC 영구 제외. landing ipo report type, ssr=false. 블러/티저 차등(D4).
- 게이트: 운영자 명시 승인 + **시의성 실측 선행**(P0 직후 0.5단계로 앞당김, §5 결정2) + content_raw 본문 퍼블릭 베이크 0 + 푸시 전 스크린샷 전수 눈검수. **현시점 코드/커밋 0이면 룰 위반 아님.**

---

## 5. 운영자 결정 필요사항 (착수 전)

1. **[P0 신호 정밀화]** `corp_cls=="E" + stock_code==""` 기계 ground-truth 실측 확정 — 경계(코넥스→코스닥 이전상장·재상장·스팩) 처리만 결정(소수 운영자 라벨 vs 보조 구조신호 규칙).
2. **[퍼블릭 시의성 — P0 직후로 앞당김]** IPO 수요예측은 청약일 전 며칠이 가치 → cron publish가 시의성 만족하나, 아니면 터미널 PRIVATE 직독만(P5 영구 보류)? ★카테고리2 메타만으로 "접수→직독 리드타임 분포" 측정 가능(비용 0) → **P5가 아니라 P0 직후 실측**으로 앞당겨 제품 형태를 일찍 결정.
3. **[story 대개조 줄세우기 — 전제 변경]** ★`buildReportModel` emitter 실재 확인됨 → P4 블로커는 "emitter 부재"가 아니라 "기존 emitter finance 전용". IPO builder를 professional-report-engine P2/P3 진행과 어디서 합류시킬지 결정.
4. **[scan("ipo") 실수요]** 단건 deep가 1차라 횡단 scan 필수 아님. "이번달 IPO 후보 횡단" 실수요·출력 스키마 정의 시 착수.
5. **[P2 폼 고정성 표본]** 밸류·유통·리스크 정확도 게이트 숫자 박제 전 측정 표본 규모(IPO 통과분 중 N건).
6. **[신설 — 시각 티저 메타 경계]** PUBLIC 티저용 "구조 메타"(비교기업 *이름*·축 범위·리스크 칩 개수)에서 비교기업 이름이 본문성(PRIVATE)인지 메타(PUBLIC)인지 판정.

---

## 6. 우수성 평가 스코어카드 (5렌즈, 2026-06-29)

| 렌즈 | 점수 | 핵심 |
|---|---|---|
| 엔진 혁신 | 66 | 증명된 혁신 1개(corp_cls 기계 ground-truth). 2단 앵커링은 미증명 가설(검출✓ 추출✗ 자인) |
| 속도·성능 | 61 | 시의성=latency 미환산·orders "35초" 무비판 차용·index-first 미설계 → mustFix#2 반영 |
| 프로덕트·시장 | 61 | 이름-내용 불일치(수요예측 결과변수 누락)·시장정의 부재 → §0.1 + 카테고리7 반영 |
| UI/UX | 52 (최약) | IPO 4대 시각화 0회 → D3 시각 primitive 4개 반영. PRD 자인(UX는 P4-P5 보류)으로 방어 |
| 운영 | (평가 누락) | 평가 에이전트 스키마 실패 — 후속 재평가 대상 |

**총평**: 데이터 파이프라인·SSOT 규율·졸업게이트는 동급 활성 플랜 상위권. 증명된 진짜 혁신은 corp_cls 판별 1개, 나머지는 미증명 가설이거나 올바른 재사용 규율(table-stakes). **치명결함 1건(buildReportModel 미존재 전제 오류)은 §1 정정2로 복구.** 본 v2는 평가 mustFix 5건 + 핵심 niceToHave를 반영한 부분 개정본(전면 재기획 아님).

---

## 7. 토론·실측·평가 산물 위치
- 실측 스크립트: 세션 scratchpad `ipo_probe{1,2,3,4}.py` (probe4가 corp_cls 정정 확정본).
- 아키텍처 토론(4인): 워크플로 `wf_7031498e-34d`. 우수성 평가(5렌즈): 워크플로 `wf_7c1db62d-8eb`.
- 인큐베이터 착수 시: `tests/_attempts/ipo/` (order-flow-scan 구조 동형 — eventSchemas/parser/probe/outputs/README).
