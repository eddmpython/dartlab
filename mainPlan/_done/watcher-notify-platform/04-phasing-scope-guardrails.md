# 04 — 단계 · 잘라낸 것 · non-goal · 운영자 결정 · 파일 계획

## 1. 단계 (P1~P4)

### P1 — 허브 + 발행 알림 + 수신 스택 (출시 가능 최소체)
- `infra/workers/pushHub/` Worker — `/subscribe`·`/send`·`DELETE`, D1 2테이블(+`sentNonce`), VAPID JWT ES256 순수 WebCrypto
- **수신 스택 0에서 신규 구축**: `service-worker.ts` push/notificationclick/pushsubscriptionchange 3 리스너 ([07](07-p1-client-receiving.md))
- `NotifyOptIn.svelte` — 2단 게이트 권한·`pushManager.subscribe`·endpoint 직렬화 → `/subscribe`
- **페이로드 = aes128gcm 암호화 본문**(라운드1 격상 — 제목 표시 + iOS 표준경로, [06 §0](06-p1-hub-worker.md)). ece 졸업 = P1 SHIP 게이트
- 발행 알림 러너 `.github/scripts/notify/` + **독립 워크플로 `notify-publish.yml`**(cancel-in-progress 유실 가드, [08 §2](08-p1-publish-ops-test.md))
- 상세설계 = [06](06-p1-hub-worker.md)(허브) · [07](07-p1-client-receiving.md)(수신) · [08](08-p1-publish-ops-test.md)(러너·운영·검증)
- **`/send` 인증(SEND_TOKEN + HMAC + nonce) + endpoint origin 화이트리스트 = P1 SHIP 게이트** (미루면 무인증 발송 = 스팸/피싱 발사대)
- iOS 가드: standalone 일 때만 활성, 미설치는 설치가이드 분기

### P2 — 공개 왓처 토픽 (per-user 식별 0)
- GHA 러너(`.github/scripts/notify/`) plain 함수, 토픽 1개=함수 1개, scan/gather SSOT 직독 → `/send`. 레지스트리·synth 모듈·새 src 엔진 0
- **첫 레퍼런스: '신규수주' 토픽** = `scan('orders')`(이미 라이브) 위 book-to-bill≥1 threshold_cross diff → 브로드캐스트. 새 데이터 0줄
- last-seen 커서(D1 매치 id set) 중복 억제
- aes128gcm 본문 푸시 격상(`tests/_attempts/pushHub/` ece 졸업 후)
- 발송 위생: 토픽별 일일 cap·기본 조용한시간(22~08 묶음)·24h dedupe — 러너 쪽 판정, 허브 thin 유지
- 알림 sink 정화(제어/RTL strip·출처라벨·dartlab 자기 라우트 링크)

### P3 — 개인 왓처 (로컬 소유·Mode A)
- `tests/_attempts/watcherEval/` 졸업(≥3 ssotRef·scope 양모드·predicate if-분기0·커서 dedup) → `src/dartlab/synth/watch/` + `WATCHER_REGISTRY`
- `~/.dartlab/watch.json` 로컬 config + `watchlist.svelte.ts` 에 알림 비트 추가(새 화면 신설 금지)
- 로컬 브리지 배선: `_PrivateNetworkAccessMiddleware`(pure-ASGI) + `_corsOrigins()` github.io 1줄 + `GET /api/bridge/ping`
- capability 토큰(`X-DL-Cap`)으로 쓰기·ai·export 보호, `allow_credentials=False`
- `src/dartlab/cli/commands/watch.py` 데몬(`channel.py` 형판, 8400 task 통합)

### P4 — 모드 B + 소비자 패키징 (단계 번호 박탈 — 별 트랙·운영자 결정 뒤)
- 모드 B(gist publish → 항상켜진 러너 평가 → 오프라인 폰 알림) — private gist·종목코드/수치임계만·D1 미기록
- 소비자 원패스 패키징(pyinstaller/briefcase) — polars rust+의존그래프+HF 캐시 번들 수백MB·3종 빌드매트릭스.
  **P1-P3 전제는 '개발자 pip 경로'**(`pip install` → `dartlab ai` → SPA 에서 watch). 원패스는 비전 문구로만 유지, 빌드 0.

> **디딤돌 서사 금지**: P1~P3 는 P4 없이 완결 가치(발행→공개토픽→로컬개인)를 낸다. P4 는 영영 안 와도 손해 0.
> P1 구현자는 P4·브리지를 향한 확장점(추상 인터페이스·미사용 컬럼·플러그인 훅)을 **선설치하지 않는다**.

## 2. 잘라낸 것 (scope cut — 클러터 비평가 반영)

- 왓처 타입 **레지스트리 추상** — P2 까지 삭제(YAGNI, N=5 형태 제각각). P3 졸업 시 발견적 추출.
- **로컬 브리지·PNA·offlineGuard·원패스 런처** — P1/P2 임계경로에서 완전 제거(0 기여). P3 로 격리.
- **P4(모드 B + 소비자 패키징)** — 단계 번호 박탈, '별도 운영자 결정·별도 PRD·미래 트랙'.
- **D1 개인조건 테이블** — 영구 0(마이그레이션 부채·재식별 surface 회피).
- **D1 익명 종목행 per-user 안** — 기각(endpoint+종목=재식별, 보안 high). 개인화는 로컬 소유.
- **OS 토스트(win10toast/plyer) P1 필수** — 제외(환경별 깨짐·무거운 의존). 기본 채널 = 폰 푸시 구독.
- **별도 만료 endpoint 청소 cron** — 0개(`/send` 404/410 inline DELETE).
- **'구독 가능 목록' 마케팅 페이지** — 금지(알림센터 시트 토픽 리스트가 곧 카탈로그).

## 3. non-goal (명시적 비목표)
- 계정·로그인·서버 사용자 프로파일.
- Cloudflare Worker 가 크롤·판정·LLM 요약을 수행하는 것(허브는 저장+발송만).
- 임의 코드 실행 브리지(컴퓨트 오프로드는 [00b](00b-local-runtime-bridge-and-gpu.md) 별 탐색, allowlist 강제).

## 4. 운영자 결정 (착수 전·P3 전 필요)

1. **개인화 = 로컬 브리지(권고) vs D1 익명행** — 통합 권고는 로컬 브리지(비전 보존 + 재식별 회피). P1/P2 는
   어느 쪽이든 영향 0이라 **P3 직전 결정 가능**. 후자 택하면 브리지 축 전체가 PRD 에서 사라짐.
2. **P1 발행 알림 발송 트리거** — 사람 수동 POST vs `blog/PIPELINE.md` 에 발행 cron 1줄 자동. 둘 다 P1 무료.
3. **P1 에 공개 공시 토픽 1종 동봉?** — 프로덕트 권고: 발행 단독은 빈도 낮아 동기 약함 → 저빈도·고가치
   토픽(신규수주 또는 IPO신규상장) 1종을 P1 에 동봉(발송경로·D1·UX 동일, 추가 비용 ~0).
   ★ **IPO신규상장 데이터원 막힘 해소(2026-06-30)**: `scan('ipo')` 본진 졸업(`scan/ipo.py`, a5bdfda35,
   alias 신규상장/공모/아이피오/증권신고서). predicate `new_listing`(01 §4 ≤3 고정의 하나)으로 rcept_no
   last-seen diff → 브로드캐스트. **신규수주와 동급 — 새 데이터·새 엔진 0**. 남은 결정은 "P1 동봉 vs P2"
   타이밍뿐(데이터원 불확실성은 제거).
4. **VAPID 키 생성·secret 등록 시점** — P1 착수 전 운영자가 `wrangler secret put` 1회(자격증명 `.env` 보유) vs 배포 단계.
5. **`scan.orders` stale 정정 동반** — 메모리 `project_order_flow_scan` "본진 미투입" + `_attempts` README 가
   라이브 `scan.orders` 축과 모순. '신규수주' 토픽을 P2 첫 데모로 승격하려면 이 정정을 본 작업단위에 포함할지.
6. **모드 B 제공 vs 영구 보류** — 종목·임계 적재가 PII 0 원칙과 충돌.

## 5. 파일 계획

| 단계 | 파일 | 비고 |
|---|---|---|
| P1 | `infra/workers/pushHub/{worker.js,schema.sql,wrangler.toml,README.md}` | siteSignals/questionCollector 형판 |
| P1 | `landing/src/service-worker.ts` | push·notificationclick·pushsubscriptionchange 추가(기존 보존) |
| P1 | `landing/src/lib/components/NotifyOptIn.svelte` | 2단 게이트·구독·POST |
| P1 | `landing/src/lib/notify/subscription.ts` | SW·컴포넌트 공유(직렬화·URL·토픽 SSOT) |
| P1 | `landing/src/lib/pwa/platform.ts` | `isStandalone`/`isIosSafari` 공유 추출(InstallPrompt 미러) |
| P1 | `landing/.env` + **`deploy-landing.yml` Build site env** | `VITE_VAPID_PUBLIC_KEY`·`VITE_PUSHHUB_URL`(공개값) |
| P1 | **`.github/scripts/notify/`** {send,authHeaders,payload,sanitize}.py | 발행 알림 러너(HMAC SSOT [06 §3]) |
| P1 | **`.github/workflows/notify-publish.yml`** | 독립 워크플로(cancel-in-progress 유실 가드) |
| P1 | **`tests/_attempts/pushHub/`** | aes128gcm ece 실브라우저 졸업(P1 SHIP 게이트) |
| P1 | `deploy-landing.yml` `npm test -w landing` 1줄 | vitest CI 게이트화 |
| P2 | `.github/scripts/notify/` *공개 왓처 토픽* 러너 | scan/gather SSOT 직독(발행 러너와 별개) |
| P3 | `tests/_attempts/watcherEval/` | 평가 졸업 |
| P3 | `src/dartlab/synth/watch/` | WATCHER_REGISTRY + 순수 evaluate |
| P3 | `src/dartlab/pipeline/stages/watch` | L4 오케스트레이션 |
| P3 | `src/dartlab/cli/commands/watch.py` | 데몬 |
| P3 | `src/dartlab/server/__init__.py` | PNA 미들웨어 + corsOrigins + bridge/ping |
| P3 | `~/.dartlab/watch.json` · `landing watchlist.svelte.ts` | 로컬 config · 알림 비트 |

## 6. 가드 요약 (불가침)
- 런타임-SSOT: 왓처는 gather/scan 직독, 베이크 0. 커서 = dedup 메타(데이터 사본 아님).
- `_attempts` 졸업 게이트: 능력(평가 로직)만 대상, 배선(워커·미들웨어·러너 스크립트)은 비대상.
- `infra/workers/<name>/` 컨벤션, `scripts/` 폴더 금지.
- landing/UI 변경 = 자동 push 금지(운영자 눈검수 후 발간).
- 새 L2 엔진·왓처 엔진 신설 금지(graph 회귀·도메인 격리).
