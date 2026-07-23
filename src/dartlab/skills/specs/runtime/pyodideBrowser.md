---
id: runtime.pyodideBrowser
title: Pyodide / Web AI 실행 범위
kind: curated
scope: builtin
status: observed
category: runtime
purpose: 브라우저의 pyproc machine에서 가능한 DartLab 실행 범위와 성능, 영속성, 격리 제한을 구분한다.
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
  - 브라우저 런타임 capability 판정
toolRefs:
  - search_reference
  - InspectDataset
requiredEvidence:
  - runtimeCompatibility
  - dataset
  - executionRef
  - sourceRef
  - browserSmoke
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
      - pyproc durable history와 process pool은 worker loader 계약이 검증될 때까지 비활성이다.
      - COOP/COEP가 없으면 기본 셀은 실행되지만 soft interrupt와 process 기능은 사용할 수 없다.
failureModes:
  - 서버 전용 skill을 브라우저에서 가능하다고 말함
  - Pyodide가 지연 import의 C 확장 의존성을 자동 발견한다고 가정함
  - SharedArrayBuffer가 없는 일반 페이지에서 기본 machine 부팅까지 막음
  - pyproc 0.x patch를 하위 호환으로 간주하고 게이트 없이 올림
forbidden:
  - Pyodide 가능 여부 허위 단정
  - 블로그를 열기만 했는데 Python 또는 데이터 다운로드 시작
  - durable history와 process 기능을 capability 확인 없이 노출
examples:
  - 파이오디드에서 바로 가능한 분석 뭐가 있나
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-07-23"
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

## DartLab 웹 실행 계약

- 블로그의 `dartlab 이야기` Python 코드펜스는 페이지가 열리면 즉시 편집 가능한 셀로 보인다.
- 페이지 진입만으로 Python, wheel, 데이터를 받지 않는다. 실행 버튼 클릭이나 명시적 hover 같은 사용자 의도 뒤에만 공용 worker를 준비한다.
- 블로그 셀, 브라우저 노트북, 플레이그라운드는 한 `WorkerEngine`과 한 pyproc machine을 공유한다. 별도 main-thread Pyodide를 만들지 않는다.
- 블로그 글을 전체 화면으로 투영한 `post:<slug>` 노트북은 기본 `sequential`, `autoRun: false`다. 일반 브라우저 노트북만 기본 reactive 자동 실행을 사용한다.
- 블로그 셀에서 만든 Python 전역은 전체 화면 노트북의 첫 실행 전에 새 machine으로 격리한다. 저장된 옛 글 노트북의 reactive 중복 정의 오류는 로드 시 제거하되 코드와 정상 출력은 보존한다.
- 런타임 버전 정본은 `landing/runtime-manifest.json`이다. 브라우저와 Node 게이트가 같은 pyproc, Pyodide, DartLab exact pin을 읽고 캐시 namespace를 만든다.
- `import dartlab`을 실행하기 전에 `lxml`, `numpy`, `polars`, `pyarrow`를 Pyodide 배포판에서 명시적으로 적재하고 DartLab exact wheel을 설치한다. 지연 import만 믿지 않는다.
- 기본 실행, 파일, 출력, 환경 진단은 pyproc machine 공개 계약을 쓴다. `runtime.raw`는 ASGI 안정화 폴백에만 허용한다.

## capability 경계

| 기능 | 현재 계약 |
|---|---|
| 기본 Python 셀 | 모든 현대 브라우저에서 지원 |
| soft interrupt | `crossOriginIsolated`와 `SharedArrayBuffer`가 있을 때만 지원 |
| OPFS workspace | 지원 시 notebook별 mount, Web Lock 단독 writer |
| core와 wheel 캐시 | OPFS 지원 시 사용, 버전별 최근 2세대 유지, 사용량 90% 이상이면 우회 |
| checkpoint | pyproc machine history의 휘발성 branching tree |
| durable history | worker deterministic replay loader 검증 전 비활성 |
| process pool | worker 자식 loader 검증 전 비활성 |
| browser-as-server | pyproc ASGI가 기본, 손수 ASGI는 한 안정화 주기의 kill-switch |

COOP/COEP가 없다는 이유로 기본 machine 부팅을 실패시키면 안 된다. 이 경우 `interrupt=hard`, `processes=unavailable-worker-loader`처럼 능력만 낮춰서 보고한다.

## 업그레이드 게이트

pyproc은 1.0 전까지 patch도 breaking으로 취급한다. 모든 후보는 다음을 통과하고 사람이 리뷰해야 한다.

1. Node Gate A: root `boot`, exact DartLab 설치, transitive C 확장 import, machine FS, stdout, branching history, ASGI health.
2. Chromium Gate B: 실제 COI와 JSPI 환경, root machine, exact DartLab, branching history, 2-lane process pool.
3. landing `check`, 전체 unit test, production build.
4. 일반 non-COI 블로그에서 초기 무실행, 첫 셀 실행, 편집 후 재실행 수동 smoke.
5. 글 전체 화면 투영에서 초기 무실행, 순차 단일 셀 실행, reactive 전환, 옛 저장본 정규화 smoke.

자동 병합은 금지한다. PR 토큰이 없으면 전체 게이트를 통과한 후보 브랜치와 중복 방지 이슈만 만든다.

