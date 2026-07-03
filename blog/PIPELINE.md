# 콘텐츠 파이프라인 SSOT: 블로그 + 카드뉴스

> **한 장으로 보는 전 과정.** 상세 how-to 는 각 단계의 `→` 링크가 정본(여기선 중복 안 씀).
> 블로그 상세 = [BLOG.md](BLOG.md) · 카드 상세 = [_scripts/CARDS.md](_scripts/CARDS.md) ·
> 작가 편집 게이트 = [_reference/BLOG_MASTER_WRITER.md](_reference/BLOG_MASTER_WRITER.md) ·
> 스크립트 인덱스 = [_scripts/README.md](_scripts/README.md) (자산 공유 `sns/scripts` 배선 포함) · SNS 트랙 = [../sns/README.md](../sns/README.md).
> 메모리는 **인덱스·진행상태만**. 운영 절차(루프·게이트·프로토콜)는 이 문서가 정본.

## 0. 덕지덕지 방지 (전 단계 공통)
- 추가 전 self-check: "이미 있나? 깎을 수 있나?" 강함은 쌓아서가 아니라 깎아서.
- 새 패널·키워드규칙 더미·특수케이스·새 파일 누적 = 신호. 의심되면 안 붙인다.
- 데이터는 런타임 SSOT 직독, **굽지 않음**. 새 산출물·사본·별도 인덱스 신설 금지.

## 1. 주제: 발굴 → 선정
- **발굴**: dartlab 5 엔진(`scan` · `analysis` 14축 · `quant` · `governance`)을 직접 돌려 "이상·의외·모순"을 찾는다. 사람이 아는 이야기가 아니라 **데이터가 말하는 이야기**. + SEO 경쟁분석(네이버 상위 H2 갭).
- **선정**: "숫자가 상식과 다른 이유 / 서사가 재무제표에서 미확인된 지점 / 급변한 한 줄 / 틀리면 바로 깨지는 조건" 중 1 개. 제목 없이 첫 질문만으로 읽고 싶어야 한다.
- 후보·진행 = 워크리스트(메모리 인덱스, 세션 간 claim 충돌 방지). 착수 전 글롭 중복확인.
- → BLOG.md §Phase 0

## 2. 기획: 전문 에이전트 적대 토론 (+ 평가·개선 루프)
- 병렬 4 에이전트(마찰 0)는 클리셰를 통과시킨다 → **적대 토론**으로: 재무분석가 vs 산업·역사가(서로 다른 관통선 경합) → 회의론자(둘 다 "템플릿 클리셰"로 격파) + 독자대리인(재미) → **단일 관통선 + 정직성 가드**로 수렴.
- 산출: 독자질문 1 + 막 구조표 + 막별 테이블 + 제목/description 후보.
- 평가·개선 루프: 막을 나열한 뒤 "이 막을 빼면 더 궁금해지나?" 안 약해지면 삭제·흡수.
- ⚠ **Workflow 팬아웃 시**: craft·관통선은 신뢰하되 **모든 수치·인과는 메인 스레드 dartlab 재검증**(에이전트 산출 환각 다수). dartlab 검증 = 메인 순차(OOM 가드, 회사 동시 import ≤ 2), 토론·WebSearch만 워크플로(에이전트 dartlab 호출 금지).
- → BLOG.md §Phase 1

## 3. 블로그 작가 루프
- **집필**: 막별 재무분석가(데이터+해석) → 스토리작가(장면+리듬). 매 막 "왜?"로 시작, 끝에 다음 막으로의 인과 다리 1 문장.
- **편집 게이트(마스터라이터)**: 첫 2 문단 재작성 · 모든 H2 검사(궁금증 심화·메커니즘·리스크 반전·판단 닫힘) · 막을 `장면→숫자→반전→판단`으로 · 보고서톤/제작어 제거 · "틀리는 조건" 3~5 개. → _reference/BLOG_MASTER_WRITER.md
- 막 개수 = 6 막 기본·고정 아님(한 막 3,500 자↑ 분할, 질문 흐려지면 합침).

## 4. 블로그 평가 루프 (품질 게이트)
- **독자 에이전트** 6 항목: 재미 · 집중 끊긴 곳 · 독자질문 생존 · "어?" 횟수 · 기억 문장 · 점수.
- **적대검증**: 본문 강한 수치 전부 메인 dartlab 재계산(NPM 행 누락 · 연도 귀속 · 배율 오류 사례 다수). 검증표에 없는 숫자 = 발행 차단.
- **정직성 가드**: 영업이익 vs 순이익 분리 · 분기/연간 라벨 명시 · 일회성 분리 · 매핑 artifact 무시 · 연결 vs 그룹 실체 구분.
- 게이트: `audit_seo.py` SEO ≥ 95(품질로만. 길이·섹션 패딩 금지, 점수는 부산물).
- **깊이 게이트(회사 심층 리포트 한정)**: 측정은 **본문 기준**(표·SVG·코드 제외한 읽는 글자수. audit_seo·auditBlog 공통). 하한 **14,000자** 미만이면 `auditBlog.py` 가 "얕음(shallow deep report)"로 리라이트 후보 표시. 심층 완성 목표 **20,000자 이상**(현재 상위 3%만 도달, 최고작 티어), 장기 야심은 4만자. 길이는 막·증거·시나리오의 산물이지 패딩이 아니다(반복도 가드와 짝, 표 복붙·문장 늘리기 차단). 교육·소식·신용 카테고리는 구조상 단문이라 제외.
- → BLOG.md §Phase 4

## 5. 카드뉴스 루프
- **3 종 구분**: ① 회사 카드(블로그 글 frontmatter `carousel:`, code 있음) ② 에디토리얼(인스타 톤, Hook Engine 후킹 채점) ③ 이슈 카드(standalone, `blog/_issues/{slug}`, 블로그 글 없음).
- **기획**: `plan_card_news.py` → `cards.plan.json`(imagePlan 5~10, reviewGate).
- **작가 패널 게이트(공개물 필수, 자동통과 금지)**: 훅 강도·서사 스파인·디자인/이미지 적합성·정직성 독립 검토 → 합의 수정 → 같은 패널 재평가. `reviewGate.status="passed"` + 라운드 passed 전 `build_carousel_contracts.py` 발행 차단.
- → _scripts/CARDS.md (카드 파이프라인 상세 SSOT)

## 6. 이미지: 생성 / 수급 / 평가·개선
- **기획**: 그 회사·사건·장소·제품을 상징하는 **실제 사용용 장면**(범용 금융 배경 탈락). 카드는 `plan_card_news.py` imagePlan, 블로그는 본문 hero 프롬프트.
- **두 경로**:
  - **GPT = 자체 `image_gen`** (1차). Codex 세션 JSONL → `sns/scripts/extractImagegenAssets.py` → webp. 가짜 공식 로고·공식 문서·식별 인물 금지.
  - **Claude = Openverse·Commons CC0 수급**. 실제 공공 사진이 더 맞는 경우. `fetch_cc0_images.py`(블로그 `gen_blog_cc0.py` · 뉴스 `gen_news_cc0.py`). ⛔ 핀터레스트·구글 이미지 금지(저작권).
  - **FLUX(Replicate)** = legacy 보조(image_gen 실패·운영자 요청 시만). 잔액 소진 시 프롬프트 적치 후 일괄.
- **평가·개선**: 색복잡도 감사(`audit_carousel_images.py`, 평면 도식·텍스트카드 탐지) + **반드시 눈검수**(자동판정 아님). 회사 특정성·시그니처 ≥ 1. 안 맞으면 다른 검색어 재시도 또는 image_gen 복귀.
- **공유풀(SSOT)**: `sns/assets/{code}/` → `build_index.py` → `publish_assets_hf.py` → HF. 블로그 hero 도 `ingest_blog_assets.py`로 같은 풀에 합류(멱등·손작성 보호).

## 7. 발행
- **블로그**: `ai:` 블록 · 검증표 · SEO ≥ 95 · 빌드 확인 → 커밋. 재무는 `<CompanyFinancials code="…" />` 라이브 태그(빌드타임 데이터 SSOT 직독). → BLOG.md §Phase 5
- **카드**: `build_carousel_contracts.py` → hfMedia `carousels/index.json` 단일 파일(안 굽고 in-place 갱신). 데이터만 올림 → 사이트 재빌드 불필요.
- **자산**: `build_index.py` → `publish_assets_hf.py` → HF `dartlab-media`.
- **발행 후**: 월 SEO 스코어링 · 내부링크 맵 · KnowledgeDB `insights` 백필(블로그=`backfill_blog_insights.py`, 카드=향후 `source="cards"`).

---
정본 위치: 블로그 단계 상세 [BLOG.md](BLOG.md) · 카드 [_scripts/CARDS.md](_scripts/CARDS.md) · 작가 게이트 [_reference/BLOG_MASTER_WRITER.md](_reference/BLOG_MASTER_WRITER.md) · 스크립트 [_scripts/README.md](_scripts/README.md).
