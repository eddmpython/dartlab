# 팟캐스트 트랙 SSOT

DartLab 팟캐스트. 우리 파이프라인이 **완결 산문 소스 문서(기획서)** 를 만들고, 운영자가 그걸
Google NotebookLM 에 넣어 오디오 개요를 생성한다. 결과 오디오를 R2 에 올리고 RSS 로 발행해
YouTube Music, Apple Podcasts, Spotify 로 내보낸다. 카드뉴스, 블로그, 터미널의 같은 회사, 같은
주제와 서로 링크된다.

> **부활 근거 (2026-07-02).** 팟캐스트 트랙은 2026-06-30 "음성 품질 미달"로 폐기됐다. 그 사유는
> 자체 TTS 렌더의 한계였다. 새 파이프라인은 오디오를 렌더하지 않는다. NotebookLM 이 오디오를
> 만든다. 우리 산출물의 정체성이 "음성"에서 "완결 내러티브 소스 문서"로 바뀐 것이 부활의 핵심이다.

---

## 1. 무엇을 우리가 하고, 무엇을 운영자가 하나

| 단계 | 주체 | 도구 |
|---|---|---|
| 주제 기획 + 소스 문서 작성 + 평가 루프 | 파이프라인 | `_lib/podcast_plan_loop.workflow.js` + `_lib/plan_episode.py` |
| script.md 검토 | 운영자 | 눈검수 |
| 오디오 생성 | 운영자 + NotebookLM | `templates/notebooklm_settings.md` 설정 |
| 오디오 -> R2 업로드 + RSS/인덱스 발행 | 파이프라인 | `_lib/publish_podcast.py` |
| 플랫폼 최초 제출(1회) | 운영자 | Apple/Spotify/YouTube 콘솔 |
| 카드/블로그/터미널 링크 렌더 | 파이프라인(프론트) | 랜딩 (Phase 2) |

핵심: **내용거리와 기획은 우리 파이프라인이 한다.** 운영자는 script.md 검토, NotebookLM 실행,
오디오 전달, 플랫폼 최초 제출만 한다. 그 다음부터는 발행 명령 하나로 세 플랫폼에 자동 반영된다.

---

## 2. 폴더 구조

```
blog/_podcasts/
├── README.md                     # 이 파일 (트랙 SSOT)
├── channel.yaml                  # RSS channel 상수 + R2 baseUrl + 커버 소스
├── assets/
│   └── showCover.png             # 쇼 커버 소스 (정식본은 생성 이미지로 교체 가능)
├── templates/
│   ├── sourceDoc.template.md     # 소스 문서(기획서) 뼈대
│   ├── episode.template.yaml     # episode.yaml 뼈대
│   └── notebooklm_settings.md    # NotebookLM 고정 설정(언어·소스만·톤)
├── _lib/
│   ├── podcast_plan_loop.workflow.js  # 기획 루프 (기획작가 -> 평가자+회의자, 통과까지)
│   ├── plan_episode.py           # plan JSON -> 에피소드 폴더(script.md+episode.yaml+brief.json)
│   └── publish_podcast.py        # 전사+R2 업로드+RSS/인덱스 발행 (발행자)
└── episodes/
    └── P0N-{lane}-{slug}/        # 에피소드 산출물
        ├── episode.yaml          # 메타데이터 SSOT (사람 작성)
        ├── cover.jpg             # RSS item 정사각 커버
        ├── static-video.jpg      # 16:9 정적 영상 이미지와 썸네일 소스
        ├── CREDITS.md            # 이미지 출처와 역할
        ├── imagegen-extract.json # 생성 이미지 추출 로그(있는 편만)
        ├── script.md             # NotebookLM 소스 문서 (우리 최종 deliverable)
        ├── brief.json            # 기획 요지 + 루프 로그
        └── published.json        # 발행 기계값 (guid mint-once, 오디오 크기/길이/발행일)
```

오디오(m4a/mp3)는 레포에 두지 않는다. R2 런타임 산출물이라 용량을 격리한다. 에피소드 `assets/`는
작업 중에만 생기는 임시 staging이며 완료 상태에는 남기지 않는다. 레포에는 텍스트와 작은 커버 소스만 커밋한다.

## 3. R2 레이아웃 (버킷 dartlab-podcast, 공개 r2.dev)

```
dartlab-podcast/                                  baseUrl = https://pub-...r2.dev
├── feed.xml                                       RSS 2.0 (플랫폼 제출 대상, 재발행마다 덮어쓰기)
├── index.json                                     프론트 크로스링크 레지스트리
├── cover/show-cover-3000.jpg                      쇼 커버 (정사각 RGB, <500KB)
└── episodes/<slug>/
    ├── audio.mp3                                  전사 MP3 (enclosure)
    ├── cover-3000.jpg                             RSS item 커버 (정사각 RGB, <500KB)
    └── static-video.jpg                           정적 영상 이미지 (16:9 RGB, <500KB)
```

## 3-1. HF media 원본 레이아웃

최종 RSS 산출물은 R2에 둔다. 재사용 가능한 원본 배경은 중앙 catalog에 등록하고 HF 콘텐츠 주소 객체로 둔다.
이 원본으로 `cover.jpg` 와 `static-video.jpg` 를 언제든 다시 만들 수 있다.

```
eddmpython/dartlab-media/
└── objects/sha256/<앞2자>/<전체해시>.webp
```

R2 를 쓰는 이유: egress 무료(청취자 스트리밍 트래픽 부담 0), 200 직응답(HF `/resolve` 는 302
리다이렉트라 Apple 이 거부), Range 요청 지원(스트리밍/시크). 자격증명은 기존 `.env`
`CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` 로 wrangler 가 업로드한다(새 S3 키 불필요).

## 4. 발행 플로우

```
# 1. 기획 루프 (통과까지 반복). evidence 는 메인 스레드에서 dartlab 직독으로 확인한 수치.
Workflow({ scriptPath: "blog/_podcasts/_lib/podcast_plan_loop.workflow.js",
           args: { topic, lane, evidence } })

# 2. 통과한 plan 을 에피소드 폴더로 저작
uv run python -X utf8 blog/_podcasts/_lib/plan_episode.py --plan plan.json --lane company --slug <slug> --stock-code <6자리>

# 3. 운영자: script.md 검토 -> NotebookLM 에 제공 -> 오디오 m4a 수령 -> episode.yaml status=ready

# 4. 정적 이미지 렌더 (sourceAssets 원본 -> cover.jpg + static-video.jpg)
uv run python -X utf8 blog/_podcasts/_lib/render_episode_image.py --episode P0N-...

# 5. 발행 (전사 -> R2 업로드 -> HF 원본 업로드 -> feed.xml + index.json 재생성 -> _uploads 사본)
uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py --episode P0N-... --audio <m4a 경로>
```

멱등: 같은 에피소드 재발행 시 guid 재사용(구독자 중복 방지), 재전사·재업로드로 정정한다.
검증만: `--dry-run`. feed/index 만 재생성: `--rebuild-only`.

## 5. 발행 게이트

- `episode.yaml` `status` 가 `ready` 이상만 발행 대상.
- 기획은 `podcast_plan_loop` 의 평가자(6원칙 각 85점 이상) + 회의자(hard 축 0 kill) 둘 다 통과해야 함.
- 6원칙: 완결·따라오기 / 인사이트(통념-반전-메커니즘-렌즈) / 귀 정합(숫자에 분모·기간, 시각 의존 금지) /
  쉬움·담백(약어 풀기, 허황된 비유 금지, AI는 그대로) / 재미·호기심(오프닝 갭, 클로징이 약속 갚음) /
  구조 독창성(같은 뼈대 반복 금지).
- 회의자 hard 축: forced-metric, misleading-frame, overclaim, external-dependency(문서 밖 지식 의존).
- 숫자는 dartlab 직독 검증본만. 지어내기 금지. 투자 권유·목표가·확정 전망 금지.
- 표기: em dash(긴 줄표) 금지, 범위는 물결(~), 문장은 다/요/까.

## 5-1. 제목 규율 (SEO + 궁금증) · 두 표면 한 규율

제목은 검색으로 발견되고 클릭으로 열려야 한다. RSS(팟캐스트 앱)와 유튜브(검색)는 표면이 달라 제목도 변형되지만, 규율은 하나다.

기획 루프는 `titlePlan` 을 필수 산출한다. 후보 3개 이상을 만들고, 채택 1개와 기각 이유를 남긴다.
`titlePlan.rssTitle` 은 `episode.yaml` 의 `title` 과 같아야 하고, `titlePlan.youtubeTitle` 은 `youtube.md` 제목의 초안이다.
`titlePlan.uploadSlugCamel` 은 `_uploads/NN{slug}.m4a` 와 `.jpg` 파일명에 쓰는 영문 camelCase 이름이다.

공통 규칙 (두 표면 모두):
- **고유명 앞으로**: 검색되는 고유명(회사명·티커·핵심 키워드)을 앞 15자 안에 둔다. 모바일 검색·팟캐스트 목록은 앞부분만 노출한다.
- **궁금증 갭**: 상식과 충돌하는 훅 또는 열린 질문("어떻게 ~했나", "~일까")으로 열되 답은 제목에 넣지 않는다. 다 말해버리면 클릭할 이유가 없다.
- **핵심 숫자 1개**: 분모·기간이 함의된 수치 하나로 구체화·신뢰를 준다(예: 영업이익률 58%).
- **금지**: 낚시(내용과 불일치), 목표가·확정전망·수익보장(`forbiddenAngles`), em dash. 구분자는 콜론 또는 전각바(ㅣ).

두 표면 변형:
- **RSS·에피소드 제목** (`episode.yaml` `title`, plan `title`): 궁금증 우선의 완결 문장. 팟캐스트 앱에서 읽히는 서사체. 예: `SK하이닉스: 다섯 번 죽을 뻔한 회사가 어떻게 AI 시대 이익률 58%를 찍었나`.
- **유튜브 SEO 제목** (`youtube.md` 제목): 같은 궁금증 + 검색 키워드·핵심 숫자를 앞으로 당기고 브랜드 태그를 꼬리에. 구조 = `[회사명] [반전 훅]ㅣ[키워드·핵심숫자], [열린 질문] [DartLab 기업분석]`. 60자 내외(검색 결과 잘림 대비). 예: `SK하이닉스 5번의 파산 위기 딛고 삼성을 넘다ㅣHBM·영업이익률 58%, 텐베거일까 [DartLab 기업분석]`.

`youtube.md` 설명은 앞 2줄이 검색 스니펫이라 훅+키워드를 먼저 쓴다. 태그는 회사명·코드·주가·분석·핵심 키워드를 넣는다. 상세 = GUIDE.md §5.

## 6. 플랫폼 제출 (최초 1회, 이후 자동)

발행하면 `feed.xml` 이 안정 URL 로 뜬다. castfeedvalidator.com 으로 검증 후 각 콘솔에 피드 URL 제출.
세 플랫폼 모두 소유권 인증은 `channel.yaml` 의 `ownerEmail` 로 온다.

- **YouTube Music**: YouTube Studio > 콘텐츠 > 팟캐스트 > RSS 피드 연결 > 피드 URL > 이메일 인증.
  YouTube 가 커버로 정지영상 비디오를 자동 생성. 이후 에피소드는 피드에 추가만 하면 자동.
- **Apple Podcasts**: podcastsconnect.apple.com > New Show > Add with RSS feed > 피드 URL > 이메일 인증.
- **Spotify**: creators.spotify.com > existing RSS feed > 피드 URL > 8자리 코드 인증. (MP3 enclosure 라 임포트됨.)

## 6-1. 수동 업로드 아카이브 (팟빵 등): `_uploads/`

RSS 자동 연결(YouTube Music·Apple·Spotify)과 별개로, 팟빵(Podbbang)처럼 사람이 오디오를 직접 올려야 하는 플랫폼이 있다. 이걸 위한 순서 아카이브가 `blog/_podcasts/_uploads/` 다. NotebookLM 오디오를 받으면 **항상 여기에 순번대로** 저장한다. 결과물을 저장하는 곳은 이 폴더 하나다.

- **git 비추적.** `_uploads/` 는 `.gitignore` 로 폴더째 제외한다(오디오 + 커버 이미지 모두). 발행 결과물이라 레포에 커밋하지 않는다.
- **영문 순번 파일명 (공백·기호 전면 금지).** `NN{slug}` 로 **붙여 쓴다**. `NN` 은 에피소드 순번(episodes `P0N` 과 일치), `slug` 는 그 에피소드 `topicSlug` 의 영문을 camelCase 로. **공백·하이픈(`-`)·밑줄(`_`) 등 기호 전부 금지, 한글 금지** (팟빵 등 사람 업로드 플랫폼 호환·정렬 안정). 예: `07netCashAboveMarketCap.m4a`, `09stealthRcsValueChain.jpg`.
- **오디오 + 16:9 커버 한 쌍.** 각 회차는 `NN{slug}.m4a` 와 `NN{slug}.jpg` 를 나란히 둔다. 팟빵 썸네일은 정사각이 아니라 **16:9 (1280x720)** 이라 에피소드의 `static-video.jpg` 를 커버로 재사용한다(에피소드 폴더가 아직 없으면 데이터리포트 배경으로 1280x720 생성). 정사각 `cover.jpg` 는 RSS/애플 자동경로 전용이므로 여기 쓰지 않는다.
- **발행 스크립트가 자동 생성.** `publish_podcast.py --episode ... --audio ...` 는 전사·R2·HF·feed/index 작업 뒤 `_uploads/NN{topicSlugCamel}.m4a` 와 `_uploads/NN{topicSlugCamel}.jpg` 를 복사하고 크기를 검증한다. 특별히 건너뛸 때만 `--no-uploads-archive` 를 쓴다.
- **다운로드 정리.** 아카이브 사본이 검증되면 다운로드 폴더 원본은 운영자가 정리한다. 스크립트는 사용자 다운로드 파일을 자동 삭제하지 않는다.

이렇게 두면 팟빵에 `01, 02, 03...` 순번대로 오디오 하나와 그 옆 16:9 이미지 하나를 그대로 올리기만 하면 된다.

## 7. 크로스 링크 (회사·주제로 카드/블로그/터미널 연결)

`index.json` 이 조인 레지스트리다. 조인 키는 `stockCode`(회사축)와 `topicSlug`(주제축). **주제 에피소드의 `topicSlug` 는 그 블로그 URL slug(= `links.blogSlug`)와 동일하게 맞춘다** (에피소드 자신의 `slug` 는 정체성, `topicSlug` 는 서피스 공유 조인 키라 별개). 계약 SSOT = Skill OS `operation.content` "서피스 x 콘텐츠 성격 매트릭스". 각 에피소드가
연결하는 카드 slug, 블로그 slug, 터미널 코드를 `episode.yaml` `links` 에 명시하고 index 에 실린다.
프론트(Phase 2)는 이 한 파일을 읽어 카드 모달, 블로그, 터미널 회사 화면에 "관련 팟캐스트"를 렌더하고,
RSS item link 는 회사 에피소드면 터미널 딥링크로 역방향 연결한다.

## 8. 커버, 정적 영상 이미지, 캡션

쇼 커버는 정사각 RGB, 3000x3000 로 정규화하고, RSS 검증 안정성을 위해 500KB 미만 JPEG 로 압축한다. 현재는 브랜드 워드마크 커버
(`assets/showCover.png`)를 쓴다. 더 정교한 커버가 필요하면 생성 이미지 정사각 소스로 교체 후 재발행한다.

에피소드 이미지는 세 필드를 분리한다.

- `image`: RSS item 용 정사각 커버. 발행 시 1400~3000 정사각 RGB JPEG, 500KB 미만으로 정규화한다.
- `staticImage`: 유튜브 정적 영상 이미지와 썸네일용 16:9 이미지. 발행 시 1280x720 RGB JPEG, 500KB 미만으로 정규화한다.
- `sourceAssets`: 재사용 가능한 원본 배경. 발행 시 `media/catalog.json`의 podcasts 컬렉션에 의미 키를 등록하고 HF `objects/sha256/`로 올린다. 회사 자산은 companies 컬렉션의 같은 객체를 재사용한다.

`thumbnail` 은 호환 필드다. `staticImage` 와 같은 파일이면 같은 source/key 를 지정한다. 프론트
`index.json` 에는 `imageUrl`, `staticImageUrl`, `thumbnailUrl`, `sourceAssets`, `caption` 이 함께 실린다.
RSS item 의 `itunes:image` 는 정사각 `image` 를 사용하고, 정적 영상 표면은 `staticImage` 를 사용한다.

에피소드별 실사 배경은 Openverse(`blog/_scripts/fetch_cc0_images.py`)나 `image_gen` 으로 수급한다. 생성형
이미지를 쓸 때는 레포 안 에피소드 폴더에 최종 소스를 저장해야 하며, 세션 기본 저장 경로에만 두지 않는다.

카드뉴스형 정적 이미지는 `_lib/render_episode_image.py` 로 만든다. 원본 배경을 흑백 cover 처리하고
어두운 스크림 위에 짧은 제목만 얹는다. 긴 설명, CTA, 해시태그는 이미지에 넣지 않고 `caption` 필드에 둔다.
캡션은 후크 한 줄, 맥락 2~3문장, CTA, 필요한 해시태그 순서로 쓴다. 투자 권유, 목표가, 수익 보장,
확정 전망은 `forbiddenAngles` 와 동일하게 금지한다.

## 9. Phase 2 (규모·안정성 필요 시)

r2.dev 공개 서브도메인은 완만한 rate limit 이 있다(니치 채널엔 충분). 커스텀 도메인이 필요해지면
Cloudflare zone 에 도메인을 붙여 R2 에 바인딩하고 `channel.yaml` 의 `baseUrl` 한 줄만 바꿔 재발행한다.
플랫폼에는 "change feed URL" 플로우로 이전한다.

## 참고 히스토리

- 2026-06-30 팟캐스트 트랙 폐기(자체 TTS 음성 품질 미달).
- 2026-07-02 부활. NotebookLM 소스 문서 파이프라인 + R2 발행 + RSS. 1편 발행(dartlab 2700 filings).
