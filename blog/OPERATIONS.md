# 콘텐츠 운영 SSOT (블로그·카드·팟캐스트·분석)

> 이 파일 하나로 콘텐츠 생산의 소스·정책·파이프라인 위치를 다 찾는다. **라우팅 + 정본 선언**만 담고, 상세는 각 문서로 링크한다(중복 금지). 강행규칙은 `CLAUDE.md`.

콘텐츠 소스 SSOT 루트 = `blog/`. 여기에 블로그 글·카드(`_issues`)·팟캐스트(`_podcasts`)가 전부 git 추적된다. 주제(subject)는 회사만이 아니라 경제·기술·분석 테마도 1급이다. 블로그만/카드만 개별 발간 가능하고, 나중에 같은 주제로 관련 카드·팟캐스트가 추가 발간된다(슬롯이 채워짐).

**세 서피스(블로그·카드·팟캐스트)는 무조건 하나의 공동 작업대를 거친다.** 주제 -> 데이터 워크벤치(dartlab, 데이터 SSOT) 런타임 직독 -> 서사 코어(StoryCore) -> 근거검증·정직성 -> 자산수급 공유 front 를 통과하고, 서피스 어댑터가 각 형식으로 투영한다. 블로그만/카드만 발행해도 이 공유 front 는 거친다. 릴스·쇼츠·비디오는 나중에 서피스 어댑터만 추가하면 붙는다. **작업대·StoryCore·서피스 seam·evidence 표준 설계 정본 = Skill OS `operation.content`.**

---

## 1. Git·추적 정책

한 줄 규칙: **손으로 쓴 텍스트·메타·차트는 repo git 추적. 대용량·파생·재생성물은 미추적. 공유/서빙 미디어는 HF(이미지)·R2(팟캐스트 오디오)로 발행되어 거기가 durable SSOT.**

| 분류 | 대상 | 위치 |
|---|---|---|
| **추적 (소스)** | 마크다운(index.md·script.md), 메타(carousel.yaml·cards.plan.json·episode.yaml·channel.yaml·published.json·brief.json), SVG 차트, 포스트별 `assets/` 손작성 이미지, 운영문서 | `blog/**` (git) |
| **미추적 (파생/대용량)** | 팟캐스트 오디오(mp3/m4a/wav/aac), sns 렌더 PNG/MP4, 빌드 산출 | `blog/_podcasts/.gitignore`, `/sns/`(root .gitignore), `landing/static/carousels\|issues` |
| **발행 = durable SSOT** | 공유 이미지 원본(회사/주제), 카드·블로그 서빙 이미지 | HF `dartlab-media` (versioned). 로컬 `sns/assets/{code}`는 재생성 staging 캐시(미추적이 정상) |
| **발행 = durable SSOT** | 팟캐스트 오디오·커버·정적프레임·feed | R2 `dartlab-podcast` |

- 커밋·푸시 규약(변경 단위·`git commit -o`·push 게이트·UI 승인)은 `CLAUDE.md` 강행규칙 + memory `git_rules` 상세가 정본.
- (선택, 운영자 결정) 손수 만든 공유 이미지 원본을 repo git 으로도 보존하려면 추적 `blog/_assets/{code}/` 신설 후 sns 파이프라인이 그곳을 우선 읽게. 기본은 HF-as-SSOT 유지(churn 0, 이미 durable).

## 2. 자산·소스·이미지 정책

- 이미지 수급: **Openverse 실사 주력(Claude) -> GPT 세션은 image_gen 1차. FLUX(Replicate)는 운영자 명시 지시 시에만**(Claude 는 먼저 제안 안 함, 2026-07-04 갱신). 정본 = memory `feedback_image_sourcing_policy`.
- 회사 주제 카드/이미지 배경은 그 회사 실제 로고·제품·상호(간판)를 기본값(generic 산업장면 탈출 금지, 재무·교육 카드라 저작권 무관). 정본 = `feedback_image_sourcing_policy` + memory `feedback_sns_assets`(회사 시그니처).
- 공유 자산 풀(한 세트): `sns/assets/{code}` 에 회사당 1벌을 모아 블로그·카드·팟캐스트가 공유. 상세 = `sns/assets/README.md`. 포맷마다 재생성 금지.
- 블로그 포스트 전용 자산은 그 포스트 `assets/` (git 추적). SVG 차트·썸네일 생성 = `blog/_scripts/`(gen_blog_thumbnails.py·gen_blog_cc0.py). 상세 = `blog/BLOG.md`.

## 3. HF/R2 저장 정책

- HF 데이터셋 `eddmpython/dartlab-media` (config `src/dartlab/core/dataConfig.py`, 프록시 origin `hfMedia`, resolver `landing/src/lib/cards/media.ts`). 프리픽스: `companies/{code}/`(공유 회사 이미지)·`issues/{slug}/`(카드)·`podcasts/{slug}/`(팟캐스트 meta/topic 소스 이미지). 파일명 콘텐츠해시. 상세 = memory `reference_hf_dataset_layout` + `sns/assets/README.md`.
- R2 버킷 `dartlab-podcast` (r2.dev 공개). 팟캐스트 오디오·커버·정적프레임·feed.xml·index.json. HF `/resolve` 302 라 팟캐스트 플랫폼 미디어는 R2. 상세 = memory `reference_cloudflare_r2_infra`.
- 이미지 규격표:

| 용도 | 규격 |
|---|---|
| 카드/블로그 이미지 | 포맷별(카드 4:5 등), HF companies/issues |
| 팟캐스트 채널·에피소드 커버 | 정사각 RGB 1400~3000, <500KB, R2 |
| 팟캐스트 정적프레임·썸네일 | 16:9 1280x720, <500KB, R2 |

## 4. 파이프라인 라우팅

| 파이프라인 | 진입/발행 | 상세 문서 |
|---|---|---|
| 블로그 | 저작 -> `blog/_scripts/audit_seo.py` -> 발행 | `blog/BLOG.md` (+ `blog/PIPELINE.md`) |
| 카드뉴스 | `plan_card_news.py` -> `build_carousel_contracts.py` -> HF `carousels/index.json` | `blog/_scripts/CARDS.md` (+ `blog/_scripts/README.md`) |
| 이미지 공유풀 | `sns/scripts/build_index.py` -> `publish_assets_hf.py` (blog 흡수 `ingest_blog_assets.py`) -> HF `companies/` | `sns/assets/README.md` |
| 팟캐스트 | `podcast_plan_loop.workflow.js` -> `plan_episode.py` -> (NotebookLM) -> `render_episode_image.py` -> `publish_podcast.py` -> R2+HF | `blog/_podcasts/README.md` + `blog/_podcasts/GUIDE.md` |
| SNS 트랙(쇼츠·릴스 등) | 트랙별 | `sns/README.md` + `sns/{track}/README.md` |

각 파이프라인의 dev(테스트)는 소스 옆(`test_carousel_contracts.py` 등), ops(발행)는 위 문서. 중복 지시는 위 정본으로 수렴.

## 5. Subject·발행 모델

- `subjectKey` = stockCode(회사) 또는 topicSlug(경제·기술·분석 테마). `kind` in {company, economy, tech, analysis, meta}.
- 각 subject 는 blog/cards/podcast 슬롯을 갖고 시간이 지나며 채워진다(빈 슬롯 = 자리표시자).
- 개별 발행: 블로그·카드·팟캐스트 각 파이프라인이 독립 발행. 집계(프론트 SubjectHub)는 발행을 막지 않고 현재 상태를 조인해 "이 주제의 블로그/카드/팟캐스트"를 보여준다.
- 조인 키 = stockCode/topicSlug. 1차는 프론트 클라이언트 조인(`carousels/index.json` + `dartlab-podcast/index.json` + `companies/index.json`), 승격 시 파생 `subjects/index.json`.

---

## 참고 히스토리
- 2026-07-02 팟캐스트 트랙 blog/_podcasts 로 이관(sns 아님). 콘텐츠 운영 SSOT 이 문서 신설.
- 정책 정본: git=`CLAUDE.md`+`git_rules`, 이미지수급=`feedback_image_sourcing_policy`, R2=`reference_cloudflare_r2_infra`, HF=`reference_hf_dataset_layout`, 공유풀=`sns/assets/README.md`, 블로그=`BLOG.md`, 카드=`CARDS.md`, 팟캐스트=`blog/_podcasts/README.md`.
