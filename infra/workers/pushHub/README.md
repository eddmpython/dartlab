# pushHub — dartlab Web Push 허브 Worker

구독 저장 + Web Push 발송만 하는 thin Cloudflare Worker. 감지 지능(무엇을 알릴지)은 dartlab(gather·scan
SSOT)에 살고, 허브는 **구독 보관 + VAPID 서명 + push 발송**만 한다. 크롤·판정·LLM 0.

설계 정본: [`mainPlan/watcher-notify-platform/`](../../../mainPlan/watcher-notify-platform/) (02 계약 · 06 허브 상세 · 08 운영).

## 라우트 3개

| method · path | 인증 | 동작 |
|---|---|---|
| `POST /subscribe` | 무인증 공개 | endpoint(push 호스트 화이트리스트)·키·토픽 검증 → `subscriptions` UPSERT + `topicSubs` 교체 |
| `DELETE /subscribe` | 무인증 공개 | `{endpoint, topics?}` — 부분/전체 해지(삭제권) |
| `POST /send` | Bearer + nonce | 러너 전용. topic 브로드캐스트 또는 endpoints[] 타겟 → aes128gcm 암호화 → push POST |

`/send` 는 server-to-server라 CORS·OPTIONS 없음. Bearer(`PUSHHUB_SEND_TOKEN` 상수시간 비교) + `X-DL-Nonce`
(`sha1(topic:slug)` 멱등·replay 거절) + `X-DL-Ts`(±300s 윈도). sentNonce 테이블이 곧 last-seen 커서.

## 암호화 (순수 WebCrypto · npm 0)

- **VAPID JWT** = ES256(`crypto.subtle.sign('ECDSA' SHA-256)` → P1363 raw 64B = JWS 그대로, DER 변환 0).
- **본문** = aes128gcm(RFC 8291 2단 HKDF: ECDH + auth → IKM, salt → CEK·NONCE → AES-128-GCM). 제목·본문 실제 표시, iOS 표준 경로.

## D1 스키마

`subscriptions(endpoint PK, p256dh, auth, uaClass, createdAt, lastSeenAt)` · `topicSubs(endpoint, topic, …)`
PK(endpoint,topic) FK CASCADE · `sentNonce(nonce PK, ts)`. **개인조건·user_id·종목 컬럼 영구 0**(재식별 surface 회피).

## 배포

```bash
cd infra/workers/pushHub
wrangler d1 create dartlab-push-hub                 # → wrangler.toml database_id
wrangler d1 execute dartlab-push-hub --remote --file schema.sql
wrangler secret put VAPID_PRIVATE_KEY               # pkcs8 base64url
wrangler secret put PUSHHUB_SEND_TOKEN              # GitHub Actions secret 과 동일값 필수(다르면 전 발송 401)
# wrangler.toml [vars] VAPID_PUBLIC_KEY·VAPID_SUBJECT 기입 후
wrangler deploy
```

VAPID 키쌍 생성은 [`tests/_attempts/pushHub/genVapid.mjs`](../../../tests/_attempts/pushHub/genVapid.mjs).

## 테스트

```bash
cd infra/workers/pushHub && npm ci && npm test     # vitest-pool-workers (401/409/purge·fan-out·JWT)
```

⚠ 하네스 config 는 **설치한 `@cloudflare/vitest-pool-workers` 버전의 공식 템플릿**에서 스캐폴드한다(버전마다
API 가 달라 손코딩 금지, [08 §4]). `vitest.config.js` 의 `defineWorkersConfig`·`miniflare.d1Databases`·`migrations`
경로가 설치 버전과 맞아야 첫 `npm test` green. 본 디렉터리 config 는 0.8.x 계열 기준 초안.
