# paseo 흡수 원장 (local agent workbench)

로컬 앱 chat 표면을 ChatGPT 양식에서 에이전트 작업대 양식으로 다시 세우는 initiative의 SSOT다.
paseo(github.com/getpaseo/paseo, AGPL-3.0)의 요소와 방법을 아이디어 수준으로 흡수한다. 소스 전사는
라이선스와 제품 정체성 양쪽 이유로 금지한다. 근거는 paseo 저장소 문서·소스 전수 조사와 dartlab
실물 직독(2026-08-06)이다.

판정 값: **있음**(그대로 쓴다) / **배선**(재료가 있고 렌더·연결만 남음) / **신설**(새로 짓는다) /
**보류**(운영자 판정 대기) / **기각**(사유 명시). 행 완료 시 판정 칸에 [x] 를 앞세운다.
initiative 종료 시 확정 사실을 Skill OS 운영문서 (`specs/operation/**`) 에 반영하고 본 폴더를 삭제한다.

## 0. 스택 판정 (원장 전제)

paseo 데스크톱은 별도 네이티브 UI가 아니라 웹 빌드 + 얇은 셸이다. Electron이 Expo 웹 빌드를
그대로 렌더하며, 저자가 Tauri에서 Electron으로 옮긴 경위 글이 저장소에 있다
(packages/website/posts/i-was-wrong-about-electron.md). dartlab은 이미 같은 모양이다
(SvelteKit 웹 빌드 + dartlab-desktop tao+wry 셸). 따라서 스택 교체는 없다.

흡수하는 것은 스택의 구조 방법 4가지다.

1. 서버(중개기)가 세션 타임라인의 진실원을 소유하고 클라이언트는 얇은 소비자다.
   paseo는 세션 파일에 타임라인을 인라인 저장해 데몬 재시작을 넘긴다.
2. 라이브 스트림(즉시성)과 타임라인 조회(권위·페이지네이션)를 이원화한다.
3. 이벤트 스키마는 append-only(필드 추가만)로 유지하고, 신기능 분기는 capability 게이팅
   한곳에 모은다.
4. wire 계약의 단일 진실원을 둔다. dartlab은 `ai/runtime/contracts.py`가 이미 그 자리다.

채택하지 않는 것: Expo/RN(앱스토어 네이티브 배포용, 브라우저 접속 제품에 해당 없음),
Electron(셸 보유), zustand/react-query(Svelte runes 대응물 보유), WebSocket 전환(현
SSE+REST로 동등 달성, 필요가 실측되면 재론).

## A. 데몬·프로토콜

| ID | paseo 방법 | dartlab 실측 | 판정 |
|---|---|---|---|
| A1 | 세션별 영속 타임라인(파일 저장, 재시작 생존) | `eventBuffer.py`는 재접속용 인메모리 링(256건/4MB)뿐. `sessionStore.py`는 "네이티브 transcript 비복제" 명시 | **신설(서버)**: 공개 이벤트 저널 + 조회 API. 모든 UI 행의 전제 |
| A2 | 재접속 시 최신 tail 페이지 + 위로 스크롤 페이지네이션 | 새로고침 시 대화 본문 증발(`chatStore#load`가 메타만 복원, `messages: []`) | **신설**(A1 소비) |
| A3 | 스키마 append-only + capability 게이팅 | `PUBLIC_AGENT_EVENT_KINDS` 실재 | **있음**(규약만 계약 주석으로 명문화) |
| A4 | 승인 흐름: pending 큐 + provider 블로킹 + 클라이언트 응답 | APPROVAL_REQUESTED 이벤트, resolve API, 스트림 내 카드 렌더까지 실재 | **있음** |
| A5 | 다중 클라이언트 동시 관측·브로드캐스트(hot set 구독) | 단일 브라우저 전제 | **보류**(devtunnel 모바일 접속이 실사용되면 A1 저널 재사용으로 성립) |
| A6 | 프로젝트/워크스페이스 2계층 세션 귀속 | 대화당 종목 코드 1개 | **번역 채택**: 종목·주제를 그룹 축으로만 쓴다. 워크스페이스 개념은 도입하지 않는다 |

## B. Composer 통제

| ID | paseo 방법 | dartlab 실측 | 판정 |
|---|---|---|---|
| B1 | 런타임(제공자) 인라인 콤보. 실행 중에도 전환 가능하며, 서버가 타임라인을 소유하므로 갈아타도 대화가 유지된다 | 전역 default 하나 + 첫 전송 시 대화 고정. 화면 전환 수단 없음(usage limit 장애 실측: ready인 다른 런타임으로 전환 불가) | **신설**, A1 의존 |
| B2 | 모델 선택(제공자별 그룹, 즐겨찾기, 실패 제공자만 재시도) | 없음. 모델은 CLI가 소유 | **신설**(manifest에 모델 능력 선언 추가, 지원 런타임 한정) |
| B3 | 추론 강도 콤보(모델 지원 시) | 없음 | B2와 묶음 |
| B4 | 권한 모드(plan/default/full-access, Shift+Tab 순환) | agent MCP profile이 읽기 전용 도구만 광고해 권한 다양성 자체가 없음 | **기각**(쓰기 도구가 생기는 날 재론) |
| B5 | 첨부(이미지·파일·이슈, 입력창 위 트레이) | 없음 | **보류**(분석 제품의 첨부 1급 대상: 공시 문서·스크린샷 질문. 별도 판정) |
| B6 | 음성: 받아쓰기 + 보이스 모드. STT/TTS는 데몬 측 실행 | 없음 | **보류**(별도 initiative 크기) |
| B7 | 바쁠 때 전송 = 큐 적재(큐 트랙: 지금 전송/수정) | busy면 전송 자체 차단 | **신설**(큐 적재만. Interrupt 기본값 설정은 후순위) |
| B8 | 컨텍스트 사용률 원형 미터 + 세션 누적 비용 | 없음 | **보류**(런타임별 usage 이벤트 실측 후) |
| B9 | 추천 칩 | 실재 | **있음**(유지) |

## C. 메시지 스트림

| ID | paseo 방법 | dartlab 실측 | 판정 |
|---|---|---|---|
| C1 | 도구 호출 = 접힌 한 줄 배지(아이콘+요약, 진행 중 shimmer) + 펼침 시 타입별 상세(shell/read/edit/search/JSON) | `ToolCard.svelte` 317줄 대형 카드가 기본 노출 | **재작성(핵심 행)**. `toolLabels.ts` 재사용 |
| C2 | 연속 도구 그룹 배지("N개 편집, N개 실행, N개 읽음") + 펼침 목록 | 없음 | **신설** |
| C3 | 턴 푸터: 진행 중 1초 갱신 경과 타이머, 완료 후 "Worked for X" | part별 startedAt/durationMs만 있고 집계 렌더 없음 | **신설**(렌더만) |
| C4 | thinking 접힘 표시 | `ThinkingPanel` "N초 동안 생각함" 실재 | **있음** |
| C5 | 승인 카드: 라이브 헤드 위 고정 배치 + Deny/Accept + plan/question 변형 | 스트림 내 렌더 실재, 변형 없음 | **배선**(고정 배치 + 버튼별 로딩. 변형은 런타임이 그 구분을 주는지 실측 후) |
| C6 | Rewind(대화·파일 되돌리기)와 Fork | retry만 실재 | **기각**(파일 변경 없는 분석 대화라 Rewind 대상 부재. Fork만 보류) |
| C7 | 우측 접이식 패널(파일/변경/PR) | paseo가 diff를 놓는 자리에 근거를 놓는다: `Evidence.svelte`(260줄)를 우측 패널로 승격하고 viewSpec·표·검증 뱃지 상세를 동행 | **신설**(재배치, 기존 컴포넌트 재사용) |
| C8 | 컨텍스트 압축 마커 | 없음 | **보류** |

## D. 세션 목록

| ID | paseo 방법 | dartlab 실측 | 판정 |
|---|---|---|---|
| D1 | 상태 5버킷(needs_input/failed/attention/running/done) + 도트 색 체계 | 시간 버킷만(오늘·어제·7일) | **신설**: 스토어 파생(승인 대기=needs_input, error=failed, streaming=running, 미검증 뱃지=attention, 나머지=done) |
| D2 | 그룹핑 토글(Project/Status) | 없음 | **신설**: 상태 그룹 기본, 시간 버킷은 done 내부 정렬로 강등 |
| D3 | 행 정량 지표(diff stats, 최근 활동, pending) | 제목+시간뿐 | **번역 신설**: 근거 수·검증 상태·상대시간 |
| D4 | "N pending" 승인 뱃지 | 없음 | **신설**(D1 재료) |
| D5 | 제목 = 내용 기반 | 타임스탬프 재생성(`#generatedTitle`) | **신설**: 첫 사용자 질문 요약을 A1 저널에 저장하고 목록에 표시 |
| D6 | 별도 History 화면 + Load more | 사이드바뿐 | **기각**(세션 규모가 다름. 사이드바로 충분) |

## E. 진행·알림 / F. 원격 / G. 설정

| ID | paseo 방법 | dartlab 실측 | 판정 |
|---|---|---|---|
| E1 | 사이드바·탭 레벨 상태 도트(실행 중 스피너) | 없음 | **신설**(D1 재료) |
| E2 | 알림 정책: 보는 중 억제, present 클라이언트엔 OS 알림, 부재 시 푸시. 트리거는 턴 종료·승인 요청 둘 | 없음 | **보류**(웹 Notification 한정 후순위) |
| E3 | 서브에이전트 트랙("N subagents, M running") | 런타임 native 이벤트로만 흘러 화면 부재 | **보류**(런타임 Task 이벤트 형태 실측 후) |
| F1 | 릴레이/터널 원격 접속 | `dartlab channel`(devtunnel) + `DARTLAB_ADMIN_TOKEN` + `_isExposedMode` 실재 | **있음**(재구현 금지) |
| F2 | 페어링 QR, URL fragment로 키 전달(중계자가 못 보는 신뢰 앵커) | 없음 | **보류**(channel 개선 시 아이디어로만) |
| G1 | 제공자 준비 상태 필(Available/Loading/Error/Not installed) + 진단 | `RuntimeCenter` + readiness/probing 구조 실재 | **있음**(작업대 개편 시 위치만 재배치) |
| G2 | 설치·로그인·MCP 연결의 계획 제시 + digest 승인 실행 | `agentRuntimeApi.ts` plan/apply 체계 실재 | **있음** |

## 착수 순서 (흐름)

의존 순서 그대로 간다. 각 단계는 완결 단위로 commit하고, UI 표면 push는 스크린샷 눈검수 후
운영자 승인으로만 한다.

1. **A1 -> A2 -> D5**: 서버 영속 타임라인 저널 + 조회 API, 재수화, 내용 기반 제목.
   서버 선행 구간이라 화면이 바뀌지 않는다.
2. **C1 -> C2 -> C3/E1**: 도구 한 줄화, 그룹핑, 턴 집계와 상태 도트. 작업대 밀도의 몸통.
3. **B1(+B2·B3)**: 런타임 인라인 전환. 실측된 장애의 직접 해소.
4. **D1 -> D2 -> D3 -> D4**: 세션 목록 상태화.
5. **C7**: 우측 근거 패널 승격.
6. **C5 -> B7**: 승인 카드 강화, 전송 큐.
7. 보류 행 일괄 재판정(운영자): A5, B5, B6, B8, C8, E2, E3, F2, Fork.
8. 진입점 정합: 루트 라우팅이 터미널로 넘어가는 구조를 chat 재편과 함께 재검토한다.
   라우팅 변경은 UI push 게이트를 따른다.

## 변경 규모 실측 (2026-08-06)

chat 표면 약 4,600줄 중 재작성 약 2,280줄(`routes/chat/+page.svelte` 1,269 ·
`Sidebar` 393 · `ToolCard`+`ToolRun` 460 · `Composer` 156), 유지·증축 약 2,320줄
(`chatStore.svelte.ts` 701 데이터 계층 포함). 서버 `ai/runtime/`은 A1 저널을 더하는
증축이며 갈아엎지 않는다. `landing/`·`ui/packages/surfaces`·dartlab-desktop은 0줄.

## 출처

- paseo: github.com/getpaseo/paseo (AGPL-3.0). docs/architecture.md, docs/timeline-sync.md,
  docs/data-model.md, docs/protocol-compatibility.md, public-docs/orchestration.md,
  public-docs/connectivity.md, packages/website/posts/i-was-wrong-about-electron.md
- dartlab 실측: `src/dartlab/ai/runtime/{contracts,eventBuffer,sessionStore,eventProjection}.py`,
  `src/dartlab/server/agentGateway.py`, `ui/apps/local/src/lib/chat/`,
  `ui/apps/local/src/lib/runtime/agentRuntimeApi.ts`
