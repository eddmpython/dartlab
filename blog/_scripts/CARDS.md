# 카드(캐러셀) 배포 — 운영 절차

/ cards 와 터미널 「카드뉴스」에 뜨는 인스타식 카드. 짧게 정리.

## 카드는 어디서 오나
- **손글 SSOT = 블로그 글 frontmatter 의 `carousel:` 블록.** (`blog/05-company-reports/{글}/index.md`)
- 화면은 hfMedia `carousels/index.json` **한 파일**을 읽어 그때그때 그린다(**안 굽는다**·디자인은 코드가 정함).
- 같은 회사 다른 주제 글이면 각자 `carousel:` → **자동으로 여러 편**(1:N).

> **정본은 /cards(이 파이프라인) 하나다.** 옛 `sns/carousels/`(hook.json→PNG·reel) 는 **유물**이다 —
> 운영자가 인스타그램에 *직접* 올릴 때만 수동으로 쓰고, 그것도 이제 **/cards 에 있는 걸 그대로 올리면 된다**.
> frontmatter ↔ hook.json **동기화는 하지 않는다**(sns 분기는 방치). 신규·개선은 전부 frontmatter 에서 한다.

## 카드 새로 올리기 — 5단계
1. 블로그 글 frontmatter 에 `carousel:` 쓴다 (아래 형식). **블로그 산문과 카드 기획은 한 번에 잡는다.**
2. 이미지·토론 계획 생성: `uv run python -X utf8 blog/_scripts/plan_card_news.py --post blog/05-company-reports/{글폴더} --write`
   - 계획 파일 = 같은 글 폴더의 `cards.plan.json`.
   - `planning.narrativeContract` 는 강행 규칙이다. 한 주제 안에서 **훅 → 왜 지금 중요한가 → 근거 → 전환 → 판단 질문**으로 이어져야 한다.
   - 슬라이드는 체크리스트가 아니다. 각 장은 앞장의 주장이나 숫자를 받아 다음 장으로 넘겨야 하며, "다음에는 이것을 본다"식 나열이면 발행 실패다.
   - `planning.plainLanguageContract` 도 강행 규칙이다. 전문용어·약어를 앞세우지 말고, 독자가 소리 내어 읽어도 자연스러운 한국어로 먼저 쓴다.
   - `imagePlan[]` 은 **5~10장**이어야 한다. 고정 템플릿이 아니라 카드 흐름에서 의미가 다른 장면만 기획한다.
   - 이미지는 그 글의 회사·사건·장소·시설·제품·운영 질문을 상징하는 **실제 사용용 장면**이어야 한다. 범용 금융 배경은 탈락.
   - 상호/회사명은 프롬프트와 검색 키워드에 써도 된다. 다만 생성형 이미지가 공식 로고·공식 문서·실제 내부시설을 사실처럼 꾸며내면 안 된다.
   - 각 항목의 `prompt` 를 GPT `image_gen` 으로 한 장씩 생성한다.
   - 생성 뒤 `imagegen.extractCommand` 로 `sns/assets/{code}/{assetKey}.webp` 에 저장하고 `imagegen.checkCommand` 로 프레이밍을 본다.
3. 작가 패널 토론·평가를 `cards.plan.json` 의 `reviewGate` 에 기록하고 `status: "passed"` 로 닫는다.
4. (선택) 검사: `uv run python -X utf8 blog/_scripts/audit_seo.py`  ← 형식·숫자 점검
5. 발행: `uv run python -X utf8 blog/_scripts/build_carousel_contracts.py`
   - hfMedia 에 `carousels/index.json` **한 파일** 올림(옛 파일 자동 삭제).
   - `/cards` 새로고침하면 뜬다. **사이트 재빌드 불필요**(데이터만 올림).
   - `--dry-run` 붙이면 *올릴 것·지울 것*만 미리 본다.

> `HF_TOKEN` 은 `.env` 에 있음(따로 입력 안 함).

## `carousel:` 형식 (예)
```yaml
carousel:
  title: "인스타 제목"
  caption: |
    설명 산문 첫 문단.

    둘째 문단.
  pinnedComment: "근거·면책 한 줄"
  keyMetrics:
    - label: "매출 (검증 기준일)"
      value: "10억달러"
    - label: "영업이익률 (기준)"
      value: "12%"
  explainers:
    - term: "낯선 용어"
      body: "처음 보는 독자가 캡션을 끊지 않고 이해할 수 있게 한두 문장으로 설명"
  relatedNews:
    - title: "관련 뉴스 제목"
      source: "naver-source.example"
      date: "2026-06-15"
      url: "https://example.com/news"
      track: "naver"
      description: "왜 이 링크가 카드 판단에 붙는지 한 줄"
  slides:
    - layout: editorial         # 표지
      line: "큰 글씨 한 줄"
      sub: "받침 문장"
      image: imagegen-xxx       # 이미지 '이름'만(hfMedia 에서 실제 파일 찾음)
    - layout: editorialStat     # 큰 숫자
      kicker: "라벨"
      bigNumber: "100"
      unit: "억개"
      context: "설명"
    - layout: editorialBeat     # 헤드라인 비트
      kicker: "라벨"
      line: "한 줄"
      sub: "받침"
```
- layout 은 **3종만**: `editorial`(표지) · `editorialStat`(큰 숫자) · `editorialBeat`(비트).
- 슬라이드 숫자는 본문에 있는 숫자만(없는 숫자 쓰면 audit 가 경고).
- `keyMetrics` 는 공식 발표·공시·검증표에서 확인한 핵심 지표만 넣는다. 자동 재무 번들에 결측이 있어도 공개 화면의 `핵심 지표` 카드가 빈 값으로 나가지 않게 하는 편집자 검증값이다.
- `explainers` 는 록빌·CDMO처럼 독자가 멈칫할 용어를 바로 풀어주는 짧은 설명이다.
- `relatedNews` 는 네이버 보관 뉴스(`track: naver`)나 공식 발표(`track: official`)를 연결한다. title/url 은 필수다.
- 카드 본문·캡션은 전문용어 약자를 앞세우지 않는다. `AI`, `ARR`, `EDR`, `SOC`, `FCF`, `CDMO`, `HBM`처럼 처음 보는 독자에게 막히는 약자는 슬라이드와 캡션에서 `인공지능`, `연간 반복 매출`, `단말 보안 대응`, `보안 관제`, `잉여현금흐름`, `위탁개발생산`, `고대역폭 메모리`처럼 풀어 쓴다. 원어가 필요하면 짧은 설명에 보조로만 둔다.
- 카드 말은 이어져야 한다. `line`, `sub`, `context` 는 독립 메모가 아니라 앞장과 다음 장 사이의 연결문이다. 제목을 잡았으면 첫 장의 질문, 중간의 근거, 마지막 판단 질문이 한 문단처럼 읽혀야 한다.
- `다음 질문`, `다음 체크포인트`, `체크포인트는` 같은 작업 지시형 문구는 쓰지 않는다. 독자에게 지시하지 말고 앞선 근거에서 자연스럽게 결론 문장으로 이어 쓴다.

## 화면(코드)도 바꿨을 때
- slides 텍스트만 바꿈 → 위 3단계로 끝(데이터만).
- 읽기측 코드/디자인을 바꿈 → **landing push 로 사이트 배포**(공개 화면이라 운영자 눈검수 후).

## 이미지
- 슬라이드는 이미지를 **이름**으로만 가리킴 → 실제 파일은 hfMedia `companies/{code}/` 에서 찾음.
- 이미지 마음에 안 들면 **계약 안 건드리고 hfMedia 이미지만 교체**하면 됨.
- 로컬 원본 = `sns/assets/{code}/{name}.webp` → `build_index.py` 인덱싱 → `publish_assets_hf.py` 가 hfMedia 업로드.
  파일명에 `card`/`thumbnail`/`og-` 토큰만 없으면 hero 로 자동 채택(별도 등록 불필요).
- **블로그 hero 공유 (SSOT)**: 블로그 회사 글 hero 사진은 `sns/scripts/ingest_blog_assets.py` 로 같은
  `sns/assets/{code}/` 공유풀에 합류한다 (블로그·카드 이미지 한 풀). 멱등·손작성 자산 보호 — 절차는 `blog/BLOG.md` "블로그 hero ↔ 카드 공유풀".

### 이미지 점검 — 쓰레기(평면 벡터·도식·인포그래픽) 먼저 잡기
생성형 hero 중 일부가 실사가 아니라 **평면 도식·막대그래프·텍스트 카드**로 나와 흑백 풀블리드 배경으로 깨진다.
발행 전·수시로 전수 스캔한다. 색복잡도(평면≈수십 색, 실사≈수천 색)로 의심을 잡고 **반드시 눈으로 한 장씩 확정**한다
(자동 판정 아님 — 야간 정유탑·검은 분말 같은 어두운 실사도 같이 잡힌다).
```
uv run python -X utf8 blog/_scripts/audit_carousel_images.py            # 색<600 또는 이름패턴 의심 목록
uv run python -X utf8 blog/_scripts/audit_carousel_images.py --max 250  # 평면 벡터/도식에 집중
```

### 이미지 가져오는 곳 — GPT image_gen 1차, CC0/PD 보강
> **카드 캐러셀 발간 규칙(강행)**: 랜딩 `/cards` 이미지는 블로그·카드 공동 기획의 `cards.plan.json`
> 에서 먼저 정한다. 기본 경로는 GPT `image_gen` 이고, 실제 장소·공공 사진이 더 적합한 경우만
> `fetch_cc0_images.py` 로 PD/CC0 스톡을 보강한다. FLUX 스크립트는 legacy/다른 용도다.

GPT image_gen 산출물은 `sns/assets/{code}/{assetKey}.webp` 공유자산으로 저장한다. 포스트 폴더에 직접
넣지 않는다. `cards.plan.json` 의 `imagegen.extractCommand` 가 이 저장 경로를 고정한다.

image_gen 프롬프트는 “그 회사/그 사건/그 장소/그 운영 질문”에 맞춘 상징 장면을 요구한다. 예를 들어
공장 램프업 글이면 막연한 금융 차트가 아니라 클린룸, 바이오리액터, 물류, 검수 서류, 고객사 미팅처럼
해당 글의 판단 축을 보이게 한다. 상호·회사명은 기획 맥락으로 써도 되지만, 생성형 이미지가 공식 로고,
공식 보도사진, 실제 내부시설 사진처럼 보이는 가짜 장면을 만들면 폐기한다.

기본 생성 절차:
```
uv run python -X utf8 blog/_scripts/plan_card_news.py --post blog/05-company-reports/{글폴더} --write
# imagePlan[].prompt 를 GPT image_gen 으로 5~10장 생성
# cards.plan.json 의 imagegen.extractCommand 실행
# cards.plan.json 의 imagegen.checkCommand 실행
uv run python -X utf8 sns/scripts/build_index.py
uv run python -X utf8 sns/scripts/publish_assets_hf.py
uv run python -X utf8 blog/_scripts/build_carousel_contracts.py
```

이슈 카드(`blog/_issues/{slug}/carousel.yaml`)는:
```
uv run python -X utf8 blog/_scripts/plan_card_news.py --issue {slug} --write
# imagePlan[].prompt 를 GPT image_gen 으로 5~10장 생성
# cards.plan.json 의 imagegen.extractCommand 실행
uv run python -X utf8 blog/_scripts/build_carousel_contracts.py
```
- 순수 매크로/제도 이슈는 `stockCode` 없이 둔다 → 손글 카드만 렌더.
- 특정 기업 관전 포인트 이슈는 `stockCode`와 `corpName`을 넣고, 공식 발표 기준 `keyMetrics` 를 함께 넣는다 → 블로그 CTA는 숨기지만 카드 뒤에 회사 report 기반 그래프·테이블이 붙고, 자동 지표 결측 때도 빈 핵심지표를 내보내지 않는다.

⛔ **핀터레스트·구글 이미지 금지** — 거기 올라온 사진은 대부분 **저작권 있음**(긁어온 것)이라 가져다 쓰면 침해다.
스톡 보강은 아래 무료 소스만 쓴다.
- **Wikimedia Commons / Openverse** — PD/CC0 (귀속 의무 0). `fetch_cc0_images.py` 가 이 둘에서만 받는다.
- 보강 여지(필요 시 API 키로 추가): **Unsplash·Pexels·Pixabay**(무료 라이선스·상업 OK), **NASA·각국 공공기관**(PD).

회사 카드 이미지가 모자라거나 부실하면 CC0 스톡으로 받아 `sns/assets/{code}/` 에 채운다.
받은 뒤 `build_index.py` → `publish_assets_hf.py` 로 올리고, 슬라이드에서 `image: <이름>` 으로 가리키면 끝(별도 배선 없음).

**스톡 (CC0/PD) — `fetch_cc0_images.py`**: Commons(실사 적중률 1순위) + Openverse 에서 PD/CC0 만 받아 `cc0-*.webp` 저장.
출처는 회사 폴더 `CREDITS.md` 에 자동 기록(의무 아니나 감사 추적).
```
uv run python -X utf8 blog/_scripts/fetch_cc0_images.py --jobs sns/assets/_plans/cc0FetchJobs.json
```
jobs = `[{"code","name","queries":[...],"keywords":[...]}]`. **반드시 받은 이미지를 눈으로 확인** —
스톡은 특정 피사체(정유탑·병입라인 등) 적중률이 들쭉날쭉해 오매치(엉뚱한 사진·텍스트 광고·도식)가 섞인다(실측: 받은 것 절반 폐기).
안 맞으면 **다른 검색어(`queries`)로 재시도**한다. 스톡으로 정확히 못 잡는 추상 장면은 `cards.plan.json`
의 image_gen 프롬프트로 되돌린다.

Openverse/Commons 검색도 범용 업종어만 넣지 않는다. `queries` 는 회사명·상호, 사건명, 시설/도시명,
제품/공정명을 앞쪽에 두고, `keywords` 는 그 글의 핵심 피사체가 제목/태그에 걸리도록 좁힌다. 회사명
직검색은 로고·인물·광고 오매치가 섞일 수 있으므로 관련 키워드와 눈검수로 걸러낸다.

> 원칙: **카드 캐러셀 이미지 = cards.plan.json 에서 먼저 기획한다.** image_gen 은 회사명·상호를
> 맥락 키워드로 쓸 수 있지만 가짜 공식 로고·가짜 공식 문서·식별 가능한 인물·읽을 수 있는 주장을 만들지 않는다.
> CC0/PD 스톡은 실제 공공 사진이 필요한 때의 보강 경로다.

## 발행 전 전문가 검토 게이트 — 작가 패널 토론·평가 (cards 정식 게이트)
**캐러셀은 공개물이라 발행 전에 전문가 루프를 반드시 거친다.** 자동 통과 금지.
이 루프는 옛 sns 의 `editorial_loop`(기획·작가·평가·재평가) 를 **cards 파이프라인으로 가져온 것**이다 — 신규·기존개선 모두 적용.
1. **작가 패널 토론(다중 에이전트)** — 서로 다른 렌즈(훅 강도·서사 스파인·앞장-다음장 연결·쉬운 말·디자인/이미지 적합성·정직성)로 독립 검토 후 약점 합의. 나열형 체크리스트와 전문용어 남발은 통과시키지 않는다.
2. **정직성·근거 평가** — 슬라이드 숫자가 전부 `## 검증표`에 있는가, 외부/실측이 분리·표기됐나, 과장·투자권유 표현 없나.
3. **이미지 적합성 평가** — 색복잡도 감사 통과 + 주제 적합 + 눈검수 완료(쓰레기·텍스트·도식 0).
4. **재평가** — 합의된 수정 반영 후 같은 패널이 다시 본다. 기준 미달이면 발행 보류·재수정.
   (점수는 실가치 proxy 가 아니라 게이트 — 미빌드 점수 인플레 금지.)

> 흐름: 신규·개선편은 위 패널(다중 에이전트 토론·평가→수정→재평가)을 거친 뒤에만 `build_carousel_contracts.py` 발행.
> **이미 발행된 편도 이 루프로 개선한다**(발행본 품질 상향이 기본 운영).
> `cards.plan.json` 이 있는 글은 `planning.narrativeContract`, `planning.plainLanguageContract`, `reviewGate.status: "passed"` 와 각 required round `status: "passed"` 가
> 아니면 `build_carousel_contracts.py` 가 발행을 중단한다. legacy 글은 plan 파일이 없으면 허용하되, 신규·개선은 plan 을 만든다.
> 발행 게이트는 실제 카드 문장도 검사한다. `AI`, `CDMO`, `HBM` 같은 약어와 `다음 질문`류 문구가 남아 있으면 발행을 중단한다.

## 도구
| 파일 | 역할 |
|---|---|
| `blog/_scripts/build_carousel_contracts.py` | **발행** — blog frontmatter → hfMedia 단일 파일 |
| `blog/_scripts/plan_card_news.py` | **블로그+카드+image_gen 기획** — `cards.plan.json` 생성·검사 |
| `blog/_scripts/audit_carousel_images.py` | **이미지 감사** — 평면 벡터·도식·인포그래픽(쓰레기) 색복잡도로 탐지 |
| `blog/_scripts/fetch_cc0_images.py` | 무료(PD/CC0) 이미지 수급 — Commons·Openverse |
| `sns/scripts/extractImagegenAssets.py` | GPT `image_gen` 세션 결과 → `sns/assets/{code}/{asset}.webp` 추출 |
| `sns/scripts/checkImagegenAssets.py` | image_gen 산출물 4:5·밝기·프레이밍 1차 검사 |
| `sns/scripts/ingest_blog_assets.py` | **블로그 hero ↔ 카드 공유풀 SSOT** — 블로그 회사글 hero → `sns/assets/{code}/`(멱등·손작성 보호) |
| `blog/_scripts/gen_company_flux.py` | legacy 생성형 hero(4:5) — 신규 `/cards` 기본 경로 아님 |
| `blog/_scripts/audit_seo.py` | carousel 형식·숫자 검사 |
| `blog/_scripts/migrate_carousels_to_blog.py` | 1회성 이관(sns/carousels → blog frontmatter, **완료**). 이후 sns 는 **유물**·재동기화 안 함 |
| `blog/_scripts/test_carousel_contracts.py` | 발행/이관 테스트 |

설계 SSOT: `mainPlan/blog-carousel-ssot/01-unified-slug-ssot.md`
