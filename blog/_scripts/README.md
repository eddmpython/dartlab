# `blog/_scripts/` — 블로그·카드 도구 인덱스

블로그(`blog/**`)와 라이브 카드 캐러셀(`/cards`·터미널 카드뉴스)을 만드는 운영 도구 모음.

> **전 과정 파이프라인 SSOT = [../PIPELINE.md](../PIPELINE.md)** (주제→기획→작가/평가 루프→카드→이미지→발행). 본 문서는 그중 **스크립트 인덱스**.
**flat 디렉터리**다 — 스크립트끼리 같은 폴더에서 형제 import(`from cards_plan import …`)하므로
하위폴더로 옮기면 import·`publishCarousels.yml` 경로 트리거가 깨진다(④ 가드 참조).

> 실행은 전부 UTF-8 강행: `uv run python -X utf8 blog/_scripts/<script>.py …`

## ① 카드 파이프라인 (캐러셀 발행) — 상세 절차는 [CARDS.md](CARDS.md)
| 스크립트 | 역할 |
|---|---|
| `plan_card_news.py` | 블로그+카드+image_gen 기획 → `cards.plan.json` 생성·검사 |
| `build_carousel_contracts.py` | **발행** — frontmatter `carousel:` → hfMedia `carousels/index.json` 단일 파일 |
| `audit_carousel_images.py` | 이미지 감사 — 평면 벡터·도식·인포그래픽(쓰레기)을 색복잡도로 탐지 |
| `migrate_carousels_to_blog.py` | 1회성 이관(sns/carousels→frontmatter, **완료**) — `test_carousel_contracts` 의존으로 보존 |
| `test_cards_plan.py` · `test_carousel_contracts.py` | 카드 계획·발행 테스트 |

## ② 콘텐츠·이미지 생성 (썸네일·배경 hero)
| 스크립트 | 역할 |
|---|---|
| `gen_blog_thumbnails.py` | **전 카테고리 썸네일 SSOT** (글마다 즉흥 레이아웃 금지) |
| `gen_blog_cc0.py` | 사실적 실사가 맞을 때 쓰는 블로그 CC0/PD 수급 (Commons·Openverse) |
| `gen_news_thumbnails.py` | dartlab 소식(news) 썸네일 합성 |
| `gen_news_cc0.py` | 뉴스 CC0/PD 수급 |
| `gen_data_thumbnails.py` | 데이터 카테고리 썸네일 |
| `gen_news_flux.py` · `gen_company_flux.py` | FLUX 생성형 hero. 운영자 명시 지시 시에만 |

## ③ audit · insights
| 스크립트 | 역할 |
|---|---|
| `publishBlogAssets.py` | **블로그 v2 미디어 발행**. 로컬 본문 이미지·OG를 HF `blog/{slug}/` 해시 경로에 올리고 `assets/media.json`과 본문 URL 반영 |
| `publishGate.py` | **블로그 발행 단일 진입점**. `auditBlog` 하드 계약 + SEO 95 + 신규 v2 시나리오·이미지 SSOT를 함께 검사 |
| `blogMedia.py` | `media.json`, HF 경로, URL, 콘텐츠 해시 계약 SSOT |
| `auditBlog.py` | 글 단위 구조 audit와 `publishGate.py`의 하드 계약 엔진. 단독 결과는 발행 승인 아님 |
| `audit_seo.py` | SEO·깊이·캐러셀 진단과 `publishGate.py`의 점수 엔진. 단독 결과는 발행 승인 아님 |
| `auditBlogFinance.py` | 회사 글 재무 표 ↔ `dartlab.Company().select()` 실측 1:1 정합 |
| `backfill_blog_insights.py` | 글 `ai:` 블록 → `dartlab.knowledge.insights(source="blog")` 백필 (AI retrieve 인용) |
| `runCells.mjs` | **브라우저 실행셀 발행 게이트** (dartlab-stories 전용). `auditBlog.py` 가 문자를 본다면 이건 실제 chromium 에서 본문 코드가 도는지 본다. ok / empty(조용히 삼킴) / error 를 가른다. `node blog/_scripts/runCells.mjs --post <폴더>` (dev 5173 전제). playwright 는 repo 설치본을 빌려 쓴다 |

## ④ 공유 lib (flat 형제 import — **이동 금지**)
| 스크립트 | import 하는 곳 |
|---|---|
| `cards_plan.py` | `plan_card_news` · `build_carousel_contracts` · `test_cards_plan` |
| `fetch_cc0_images.py` | `gen_blog_cc0` · `gen_news_cc0` (CC0/PD 다운로드 헬퍼 공유) |

## 관련 — `sns/scripts/` (자산 공유풀·HF 발행)
신규 v2 블로그 바이너리는 HF `dartlab-media/blog/{slug}/`가 SSOT다. `sns/assets/{subjectKey}/`는 legacy 회사 공유 staging이다.
- `ingest_blog_assets.py`: legacy 회사 블로그 자산을 공유 staging으로 복사(멱등·손작성 자산 보호). v2 블로그에는 사용하지 않는다.
- `build_index.py` → `publish_assets_hf.py` — 인덱싱 → hfMedia 업로드.
- `extractImagegenAssets.py` · `checkImagegenAssets.py` — GPT image_gen 산출물 추출·프레이밍 검사.
