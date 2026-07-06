# scan note 횡단 프리빌드 (카탈로그 구동)

> 상태: 진행 중 (2026-07-06 착수). SSOT = 본 폴더. 완료 시 `mainPlan/_done/` 이동.
> 부모 프로젝트: [[panel-extraction-workbench-ssot]] (추출 카탈로그 SSOT). 본 작업은 그 카탈로그를 scan 횡단으로 소비한다.

## 배경 / 문제

추출 카탈로그(`core/extractionCatalog`)는 사업보고서를 78개념까지 뽑는다(note 34, narrative 10, 정형공시·재무표 등). 그런데 scan 프리빌드는 finance 5표 + 정형공시 17 apiType + salesByProduct 만 횡단으로 굽고, **note 34개와 narrative 정량은 오직 `Company.panel(노트명)` 단일종목 경로로만 존재한다.** census상 ~28개 note가 dartCov >= 0.3(전종목 추출 실재)인데 횡단 스크리닝 축이 0개다. "재고 세분 급증 종목", "리스부담 상위", "법인세율 이상치", "판관비 구조" 같은 질문을 scan이 못 받는다.

핵심: scan은 프리빌드 엔진 자체(CLAUDE.md "가공/횡단=scan"). note 횡단을 scan에 추가하는 것은 별도빌드가 아니라 scan이 제 일을 하는 것. 제약은 체계적으로 하는 것뿐.

## 1. 목표 / 범위

**Phase 1 (본 사이클):** 카탈로그 registered 단일축 note 개념을 전종목 횡단으로 굽고 `scan("note", "재고자산")` primitive 축 신설. account/ratio 원자 축과 동형. `readNoteStatement`(단일축 lineitem 정규화 SSOT)를 배치 위임으로 재사용, 추출 재구현 0.

**Phase 2 (별도 사이클, 승인 후):** multiAxis note(세그먼트·특수관계자 축차원) + narrative 정량(가동률·R&D집약도) + 고가치 파생 축 승격 + **퍼블릭 터미널 카드**(화면이라 운영자 눈검수). Phase 1과 분리해 시각 회귀 격리.

## 2. 영향 파일 / 함수

신규:
- `src/dartlab/scan/builders/kr/notes.py` . `buildNotes(verbose)` + `SCAN_NOTE_CONCEPTS` + `extractNoteLong`. 전종목 panel 순회, 회사당 `readNoteStatements` 1회 위임, long 스택, 개념별 batch merge -> `scan/note/{bareName}.parquet`. **full 모드 전용**(annual 노트, 주간 신선도 충분, 증분 시드 데이터손실 회피).
- `src/dartlab/scan/note.py` . `scanNote(conceptId, *, freq)` + `scanNoteList()`. best-effort 다운로드(salesByProduct 패턴, _REQUIRED 미포함). 부재 = 빈 프레임(honest "데이터 없음").
- `tests/scan/test_note.py`, `tests/scan/builders/kr/test_notes.py` (구조 미러).

수정:
- `src/dartlab/providers/dart/panel/cell.py` . `_noteCellsFromPanel`을 `_alignedNoteFrame`(회사당 1회 정렬) + `_noteCellsFromAligned`(노트별 파싱)로 분리. 배치 공개함수 `readNoteStatements` 추가. 기존 소비자(census·_revenueSelect·panel.py) 계약 무변경.
- `src/dartlab/scan/router.py` . `_AXIS_REGISTRY["note"]`(targetParam="conceptId", targetRequired) + aliases(주석/노트).
- `src/dartlab/scan/builders/kr/core.py` . buildScan에 buildNotes(`not incremental` 시) 단계 + `__all__` + results["notes"].
- `tests/scan/test_prebuild_contract.py` . note SSOT 정합(SCAN_NOTE_CONCEPTS ⊆ 카탈로그 registered note).
- `src/dartlab/skills/specs/engines/scan/SKILL.md` . axis 표 note 행 + 회피 + 반환형태.
- `tests/audit/publicApiScenarios.yml` . scan_axes에 note + scenario.

HF 업로드: `_uploadScan`이 `scanDir.rglob("*.parquet")` + `upload_folder` 라 `scan/note/` 하위 자동 업로드. prebuildData.py 무변경.

## 3. 데이터 계약 (스키마)

`scan/note/{bareName}.parquet` long: `stockCode(str), account(str 정규화명), label(str 표시명), period(str YYYY), value(str raw valueRaw)`. account는 wide지만 note는 회사별 하위항목이 이질적이라 long이 정답(컬럼 폭발 회피). value는 readNoteStatement 계약대로 raw(숫자화는 소비자, scanNote가 `valueNum` 파생). scope는 연결 우선 자동 해소(readNoteStatement 기본). `scan/note/`는 기존 `scan/report/`와 별도 dir라 순수 additive.

## 4. 테스트 / 게이트

- 구조 미러(dartlabGuard --scope l0-l15 + test_structureMirror): 신규 src 2모듈 -> tests 미러 2.
- publicApi(publicApiCoverage + productSmoke quick): scan_axes note 등록 + scenario.
- prebuild 계약(test_prebuild_contract): note SSOT 정합.
- census(extractionCoverageCensus): note 커버리지 baseline 무회귀.
- 4계층 lint-imports: scan(L1.5) -> panel.cell(L1) + extractionCatalog(L0) 합법.
- preflight 27 게이트.
- 메모리: 회사당 1 read(정렬) + releaseNativeMemory. buildChanges 동급.

## 5. 롤백 / 리스크 + 이중평가

- 롤백: 신규 파일 삭제 + 수정 revert. `scan/note/` 별도 dir라 기존 24축 0 회귀.
- 리스크: (a) 전종목 순회 = buildChanges 동급, 회사당 1 정렬로 억제 + full 전용. (b) multiAxis note(세그먼트·특수관계자)는 readNoteStatement None -> 파일 미생성(정직 gap, census 기록). (c) best-effort read라 첫 베이크 전 빈 프레임(축 무회귀).
- 개발자 평가: additive, 기존 패턴(buildReport 배치·salesByProduct read) 재사용, 추출 재구현 0(위임), 계약테스트로 SSOT 드리프트 차단.
- PM 평가: 재고·리스·법인세·판관비 횡단 스크리닝 신규 가치 직결, 카탈로그 dogfooding으로 census 정합. 퍼블릭 UI는 Phase 2 격리.

## 진행 원장

- 2026-07-06: 착수. 조사 완료(카탈로그·inventory·scan 빌더·readNoteStatement·프리빌드 배선). 플랜 승인.
- 2026-07-06: Phase 1 구현 완료. 신규 2모듈(scan/note.py·scan/builders/kr/notes.py) + provider 배치함수(readNoteStatements, 회사당 1회 정렬) + router note 축 + buildScan full 단계 + 계약/미러 테스트 + SKILL/manifest. `note/` 는 HF `_uploadScan` rglob 자동 업로드(prebuildData 무변경). SCAN_NOTE_CONCEPTS = 카탈로그 registered 단일축 note 29개(도출).
- 2026-07-06 게이트: 신규 유닛 17 pass · ruff clean · publicApiCoverage OK(scanAxes 25) · dartlabGuard strict l0-l15 PASS(7 rules, 외부 6 게이트, active debt 0 신규위반 0) · productSmoke quick 4 OK.
- 2026-07-06 실측: readNoteStatements("005930")=26/29 노트 추출(재고 5항목x18기간 등) ~2917행, "000660" 26노트 ~3710행. write->read 라운드트립: scanNote("재고자산") 2사 178행 + valueNum 정확 파싱(58,478,593). 3개 미추출 = 다축 matrix(세그먼트·특수관계자 등) Phase 2 대상(정직 gap).
- 잔여(Phase 2, 별도 승인): multiAxis 축차원 + narrative 정량 + 파생축 승격 + 터미널 카드(퍼블릭 UI 눈검수). 첫 실제 베이크는 주간 full cron(PREBUILD_FULL) 시 note/*.parquet 생성 + HF 업로드.
