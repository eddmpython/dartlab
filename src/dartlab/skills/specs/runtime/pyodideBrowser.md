---
id: runtime.pyodideBrowser
title: Pyodide / Web AI 실행 범위
kind: curated
scope: builtin
status: unverified
category: runtime
purpose: 브라우저에서 가능한 DartLab skill과 제한을 구분한다.
whenToUse:
  - 파이오디드에서 가능한 분석
  - 웹 AI에서 바로 실행 가능한 기능
  - HuggingFace prebuilt 데이터 기반 분석
inputs:
  - Pyodide runtime
  - HF snapshot 또는 업로드 파일
outputs:
  - supported/limited/unsupported 판정
  - 필요한 데이터 원천
toolRefs:
  - search_reference
  - InspectDataset
requiredEvidence:
  - runtimeCompatibility
  - dataset
  - executionRef
  - sourceRef
expectedOutputs:
  - runtime limits
  - available skill list
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
    dataSources:
      - HuggingFace dartlab-data snapshot
      - browser uploaded parquet/csv
    limitations:
      - live KRX/DART/OpenAI OAuth 호출은 브라우저에서 제한된다.
failureModes:
  - 서버 전용 skill을 브라우저에서 가능하다고 말함
forbidden:
  - Pyodide 가능 여부 허위 단정
examples:
  - 파이오디드에서 바로 가능한 분석 뭐가 있나
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-07-09"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 절차

- skill search 결과의 `runtimeCompatibility.pyodide.status`를 먼저 확인한다.
- `supported`는 브라우저 내 파일 또는 자동 lazy 로드 데이터로 바로 실행할 수 있다.
- `limited`는 HF snapshot, 업로드 파일, prebuilt parquet 같은 제한 조건을 함께 표시한다.
- `unsupported`는 로컬 Python 또는 서버 ask 경로를 안내한다.
- 브라우저에서 말하는 최신성은 live API가 아니라 사용한 snapshot의 asOf 기준으로만 표현한다.

