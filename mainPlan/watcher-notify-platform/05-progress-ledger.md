# 05 — 진행 원장

## 상태: P1+P2 구현 완료(2026-06-30) · 운영자 롤아웃 게이트 대기

| 날짜 | 항목 | 상태 |
|---|---|---|
| 2026-06-28 | 설계 브리프 작성([00-design-brief.md](00-design-brief.md)) — 3계층·퍼블릭↔개인 통일·로컬 브리지·P1~P4 | ✅ |
| 2026-06-28 | 로컬 런타임 브리지 일반화 + 로컬 GPU 방향 노트([00b](00b-local-runtime-bridge-and-gpu.md)) | ✅ |
| 2026-06-28 | 6 분야 전문 패널 토론 + 통합(라이브러리·인프라/WebPush·프로덕트/UX·보안·로컬브리지·클러터비평) | ✅ |
| 2026-06-28 | PRD 문서 세트 합성(00~04 + README) | ✅ |
| 2026-06-30 | **IPO 토픽 데이터원 막힘 해소** — `scan('ipo')` 본진 졸업(a5bdfda35)으로 운영자 결정 3 의 "신규상장 축 있는지 확인 필요" 제거. IPO = 신규수주 동급 P2 토픽(러너 함수 1개·새 데이터 0) | ✅ |
| 2026-06-30 | **P1 허브 Worker** — `infra/workers/pushHub/` worker.js(3라우트·VAPID ES256·aes128gcm 2단HKDF·JOIN·allSettled·purge) + D1 schema/migrations + 하네스. **vitest-pool-workers 16/16** | ✅ |
| 2026-06-30 | **P1 크립토 게이트** — `tests/_attempts/pushHub/eceRoundTrip.mjs` 발신 암호화→UA 복호 평문일치+키격리+VAPID 검증 **16/16**(브라우저 전 R2 닫음) | ✅ |
| 2026-06-30 | **P1 수신 스택** — `service-worker.ts` 3리스너 + `NotifyOptIn.svelte`(2단게이트·iOS가드) + subscription/sanitize/platform 공유. **vitest 17/17·svelte-check 0** | ✅ |
| 2026-06-30 | **P1 발행 러너** — `.github/scripts/notify/`(send·hubClient·authHeaders·payload·sanitize) + notify-publish.yml + pushhub-test.yml + deploy-landing vitest게이트. **pytest** | ✅ |
| 2026-06-30 | **P2 공개 토픽** — watch.py(`eval_new_ipo`·`eval_new_orders` scan직독·sentNonce=커서) + notify-watch.yml(cron) + TOPIC_ALLOWLIST 4개 + monitorPipeline 등록. **러너 pytest 18/18** | ✅ |
| — | 운영자 롤아웃: Cloudflare 배포(D1·secret·VAPID·deploy) + GitHub vars/secret | ⏳ 운영자 |
| — | 운영자 롤아웃: landing UI 눈검수 후 push(자동 push 금지) | ⏳ 운영자 |
| — | P1 SHIP: 실기기 1대 aes128gcm 수신 확인(Chrome·iOS 16.4+) | ⏳ 운영자 |
| — | P3 개인 왓처(로컬 소유·브리지) — ≥2 소비자 실증 후 발견적 추출 | ⬜ 의도적 보류(YAGNI) |
| — | P4 모드B·패키징 | ⬜ 운영자 결정 게이트 |

## 배포 런북 (운영자 — 코드는 전부 green, 이것만 하면 활성)

```bash
# 1) VAPID 키쌍 + 발송토큰 생성
node tests/_attempts/pushHub/genVapid.mjs      # PRIV·PUB·SEND_TOKEN 출력

# 2) 허브 배포
cd infra/workers/pushHub
wrangler d1 create dartlab-push-hub            # database_id → wrangler.toml
wrangler d1 execute dartlab-push-hub --remote --file schema.sql
wrangler secret put VAPID_PRIVATE_KEY          # 1)의 PRIV
wrangler secret put PUSHHUB_SEND_TOKEN         # 1)의 SEND_TOKEN
# wrangler.toml [vars] VAPID_PUBLIC_KEY·VAPID_SUBJECT 기입
wrangler deploy                                # → https://dartlab-push-hub.<sub>.workers.dev

# 3) GitHub 설정 (Settings → Secrets and variables → Actions)
#   vars:    VITE_VAPID_PUBLIC_KEY = 1)의 PUB,  VITE_PUSHHUB_URL = 2)의 배포 URL
#   secret:  PUSHHUB_SEND_TOKEN    = 1)의 SEND_TOKEN (Worker secret 과 동일값 필수)

# 4) landing 눈검수 후 push → 배포 → 폰에서 PWA 설치 → '알림 켜기' → 실기기 수신 확인
```
설정 전까지 러너는 graceful no-op(RED 0). 설정 직후 다음 발행/cron 부터 자동 활성.

## 패널 산출 핵심 (통합자 확정)

- **수신 스택은 0부터** — `service-worker.ts` 셸캐시만, push 핸들러·pushManager·VAPID 전무(grep 0건).
- **왓처 ≠ 새 L2 엔진** — P1-P2 러너 plain 함수(게이트 비대상), P3 에서 synth/watch 발견적 추출.
- **`scan.orders` 이미 본진 졸업** — '신규수주' 토픽 새 데이터 0줄. 메모리 stale 정정 필요.
- **D1 = 2테이블·개인조건 0** — 개인화는 로컬 소유(재식별 회피).
- **`/send` 인증** — Bearer SEND_TOKEN + 결정적 nonce(품질점검서 HMAC 층 절단=독립 신뢰축 0). 발신자 인증 없으면 스팸/피싱 발사대.
- **PNA 미들웨어 신규 필수** — Starlette CORSMiddleware 는 PNA 헤더 미발급. pure-ASGI 추가.
- **capability 토큰** — 로컬 `/api` 무인증 + CORS 개방 = 악성 사이트 CSRF 면. 쓰기/ai/export 토큰 강제.

## 미해결 분기 → [04](04-phasing-scope-guardrails.md) §4 (운영자 결정)

## 비용 메모
- 패널 토론: 7 에이전트 · 531k 토큰 · 7분 24초.

## 다음 액션
1. 운영자: 위 배포 런북 4단계 수행(Cloudflare + GitHub 설정 + landing 눈검수 push).
2. 운영자: 실기기 1대 aes128gcm 수신 확인(P1 SHIP 게이트 마지막 항목).
3. (선택) 발송 위생 강화 — 토픽별 일일 cap·조용한시간(22~08 묶음)·24h dedupe(러너 측). 현재 sentNonce 멱등만.
4. (선택) P3 — ≥2 소비자(로컬 데몬) 실증 시 synth/watch 발견적 추출 + 개인 종목 알림.
