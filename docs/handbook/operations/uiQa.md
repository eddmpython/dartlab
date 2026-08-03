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
