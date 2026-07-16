# 콘텐츠 자산 SSOT 구조화 PRD

> **위치.** 이 PRD 는 Skill OS `operation.content` 가 정의한 **공동 작업대 SSOT** 를 물리로 실현하는 실행 로드맵이다(StoryCore 개념 계약 -> StoryManifest 물리 통합). 설계 정본은 operation.content, 본 PRD 는 P0~P4 마이그레이션 집행. 조인 키 어휘는 `blog/OPERATIONS.md` §5 와 통일한다: **subject**(조인 키, 회사=stockCode·주제=topicSlug) 아래 여러 **story**(관통선 1개 = 생산 단위, `storyId`)가 달린다.

## 1. 문제

현재 블로그, 랜딩 카드뉴스, 이미지 자산은 같은 콘텐츠를 만들지만 저장 위치와 발행 경로가 나뉘어 있다.

| 영역 | 현재 원본 | 현재 HF 서빙 |
|---|---|---|
| 회사 장문 글 | `blog/05-company-reports/{post}/index.md` | 랜딩 빌드 산출물 |
| 회사 카드뉴스 | 글 frontmatter `carousel:` | `carousels/index.json` |
| 이슈 카드뉴스 | `blog/_issues/{slug}/carousel.yaml` | `carousels/index.json` |
| 회사 이미지 | `sns/assets/{code}/` | `companies/{code}/...` |
| 이슈 이미지 | `blog/_issues/{slug}/assets/` | `issues/{slug}/...` |
| image_gen 기획·검수 | 각 글/이슈의 `cards.plan.json` | 일부만 `carousels/index.json`에 반영 |

이 구조는 동작은 하지만 장기 자산화에는 약하다.

- 같은 story의 글, 카드, 이미지, 출처, 검수 기록이 한 폴더/manifest로 모이지 않는다.
- 회사 카드와 이슈 카드가 `code` 유무만으로 라이브 report 첨부 여부가 갈린다.
- HF에는 서빙 파일이 흩어져 있고, Git에는 편집 원본이 흩어져 있어 추적 단위가 story가 아니다.
- SNS 재활용, 카드 개선, 이미지 교체, 출처 감사가 매번 경로별 규칙을 다시 알아야 한다.

## 2. 목표

콘텐츠의 기본 단위를 `story`로 올린다.

1. 블로그 글, 카드뉴스, 이미지, 출처, image_gen 기획, 리뷰 게이트를 story 단위로 묶는다.
2. Git은 사람이 편집하는 원본 SSOT로 유지한다.
3. HF `dartlab-media`는 브라우저가 읽는 서빙 자산 SSOT로 유지한다.
4. `/cards`, `/blog`, SNS 재활용은 같은 story manifest를 소비한다.
5. 기존 `carousels/index.json`, `companies/{code}`, `issues/{slug}`는 깨지지 않게 호환 레이어로 유지한다.

## 3. 비목표

- 블로그 글 전체를 즉시 HF로 이관하지 않는다.
- 랜딩 화면을 먼저 갈아엎지 않는다.
- 기존 발행물 URL과 카드 슬러그를 깨지 않는다.
- 이미지 원본과 해시 서빙 파일을 같은 의미로 섞지 않는다.

## 4. 제안 구조

### Git 원본

신규 story 단위 원본 폴더를 둔다.

```text
content/stories/{storyId}/
  story.yaml
  article.md              # 있으면 블로그 장문 원본
  cards.yaml              # 랜딩 카드 손글 계약
  cards.plan.json         # image_gen 기획·토론·검수 게이트
  assets/
    {assetKey}.webp       # 사람이 검수한 원본 이미지
    CREDITS.md
  sources.yaml            # 공식 출처, 수치 근거, 조회일
```

`story.yaml` 핵심 필드:

```yaml
storyId: samsung-biologics-rockville-rampup
kind: companyStory        # companyStory | issueStory | macroStory | productStory
stockCode: "207940"       # 있으면 회사 report 덱 첨부 가능
corpName: 삼성바이오로직스
title: 삼성바이오로직스는 좋은 숫자보다 공장 가동을 봅니다
date: 2026-06-28
surfaces:
  blog: false
  cards: true
  snsReuse: true
```

### HF 서빙

HF는 브라우저 소비 기준으로 story 네임스페이스를 둔다.

```text
stories/{storyId}/manifest.json
stories/{storyId}/assets/{assetKey}.{hash8}.webp
stories/index.json
carousels/index.json       # 호환 산출물, stories에서 생성
companies/index.json       # 회사 hero 호환 산출물
```

`manifest.json`은 카드 계약, 이미지 해시 경로, 출처 요약, company code를 함께 갖는다.

```json
{
  "storyId": "samsung-biologics-rockville-rampup",
  "kind": "companyStory",
  "stockCode": "207940",
  "corpName": "삼성바이오로직스",
  "date": "2026-06-28",
  "cards": { "slides": [] },
  "assets": {
    "scene-01-cover-hook": "stories/samsung-biologics-rockville-rampup/assets/scene-01-cover-hook.7b725aa9.webp"
  },
  "sources": [],
  "reviewGate": { "status": "passed" }
}
```

## 5. 동작 원칙

- `stockCode`가 있으면 카드 뒤에 회사 report 기반 KPI·그래프·테이블을 붙인다.
- `article.md`가 없으면 블로그 CTA는 숨긴다.
- `stockCode`와 `article` 존재 여부를 분리한다. 이슈 카드라도 기업 코드가 있으면 회사 덱을 붙일 수 있다.
- 카드 이미지 참조는 `assetKey`만 쓴다. 서빙 경로와 해시는 manifest 생성기가 채운다.
- 출처 수치가 없는 숫자는 카드 슬라이드에 쓰지 않는다.
- `cards.plan.json`이 있으면 `reviewGate.status=passed` 전에는 발행하지 않는다.

## 6. 마이그레이션

1. **P0 — 현재 버그 정정**
   - `blog/_issues/*/carousel.yaml`에서 `stockCode`를 읽어 카드 계약 `code`에 싣는다.
   - `stockCode`가 있는 이슈 카드는 블로그 CTA는 숨기되 회사 report 덱은 붙인다.

2. **P1 — story manifest 생성기 추가**
   - 기존 `blog/05-company-reports`와 `blog/_issues`를 읽어 내부 `StoryManifest`로 정규화한다.
   - 기존 `carousels/index.json`은 `StoryManifest`에서 생성한다.
   - 기존 URL과 HF 경로는 그대로 유지한다.

3. **P2 — HF `stories/` 병행 발행**
   - `stories/index.json`과 `stories/{storyId}/manifest.json`을 추가 발행한다.
   - `/cards`는 아직 `carousels/index.json`을 읽는다.
   - 검증은 두 산출물이 같은 카드 수와 슬라이드 수를 갖는지 비교한다.

4. **P3 — `/cards` 소비자 전환**
   - `/cards`가 `stories/index.json`을 읽고, 호환 경로가 필요한 곳만 어댑터를 탄다.
   - `carousels/index.json`은 레거시 호환 파일로 남긴다.

5. **P4 — 원본 폴더 통합**
   - 신규 콘텐츠는 `content/stories/{storyId}`에서만 작성한다.
   - 기존 `blog/_issues`와 frontmatter carousel은 읽기 호환만 유지한다.

## 7. 검증 게이트

- story manifest 스키마 검사.
- 카드 계약 수, 슬라이드 수, image asset key 매칭 검사.
- `stockCode` 있는 story는 `/cards` 덱에 report 카드가 붙는지 Playwright로 확인.
- `article.md` 없는 story는 블로그 CTA가 숨는지 확인.
- HF 발행 dry-run에서 신규/삭제 파일 목록 확인.
- 기존 `carousels/index.json` 소비 테스트 유지.

## 8. 판단

바로 전체 이관하지 말고, 먼저 `StoryManifest` 내부 모델을 세운 뒤 HF `stories/`를 병행 발행하는 순서가 맞다. 현재 운영 중인 `/cards`는 단일 `carousels/index.json` 덕분에 안정적이므로, 그 파일을 깨지 않고 뒤에서 story SSOT를 키워야 한다.

## 9. 진행 원장

- 2026-07-17 **블로그 발행 계약 v2와 현행 자산 경계 안정화 완료.** 물리 StoryManifest 이관 없이 현재 글 폴더를 기준으로 의미 계약 `brief.json.imagePlan[]`, 바이너리 저작 원본 `assets/<assetKey>.webp`, 출처 원본 `assets/CREDITS.md`를 고정했다. `sns/assets/{subjectKey}`는 재사용 staging, HF는 서빙 SSOT, `landing/static/thumbnails`는 파생본으로 분리했다. 신규 심층 글은 `watchScenarios[]`와 마지막 시나리오형 관전 포인트를 요구하며, `publishGate.py`가 하드 계약과 SEO를 한 번에 검사한다.
- 2026-07-06 **개념 토대(subject 조인 키 모델) 표준화·강제 완료.** 이 PRD 의 1절(회사·이슈 카드가 `code` 유무로만 갈림)과 3절(subject 단위 추적)을 실현하는 조인 키를 전 서피스에서 통일했다: 회사=`stockCode`, 주제=`topicSlug`(= 블로그 URL slug, 전 서피스 공유). `operation.content` "서피스 x 콘텐츠 성격 매트릭스"로 명문화하고 블로그·팟캐스트·카드 게이트로 강제(상세 = `blog-enrichment` 진행 원장 2026-07-06). 즉 **subject 조인 키 계약은 물리 SSOT 로 살아있고**, 남은 것은 물리 통합뿐이다.
- **미착수·승인 게이트 유지**: 물리 `StoryManifest` 마이그레이션(P1 manifest 생성기, P2 HF `stories/` 병행 발행, P3 `/cards` 소비자 전환, P4 원본 폴더 통합)은 대형 저장구조 변경 + 랜딩 소비자 전환이라 런타임-SSOT 규율상 사전토론·명시 승인 후에만 착수한다. 현행 `carousels/index.json` 단일 소비가 안정적이라 급하지 않다. 착수 트리거는 운영자 결정.
