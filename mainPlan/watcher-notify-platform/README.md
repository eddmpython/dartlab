# 왓처·알림 플랫폼 (watcher-notify-platform)

DartLab 을 "보고 끝"이 아니라 "**변화가 생기면 먼저 알려주는**" 플랫폼으로 만든다. PWA 웹 푸시로
새 글·카드 발행, 그리고 (단계적으로) 공시·주가·IPO 같은 시장 이벤트를 사용자 기기로 알린다.

## 한 줄 아키텍처

```
감지 지능 = dartlab(gather·scan SSOT 직독)   ·   스케줄 = GitHub Actions cron   ·   배달 = Cloudflare thin 허브
```

감지는 dartlab 이 사는 곳에(런타임-SSOT 정합), Cloudflare 는 구독 저장 + 발송만. 크롤·판정 재구현 0.

## 문서 지도

| 문서 | 내용 |
|---|---|
| [00-design-brief.md](00-design-brief.md) | 패널 토론 입력(원안). 역사 보존용 |
| [00b-local-runtime-bridge-and-gpu.md](00b-local-runtime-bridge-and-gpu.md) | 로컬 브리지 일반화 + 로컬 GPU 방향(별 탐색) |
| [00-product-prd.md](00-product-prd.md) | 제품 PRD — 문제·사용자·약속(MUST/SHOULD/KILL)·정정 |
| [01-architecture.md](01-architecture.md) | 3계층·왓처 물리적 자리·import inversion·졸업 트랙 |
| [02-hub-d1-receiving.md](02-hub-d1-receiving.md) | 허브 계약 3라우트·D1 2테이블·VAPID·발신 인증·수신단 구축 |
| [03-local-bridge-personalization.md](03-local-bridge-personalization.md) | 개인화 분기·PNA 미들웨어·capability 토큰·watch.json |
| [04-phasing-scope-guardrails.md](04-phasing-scope-guardrails.md) | P1~P4·잘라낸 것(scope cut)·non-goal·운영자 결정·파일 계획 |
| [05-progress-ledger.md](05-progress-ledger.md) | 진행 원장 |
| [06-p1-hub-worker.md](06-p1-hub-worker.md) | **P1 상세설계** — pushHub worker.js·VAPID JWT·aes128gcm·schema·wrangler (build-ready) |
| [07-p1-client-receiving.md](07-p1-client-receiving.md) | **P1 상세설계** — SW 3 리스너·NotifyOptIn·공유모듈·env 주입 |
| [08-p1-publish-ops-test.md](08-p1-publish-ops-test.md) | **P1 상세설계** — 발행 러너·독립 워크플로·배포/롤백·SHIP 게이트 |
| [09-evaluation-ledger.md](09-evaluation-ledger.md) | **PRD 평가 원장** — 갭 소진 추적(라운드별 PASS/PARTIAL + 폐쇄) |

## 상태

PRD 합성(6 분야 패널) + P1 구현급 상세설계(06~08) + 적대적 평가 4 라운드 → 빌드-ready 수렴 → **P1+P2 구현 완료(2026-06-30)**.
구현·검증 = [05 진행원장](05-progress-ledger.md). 코드·테스트 전부 green(허브 16 + 러너 18 + landing 17 + 크립토 16),
커밋 완료. **남은 = 운영자 롤아웃 게이트**: ① Cloudflare 배포(D1·secret·VAPID·wrangler deploy) ② landing UI 눈검수 후
push ③ 실기기 1대 aes128gcm 수신 확인(P1 SHIP). 런북 = [05 §배포](05-progress-ledger.md) · [08 §3](08-p1-publish-ops-test.md).
P3(개인 왓처·로컬 브리지)·P4 는 PRD 가 정한 게이트(≥2 소비자 실증·운영자 결정)대로 **의도적 보류**(YAGNI).

## 핵심 정정 (브리프 원안 → 패널 확정)

1. **"받는 쪽(service-worker)은 이미 있다"는 거짓.** `service-worker.ts` 는 셸 캐시(install/activate/fetch)만,
   `push`·`notificationclick`·`pushsubscriptionchange` 0. landing 전역에 `pushManager`·VAPID·`requestPermission` 0건.
   → **P1 = 수신 스택을 0에서 구축**(5종).
2. **왓처 = 새 L2 엔진 아님.** P1-P2 는 GHA 러너 plain 함수(`.github/scripts/notify/`), `_attempts` 게이트 비대상.
   레지스트리·synth 모듈은 P3 에서 *발견적으로* 추출(YAGNI).
3. **`scan.orders`(신규수주) 축은 이미 본진 졸업.** 메모리 `project_order_flow_scan` "본진 미투입" 표기 stale →
   '신규수주' 토픽은 새 데이터 0줄로 P2 첫 레퍼런스.
4. **개인 조건(종목·임계)은 D1 에 영구 미저장.** endpoint+종목 = 재식별 surface. 개인화는 로컬 소유.
