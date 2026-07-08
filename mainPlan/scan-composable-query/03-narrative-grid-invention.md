# 발명: panel narrative 표 전천후 격자 추출기 ("모든 것은 라벨된 격자")

> 트리거: 운영자 "수주잔고·가동률 회사마다 표가 달라도 전천후 파서를 하드코딩 없이 발명할 수 없나. panel 파케를 완전히 탈탈 털어쓸 방법을 조사하고 창의성을 보태라."
> 상태: 조사 완료 + POC 실증. 2026-07-07. 빌드 승인 대기.

## 뒤집힌 전제 (P2 재판정)

이전 P2 판정("narrative 는 회사별 포맷 상이라 cross-company 수치화 fragile")은 **틀렸다.** 실 데이터를 열어보니 panel 의 narrative 표는 임의 HTML 이 아니라 **DART 편집기 표준 서식 XML** (`<TABLE ACLASS>` · `<THEAD>` · `<TH>사업부문/품목/수주잔고</TH>` · `(단위:백만원)` · COLSPAN/ROWSPAN)이다. 서식이 정부 표준이라 헤더 라벨이 회사간 놀랍도록 일관된다:

- 수주 표 7사 측정: **수주잔고** 6/7 그대로(나머지 "기초계약잔액"·"기말수주잔고" 변형), 수주총액·기납품액·단위(백만원) 표준.
- 가동률 표 7사: 직접 라벨(가동률/평균가동률) 또는 성분(실제가동시간/가동가능시간, 생산실적/생산능력)에서 계산. 서비스사는 정직 gap.

즉 변형은 **작고 유한**해 회사별 하드코딩이 아니라 **성장형 라벨 taxonomy** 로 흡수된다.

## 핵심: panel 표 파서 통합 (덕지덕지 정리 + 셀 파싱 완성)

배치 정본 = **panel 이 파서 SSOT, scan 이 프리빌드.** 그리고 panel 표 파싱은 이미 덕지덕지다 (표 건드리는 함수 5~6개, 각자 TR/셀 반복 재구현):
- `build/cell.py`: `_xbrlCellsFromContent`(`<TE ACODE>` 재무 셀) + `_parseOldStatementTable`/`_parseOldNoteTable`(pre-XBRL 구식 표).
- `build/titleRows.py`: `_tableToMarkdown`(colspan/rowspan **보존만**, 렌더링 HTML. 격자로 펼치진 않음).
- `build/leafSplit.py`(text/table 분리) · `refScan/aclassExtractor`(TABLE-GROUP ACLASS 정체) · `walker`.

즉 재무표는 acode 로 셀화, 서술표(수주·가동률)는 raw 방치, 렌더링은 또 따로. **공용 "표 → 펼친 dense 격자 → 의미 셀" primitive 가 없다.** 그래서 발명은 새 파서 추가가 아니라 **그 공용 primitive 하나를 만들고 전부 그 위로 통합**하는 것이다.

### 부품 (panel SSOT, 공용 primitive 위로 통합)

1. **`tableToGrid`** (신규 공용 primitive, panel `build/`): `<TABLE>` XML → COLSPAN/ROWSPAN **확장** dense 격자 (row×col) + 멀티행 헤더 합성라벨. **모든 표 파싱의 단일 기반.** POC 의 `_parseGrid` 를 여기로 승격.
2. **anchor 해소 (격자 위 의미 head, 2 전략)**: 재무/주석 = acode 앵커(기존 정밀 경로 유지, 다운그레이드 금지) · 서술표 = **한글 헤더 앵커** (성장형 `headerTaxonomy`, `NOTE_TAXONOMY` 형제: `수주잔고 ← {수주잔고,기말수주잔고,계약잔액}`, `가동률 ← 직접 OR 실제가동시간/가동가능시간 OR 생산실적/생산능력`).
3. **`readMetric`** (panel `cell.py`, `readNoteStatement` 형제, confidence gate): tableToGrid → 개념 컬럼 지목(금액 우선) → 합계행 우선 → 단위환산 → sanity → (value, confidence, provenance). 저신뢰·다중후보·단위불명·sanity 실패 = **정직 gap**.
4. **`buildNarrativeMetrics`** (scan 프리빌드, `buildNotes` 형제): 전종목 readMetric → parquet 횡단 + census.
5. **scan 축**: `scan("orders")` 확장 또는 신규. 전종목 스크리닝.

**통합 효과**: 표 넣으면서 오히려 덕지덕지가 준다 (격자 엔진 1개, 의미 head 만 다름). 단 렌더링(`_tableToMarkdown`)·재무 acode 경로는 터미널 직결이라 **한 번에 갈아엎지 않는다**: primitive 먼저 신설(무회귀) → 서술표가 첫 소비자 → 기존 경로는 이후 시각/재무 회귀 게이트 두고 조심히 이관.

## POC 실증 (2026-07-07, scratchpad)

`tableToGrid`(colspan 확장) + `수주잔고` taxonomy + 합계행/단위 로직만으로 회사별 코드 0:

| 종목 | 추출 | 검증 |
|---|---|---|
| 042660 한화오션 | 수주잔고 **35.4조** (conf high) | ✅ 합계행 35,374,442 백만원 정확 |
| 272210 한화시스템 | 12.2조 (high) | 타당 |
| 012450 한화에어로 | 116.8조 (high) | 규모 재확인 필요(합산 vs 총계) |
| 064350 현대로템 | **오검(1192조)** | ⚠ 단위 중복선언(백만원+억원)에 억원 오선택 |
| 009540·010620·005930·097520 | 정직 gap | 변형라벨(기초계약잔액)·수주표 없음(정상) |

**POC 가 스스로 증명한 두 가지**: (1) 범용 격자+taxonomy 로 실제 추출된다(한화오션 35.4조 정확). (2) 실패모드(단위 중복·변형라벨·합산오차)가 실재하며 **confidence gate + sanity bound 이 필수**다. 1192조 오검은 "시총·매출 대비 상한" sanity 로 즉시 걸러진다.

## 안전 설계 (조용한 오답 0 = 이 발명의 핵심)

억지 숫자 금지. 추출은 **다음 전부 충족 시에만**: 헤더 강매칭 + 값 셀 유일 + 단위 명확 + 기간 정합 + sanity 통과(예 수주잔고 < 시총x N). 하나라도 미달 = 정직 gap. 그래서 틀린 값 대신 "미추출"이 나온다(missing > wrong). census 가 커버리지 + 표본 정확도(N사 수기 대조)를 측정.

## 자가성장 루프 (dartlab 발명)

census 가 미커버 회사의 **미매칭 헤더를 surface** → 운영자/AI 가 taxonomy 에 동의어 1줄 추가 → 커버리지↑, 게이트가 정확도 유지. 손 하드코딩(회사별 규칙)이 아니라 **개념 사전(회사무관)**이 자란다. 이것이 "탈탈 털어쓰기"의 정공법: 파서 고정, 사전 성장, 도태는 census 측정.

## 로드맵 (승인 후)

- **R1 panel 공용 primitive**: `tableToGrid`(colspan 확장 격자) + `headerTaxonomy` + `readMetric`(confidence + sanity), panel `build/`·`cell.py`. 무회귀 신설(기존 경로 미변경). 유닛(합성헤더·colspan·단위·gap·저신뢰) 결정적 테스트.
- **R2 `buildNarrativeMetrics`**: 수주잔고·가동률 2개념 전종목 prebuild + census(커버리지 + 표본 정확도).
- **R3 scan 축 배선**: `scan("orders")` 확장(백로그커버=수주잔고/매출) 또는 신규 축. 계약 테스트.
- **R4 taxonomy 성장**: census gap 상위 회사 헤더 → 동의어 확장, 커버리지 목표(예 수주 있는 회사의 80%+).

## 구현 완료 (2026-07-07, R1~R3)

- **R1** (commit panel grid): `build/grid.py tableToGrid`(colspan/rowspan 확장 dense 격자, 범용 primitive) + `narrativeMetric.py`(성장형 headerTaxonomy + readMetric/readMetrics + confidence gate + sanity). 유닛 24 + requires_data 3.
- **R2**: `scan/builders/kr/narrativeMetrics.buildNarrativeMetrics`(전종목 프리빌드, buildNotes 형제) + buildScan full 단계 통합.
- **R3**: `scan/narrativeMetric` 축(reader) + router 등록(별칭 수주잔고/백로그/가동률) + publicApiScenarios + mirror 테스트.
- **실측 프리빌드**: `narrativeMetrics.parquet` **1102종목** (backlog high 460 + util high 538 = **998 고신뢰**). `scan("narrativeMetric")` 라이브: 한화에어로 116조·HD조선 82조·삼성 가동률 등. 이전 방치 서술 표를 전종목 격자 추출로 탈탈. 저신뢰/부재는 정직 gap.
- **게이트**: dartlabGuard strict l0-l15 PASS(providerGate 11/11) · publicApiCoverage scanAxes 26 · scan 유닛 303 · productSmoke.
- **잔여(R4, demand-driven)**: taxonomy 성장(census gap 상위 회사 헤더 흡수로 커버리지↑), 지표 추가(생산능력·연구개발비 등), 기존 표 파서(_tableToMarkdown·구식표)를 tableToGrid 로 이관(시각/재무 회귀 게이트 후).

## 차별점 (왜 dartlab 발명인가)

- 외부 LLM 아님: 결정적, ref 감사가능, 비용 0, 재현.
- 재무 XBRL 셀과 narrative 셀을 **한 격자 모델로 통합** (panel 을 진짜 뿌리까지).
- fragile 하드코딩 아님: 범용 격자 + 성장 사전 + confidence 게이트. 실패는 정직 gap 으로 드러남.
- P2 매트릭스 relatedParty 는 여전히 원천 비구조(축 없음)라 별개. narrative 표는 서식 구조가 있어 가능.
