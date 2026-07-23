# 현재 아키텍처

## 실행 흐름

```text
블로그 편집 셀 / 브라우저 노트북 / 플레이그라운드
  -> executionStore 직렬 실행 큐
  -> WorkerEngine
  -> pyodideWorker
  -> pyproc root boot
  -> PyprocMachine
     - run, runAsync
     - fs
     - history
     - runtime packages, stdout, interrupt, OPFS, ASGI
```

페이지가 열릴 때 편집기만 만든다. 실행 버튼 클릭이나 명시적 hover 뒤에 worker를 만들고 machine을 부팅한다. 같은 SPA 세션에서는 모든 Python 표면이 이 singleton을 재사용한다.

## 버전과 의존성

`landing/runtime-manifest.json`이 다음 세 값을 함께 잠근다. 브라우저의 `runtimeManifest.ts`와 Node 게이트가 이 파일을 같이 읽는다.

- pyproc 0.0.10
- Pyodide 0.27.5
- DartLab 0.10.9

`import dartlab`을 감지하면 `lxml`, `numpy`, `polars`, `pyarrow`를 먼저 적재하고 `dartlab==0.10.9`를 설치한다. DartLab의 지연 import는 Pyodide 자동 의존성 탐지가 보지 못하므로 명시 목록이 필요하다.

## 저장과 캐시

- notebook workspace는 OPFS에 mount한다.
- Web Lock으로 notebook별 writer를 하나로 제한한다.
- 설치 요구사항은 `/workspace/.dartlab/requirements.json`에 남겨 복원한다.
- core와 wheel은 버전 조합 namespace에 저장한다.
- 최근 2세대만 유지한다.
- 저장소 사용량이 quota의 90%를 넘으면 캐시 없이 부팅한다.
- Service Worker는 runtime wheel을 다시 캐시하지 않는다. 데이터 응답 캐시는 유지한다.

## history

pyproc가 부팅하며 만드는 `cp0`은 전체 heap 복사 비용이 있으므로 즉시 dispose한다. 사용자가 checkpoint를 만들 때 새 기준을 만든다. 복원 뒤 새 checkpoint를 만들면 기존 미래를 지우지 않고 branch가 된다.

현재 계약은 `branching-volatile`이다. 페이지를 닫아도 복원되는 durable history라고 표현하지 않는다.

## 브라우저 capability

COOP/COEP가 없는 일반 블로그에서도 기본 machine은 떠야 한다. `SharedArrayBuffer`가 없으면 soft interrupt만 내리고 hard interrupt를 쓴다. process pool도 비활성으로 보고한다.

`/pyapi`는 base path를 포함해 Service Worker가 요청한 clientId로 우선 전달한다. clientId를 찾지 못할 때만 visible 또는 focused client를 고른다. worker의 같은 DartLab 커널이 ASGI 응답을 만들고 원래 response headers를 보존한다.

## 소유권

pyproc 소유:

- Pyodide boot
- machine 실행과 FS
- runtime 패키지와 출력
- environment report
- OPFS core와 wheel cache
- branching history
- ASGI 기본 경로

DartLab 소유:

- postMessage 명령과 실행 직렬화
- 셀 출력 포매팅과 widget shim
- DartLab 의존성 목록
- notebook workspace ID와 manifest
- Service Worker client routing
- UI와 capability 표기
- 손수 ASGI 임시 kill-switch
