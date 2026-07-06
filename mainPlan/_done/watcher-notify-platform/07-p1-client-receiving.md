# 07 — P1 상세설계: 수신 스택 (build-ready)

`service-worker.ts` 3 리스너 + `NotifyOptIn.svelte` + 공유 모듈. 라운드1 갭 닫은 확정본.

## 0. 전제 (실측)
- `landing/src/service-worker.ts` = install/activate/fetch만(push 핸들러 0). `svelte.config.js` `serviceWorker.register`
  미설정 → SvelteKit 자동등록 → `navigator.serviceWorker.ready` 로 active reg 확보(별도 register 0).
- `InstallPrompt.svelte` 의 `isStandalone()`/`isIosSafari()`/`dl-install-dismissed` 미러. (private → §5 공유 추출)
- **BASE_PATH=/dartlab** 빌드(`deploy-landing.yml`) → 절대경로 `/icon-192.png` 는 404. **`import.meta.env.BASE_URL` 접두 필수**(라운드1 갭).
- P1 = **aes128gcm 본문**([06](06-p1-hub-worker.md) §0) → push `event.data` 가 **실제 payload 보유**(고정문구는 파싱 실패시만 fallback).

## 1. service-worker.ts — 3 리스너 추가 (기존 install/activate/fetch 불변)

상단 상수(기존 SHELL 근처):
```ts
const VAPID_PUBLIC_KEY: string = import.meta.env.VITE_VAPID_PUBLIC_KEY ?? '';
const ICON = `${import.meta.env.BASE_URL}icon-192.png`;   // BASE_URL = '/dartlab/' (404 가드)
// SUBSCRIBE_URL·DEFAULT_TOPICS·serializeSubscription·urlBase64ToUint8Array = $lib/notify/subscription (공유 import)
```

`export {};` 앞에 append:
- **push**: `event.data?.json()` 안전 파싱(실패→고정문구). title/body=payload 신뢰필드. payload.url 은 **app-path(base 없음)**
  이라 SW 가 **BASE_PATH 접두**: `const BASE = import.meta.env.BASE_URL.replace(/\/$/,'')`(=`/dartlab`), `dest = new URL(BASE + payload.url, origin)`,
  origin 일치만 채택(피싱 차단)·불일치→`new URL(BASE+'/', origin)`. data.url = `dest.pathname + dest.search`(=`/dartlab/blog/…`, 라운드4 blocker 닫음).
  `showNotification(title, {body, tag, icon:ICON, badge:ICON, data:{url}})`. **항상 showNotification 호출**(미표시=userVisibleOnly 위반→발송 차단).
- **notificationclick**: `notification.close()` → matchAll window 중 same-origin 있으면 focus+navigate, 없으면 openWindow.
  목적지 = data.url(이미 same-origin 검증된 상대경로).
- **pushsubscriptionchange**: `newSubscription ?? registration.pushManager.subscribe(event.oldSubscription?.options ?? {userVisibleOnly:true, applicationServerKey:…})`.
  `oldSubscription.options` 에 원래 `applicationServerKey` 가 보존돼 **재구독 시 VAPID 키 플러밍 거의 불요**(키 없으면 첫 신규구독 경로에서만 §7-1 fallback). 새 endpoint→`POST /subscribe`(구 endpoint 는 /send 404/410 inline purge 자가청소).
  `interface PushSubscriptionChangeEvent { newSubscription: PushSubscription|null; oldSubscription: PushSubscription|null }` 수동 선언(lib.dom 버전별).

## 2. NotifyOptIn.svelte — 컴포넌트 계약

- **props**: `{topics=['blogPublish'], variant='bar'}`. P1 default 하단 바(InstallPrompt 미러).
- **$state phase**: `hidden|soft|subscribing|on|blocked`.
- **상수**: `DISMISS_KEY='dl-notify-dismissed'`, `VAPID_PUBLIC_KEY`(import.meta.env).
- **onMount 가드 순서**(하나라도 걸리면 requestPermission 미호출):
  1. 미지원(`Notification`/`serviceWorker`/`PushManager` 부재) → hidden
  2. `!VAPID_PUBLIC_KEY` → hidden(키 미주입=기능 off)
  3. `!isStandalone() && isIosSafari()` → hidden(iOS 미설치는 InstallPrompt 가 설치유도 — 중복 안내 0)
  4. `dismissed()` → hidden
  5. `permission==='denied'` → **blocked**(영구차단 안내만, 재요청 버튼 0)
  6. `permission==='granted'` → 기존 구독 있으면 on, 없으면 subscribe→on
  7. `'default'` → **soft**(소프트 프롬프트만)
- **'알림 켜기' 클릭(제스처)** → `requestPermission()`(**OS 팝업은 오직 여기**) → granted: subscribeAndPost→on / denied: blocked+remember(콜드 재시도 0) / default: soft 복귀(remember 안 함).
- **off**: `sub.unsubscribe()` + `DELETE /subscribe` 동시 → soft.
- **close**: hidden + remember(`dl-notify-dismissed`).

## 3. 공유 모듈 `landing/src/lib/notify/subscription.ts`
```ts
export const SUBSCRIBE_URL = (import.meta.env.VITE_PUSHHUB_URL ?? '').replace(/\/+$/, '') + '/subscribe';
export const DEFAULT_TOPICS = ['blogPublish', 'cardPublish'];   // [06] TOPIC_ALLOWLIST 와 일치
export function urlBase64ToUint8Array(b64: string): Uint8Array { /* padding 복원 후 atob */ }
export interface SubscribePayload { endpoint: string; keys: { p256dh: string; auth: string }; topics: string[]; }
export function serializeSubscription(sub: PushSubscription, topics: string[]): SubscribePayload { /* sub.toJSON() */ }
export async function subscribePush(reg, vapidPublicKey): Promise<PushSubscription> {
  return (await reg.pushManager.getSubscription()) ??
    reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) });
}
```
SW·NotifyOptIn 양쪽 import(직렬화 형태·URL·토픽 1 SSOT). `sub.toJSON().keys` 는 padding 포함 base64url 가능 →
허브 b64ok 가 padding 허용([06] §2)으로 정합.

## 4. 환경변수 주입 (SSOT — 변수명·위치 확정)

| 변수 | 값 | 위치 |
|---|---|---|
| `VITE_VAPID_PUBLIC_KEY` | base64url 공개키(공개값) | `landing/.env`(dev) + **`deploy-landing.yml` Build site step env**(`VITE_FEEDBACK_URL` 인접) |
| `VITE_PUSHHUB_URL` | 허브 base(`https://dartlab-push-hub.<sub>.workers.dev`) | 동일 2곳 |

미주입 시 graceful(NotifyOptIn 가드② hidden, SW 재구독 skip) — 에러 0(`VITE_FEEDBACK_URL` 패턴).

## 5. 재사용 (덕지덕지 방지)
- `isStandalone()`/`isIosSafari()` → `landing/src/lib/pwa/platform.ts` 공유 추출(InstallPrompt 동작 불변, 순수 이동) → 양쪽 import.
- 알림 sink 정화는 **러너 책임**(발송 전). P1 수신단은 이미 정화된 구조화 필드만 렌더 — sanitize 선설치 0.

## 6. 마운트
`+layout.svelte` 에 `<InstallPrompt />` 옆 `<NotifyOptIn />`. 두 바 시각 겹침 방지(bottom offset/상호배제) — **landing UI = 자동 push 금지, 운영자 눈검수 후 발간**.

## 7. P1 SHIP 전 실측 게이트 (가정 아님 — 닫을 항목)
라운드1이 "검증 필요"로 남긴 것을 *닫는 작업*으로 승격:
1. **SW `import.meta.env.VITE_VAPID_PUBLIC_KEY` 정적 치환** — P1 *첫 작업* = `npm run build -w landing` 1회로 SW 산출물에
   키 인라인 확인. SvelteKit+Vite 의 `import.meta.env` 정적 치환은 SW 빌드에도 적용되는 표준 동작이라 **치환됨이 압도적 기대값**
   → §1.2 직독 그대로. *(미치환이 실측되면)* page→SW `postMessage` 키 전달로 패치 — **측정 후 설계**(양분기 동시 설계 = over-build,
   품질점검). 추가로 `pushsubscriptionchange` 가 `oldSubscription.options` 로 키를 보존(§1)하므로 fallback 의존도 자체가 낮음.
2. **iOS 16.4+ standalone aes128gcm 실배달** — 실기기 1대 수신 확인.
3. **iOS user-gesture 소실**(`await serviceWorker.ready` 가 제스처 끊는지) — 끊기면 `ready` 를 클릭 전 미리 확보.
4. **aes128gcm ece 바이트 프레이밍** — `tests/_attempts/pushHub/` 실브라우저 졸업([06] §5).
