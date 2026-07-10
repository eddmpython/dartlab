---
id: runtime.python
title: RunPython 신뢰 경계
kind: curated
scope: builtin
status: observed
category: runtime
purpose: dartlab RunPython 도구 안에서 무엇이 허용되고 무엇이 차단되는지 명시한다. 외부 클라이언트가 attach 한 상태에서도 신뢰 경계가 회색 지대 없이 분명하도록 SSOT.
whenToUse:
  - RunPython 으로 분석 코드 작성 전 무엇이 가능한지 확인
  - 외부 클라이언트로 dartlab MCP 사용 시 신뢰 경계 파악
  - sandbox 가 차단한 호출 메시지 받았을 때 대안 찾기
inputs:
  - 작성할 코드의 의도
  - 파일 쓰기 필요 여부
  - 외부 명령 실행 필요 여부
outputs:
  - 허용 / 차단 분류
  - 우회 시도 시 에러 메시지
  - 대안 도구 안내
capabilityRefs: []
toolRefs:
  - RunPython
  - SaveArtifact
knowledgeRefs:
  - runtime.mcp
  - operation.testing
sourceRefs:
  - dartlab://skills/runtime.python
procedure:
  - 분석 의도를 1 문장으로 정의한다.
  - 허용 표면 안에서 코드를 작성한다 (dartlab API · polars · pathlib 읽기 · 안전 경로 쓰기).
  - 차단된 호출이 필요하면 해당 도구 (SaveArtifact 등) 로 대체한다.
  - 차단 에러를 받으면 메시지의 안내에 따라 코드를 수정한다.
requiredEvidence:
  - executionRef
  - sourceRef
expectedOutputs:
  - emit_result 호출 결과
  - 차단 시 PermissionError 메시지
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
    status: limited
    notes:
      - Pyodide 는 별도 sandbox — os/subprocess/socket 자체가 없거나 다른 의미.
failureModes:
  - shell 명령으로 분석을 시도해 차단됨 (대안: dartlab API)
  - 임의 경로에 파일 쓰기 시도해 차단됨 (대안: SaveArtifact 또는 ~/.dartlab/)
  - import 자체가 막힌다고 오인 (실제로는 호출 시점에만 차단)
forbidden:
  - destructive shell 호출을 우회하려고 __import__ 사용 금지 — 동일 차단.
  - 안전 경로 외 파일 쓰기를 시도하지 않는다 — SaveArtifact 도구 권장.
examples:
  - dartlab.Company('005930').panel 실행
  - polars 로 dataframe 가공
  - tempfile.gettempdir() 안에 임시 결과 저장
source:
  type: handcrafted
  format: markdown
lastUpdated: '2026-05-09'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 신뢰 모델

dartlab 의 RunPython 은 *단일 사용자 로컬 신뢰* 환경을 가정한다. 코드를 작성하는 주체는 (a) 사용자 자신이거나, (b) 사용자가 신뢰해서 attach 한 LLM 클라이언트다. sandbox 의 목적은 *완전 격리* 가 아니라 *우발적/실수성 destructive 호출 차단* + *신뢰 경계 명시* 다.

운영 환경이 외부 공유 (팀/공개 attach) 로 확장되면 본 신뢰 모델은 재검토 필요하다.

## 허용

- **dartlab API 전체** — `dartlab.Company`, `dartlab.scan`, `dartlab.macro`, `dartlab.analysis`, `dartlab.story`, `dartlab.gather`, `dartlab.quant`, `dartlab.industry` 등.
- **polars 전체** — `pl.DataFrame`, `pl.Series`, lazy frames, joins, window functions.
- **pathlib 읽기** — `Path.read_text`, `Path.exists`, `Path.glob` 등.
- **read mode `open`** — 어디든 읽기 가능. 외부 본문 분석 use case 보존.
- **read-only os 모듈** — `os.path.expanduser`, `os.path.join`, `os.environ.get`, `os.getcwd`, `os.listdir` 등. 호출 가능 attr 만 차단되며 path/environ 은 통과.
- **import 자체** — `import os`, `import subprocess` 모두 OK. 차단은 *호출 시점* 만.
- **안전 경로 쓰기** — 다음 prefix 안의 파일 쓰기 통과:
  - `~/.dartlab/` (사용자 dartlab home)
  - `./tmp/` (현재 작업 폴더 안)
  - `/tmp/` (Unix 임시)
  - `tempfile.gettempdir()` (OS 표준 임시 — Windows `%TEMP%`)

## 차단

| 호출 | 사유 | 대안 |
|---|---|---|
| `os.system(...)` / `os.popen(...)` | shell 호출 | dartlab API 또는 polars |
| `os.exec*(...)` / `os.spawn*(...)` | 프로세스 교체/생성 | 사용처 없음 |
| `os.kill(...)` | 프로세스 종료 | 사용처 없음 |
| `os.remove/unlink/rmdir/removedirs(...)` | 파일/디렉토리 삭제 | 사용처 없음 — 분석은 read-only |
| `subprocess.run/Popen/call/check_*/get*(...)` | 외부 프로세스 실행 | dartlab API 또는 SaveArtifact |
| `shutil.rmtree/move/copytree(...)` | 대량 파일 조작 | 사용처 없음 |
| `socket.socket/create_connection/create_server(...)` | raw 소켓 | `requests`/`httpx` 같은 high-level |
| `__import__('os'\|'subprocess'\|'shutil'\|'socket')` | 우회 시도 | 동일 차단 |
| `from os import system` 등 | 직접 import | 동일 차단 |
| 안전 경로 외 `open(path, mode=write)` | 임의 경로 쓰기 | `SaveArtifact` 도구 또는 ~/.dartlab/ |

차단 시 `PermissionError` 메시지에 *원인 + 대안* 포함.

## 우회 시도 시 에러 메시지 예

```
PermissionError: RunPython: 'os.system(...)' 호출 차단. 외부 클라이언트 안전을 위해
destructive / shell 호출 비허용. 분석은 dartlab API · polars · pathlib (읽기) ·
~/.dartlab/ · /tmp/ 안의 안전 쓰기로.
```

```
PermissionError: RunPython: 파일 쓰기는 안전 경로만 허용 (...). 시도된 경로:
C:\Windows\system_test.ini. 결과 저장은 SaveArtifact 도구 사용 권장.
```

## 구현 위치 — 회귀 가드

- AST 검사: [src/dartlab/ai/tools/runPython_guard.py](file://src/dartlab/ai/tools/runPython_guard.py) `_assertSafeAst`
- 경로 가드: 같은 파일 `_safeOpenFactory` + `_defaultSafeRoots`
- exec 직전 wire: [src/dartlab/ai/tools/runPython.py](file://src/dartlab/ai/tools/runPython.py) `_runner`
- 회귀 테스트: [tests/test_runpython_security.py](file://tests/test_runpython_security.py) — 차단 6 + 허용 7 + 단위 4

## 한계 (sandbox 가 막지 않는 것)

- **CPU/메모리 폭주** — 60 s timeout 만 있음. 큰 dataframe 으로 OOM 가능.
- **네트워크 호출** — `requests`/`httpx` 통한 HTTP 는 허용 (정상 use case 다수).
- **`dartlab` 자체 함수의 부수 효과** — dartlab API 가 disk write 하면 그건 그 API 의 정책.
- **`pickle.loads` 등 위험 deserialize** — block 안 됨. 신뢰된 데이터만 다룰 책임은 LLM/사용자.
