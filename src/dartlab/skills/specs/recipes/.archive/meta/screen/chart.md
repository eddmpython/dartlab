---
id: recipes.meta.screen.chart
title: 스캔 + 차트 결합 (scan 결과 → table-backed chart)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: scan 으로 후보를 스크리닝한 뒤 그 결과를 table-backed chart 로 시각화하는 절차. UI / 보고서 출력 직전 단계. 트리거 — '스캔 후 차트', 'table-backed chart', '보고서 직전 시각화'.
whenToUse:
  - 스캔 차트
  - 후보 시각화
  - 랭킹 차트
  - 스크리닝 차트
  - scan visualization
  - 후보 chart
linkedSkills:
  - engines.scan
  - engines.viz.tableBackedChart
  - engines.industry
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - artifactRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.priceChart"
  - "engines.viz.tableBackedChart"
visualGuidance:
  - "가격·수급 반응은 engines.viz.priceChart로만 그리며 OHLCV 기간·벤치마크·latestAsOf가 맞지 않으면 본문 차트로 쓰지 않는다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."

forbidden:
  - chart 는 항상 table 뒷받침 — 단일값 chart 금지.
  - 차트 axis label / 단위 명시 없이 시각화 금지.
  - 상위 N 추출 기준 (CAGR / score) 명시 없이 시각화 금지.
  - 결손값 (None) 0 으로 채워 chart 금지 — 결손은 결손으로 표시.
failureModes:
  - 상위 N 의 sample size 통계 의미 부족 (N < 5)
  - chart axis 의 시간 (분기 vs 연간) 차이로 시계열 왜곡
  - 색상 / 마커 분류 (산업별 / size 별) 누락
  - 단위 (백만원 vs 조 vs %) 혼용 차트
  - 절대값 chart vs 변화율 chart 의미 차이 무시
examples:
  - 매출 CAGR 상위 10 종목 bar chart
  - 수익성 scan 결과 시각화
  - 산업별 색상 분류 chart
  - 시계열 + scan 결합 chart
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
---

## 공개 호출 방식

```python
import dartlab

candidates = dartlab.scan("growth")
top10 = candidates.head(10)
# table-backed chart 로 시각화 (viz 엔진)
# 차트 렌더는 공개 호출 계약이 아니다. CompileVisual 도구 또는 내부 viz generator 가 맡는다.
chart_input = top10.select(["종목명", "매출CAGR"])
```

## 호출 동작

scan 결과 (~2000 종목) 에서 상위 N 추출 → table-backed chart 로 시각화 (artifact 저장).

1. scan(axis) — 전종목 스코어
2. crossSectionStockScreen — 매출 규모·기간 필터
3. 상위 10~20 추출
4. viz.tableBackedChart — chart 생성 + artifactRef 저장

## 대표 반환 형태

- `tableRef` 1 (scan + 필터 결과)
- `artifactRef` 1 (chart 파일)
- 답변 본문: chart 미리보기 + 상위 N 행 markdown table

## 연계 절차

1. engines.scan — 전종목 스코어
2. engines.scan — 매출 규모·기간 필터
3. engines.viz.tableBackedChart — chart 생성

## 기본 검증

- chart 는 항상 table 뒷받침 — 단일값 chart X.
- 차트 axis label + 단위 명시.
- 상위 N 추출 기준 (CAGR / score) 명시.
