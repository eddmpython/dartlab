# Panel 주석 추출 SSOT — 개념체계 카탈로그 & 확장 PRD

> 목표(운영자): "panel 파케에서 뺄 수 있는 중요정보를 전수 리스트업하고, 라이브러리 엔진에서 SSOT 로
> 빼낼 수 있는 개념체계를 providers 에 만든다." 데이터 작업대 실측으로 검증.

## 결론 (3줄)

1. **개념체계는 이미 존재한다** — `cellsFromContent`(providers/panel) → `_noteCellsFromPanel`(노트 셀 read)
   → `providers/dart/notes.py`(레지스트리 구동 디스패치) → `core/_entries/notes.py`(의미 레지스트리 11종)
   → `analysis/financial`(타입추출기). 운영자 직관 "**providers 에서**"가 맞다(추출 1차 표면이 거기다).
2. **빠진 건 커버리지** — 표준 IFRS 주석은 회사당 ~32종인데 레지스트리는 11종만, **고가치 ~10종 미등록**.
   전종목 카탈로그 생산기 `scanNotes()`는 **stub(`return {}`)** 이라 notesStructure.json(2,640항목)은 동결.
3. **추출 엔진은 완벽히 작동** — 미등록 노트도 `_noteCellsFromPanel` 로 즉시 빠짐(실측 아래). 확장 = 엔진
   신설이 아니라 **레지스트리+타입추출기+표면** 채우기 + **scanNotes stub 구현**.

## 레이어 지도 (4계층 정합 — "providers 맞지?"의 정확한 답)

| 역할 | 위치 | 상태 |
|---|---|---|
| 원본 XBRL/옛표 → 셀(CELL_SCHEMA: acode·axisPath·label·ctxYear·value) | `providers/dart/panel/build/cell.py::cellsFromContent` | ✅ 완성 (테스트 11/11) |
| 노트가족(NT_) → 셀 read 표면 (aligned long, Q4 deep history) | `providers/dart/panel/cell.py::_noteCellsFromPanel` | ✅ 완성 |
| 노트 디스패치 (레지스트리 → extractor 해소) | `providers/dart/notes.py` | ✅ 구동 (레지스트리 SSOT) |
| **의미 레지스트리 (카탈로그)** — note→label·dispatch·extractor | `core/_entries/notes.py` | ⚠ 11/32 |
| 타입 추출기 (segment 피벗·cost 그룹 등) | `analysis/financial/*` | ⚠ 부분 |
| **전종목 구조 스캐너** (panel→notesStructure.json) | `providers/mappers/scanner.py::scanNotes` | ⛔ **stub** |
| 카탈로그 데이터 | `providers/mappers/mapperData/notesStructure.json` | ⚠ 동결(2,640항목·2,877사·2026-04) |
| 소비 (report/cards/terminal/export) | report·landing·viz | ⚠ cost/segment만 |

→ **추출·스캔 1차 표면 = providers (맞다). 의미 카탈로그 = core 레지스트리. 타입가공 = analysis(L2).**
무bake·런타임 직독(panel.parquet contentRaw read-time 분해, 별 artifact 0) — 기존 사상 그대로.

## 카탈로그 — 표준 IFRS 주석 (SK하이닉스 000660 실측, 32종)

> 코드=정부 canonicalKey(disclosureKey). `_5`/`_S_`=별도, `_C_`=연결. 회사 간 코드 공유(표준 택소노미).

**✅ 레지스트리 등록(11)**: 재고자산(NT_D826380)·매출채권(NT_D822420)·유형자산(NT_D822100)·무형자산
(NT_D823180)·관계기업(NT_D825700)·차입금(NT_D822400)·충당부채(NT_D827570)·주당이익(NT_D838000)·
리스(NT_D832610)·영업부문(NT_D871100)·비용성격별(NT_D834300). (+투자부동산 — SK엔 부재)

**⛔ 미등록 고가치(우선순위순)**:
- **NT_D831150 지역별 매출** — 국내/미국/중국/유럽… (어디서 버나·지역). 실측: 미국 66.9조·중국 19.1조.
- **NT_D834310 판매비와관리비** — 급여·복리후생·지급수수료 등 판관비 분해.
- **NT_D834480 종업원급여** — DBO/사외적립/근무원가 (인건비 깊이).
- **NT_D834330 금융수익·금융비용** — 이자수익/이자비용/외환 (이자부담).
- **NT_D818000 특수관계자 거래** — 거래상대별 매출/매입 (계열 의존도, axisPath=상대사).
- **NT_D827580 우발부채·약정** · **NT_D835110 법인세** · **NT_D834120 주식기준보상** ·
  **NT_D861200/861300 자본·이익잉여금** · **NT_D822430 금융상품 범주별**.

**라인아이템 레벨**: notesStructure.json = 2,640 항목(category·frequency·type[amount/rate/text]) — 단
scanNotes stub 라 재생성 불가(동결 debt).

**⛔ panel NT_* 에 없는 것**: **수주잔고·생산능력/가동률** — 재무주석이 아니라 사업보고서 II.사업의내용
*narrative 텍스트*(panel chapter 행, 비정형). 별도 파서 트랙(report-full-harvest). 확정.

> **narrative 트랙 진행(2026-07-01):** 격자전개(rowspan/colspan) + businessTables(터미널·카드) + 라이브러리
> `panelTableRows` 완료. cross-company `scan("salesByProduct")` 축 추가(prebuild consolidation, 매출및수주
> 표 leaf 합산 → 부문 mix·HHI·다각화등급, 단위-불변). 표준 매출실적 표(매출유형 지문) 회사 약 42% 커버,
> 비표준(현대차·NAVER·은행)은 정직하게 제외. `scan/builders/kr/salesByProduct.py` + `scan/salesByProduct.py`.

## 실측 증거 (데이터 작업대 — `_noteCellsFromPanel`)

- 노트 셀 추출 단위테스트 `tests/providers/dart/panel/build/test_cell.py`·`test_cellSchema.py` = **11/11 통과**.
- SK하이닉스 미등록 노트 라이브 추출:
  - 지역별매출: 121셀·2022~2025·합계 97.1조 (국내1.9/미국66.9/중국19.1/아시아7.2/유럽2.0조).
  - 종업원급여: 157셀 (DBO·PlanAssets 축). 특수관계자: 469셀 (상대사별 axisPath).
- → **추출 엔진 무결. 확장은 등록·가공·표면만.**

## 플랜 (단계 — 엔진-add 게이트 대상, 운영자 승인 후)

- **P0 카탈로그 SSOT 확정** — notesStructure.json 의 note-TYPE 카탈로그(32 표준코드→label·축유형[단일/다축/movement]·
  가치등급) 명문화. core 레지스트리에 미등록 고가치 노트 항목 추가(notesDispatch+extractor). _attempts 데모 선행.
- **P1 `scanNotes` stub 구현** — `providers/mappers/scanner.py`: panel 노트행 → 라인아이템 구조 추출(OOM-safe,
  500종목 gc). scanAll 재가동 → notesStructure.json 재생성. 신규 테스트 `tests/providers/mappers/test_scanner.py`.
- **P2 타입 추출기** — analysis/financial 에 지역별매출·판관비·종업원급여·금융손익·특수관계자 추출기(부문/비용
  동형: axisPath/acode 피벗 → CompositionSeries/표). 각 9섹션 docstring + 미러 테스트.
- **P3 소비 표면** — report ReportPort 확장(noteSeries 형) + 카드 composition 카드 재사용 + 터미널 NotesDashboard.

## 평가

- **개발자**: 엔진 신설 0(기존 cellsFromContent/_noteCellsFromPanel 재사용), 무bake 유지, R1/R2 계층 격리 준수.
  위험=scanNotes 의 2,877종목 스캔 OOM(가드: 회사당 1 panel·gc)·옛era 병합행 phantom(기존 _parseOldNoteTable
  가드 재사용). breaking 0(additive 레지스트리).
- **PM**: "리스트업+개념체계" 목표를 카탈로그+레이어맵+검증+플랜으로 충족. 고가치 ~10노트가 즉시 추출 가능함을
  실증해 ROI 확실. 수주/생산능력은 narrative 라 별 트랙으로 정직 분리. 한-번에-하나로 P0→P3 단계.

## 보류·결정 필요

1. scanNotes 구현 + notesStructure.json 재생성 착수 승인(엔진-add 게이트).
2. P2 추출기 우선순위 — 지역별매출·판관비 먼저(카드/리포트 ROI 최고)?
3. 소비 표면 — report ReportPort 에 노트 확장 vs 카드 직접 `_noteCellsFromPanel` 소비.
