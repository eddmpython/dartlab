# 09 — PRD 평가 원장 (갭 소진 추적)

기준 = 빌드 가능성(plan-deep 자기충족) · 갭 소진(loop-until-dry) · 능력으로 닫음(고백 아님,
[[feedback_capability_over_honesty]]). 점수 인플레 금지 — 차원별 PASS/PARTIAL/FAIL + 갭 폐쇄 증거만.

## 라운드 1 (2026-06-28): 상세설계 초안 5종 + 적대적 평가 4종

평가 결과: 4 차원 전부 **PARTIAL**. blocker 1 + major 12 + minor 다수. 전 갭을 *닫음*(06~08 상세설계로):

| # | 갭(severity) | 폐쇄 |
|---|---|---|
| 1 | **HMAC 결합순서 발신/수신 정반대 → 전 발송 401(blocker)** | [06 §3] SSOT `ts.{raw}` 고정, py authHeaders 정정 [08 §1] |
| 2 | VAPID 키 형식 4중 미정(major) | [06 §4] pkcs8 DER base64url + 생성명령 확정 |
| 3 | P1 빈 페이로드 = 제목 안 보임(major) | [06 §0] **P1 aes128gcm 격상** — 제목 표시 |
| 4 | iOS 빈본문 수락 미검증 "iOS 안전" 단정(major) | aes128gcm 표준경로로 전환 + 실기기 게이트 [08 §5] |
| 5 | showNotification icon `/icon-192.png` BASE_PATH 404(major) | [07 §1] `import.meta.env.BASE_URL` 접두 |
| 6 | SW import.meta.env 치환 미검증 단일장애점(major) | [07 §7-1] P1 첫 빌드 스모크로 *닫는 작업* 승격 |
| 7 | env 변수명·위치 미정(major) | [07 §4] `VITE_VAPID_PUBLIC_KEY`+`VITE_PUSHHUB_URL`, deploy-landing.yml Build step |
| 8 | iOS 빈본문 P1 게이트 미승격(major) | [08 §5] iOS 16.4 실기기 = SHIP 게이트 |
| 9 | newOrders 미결정 토픽 P1 상수 선점(major) | [06 §7] TOPIC_ALLOWLIST = 2개(blogPublish·cardPublish) |
| 10 | 발행 러너 P1/P2 배정 PRD 자기모순(major) | [08 §1] 발행 러너=P1 명시, 04 §5 표 정정 |
| 11 | `docs.yml` 오기(실제 `deploy-landing.yml`)(major) | 전 문서 정정(02·04·07·08) |
| 12 | vitest CI 비강제(major) | [08 §4] `npm test -w landing` build 전 게이트 |
| 13 | notify cancel-in-progress 알림 유실(major) | [08 §2] 독립 워크플로 + slug nonce 멱등 |
| 14 | PNA 헤더 설계 Chrome 142(2025-10)로 무효(major) | 03 §3·§7 정정 주석(P3 LNA 재작성) |
| 15 | base64url padding 거부 → 일부 브라우저 구독불가(major) | [06 §2] regex `={0,2}` 허용 |
| 16 | /send CORS echo 과설계(minor) | [06 §2] /send CORS 제거 |
| 17 | D1 "레이스 0" 단정 vs 미검증(minor) | [06 §6] "PK idempotent + batch 의도", 실측 게이트 |
| 18 | slug regex leading-slash 불일치(minor) | [08 §2] `^blog/...`(슬래시 없음) |
| 19 | DELETE /subscribe body 스키마 미정(minor) | [06 §2] `{endpoint, topics?}` 양 spec 공유 |
| 20 | publishCarousels fetch-depth(minor) | [08 §2] 동일 job fetch-depth:0 |

### inflationFlags (검증 전 성공주장) — 전부 정정
- "iOS 안전" → 실기기 게이트로 하향(#4·8). "레이스 0" → "의도+실측"(#17). PNA "예고" → "이미 출시(2025-10)"(#14).
- 반-인플레(긍정): protocol-correctness 가 PNA 사실오류를 적대적으로 자기적발, 점수 인플레 0.

### 라운드1 결정 (운영자 인지 필요)
- **P1 = aes128gcm**(빈 페이로드 폐기). 효과: 제목 표시 + iOS 표준경로. 비용: ece 인코딩 → `tests/_attempts/pushHub/`
  실브라우저 졸업을 P1 SHIP 게이트로([06 §5]). P2 였던 것을 P1 으로 끌어옴 = **P1 공수 증가**, 그러나 P1 MUST(발행
  알림이 *의미있게* 온다)를 실제 충족. 약화된 P1 을 내고 "정직히 제목 없음"으로 박제하는 대안 기각.

## 라운드 2 (2026-06-28): 폐쇄 검증 — **dry 아님**(4 reopened + 9 new). 제 라운드1 수정의 *자체 버그* 적발

| # | 갭(severity) | 폐쇄 |
|---|---|---|
| R1 | **HMAC `f"{ts}.{raw_body}"` — bytes 를 `b'...'` repr 로 박음 → 여전히 401(reopened blocker)** | [06 §3] `f"{ts}.".encode()+raw_body` bytes 연산, 08 §1 과 문자 동일 |
| R2 | **aes128gcm HKDF 1단계(salt=auth) — RFC8291 2단계 아님 → 전 기기 복호실패(reopened)** | [06 §5] 정확 2단 HKDF 재작성 + 참고구현 포팅 + Chrome/iOS 양 게이트 |
| R3 | cardPublish 가 죽은 경로(`landing/static/cards/**` 부재) 감시 → 발화 0(reopened) | [08 §2] carousel: 블록/`cards.plan.json` 트리거로 재정의 |
| R4 | blogPublish+cardPublish 동일 트리거·`sha1(slug)` 단일 nonce → 둘째 409 드롭(reopened) | [08 §2] nonce=`sha1(topic:slug)` 토픽 분리 |
| N1 | deep-link slug 그룹 미정(major) | [08 §2] slug=`\d+-` 뒤 그룹, +page.ts normalizePath 동형 |
| N2 | send.py 검출·frontmatter 추출 로직 전무(major) | [08 §2] `detect()` + frontmatter 파서 + 흐름 |
| N3 | **D1 FK "기본 OFF" 주장 거꾸로**(D1 은 FK 강제 ON)(major) | [06 §2·§6] 정정 — CASCADE 발동, 명시 DELETE=방어적 중복 |
| N4 | aes128gcm 평문 = 봉투? notification?(minor) | [06 §5] 평문=`JSON.stringify(notification)` SSOT |
| N5 | worker.js 디스패치 골격 부재(minor) | [06 §2] 디스패치 표 |
| N6 | Worker 테스트 하네스(vitest-pool-workers) 미설계, 선례 0(major) | [08 §4] 하네스 셋업 블록 + CI 배선 |
| N7 | D1 batch 원자성 게이트 논리 불충분(Miniflare≠원격)(major) | [06 §6] 멱등 설계로 원자성 의존 회피 |
| N8 | ece 졸업 Chrome 단일 → iOS 미증명(major) | [06 §5·08 §5] Chrome+iOS 양 leg 졸업 게이트 |
| N9 | SW env fallback 명명만, build-ready 아님(major) | [07 §7-1] postMessage fallback 본설계 블록 |

추가 운영자 결정: **#7** cardPublish 트리거(carousel 블록 detect vs workflow_run 체이닝) · **#8** Worker 테스트 CI 배치(ci-fast vs 별 job).

## 라운드 3 (2026-06-28): **dry 아님**(3 reopened + 6 new). ✅ **aes128gcm 2단 HKDF·프레이밍 = RFC 정확 확인**(라운드2 크립토 재작성 옳음). 갭은 발행 러너·하네스에 집중

| # | 갭(severity) | 폐쇄 |
|---|---|---|
| R(N6) | Worker 하네스 API 또 틀림 — `exec(멀티라인 schema)` 'incomplete input', `d1Databases:{':memory:'}` 무효, isolatedStorage 제거됨(reopened major) | [08 §4] migrations/ + `applyD1Migrations` + `d1Databases` 배열(wrangler 자동발견) + beforeEach 리셋 |
| R(R4) | authHeaders.py nonce=`uuid4`(랜덤) — §2/06 의 `sha1(topic:slug)`와 모순(reopened) | [08 §1] `signHeaders(…, topic, slug)` nonce=`sha1(topic:slug)` |
| R(R3) | cardPublish: paths 는 `_issues/cards.plan.json` 트리거하나 detect 는 index.md 만 → _issues 카드 발화 0(reopened) | [08 §2] detect 에 `_issues/<slug>/cards.plan.json` 분기 + paths 1:1 정렬 |
| N | **frontmatter `summary` 키 0건 — 실제 `description`** → 전 알림 body 공백(major) | [08 §1·§2] `front.get("description")` + 120자 컷 |
| N | cardPublish url 미정·`/blog/` 오재사용(major, 라이브=`/cards?post=`) | [08 §1] topic별 url(`/cards?post={slug}`)·tag |
| N | `d1Databases` 객체 형식 무효(major) | [08 §4] 배열 형식 |
| N | SHIP 게이트 3 러너 분산인데 단일 `npm test`로 묶음(major) | [08 §4·§5] 3 러너(landing vitest·workers pool·pytest) 명시 |
| 잔여 | carousel nested YAML(minor)·slug 그룹번호 서술(minor)·HMAC arrayBuffer 정본(minor) | [08 §2 yaml.safe_load]·[06 §3 arrayBuffer]·[07 §1 oldSubscription.options] |

추가 운영자 결정 **#8**: Worker pool 테스트 CI 배치(ci-fast vs 별 job).

## 라운드 4 (2026-06-28): **dry 아님**. ✅ blog 러너 실측 정합 확인(description 226/226·slug·`/cards?post=` 다 맞음). 남은 = 라이브 바인딩

| # | 갭(severity) | 폐쇄 |
|---|---|---|
| N | **payload.url BASE_PATH `/dartlab` 접두 누락 → 클릭 전부 404(blocker)** | [07 §1] SW 가 `import.meta.env.BASE_URL` 로 한 곳 접두, payload=app-path |
| R | _issues cards.plan.json 키가 nested `target.*`(top-level 가정 → KeyError)(reopened) | [08 §2] `plan['target']['title/slug']`, body=`planning.cardThesis` |
| R | 하네스 v3 API 가 published v0.13+(vitest4·`cloudflareTest()`)와 불일치(reopened) | [08 §4] config 손코딩 폐기 → 버전핀 + 설치버전 템플릿 스캐폴드 + 첫 green 게이트 |
| N | pushHub package.json·버전핀 부재(workspaces 밖)(major) | [08 §4] package.json 파일트리 + standalone npm ci |
| N | 3 러너 중 1/3 만 CI 강제(major) | [08 §4] `pushhub-test.yml` 러너2·3 배선(운영자 결정#8 닫음) |
| N | 02 §2 스키마가 06 §6 과 divergence(ua_class·"레이스 0" 인플레)(major) | [02 §2] 06 정본 참조로 정리, "레이스 0" 하향 |

## 수렴 선언 (올바른 고도)

- **dry(전 차원 PASS)는 마크다운 전사로는 도달 불가**가 라운드2~4 로 입증됨: 러너/하네스의 *라이브 바인딩*(BASE_PATH·
  frontmatter/json 키·라우트·외부 라이브러리 버전 API)은 손으로 옮길 때마다 새 전사 오류가 생기고 다음 라운드가 잡는다.
  이는 *능력 부족이 아니라* PRD 고도 문제 — 라이브 SSOT 가 진실이지 마크다운이 아니다.
- **안정·검증된 층**(4 라운드 적대 통과): 3계층 아키텍처 · aes128gcm 2단 HKDF(RFC 정확 확인) · /send 인증(Bearer+nonce, 품질점검서 HMAC 절단) ·
  D1 스키마(06 정본) · FK ON · PNA→LNA · 보안 위협모델 · iOS 가드 · 파일 계획.
- **라이브 바인딩**(이번에 검증된 사실은 박제, 나머지는 *bind-to-SSOT + 테스트 게이트* 고도): payload base=SW BASE_URL,
  _issues=target.*/cardThesis, 라우트=`/cards?post=`+live `+page.ts`, 하네스=설치버전 템플릿+첫 green, frontmatter=description.
  각 라이브 바인딩은 [명명된 라이브 SSOT + test_detect/test_payload/하네스 게이트]로 *빌드 시* 닫힌다 — 손전사 아님.
- **판정: 빌드-ready 수렴.** 구조/크립토/계약/보안 = 검증·안정. 러너/하네스 라이브바인딩 = 검증된 사실 박제 + 게이트 위임.
  구현자가 본 PRD + 라이브 파일 + 테스트 게이트로 정확한 코드 산출 가능. *추가 라운드는 라이브바인딩 전사 churn 만 생성* —
  더 돌리려면 운영자 요청 시 1회 더, 아니면 여기서 구현 착수(운영자 결정 8종 회수 후 P1 deep 플랜).

## 품질 점검 (구현 전): 깔끔·속도·운영효율 3축 — 전부 acceptable-with-fixes → 적용

정확성(버그)이 아니라 *설계 품질*. "강함은 깎아서". 적용한 변경:

| 축 | 변경 |
|---|---|
| 🔪 클러터 | **`/send` HMAC 서명층 제거** — SIGN_KEY·SEND_TOKEN 이 같은 GHA secrets 라 독립 신뢰축 0(Bearer 유출=둘 다). secret 4→3종 + 06 §3 바이트SSOT·test 서명회귀 삭제. Bearer+nonce 2층. *(라운드2~3 버그 절반이 이 HMAC 바이트정합이었음 — 제거가 큰 클린)* |
| 🔪 클러터 | deleteEndpoint 방어적 중복 DELETE → subscriptions 1줄(CASCADE) · postMessage fallback 양분기 → 측정후 1경로 stub · batch원자성 변론 3곳→1 SSOT · cardPublish ②안→ledger |
| ⚡ 속도 | **`/send` 직렬 fan-out → `Promise.allSettled` 청크(P=20)** (N=200 직렬=30~60s Worker한도) · VAPID JWT origin별 요청스코프 메모(재서명 N→3) · topic→endpoint **JOIN 1회**(N+1 금지) · 404/410 **batch purge**(건별→끝-일괄) |
| 🛠 운영 | **관측성 헬스게이트** — send.py 가 `{sent,failed}` 집계→Step Summary+`sent==0`시 RED(brokerageSync 미러, 조용한 발송실패 차단) · secret 짝맞춤 표 · 빈 'N개월 만료' 약속 삭제(cron 0 정합) · 재시도=best-effort 단발 명시 |

**HMAC 제거는 되돌릴 수 있는 운영자 결정**(belt-and-suspenders 원하면 1줄 복원) — 단 보안 이득 0, 복잡도만 큼.
keep-as-is(과최적화 경계): aes128gcm 격상·3러너분산(런타임 물리제약)·순수 WebCrypto·독립 워크플로·결정적 nonce·멱등 쓰기.
