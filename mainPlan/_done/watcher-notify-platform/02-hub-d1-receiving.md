# 02 — 허브 계약 · D1 스키마 · 발신 인증 · 수신 스택

허브 = `infra/workers/pushHub/` (`siteSignals`/`questionCollector` thin-POST 형판, 새 최상위 폴더 0).

## 1. 허브 라우트 3개

### POST /subscribe (무인증·공개)
- body: `{endpoint, keys:{p256dh, auth}, topics:[]}`
- CORS: `ALLOW_ORIGIN` echo (`siteSignals` corsHeaders 차용)
- 검증:
  - `endpoint` origin ∈ push 서비스 화이트리스트 — `fcm.googleapis.com`·`web.push.apple.com`·
    `*.push.services.mozilla.com` 만 (**임의 URL = SSRF 발사대 차단**)
  - `p256dh`/`auth` base64url 길이 정상
  - `topics` ⊆ `TOPIC_ALLOWLIST` (코드 상수, `siteSignals` `ALLOWED_EVENTS` 동형)
- 동작: `subscriptions` UPSERT + `topicSubs` 차집합 동기화
- rate limit: Cloudflare WAF / Rate Limiting binding (D1 쓰기 절약)

### POST /send (러너 전용 — Bearer + nonce)
- `Authorization: Bearer <PUSHHUB_SEND_TOKEN>` (Worker secret, GHA `secrets.` 주입). HMAC 서명층 제거(품질점검, [06 §2]).
- nonce `X-DL-Nonce`=`sha1(topic:slug)`: D1 `sentNonce` unique insert (중복 = **replay 거절** + 멱등). `X-DL-Ts` 윈도 ±300s
- body: `{topic, notification:{title, body, url, tag}}` 또는 `{endpoints:[], notification}`(개인 타겟)
- 동작: **JOIN 1회** topic→endpoint → origin별 VAPID JWT 메모 → **`Promise.allSettled` 청크 발송**(직렬 금지, [06 §3])
- 응답별: 2xx=성공 · **404/410 = batch purge(끝-일괄, 청소 cron 0)** · 429/5xx=보존. 응답 `{sent,pruned,failed}` → 러너 헬스게이트
- origin 헤더는 server-to-server 호출에서 신뢰 불가(위조) → `/send` 는 origin 무관, Bearer+nonce 만.

### DELETE /subscribe (또는 topics:[])
- 즉시 행 삭제 — 삭제권 보장. 클라가 `pushManager.unsubscribe` 시 동시 호출.

## 2. D1 스키마 — 2 테이블, 개인조건 컬럼 영구 0

> **정본 DDL = [06 §6](06-p1-hub-worker.md)** (`uaClass NOT NULL DEFAULT 'other'`·`CREATE TABLE IF NOT EXISTS`·
> `sentNonce(ts NOT NULL)`+`sentNonceTsIdx`). 본 절은 *계약 개요*만 — 컬럼명/제약은 06 이 SSOT(중복 DDL 미게재로 divergence 차단).

- `subscriptions(endpoint PK, p256dh, auth, uaClass, createdAt, lastSeenAt)` — endpoint 자연 PK → 재구독 **멱등 UPSERT**
  (원자성 미가정·실측 게이트, [06 §6]). `topicSubs(endpoint, topic, …)` PK(endpoint,topic) + FK CASCADE + `topicSubsTopicIdx`.
  `sentNonce(nonce PK, ts NOT NULL)` replay 거절.
- **개인조건·user_id·종목 컬럼 0** — endpoint+종목 list = 재식별 surface(보안 high). 개인화는 로컬 소유([03](03-local-bridge-personalization.md)).
- 위생: `/unsubscribe` 즉시 delete + 발송 404/410 batch purge. **별도 만료 cron 0**(품질점검: '미수신 N개월 자동 만료'는
  메커니즘 없는 빈 약속이라 삭제 — purge 가 닿는 구독은 결국 정리, stale 잔류는 무해·소량. 설계의 'cron 0' 자랑과 정합).
- last-seen 평가 커서(매치 id set)는 D1 에 저장 — dedup 메타, 원천 데이터 베이크 아님.

## 3. VAPID 키 운용

- 키쌍 1회 생성(P-256 ECDSA).
- **공개키**(application server key, 비밀 아님) → landing build env `VITE_VAPID_PUBLIC_KEY`
  (`questionCollector` 의 `VITE_FEEDBACK_URL` 패턴: **`deploy-landing.yml` Build site step** env + `landing/.env` 양쪽, 공개값).
  허브 base URL `VITE_PUSHHUB_URL` 도 동일 2곳. 변수명·위치 SSOT = [07 §4](07-p1-client-receiving.md).
- **비밀키** → `wrangler secret put VAPID_PRIVATE_KEY` (절대 커밋 금지, `HF_TOKEN` 패턴).
- JWT 서명 = Worker 가 `crypto.subtle.importKey(pkcs8) + sign(ECDSA SHA-256)` 직접 — **npm 의존 0**,
  `nodejs_compat` 불필요(순수 WebCrypto). `sub` 클레임 = `mailto:` 운영자.

## 4. 페이로드 — P1 = aes128gcm (라운드1 정정)

> ⚠ 원안은 "P1 = VAPID-only 빈 본문, iOS 안전"이었으나 평가가 두 갭을 적발: (1) 빈 본문은 글 제목이
> 기기에 안 보이고(고정문구만), (2) `web.push.apple.com` 빈-본문 수락은 미검증("iOS 안전"은 검증 전 단정).
> → **P1 을 aes128gcm 본문으로 격상**해 두 갭을 닫는다. 상세 = [06 §0·§5](06-p1-hub-worker.md).

- **P1** = aes128gcm 암호화 본문(RFC8291: ECDH + HKDF-SHA256 + AES-128-GCM, 순수 WebCrypto, npm 0).
  제목·본문이 실제 표시. iOS 표준 경로. ece 바이트 프레이밍은 `tests/_attempts/pushHub/` 실브라우저 1대
  졸업을 **P1 SHIP 게이트**로(원안의 P2 졸업을 P1 으로 끌어옴).
- 빈 페이로드(VAPID-only)는 폐기 — '/api 재조회 표시' 분기도 삭제(iOS 구독취소 유발).

## 5. 수신 스택 — P1 에서 0부터 구축 (브리프 원안 오판 핵심)

`service-worker.ts` 는 셸 캐시(install/activate/fetch)만 — push 수신 파이프 전무. P1 신규 5종:

1. `service-worker.ts` + **3 리스너**: `push`(`event.data.json()` → `showNotification`) ·
   `notificationclick`(`clients.openWindow(data.url)`) · `pushsubscriptionchange`(재구독 + `/subscribe` 재등록).
   기존 install/activate/fetch 보존.
2. `NotifyOptIn.svelte` — **2단 게이트**: 소프트 프롬프트(우리 UI 토글 명시 클릭) → *그때만* OS
   `Notification.requestPermission`. 콜드 자동 팝업 금지(1회 거부=영구 차단). 거절은 `localStorage('dl-notify-dismissed')`
   기억(`InstallPrompt` 의 `dl-install-dismissed` 미러).
3. `registration.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:<VAPID 공개키>})` → endpoint 직렬화 → `/subscribe` POST.
4. VAPID 키 생성·secret 운용(§3).
5. Worker 발송(§1 `/send`).

### iOS 16.4+ 가드 (불가침 3종)
- 푸시 권한은 **홈화면 설치 PWA(standalone) 안에서만** 가능. `NotifyOptIn` 은 `display-mode: standalone`
  일 때만 활성(`InstallPrompt` 의 `isStandalone()` 가드 재사용). 미설치 Safari 탭은 설치가이드로 분기(`InstallPrompt` mode=ios 재사용).
- 권한 요청은 **사용자 제스처(클릭) 안에서만**.
- `userVisibleOnly:true` 강제(silent push 불가).

## 6. 알림 본문 정화 (untrusted sink)

알림 body 는 LLM 프롬프트가 아니라 사용자 화면 + OS 알림센터에 렌더되는 별개 sink → `wrap_external_in_result`
(LLM 직렬화 전용) 부적용. 대신 전용 정화:
- 외부 텍스트(공시 제목·뉴스 헤드라인) 제어문자·zero-width·RTL override(U+202A~202E, U+2066~2069) strip + 길이 cap + **출처 라벨**('DART 공시'/'네이버뉴스') prepend.
- SW 에서 **`textContent` 로만** 렌더(HTML 0).
- 클릭 목적지 URL 은 **항상 dartlab 자기 라우트**(`/report?rcept=…`)로만 — 외부 originallink 직링크 금지(피싱 차단).
- 본문 = 우리가 분류한 이벤트 라벨 + 수치만(원문 제목 직삽 금지).
- 도구: `landing/src/lib/notify/sanitize.ts` (`cardShare` worker `esc()` 출력 안전화 정신).
