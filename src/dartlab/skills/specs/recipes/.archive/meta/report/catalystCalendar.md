---
id: recipes.meta.report.catalystCalendar
title: catalyst 일정 캘린더 (다가오는 정기공시 추론)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 커버리지 종목들의 다가오는 catalyst (정기공시 due · 분기/반기/사업보고서) 일정을 fiscal cycle 추론으로 미리 정리하는 절차. 트리거 — '실적 일정', '다가오는 catalyst', 'catalyst calendar', '정기공시 예정'.
whenToUse:
  - 다가오는 일정
  - catalyst calendar
  - 실적 발표 예정
  - 정기공시 due
  - upcoming events
  - 커버리지 일정
inputs:
  - tickers list
  - horizon_days (default 30)
outputs:
  - tableRef (날짜·종목·이벤트·예상 영향)
  - dateRef (기준일)
  - 한국어 weekly preview 본문
linkedSkills:
  - engines.gather
  - recipes.meta.report.dailyMorningNote
  - recipes.fundamental.disclosure.event
  - engines.company
toolRefs:
  - RunPython
  - EngineCall
requiredEvidence:
  - skillRef
  - executionRef
  - tableRef
  - dateRef
  - sourceRef
expectedOutputs:
  - 향후 N 일 일정 표
  - 종목별 next earnings 추론
  - 한국어 weekly preview
failureModes:
  - confidence LOW 인 추론을 high-confidence 답변처럼 인용
  - horizon_days 무시하고 너무 먼 cycle 까지 답변 (사용자 시야 흐림)
  - 미국 종목 입력 시 capability 가 빈 결과 반환하는데 "데이터 없음" 안내 누락
forbidden:
  - 추정 일정에 정확한 시각 인용 (예 — 5 월 15 일 09 시) — capability 는 due date 까지만
  - AGM·만기·컨센서스 일정처럼 본 capability 가 미지원하는 이벤트를 가짜로 채워 넣기
examples:
  - "다가오는 실적 발표 일정"
  - "향후 30 일 catalyst calendar"
  - "다음 정기공시 due date 추론"
  - "커버리지 종목 catalyst 정리"
procedure:
  - tickers list + horizon_days (default 30) 확정.
  - dartlab.gather("calendar", codes=tickers, horizon_days=horizon_days) 호출 → DataFrame[date, code, eventType, title, source, impactHint, confidence].
  - confidence 별 분류 — HIGH 만 우선 노출, MEDIUM/LOW 는 *추정* 표시.
  - emit_result(table=일정표, date=오늘) → tableRef·dateRef 발급.
  - 본문 — "이번 주 / 다음 주 / 그 후" 시점별 그룹핑 + 가장 임팩트 큰 이벤트 헤드라인.
  - 미국 종목 포함 시 빈 결과 + "P0 KR 정기공시만 지원" 안내.
sourceRefs:
  - dartlab://skills/engines.gather
lastUpdated: '2026-05-13'
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
testUniverse:
  market: KR
  stockCodes:
    - "005930"
visualRefs:
  - "engines.viz.peerMatrix"
  - "engines.viz.tableBackedChart"
---

## 공개 호출 방식

```python
import dartlab

tickers = ["005930", "000660", "035420"]
df = dartlab.gather("calendar", tickers, horizon_days=30)
# df: date, code, eventType, title, source, impactHint, confidence

emit_result(
    table=df.to_dicts(),
    date=str(df["date"].max()) if not df.is_empty() else None,
)
```

## 호출 동작

`gather('calendar')` 가 회사별 disclosure 시계열에서 마지막 정기보고서 → 다음 fiscal cycle due 추론. horizon 안의 이벤트만 반환.

1. tickers + horizon 확정.
2. gather('calendar', codes, horizon_days) — DART API 호출 (각 종목 disclosure 1 회).
3. confidence 별 classification.
4. 본문 — 이번 주 / 다음 주 / 그 후 그룹핑.
5. catalystCalendar 결과는 dailyMorningNote 의 "오늘 주목" 섹션과 연동 가능.

## 대표 반환 형태

- `tableRef` 1 개 — 향후 N 일 일정 (date · code · eventType · title · impactHint · confidence)
- `dateRef` 1 개 — 기준일
- 답변 본문 — 시점별 그룹 + 임팩트 큰 이벤트 헤드라인

## 연계 절차

1. engines.gather — gather('calendar', codes, horizon_days) 호출
2. recipes.meta.report.dailyMorningNote — morning note 의 "오늘 주목" 섹션과 연동
3. recipes.meta.report.thesisTracker — thesis 의 catalyst 영역 갱신
4. recipes.fundamental.disclosure.event — 발생한 이벤트 사후 분석 path

## 한계 (P0)

- 한국 정기공시 (사업·반기·분기) 추론만 지원. AGM·만기·컨센서스·EDGAR 8-K 미포함 (P1+).
- fiscal year ≠ calendar year 인 회사 (소수) 는 추론 정확도 낮음 — capability 가 confidence 로 표시.
- 추론된 due date 는 *예상* — 실제 회사 사정으로 ±3 일 변동 가능.
- US 시장 호출 → 빈 DataFrame + 안내. P1 에서 EDGAR 분기 cycle 추가 예정.

## 외부 본문 가드

본 recipe 는 dartlab internal capability (gather + Company.filings) 만 호출 — sourceType=internal. 외부 컨센서스 사이트 (FactSet/Bloomberg 등) 는 본 capability 가 호출하지 않는다. 사용자가 외부 confirmation 을 WebSearch 로 가져오면 그 결과는 [EXTERNAL CONTENT START/END] 마커로 감싸지고 *2 차 검증* 없이 인용 금지. 상세: `runtime.workbenchEvidenceFlow`.
