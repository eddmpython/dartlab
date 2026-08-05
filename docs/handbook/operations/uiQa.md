# UI 검수 운영

UI QA는 로컬 개발 GUI를 의미 단위로 읽고 제한된 동작만 수행하는 검수 표면이다. 운영 서버나 외부 노출 모드에서는 사용할 수 없다.

## 시작

loopback 개발 모드에서는 UI QA가 자동으로 켜진다.

```powershell
uv run python -X utf8 -m dartlab ai --dev --no-browser
```

API는 `http://127.0.0.1:8400`, Svelte 개발 화면은 `http://127.0.0.1:5174`에서 열린다. `--host`가 loopback이 아니면 `DARTLAB_UI_QA`를 자동으로 제거하고 모든 조작 엔드포인트가 403을 반환한다.

## 계약 확인

```powershell
Invoke-RestMethod http://127.0.0.1:8400/api/ui-qa/config
Invoke-RestMethod http://127.0.0.1:8400/api/ui-qa/audit-plan
```

`config.enabled=true`와 `schemaVersion=dartlab.ui-qa.v1`을 확인한다. audit plan은 desktop 1440x900, tablet 768x1024, mobile 390x844 viewport와 다음 시나리오를 제공한다.

- `chat-core`: 투자분석 환영 화면과 composer
- `runtime-center`: 런타임 준비 dialog 열기와 닫기
- `runtime-settings`: 설치 상태와 준비 action
- `terminal-shell`: 종목 터미널 로딩과 본문

## 검수 실행기

브라우저가 붙어야만 도는 구조라 사람이 화면을 열어 두지 않으면 제어면을 쓸 수 없었다. 실행기가 그 자리를 대신한다.

```powershell
npm install --no-save playwright@1.62.1   # 최초 1 회
node ui/apps/local/qa/uiAudit.mjs --base http://127.0.0.1:5174 --out /tmp/dartlab-ui-audit
```

실행기는 서버가 발행한 검수 계획을 화면 크기별로 실행하고 실제 사진을 남긴다. 조작은 전부 제어면을 왕복하므로 같은 실행이 제어면 자체가 도는지도 함께 증명한다. 설치된 실물 Chrome 을 기본으로 쓰므로 별도 내려받기가 없고 사용자가 보는 렌더링과 같다. `--channel bundled` 로 번들 브라우저를 쓸 수 있고, `--scenario` 와 `--viewport` 로 범위를 좁힌다. error 심각도 finding 이 있으면 종료코드 1 이다.

한 턴이 흘러가는 모습은 정지 화면 한 장으로 판정할 수 없다. 사고와 도구 호출과 본문이 어떤 순서로 나타나고 완료 순간 무엇이 흔들리는지는 시간축을 봐야 안다.

```powershell
node ui/apps/local/qa/uiAudit.mjs --base http://127.0.0.1:5174 --out /tmp/dartlab-turn `
  --live "삼성전자 005930 최근 3년 매출 추이" --liveMs 300000 --frameMs 20000
```

질문을 넣고 전송한 뒤 지정한 간격으로 화면을 연속 촬영한다. 스트리밍이 끝나면 마지막 한 장을 더 찍고 멈춘다.

### 판정이 놓치기 쉬운 것

`data-qa` 존재만으로 통과시키면 스피너 하나만 도는 빈 화면도 정상으로 보고된다. 반대로 `data-qa` 개수를 화면 충실도의 대리지표로 쓰면 계기판 전체를 하나로 감싼 터미널을 비었다고 오판한다. 실행기는 앱이 선언한 로딩 표시가 사라질 때까지 기다린 뒤, 브라우저에서 실제로 그려진 글자 수와 박스 수를 직접 재서 판정한다.

같은 경로를 다시 열면 이전 세션이 TTL 동안 남아 있다. 경로만 보고 세션을 고르면 이미 죽은 세션에 명령을 보내 영원히 기다린다. 이동 전 식별자 집합에 없던 새 세션만 받아들여야 한다.

다른 작업이 소스를 편집하면 개발 서버가 화면을 다시 불러 스트리밍이 끊긴다. 촬영 중 턴 실패를 제품 결함으로 읽기 전에 그 사이 편집이 있었는지 먼저 본다.

## 검수 클라이언트 흐름

1. UUID로 `POST /api/ui-qa/sessions/register`를 호출한다.
2. `[data-qa]` 요소의 역할, label, 안전한 텍스트, viewport 위치와 진단을 `POST /sessions/{sessionId}/snapshot`으로 보낸다.
3. 검수자는 `POST /sessions/{sessionId}/commands`로 명령을 넣는다.
4. 브라우저 브리지는 `/commands/next`를 polling하고 결과를 `/commands/{commandId}/result`에 기록한다.
5. viewport별 시각 판정과 스크린숏 촬영 여부를 `POST /sessions/{sessionId}/visual-audits`에 기록한다.
6. 검수가 끝나면 `DELETE /sessions/{sessionId}`로 세션을 닫는다.

허용 동작은 `click`, `fill`, `key`, `navigate`, `scroll`, `snapshot`뿐이다. 조작 대상은 등록된 `data-qa` 식별자여야 하고, navigation은 query와 fragment가 없는 same-origin 절대 경로만 허용한다. 비밀번호 입력은 수집하지 않으며 입력값은 브리지의 안전값 정책을 통과한 경우에만 snapshot에 포함한다.

## 합격 기준

- 중복 `data-qa` 식별자가 없음
- 수평 overflow와 주요 요소의 viewport 이탈이 없음
- console error가 없음
- 주요 조작 대상이 현재 viewport에 보임
- 실패한 visual audit에는 하나 이상의 finding이 있음
- 테스트 후 서버, Vite, 브라우저 자동화 프로세스를 모두 종료함

코드 계약 검증은 다음 focused test와 UI 검사로 수행한다.

```powershell
uv run python -X utf8 -m pytest tests/server/test_uiQaApi.py -q
npm --prefix ui/apps/local run check
npm --prefix ui/apps/local run build
```

`check`의 기존 warning은 별도로 추적하되 신규 error는 허용하지 않는다. 실제 시각 완료 판정은 audit receipt와 스크린숏을 함께 남긴 경우에만 내린다.
