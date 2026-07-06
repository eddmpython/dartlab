# 03 — 개인화 분기 · 로컬 브리지 · capability 토큰

> 본 문서는 P3 의 핵심이자 가장 논쟁적인 축이다. **개인 조건을 어디에 두느냐**가 전부를 가른다.

## 1. 중심 분기 (운영자 결정 대상)

개인 알림(내 종목·임계)을 어디에 저장·평가하나:

| 안 | 장점 | 비용 |
|---|---|---|
| **A. 로컬 소유 (브리지)** | 계정 0·프라이버시 최대·"신원=내 localhost" 비전 보존. 서버에 행동 프로파일 0 | 하드 허들 3개(PNA·패키징·머신off 격차) |
| B. D1 익명 종목행 | 허들 0(브리지 불요) | **재식별 surface** — endpoint+종목 list = 매수의향 시그널 노출(보안 high) |

**통합 권고 = A(로컬 소유).** 근거: ① 사용자가 명시적으로 원한 비전, ② 보안 패널이 B 를 high-severity
재식별로 판정. 단 A 의 3허들은 **P3 로 격리**하고 P1/P2 는 브리지 0으로 출시 → 클러터 비평가의 "브리지가
P1 을 오염시킨다" 우려와 양립. 즉 분기는 *순차로 해소* — P1/P2 는 브리지 없이 가치를 내고, 개인화/브리지
판단은 P1/P2 실사용 데이터를 보고 P3 에서 내린다.

## 2. 개인 조건의 소유 = 로컬 (Mode A)

- 설정 SSOT = `~/.dartlab/watch.json` (`channel.json` 형제, `channel.py` `_loadState`/`_saveState` 패턴).
  ```
  { version, identity:{installId:uuid(서버 미전송)},
    push:{subscription:<PushSubscription JSON|null>, vapidPublicKey},
    watchers:[{id, type, params, enabled, mode:'A'|'B', lastFiredTs, dedupeKeys}],
    hub:{sendUrl} }
  ```
- "내 종목" SSOT = 기존 `landing/src/lib/stores/map/watchlist.svelte.ts` (localStorage·계정0·최대20·`?watch=` 공유).
  개인 알림 = 이 리스트에 **'알림 ON' 비트만 추가** — 새 종목 picker·서버 종목DB **신설 금지**.
- 평가 = 로컬 데몬(`dartlab watch`)이 gather/scan online 직독 → 매치 시 사용자 자기 폰 구독 endpoint 로 허브 `/send`.

### 머신 off 격차
Mode A 는 머신 켜질 때만. 진짜 오프라인 폰 알림은 **폰 구독 + 항상 켜진 허브**가 커버하므로, Mode A 핵심
경로를 'OS 토스트'가 아니라 'watchlist 바인딩 + 허브 타겟 발송(폰)'으로 잡아 침묵을 우회. (OS 토스트는 optional
의존 — WSL·헤드리스·맥 권한별 깨짐, P1 필수 제외.)

## 3. 로컬 브리지 — PNA/CORS 정밀 (배선, `_attempts` 비대상)

> ⚠ **정정(라운드1): PNA 서버헤더 방식은 이미 무효.** Chrome 142(2025-10-28 안정판)부터 PNA 가
> Local Network Access(LNA)로 교체됐다 — `Access-Control-Allow-Private-Network` 응답 헤더는 **더 이상
> 통과 메커니즘이 아니고**, 사용자 *권한 프롬프트* + `Private-Network-Access-Name`/`-ID` 응답 헤더로 바뀌었다.
> 아래 미들웨어 설계는 **P3 착수 직전 LNA 권한-프롬프트 모델로 재작성**해야 한다(P1/P2 무영향 — 브리지는 P3).
> Firefox/Safari 는 PNA/LNA 미적용이라 origin CORS 만으로 통과(Chrome 한정 게이트). 아래는 *옛 PNA 기준
> 골격*으로, LNA 재작성 전까지 참고용.

퍼블릭 HTTPS(`https://eddmpython.github.io`) → `http://127.0.0.1:8400` 호출은 mixed-content + 로컬망 접근
preflight. **현재 코드엔 관련 헤더 0이고 Starlette `CORSMiddleware` 는 미구현**이라 "allow_origins 추가만
하면 된다"는 착각이다.

- `server/__init__.py` 에 `_PrivateNetworkAccessMiddleware` (**pure-ASGI** — `BaseHTTPMiddleware` 금지,
  streaming buffer 회귀 가드 준수). OPTIONS + `access-control-request-private-network: true` →
  204 + `Access-Control-Allow-Private-Network: true` + `Allow-Origin`(echo)/Methods/Headers/Max-Age.
- `_corsOrigins()` 기본 리스트에 `https://eddmpython.github.io` **1줄 하드코딩**(소비자는 env 못 깖, `*` 금지).
  커스텀 도메인은 `DARTLAB_BRIDGE_ORIGINS` 로 추가만.
- 경량 핸드셰이크 **`GET /api/bridge/ping`** → `{ok, version, caps:['watch']}` (provider probe 0 —
  기존 `/api/status?probe` 는 provider availability 까지 돌아 탐지용으로 과함). PWA 1회 fetch 탐지 + 실패 시
  안내(**폴링 금지** — 부재 시 콘솔 에러 스팸).

## 4. capability 토큰 — 인바운드 위협모델 (보안 high)

`127.0.0.1` 데몬이 떠 있으면 **임의 악성 웹페이지**도 PNA/CORS 만 뚫으면 로컬 데이터·`/api/ai`(SSE,
LLM 비용)·`/api/export` 를 트리거할 수 있다(`/api` 는 현재 무인증). origin allowlist 가 유일 방어선이면 부족.

- `GET /api/bridge/ping`·status = read-only, PNA 허용, 무토큰 200.
- **쓰기·ai·export** 라우트(`/api/watch/config` PUT 등)는 **per-session capability 토큰**(`X-DL-Cap` 또는
  설치 시 발급 `installId` 를 `X-Dartlab-Bridge` custom 헤더) 필수 — custom 헤더라 simple-request 우회 불가 →
  preflight 강제 → CSRF 우회 차단.
- 토큰 발급 = 사용자가 로컬 UI 에서 '이 브라우저 세션 연결 허용' 명시 클릭 시 단명 토큰(메모리, TTL).
- `allow_credentials=False`(쿠키 CSRF 면 제거). 데몬 `127.0.0.1` 바인딩 유지(**`0.0.0.0` 금지**, 채널 모드와 분리).
- `offlineGuard` 는 이 축과 **무관**(prebuild **outbound** 가드 — socket.connect monkey-patch). 인바운드 게이팅 아님.
  브리프 §52 의 offlineGuard 인용은 범주 오류 → 삭제.

## 5. 퍼블릭 PWA → 로컬 편집 흐름

PWA '개인 왓처' 패널 → `GET /api/watch/config`(데몬, `watch.json` 직독) · `PUT /api/watch/config`(저장).
설정이 머신 밖으로 안 나감. 두 라우트는 **데몬에만** 존재(허브엔 없음). 호출 = `localApi.ts` 게이트 형태를
PWA 쪽에서 cross-origin 재현(`apiBase='http://127.0.0.1:8400'`).

사용자 표면 카피: '내 설정은 내 PC 에만 저장됩니다(서버에 안 올라감)' + '내 PC 연결됨/꺼짐' 상태칩 1개.
PNA/CORS·`dartlab serve` 명령은 설치가이드로 격리(UI 비노출).

## 6. 데몬 정체성

`src/dartlab/cli/commands/watch.py` (`channel.py` 형판). 권고 = **`dartlab ai` 서버(8400) 안의 백그라운드
평가 task 로 합쳐 단일 포트** — `ensurePort` 핑퐁·이중 포트 혼란 회피, `bridge/ping` caps 로 통합 상태 노출.
헤드리스 사용자용 `dartlab watch` 단독 기동 경로도 남김. (`dartlab serve` 는 존재하지 않음 — 진입은 `dartlab ai`.)

## 7. LNA 종속성 리스크 (정정: 예고 아님 — 이미 출시)

Chrome 142(2025-10-28)에서 PNA→LNA 가 **이미 출시**됐다(예고 아님). 로컬망 접근은 이제 사용자 *권한
프롬프트*가 1급이고, 서버 헤더(`Private-Network-Access-Name`/`-ID`)는 디바이스 식별용일 뿐 통과 메커니즘이
아니다. → 핸드셰이크를 '권한 프롬프트 + 실패 시 명시 안내'로 설계(자동 탐지 의존 0). Firefox/Safari 는
미적용이라 origin CORS 만으로 통과 — Chrome 한정 추가 게이트. **P3 본설계 = LNA 모델 기준 재작성.**

## 8. 모드 B (gist 등록) = P4, 운영자 결정 뒤

로컬 설정을 사용자 자기 private gist 로 publish → 항상 켜진 GHA 러너가 읽어 평가 → 오프라인 폰 알림.
신원·PII 경계 재등장(종목·임계 = 행동 프로파일). 조건: private gist 강제 · 종목코드/수치임계만(자유서술 0) ·
러너 읽기전용·D1 미기록. `questionCollector` PII 0 원칙과 충돌하므로 **착수 전 운영자 결정 필수**.
