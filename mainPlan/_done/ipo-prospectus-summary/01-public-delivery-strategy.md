# 01. IPO 단건 리포트 퍼블릭 전달 전략 (전략 E 승인·구현 완료)

> 운영자 지시("무조건 런타임, 로컬 전용 금지" + "퍼블릭 터미널 속도·버벅임 없이 + 공동작업대 방법 포함 전수 고려")에 따른 5전략 전수 탐색·실측·적대검증 종합. **운영자 승인("차라리 베이크하자, 체계적으로, actions 자동화, 왓치 첫 관문")으로 전략 E 구현 완료(2026-07-05).**

## ✅ 구현 완료 (전략 E, 2026-07-05)

- **베이크 파이프라인**: `.github/scripts/sync/buildIpoReports.py` (online sync, buildIpoReport 위임·재구현 0, 단일 파싱). dataConfig `ipoReports` 릴리즈 키(dart/ipo). 왓치 cron(`notify-watch.yml`)이 **첫 관문**으로 베이크(리포트 HF push) 후 알림(딥링크 목적지 리포트가 이미 HF에 존재). watch.py 는 베이크 산출 parquet 직독(단일 파싱, scan 폴백).
- **런타임 직독**: `ipoReportSource.ts`(HF dart/ipo/reports.parquet whole-file + reportJson JSON.parse, reportSource 동형). public report = notWiredYet 제거·HF 직독. local = HF 우선 + 미베이크만 /api 헤드룸. IpoDialog env.kind 게이트 제거(퍼블릭도 렌더), 미베이크는 "준비중".
- **실측 검증**: 9 발행사 build → HF push → 라이브 readback. 파이썬 2/2·runtime vitest 81/81(ipoReportSource 5/5)·watch 8/8·surfaces svelte-check 0. **퍼블릭 터미널(env.kind=public) 6카테고리 리포트 HF 직독 렌더 스크린샷 확인**(로컬서버·pyodide 0).
- **운영자 잔여**: ① hfProxy `/ipo-filings` 워커 재배포(발굴 리스트 데이터원, 리포트와 별개). ② GitHub Secret `HF_TOKEN`(왓치 베이크 push용, 기존 있으면 무관). ③ landing/ui 커밋 눈검수 후 push.

---

## 문제

발굴 리스트(증권신고서 지분증권 발행사)는 라이브 워커 `/ipo-filings`로 이미 퍼블릭. 문제는 단건 6카테고리 리포트다. 원문(2만~470만 자 dart4.xsd XML)을 `parseIpoProspectus`(파이썬 수백 줄 엔진)로 파싱해야 나오는데, 퍼블릭 터미널은 정적(백엔드 0)이고 DART 원문 fetch는 키 비밀 + CORS로 막힘. 지금은 로컬 서버(:8400)만 파싱 = 로컬 전용. 운영자가 이걸 거부.

## 핵심 긴장 (물리)

"베이크 없는 순수 런타임"과 "무버벅임"은 퍼블릭 풀 리포트에서 **양립 불가**. 순수 런타임 = 브라우저 pyodide인데 실측 결과 무겁고 버벅임. 버벅임 0 = CI가 리포트를 만들어 HF에 올리고 직독(= 기술적으로 베이크). 넷째 선택지 없음.

## 5전략 랭킹 (실측 보정)

| 순위 | 전략 | 점수 | 속도·버벅임 (실측) | 판정 |
|---|---|---|---|---|
| 1 | **CI가 리포트 생산 → HF 직독** (구조화 typed, 다른 터미널 데이터와 동일) | 8 | 수십~수백KB 1 GET, 파싱 0, 버벅임 0 | viable |
| 2 | 2티어 (scan floor + 온디맨드 pyodide deep) | 8 | floor 완벽, Tier2 pyodide 콜드 = 덕지덕지 | viable(과설계) |
| 3 | scan 스칼라 parquet만 | 6 | 빠르나 헤드라인만, 6카테고리 내러티브 결측 | 부분 |
| 4 | 브라우저 pyodide (순수 런타임, 베이크 0) | 4 | 휠 21MB(+pyodide 5.5+lxml 1.4+polars 9)=~28~37MB, 메인스레드 프리즈 15~45s | marginal |
| 5 | Cloudflare Python Worker (엣지) | 2 | 무료 10ms CPU/invocation 한도, 파싱 수초라 초과. Paid(30s~5min) 필요 | blocked |

실측 근거: 휠 21,095,353 bytes(로컬 실측), pyodide core 5.55MB·lxml 1.42MB(jsdelivr range), `providers/dart/__init__`가 Company eager import로 polars(9MB) 견인. CF: Free 100k req/day + 10ms CPU, Paid 30s~5min, Python Workers open beta(공식 문서). E의 속도 프로파일은 market_recent(656KB/38K행)·finance-lite·reportSource 실배포 경로 상속(추정 아님).

## 추천: 전략 E (구조화 typed bake)

CI sync 잡이 `buildIpoReport(rcept)`를 돌려 6카테고리 리포트를 파싱·산출하고, 그 **구조화 typed 값**(markdown 통짜 아님, reportSource.ts 선례)을 HF에 push. 퍼블릭 터미널은 소형 parquet을 whole-file 직독 + 얇은 JS transform으로 표시.

**규율(규칙준수의 핵심)**:
- 파서(`parseIpoProspectus`)·렌더(`renderIpoReport`)는 CI 파이썬 존치. JS 재구현 0.
- 굽는 건 구조화 typed 컬럼(가변길이는 JSON 컬럼: lockups·rows·peers). 최종 표시 조립은 런타임 얇은 TS.
- 발굴 리스트는 현행 라이브 워커 유지(market_recent + 워커 오버레이 동형).

**왜 "나쁜 베이크"가 아닌가**: 터미널의 모든 데이터(재무·scan·market_recent·주가·검색)가 이미 CI 생산 → HF 직독. IPO 리포트만 예외로 클라 파싱을 요구할 이유 없음. 운영자의 "베이크 아니라 런타임"은 로컬 서버라는 런타임이 있는데 사본을 또 굽는 **우회 베이크**를 겨눈 것. 퍼블릭엔 파싱 런타임 자체가 부재하므로 이건 우회가 아니라 **없는 SSOT를 처음 생산**(allFilings·scan·panel과 동일 online sync 모델).

## ⛔ 착수 조건 (운영자 결정)

1. **명시 승인 필수**: 신규 HF 아티팩트 + online sync 베이크. "scan 축 프리빌드 상시 인정" 예외는 offlineGuard 경유 offline 한정이라 이걸 **자동 커버 못 함**(적대검증이 이 착각을 잡음). CLAUDE.md "무승인 빌드 착수 금지" 적용. 제안까지만, 승인 후 착수.
2. bake 형태: 구조화 typed(추천) vs markdown blob.
3. 아티팩트 shape: 단일 reports.parquet(rcept 키) vs per-rcept JSON. 크기 가드 1.5MB.
4. 당일 접수~cron 갭(며칠 여유): "준비중" 정직표시 + 로컬 /api 헤드룸. pyodide deep 티어는 보류(덕지덕지).
5. 확정공모가 병합: scanIpo(deep)는 FULL만 파싱. [발행조건확정] doc은 `buildIpoReport(confirmationRcept=)` 별도 병합.

## 구현 스텝 (승인 시)

1. `.github/scripts/sync/buildIpoReports.py` 신규 (buildAllFilingsRecent 패턴, online sync, offlineGuard 미사용). listFilings(E,C001) → rcept별 buildIpoReport → 구조화 typed → HF `dart/ipo/` push.
2. sync 워크플로 cron 잡 추가(3~6h).
3. `ui/packages/runtime/src/adapters/public/sources/ipoReportSource.ts` 신규 (requestParquetWholeFile + IpoReport 매핑, reportSource 패턴).
4. `createPublicRuntime.ts`: `publicIpoPort.report` notWiredYet → loadIpoReport 교체. hf origin 재사용.
5. IpoDialog: `env.kind==='local'` 게이트 제거(퍼블릭도 report).
6. 신규 src 모듈 CI 게이트(publicApiScenarios·productSmoke·structureMirror) 선제.
7. 테스트 + 스크립트 스모크.

엔진(providers/story) 무수정 재사용.

---

*탐색: workflow wf_92e68bad (11 에이전트, 5전략 × 심층평가 + 적대검증 + 종합). 미빌드라 성공 주장 없음. E 속도근거 = 동형 실배포 경로 상속, 규칙 핵심판정 = 코드 실측 CONFIRMED.*
