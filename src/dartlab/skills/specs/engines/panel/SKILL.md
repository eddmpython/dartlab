---
id: engines.panel
title: Panel (공시 수평화)
kind: curated
scope: builtin
status: observed
category: engines
purpose: Panel 은 DART 공시 본문(재무제표·주석·서술)을 정부 표준 XBRL 분류(canonicalKey, ACLASS scope-strip) 뼈대 위에서 항목 × 기간 wide pl.DataFrame 으로 수평화하는 엔진. Panel(code)/c.panel 을 잡는 순간 큰 분기별 시계열 DataFrame 이 되고(그 자체가 pl.DataFrame subclass), panel("섹션명") 으로 행 검색. 사전빌드 artifact 를 read (콜드 <1s, 태그 무손실). 트리거 — '공시 수평화', 'panel', '재무제표 다기간', 'canonicalKey', 'disclosureKey'.
whenToUse:
  - panel
  - 공시 수평화
  - 재무제표 다기간 정렬
  - 주석 다기간
  - canonicalKey
  - disclosureKey
  - 항목 × 기간 wide
  - 회사내 수평화
  - 여러 종목 비교
  - 종목 묶음 분석
  - "삼성전자 vs SK하이닉스"
  - peer compare
  - "AAPL과 MSFT"
  - 동종 산업 비교
  - cross-target ranking
inputs:
  - 종목코드 (KR 6자리)
  - 섹션 검색 key — canonicalKey(NT_D826380/BS) 또는 한글 섹션명 substring(재고) 또는 강한 소스 topic(IS/dividend)
  - period 목록 (선택, YYYYQn)
  - tag (선택, 기본 raw 원본 XML / False 면 plain 태그 strip)
  - 소스 = 대소문자 5표 — 소문자 is/bs/cf/cis/sce = native(자급) / 대문자 IS/BS/CF/CIS/SCE = finance(파사드)
  - freq (선택, 입도 — year 연/quarter 분기/ytd 누적, 소스와 직교)
  - 비교 codes 2~6개 (compare — 같은 시장끼리, KR 6자리 또는 US ticker)
  - 비교 scope (compare — consolidated/standalone, 재무 셀모드 고정)
outputs:
  - 항목 × period 수평화 wide (pl.DataFrame, Panel subclass)
  - 섹션 검색 행 (panel(key)) / 본문 전체검색 (panel.search(term))
  - native 재무제표 (c.panel("is", freq="year") = 항목명×기간, XBRL+옛 통합 2011~)
  - finance 재무제표 (c.panel("IS", freq="year") = 파사드 attach, deep history)
  - native 재무비율 (c.panel("ratios") = BS/IS/CF native 항목 → core 공식, 자급, deep history)
  - finance 재무비율 (c.panel("RATIOS") = 파사드 attach, 기존)
  - N사 비교 wide (compare — 식별 컬럼 + 회사별 셀, 재무 topic 은 acode·원 환산, 다기간은 {code}␟{period})
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.dataHub
  - operation.philosophy
capabilityRefs:
  - compare
sourceRefs:
  - dartlab://skills/engines.panel
forbidden:
  - 결손을 0 또는 직전 분기 값으로 채워 추세 왜곡 (compare honest-gap NaN 유지)
  - KO/US 혼합을 한 표로 직접 비교 (compare 시장 경계)
  - EDGAR 재무 adapter 확정 전 US finance 셀 비교
  - 비교 대상 회사명/티커의 영문·한글 변종 혼용
requiredEvidence:
  - disclosureKey
  - canonicalKey
  - period
  - rceptNo
  - corp
  - sourceRef
expectedOutputs:
  - 한 회사 공시 항목의 다기간 가로 정렬 wide
  - 섹션명/canonicalKey 행 검색
  - 강한 소스(재무제표/정형공시)는 finance/report 주입
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
    notes: 로컬 panel artifact 필요 — HF fetch 또는 사전 다운로드 후 read.
failureModes:
  - canonicalKey/섹션명을 추측 (Panel(code) wide 를 먼저 보고 행 식별 컬럼 확인 안 함)
  - tag=True(기본, raw 원본 XML)를 plain 으로 가정 (태그 strip 은 tag=False)
  - 연결/별도(scope) 무시하고 BS_C↔BS_S 병합으로 착시
  - c.panel("IS") 를 raw 공시로 가정 (강한 소스는 finance 주입 — source="raw" 로 raw 강제)
  - freq 를 native↔finance 스위치로 오인 (freq=입도, 소스는 대소문자 is/IS)
  - native(is)에 XBRL 정밀(acode/축)을 2022 이전 기대 (옛 표는 항목명 파싱 — XBRL 태그 없음)
  - 회사 간 비교를 단일 Company 로 반복 (회사 간은 dartlab.compare 가 정렬키로 한 표에 수평화)
  - 토픽 변종 미정규화 (매출액·영업수익·revenue 가 다른 행으로 분리 — compare 가 acode/정렬키로 해소)
examples:
  - 005930 잡는 순간 wide raw (Panel("005930") 또는 c.panel) / plain 은 c.panel(tag=False)
  - 재고자산 주석 다기간 행 검색 (c.panel("재고")) / 본문 전체검색 (c.panel.search("반도체"))
  - native 손익 연속 (c.panel("is", freq="year") — 항목명×연도, XBRL 최근+옛 표 과거 2011~)
  - finance 손익 (c.panel("IS", freq="year") — 파사드 attach, OpenDART deep history)
  - 회사 간 재고 비교 (dartlab.compare(["005930","000660"], topic="재고"))
  - 회사 간 손익 셀 비교 (dartlab.compare(["005930","000660"], topic="is", freq="year") — acode 정렬·원 환산)
procedure:
  - KR(DART) 진입은 `from dartlab.providers.dart.panel import Panel` 또는 `Company(code).panel`.
  - US(EDGAR) 진입은 `from dartlab.providers.edgar.panel import Panel` 또는 `Company(ticker).panel`.
  - 잡는 순간 `Panel(code)`·`c.panel` 이 wide pl.DataFrame — shape/filter/columns 등 polars 연산 그대로.
  - 섹션 검색은 `panel("재고")`(한글) 또는 `panel("NT_D826380")`(canonicalKey). 기본 raw, plain 은 `tag=False`.
  - 본문 전체검색(이름표 아닌 내용)은 `panel.search("키워드")` — 별 메서드(의도 분리).
  - 소스는 대소문자로 가른다. native 재무제표는 소문자 `panel("is"|"bs"|"cf"|"cis"|"sce", freq=)` — XBRL 정밀(2022+) + 옛 표 항목명 파싱(과거 2011~) 통합 statement, panel 자급. finance 는 대문자 `panel("IS", freq=)` — 파사드가 `c.show` 주입(deep history). SCE=자본변동표(EF), CIS=포괄손익(IS3).
  - freq 는 입도(year/quarter/ytd), 소스 스위치 아님 — native·finance 둘 다 받음. finance 는 Y/Q/YTD 로 매핑.
  - report(dividend 등) 정형공시도 facade `c.panel("dividend")` 가 주입. raw 공시 강제는 `source="raw"`.
  - 빌드는 운영자/CI — 로컬 zip `python -m dartlab.providers.dart.panel.build`, 또는 online `.github/scripts/sync/onlinePanel.py`.
  - US(EDGAR)는 같은 read 표면 — `from dartlab.providers.edgar.panel import Panel; Panel(ticker)` / `Company(ticker).panel`. EDGAR `panel` 패키지도 `read`·`schema`·`period`·`mapper`·`canonical`·`spine` 뼈대 이름을 DART 와 맞춘다. 빌드는 SEC full-submission text 를 메모리로 fetch 한 뒤 `edgar/panel/{ticker}.parquet` 만 저장한다. 원본 `.txt` 저장과 별도 `panelCell` artifact 는 없다. 소문자 재무 키 `Panel(ticker)("is")` / `c.panel("is")` 는 panel row native payload 를 read-time 분해하고, 대문자 `c.panel("IS")` 는 companyfacts finance 로 위임한다.
linkedSkills:
  - engines.company
  - engines.dataHub
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-08-09'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`panel` 은 DART 공시 본문을 **정부 표준 XBRL 분류(canonicalKey) 뼈대 위에서 항목(행) × 기간(열)
wide 로 수평화**하는 엔진이다. 양식(era)·회사마다 흔들리는 ACLASS·제목을 기간 간 정렬 가능한
형태로 고정한다. `Panel(code)` / `c.panel` 을 잡는 순간 그 회사의 큰 분기별 시계열 wide
`pl.DataFrame` 이 된다 (Panel 은 `pl.DataFrame` subclass).

핵심 설계:

- **정렬키 = native canonicalKey** — `disclosureKey` 는 정부 발행 ACLASS(DART XBRL 표준 Link
  Role)를 scope-strip 한 순수함수 산출(`mapper.canonicalKey`, BS_C→BS / NT_C_D826380→NT_D826380).
  손매핑과 학습 없이 원천 표준 키를 유지한다.
- **행 순서·계층 = 정부 서식 뼈대(spine)** — `blockOrder` 는 보고서마다 0 리셋이라 read 가
  재발견 못 하고 `canonicalKey` 는 정렬 가능 번호가 아니다 → 정부 문서 표시순서·트리를 빌드 시 1회
  명시 spine 으로 굽는다. `build.buildSpine` 이 **기준 종목 한 회사**(정부 표준 서식이라 reference
  하나로 충분) 최신 사업보고서(Q4)를 raw 파싱 → `rowIdentity`(keyed=disclosureKey /
  narrative=NARR::chapter␟section)별 문서순서·parentKey → `spine/spineData.py`(생성 .py, git-diff
  추적) 생성. `read.readWide` 가 `SPINE` dict 로 `(chapterRank 우선, spineOrder 차선)` 정렬 →
  표지→I→II→III→재무→주석 정부순서(챕터 단위 그룹핑, '(첨부)' 본문 중간 삽입도 자기 챕터로 모음).
  회사간 비교는 `disclosureKey`(같은 항목 같은 키)로 — 회사간 순서 표준화/합의는 panel 책임 밖(scan
  엔진의 cross-market 일). `parentKey` 트리는 Phase 2 셀 세분화 토대.
- **TOC 표준 = SPINE 수렴 (라벨 통일)** — TOC 는 최신 골격(SPINE)으로 고정하고, 과거 era 의 비슷한 섹션
  명칭 변형을 표준 노드로 수렴한다. `read.anchorNarrativeToSpine` 3중 수렴(전부 bounded, 자유 fuzzy 0):
  ① 챕터-자기행 변형(로마/【 헤더, canonical 라벨=자기 chapter)→canonical 챕터 라벨 ② SPINE 제목코어
  일치 = 표면 표기 정규화("6.배당 등"→"6.배당", 옛 번호→현행 번호) ③ 서식개정 era-alias
  (`canonical/canonicalData.NARRATIVE_ERA_ALIASES`, 운영자 수동 — 2018 외감법 V 재편: 옛 INS_* keyed
  감사절 포함 "감사대상업무"→"1. 외부감사에 관한 사항" 등). keyed/narrative 균일 적용 — sectionLeaf 는
  그룹핑 라벨(wide 식별=disclosureKey)이라 셀 식별 무손실(non-null 셀수 불변 게이트 실측). **같은 번호의
  다른 항목**(옛 I.5 의결권현황 vs 현행 I.5 정관)·**1:N 구조분할**(옛 "7. 증권의발행" vs 현행 7-1/7-2)·
  **현행 대응물 없는 단종 섹션**(독립된 감사인의 감사보고서)은 등재 금지 — 분리 유지(honest, 병합=진짜
  정보손실). 뷰어 TS 미러 `viewer/pipeline/narrativeSpine.ts`·`viewer/canonical.ts` 1:1 동기.
- **매퍼 체계 (파일·구분·순서)** — 수렴 매퍼는 새 파서 신설 없이 이 체계 안에서만 자란다:
  ① 데이터 SSOT = `canonical/canonicalData.py` (운영자 수동: CANONICAL_L1 14챕터 키워드 ·
  NARRATIVE_ERA_ALIASES 서식개정 alias · CERT_NODE_IDS) ② 챕터 수렴 = `canonical.canonicalChapterExpr`
  (sectionPath deepest + **XII(상세표) 우선**[상세표 자식 제목의 챕터 키워드 오배정 차단] + NT_→III)
  ③ 섹션 수렴 = `read.sectionLeafConvergeExpr` (단일 Expr SSOT — 자기행·SPINE 코어·era-alias)
  ④ 검열 = `audit.auditToc` — **전종목 lazy 스캔**(projection 5컬럼)으로 ②③ 적용 후 잔존 불변식 위반
  (misplacedDetail·duplicateNumber·selfVariant·coreVariant) 탐지. read 와 같은 Expr 공용이라 검열
  결과 = 사용자가 보는 TOC 와 동형. 새 위반 발견 → 운영자가 ① 에 등재(자동 수정 금지).
- **단일 패키지 자급** — schema·mapper·spine·build·read 가 `providers/dart/panel/` 한 곳. 수집
  (OpenDART API)은 이미 `providers/dart/openapi` 라 build 도 providers 가 자급 (gather panel 폐기).
- **BUILD/READ import 격리** — build(`build/`, lxml/zipfile)는 무거운 zip→16col·spine 생산, read 표면
  (`panel.py`·`read.py`·`spine/`)은 build 를 import 안 함 → read 표면 lxml 0 (콜드 <1s, R2).
  KR 정규화는 native canonicalKey 단독(bridge lookup 농장 0) — US cross-market 정규화는 후속(별도
  설계, scan panel bridge 재사용).
- **태그 무손실** — contentRaw = 원본 XML 그대로 저장. 기본 read 는 plain(태그 strip), `tag=True`
  면 원본 XML (collapse 단계 1회 strip, raw wide 2중 materialize 회피).

### 공시 전체구조 수평화 — BUILD split (확정) / READ 골격정렬 (책임 분리 SSOT)

재무제표(cell, is/bs/cf)는 acode+금액스티칭으로 이미 풀린 시계열. **보고서 전체구조**(챕터·섹션·서술·표)의
수평화는 **BUILD = 잘 나누기 / READ = 현재 골격에 맞춰 정렬** 로 가른다 — "과거 뭉태기 섹션을 현재 기준에 맞춰
비교"가 수평화의 정의이고, 그 비교가능성 메커니즘은 READ 책임.

- **BUILD split (확정·동결, 7사 직접검증)**: 그 zip 하나로 결정되는 확실한 것만.
  - **순서 보존** — `blockOrder` = 문서 위치(split 후 period 내 distinct·0..N-1 연속). horizontalize 가
    섹션을 1행으로 병합해 순서를 잃던 버그 수정 — 각 leaf 가 뼈대 위치를 가짐.
  - **text/table 분리** — `leafSplit.splitOrdered` 가 outermost `<TABLE>` 경계(깊이 스캐너, nested 표는
    바깥 1단위)로 표·텍스트를 별도 행으로. 무손실(part 이으면 원본 byte-identical), 재뭉침 0.
  - **구조 truth** — `sectionPath`(SECTION-N 전 깊이). era mis-nesting 으로 chapter 가 붕괴해도 진짜
    챕터 복원의 재료. **정렬용 해시(contentSig 류)는 bake 안 함** — 정렬은 READ 파생(speculative bake 0).
- **READ 골격정렬 (canonical 복원 확정 + narrative 정렬 baseline)**:
  - **canonical chapter 복원 (`canonical/`)** — `sectionPath` 의 가장 깊은 canonical 14-노드 매치 원소가
    진짜 챕터(`II␟…␟III. 재무에 관한 사항` → III). 붕괴된 chapter(은행 99.5% II 몰림) 복원 + `(첨부)재무제표`
    →III 흡수. READ 파생(재빌드 무관).
  - **narrative 정렬 (현 baseline = 섹션 내 위치정렬 `leafSeq`)** — 같은 섹션 같은 위치 표가 기간 간 한 행
    (매출실적 등 안정위치 표 정렬). 재뭉침 0. **직접확인 결론(7사)**: narrative 표는 대부분 1회성+데이터 진화라
    위치정렬(안정위치엔 효과적, 삽입 누적 시 drift)·구조해시(boilerplate만 매칭, 데이터표 불일치) 둘 다 천장.
    **확신오정렬 > 정렬실패** 라 honest-gap 우선. **정공 후속 = 표구조-aware fuzzy sequence-alignment**
    (reference=최신 Q4 골격, 헤더 구조 매칭) → `operation.architecture` 프런티어.
  - keyed 재무행은 `disclosureKey` 가 식별(시계열 이미 풀림), narrative 만 `leafSeq` 위치정렬.

### parquet 저장 기준 — "불변 원본 + 순수 규칙 산물"만 굽는다 (SSOT)

panel artifact(`{code}.parquet (flat)`)에 **굽는 것**과 **read 가 매번 계산하는 것**을 가르는 단일
기준: **그 값이 "언제 어떻게 바뀔지 모르는가"**. 바뀔 수 있으면 굽지 않는다.

| 무엇 | 굽나 | 왜 |
|---|---|---|
| `contentRaw` (원본 XML) | ✅ build | **불변 원본** — etree.tostring 그대로(R4). 원본이라 영원히 안 변함 |
| `disclosureKey`(=canonicalKey)·`xbrlClass`·`blockOrder`·`atocId` 등 | ✅ build | walker 가 뽑은 원본 속성 + `canonicalKey` **순수함수 규칙** (read fallback 보유 → 규칙 변경 시 재빌드 전에도 동작) |
| `sectionPath` (SECTION-N 전 깊이) | ✅ build | **flatten 으로 잃는 계층 truth** — read 가 재계산 불가(원본 트리 깊이). 붕괴 챕터 복원 재료 |
| `leafType` (text/table) | ✅ build | **확실한 결정론 경계**(`<TABLE>` 유무) — 표·텍스트 분할은 그 zip 으로 결정, 무손실 |
| 정렬용 해시 (contentSig 류) | ❌ bake 안 함 | narrative 정렬축은 read 파생 — 내용해시 bake 는 speculative(필요 시 contentRaw 에서 read-time 재계산) |
| `scope` (연결/별도) | ❌ read 파생 | `scopeExpr(xbrlClass)` 판정 — **규칙이 바뀔 수 있음** → 안 구움, read 가 계산 |
| canonical chapter (붕괴 복원) | ❌ read 파생 | `canonicalChapterExpr` 가 `sectionPath` 깊은 canonical 원소로 진짜 챕터 복원 — 14-노드 매핑 개선이 재빌드 무관 |
| narrative 정렬 (`leafSeq`) | ❌ read 정렬 | 섹션 내 위치정렬(현 baseline) — 정렬 메커니즘 개선(fuzzy sequence-align)이 재빌드 무관 |
| 행 순서·계층 (spine) | ❌ read 정렬 | 전역 spine `(chapterRank, spineOrder)` — corpus 확대·정부 양식 변경 시 재산정 → artifact 불변, spineData.py 만 재생성 |
| 옛 주석 **분할** (de-chunk 제목 행) | ✅ build | `dechunkNotes` 가 통짜 덩어리를 `N.제목` 헤더로 물리 분할(blockLeaf=제목, **disclosureKey=null**) — 헤더 검출 규칙 변경 시에만 재빌드 |
| 옛 주석 **정렬** (NT_ 부여) | ❌ read 정렬 | `alignNotes` 가 read 시 옛 제목 행을 회사 최근 XBRL 뼈대(scope,제목)→NT_ 에 매칭 — **정렬·뼈대 개선이 재빌드 무관**, 뼈대 없는 제목은 narrative |
| 본문+첨부 중복 제거 (dedup) | ❌ read 정렬 | `dedupKeyed` 가 read 시 `(key,scope,period)` 1개 — build 는 분류만(중복 emit), dedup 은 READ 단일책임 |
| plain (태그 strip) | ❌ read strip | raw의 파생 표현이다. strip 규칙이 바뀔 수 있고 같은 정보를 이중 저장하므로 build에 굽지 않는다. |

**원칙**: 파생물·정렬·표현·판정은 **굽지(build) 도, 즉시 다 계산(eager)도 강제하지 않는다.** 굽으면
규칙 변경 시 전 종목 재빌드 폭탄 + 이중저장 회귀. → scope·spine·plain 이 전부 read 시점인 이유.
이 규칙은 panel wide의 형태와 내용 정체성을 유지하는 원칙과 같다.

### 콜드스타트 — strip 위치(채택) + lazy(후속), build 굽기·wide 교체 금지

read plain 콜드 비용의 90%가 173MB raw→plain 정규식 strip (정규식 chain 자체는 floor — per-row·
대체정규식 전부 더 느리거나 틀림, 측정 확인). I/O 72ms·anchor·pivot·orderBySpine 는 ≤10ms.
strip 을 **빠르게**가 아니라 **언제·어디서 하나**로 푼다 — 세 제약 충족: (1) wide 형태·내용 불가침
(2) build 굽기 금지, (3) plain 결과 불변을 모두 충족해야 한다.

- **채택(strip 위치 이동)**: strip 을 collapse(long fragment) 단계가 아니라 **pivot·spine 정렬 후
  wide period 셀**에 1회. 큰 셀 1회 정규식이 작은 조각 수천개보다 빠름 → **콜드 ~1s→0.35s (2.8x)**,
  byte-identical(10481 셀 불일치 0)·plain 기본·tag 옵션·wide 정체성 0 변경. `read._stripExpr` 재사용
  Expr. 이미 적용.
- **raw 기본(채택)**: 기본 `tag=True` raw 라 **잡는 순간 strip 자체를 안 함** → 정부 native 태그
  (ACODE/ACONTEXT) 보존 + AI 이해 + 콜드 더 빠름. plain 은 `tag=False` opt-in (strip-relocation 2.8x
  는 이제 plain 경로 전용). 근거: panel 정체성 = native truth, plain strip 은 그 truth 를 지움 → 기본이
  자기 정체성을 지우면 모순. 사람 표시는 `c.panel(tag=False)` 한 칸.
- **금지**: build plain 사전계산(R4 위반) · wide 를 metadata-only/long 으로 교체(정체성 파괴).

### native 재무제표 (is) — panel.parquet 단일 artifact, read-time 분해, XBRL 정밀 + 옛 표 과거 연장

메인 16-col blob 격자(wide 정체성 불가침)는 안 건드리고, 재무 5표(BS/IS/CIS/CF/SCE)를 **별개 parquet 파일
없이** panel.parquet 의 5표 row `contentRaw`(표 XML)에서 **read-time 분해**(`cell._cellsFromPanel` →
`build/cell.cellsFromContent` 함수 lazy lxml). **소스 = panel.parquet 단일**(zip 재처리 0, 별도 DART 문서 parquet 0,
별 panelCell artifact 0). 체인 zip → buildPanel → panel.parquet → (read 시) `cellsFromContent` 분해 →
`cell.readStatement` → `c.panel("is", freq=)`(소문자, panel 자급, 단일 artifact). 콜드: 모듈 top-level lxml 0
(분해는 panel("is") 호출 시에만 lazy 로드). finance(대문자 IS)는 파사드 attach(별개).

- **두 era 통합** — XBRL 있으면(2022+) `<TE ACODE ACONTEXT>` 정밀 셀(`decodeAcontext`: 정부 토큰
  `[C|P|BP]FY{year}[d|e]{marker}`, 산수 0). 없으면(2021 이전, XBRL 태그 없음) **옛 표 위치 파싱**(첫 셀=항목명,
  이후 셀=당기/전기/전전기 금액, `_parseAmount`/`_detectUnit` — docs/finance 로직 참고 재구현). 한 보고서가
  당기/전기/전전기 3년 운반.
- **항목명 통합** — `readStatement` 가 XBRL `label`("매출액 (주30)")과 옛 항목명("매출액")을 `_normalizeLabel`
  ((주N) strip)로 매칭 → 전 기간 연속(2011~). 정밀 최근 + 과거 한 줄. **개명 항목**("수익(매출액)"→"매출액")은
  `_stitchRecentName` 이 **금액 겹침**(연속 보고서 당기/전기 겹친 해의 동일 금액)으로 묶어 **최근 이름** 기준
  한 줄(식별력 있는 큰 금액=콤마만 링크, over-merge 회피). 겹치는 해는 최신 filing(=XBRL) 우선.
- **statement resolution = 단일 SSOT (`STATEMENT_VARIANTS`)** — 논리 키(`is`/`bs`/`cf`/`cis`/`sce`)를
  물리 XBRL class 후보(우선순위)로 해소하는 *한 테이블*. 회사마다 손익을 단일(IS1)/별도(IS2)/포괄(IS3)로,
  공시를 연결/별도로 달리 내므로 그 변형을 한 곳이 흡수한다 — 폴백을 코드에 흩지 않음(덕지덕지 금지).
  `is → (IS2, IS3, IS1)` · `cis → (IS3, IS2, IS1)` · `bs → (BS,)` · `cf → (CF,)` · `sce → (EF,)`,
  scope 는 `SCOPE_ORDER=(consolidated, standalone)`. `readStatement(statement=논리키)` →
  `_resolveStatement(variants × scope)` 단일 resolver. panel.py 는 `_NATIVE_KEYS`(논리 키)만 넘긴다
  (물리 매핑 중복 0). 비율도 `_RATIO_SOURCE`(논리키)로 동일 해소. **이게 panel native 의 근본 축**.
- **freq = 입도** (소스 스위치 아님) — `year`(연)/`quarter`(분기)/`ytd`(누적), native·finance 둘 다. native
  XBRL 은 ctxMode 토큰 선택. **연간 = dFY(Y) 또는 Q4 누적(A & Q4=12M)** — 회사별 연간 인코딩 차이 흡수.
  옛 분기만 신고한 신규 상장사는 `ytd`/`quarter` 로 도달(연간 미신고). `readCellWide`(acode 정밀 차원 view,
  물리 statement)는 XBRL 전용 유지.
- **저장 원칙 적용** — 파싱(ctxYear/ctxFlow/ctxQuarter/ctxMode/axisPath/valueRaw)은 순수 규칙이라 build,
  freq/통합은 표현이라 read. valueRaw 콤마·괄호 무손실(숫자화는 소비자). 셀은 panel.parquet 파생이라 stale 면
  재빌드(파생 체인).
- **주석 미포함** — 확정 범위 = 5표만. NT_* 주석은 schema `statement` 컬럼이라 후속 확장 대비(미착수).

### native 재무비율 (ratios) — 공시 표 아닌 native 5표 항목의 산수

- **소스 = 대소문자** — 소문자 `c.panel("ratios")` = native(panel 자급), 대문자 `c.panel("RATIOS")` = finance
  (파사드 위임, 기존). is/IS 와 대칭.
- **비율은 "공시 표 읽기"가 아니라 "재무제표 항목 산수"** — DART 에 표준 재무비율 표 없음(5표가 전부). native
  비율 = `readStatement`(bs/is/cf native, 2013~) 항목 → core mappings 로 snakeId series 조립 →
  `core.ratios.calcRatioSeries`(공식 SSOT) → 비율 wide. **공식·매핑·파서·라벨 전부 core(L0) 호출, panel
  재구현 0**(농장 금지). native 5표 과거연장 덕에 finance(2016~)보다 깊은 history.
- **계산 위치 = panel 자급** — cell.py 가 core(L0)만 import(finance/reference 0, R1 유지). standalone
  `Panel(code)("ratios")` 도 동작. snakeId 버킷 = 읽은 statement(BS/IS/CF) — `standardAccounts.sj` COMMON 모호
  회피. 단위는 동일 표 항목 몫이라 상쇄.
- **제외 범위** — 밸류에이션(PER/PBR)은 price 미보유로 제외(statement-only: 수익성/안정성/효율성/현금흐름/복합/
  성장). 매핑 갭은 그 비율만 해당 period None(숨김 0) — 갭은 core `accountMappings.json` 보강(panel-local 0).

### 주석 수평화 (de-chunk 분할 + alignNotes 정렬) — 옛 통짜 주석을 최근 XBRL 뼈대로

2023+ 보고서는 주석이 항목별 `NT_*` 행(XBRL 태깅, native disclosureKey)으로 들어오나, 그 이전은 **disclosureKey
없는 통짜 덩어리**라 era 경계에서 수평화가 끊긴다. **책임 분리 = BUILD 분할(동결) / READ 정렬(동적)** — 정렬·뼈대
개선이 재빌드를 부르지 않게 한다(빌드는 헤딩 분류가 틀렸을 때만 재빌드).

- **BUILD 분할 — `build/dechunkNotes.py`**: 재무제표 노트 영역 gate(`sectionLeaf 주석` OR `ctx 재무제표`, 사업
  보고서 TOC·배당·MD&A 제외)로 통짜 덩어리만 골라, 본문 `N. 제목` 헤더를 **통합 검출**(`_detectHeaders`)로 노트 1개당
  한 행(`blockLeaf`=제목)으로 **쪼갠다 — `disclosureKey` 는 null**(NT_ 부여 안 함). 검출은 delimited
  (`<SPAN>1. 재고자산</SPAN>`)·옛 concatenated(`…비츠로시스1. 일반사항</P>` 제목이 산문·본문에 붙음, 전 종목 68%)
  양 포맷을 한 패턴(`_NUMDOT`)으로 후보화하고 **뼈대 사전 최장 prefix-match + 표셀 가드(`_inTableCell`, 전 corpus
  유일 오탐=표셀 7.3% 차단) + 번호 단조증가** 로 진짜 헤더만 가린다(2자 제목은 비-한글 경계일 때만). preamble(재무제표
  본표)은 원 블록 보존. **preamble + Σ제목행 = 원 블록 byte-exact**(무손실).
- **검출 뼈대 사전 — `build/noteTaxonomy.py`(생성기) → `noteTaxonomyData.py`(생성물, git 추적)**: 전 corpus
  2023+ XBRL 에서 `(scope, 정규화제목)` dominant 제목 학습 — `_detectHeaders` 가 "진짜 노트 제목인가" 판정에만 쓴다
  (코드 부여 아님). 모호 제목(`dominanceRatio` 미달)은 제외(미매칭→narrative). `_norm`(제목 정규화) SSOT 공유.
- **READ 정렬 — `read.alignNotes`(신규)**: 옛 split 주석행(null key)을 **회사 자기 최근 XBRL 뼈대**((scope,
  정규화제목)→native NT_, 제목 접미사 " - 연결/별도" 분리)에 매칭해 같은 identity 부여 → 최근과 수평 정렬. **뼈대에 없는
  제목은 null 유지(narrative)** — 산문 오분할·미공시도 가짜 NT_ 안 받음(뼈대 중복 0). `readWide` 가 `readLong` 직후
  ·anchorLatest 직전 호출. 정렬 규칙·뼈대 개선이 **재빌드 무관**(read-time).
- **READ 중복 축약 — `mapper.dedupKeyed`**: 본문("III.재무")·첨부("(첨부)재무제표") 중복 수록된 같은 NT_ 를
  `(disclosureKey, scope, period)` 당 1개(xbrlClass native 우선)로 — dedup 도 READ 한 곳.

**재빌드 cadence(중요)** — de-chunk 는 **분할만 baked**(헤딩 분류). **정렬(NT_ 부여)·뼈대는 READ(`alignNotes`)라
재빌드 무관** — taxonomy 정밀화·정렬 규칙 개선은 read-time 즉시 반영. **전수 `--all` 재빌드는 헤더 검출 규칙
(`_detectHeaders`) 자체가 바뀔 때만**(~135분). 새 증분 회사는 `--changed` 로 그 회사만 빌드(전수 아님).

**모니터링** — `tests/audit/panelHorizonCensus.py`: `grid_duplicated`(증식)·`content_dropped`(char-parity)·
`note_discontinuous`(과거연간 NT_ 0). 단 `note_discontinuous` 는 *비표준 주석 회사*(genuine narrative)도
깃발하니 버그 vs 정상 수동 판별 필요(택소노미 미등재=정상).

```
DART zip / DART API ──build(providers/dart/panel/build)─→ {code}.parquet (flat) (16-col)
                                                              │
                                                              ↓
                          Panel(code) / c.panel  (read, plain 콜드 ~0.35s, pl.DataFrame subclass)
```

### EDGAR (US) 미러 — SEC text 자급 파싱 (DART panel급 보드 단일 artifact)

DART panel 의 단일 artifact 원칙을 EDGAR 도 **필링 원본 inline us-gaap XBRL** 로 재현한다.
입력은 SEC full-submission text 를 메모리로 fetch 한 값이며, `data/original/edgar/docs/*.txt` 로 저장하지
않는다. read 표면(`Panel`·`read`·`mapper`·`canonical`·`spine`)은 `marketNs="us"` 로 무변경 재사용
(16-col `PANEL_SCHEMA` 동결 계약).

- **build = SEC full-submission text 자급 파싱 (`providers/edgar/panel/build`, sections/gather/meta 의존 0)** —
  `submission`(SGML→header+primary HTML+EX-101.PRE) → `linkbase`(presentation role→concept 순서) →
  `walker`(보드).
- **보드 = XBRL 앵커링** — 재무제표 본표는 presentation **role URI → 정규 statement key**(BS/IS/CF/CIS/EF,
  `mapper.roleToStatement`)로 `disclosureKey` 앵커링(statement 당 커버리지 최대 표 1개 — DART ACLASS 의
  EDGAR 미러). 서술 Item 은 narrative(null, rowIdentity=`NARR::{form}␟Item`). DART read 변환 graceful:
  `scopeExpr`(null→consolidated, 연결-only 정답)·`canonicalChapterExpr`(passthrough)·`orderBySpine`(_skel).
- **재무제표 표면** — `c.panel("is"/"bs"/"cf"/"ratios")` 소문자 키는 EDGAR panel row native payload 를
  read-time 분해한다. `c.panel("IS"/"BS"/"CF"/"RATIOS")` 대문자 강한 재무 키는
  EDGAR finance/companyfacts facade 가 담당한다. EDGAR panel 은 별도 native cell artifact 를 만들지 않는다.
- **배포** — `edgar/panel/{ticker}.parquet`(보드) flat. HF `edgarPanel` 카테고리, read 부재 시
  `ensurePanelFromHf(marketNs="us")` 가 panel 단일 artifact 를 lazy 다운로드. sync 는 weekly
  `buildEdgarPanel.py` (SEC text fetch→build).

```
SEC full-submission text (in-memory)
  │ submission(SGML) → linkbase(PRE)
  └─ walker → 보드 16-col (재무표 role→disclosureKey 앵커링, 서술 narrative)
  ↓
edgar/panel/{ticker}.parquet
  │ Panel(ticker, marketNs="us")/c.panel
```

## 공개 호출 방식

```python
from dartlab.providers.dart.panel import Panel

# 1. 잡는 순간 wide — Panel 은 pl.DataFrame subclass
p = Panel("005930")                  # 항목 × period wide (행=공시항목, 열=period)
p.shape                              # (항목수, period수) — polars 연산 그대로
p.columns                           # chapter · sectionLeaf · blockLeaf · disclosureKey · scope · 2025Q4 · ...
p.filter(...)                       # filter/select 등 그대로

# 2. 섹션 행 검색 — callable (board/show verb 없음)
inv = p("재고")                      # 한글 섹션명 substring 매칭 행
invc = p("NT_D826380")              # canonicalKey exact
raw = p("재고", tag=True)           # 원본 XML 보존 (기본은 plain)

# 3. 대형 종목 메모리 핸들 — period 파일 prune
p2 = Panel("005930", periods=["2025Q4", "2026Q1"])

# 4. 사용법 가이드 — 호출 패턴 (전역 dartlab.help=발견과 구분, 상세는 skills.describe)
print(Panel.guide())                # 또는 c.panel.guide() — wide·섹션검색·native/finance·freq·tag 패턴
```

```python
import dartlab

c = dartlab.Company("005930")
c.panel                              # 동일 — 잡는 순간 wide pl.DataFrame
c.panel("재고")                      # 섹션 행 (raw 공시)
c.panel("IS")                        # 강한 소스 — finance 주입 (XBRL 정규화 숫자)
c.panel("dividend")                  # 강한 소스 — report 주입 (정형 공시)
c.panel("IS", source="raw")          # raw 공시 강제 (오리지널)
```

```bash
# 빌드 트랙 A — 로컬 zip 소비 (network 0)
python -X utf8 -m dartlab.providers.dart.panel.build --codes 005930,000660
python .github/scripts/sync/buildPanel.py --changed                       # sync 증분(로컬 zip)

# 빌드 트랙 B — online 1패스 (DART API → 메모리 → parquet, 디스크 zip 0)
python .github/scripts/sync/onlinePanel.py --changed                      # DART filings rcept fetch

# 정부 서식 뼈대(spine) 생성 — 기준 종목 최신 사업보고서 문서순서·트리 → spine/spineData.py (git 추적)
python -X utf8 -m dartlab.providers.dart.panel.build --spine --codes 005930,000660

# 주석 뼈대(noteTaxonomy) 생성 — 전 corpus 2023+ XBRL 학습 → build/noteTaxonomyData.py (git 추적).
# build-baked(spine 과 달리 read 정렬 아님) → 재생성 후 전수 --all 재빌드 필수. 노브 --minFreq/--dominanceRatio.
python -X utf8 -m dartlab.providers.dart.panel.build --noteTaxonomy

# EDGAR (US) 빌드 — SEC full-submission text 메모리 fetch → edgar/panel 단일 artifact
python -X utf8 -m dartlab.providers.edgar.panel.build --ticker AAPL filing1.txt
python .github/scripts/sync/buildEdgarPanel.py --tickers AAPL,MSFT         # sync(weekly, txt 저장 없음)
python .github/scripts/sync/buildEdgarPanel.py --all --overwrite
```

## 호출 동작

`Panel(code, *, marketNs="kr", periods=None, tag=False)` — 한 회사의 panel artifact 를 read 해
wide `pl.DataFrame` 으로 materialize. standalone `Panel` 은 상태 없음(누적 0). Company facade 의
`c.panel` 은 Company 수명 동안 같은 Panel 한 개를 `BoundedCache` 로 재사용하며,
`cleanupCache()` 또는 context manager 종료 시 폐기한다. multi-company 루프는 회사마다 새 Company 를
context manager 로 열어 Polars Rust heap 누적을 막는다.

- `Panel(code)` 자체 = wide DataFrame. 행 identity = (chapter, sectionLeaf, blockLeaf,
  disclosureKey, scope), 열 = period, cell = 본문(tag=False plain / tag=True raw XML).
- `panel(key, *, source="auto", tag=None, periods=None)` — callable 섹션 검색.
  - `source="auto"`(기본): 강한 소스(BS/IS/CF/ratios/inventory/dividend…)는 facade 주입 `c.show`
    위임(finance/report 가 raw 공시보다 강함). canonicalKey/한글 섹션명은 raw 공시 행 검색.
  - `source="raw"`: 강제 raw 공시 행. `source="finance"/"report"`: 강제 주입.
  - `tag`: None 면 인스턴스 tag 상속, 명시 시 그 tag 로 재read (raw 검색만).
  - finance/report 주입은 **facade(`c.panel`) 전용** — standalone `Panel(code)` 는 주입 없어 항상
    raw 검색 (panel 패키지는 finance 를 import 안 함, cycle 0).

정상 artifact 부재와 조회 조건에 맞는 행이 없는 경우는 빈 DataFrame / None 이다. 존재하는 artifact 의
손상·읽기 실패·schema 위반은 정상 무데이터로 바꾸지 않고 원인 예외를 호출자에게 전달한다.
disclosureKey(=canonicalKey)는 build 가 부착하며, 옛 artifact(전부 null)만 read 시점 canonicalKey
fallback resolve.

## 대표 반환 형태

```text
Panel("005930")     # 그 자체가 wide pl.DataFrame
→ chapter · sectionLeaf · blockLeaf · disclosureKey · scope · 2025Q4 · 2025Q3 · ...
  (행 = 공시 항목, cell = 본문 plain — tag=True 면 원본 XML)
```

```text
Panel("005930")("재고")     # 또는 ("NT_D826380")
→ pl.DataFrame  (매칭 행만, 연결 NT_D826380 + 별도 NT_D826385 = scope 로 분리된 2 행)
```

```text
c.panel("IS")     # 강한 소스 — finance 주입 (XBRL 정규화 숫자)
→ pl.DataFrame  (snakeId · 항목 · 2026Q1 · 2025Q4 · ... — XBRL 정규화 숫자)
```

16-col artifact schema (PANEL_SCHEMA): chapter · sectionLeaf · **sectionPath** · **leafType** ·
blockLeaf · xbrlClass · xbrlMatched · xbrlMatchScore · atocId · aassocnote · blockOrder ·
contentRaw · period · corp · rceptNo · disclosureKey(=canonicalKey). `scope`(연결/별도)는 read 파생
(저장 안 함). `sectionPath`(SECTION-N 전 깊이 ␟join) = flatten 으로 잃는 계층 truth — DART era 가 챕터
III~XII 를 II 아래 mis-nesting 해 chapter 가 붕괴할 때 read 가 sectionPath 깊은 canonical 원소로 진짜 챕터
복원(은행 99.5% 붕괴→정상). `leafType`(text/table) = 확실한 결정론 경계라 BUILD 가 표·텍스트를 별도 행으로
분할(표↔표 비교). 행 순서·계층은 artifact 가 아니라 정부 서식 spine + canonical chapter 가 결정 — schema 불변.

## 회사 간 비교 (compare)

`Panel`/`c.panel` 이 *한 회사* 를 항목×기간으로 수평화한다면, **`dartlab.compare`** 는 *2~6개 회사* 를 같은
토픽·시점 격자로 정렬한다. `scan` 처럼 단어 1 개 톱레벨 verb — 회사 간 비교의 공식 호출계약이다 (호출계약은
`dartlab.compare` 하나, 옛 `compareTargets`/`comparePanel` 별칭 없음). 구현 `providers/dart/panel/compare.py`,
EDGAR 미러 `providers/edgar/panel/compare.py`.

```python
import dartlab

# 주석·서술 row 비교 — 정렬키 (disclosureKey, scope, leafType)
dartlab.compare(["005930", "000660"], topic="재고")

# 재무제표 셀 비교 — acode 단위, 값은 원 환산 (단위·라벨 착시 제거)
dartlab.compare(["005930", "000660"], topic="is", freq="year")

# 다기간 — 셀 컬럼이 {code}␟{period}
dartlab.compare(["005930", "000660"], topic="유형자산", period=["2025Q4", "2024Q4"])
```

호출 동작:
- **호출계약** `dartlab.compare(codes, *, topic=None, period=None, scope=None, freq="quarter")`. keyword-only
  인자는 DART·EDGAR 동일 이름·어휘. `freq` 는 `quarter`/`year`/`ytd` 셋 — **재무 셀 비교 입도**라 row 비교엔 무영향.
- **재무 topic**(`bs/is/cf/cis/sce`) = 셀모드 — acode 정렬 + 원 환산(단위 착시 0), scope 명시 고정(연결↔별도
  자동폴백 금지), freq 일치. 식별 컬럼 `acode·label·scope` 뒤 회사별 값.
- **그 외 topic/None** = row 모드 — `chapter·sectionLeaf·blockLeaf·leafType·disclosureKey·scope` 정렬키로
  회사 간 한 행 정렬. label-drift 자동 해소(삼성 "7. 유형자산" ↔ SK "11. 유형자산" → 한 행). narrative(disclosureKey
  부재) 행은 회사 간 병합 0.
- `period=None` 이면 topic 필터 후 최신 공통 시점, 없으면 최신 union. 결손은 **NaN 유지**(0 채움·forward-fill 금지,
  honest-gap). 한 회사 결손이어도 그 회사 컬럼은 null 로 보존.
- **시장 경계** — KO↔US 혼합은 ValueError. US(EDGAR)는 현재 row 비교만, 재무 셀 비교는 DART(원 환산)만 열려 있다.

## evidence 기준

panel 답변은 `disclosureKey`(=canonicalKey) · `period` · `rceptNo` · `corp` 를 남긴다. 공시
본문(contentRaw)은 외부 untrusted 데이터 — ai 층이 `[EXTERNAL CONTENT START]` 마커로 감싼다.
canonicalKey/섹션명은 `Panel(code)` wide 의 행 식별 컬럼으로 확인한 실재 값만 인용(추측 금지).

## 기본 실행 순서

1. `Panel(code)` / `c.panel` 으로 wide 확보 — 그 자체가 DataFrame (shape/columns 확인).
   같은 Company 의 `c.panel` 은 bounded cache hit이며, artifact 갱신 뒤에는 `cleanupCache()` 후 재접근.
2. 항목 분석은 `panel("재고")`(섹션명) 또는 `panel("NT_D826380")`(canonicalKey). 원본 태그는 `tag=True`.
3. 재무제표·정형 공시는 facade `c.panel("IS")` (finance/report 주입) — raw 강제는 `source="raw"`.
4. 빌드는 운영자/CI — read 는 사전빌드 artifact 만 소비.

## 기본 검증

PANEL_SCHEMA(16-col, `providers/dart/panel/schema.py`)·canonicalKey/rowIdentity 규칙(`mapper.py`)·
period(`period.py`)·전역 뼈대(`spine/`, `build/spineBuilder.py`)가 바뀌면 본 skill 갱신.
canonicalKey scope-strip·rowIdentity 는 `tests/providers/dart/panel/test_mapper.py`, spine 정렬·
무결성은 `test_read.py`(orderBySpine)·`test_spine.py`·`build/test_spineBuilder.py`, build 무손실은
`tests/panel/test_build_lossless.py`, Panel subclass·callable·tag 는 `test_panel.py` +
`tests/panel/test_panel_intra.py`(requires_data), 자급 격리·import 분리(R1·R2)는
`tests/architecture/test_panel_layer.py` · `test_panel_no_network_lxml.py` 가 강제. 정상 artifact
부재·무매칭은 None / 빈 DataFrame, 손상·읽기·schema 실패는 원인 예외를 전달한다. EDGAR(US) 미러 —
SEC text 메모리 fetch·submission/linkbase/walker/
mapper·role→disclosureKey 앵커링·Panel(us) 보드·finance 라우팅 계약은
`tests/providers/edgar/panel/`(test_submission·instance·linkbase·walker·mapper·builder·panel).

> Skill OS JSON index(`src/dartlab/skills/*.json`)는 **운영자 수동 동기화** — 본 spec 변경 시
> 자동 생성 금지(CLAUDE.md "자동 빌드 도구 금지").
