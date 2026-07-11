# 00. Product Vision - 브라우저가 dartlab 서버다

상태: 비전 v0.1 (2026-07-11)
범위: 문제 정의, 왜 dartlab 에 맞나, codaro 3발명 중 채택 근거, 성공/실패 기준.

---

## 1. 문제 정의

dartlab 은 이미 두 실행 표면을 갖는다.

1. **브라우저 노트북** - pyodide 웹워커(`pyodideWorker.ts`)가 셀 코드를 execute. dartlab 이야기 블로그 실행셀도 같은 커널.
2. **로컬 서버(:8400)** - FastAPI(`src/dartlab/server`, 395 엔드포인트). 터미널의 무거운/라이브/AI 데이터.

두 표면이 **데이터를 얻는 길이 서로 다르다.** 노트북은 pyodide 안 dartlab 직호출, 터미널은 HF 직독 또는 :8400 FastAPI. 그래서 같은 "005930 손익계산서" 를 세 경로가 각자 만든다. dartlab 의 명시 목표는 "터미널 :8400 없이 떠야 정상"(CLAUDE.md, [[feedback_terminal_hf_ssot_local_compute]])인데, 무거운 계산 엔드포인트는 아직 :8400 에 묶여 있다.

## 2. 발명: 한 커널, 두 인터페이스

codaro 의 재프레임을 dartlab 에 적용한다.

> 로컬 서버의 본질은 TCP 소켓이 아니라 요청/응답 인터페이스(ASGI)다. dartlab 의 FastAPI 를
> pyodide 안에서 돌리고 Service Worker 가 페이지 fetch 를 그 앱으로 넘기면, 페이지 입장에서
> 백엔드 없는 로컬 dartlab 서버가 된다.

핵심은 **커널을 두 개 만들지 않는 것**이다. 노트북 execute 가 쓰는 pyodide 워커가 FastAPI 앱도 품는다. 노트북은 postMessage(execute), 데이터 API 는 fetch -> SW -> 같은 워커의 ASGI dispatch. **실행 SSOT 는 커널 하나**이고 인터페이스가 둘이다.

이것이 dartlab 에 주는 것: 터미널도 노트북도 dartlab 이야기도, 무거운 데이터를 얻을 때 `:8400` 이든 브라우저든 **같은 fetch 계약**을 쓴다. 순수 데이터 계산 엔드포인트에서 백엔드가 소멸한다.

## 3. 왜 dartlab 이 할 수 있나 (검증된 자산)

| 자산 | 실체 | 왜 결정적인가 |
|---|---|---|
| 실제 FastAPI 서버 | `src/dartlab/server` 395 엔드포인트 | 브라우저용 새 API 를 짜지 않는다. 있는 서버 코드를 pyodide 에 올린다. |
| pyodide 커널 | `pyodideWorker.ts` (execute·warm·파일·완성) | FastAPI 를 품을 인터프리터가 이미 워커에 있다. 셀 실행과 한 커널. |
| dartlab 브라우저 동작 | wheel 0.10.8, panel·scan·analysis·credit·story 실측 PASS | 엔드포인트가 부를 dartlab 이 이미 브라우저에서 돈다. |
| SW 존재 | `landing/src/service-worker.ts` | fetch 가로채기 지점이 이미 있다. /pyapi/* 라우팅만 추가. |
| pydantic-core wasm | pyodide 0.27.5 lockfile 에 실재 | FastAPI 의 유일한 네이티브 의존이 브라우저에 있다. fastapi/starlette 는 순수휠. |

## 4. codaro 3발명 중 이것만 채택 (근거)

codaro-anywhere 는 "로컬급 브라우저" 발명 셋을 낸다. dartlab 접목 실측 결과.

- **채택: browser-as-server.** dartlab FastAPI 가 브라우저에서 진짜 데이터 서빙(엔드투엔드 PASS). 로컬 엔진 불필요, 순수 브라우저. dartlab 목표와 정합.
- **기각: 빌린 소켓 브리지.** 로컬 WS<->TCP 프록시/엔진이 필수. dartlab 은 상주 로컬 엔진이 없어 전제 붕괴.
- **기각: 힙 스냅샷 웜스타트.** polars 로드 후 스냅샷은 hiwire 참조로 막힘(제 실측 + codaro 동일). 무거운 패키지 스냅샷 자체가 불가.

## 5. 정체성 정합

- **실행 SSOT = pyodide 커널 하나.** browser-as-server 는 그 커널에 얹는 데이터 인터페이스이지 노트북 실행 경로가 아니다. local-first 를 훼손하지 않고 증명한다: "브라우저는 화면과 서버, 진실은 한 커널."
- **터미널 :8400 없이** 의 물리적 완성. 순수 데이터 엔드포인트를 브라우저가 직접 서빙.
- 계약 불변: 공개 호출계약은 여전히 엔진명뿐([[feedback_public_contract_only]]). browser-as-server 는 그 계약을 HTTP 로 노출하는 배송 계층일 뿐 새 계약이 아니다.

## 6. 성공/실패 기준

**성공 (v1):**
1. dartlab 이야기 페이지 또는 노트북에서 표준 `fetch('/pyapi/company/{code}/panel/{topic}')` 가 브라우저 안 dartlab FastAPI 로 200 + 실제 데이터를 돌려준다.
2. 그 FastAPI 가 노트북 execute 와 **같은 pyodide 워커 커널**을 쓴다(두 커널 아님, 콜드스타트·메모리 1배).
3. 노트북 execute·스트리밍·위젯이 회귀 없이 그대로 동작(browser-as-server 가 얹혀도 워커 경로 불변).
4. 콜드스타트에서 fastapi 추가비용이 2초 이내(실측 1.6s)이고, 프리워밍/precache 로 체감 은닉.

**실패로 간주 (중단 트리거):**
- 노트북 execute 가 browser-as-server 배선으로 회귀(느려지거나 위젯·스트리밍 깨짐).
- FastAPI 를 위해 별도 pyodide 커널이 떠서 콜드스타트·메모리가 2배가 되는 경우.
- 데이터 엔드포인트가 sync def 스레드풀로 `can't start new thread` 를 못 피하는 경우(async 강제 실패).
