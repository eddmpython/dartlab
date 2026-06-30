# `lib/viewer/dev/` · 테스트 라우터 격리 사본

`/lab/viewer-dev/[stockCode]` 테스트 라우터가 **본진과 같은 동일환경**에서 코파일럿/액션레이어를
개발하되, 본진(`/viewer/company`)에 새지 않도록 **파일로 격리**한 사본 폴더다.
개발은 여기서, 확정되면 canonical 로 promote → 본진 라우터가 흡수한다.

## 규칙

- **이 폴더의 파일은 `routes/lab/viewer-dev/` 밖에서 import 금지.** (누수 = 격리 깨짐)
- dev 라우터의 핫파일은 여기서 import, 안정 leaf 는 `$lib/viewer/*` 공유 그대로.
- promote: dev 사본 → canonical 로 내용 복사(상대 import `./` ↔ `$lib/viewer/*` 만 되돌림),
  본진 라우터에 배선 반영, svelte-check + build 게이트.

## 현재 격리 대상

- `AskDrawer.svelte` · 코파일럿 UI (개발 surface). 내부 import 중 `askSession` 만 `./`(dev 사본),
  나머지(`$lib/viewer/searchIndex·answerCompose·webllm·viewerActions·translate·...`)는 공유.
- `askSession.svelte.ts` · 대화/모델 상태 **모듈 싱글턴**. 공유하면 dev↔본진 대화가 섞이므로 **반드시 격리**.
  (내부 `searchIndex`/`webllm` import 는 공유 canonical 로 재지정.)

그 외 코파일럿 모듈(`answerCompose`/`financeAsk`/`webllm`/`ollama`/`translate`/`searchIndex`/
`viewerActions`)은 현재 **공유**. dev 에서 실제로 손대기 시작할 때 이 폴더로 사본을 들이고 import 만 `./` 로 바꾼다.
