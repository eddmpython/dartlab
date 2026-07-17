# 카드·블로그 지식망 PRD — 진입점·회사 간 카드망·지식화

> **관계**: 본 PRD 는 [content-asset-ssot](../content-asset-ssot/00-prd.md)(저장·발행 SSOT = story 단위)
> **위에 얹는 연결·소비 레이어**다. content-asset-ssot 가 "어디에 저장·발행하나"라면, 본 문서는
> "쌓인 카드·블로그를 어떻게 **서로 잇고 터미널 종목검토로 들여보내고 지식으로 쓰나**"를 설계한다.
> 데이터 백본은 이미 존재 — `CarouselContract.code`·`relatedNews[]`·`corpName`, 공유 소비 SSOT `PostModal.svelte`.

## 1. 문제 / 동기

카드뉴스·블로그가 쌓이면 단순 콘텐츠가 아니라 **분석 진입점·회사 간 지식망**이 될 수 있는데 지금은 끊겨 있다.

- 카드(`PostModal`)에는 "블로그 이어 읽기"·관련 뉴스(외부)만 있고 **터미널 종목검토로 들어가는 길이 없다**.
- 카드 본문이 다른 회사를 언급해도 **그 회사 카드/리포트로 점프할 망이 없다** — 카드끼리 섬이다.
- 블로그 글 결론은 `backfill_blog_insights.py` 로 KnowledgeDB 에 들어가 AI 인용되지만, **카드(요약·결론)는 지식화 안 됨**.

## 2. 목표

1. **진입점화** — 카드 → 해당 종목의 터미널 종목검토(전문 분석 계기판)로 한 번에 진입.
2. **회사 간 카드망** — 카드가 언급한 다른 회사를 그 회사 카드/리포트로 점프하는 망.
3. **지식화** — 카드 결론도 KnowledgeDB 에 들어가 블로그와 함께 AI retrieve 인용 자산이 됨.
4. 데이터·소비 SSOT 불가침 - `manifests/carousels.json` 단일 파일, 공유 `PostModal` 한 곳만 늘린다(분기 신설 금지).

## 3. 비목표

- 새 그래프 DB·별도 인덱스 파일 신설 금지(KnowledgeDB와 `manifests/carousels.json` 재사용).
- 카드 산문/디자인 갈아엎기 금지 — 연결 요소만 얹는다.
- 자동 회사 추출(NER) 금지 1차 — 회사망 엣지는 **손글 큐레이션**(frontmatter)로 시작(정직·오매치 0).

## 4. 설계 (5 비전 → 빌드 매핑)

### ① 카드 → 터미널 종목검토 진입 CTA
- **소비**: `landing/src/lib/cards/PostModal.svelte` 에 `!standalone && code` 일 때
  "터미널에서 종목 검토" CTA 추가(기존 "블로그 이어 읽기" CTA 아래, 같은 `--dl-accent` 배선).
  `/cards`·`/terminal 카드뉴스` 가 같은 `PostModal` 을 쓰므로 **한 번 추가로 양쪽 동시 적용**.
- **라우트**: 터미널 종목 진입 규약 확인 필요 — `landing/src/routes/terminal/+page.svelte` 의
  `createEngine`/`TerminalSurface` 종목 로드 API + `goto`. 빌드 시 `?code={code}` 진입 또는
  터미널 회사 전환 API 로 연결(현 PostModal 은 `code` 보유).
- **데이터**: 신설 0 — `CarouselContract.code` 이미 존재.

### ② 카드뉴스 = 진입점 (흐름)
- `/cards` 피드 → 카드 열람 → ①CTA 로 종목 터미널/`/report` 진입. 모바일은 `/report`(터미널 대체) 경로.
- 터미널 회사 네비「카드뉴스」(이미 `PostModal` 공유) → 같은 CTA 로 그 종목 계기판 복귀. 순환 진입.

### ③ 회사 간 카드망 (relatedCompanies)
- **신규 필드**: frontmatter `carousel:` 에 `relatedCompanies: [{code, name, reason}]`(손글 큐레이션).
- **타입**: `landing/src/lib/cards/model.ts`·`contract.ts` 에
  `CarouselContract.relatedCompanies?: {code:string; name:string; reason:string}[]` (camelCase).
- **빌드**: `blog/_scripts/build_carousel_contracts.py::_relatedCompanies(fm)` — `_related_news`(기존 `_relatedNews` 헬퍼) 동형 패턴.
- **검증**: `blog/_scripts/cards_plan.py::validate_contract_plan_gate` + `blog/_scripts/audit_seo.py` —
  `code` 6자리·중복 자기참조 금지·`reason` 필수.
- **소비**: `PostModal.svelte` 에 `relatedCompanies` chips → 클릭 시 그 회사 카드(같은 code 의 첫 slug) 또는
  터미널 진입. `manifests/carousels.json` 한 파일 안에 이미 전 카드가 있어 **추가 fetch 0**(클라 lookup).

### ④ 블로그 + 카드 지식화
- **확장**: `blog/_scripts/backfill_blog_insights.py` — 카드 계약(`title`·`caption`·`pinnedComment`·cover `conclusion`)
  → `dartlab.knowledge.insights(source="cards")` 백필. 블로그(`source="blog"`)와 동일 retrieve 경로.
- 카드는 짧은 결론체라 insight 1~2개/카드. no-new-number 게이트 통과분만(이미 audit_seo 검증).

### ⑤ 이미지 SSOT (토대 — 트랙 A 에서 1차 표준화 완료)
- 의미·해시 정본은 Git `media/catalog.json`, durable 바이너리는 HF `objects/sha256/`다. 카드와 블로그는 같은 객체를 재사용한다.
- `sns/assets/{code}/`는 로컬 staging/cache일 뿐 정본이 아니다. `ingest_blog_assets.py`는 이관 전 레거시 글에만 쓰고 신규 v2 글에는 사용하지 않는다.

## 5. 단계 (ROI 순)

- **P0 (저비용·고가치)**: ① 카드→터미널 CTA. 데이터 신설 0, PostModal 한 곳. 터미널 라우트 규약만 확인.
- **P1**: ③ relatedCompanies — 필드→빌드→검증→chips. 손글 큐레이션으로 1~2편 시범.
- **P2**: ④ 카드 지식화 — backfill 확장 + retrieve 인용 확인.
- (②는 ①·③의 자연 산물 — 별도 빌드 최소.)

## 6. 검증 게이트

- ③: `audit_seo.py` relatedCompanies 스키마(code 6자리·reason 필수) + `contract.test.ts` 동행(변경 단위 룰).
- ①③ UI: **푸시 게이트** — `/cards`·`/terminal` 양쪽 스크린샷 운영자 눈검수 후에만 push(UI 시각 회귀 가드).
- ④: backfill `--dry-run` diff → `--confirm` 쓰기 → AI retrieve 에서 카드 결론 인용되는지 실측.

## 7. 판단

데이터 백본(`code`·공유 `PostModal`)이 이미 있어 **①은 거의 CTA 한 줄**, ③은 손글 필드+chips 로 저비용.
NER 자동추출 대신 손글 큐레이션으로 시작해 오매치 0·정직 유지. 저장 SSOT(story manifest)는 content-asset-ssot 가
키우고, 본 PRD는 그 위 **연결망**만 얹는다. "굽지 않고 manifests/carousels.json과 KnowledgeDB 재사용" 원칙을 준수한다.
UI 빌드는 푸시 게이트라 운영자 승인 후 한 편씩 완성한다.

## 8. 카드 필터·크로스검색 (scan식 — 데이터 토대 착수, UI 향후)

운영자 2026-06-28: 카드뉴스 전체를 scan 처럼 **크로스로 금방 찾아지게**. 필터 축을 카드 데이터에 박아둔다.

**필터 축 (`CarouselContract` 필드)**
- `code`(종목코드) · `name`(회사명) · `sector` — 이미 존재.
- **`cardType`** — `company`(기업이야기) | `event`(기업 이벤트) | `economy`(경제이야기). 2026-06-28 데이터 토대 착수:
  `build_carousel_contracts.py` 가 company-reports→`company`, `_issues`→yaml `type:`(기본: code 있으면 `event`·없으면 `economy`) 로 emit.
  build가 `manifests/carousels.json`에 emit한다. `model.ts` 인터페이스 타입은 필터 UI 빌드 때 반영한다. 3 이슈 카드(`samsung-biologics`=event·`buyback`=event·`korea-macro`=economy)에 type을 기록한다.
- **popularity(인기순 슬라이딩)** — 자주 찾고 자주 열어본 카드. 현재 view 데이터 없음 → 향후 조회/오픈 카운트 적재 후 `popularity` 필드. 데이터 생기기 전 보류(날조 금지).

**소비 (UI·향후·푸시 게이트)**: `/cards` 피드에 필터 chip(타입·섹터) + 검색(code/name) + 정렬(date/popularity). `manifests/carousels.json` 단일 파일이라 클라이언트 필터에 추가 fetch가 없다.

**백필 정합**: 카드 근거 백필([[project_card_evidence_backfill]]) 시 code/name/cardType 정확히 박혔는지 함께 점검 → 필터 준비.
