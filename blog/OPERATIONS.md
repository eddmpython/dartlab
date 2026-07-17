# 콘텐츠 운영 SSOT (블로그·카드·팟캐스트·분석)

> 이 파일 하나로 콘텐츠 생산의 소스·정책·파이프라인 위치를 다 찾는다. **라우팅 + 정본 선언**만 담고, 상세는 각 문서로 링크한다(중복 금지). 강행규칙은 `CLAUDE.md`.

콘텐츠 소스 SSOT 루트 = `blog/`. 여기에 블로그 글·카드(`_issues`)·팟캐스트(`_podcasts`)가 전부 git 추적된다. 주제(subject)는 회사만이 아니라 경제·기술·분석 테마도 1급이다. 블로그만/카드만 개별 발간 가능하고, 나중에 같은 주제로 관련 카드·팟캐스트가 추가 발간된다(슬롯이 채워짐).

**세 서피스(블로그·카드·팟캐스트)는 무조건 하나의 공동 작업대를 거친다.** 주제 -> 데이터 워크벤치(dartlab, 데이터 SSOT) 런타임 직독 -> 서사 코어(StoryCore) -> 근거검증·정직성 -> 자산수급 공유 front 를 통과하고, 서피스 어댑터가 각 형식으로 투영한다. 블로그만/카드만 발행해도 이 공유 front 는 거친다. **데이터 워크벤치의 유니버스는 DART(국내 상장)와 EDGAR(미국 상장) 전 종목을 함께 쓴다.** 한 이야기가 두 시장을 동시에 근거로 삼을 수 있다(예: 국내사와 미국사 비교, 또는 공급망이 두 시장에 걸친 대상). 릴스·쇼츠·비디오는 나중에 서피스 어댑터만 추가하면 붙는다. **작업대·StoryCore·서피스 seam·evidence 표준 + 양시장 유니버스 설계 정본 = Skill OS `operation.content`.**

---

## 1. Git·추적 정책

한 줄 규칙: **손으로 쓴 텍스트·메타·차트는 repo git 추적. 대용량·파생·재생성물은 미추적. 공유/서빙 미디어는 HF(이미지)·R2(팟캐스트 오디오)로 발행되어 거기가 durable SSOT.**

| 분류 | 대상 | 위치 |
|---|---|---|
| **추적 (저작 원본)** | 마크다운(index.md·script.md), 메타(carousel.yaml·cards.plan.json·episode.yaml·channel.yaml·published.json·brief.json), SVG 차트, `assets/CREDITS.md`, 중앙 `media/catalog.json`, 운영문서 | `blog/**` (git) |
| **미추적 (작업/파생)** | 블로그 WebP/JPG/PNG staging, 합성 썸네일, 팟캐스트 오디오, sns 렌더 PNG/MP4, 빌드 산출 | 포스트 `assets/`, `landing/static/thumbnails/`, `blog/_podcasts/.gitignore`, `/sns/` |
| **재사용 staging** | HF 발행 전 로컬 작업본과 회사 공유 작업본 | 포스트 `assets/<assetKey>.webp`, `sns/assets/{subjectKey}`. durable 원본 아님 |
| **발행 = 이미지 SSOT** | 블로그 본문·OG·카드·브라우저 서빙 이미지 | HF `dartlab-media/objects/sha256/`의 전역 콘텐츠 주소 객체 |
| **발행 = durable SSOT** | 팟캐스트 오디오·커버·정적프레임·feed | R2 `dartlab-podcast` |

- 커밋·푸시 규약(변경 단위·`git commit -o`·push 게이트·UI 승인)은 `CLAUDE.md` 강행규칙 + memory `git_rules` 상세가 정본.
- 새 `blog/_assets`, 임시 다운로드 폴더, 포스트 밖 원본 폴더를 만들지 않는다. 블로그 로컬 staging은 포스트 `assets/`, 카드 전용 staging은 `blog/_issues/<slug>/assets/`에만 두고 바이너리는 Git에 추가하지 않는다.

## 2. 자산·소스·이미지 정책

- 이미지 수급은 **자율**이다. 파이프라인이 실제 제품·인물·현장처럼 사실성이 중요한 피사체는 공식 출처 또는 라이선스가 확인된 실사를, 개념·원리·추상 장면은 `image_gen`을 선택한다. 적합본이 없으면 운영자 질문으로 멈추지 않고 다른 적합 경로로 전환한다. 핀터레스트·구글 이미지 무단 사용은 금지다. FLUX는 운영자의 명시 지시가 있을 때만 쓴다.
- 이미지 의미 계약 SSOT는 블로그 `brief.json.imagePlan[]`, 카드 `cards.plan.json`이다. 블로그 신규 계약은 고유 `assetKey`와 `sourcePolicy: auto`를 요구한다.
- 블로그 바이너리는 포스트 `assets/<assetKey>.webp`에서 로컬 검수한 뒤 `publishBlogAssets.py`로 HF 전역 콘텐츠 주소 객체에 올린다. 같은 바이트는 포스트·OG·카드 구분 없이 한 번만 저장한다. 본문, `ogImage`, `cardPreview`는 HF URL만 참조하며 Git에는 중앙 `media/catalog.json`의 별칭·역할·해시와 `assets/CREDITS.md`의 출처만 남긴다.
- `sns/assets/{subjectKey}`도 공유 staging일 뿐 SSOT가 아니다. 블로그, 기술 카드, 회사 카드, 팟캐스트 원본은 중앙 카탈로그의 같은 HF 객체를 재사용한다. 로컬 staging 복원은 `seedBlogMedia.py --post ...` 또는 `--all`로만 한다.

## 3. HF/R2 저장 정책

- HF 데이터셋 `eddmpython/dartlab-media` (config `src/dartlab/core/dataConfig.py`, origin `hfMedia`). 바이너리 허용 위치는 전역 `objects/sha256/` 하나다. 런타임이 읽는 파생 뷰는 `manifests/companies.json`, `manifests/carousels.json` 두 파일뿐이다. 의미 키, source, 역할, SHA-256 대응의 정본은 Git `media/catalog.json`이다. HF에 회사별, 글별, 콘텐츠 종류별 바이너리 폴더를 만들지 않는다.
- R2 버킷 `dartlab-podcast` (r2.dev 공개). 팟캐스트 오디오·커버·정적프레임·feed.xml·index.json. HF `/resolve` 302 라 팟캐스트 플랫폼 미디어는 R2. 상세 = memory `reference_cloudflare_r2_infra`.
- 이미지 규격표:

| 용도 | 규격 |
|---|---|
| 카드/블로그 이미지 | 포맷별(카드 4:5 등), HF `objects/sha256/` |
| 팟캐스트 채널·에피소드 커버 | 정사각 RGB 1400~3000, <500KB, R2 |
| 팟캐스트 정적프레임·썸네일 | 16:9 1280x720, <500KB, R2 |

## 4. 파이프라인 라우팅

| 파이프라인 | 진입/발행 | 상세 문서 |
|---|---|---|
| 블로그 | 저작 -> `publishBlogAssets.py --post <글폴더>` -> `publishGate.py --post <글폴더>` -> 발행 | `blog/BLOG.md` (+ `blog/PIPELINE.md`) |
| 카드뉴스 | `plan_card_news.py` -> `build_carousel_contracts.py` -> HF `manifests/carousels.json` + 객체 | `blog/_scripts/CARDS.md` (+ `blog/_scripts/README.md`) |
| 이미지 공유 staging | `sns/scripts/build_index.py` -> `publish_assets_hf.py` -> 중앙 catalog + HF `manifests/companies.json` + 객체 | `sns/assets/README.md` |
| 팟캐스트 | `podcast_plan_loop.workflow.js` -> `plan_episode.py` -> (NotebookLM) -> `render_episode_image.py` -> `publish_podcast.py` -> R2+HF | `blog/_podcasts/README.md` + `blog/_podcasts/GUIDE.md` |
| SNS 트랙(쇼츠·릴스 등) | 트랙별 | `sns/README.md` + `sns/{track}/README.md` |

각 파이프라인의 dev(테스트)는 소스 옆(`test_carousel_contracts.py` 등), ops(발행)는 위 문서. 중복 지시는 위 정본으로 수렴.

## 5. Subject·발행 모델

- `subjectKey` = stockCode(회사) 또는 topicSlug(경제·기술·분석 주제). **주제 topicSlug = 블로그 URL slug** 로 통일한다(전 서피스 공유 조인 키). 회사 하나가 주인공일 때만 stockCode, 기술·데이터·이슈처럼 여러 회사를 다루면 topicSlug. **조인 키 계약 SSOT = Skill OS `operation.content` "서피스 x 콘텐츠 성격 매트릭스".**
- 각 subject 는 blog/cards/podcast 슬롯을 갖고 시간이 지나며 채워진다(빈 슬롯 = 자리표시자).
- 개별 발행: 블로그·카드·팟캐스트 각 파이프라인이 독립 발행. 집계(프론트 SubjectHub)는 발행을 막지 않고 현재 상태를 조인해 "이 주제의 블로그/카드/팟캐스트"를 보여준다.
- 조인 키 = stockCode/topicSlug. 1차는 프론트 클라이언트 조인(`manifests/carousels.json` + `dartlab-podcast/index.json` + `manifests/companies.json`), 승격 시 파생 `subjects/index.json`.

---

## 참고 히스토리
- 2026-07-05 데이터 유니버스 명시: DART(국내)+EDGAR(미국) 전 종목을 한 파이프라인에서 함께 근거로 사용(양시장 비교·크로스 공급망). 정본 = `operation.content` 데이터 워크벤치 절.
- 2026-07-02 팟캐스트 트랙 blog/_podcasts 로 이관(sns 아님). 콘텐츠 운영 SSOT 이 문서 신설.
- 정책 정본: git=`CLAUDE.md`+`git_rules`, 이미지 수급과 자산 경계=이 문서 2절, R2=`reference_cloudflare_r2_infra`, HF=`reference_hf_dataset_layout`, 공유 staging=`sns/assets/README.md`, 블로그 집필=`BLOG.md`, 카드=`CARDS.md`, 팟캐스트=`blog/_podcasts/README.md`.
