---
id: runtime.pyodide
title: Pyodide
kind: curated
scope: builtin
status: observed
category: runtime
purpose: Pyodide 실행 환경의 제약, 시작 절차, 검증 기준을 Skill OS에서 확인한다.
whenToUse:
  - Pyodide
  - pyodide
  - 1. 호출 단계. `Company` 로 바로 간다 (prefetch 없이, 데이터는 첫 접근 시 lazy fetch)
  - 2. 아키텍처 — 설치·데이터·실행 3 층으로 간다
  - 3. polars WASM 제약 — pyarrow 경유로 우회한다
  - 4. pyodide 분기 패턴 — `sys.platform == "emscripten"` 로 체크한다
  - 수정된 파일
inputs:
  - 작업 목적
  - 대상 엔진 또는 실행 환경
  - 검증 범위
outputs:
  - selected skill
  - capability/docstring handoff
  - verification gate
capabilityRefs: []
toolRefs:
  - search_reference
knowledgeRefs:
  - start.dartlabSkillOs
sourceRefs:
  - dartlab://skills/runtime.pyodide
procedure:
  - 1. 호출 단계. `Company` 로 바로 간다 (prefetch 없이, 데이터는 첫 접근 시 lazy fetch) 기준을 확인한다.
  - 2. 아키텍처 — 설치·데이터·실행 3 층으로 간다 기준을 확인한다.
  - 3. polars WASM 제약 — pyarrow 경유로 우회한다 기준을 확인한다.
  - 4. pyodide 분기 패턴 — `sys.platform == "emscripten"` 로 체크한다 기준을 확인한다.
  - 수정된 파일 기준을 확인한다.
  - 프리빌드 — `dart/scan/finance-lite.parquet` (~18MB, 30 계정, 2022 년 ~ 분기).
  - 다운로드 — `loader.js::loadScanLite(py)` 또는 파이썬 측 `dartlab.scan(...)` 첫 호출 시 자동.
  - 내부 구현 — `scanAccount._scanAccountFromMerged` 가 `_IS_PYODIDE` 분기에서 `pyarrow.parquet.read_table` + `pl.from_arrow` 로 전환 (polars `scan_parquet` 미지원 우회).
  - SSOT 계정 리스트 — `src/dartlab/scan/_helpers.py::LITE_ACCOUNTS`.
requiredEvidence:
  - skillRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 작업 경로
  - 확인한 근거
  - 검증 결과
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
    notes: []
failureModes:
  - Skill OS 검색 없이 과거 문서 경로를 직접 찾음
  - API schema를 skill 본문에 중복해 docstring/capability와 어긋남
  - 검증 게이트 없이 변경 또는 답변을 완료 처리함
forbidden:
  - 삭제된 운영 문서 경로를 공식 진입점으로 안내하지 않는다.
  - 공개 호출 방식, 대표 반환 형태, 오류/제한 동작을 skill과 불일치한 채 방치하지 않는다.
examples:
  - Pyodide 규칙 확인
  - pyodide 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: pyodide
  format: markdown
lastUpdated: '2026-07-09'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## Skill OS 흡수 규칙

- 이 skill이 공식 진입점이다. 삭제된 운영 문서 경로를 다시 안내하지 않는다.
- 공개 호출 방식과 대표 반환 형태는 skill에서 확인하고, 세부 필드는 capability/docstring으로 검산한다.
- 분석이나 변경 결과는 ref, 실행 로그, 테스트 결과로 검증한다.

## 실행 순서

- 1. 호출 단계. `Company` 로 바로 간다 (prefetch 없이, 데이터는 첫 접근 시 lazy fetch) 기준을 확인한다.
- 2. 아키텍처 — 설치·데이터·실행 3 층으로 간다 기준을 확인한다.
- 3. polars WASM 제약 — pyarrow 경유로 우회한다 기준을 확인한다.
- 4. pyodide 분기 패턴 — `sys.platform == "emscripten"` 로 체크한다 기준을 확인한다.
- 수정된 파일 기준을 확인한다.
- 프리빌드 — `dart/scan/finance-lite.parquet` (~18MB, 30 계정, 2022 년 ~ 분기).
- 다운로드 — `loader.js::loadScanLite(py)` 또는 파이썬 측 `dartlab.scan(...)` 첫 호출 시 자동.
- 내부 구현 — `scanAccount._scanAccountFromMerged` 가 `_IS_PYODIDE` 분기에서 `pyarrow.parquet.read_table` + `pl.from_arrow` 로 전환 (polars `scan_parquet` 미지원 우회).
- SSOT 계정 리스트 — `src/dartlab/scan/_helpers.py::LITE_ACCOUNTS`.

