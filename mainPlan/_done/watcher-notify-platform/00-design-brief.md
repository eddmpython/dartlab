# 00 — 설계 브리프 (전문 패널 토론 입력)

> 본 문서는 PRD 가 아니라 **토론의 입력**이다. 아래 제안 아키텍처를 분야별 전문가가
> 검증·반박·확장해 최종 PRD(`00-product-prd.md` 이하 번호 문서)로 합성한다.

## 비전

DartLab 을 "보고 끝나는" 도구에서 "**변화가 생기면 먼저 알려주는**" 플랫폼으로.
PWA 웹 푸시의 *받는 쪽*(service-worker)은 이미 있다(`landing/src/service-worker.ts`,
`InstallPrompt.svelte`, manifest·아이콘·iOS 메타 전부 라이브). 필요한 것은 셋:

1. 알림을 **쏘는 thin 허브** (정적 GitHub Pages 는 런타임 쓰기 불가 → 수신단 필요)
2. **무엇을 감시하고 어떻게 판정하는지** 정의·평가하는 라이브러리 왓처
3. 주기 실행 **러너**

범위: 공개 발행 알림(블로그·카드뉴스)부터 → 사용자별 조건 알림(공시·뉴스·주가·IPO·저가 등)까지.

## 제안 아키텍처 — 3 계층 (패널이 검증할 가설)

| 계층 | 자리 | 책임 | 선례 |
|---|---|---|---|
| **왓처 (지능)** | dartlab 라이브러리 | 감시 대상·판정 로직을 *선언적*으로 정의. gather·scan SSOT 위에서 평가. 왓처 타입 레지스트리. | gather 축·scan 레지스트리·recipe lifecycle |
| **러너 (스케줄)** | GitHub Actions cron | 이미 도는 cron 이 dartlab 으로 왓처 평가 → 매치를 허브 `/send` 로 전달 | sync/prebuild cron |
| **허브 (배달)** | Cloudflare Worker | 얇게: `/subscribe`(구독+토픽 저장, D1) · `/send`(인증, 발송) · VAPID | `questionCollector`(thin POST·CORS·시크릿·레이스0) · `siteSignals`(D1) |

핵심 원칙: **감지 지능은 dartlab 이 사는 곳에** 둔다(런타임-SSOT 정합). Cloudflare 는
크롤·판정을 재구현하지 않는다 — 구독 저장 + 발송만. 무엇을 감시할지는 라이브러리 SSOT.

## 퍼블릭 ↔ 개인 통일 (제안)

공개와 개인은 **두 시스템이 아니라 하나의 왓처 타입 레지스트리의 두 바인딩 모드**다.

- **공개** = 고정 파라미터 + 토픽 브로드캐스트 (누구나 구독, per-user 식별 불필요, stateless)
- **개인** = 같은 타입 + 사용자 파라미터(내 종목·임계) + 타겟 발송 (per-user 저장·식별 필요)

"동기화"의 정의 = 둘이 **같은 레지스트리를 읽음**. 개인 왓처 = 사적 파라미터를 가진 공개
왓처 타입. → 타입 하나 등록하면 공개·개인 양쪽에 즉시 노출 = "쉽게 SSOT 로 추가".

왓처 타입 후보(레지스트리 초기 멤버): `공시키워드추적` · `주가임계돌파` · `IPO신규상장` ·
`뉴스키워드` · `저가알림` · (장기) `신규수주`(→ `project_order_flow_scan` 과 합류 가능).

## 추가 축 — 퍼블릭↔로컬 브리지 · 계정 없는 신원 · 원패스 런처

개인 설정을 **서버 계정 DB 에 두지 않는다.** 신원 = "**내 localhost 와 대화 중**"이라는 사실 자체.
이 모델의 뼈대는 *이미 존재*하므로 재사용한다:

- **런처**: `dartlab` CLI(pip console script, `dartlab.cli.main:main`) → `dartlab ai` 가 `127.0.0.1:8400`
  FastAPI+SPA 기동. `ensurePort` 가 이미 도는 서버 재사용.
- **탐지**: `/api/status?probe` 헬스 엔드포인트 — 퍼블릭 PWA 가 이걸로 로컬 서버 생존을 탐지.
- **브리지**: `/api` 게이트 + sources(company·price·filing·export·ai) — "퍼블릭에서 로컬 라이브러리 접근"은
  새 배선이 아니라 *기존 `/api` 재사용*. (`ui/packages/runtime/src/adapters/local/api`)
- **격리**: `core/offlineGuard.py` loopback(127.0.0.1·::1·localhost) allow-list.

### 개인 왓처 = 로컬 소유, 두 알림 모드

- **설정 소유** = 로컬 dartlab 라이브러리(사용자 config). 퍼블릭 PWA 에서 편집해도 저장은 localhost.
- **모드 A (로컬 데몬)**: `dartlab watch` 류 데몬이 로컬에서 평가 → 매치 시 (ⓐ OS 알림 또는 ⓑ 사용자
  자기 폰 구독으로 허브 `/send`). 설정이 머신 밖으로 안 나감, 식별 0, 프라이버시 최대. 한계 = 머신 켜져 있을 때만.
- **모드 B (레포 등록)**: 로컬 설정을 사용자 *자기 저장처*(개인 gist 등)로 publish → 항상 켜진 GitHub
  Actions 러너가 읽어 평가 → 오프라인에도 폰 알림. 무거움 + 신원·프라이버시 경계 재등장.

### 원패스

퍼블릭에서 "런처 다운로드+설치" → 설치 → `dartlab serve` → 퍼블릭이 localhost 자동 탐지 → 개인 왓처 라이브. 한 흐름.

### 하드 허들 (패널 필수 해결)

- **HTTPS→localhost**: 퍼블릭 HTTPS(GitHub Pages)가 `http://127.0.0.1` 호출 = mixed-content +
  Private Network Access(PNA) preflight. 로컬 FastAPI 가 `Access-Control-Allow-Origin:
  https://eddmpython.github.io` + PNA 헤더 응답 필요. 해결 가능하나 정밀 설계 요함.
- **항상-켜짐 격차**: 모드 A 는 머신 off 면 침묵. 진짜 오프라인 폰 알림은 모드 B 필요.
- **소비자 패키징**: 현재 런처 = pip console script(개발자급). 진짜 "다운로드+더블클릭" 원패스는 패키징
  (pyinstaller/briefcase 등) = 별도 트랙·무거움. "pip+serve(개발자) vs 소비자 설치관" 운영자 결정.

## 단계 (가설 — 패널이 재단)

- **P1** 허브(D1·VAPID·`/subscribe`·`/send`) + **발행 알림**(블로그·카드) + 구독 UI. 수동 발송은 같은 `/send` 라 무료.
- **P2** **공개 왓처 토픽**(공시·IPO 등 큐레이션 브로드캐스트) — per-user 식별 불필요, 러너가 평가 → 토픽 발송.
- **P3** **개인 왓처 (로컬 소유·모드 A)** — 퍼블릭↔로컬 브리지로 설정 편집, 로컬 데몬이 평가·발송. 계정 0.
- **P4** **항상-켜짐(모드 B)·소비자 원패스 패키징** — 오프라인 커버 + 더블클릭 설치관. 별 트랙, 운영자 결정 후.

## 제약 (불가침)

- 신규 dartlab 능력 = `tests/_attempts/<카테고리>/` 졸업 게이트 경유, src/ 직행 금지.
- 런타임-SSOT: 빌드/베이크 금지. 왓처는 gather·scan 직독 평가.
- 새 Cloudflare 자원 = `infra/workers/<name>/` 컨벤션(새 최상위 폴더 금지). `scripts/` 금지.
- 알림 본문에 외부(공시·뉴스) 텍스트가 들어가면 untrusted 취급.
- iOS 푸시 = 홈화면 설치 PWA + iOS 16.4+ 에서만 (설치 UX 가 선행조건).
- 덕지덕지 금지 — 과빌드·과추상은 클러터 비평가가 잘라낸다.

## 패널이 풀 공개 질문 (분야별)

- **라이브러리 아키텍트**: 왓처가 L0~L4 어디에? 새 엔진 vs recipe vs scan 확장? `order_flow_scan` 과 관계?
  타입 레지스트리 형태(추가가 진짜 한 곳이려면)? `_attempts` 졸업 경로·개념증명 기준?
- **인프라/WebPush 아키텍트**: D1 스키마(구독·토픽·개인조건)? `/send` 인증 모델? 러너가 per-user 조건을
  평가하는 데이터 흐름(D1 ↔ GitHub Actions)? VAPID 키 운용·iOS·rate limit·재구독·만료 endpoint 정리?
- **프로덕트/UX**: 구독 UX(권한 요청 타이밍·토픽 토글·종목 설정)? 알림 본문·빈도·중복억제·opt-out?
  공개 왓처 "구독 가능 목록" 노출? P1 최소 가치 범위?
- **보안/프라이버시**: 익명 구독 vs 식별 경계? per-user 데이터 보존·삭제? `/send` 남용·스팸 차단?
  알림 본문 untrusted 래핑? VAPID 시크릿 운용?
- **로컬 브리지/배포 아키텍트**: HTTPS→localhost PNA/CORS 정밀 해결책? 퍼블릭↔로컬 탐지·핸드셰이크 UX?
  로컬 config 스키마·위치(사용자 config dir)? 모드 A/B 경계? 원패스 패키징 현실(pip vs 설치관)? `offlineGuard` 와 정합?
- **클러터 비평가**: 어디가 과빌드인가? per-user 동기화가 값어치를 하나, 로컬 브리지가 환상 복잡도 아닌가?
  라이브러리 왓처 추상이 과한가? 레지스트리가 진짜 "한 곳 추가"가 되나? P4(패키징)는 야망일 뿐 잘라야 하나?
