# 콘텐츠 자산 SSOT 구조

> 상태: 2026-07-17 기준 적용 완료. 이 문서는 새 저장 구조 제안이 아니라 현재 운영 계약을 설명한다.

## 1. 정본은 세 층뿐이다

| 층 | 정본 | 책임 |
|---|---|---|
| 저작 | 기존 `blog/**` 글, 기획, 출처 문서 | 사람이 고치는 이야기와 의미 계약 |
| 자산 카탈로그 | Git `media/catalog.json` | source, 의미 키, 역할, SHA-256, 포스트 매핑 |
| 미디어 | HF `objects/sha256/<앞2자>/<전체해시>.<확장자>` | 모든 SVG/WebP/JPG/PNG의 durable 원본과 서빙본 |

새 `content/stories/`, 포스트별 자산 manifest, 회사별 HF 바이너리 폴더를 추가하지 않는다. StoryCore는 공동 기획 어휘일 뿐 새 물리 파일이 아니다. 현재 글, 카드, 팟캐스트 저작 위치를 유지하면서 자산만 중앙 카탈로그와 콘텐츠 주소 객체로 모은다.

## 2. HF 허용 구조

```text
.gitattributes
objects/
  sha256/
    <앞2자>/
      <전체해시>.<확장자>
manifests/
  companies.json
  carousels.json
```

- 바이너리는 `objects/sha256/` 밖에 둘 수 없다.
- `manifests/companies.json`은 회사 의미 키를 객체 경로로 연결하는 런타임 뷰다.
- `manifests/carousels.json`은 모든 카드 계약을 담는 런타임 뷰다. 각 `slides[].image`와 `ogImage`는 객체 경로다.
- 두 manifest는 파생물이다. 재생성 기준은 Git `media/catalog.json`과 기존 저작 원본이다.
- 회사, 이슈, 기술, 팟캐스트별 HF 폴더를 만들지 않는다.

## 3. 경로별 책임

| 콘텐츠 | 저작 입력 | 발행 결과 |
|---|---|---|
| 블로그 | `index.md`, `brief.json`, `assets/CREDITS.md`, 로컬 `assets/` staging | 본문과 OG가 HF 객체 URL을 참조 |
| 회사 카드 | 글 frontmatter `carousel:` + `cards.plan.json` | `manifests/carousels.json` + 객체 |
| 이슈 카드 | `blog/_issues/<slug>/carousel.yaml` + 로컬 assets | `manifests/carousels.json` + 객체 |
| 회사 이미지 | `sns/assets/<subjectKey>` 로컬 staging | `manifests/companies.json` + 객체 |
| 팟캐스트 원본 이미지 | `episode.yaml sourceAssets` + 로컬 assets | 중앙 catalog + 객체 |
| 팟캐스트 오디오와 공개 커버 | episode 저작 원본 | R2 `dartlab-podcast` |

## 4. 발행 불변식

1. 같은 바이트는 SHA-256 하나로 한 번만 저장한다.
2. 로컬 SVG/WebP/JPG/PNG staging은 Git에 넣지 않는다.
3. 의미 키는 경로가 아니다. 발행기가 중앙 catalog에서 객체 경로로 해석한다.
4. 런타임 소비자는 `manifests/*.json`과 `objects/sha256/`만 읽는다.
5. 발행기는 `companies/`, `issues/`, `tech-story/`, `podcasts/`, `carousels/`를 만들 수 없다.
6. 깨끗한 체크아웃의 블로그 staging 복원은 `seedBlogMedia.py`만 담당한다.
7. 자산 교체는 새 객체를 추가하고 catalog 별칭을 바꾼다. 기존 객체를 덮어쓰지 않는다.

## 5. 안전한 전환 순서

1. 새 객체와 새 manifest를 먼저 올린다.
2. landing과 cardShare 소비자를 `manifests/`로 전환한다.
3. 배포본이 새 manifest를 읽는지 확인한다.
4. `consolidateHfMedia.py --apply --delete-legacy`로 옛 HF 폴더를 지운다.
5. HF 최상위가 `.gitattributes`, `objects`, `manifests`만 남았는지 검사한다.

삭제를 소비자 배포보다 먼저 하면 현재 공개 화면이 끊긴다. 이 순서는 구조적 안전장치이며 옛 폴더를 장기 호환 계층으로 인정한다는 뜻이 아니다.

## 6. 완료 기준

- Git 추적 블로그 SVG·래스터 0건.
- `media/catalog.json`의 모든 객체가 정규 콘텐츠 주소 경로를 가진다.
- 회사와 캐러셀 manifest의 모든 이미지가 실제 HF 객체를 가리킨다.
- 저장소와 운영 문서에 옛 HF 소비 경로가 없다. 이관 도구의 입력 경로와 회귀 테스트 fixture만 예외다.
- landing, cardShare, 블로그 발행, 회사 자산 발행, 카드 발행, 팟캐스트 원본 발행이 같은 계약을 쓴다.

## 7. 콘텐츠 품질과의 경계

저장 구조는 글의 질을 대신하지 않는다. 블로그 기획은 `brief.json.imagePlan[]`, 카드 기획은 `cards.plan.json`, 출처는 `assets/CREDITS.md`가 담당한다. 이미지 수급은 사실 적합성에 따라 공식 및 라이선스 실사와 `image_gen` 중 자율 선택한다. 심층 글의 마지막은 요약표가 아니라 조건, 변화 경로, 결과, 확인 지표, 반증 조건을 갖춘 시나리오형 관전 포인트로 닫는다.
