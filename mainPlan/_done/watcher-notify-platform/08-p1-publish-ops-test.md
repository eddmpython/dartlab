# 08 — P1 상세설계: 발행 러너 · 운영 · 검증/롤백 (build-ready)

발행(블로그·카드) 시 `/send` 호출 + 배포·SHIP 게이트. 라운드1 갭 닫은 확정본.

## 1. 발행 알림 러너 — `.github/scripts/notify/` (P1, P2 아님)

라운드1 정정: PRD 04 §5 표가 이 폴더를 P2 에 뒀으나 **발행 알림은 P1** → 표 정정([04](04-phasing-scope-guardrails.md)).
P2 = *공개 왓처 토픽 러너*(scan SSOT 직독)로 별개.

```
.github/scripts/notify/
  send.py          # detect → /send 호출 + Bearer/nonce 헤더 + 응답 집계 헬스게이트
  authHeaders.py   # Bearer + 결정적 nonce (HMAC 서명 제거)
  payload.py       # aes128gcm 평문(title/body/url/tag) 조립 + sanitize
  sanitize.py      # 제어/RTL/zero-width strip + 출처라벨 + dartlab 자기 라우트 링크
```

`noScriptsDir.py` 는 repo-루트 `scripts/`만 차단 → `.github/scripts/notify/` 허용(실측 확인, 안전).

### authHeaders.py — Bearer + nonce (HMAC 서명 제거, 품질점검)
```python
def authHeaders(payload: dict, ts: int, topic: str, slug: str) -> tuple[bytes, dict]:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")  # 전송할 바로 그 바이트
    nonce = hashlib.sha1(f"{topic}:{slug}".encode()).hexdigest()   # 결정적 — (topic,slug) 재push 멱등 (uuid 아님!)
    return raw, {"X-DL-Ts": str(ts), "X-DL-Nonce": nonce}           # Authorization: Bearer 는 send.py 가 부착
```
**send.py 는 `raw` 바이트를 그대로 HTTP body 로 전송**(재직렬화 금지). HMAC `X-DL-Sign` 제거 — SIGN_KEY·SEND_TOKEN 이
같은 secrets 라 독립 신뢰축 0([06 §2]). nonce 가 (topic,slug) 결정적이라 같은 발행 재push 1회, blog·card 는 토픽이 달라 둘 다 발송.

### payload.py — 발행 알림 본문 (토픽별 url/tag, body=description)
```python
def buildPayload(ev: PublishEvent) -> dict:
    url = f"/blog/{ev.slug}" if ev.topic == "blogPublish" else f"/cards?post={ev.slug}"  # 라이브 라우트 SSOT
    tag = f"{'blog' if ev.topic=='blogPublish' else 'card'}:{ev.slug}"
    title = ("[새 글] " if ev.topic == "blogPublish" else "[새 카드] ") + ev.title
    body  = sanitize(ev.summary)[:120]                          # ev.summary = frontmatter description (아래 detect)
    return {"topic": ev.topic, "notification": {"title": title, "body": body, "url": url, "tag": tag}}
```
- **url 은 app-path(base 없음)** — `/blog/{slug}`·`/cards?post={slug}`. **BASE_PATH `/dartlab` 접두는 SW 가 한 곳에서**
  ([07 §1] push 핸들러가 `import.meta.env.BASE_URL`=`/dartlab/` 로 접두 → `/dartlab/blog/…`). payload 에 base 박지 않음(SSOT 1곳).
  ⚠ 라이브 배포 = `BASE_PATH=/dartlab`(deploy-landing.yml)·`origin=eddmpython.github.io` 라 base 누락 시 클릭 404(라운드4 blocker).
- **cardPublish url = `/cards?post={slug}`** — 라이브 카드 라우트는 `/cards`+`?post=`(`+page.ts` searchParams), `/cards/[slug]` 부재. `share.ts cardShareUrl` 와 동형. slug 는 `[a-z0-9-]` 규약이나 방어상 `urllib.parse.quote(slug)`.
- title/body 는 우리가 쓴 글이라 외부 untrusted 아님(sanitize=길이컷·제어문자). aes128gcm 이라 **제목+본문 실제 표시**([06] §0).
  body 소스: 블로그=frontmatter `description`, **이슈 카드=`planning.cardThesis`**(cards.plan.json 에 description 부재, [§2]).

## 2. send.py 검출 로직 + 독립 워크플로 (라운드2 정정)

### detect — git diff → 발행 이벤트
```python
def detect(before: str, sha: str) -> list[PublishEvent]:
    files = git("diff", "--name-only", before, sha).splitlines()            # 추가/변경 파일(leading slash 없음)
    events = []
    for f in files:
        # (1) 블로그 글: blog/<cat>/<NN>-<slug>/index.md → blogPublish (+ carousel: 키 있으면 cardPublish)
        m = re.match(r"^blog/[^/]+/\d+-([^/]+)/index\.md$", f)
        if m:
            slug = m.group(1)                                               # \d+- 뒤 그룹 = 라이브 normalizePath 와 동형 slug
            front = parse_frontmatter(Path(f).read_text("utf-8"))           # 전체 yaml.safe_load (라인파서 금지)
            desc = front.get("description", "")                             # ⚠ 키 = description (summary 0건 실측)
            events.append(PublishEvent("blogPublish", slug, front["title"], desc))
            if front.get("carousel"):                                       # carousel: = nested dict → 카드도 발행
                events.append(PublishEvent("cardPublish", slug, front["title"], desc))
            continue
        # (2) standalone 이슈 카드: blog/_issues/<slug>/cards.plan.json (index.md 부재) → cardPublish
        m = re.match(r"^blog/_issues/([^/]+)/cards\.plan\.json$", f)
        if m:
            plan = json.loads(Path(f).read_text("utf-8"))
            tgt = plan.get("target", {})                                    # ⚠ title/slug 는 target 하위(top-level 부재, 실측 3/3)
            slug = tgt.get("slug", m.group(1))
            title = tgt.get("title", m.group(1))
            body = plan.get("planning", {}).get("cardThesis", "")           # description 부재 → cardThesis 가 body 소스
            events.append(PublishEvent("cardPublish", slug, title, body))
    return events
```
- **slug = `\d+-` 뒤 그룹** — 라이브 라우팅 SSOT `landing/src/routes/blog/[slug]/+page.ts` `normalizePath`
  (`/blog/[^/]+/\d+-([^/]+)/index.md/`)와 **동형 slug 값**(카테고리·번호 미포함, 예 `everything-about-dart`).
- **frontmatter 키 = `title`/`description`/`carousel`** (실측: `summary:` 0건, `description:` 정본, `blog/PIPELINE.md`).
  `parse_frontmatter` = `---`…`---` 사이 통째 `yaml.safe_load`(PyYAML, `pyproject.toml` 의존 확인) — nested carousel dict·`|-` 멀티라인 caption·list 처리. carousel 키 없는 회사글은 KeyError 없이 skip.
- **detect ↔ 워크플로 paths 1:1 커버** — detect 가 매칭하는 경로(index.md·_issues/cards.plan.json)만 paths 에. 비대칭(트리거되는데 detect 0) 금지.
- 흐름: `detect → buildPayload(ev) → authHeaders(payload, ts, ev.topic, ev.slug) → POST /send(Bearer)`. 이벤트 1개당 1 POST.
- 회귀: `test_detect` — 실제 index.md(description 키)·_issues/cards.plan.json 입력에 title+body 비지 않음 + slug 가 +page.ts 와 동형 + (topic,slug) 결정적 nonce.

### 독립 워크플로
`deploy-landing.yml`(group=pages, `cancel-in-progress:true`)에 얹으면 연속 push 시 취소로 알림 유실 → 분리:
```yaml
# .github/workflows/notify-publish.yml
name: Notify Publish
on:
  push:
    branches: [master]
    paths: ['blog/**/index.md', 'blog/_issues/**/cards.plan.json']   # detect 커버리지와 1:1 (landing/static/cards 폐기=부재)
concurrency: { group: notify-publish }    # cancel-in-progress 미설정 → 취소 0, push 이벤트당 1회 보장
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }          # git diff before..sha (얕은 checkout 금지)
      - run: uv run python -m notify.send --before "${{ github.event.before }}" --sha "${{ github.sha }}"
        env: { PUSHHUB_URL: "${{ vars.VITE_PUSHHUB_URL }}", PUSHHUB_SEND_TOKEN: "${{ secrets.PUSHHUB_SEND_TOKEN }}" }
```
- cardPublish 트리거 = ① blog index.md `carousel:` 블록 detect(본 설계 확정). 대안 ②(`workflow_run` 체이닝)는 [09](09-evaluation-ledger.md) 운영자 결정#7 에만 박제(여기선 노이즈라 컷).
- **관측성 헬스게이트(send.py, brokerageSync 패턴 미러)**: send.py 가 각 `/send` 응답 `{sent,pruned,failed}` 를 집계 →
  `GITHUB_STEP_SUMMARY` 에 topic별 표 출력 + **발송 이벤트가 있었는데 `sent==0`(전 실패)·HTTP 자체실패(401/409)·`failed` 비율
  임계 초과 시 비-0 exit → 워크플로 RED → 운영자 자동알림.** 구독 0(no-op)은 정상 종료로 구분. *조용한 발송 실패 차단*(알림 도메인 핵심).
- **재시도 = P1 비범위(의도)**: (topic,slug) 결정적 nonce 라 워크플로 재실행은 전부 409(성공자 멱등) — 일시 실패자만 재시도 불가.
  발행 알림은 *저-stakes 단발*(놓친 알림 = 데이터 손실 아님, 다음 발행은 새 알림)이라 best-effort 단발로 둔다. per-endpoint 재시도는 P2 향상안.

## 3. 배포 절차 + 롤백

```bash
cd infra/workers/pushHub
wrangler d1 create dartlab-push-hub                 # → database_id 를 wrangler.toml 기입
wrangler d1 execute dartlab-push-hub --remote --file schema.sql
wrangler secret put VAPID_PRIVATE_KEY               # pkcs8 base64url ([06] §4)
wrangler secret put PUSHHUB_SEND_TOKEN              # (SIGN_KEY 제거 — HMAC 층 삭제)
# wrangler.toml [vars] VAPID_PUBLIC_KEY·VAPID_SUBJECT 기입
wrangler deploy
# GitHub: vars VITE_VAPID_PUBLIC_KEY·VITE_PUSHHUB_URL, secret PUSHHUB_SEND_TOKEN
```
**⚠ secret 짝맞춤**: `PUSHHUB_SEND_TOKEN` 은 **Cloudflare Worker secret ↔ GitHub Actions secret 동일값 필수**(다르면 전 발송 401).
회전 시 양쪽 동시 갱신(롤백 §3-③ 함정). 나머지: VAPID 비밀키=Worker only, 공개키=양쪽 공개값.
롤백: ① Worker 미배포/문제 → `VITE_PUSHHUB_URL` 미설정 시 NotifyOptIn 자동 hidden(랜딩 무영향). ② 구독 0 → 발송 no-op.
③ 발송 사고 → secret 회전(`wrangler secret put` 재실행)으로 즉시 발송 차단. ④ landing 회귀 → 직전 커밋 revert(자동 push 안 했으므로 미발간 상태).

## 4. CI 검증 게이트 (라운드1: vitest 비강제 닫음)

`deploy-landing.yml` build job 은 현재 `npm ci + build` 만 — vitest 0. **추가**:
```yaml
      - run: npm test -w landing      # vitest run — sanitize/pushPayload 보안 sink 게이트 (build 전)
```
테스트 자산은 **3 러너에 분산**(단일 `npm test` 로 못 묶음 — landing vitest=node pool, Worker=workers pool, py=pytest):
- `landing/src/lib/notify/{sanitize,subscription}.test.ts` — **`src/lib/**` 글롭 아래**여야 `landing/vitest.config.ts`(environment:node, include `src/lib/**/*.test.ts`)가 수집. 제어/RTL/피싱 URL·직렬화 라운드트립.
- `infra/workers/pushHub/test/{send,subscribe}.test.js` — vitest-pool-workers(위 하네스). 401/409/nonce/purge·JWT.
- `.github/scripts/notify/test_detect.py` — pytest. detect/payload/nonce: 실제 index.md(description)·_issues cards.plan.json(target.*) 픽스처로 title+body 비지않음·slug 동형·`sha1(topic:slug)` 결정성(같은=같은, 다른 topic=다른). (HMAC 서명 회귀 제거 — 층 삭제.)

### Worker 테스트 하네스 — 그린필드 (infra/workers 선례 0). 버전핀 + 설치 버전 템플릿 스캐폴드
pushHub 가 repo 최초 package.json 보유 Worker(형제 4종은 raw `wrangler deploy`). `infra/workers/*` 는 루트
workspaces(`landing`·`ui/*`) **밖** → standalone `npm ci`. 파일트리:
```
infra/workers/pushHub/
  package.json               # { "private":true, "scripts":{"test":"vitest run"},
                             #   "devDependencies":{ "@cloudflare/vitest-pool-workers":"<핀>", "vitest":"<해당 peer 핀>", "wrangler":"<핀>" } }
  migrations/0001_init.sql   # = schema.sql (멀티라인 DDL → exec() 'incomplete input' 회피, migrations 경유)
  vitest.config.js · test/setup.ts · test/{send,subscribe}.test.js
```
**⚠ config API 손코딩 금지**(라운드2·3·4 에서 `d1Databases`·`exec(schema)`·`defineWorkersConfig` vs `cloudflareTest()`
플러그인·`cloudflare:test` vs `cloudflare:workers` env 가 *버전마다* 깨짐). 외부 라이브러리 버전 사실이라 **설치한 버전의
공식 템플릿**(`npm create cloudflare` → Worker+Vitest, 또는 패키지 README)에서 스캐폴드 + **버전 package.json 핀** + 첫
`npm test` green 을 게이트로 닫는다. 버전 무관 *불변 요구사항*만 본 문서가 못박는다:
- **스키마 = `migrations/` + `readD1Migrations`/`applyD1Migrations`**(`exec(멀티라인 schema)` 금지). D1 바인딩 = `wrangler.toml` `[[d1_databases]]` 자동발견.
- **`beforeEach` 3 테이블 DELETE 리셋** — `isolatedStorage` 제거됨(파일단위 격리)이라 시나리오간 상태 누수 가드 필수(순서 무관, FK CASCADE).
- **원격 D1 의존 회피**: Miniflare 로컬 D1 은 원격 batch 트랜잭션 의미 미재현 → 테스트=*기능 정확성*만(멱등 설계라 원자성 불요, [06 §6]). 원격 1회 스모크는 배포 후 수동.

### 3 러너 CI 강제 (운영자 결정 #8 — 본 플랜에서 닫음)
러너2·3 을 별 워크플로로 push 트리거 게이트화(markdown 체크박스 아닌 CI 차단):
```yaml
# .github/workflows/pushhub-test.yml — paths: infra/workers/pushHub/** · .github/scripts/notify/** · landing/src/lib/notify/**
jobs:
  worker: { steps: [checkout, {run: 'npm ci && npm test', working-directory: infra/workers/pushHub}] }   # 러너2
  py:     { steps: [checkout, {run: 'uv run python -X utf8 -m pytest .github/scripts/notify/'}] }          # 러너3
```
러너1(landing sink·직렬화)=`npm test -w landing` → `deploy-landing.yml` build 전 step.

## 5. P1 SHIP 게이트 (전부 닫혀야 출시)

- [ ] **인증**: Bearer 누락/오류 401, nonce replay 409 (send.test)
- [ ] **발송 동시성**: N≥50 구독 브로드캐스트가 단일 `/send` wall-clock 한도 내 완주(Promise.allSettled 청크, [06 §3])
- [ ] **관측성**: send.py 가 `sent==0`/HTTP 실패 시 워크플로 RED(헬스게이트, [08 §2])
- [ ] **ece 졸업(선행)**: `tests/_attempts/pushHub/` Chrome ece 수신 성공 ([06 §5])
- [ ] **aes128gcm 실배달 — Chrome 1대**: 알림 수신·제목 표시
- [ ] **aes128gcm 실배달 — iOS 16.4+ standalone 1대**: 수신·제목 표시(Chrome 통과≠Apple 수락, 별 leg)
- [ ] **SW env 치환**: 빌드 산출물에 VAPID 키 인라인 확인([07] §7-1)
- [ ] **무인증 발송 차단**: Bearer/HMAC/nonce 누락·위조 시 401/409(send.test 9 시나리오)
- [ ] **sink 정화**: 제어문자·RTL·외부 originallink 링크 차단(sanitize.test)
- [ ] **권한 제스처**: requestPermission 이 클릭 안에서만, 콜드 자동팝업 0
- [ ] **landing 시각 회귀**: NotifyOptIn/InstallPrompt 겹침 없음 — **운영자 스크린샷 눈검수**
- [ ] **TOPIC_ALLOWLIST = blogPublish·cardPublish 2개**(newOrders 미포함)
- [ ] **3 러너 green**: ① `npm test -w landing`(node vitest, sink·직렬화) ② `cd infra/workers/pushHub && npm test`(workers pool, 401/409/purge·fan-out) ③ `pytest .github/scripts/notify/`(detect/payload/nonce). 단일 명령으로 못 묶음 — 셋 다 별 step

## 6. 미검증 → 닫을 작업 (가정 박제 금지)
- D1 `batch` 원자성 → `send.test`/`subscribe.test` 로 실측.
- Apple aes128gcm 수신 → iOS 실기기 게이트(§5).
- `npm test -w landing` CI 게이트화는 본 문서 §4 로 닫음(운영자 승인 = deploy-landing.yml 수정 1줄).
