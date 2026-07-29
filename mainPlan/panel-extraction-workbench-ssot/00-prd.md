# Panel 추출 완전 카탈로그 SSOT + 데이터 워크벤치 · 통합 PRD

> 운영자 목표: "provider panel 에서 빼먹을 수 있는 모든 정보를 EDGAR·DART 동급으로 panel 단위 카테고리화(SSOT)
> 하고 성공 TODO 까지 엔진차원에서 정한다. 사업보고서 전부(과거 연결·XBRL 한도·정성 텍스트까지)를 덕지덕지
> 없는 체계적 파서로 탈탈 턴다. providers·company facade 차원의 공동 작업대(수집·정리·가공준비·예측)를
> SSOT 로 만든다. 새 엔진 신설이든 L1.5 분배든 정공법을 토론으로 체계화한다."
>
> 본 PRD 는 `panel-note-extraction-ssot`(노트 한정)를 흡수·확장한다. 그 문서의 결론 일부는 stale
> (scanNotes 를 stub 이라 기재했으나 실제는 완전 구현됨) 이라 본 문서가 정본이 된다.

## 결론 (5줄)

1. **추출 능력은 이미 무결하다.** 빠진 건 (a) 통합 개념 카탈로그 SSOT, (b) 정성 추출의 체계화, (c) 카탈로그
   구동 워크벤치 표면, (d) 성공을 판정하는 coverage census. 넷 다 신설이 아니라 기존 자산 정합.
2. **새 모놀리식 워크벤치 엔진은 거부한다.** 수집(L1)·정리(L1.5)·예측(L2)을 한 엔진에 담으면 4계층 단방향·
   도메인 격리·런타임-SSOT 무bake 를 동시에 깬다. 예측은 워크벤치가 소유가 아니라 위임이 맞다.
3. **정공법 = 3 조각 분배**: 카탈로그 SSOT 는 `core/dataEntry.py`(L0, 기존 seed 확장), 조립 view 는
   `frame/`(L1.5, "raw 결합" 헌장 정합), 표면은 Company·root facade(카탈로그 구동) + 예측은 기존 L2 위임.
4. **성공 TODO = coverage census 원장.** 카탈로그 매니페스트 vs 실제 추출을 전종목·양 provider 로 대조하여
   개념별 `추출됨?(DART/EDGAR)·커버리지%·honest-null 사유` 산출. 성공 = 전 개념이 (추출됨) 또는 (기록된 정직-null).
5. **덕지덕지 제거의 정확한 타깃 = DART `sectionTopic.py` ~200 손regex.** EDGAR 는 이미 SEC Item 택소노미로
   체계적. 정공 = 양 provider 를 "앵커 구동 정성추출"로 수렴(DART 앵커는 panel SPINE canonical 노드, 이미 빌드됨).

---

## 1. 실측 현황 (재조정 · 스윕 근거)

### 1.1 추출 표면 (완성)

| 표면 | 위치 | 상태 |
|---|---|---|
| 재무 5표 셀 (is/bs/cf/cis/sce) | `providers/dart/panel/build/cell.py::cellsFromContent` + edgar 미러 | 완성 |
| 노트가족 read (NT_, aligned long, Q4 deep) | `providers/dart/panel/cell.py::_noteCellsFromPanel` | 완성 |
| 전종목 노트 구조 스캐너 | `providers/mappers/scanner.py::scanNotes/scanAll` | 완성 (노트판 PRD "stub" 기재는 오류) |
| DART 정형공시 28 apiType | `providers/dart/report/{spec,extract,pivot}.py` | 완성 (self-describing catalog `buildSpec`) |
| EDGAR report 파서 8종 | `providers/edgar/report/{auditOpinion,executivePay,majorHolder,outsideDirector,ex21Parse,employee,capitalChange,debtSecurities}.py` | 완성 (proxy/EX-21/DERA, 적중 75~85%) |
| DART 정성 topic ~15 | `providers/dart/sectionTopic.py` (~200 손regex) | 덕지덕지 |
| EDGAR 정성 (SEC Item 택소노미) | `providers/edgar/docs/sections/{mapper,textStructure,itemBoundary}.py` | 체계적 |

### 1.2 개념 레지스트리 (분산 · 통합 SSOT 부재)

- `core/dataEntry.py`: DataEntry 12종 (표준 IFRS ~32 중). `notesDispatch`+`extractor` 구동.
- `providers/dart/report/spec.py::buildSpec`: DART 28 apiType self-describing 카탈로그 (EDGAR 대응 spec 없음).
- `scan/builders/kr/{report,}/fieldCatalog.py`: screening 필드 SSOT (KR 한정).
- `providers/mappers/mapperData/notesStructure.json`: 499KB, 2877사 스캔, `lastScan 2026-04-10`(stale, 미동결).
- **갭: 양 provider 를 아우르는 단일 개념 카탈로그 0. DART↔EDGAR parity 판정 0.**

### 1.3 DART↔EDGAR parity 갭 (성공 원장의 원재료)

**DART 추출 · EDGAR 미비:**
- 수주잔고/book-to-bill(`scan/orders.py`, 이벤트공시 파생), IPO(`scan/ipo.py`), 공시변화리스크(`scan/disclosureRisk.py`),
  내부자/최대주주변동(`scan/insider.py`): US 규제에 단건계약 공시 없음. 상당수 구조적 부재.
- network 타법인출자 장부가·지분%(`scan/network/scanner.py`): EDGAR 는 EX-21 자회사 이름+관할만(장부가/지분% null, 정직).
- workforce 급여/근속/성별/부가가치(`scan/workforce/`): EDGAR 는 headcount 만.
- `scan/router.py::_EDGAR_XBRL_AXES` 가 governance·workforce·insider·network 축을 US 미라우팅.

**EDGAR 추출 · DART 미비:**
- XBRL TextBlock 서술노트 ~20(`providers/edgar/docs/notes.py::_NOTE_LABELS`: AccountingPolicies·RevenueRecognition·
  FairValue·CommitmentsAndContingencies·SubsequentEvents 등): DART 1급 개념 없음.
- ecd Pay-vs-Performance(CEO actually-paid·peer TSR): DART 대응 없음.
- 표준화된 MD&A(Item 7)·Risk Factors(Item 1A) 깨끗한 매핑 섹션: DART canonical topic 없음.

**구조 비대칭:** DART 사업보고서 = 28 정형 apiType(거버넌스·자본·인력·부채가 깔끔한 표). EDGAR = XBRL fact 또는
proxy/EX-21 HTML 재구성(적중률 부분). 이 비대칭 자체가 카탈로그의 `axisType`·`honestNull` 로 명문화될 재료.

### 1.4 워크벤치 표면 (부재)

- `src/dartlab` 의 "workbench" 는 전부 AI Ask Workbench(`ai/workbench/`, BRIEF부터 HARVEST 5패스). 데이터 조립 아님.
- 실질 조립 facade = `Company`(dart 5.5K줄 + edgar 3.8K줄) + `panel`. 회사 전체(재무+노트+거버넌스+정성+scan)를 한
  자리에 정리하는 상위 객체 0. 오늘은 `c.panel()`·`c.finance`·apiType accessor·`scan(axis)` 를 손으로 조합해야 함.

---

## 2. 아키텍처 결정 (토론 정본)

### 2.1 선택지 대면

| 선택지 | 판정 | 근거 |
|---|---|---|
| A. company/gather 위 새 모놀리식 "워크벤치 엔진"(수집·정리·예측) | 거부 | L1·L2 관통 = 단방향 import·도메인 격리·무bake 동시 위반. "예측 소유"가 오류 |
| B. L1.5 정밀 분배 + facade + L2 예측 위임 | 채택 | 각 조각이 기존 헌장에 정확히 안착. 새 엔진 0·새 bake 0 |

### 2.2 채택안의 계층 배치 (import 규칙 증명 포함)

| 조각 | 위치 | 계층 | import 정합 |
|---|---|---|---|
| 개념 카탈로그 (매니페스트) | `core/dataEntry.py` 확장 (기존 notes seed) | L0 | 모든 계층 import 가능. 데이터+dispatch 키+parity 메타만 보유(provider import 0 → L0 유지). |
| 조립 view (정리/가공준비) | `frame/workbench.py` (신규) | L1.5 | frame 이 core(카탈로그)·providers(추출)·gather 전부 import OK. frame↛reference 회피가 카탈로그를 core 에 둔 이유. |
| coverage census (성공 TODO) | `tests/audit/extractionCoverageCensus.py` (신규) | audit | 최상위 감사도구. Guard Index 형제. |
| 단일사 표면 | `Company.workbench`(프로퍼티) + root `dartlab.workbench(code)` | facade | frame 조립 위임. Company frozen surface 계약 유지(additive). |
| 횡단 표면 | `scan`(기존) | L1.5 | 이미 횡단 워크벤치. 변경 0. |
| 예측 | `analysis.forecast`·`quant`·`macro` | L2 | facade 가 위임(예: `c.workbench.forecast()` 가 analysis 호출). 워크벤치는 재료만, 예측은 L2. |

> **핵심 정합**: 카탈로그를 `reference/` 가 아니라 `core/dataEntry.py` 에 두는 것이 결정적. frame(조립)이 catalog 를
> 읽어야 하는데 `frame↛reference` 4형제 cross 금지라 reference 면 배선 불가. core(L0)면 frame·providers·scan·L2 모두
> 합법 소비. 게다가 `core/dataEntry.py` 가 이미 그 패턴(DataEntry+notesDispatch+extractor)이라 확장이 정공.

### 2.3 덕지덕지 제거 원칙 (정성 추출)

개념마다 파서를 늘리지 않는다. 카탈로그가 (앵커+타입)을 들고 단일 메커니즘이 처리한다:

```
narrative concept  ──catalog──▶  (anchor, leafType, decoder)
                                        │
panel SPINE(canonical 14챕터·sectionLeaf 수렴, 이미 빌드) ─anchor→ leaf 선택 ─decode→ typed 산출
```

- DART 앵커 = panel 이 이미 빌드하는 SPINE canonical 노드(`canonical/canonicalData.py` + `read.sectionLeafConvergeExpr`).
  즉 `sectionTopic.py` 의 ~200 손regex 를 SPINE 앵커로 수렴. 파서 1개, 카탈로그가 자란다.
- EDGAR 앵커 = SEC Item(`docs/sections/mapper.py`, 이미 체계적).
- 수주잔고·생산능력·가동률 = II.사업의내용의 typed narrative table. `panelTableRows`(이미 빌드) + `tableSchema` 디코드.
  cross-company 는 `salesByProduct` 축 패턴 확장.
- 위험요소·MD&A free-text = 앵커+text leaf 반환, `[EXTERNAL CONTENT]` 마커(ai 층).

---

## 3. 4 기둥 설계 (스키마·영향 파일·함수)

### 기둥 A · 개념 카탈로그 SSOT (`core/extractionCatalog.py` + `core/dataEntry.py` 확장)

단일 매니페스트. 개념 1건 =

```python
ExtractionConcept(
    conceptId,            # "notes.regionalRevenue"
    category,             # financialStatement|note|governance|capital|workforce|debt|segment|narrative|filingMeta
    label,                # "지역별매출"
    dart=Source(canonicalKey="NT_D831150", surface="note", dispatch=("notesDetail","지역별매출")),  # 또는 None
    edgar=Source(concept="us-gaap:...", surface="deraFacts"),  # 또는 HonestNull(reason="US GAAP 미공시")
    axisType,             # single|multiAxis|movement|text
    valueType,            # amount|rate|text
    narrativeAnchor=None, # (chapterCanonical, sectionCore), narrative 개념만
)
```

- 흡수 대상(중복 제거): report `spec.py` apiTypes, `fieldCatalog.py`, `notesStructure.json` note-type, `core/dataEntry.py`.
- ADD: EDGAR 열 + parity 판정 + narrativeAnchor. 기존 12 노트는 dart+edgar 둘 다 채움(EDGAR `_CATEGORY_TAGS` 가
  같은 12 카테고리 미러라 즉시 parity green).
- L0 유지 증명: 문자열·dispatch 키·lambda(제네릭 result 대상)만. provider import 0.

### 기둥 B · coverage census (`tests/audit/extractionCoverageCensus.py` 신규)

카탈로그 매니페스트 × 표본 유니버스 → 개념별 실제 추출 성공률(OOM-safe, 회사당 1 panel·gc).

```
concept                │ category  │ dart% │ edgar% │ parity    │ honestNull   │ status
notes.regionalRevenue  │ note      │ 71%   │ 0%     │ DART-only │ (edgar 검증) │ gap
notes.inventory        │ note      │ 98%   │ 95%    │ parity    │ -            │ ok
workforce.avgSalary    │ workforce │ 89%   │ -      │ DART-only │ US 미공시    │ honestNull-ok
```

- 성공 = 전 개념 status ∈ {ok, honestNull-ok}. Guard Index 처럼 census > pytest 전수.
- baseline 원장(`_baselines/extractionCoverage.json`) = 신규 갭 증가만 회귀로 차단(부채 원장 패턴).

### 기둥 C · 체계적 정성 추출 (`frame/narrative.py` 신규 + DART sectionTopic 수렴)

- `frame/narrative.py::extractNarrative(code, conceptId)`: 카탈로그 narrativeAnchor → SPINE leaf 선택 → 타입 디코드.
- DART: `sectionTopic.py` 의 ~200 regex 를 SPINE canonical 앵커 매핑으로 점진 이관(파서 소멸, 매핑만 카탈로그로).
- EDGAR: 기존 SEC Item 매핑 재사용(무변경).
- typed table(backlog/capacity/utilization): `panelTableRows` + `tableSchema`.
- 신규 파서 신설 0 원칙 강제: `tests/audit` 에 "narrative 추출은 frame/narrative 단일 경로" 가드.

### 기둥 D · 워크벤치 facade (`frame/workbench.py` 신규 + Company·root 표면)

- `frame/workbench.py::assemble(code, categories=None)`: 카탈로그 구동으로 panel·notes·report·narrative 를 category
  트리로 조립(read-only, 런타임 직독, 무bake). ≥2 소비자(analysis·story·credit·ai)라 L1.5 진입 룰 충족.
- `Company.workbench` 프로퍼티 + `dartlab.workbench(code)` root verb 가 assemble 위임.
- 예측: `c.workbench.forecast(...)` 가 analysis.forecast/quant/macro 위임(facade established 패턴, 워크벤치 계산 0).
- **표면 명칭 결정필요**: "workbench" 가 AI Ask 와 충돌. 데이터 조립은 `dossier`(기업 종합 자료철) 권장. 충돌 0·의미
  명확. 최종 명칭은 운영자 콜.

---

## 4. 단계 (한 번에 하나 · 영향/테스트/롤백)

### P0 · 카탈로그 SSOT + census (성공 원장 백본) · 최우선·최저위험

- 영향: `core/extractionCatalog.py`, `core/dataEntry.py`(edgar 열 보강), `tests/audit/extractionCoverageCensus.py`,
  `_baselines/extractionCoverage.json`(신규).
- 추출 변경 0. 통합+측정만. 즉시 진짜 갭 원장 산출.
- 테스트: `tests/providers/mappers/test_extractionCatalog.py`(스키마·parity 불변식), census smoke(표본 20사).
- 롤백: 순수 additive. 파일 삭제로 원복. 런타임 경로 무변경.

### P1 · 고가치 노트 갭 충전 (양 provider)

- 지역별매출(NT_D831150)·판관비(NT_D834310)·종업원급여(NT_D834480)·금융손익(NT_D834330)·특수관계자(NT_D818000)·
  법인세(NT_D835110). 각 registry+extractor(dart), edgar 대응(DERA/XBRL) 또는 honestNull.
- `_attempts/` 데모 선행(졸업 게이트) → 9섹션 docstring → 본진. census green 확인.
- 롤백: 개념별 registry entry 제거(격리).

### P2 · 정성 추출 체계화 (덕지덕지 제거)

- `frame/narrative.py` + DART sectionTopic 를 SPINE 앵커로 점진 이관. backlog/capacity/utilization typed table.
- EDGAR 서술노트 ~20 을 DART parity 로(DART 공시분만, 나머지 honestNull).
- 테스트: 앵커 매핑 불변식 + 무손실(char-parity) + 단일경로 가드.
- 롤백: sectionTopic 병행 유지(신경로 실패시 구경로 fallback), 이관 완료 후 구regex 제거.

### P3 · 워크벤치 facade

- `frame/workbench.py` + `Company.workbench`/`dartlab.workbench` + 예측 위임. Skill OS `engines.company`·신규 표면 갱신.
- 테스트: assemble category 트리·frozen surface·L1.5 진입룰(≥2 소비자) 미러.
- 롤백: facade 프로퍼티 제거(하위 무변경).

---

## 5. 이중 평가 + 위험

**개발자**: 엔진 신설 0(core seed·frame 헌장·기존 추출 재사용), 무bake 유지, 4계층·frame↛reference 정합 증명됨.
breaking 0(전부 additive·frozen surface 보존). 위험 = (a) census 전종목 OOM 은 회사당 1 panel·gc·표본 캡으로, (b) sectionTopic
이관 중 회귀는 병행 fallback + char-parity 게이트로, (c) EDGAR parity 과대주장은 honestNull 명문화로 방지.

**PM**: "빼먹을 수 있는 모든 정보 카테고리화 + 성공 TODO 엔진차원"을 카탈로그 매니페스트 + census 원장으로 정확히
충족. P0 가 즉시 진짜 갭을 드러내 ROI·방향 확정. "덕지덕지 없이"를 sectionTopic 수렴으로 구체 타깃. 예측은 L2 위임이라
아키텍처 부채 0. 수주/IPO 등 US 구조부재는 honestNull 로 정직 기록(능력부족 포장 아님).

## 6. 보류·결정 필요 (운영자)

1. **착수 승인 + 시작 단계**: P0(카탈로그+census, 최저위험·성공정의)부터 무중단 실행 권장. 승인?
2. **워크벤치 표면 명칭**: 데이터 조립 facade = `dossier` 권장(AI `workbench` 충돌 회피). 대안 `dataWorkbench`.
3. **카탈로그 범위 1차**: note+financialStatement+report 정형(구조화)부터, narrative 는 P2 로 분리(권장) vs 동시.

## 7. 구현 완료 (2026-07-05, P0~P3 전부)

운영자 승인("정공법으로 구현 완료해라") 후 무중단 정공법 실행. 4 단계 전부 커밋(engine, master).

| 단계 | 산출 | commit | 검증 |
|---|---|---|---|
| P0 | `core/extractionCatalog.py`(개념 64종 SSOT) + `tests/audit/extractionCoverageCensus.py`(성공 원장) + baseline + 미러 테스트 12 | 2ba5cb33a | census rollup parity-ok 33·narrative-P2 11·dartOnly-ok 9·honestNull-ok 5 |
| P1 | 고가치 노트 10종 first-class 이름 접근. `resolveNoteKey` + panel `__call__` 카탈로그 폴백(additive) | fa936f568 | 005930 10종 전부 이름 추출(지역별매출 2·법인세 24·종업원급여 19·특수관계자 27) |
| P2 | `frame/narrative.py` 앵커 구동 단일 메커니즘(덕지덕지 sectionTopic 대체) | c96ea7af8 | 수주 31·생산능력 37·위험 21·경영진단 46·연구개발 17. table-only(backlog) 20 |
| P3 | `frame/workbench.py` 데이터 공동작업대 + root `dartlab.dossier(code)`. 예측 L2 위임 | 80e8dde7c | 조직맵(재무6/6·노트21/23·거버넌스8/8) + 라우팅 추출(배당 612·최대주주 911) |

**아키텍처 결정 실현**: 새 엔진 0. 카탈로그=core(L0), 조립 view=frame(L1.5), 표면=root facade, 예측=L2 위임.
`frame↛reference` 회피로 카탈로그 L0 배치가 정합. Guard Index l0-l15 전 rule PASS(신규 위반 0).

**게이트 전량 green**: ruff·camelCase·core-l0-only·l15-cross-import·publicApiCoverage(dartlab=33)·productSmoke
quick·folderMirror(src↔tests)·cycleScan·providerGate·panel 회귀 5/5. 신규 테스트 22(catalog 13·narrative 4·workbench 5).

**정직 상한(honest-null 기록)**: US 미공시(topPay·수주·신종자본증권 등) + narrative US(SEC Item 별도경로) +
segmentTable 횡단(scan 경로). 능력부족 포장 아니라 원천 구조 차이로 census 원장에 사유 명시.

**후속(별 트랙, 본 PRD 범위 밖)**: EDGAR report-concept census 로컬 측정(HF scan pull) · sectionTopic ~200 regex
의 frame.narrative 완전 이관(현재 additive 병존) · `review` 3종(inventory/investmentProperty/relatedParty)
EDGAR 태그 보강.

**push 상태**: engine 완결·전 게이트 green 이나, 미푸시 history 에 타 세션 블로그·landing(프론트) 커밋이
조상으로 끼어 있어 자동 push 보류(프론트 변경은 운영자 눈검수 필수). 운영자 push 트리거 대기.

## 8. 완전 인벤토리 메커니즘 (2 차 목표: "진심으로 탈탈털기")

운영자 재도전("완벽한가"·"진심으로 탈탈털었나")에 실측으로 답: 카탈로그(78 개념)는 표본 note 패밀리 175 중
33(~19%)만 커버 = 탈탈털기 아님. 근본 원인 = **손 카탈로그(고정 canonicalKey)는 회사별 노트(NT_C_U/NT_S_U)·
임베디드 정형표를 구조적으로 못 담는다.** 정공 = panel 이 이미 보고서 전체를 기록하므로 **자동 전수 열거 + 의미
카탈로그 enrich** 2 층. 전문에이전트 2명(도메인 taxonomy + 아키텍처)과 2 라운드 토론으로 설계.

**산출 (`frame/inventory.py` + `dossier.inventory()/get()/materialize()`, commit 82f295769·afbebb09b):**
- `reportInventory(code)`: **정규화 Panel wide + report** 에서 전 단위 자동 열거. 표준 노트 + 회사별 노트 +
  임베디드 정형 ACLASS(TOT_STK·EMPLOYEE·VOT_STK·SUB_*·INS_*) + 내러티브 섹션 + 재무 5표 + OpenDART apiType.
  각 단위 안정 handle + conceptId 의미 태깅.
- `dossier.get(handle)`: 어떤 단위든 handle 로 추출(panel canonicalKey/native/sectionLeaf + report 라우팅).
- `dossier.materialize()`: board 1회 로드로 전 단위 배치 추출(OOM-safe).

**라운드2 핵심 교정(에이전트 감사)**: ① raw parquet 열거 -> **정규화 wide board 열거**(reader 정규화 재사용,
phantom 중복 제거). ② round-trip 87.8% -> **100%**(206/206, 모든 handle 이 추출로 해소). ③ handle collision 0.
④ 정직 상한 명시: cover-to-cover 100% 아님. **panel+report BUILD 포착분·unit 입도·KR**. 이미지 바이너리·
cover 구조메타·해소된 cross-ref·multiaxis cell 분해는 상한 밖.

**실측(005930)**: 206 단위(form 39·note 74·narrative 62·statement 5·report 26), enrich 95/206. round-trip
머신 게이트 `test_inventory_roundtrip`(모든 handle non-empty + collision 0). Guard Index l0-l15 PASS.

**정직 잔여(Tier-2, 후속 커밋)**: census 를 note+apiType 외 narrative/table 단위까지 열거하도록 확장(완전성
*측정*을 인벤토리 수준으로), 시총·섹터·era 층화. 인벤토리 *메커니즘* 자체는 완결(전 단위 열거+추출).
```

## 9. EDGAR 동급 + 전 종목 완전성 census (2026-07-05, 운영자 "edgar도 다했나"·"모든 종목 눈으로 훑어라")

운영자 재도전에 실측으로 답: 이전 인벤토리는 KR 전용이고 US 는 얇은 edgar panel(재무 5표 + 회사별 편차 큰 raw
narrative)만 잡아 동급 아니었다. 원인 = US 보고서 본문(SEC Item 27+11)은 별도 표면 `docs/sections` 에 있는데
inventory 가 안 읽었고, workbench get 이 dart panel 을 하드코딩해 US 재무제표 추출조차 깨져 있었다.

**전 종목 실측 우선(눈으로 처음부터 끝까지)**: 손 표본 대신 전 우주 survey(2930 KR panel + 7070 US docs) 전수
열거로 실재 unit 을 빈도로 확인. KR note family 531·narrative 936·form 90·table 7880, US SEC Item topic 753.
카탈로그(88 개념)는 head 만 = 생존편향 실체 확인. 전문에이전트 2명(도메인 parity·아키텍처 배선) 2 라운드 토론.

**산출 (commit 16294a54e·2114a56a8):**
- `providers/edgar/docs/sections/topics.py`: topic(form 별 itemId) 라벨 택소노미 SSOT(company 흩어진 dict 이관).
- `providers/edgar/docs/sections/topicUnits.py`: 경량 열거기(topic 컬럼만 projection, 본문 무접촉, OOM 안전).
- `frame/inventory.py`: US 는 `_itemUnits`(docs Item) + 재무 5표. handle 을 데이터에서 열거(고정 dict 아님)라
  round-trip by construction. `frame/workbench.py`: `_loadBoard` dart/edgar 스위치 SSOT + item handle sections slice.
- `core/extractionCatalog.py`: EDGAR Item first-class(28 category map + reverse index + US 전용 8 edgarOnly) +
  `edgarItemCoverage`(US side 대칭 측정) + 실측 고빈도 신규 노트 2. `tests/audit/inventoryUniverseCensus.py`:
  전 종목 unit 전수 census(2-tier 완전성 measured, baseline 부채원장).

**2-tier 완전성 정의(도메인 감사)**: Tier A mechanical = 우주 전 unit 열거·round-trip 100%(KR 9437 distinct·US
753 topic). Tier B curated head = 고빈도 표준만 카탈로그(≥80% mandatory·30~80% 재량·<30% inventory-only).
완전 = (Tier A 100%, Tier B head) + 잔여 tail 명시. 손 카탈로그 100% 아님(그건 덕지덕지·불가능).

**실측**: AAPL US 인벤토리 39(item 34 + 재무 5), round-trip 34/34·collision 0·handle form-namespaced.
KR 005930 206 무회귀. Guard Index l0-l15 PASS. 신규 테스트: test_topics·test_topicUnits·US round-trip 게이트.

**정직 잔여(후속)**: ① US narrative `extract(conceptId)` 는 None(topic-handle 경로가 US 추출 정본, 아키텍트
후속 판정). ② 20-F Item 택소노미 미카탈로그(census 에 tail 로 정직 노출, ~1216 filer). ③ 변종 노트 코드
(재무위험관리 D82238 vs D82239 등 동일개념 다른코드)는 mechanism 이 열거하되 census 에 미카탈로그로 노출(2-tier).
```
