# 02. Phasing and Wiring - dartlab 이야기·노트북 배선 순서

상태: 상세 설계 v0.1 (2026-07-11)
범위: Phase 0~4, 배선 순서, 콜드스타트 완화, 게이트·롤백, 개발자+PM 이중 평가.

---

## Phase 0. 커널 안 FastAPI (기반, 배선 없음)

`pyodideWorker.ts` 에 `case 'pyapi'` + `ensureServer()` 추가. fastapi lazy micropip + `browserApi.py`(async 데이터 라우터) 마운트 + ASGI 직접 dispatch. `workerEngine.ts` 에 `serveApi`, `executionEngine.ts` 인터페이스 확장.

- 게이트: 워커 유닛 테스트(playwright)로 `serveApi('GET','/company/005930/panel/IS')` -> 200 실제 데이터. 노트북 execute 회귀 0(기존 셀 테스트 그대로 PASS).
- 롤백: `case 'pyapi'` 제거 = 노트북 무영향(추가만 했으므로).

## Phase 1. Service Worker /pyapi 라우팅 + 페이지 브리지

`service-worker.ts` 에 `/pyapi/*` 가로채기 + `pyapiBridge.ts`(SW message -> 공유 WorkerEngine.serveApi -> 응답). 페이지 어디서든 `fetch('/pyapi/*')` 가 커널로 간다.

- 게이트: landing dev 에서 실제 `fetch('/pyapi/company/005930/panel/IS')` -> 200. `X-Dartlab-Tier: browser` 헤더.
- 롤백: SW 의 /pyapi 분기 제거(shell/데이터 캐시 로직과 분리돼 있어 안전).

## Phase 2. dartlab 이야기 배선 (첫 소비자)

dartlab 이야기 본문에서 마크다운 표/차트가 `fetch('/pyapi/*')` 로 라이브 데이터를 얹을 수 있게 한다. 예: 글 안 "삼성전자 최신 손익" 표를 빌드타임 고정값이 아니라 browser-as-server 라이브로. 실행셀(코드)은 기존 워커 execute 유지(회귀 금지), 데이터 위젯만 fetch.

- 배선점: `RunnableCode` 는 불변. 새 경량 컴포넌트 `LiveTable.svelte`(마크다운 `@[data](company/005930/panel/IS)` 확장, richMarkdown 임베드 계열과 동형)가 fetch.
- 게이트: 발행 글 한 편에 라이브 표 1개, 다크/라이트 눈검수. `runCells.mjs` 회귀 0.
- async def 게이트: `browserApi.py` sync def 부재 AST 검사.

## Phase 3. 노트북 배선 (데이터 패널)

노트북 사이드바/셀 결과에서 dartlab API 를 fetch 로 부를 수 있는 얇은 헬퍼. 노트북 execute 는 불변. 예: 변수 인스펙터 옆 "이 회사 API 로 보기" 가 `/pyapi` 호출.

- 게이트: 노트북에서 fetch 200 + execute 회귀 0.

## Phase 4. (범위 밖, 후속) 터미널 :8400 축소 · SSE

터미널의 순수 데이터 엔드포인트를 browser-as-server 로 이관해 :8400 의존을 줄인다. SSE 스트리밍(SW ReadableStream + ASGI more_body). 별도 PRD.

---

## 콜드스타트 완화 (전 Phase 관통)

1. **fastapi lazy** - 첫 `/pyapi` 요청 때만 `ensureServer`. 노트북만 쓰는 사용자는 fastapi 비용 0.
2. **SW precache** - pyodide wasm + fastapi + dartlab wheel 을 SW install 때 캐시. 재방문 네트워크 0.
3. **진입 프리워밍** - 이번 세션 노트북에 적용한 idle 프리워밍 패턴 재사용(데이터 API 를 쓸 표면 진입 시).
4. **fastapi 는 1.6s** - 실측. 진짜 비용은 dartlab 10.3s 인데 커널 공유라 노트북 프리워밍이 그대로 커버.

## 기계 가드레일

| 가드 | 무엇 | 어디 |
|---|---|---|
| G1 async 강제 | browserApi.py 에 sync def 엔드포인트 0 | `tests/audit/browserApiAsync.py` (AST) |
| G2 한 커널 | FastAPI 가 별도 pyodide 를 안 띄움(워커 재사용) | 워커 유닛 테스트 |
| G3 노트북 회귀 0 | execute 경로 불변 | 기존 셀 테스트 + `runCells.mjs` |
| G4 계약 무증식 | /pyapi 는 dartlab 공개계약(엔진명) 노출뿐, 새 verb 신설 금지 | `notebookContract` 확장 검토 |
| G5 tierUsed | 응답에 X-Dartlab-Tier | 통합 테스트 |

## 롤백

각 Phase 는 추가만 한다(기존 경로 미변경). 되돌리기 = 그 Phase 의 신설 파일/분기 제거로 이전 상태 복귀. 노트북 execute·터미널 HF 직독은 어느 Phase 에서도 불변.

## 이중 평가 (개발자 + PM)

- **개발자**: 위험은 async 강제 누락(sync def -> 스레드 크래시)과 두 커널 실수(콜드스타트 2배). 둘 다 G1·G2 로 기계 차단. HTTP 오버헤드 8ms 실측이라 성능 리스크 없음.
- **PM**: 가치는 ":8400 없이 라이브 데이터" 로 dartlab 이야기·터미널이 정적 한계를 벗는 것. 리스크는 콜드스타트 체감(fastapi 1.6s + dartlab 10.3s)인데 lazy+precache+프리워밍으로 은닉. 첫 출하는 dartlab 이야기 라이브 표 1개로 좁게(덕지덕지 방지), 검증 후 확장.
