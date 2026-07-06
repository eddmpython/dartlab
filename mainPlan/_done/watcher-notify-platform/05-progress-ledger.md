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
| 2026-07-03 | **발송위생** . 토픽별 cap(aa57e02ae). 24h dedupe=허브 sentNonce 영구멱등·조용한시간=cron 시각(17시 KST) 구조 회피로 각각 불요 판정(watch.py 주석 박제) | ✅ |
| 2026-07-03 | **newIpo 딥링크 격상** . 클릭 url `/terminal?ipo=1` = 터미널 IPO 공모 다이얼로그 자동 오픈(발굴 리스트 + 로컬 6카테고리 리포트, 알림→인사이트 루프 완결). 러너 pytest 7/7 | ✅ |
| 2026-07-03 | **newOrders 딥링크 파리티** . 옛 클릭 url `/terminal`(기본종목 삼성전자로 dump, 루프 끊김) → `/terminal?sym={code}`(해당 종목 오픈). 제목도 코드→회사명(scan orders `corpName` 컬럼 신설, allFilings corp_name). 러너 pytest 8/8 | ✅ |
| 2026-07-05 | **★왓치 IPO 리포트 베이크 첫 관문** . cron 이 `buildIpoReports.py`(sync, buildIpoReport 위임) 를 먼저 돌려 6카테고리 리포트를 HF `dart/ipo/reports.parquet` push(퍼블릭 터미널 직독 SSOT, pyodide 0), 그다음 알림(딥링크 목적지 이미 존재). 단일 파싱(watch.py 가 산출 parquet 소비, scan 폴백). 실측 9 발행사 build→push→readback + 퍼블릭 렌더. 전략 E([[project_ipo_prospectus_summary]] 01) | ✅ |
| 2026-07-05 | **파이프라인 정합성 감사(5차원 팬아웃 + 적대검증, wf_47c0b9eb)** . 확증 10 / 반증 0. 데이터플로우·스키마·HF직독·렌더는 깨끗. 결함은 모니터링 가시성·왓치 캐치 품질 2 갈래. 아래 §감사 참조 | ✅ |
| 2026-07-05 | **F1 모니터링 사각 수리** . bake `continue-on-error` 가 genuine-failure 를 job green 으로 삼켜 monitorPipeline 이 못 보던 조용한 실패 봉인. buildIpoReports.main 토큰부재=exit 0(graceful no-op), notify-watch 에 `Assert IPO bake` 스텝 추가(진짜 실패만 job RED). 왓치 첫관문·회복성 보존. monitor 20/20·buildIpo 2/2 green | ✅ |
| 2026-07-05 | **F5 cron-drop 감지** . monitorPipeline STALE_AFTER_HOURS 에 "Notify Watch"=80h 등록(3일+ 연속 스케줄 누락 시 IPO SSOT 동결 갭 감지). 커버리지 테스트 동행 | ✅ |
| 2026-07-06 | **F2·F6·F7·F8 왓치 캐치 품질 정공법 수리** . F2 newIpo slug=corpCode(발행사별 1회)+확정공모가 2신호, F6 cap 40, F8 중립 적용배수 라벨. **F7 재크로싱**: 허브 topicActive 커서 + /active set-diff 엔드포인트 신설(신규 진입만 발화, 이탈 종목 재진입 시 재발화). watch 13/13·worker 24/24 | ✅ |
| 2026-07-06 | **F3 허브 nonce 롤백 + 러너 body.failed 가시화** . 전건 발송실패·구독0 nonce 롤백(재시도 가능), 러너 전건실패=RED·부분=warning. F9 윈도 상수 SSOT·F10 죽은 CSS 동반 | ✅ |
| 2026-07-06 | **master red 해소** . 타 세션 frame/inventory.py silent-fail 린트(종목별 옵셔널 report 로더)를 checkSilentFail 화이트리스트 등록(panel/build/builder 동형). lint 게이트 전 체인 green | ✅ |
| 대기 | 운영자 롤아웃: Cloudflare 배포(D1·secret·VAPID·deploy) + GitHub vars/secret | ⏳ 운영자 |
| 대기 | 운영자 롤아웃: hfProxy 재배포(`infra/workers/hfProxy` 에서 `wrangler deploy`) . `/ipo-filings` 라우트 활성(newIpo 딥링크 목적지 데이터원) | ⏳ 운영자 |
| — | 운영자 롤아웃: landing UI 눈검수 후 push(자동 push 금지) | ⏳ 운영자 |
| — | P1 SHIP: 실기기 1대 aes128gcm 수신 확인(Chrome·iOS 16.4+) | ⏳ 운영자 |
| — | P3 개인 왓처(로컬 소유·브리지) — ≥2 소비자 실증 후 발견적 추출 | ⬜ 의도적 보류(YAGNI) |
| — | P4 모드B·패키징 | ⬜ 운영자 결정 게이트 |

## 감사 (2026-07-05) . 파이프라인 정합성 + 일일 체크 규칙

**★ 운영자 상시 규칙: IPO 베이크→왓치→알림 파이프라인은 하루 1회 헬스 체크.** 자동 기전 = `Data Audit` 워크플로(매일 05시 KST `monitorPipeline.py`). F1·F5 로 이 자동 감사가 이 파이프라인의 조용한 실패(bake 실패)·스케줄 누락까지 잡도록 사각을 닫음. 세션 진입 시 확인 지점: ① 최근 `Notify Watch` run 초록 + assert 스텝 통과 ② HF `dart/ipo/reports.parquet` 최신(발행사 수·rceptDt) ③ 열린 `pipeline-failure` Issue 유무.

5차원 팬아웃 감사(wf_47c0b9eb, opus, 적대검증 refute-우선) 결과 = **확증 10 / 반증 0**. 데이터플로우·스키마·HF직독·렌더는 clean. 결함은 아래 2 갈래.

**모니터링 가시성 (수리 완료)**
- **F1 [medium, 수리됨]** bake `continue-on-error:true` 가 HF push·파싱·사이즈가드 실패를 job conclusion 에서 삼켜 monitorPipeline 이 못 봄(조용한 실패). 토큰부재(롤아웃 전 no-op)와 genuine-failure 미구분. 수리: main 토큰부재 exit 0 + `Assert IPO bake` 스텝(진짜 실패만 RED). 회복성·첫관문 보존.
- **F5 [low, 수리됨]** "Notify Watch" 가 STALE_AFTER_HOURS 미등록이라 cron drop(스케줄 누락) 미감지. 수리: 80h 등록.

**왓치 캐치 품질 (전부 수리 완료 2026-07-06, 롤아웃 전이라 실사용 무해)**
- **F2 [medium]** newIpo slug=rcept 라 기재정정마다 rcept 바뀌어 같은 발행사 재발화(중복알림). docstring "발행사별 1회" 허위. 수리안: slug=corpCode(newOrders 동형) + 테스트. (재발화를 확정공모가 알림으로 원하면 별도 토픽으로 명시.)
- **F3 [medium]** 허브가 fan-out 전에 nonce 등록·롤백 안 함. 전건 발송실패(429/5xx)·구독자0 도 nonce 소각되어 영구 재시도 불가. 러너가 body.failed 무시(조용한 미발화). worker.js "재시도 가능" 주석과 모순. 수리안: 전건실패 시 nonce 롤백 + 러너 body.failed>0 을 RED 승격. (pushHub worker + 러너 + 테스트 변경.)
- **F7 [low, 수리됨]** newOrders 가 code 단위 영구 nonce dedup 이라 재크로싱(하락 후 재상승) 영구 미발화였음. 수리: 허브 `topicActive` 커서 테이블 + `/active` set-diff 엔드포인트(직전 활성 set 과 diff, 신규 진입만 발화, 이탈 종목 제거 후 재진입 시 재발화). 러너는 stateful 토픽을 /active 로(`_send_stateful`), stateless(newIpo)는 /send. 01-architecture §5 구현. 배포 시 D1 migration 0002 적용 필요(런북 반영).
- **F6 [low]** 콜드스타트 시 cap(newIpo=20) < 윈도 발행사(~30) 라 오래된 매치가 nonce 미등록 + newest-first 정렬로 영구 미발화(aging-out). 수리안: cap 을 윈도 최대 초과(~50) 상향, 또는 콜드스타트 절단 명시.
- **F8 [low]** 알림 본문이 peerMultiple 을 무조건 "적용PER" 라벨. 비-PER 모형(EV/EBITDA)에서 오표기(터미널 IpoDialog 는 perModel 게이트로 정확). 수리안: 중립 "적용배수" 또는 모형 컬럼 추가.

**청결 (전부 수리 완료 2026-07-06)**
- **F9 [low, PARTIAL]** 베이크 `_discover` 가 scan `_latestFullProspectuses` 발굴로직 복제 + 윈도 상수 이원(85 리터럴 2곳). 현재 값 일치라 무해하나 드리프트 위험. 수리안: scan 위임 또는 상수 SSOT 공유.
- **F10 [low]** IpoDialog.svelte 죽은 CSS(`.ipoErr`·`.ipoPublicNote code`, 옛 로컬설치 잔재). 수리안: 다음 파일 편집 시 제거(UI, push 게이트).

주: 검증기 1개가 스키마 재시도 초과로 죽어 findings 1건 드롭(중복·저심각 추정). 재실행 불요.

## 배포 런북 (운영자, 코드는 전부 green, 이것만 하면 활성)

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
