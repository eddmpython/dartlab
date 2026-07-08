# 발명: panel narrative 표 전천후 격자 추출기 ("모든 것은 라벨된 격자")

> 트리거: 운영자 "수주잔고·가동률 회사마다 표가 달라도 전천후 파서를 하드코딩 없이 발명할 수 없나. panel 파케를 완전히 탈탈 털어쓸 방법을 조사하고 창의성을 보태라."
> 상태: 조사 완료 + POC 실증. 2026-07-07. 빌드 승인 대기.

## 뒤집힌 전제 (P2 재판정)

이전 P2 판정("narrative 는 회사별 포맷 상이라 cross-company 수치화 fragile")은 **틀렸다.** 실 데이터를 열어보니 panel 의 narrative 표는 임의 HTML 이 아니라 **DART 편집기 표준 서식 XML** (`<TABLE ACLASS>` · `<THEAD>` · `<TH>사업부문/품목/수주잔고</TH>` · `(단위:백만원)` · COLSPAN/ROWSPAN)이다. 서식이 정부 표준이라 헤더 라벨이 회사간 놀랍도록 일관된다:

- 수주 표 7사 측정: **수주잔고** 6/7 그대로(나머지 "기초계약잔액"·"기말수주잔고" 변형), 수주총액·기납품액·단위(백만원) 표준.
- 가동률 표 7사: 직접 라벨(가동률/평균가동률) 또는 성분(실제가동시간/가동가능시간, 생산실적/생산능력)에서 계산. 서비스사는 정직 gap.

즉 변형은 **작고 유한**해 회사별 하드코딩이 아니라 **성장형 라벨 taxonomy** 로 흡수된다.

## 핵심 발명: narrative 표를 재무 셀과 동일하게 격자화

panel 은 이미 셀을 두 층으로 담는다. (1) 재무·주석 셀 = XBRL 앵커(acode/axisPath) 구조화(CELL_SCHEMA). (2) narrative 표 = raw `<TABLE>` XML 방치. **발명 = narrative 표도 (1)과 동일한 격자로 파싱하고, 시맨틱 앵커를 acode 대신 "한글 헤더 라벨"(성장형 taxonomy 로 해소)로 삼는다.** dartlab 사상 "파서는 하나, 카탈로그가 자란다"를 note 표에서 narrative 표로 확장. 외부 LLM/NLP 아님 = 결정적·감사가능·ref.

### 부품 (전부 범용, 회사무관)

1. **`tableToGrid`**: `<TABLE>` XML 을 COLSPAN/ROWSPAN 확장한 dense 격자로. 멀티행 헤더를 컬럼별 합성라벨로 결합. HTML 표 정규화 표준 알고리즘 1개.
2. **`headerTaxonomy`** (성장형, NOTE_TAXONOMY 형제): 개념 → 동의어 + **계산전략**. `수주잔고 ← {수주잔고, 기말수주잔고, 계약잔액, 기초계약잔액}`, `가동률 ← 직접라벨 OR 실제가동시간/가동가능시간 OR 생산실적/생산능력`. 단위 어휘 `{백만원:1e6, 억원:1e8}`.
3. **`resolveCell`** (confidence gate): 합성헤더에서 개념 컬럼 지목(금액 컬럼 우선, 수량 제외) → 합계행 우선(없으면 데이터 합산) → 단위 환산 → (value, confidence, provenance). 저신뢰·다중후보·단위불명 = **정직 gap(추측 금지)**.
4. **`buildNarrativeMetrics`** (prebuild, buildNotes 형제): 전종목 resolveCell → parquet 횡단. census 커버리지 측정.
5. **scan 축**: `scan("orders")` 확장 또는 신규. 수주잔고·가동률 등 전종목 스크리닝.

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

- **R1 `frame/narrativeGrid`**: tableToGrid + headerTaxonomy + resolveCell(confidence) + sanity. 유닛(합성헤더·colspan·단위·gap) 결정적 테스트.
- **R2 `buildNarrativeMetrics`**: 수주잔고·가동률 2개념 전종목 prebuild + census(커버리지 + 표본 정확도).
- **R3 scan 축 배선**: `scan("orders")` 확장(백로그커버=수주잔고/매출) 또는 신규 축. 계약 테스트.
- **R4 taxonomy 성장**: census gap 상위 회사 헤더 → 동의어 확장, 커버리지 목표(예 수주 있는 회사의 80%+).

## 차별점 (왜 dartlab 발명인가)

- 외부 LLM 아님: 결정적, ref 감사가능, 비용 0, 재현.
- 재무 XBRL 셀과 narrative 셀을 **한 격자 모델로 통합** (panel 을 진짜 뿌리까지).
- fragile 하드코딩 아님: 범용 격자 + 성장 사전 + confidence 게이트. 실패는 정직 gap 으로 드러남.
- P2 매트릭스 relatedParty 는 여전히 원천 비구조(축 없음)라 별개. narrative 표는 서식 구조가 있어 가능.
