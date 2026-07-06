# 06 — P1 상세설계: pushHub Worker (build-ready)

`infra/workers/pushHub/`. 순수 WebCrypto(npm 0) → `siteSignals` 형판(`nodejs_compat` 불필요).
본 문서는 평가 라운드1의 갭을 닫은 확정본. 닫힌 갭은 [09-evaluation-ledger.md](09-evaluation-ledger.md) 참조.

## 0. P1 페이로드 = aes128gcm (라운드1 결정)

P1 을 VAPID-only 빈 본문에서 **aes128gcm 암호화 본문으로 격상**한다. 이유: 빈 본문은 (1) 글 제목이
기기에 안 보이고(고정문구만) (2) `web.push.apple.com` 의 빈-본문 수락이 미검증이다. aes128gcm 은
제목을 띄우고 iOS 표준 경로라 두 갭을 동시에 닫는다. 비용(ece 인코딩 정확성)은 **실브라우저 1대 ece
라운드트립 게이트**(P1 SHIP 필수)로 닫는다 — `tests/_attempts/pushHub/` 졸업을 P1 으로 끌어온다.

## 1. 프로토콜 사실 (1차 사료 검증)

| 사실 | 출처 | 영향 |
|---|---|---|
| VAPID Authorization 단일헤더 `vapid t=<JWT>, k=<base64url(공개키 raw 65B)>` | RFC 8292 §3 | 헤더 1줄 |
| `crypto.subtle.sign('ECDSA')` = IEEE **P1363 raw 64B**(r‖s) = JWS ES256 그대로 | MDN | DER 변환 0 → npm 0 |
| `TTL` 헤더 필수, 누락=400 | RFC 8030 §5.2 | 항상 부착 |
| aes128gcm: ECDH(구독 p256dh) + HKDF-SHA256 + AES-128-GCM, `Content-Encoding: aes128gcm` | RFC 8291 | §3 본문 암호화 |
| 성공=201(200/202도), 만료=404/410 | web.dev | inline purge |
| `aud`=`new URL(endpoint).origin`, `exp`≤24h | RFC 8292 §2 | origin별 JWT 캐시 |

## 2. 라우트 계약 (3개)

**디스패치 표**(`fetch(req,env)` 단일 진입, siteSignals 형판 `isOriginAllowed`/`corsHeaders` 재사용):

| method · path | 처리 | CORS/OPTIONS |
|---|---|---|
| `OPTIONS /subscribe` | 204 preflight | CORS echo |
| `POST /subscribe` · `DELETE /subscribe` | 핸들러 | CORS echo |
| `POST /send` | 핸들러 | **CORS 없음**(server-to-server, OPTIONS 미수신) |
| 그 외 | 404 | — |
| `/subscribe` 비-POST/DELETE | 405 | — |

### POST /subscribe (무인증 공개)
- body: `{endpoint, keys:{p256dh, auth}, topics:[]}`
- 검증: `endpoint` host ∈ {`fcm.googleapis.com`, `web.push.apple.com`, `*.push.services.mozilla.com`}(SSRF 차단) ·
  `p256dh`/`auth` base64url(**padding 허용** `/^[A-Za-z0-9_-]+={0,2}$/`) · `topics ⊆ TOPIC_ALLOWLIST`
- 동작: `subscriptions` UPSERT(endpoint PK, idempotent) + `topicSubs` 전량 교체(`batch` 단일 명령군)
- CORS: `ALLOW_ORIGIN` echo(siteSignals 패턴)

### DELETE /subscribe (삭제권)
- body `{endpoint, topics?}`(스키마 양 spec 공유, `Content-Type: application/json` 필수). topics 지정=부분해지,
  남은 토픽 0 또는 topics 생략=전체삭제. **D1 은 FK 를 기본 ON 으로 강제**(끌 수 없음, `defer_foreign_keys` 만 지원)
  이므로 `ON DELETE CASCADE` 가 실제 발동 — subscriptions 1행 삭제 시 topicSubs 자동삭제. `deleteEndpoint` 의 두
  테이블 명시 DELETE 는 CASCADE 의존을 줄이는 *방어적 중복*일 뿐 FK-off 회피가 아니다(라운드2 정정).

### POST /send (러너 전용 — Bearer + nonce, CORS 없음)
- **(1)** `Authorization: Bearer <PUSHHUB_SEND_TOKEN>`(상수시간 비교) — 발송 권한
- **(2)** `X-DL-Nonce` = `sha1(f"{topic}:{slug}")`([08 §2]) → `sentNonce` unique insert, PK 충돌=409 replay 거절 + (topic,slug) 멱등.
  `X-DL-Ts` 윈도 ±300s 로 replay 창 닫음(서명 없음)
- body `{topic, notification:{title,body,url,tag}}` 또는 `{endpoints:[], notification}`
- **CORS echo·OPTIONS·X-DL-* Allow-Headers 없음** — server-to-server 라 불요
- ⚠ **HMAC 서명층 제거**(품질점검 절단): `PUSHHUB_SIGN_KEY` 와 `PUSHHUB_SEND_TOKEN` 이 *같은 GHA secrets* 에 살아
  독립 신뢰축이 아님(Bearer 유출=SIGN_KEY 도 유출). HMAC 이 막는 위협("Bearer 알지만 SIGN_KEY 모름") 미성립 → secret 4→3종,
  06 §3 바이트 SSOT·`test_authHeaders` 서명 회귀 제거. *belt-and-suspenders 원하면 운영자가 되돌릴 수 있는 1줄 결정.*

## 3. /send 성능 — 대상 조회·발송 동시성·청소

**대상 조회 = JOIN 1회**(N+1 D1 쿼리 금지):
```sql
SELECT s.endpoint, s.p256dh, s.auth FROM topicSubs t JOIN subscriptions s ON s.endpoint=t.endpoint WHERE t.topic=?
```
`topicSubsTopicIdx` + `subscriptions` PK 가 커버(추가 인덱스 0). endpoints[] 타겟 모드는 `WHERE endpoint IN (…)`.

**발송 동시성(직렬 금지 — 본 플랫폼 유일한 N-fan-out)**:
- **VAPID JWT origin별 1회 메모**: `const jwtByOrigin = {}` (push origin = fcm/apple/mozilla 3개뿐), `getPrivKey`/`importKey('pkcs8')` 도 요청당 1회. 구독마다 재서명 금지(ECDSA N회 낭비 CPU).
- 각 구독 `sendOne(sub)` = aes128gcm 암호화 + push POST 를 **`Promise.allSettled` 청크(P=20)** 로 — CF free subrequest
  50/req·push 서비스 per-conn 한도 존중. ⚠ **직렬 `for-await pushOne` 금지**(N=200 → 30~60s = Worker wall-clock/CPU 한도 위협).

**응답·청소**: 2xx=sent · 404/410=`toPurge[]` 수집 후 **루프 끝 `DELETE … WHERE endpoint IN (…)` batch 1회**(inline 건별
DELETE 금지, CASCADE 가 topicSubs 정리) · 429/5xx=보존(failed). 응답 `{sent, pruned, failed}` → 러너 헬스게이트([08 §2]).

## 4. VAPID JWT ES256 (crypto.subtle, npm 0)

```js
async function makeVapidJwt(audOrigin, env) {
  const header = b64url(JSON.stringify({ typ:'JWT', alg:'ES256' }));
  const payload = b64url(JSON.stringify({ aud: audOrigin, exp: nowSec()+JWT_TTL_S, sub: env.VAPID_SUBJECT }));
  const input = `${header}.${payload}`;
  const sig = await crypto.subtle.sign({ name:'ECDSA', hash:'SHA-256' }, await getPrivKey(env), enc.encode(input));
  return `${input}.${b64url(sig)}`;   // sig = P1363 raw 64B, 변환 0
}
```

**키 형식 SSOT**: `VAPID_PRIVATE_KEY` = **pkcs8 DER 의 base64url**(`importKey('pkcs8', …)`).
`VAPID_PUBLIC_KEY` = **uncompressed 65B(0x04‖x‖y)의 base64url**(k= 파라미터·`applicationServerKey` 공용).
생성(1회):
```bash
# Node: crypto.subtle.generateKey ECDSA P-256 → exportKey('pkcs8')·('raw') → base64url
#  privateKey: pkcs8 DER → basenc --base64url | tr -d '='   →  wrangler secret put VAPID_PRIVATE_KEY
#  publicKey : raw 65B   → basenc --base64url | tr -d '='   →  wrangler.toml [vars] VAPID_PUBLIC_KEY + VITE_VAPID_PUBLIC_KEY
```

## 5. aes128gcm 본문 암호화 (RFC 8291, 순수 WebCrypto)

**평문 SSOT**: `plaintext = JSON.stringify(payload.notification)` (= `{title,body,url,tag}` *서브객체만*, `{topic,…}`
봉투 아님). 07 §1 push 핸들러의 `event.data.json()` 이 이걸 그대로 받음.

키 유도는 **RFC 8291 §3.4 의 2단계 HKDF**다(1단계로 뭉개면 전 기기 복호 실패). 각 구독별(`p256dh`·`auth`마다) 1회:
```
as = 서버 임시 ECDH 키쌍(P-256). ua_pub = 구독 p256dh(raw 65B). as_pub = as 공개키(raw 65B). salt = random 16B.
ecdh   = ECDH(as_priv, ua_pub)                                                    # 32B
PRK_key = HMAC-SHA256(key=auth_secret, msg=ecdh)                                  # 1단계 extract
keyinfo = "WebPush: info" || 0x00 || ua_pub || as_pub
IKM     = HMAC-SHA256(key=PRK_key, msg=keyinfo || 0x01)[:32]                      # 1단계 expand
PRK     = HMAC-SHA256(key=salt, msg=IKM)                                          # 2단계 extract(salt=랜덤16B, auth 아님!)
CEK     = HMAC-SHA256(key=PRK, msg="Content-Encoding: aes128gcm" || 0x00 || 0x01)[:16]   # 2단계 expand
NONCE   = HMAC-SHA256(key=PRK, msg="Content-Encoding: nonce"     || 0x00 || 0x01)[:12]
record  = AES-128-GCM(CEK, NONCE, plaintext || 0x02)                             # 0x02 = 단일 record delimiter
body    = salt[16] || rs[4]=uint32(4096) || idlen[1]=65 || keyid=as_pub[65] || record   # RFC8188 헤더 + 본문
헤더: Content-Encoding: aes128gcm, TTL, Urgency, Authorization: vapid t=,k=
```
**구현 = 검증된 참고구현 포팅** — RFC 바이트를 손으로 옮기지 않고 `web-push` JS `encrypt`(WebCrypto)를 포팅한다.
**졸업 게이트(P1 SHIP 필수)**: `tests/_attempts/pushHub/` 에서 **Chrome 1대 + iOS 16.4+ standalone 1대 *양쪽*
ece 수신 성공**(둘은 record-size·헤더 엄격도가 달라 Chrome 통과≠Apple 수락). 이 게이트가 곧 iOS aes128gcm
실배달([08 §5])의 선행 — 미졸업 시 P1 출시 금지.

## 6. schema.sql

```sql
CREATE TABLE IF NOT EXISTS subscriptions (
  endpoint TEXT PRIMARY KEY, p256dh TEXT NOT NULL, auth TEXT NOT NULL,
  uaClass TEXT NOT NULL DEFAULT 'other', createdAt TEXT NOT NULL, lastSeenAt TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS topicSubs (
  endpoint TEXT NOT NULL, topic TEXT NOT NULL, subscribedAt TEXT NOT NULL,
  PRIMARY KEY (endpoint, topic), FOREIGN KEY (endpoint) REFERENCES subscriptions(endpoint) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS topicSubsTopicIdx ON topicSubs (topic);
CREATE TABLE IF NOT EXISTS sentNonce (nonce TEXT PRIMARY KEY, ts INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS sentNonceTsIdx ON sentNonce (ts);
```
- 개인조건·user_id·종목 컬럼 영구 0. **D1 FK 기본 ON → `deleteEndpoint` = `DELETE FROM subscriptions` 1줄, topicSubs 는
  CASCADE 자동**(방어적 중복 DELETE 제거 — 품질점검). 부분해지(topics 지정)만 topicSubs 타겟 DELETE.
- **멱등 단일효과 쓰기**(batch 원자성 비의존, SSOT): `subscriptions` UPSERT(PK, 재실행 무해) + topicSubs `DELETE WHERE endpoint=?`
  + `INSERT OR IGNORE`. 게이트=로컬 round-trip 기능정확성(Miniflare≠원격 batch 의미). 원자성 불요. [02 §2]·[08 §6] 은 포인터.

## 7. wrangler.toml + 상수

```toml
name = "dartlab-push-hub"
main = "worker.js"
compatibility_date = "2024-12-01"
[[d1_databases]]
binding = "PUSHHUB_DB"
database_name = "dartlab-push-hub"
database_id = "replace-with-cloudflare-d1-database-id"
[vars]
ALLOW_ORIGIN = "https://eddmpython.github.io"
VAPID_SUBJECT = "mailto:replace-with-ops-email"
VAPID_PUBLIC_KEY = "replace-with-base64url-uncompressed-public-key"
# secrets (wrangler secret put): VAPID_PRIVATE_KEY(pkcs8 base64url)·PUSHHUB_SEND_TOKEN  (SIGN_KEY 제거=3종)
```
상수: `TOPIC_ALLOWLIST = {'blogPublish','cardPublish'}` (**newOrders 제외** — 운영자 결정#3 확정·P2 scan.orders 졸업 후 추가).
`NONCE_WINDOW_S=300`, `JWT_TTL_S=12h`, `PUSH_TTL_S=4d`. rate limit = Cloudflare 대시보드 WAF Rule(`/subscribe` IP/분, wrangler 코드 0).

## 8. 가드 적합성
런타임-SSOT(저장+발송만)✓ · `_attempts` = aes128gcm ece 졸업만 대상, Worker 배선은 직접✓ · `infra/workers/pushHub/` 컨벤션✓ ·
외부본문 = 러너 sanitize 후 발송(Worker 본문 가공 0)✓ · 덕지덕지(라우트 3·테이블 3, 확장점 선설치 0)✓
