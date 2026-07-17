# 콘텐츠 파이프라인 SSOT: 블로그 + 카드뉴스

> **한 장으로 보는 전 과정.** 상세 how-to 는 각 단계의 `→` 링크가 정본(여기선 중복 안 씀).
> 블로그 상세 = [BLOG.md](BLOG.md) · 카드 상세 = [_scripts/CARDS.md](_scripts/CARDS.md) ·
> dartlab 이야기(교육 연재 -> 브라우저 실행 셀) 파생 파이프라인 = [03-dartlab-stories/PIPELINE.md](03-dartlab-stories/PIPELINE.md) ·
> 기업이야기 파생 파이프라인 = [05-company-reports/PIPELINE.md](05-company-reports/PIPELINE.md) ·
> 데이터 리포트(전상장사 전수) 파생 파이프라인 = [06-data-reports/PIPELINE.md](06-data-reports/PIPELINE.md) ·
> 기술이야기(기술 원리 -> 재무 착지) 파생 파이프라인 = [08-tech-story/PIPELINE.md](08-tech-story/PIPELINE.md) ·
> 투자이야기(시장 언어 -> 판단 프레임) 파생 파이프라인 = [09-investment-stories/PIPELINE.md](09-investment-stories/PIPELINE.md) ·
> 작가 편집 게이트 = [_reference/BLOG_MASTER_WRITER.md](_reference/BLOG_MASTER_WRITER.md) ·
> 스크립트 인덱스 = [_scripts/README.md](_scripts/README.md) (자산 공유 `sns/scripts` 배선 포함) · SNS 트랙 = [../sns/README.md](../sns/README.md).
> 메모리는 **인덱스·진행상태만**. 운영 절차(루프·게이트·프로토콜)는 이 문서가 정본.
> **공동 작업대 설계 정본 = Skill OS `operation.content`** (세 서피스 공유 front -> StoryCore -> 서피스 어댑터, evidence 표준, 데이터 워크벤치=데이터 SSOT). 본 문서는 블로그·카드 **운영 런시트**.

## 0. 덕지덕지 방지 (전 단계 공통)
- 추가 전 self-check: "이미 있나? 깎을 수 있나?" 강함은 쌓아서가 아니라 깎아서.
- 새 패널·키워드규칙 더미·특수케이스·새 파일 누적 = 신호. 의심되면 안 붙인다.
- 데이터는 런타임 SSOT 직독, **굽지 않음**. 새 산출물·사본·별도 인덱스 신설 금지.

## 0.5 블로그 전체 카테고리 공통 계약

- **내러티브 집중**: 9개 카테고리 모두 독자 질문 하나를 처음부터 끝까지 붙든다. 각 섹션은 앞의 답에서 다음 궁금증을 만들고, 빼도 관통선이 약해지지 않는 섹션은 삭제한다. 정보 목록, 보고서 목차, 체크리스트 나열로 본문을 대신하면 실패다.
- **쉬운 설명**: 9개 카테고리 모두 처음 온 비전문가를 기준으로 쓴다. 어려운 개념은 첫 등장 문장에서 일상어로 풀고 실제 숫자, 회사, 공시 문장, 표, 차트, 제품, 기간, 계정 중 하나를 바로 붙인다. 쉬운 말은 내용을 줄이는 일이 아니라 인과를 따라가게 만드는 일이다.
- **장르 델타의 한계**: 아래 장르별 규칙과 파생 `PIPELINE.md`는 주어, 근거, 분량, 시각물만 바꿀 수 있다. 내러티브 집중과 쉬운 설명은 어떤 장르도 덮어쓸 수 없는 공통 계약이다.

- **기술이야기**: 기술이 주인공이다. 원리·공정 병목·세대 변화·대표 회사 위치를 먼저 파고, DART·EDGAR 공시와 dartlab 실측으로 그 기술이 기업 숫자에 남기는 흔적을 붙인다. 돈 이야기만 앞세우면 실패다.
- **데이터 리포트**: `scan`과 전종목 파서를 써서 DART·EDGAR 전체 시장의 특이점을 찾는다. 개별 회사는 대표 사례일 뿐이고, 핵심은 전체 시장에서 무엇이 비정상적으로 튀는지다.
- **기업이야기**: 한 회사의 내러티브를 깊게 판다. 사업 구조, 공시 문장, 수주·제품·자본배치·현금흐름을 한 회사 안에서 끝까지 연결한다.
- **투자이야기**: 투자자가 시장을 읽을 때 쓰는 언어와 프레임이 주인공이다. 주가·경제·증권사 표현·투자 용어·기술적투자 보조지표·기술투자 관점을 설명하고, 회사·공시·기술 글은 사례와 참고글로 연결한다. 매수·매도·목표가 결론으로 닫으면 실패다.
- **깊이의 공통 기준**: 쉬운 말은 얕은 말이 아니다. 용어는 풀어 쓰되, 원리·분모·기간·공시 위치·사업 메커니즘·반례까지 설명해 독자가 "아, 그래서 다음에는 이것을 보면 되겠구나"까지 도달해야 한다.
- **마지막 관전 시나리오 게이트**: 심층 글의 마지막 H2는 요약이 아니라 "만약 어떤 조건이면, 어떤 경로로 무엇이 달라질까"를 2~4개로 푼다. 각 시나리오는 `condition`, `mechanism`, `outcome`, `watchMetric`, `invalidatedBy`, `evidenceRefs`를 가진다. 낙관·기본·비관 이름만 바꾼 표나 감상, 순위, 주가 반응으로 끝나면 재작성한다.
- **초보자 서사 게이트**: 모든 공개 글은 전문가가 아니라 처음 온 독자를 기준으로 쓴다. 글은 `기: 왜 이 글을 읽어야 하나`, `승: 숫자·표·공시·차트에서 첫 결과를 본다`, `전: 그 결과를 잘못 읽기 쉬운 오해와 한계`, `결: 다음에 볼 기준·지표·공시 질문` 순서로 닫힌다. 이 순서가 없으면 발행 실패다.
- **전문가 말투 차단**: OPM, EBITDA, CAPEX, FCF, ROE, PER, PBR, 밸류에이션, 컨센서스, 레버리지 같은 말은 첫 등장 문장에서 한국어로 풀고 바로 옆에 숫자·표·공시 위치를 붙인다. "구조", "흐름", "맥락", "시사점", "메커니즘", "핵심", "프레임" 같은 말만으로 설명을 끝내면 재작성한다.
- **공통 파이프라인**: 기획이 글과 이미지를 동시에 결정한다. 신규 심층 글의 `brief.json`은 `contractVersion: 2`이며 관통선, 핵심 인싸이트, `watchScenarios[]`, `sections[]`, evidenceMap, DART/EDGAR·dartlab·price·macro·internal-blog 근거, 보여줄 표·차트·`imagePlan[]`, 참고글 연결 계획, 오독 방지 조건을 함께 가진다. 기존 글은 수정 전까지 레거시 호환으로 감사한다.
- **섹션 독해 구조 계약**: 각 주요 H2는 `타이틀 -> 한 줄 서브타이틀/훅 -> 이미지·표·도식·코드 출력 같은 시각 앵커 -> 설명적 서술 -> 실제 예시 -> 보완 설명·오해 방지 -> 다음 섹션 연결문` 순서로 기획한다. `brief.json.sections[]` 는 `heading`, `subtitle`, `visualAnchor`, `explanation`, `example`, `support`, `transition`, `evaluation` 을 모두 가진다. 평가·개선 루프는 섹션별로 이 흐름을 점검하고 약한 섹션을 재기획한다.
- **비주얼 위치 계약**: 표·그래프·테이블·이미지는 뒤에 자동으로 붙는 부록이 아니다. 기획이 각 `visuals[]` 와 `imagePlan[]` 에 `placement`, `insertAfter`, `narrativeUse` 를 적어 본문 어느 설명 뒤에서 어떤 이해를 만들지 결정한다. 한 막이나 카드에 하나로 부족하면 2~4개 시각물을 같이 기획한다.
- **템플릿 금지**: "누가 돈을 버나", "왜 못 버나", "아직 적자" 같은 금융 결론형 문구를 제목·막 구조의 기본 프레임으로 반복하지 않는다. 기술·시장·기업의 구체 메커니즘이 제목과 H2의 주어여야 한다.
- **누락 차단**: imagePlan 없이 발행, 데이터 설명 없는 숫자 카드, 공정·회사 지도 없는 기술 글, 전수 스캔 없는 데이터 글, 회사 내러티브 없는 기업 글은 형식 점수와 관계없이 재작성한다.

## 1. 주제: 데이터 작업대 완주 → 이야기꺼리 선정
- **데이터 완주(작가 = 데이터 기획)**: 관통선을 정하기 **전에** dartlab 데이터 작업대를 끝까지 몬다. 고정 템플릿(특정 지표 몇 개)이 아니라 이 회사가 가진 걸 다 꺼내 본다.
  - 재무제표: `c.panel` IS/BS/CF/CIS/SCE/ratios (완전 구조화).
  - DART 표준공시 **28유형**(`report.*`, 2,799필드): 배당·최대주주·자기주식·증자·임원·임원보수(개인/총액)·감사계약·감사의견·직원·회사채·CP·타법인출자·사외이사·소액주주.
  - 사업부문 매출: `scan.salesByProduct`(부분 커버, 없으면 "4. 매출 및 수주상황" body 표 직접 파싱 = 부문·지역·수주잔고).
  - 동종·시장: `scan`(전종목 축) · `PeerCompareN` · `industry`(밸류체인).
  - 주가·테마·뉴스: `gather`. 외부 증권사 리포트·최근 뉴스: `WebSearch`(untrusted 라벨).
  - 없는 회사는 없는 대로 넘어간다.
- **이야기꺼리(이상 아님)**: red flag를 찾는 게 아니라 **읽고 싶어지는 실**(전환·성장·베팅·해자·사이클·믹스 이동)을 찾는다. 예: "적자 변압기 회사가 고마진 AI 전력주가 된 이야기, 근데 그 값이 버티나".
- **선정**: 관통선 1 개. 제목 없이 첫 질문만으로 읽고 싶어야 한다. 후보·진행 = 워크리스트(세션 간 claim 충돌 방지), 착수 전 글롭 중복확인.
- ⚠ **추출 갭(fill 대상)**: "II. 사업의 내용" body 표(수주잔고·지역별매출·가동률/생산능력·주요제품 가격·원재료·R&D·MD&A)는 아직 미구조화라 필요 시 body text 직접 파싱. gather/scan 파서가 채워지는 대로 이 목록 축소.
- → BLOG.md §Phase 0

## 2. 기획: 전문 에이전트 적대 토론 (+ 평가·개선 루프)
- **turnkey 루프(필수, 카드·팟캐스트 파리티)**: `Workflow({ scriptPath: "blog/_scripts/blog_plan_loop.workflow.js", args: { contentKind, topic, corpName, stockCode, evidence, recentTitles } })`. 단독 작업(에이전트 체인 스킵)은 BLOG.md:158 경고 위반이고 클리셰·얕음·이미지 부실을 부른다. **반드시 이 루프로 기획한다.** 산출 plan(관통선·인싸이트·막구조·섹션별 독해 구조·막별비주얼·imagePlan·evidenceMap·정직성가드)을 `brief.json` 으로 글 폴더에 저장(발행 게이트가 이 산출물을 확인).
- **92점 루프 게이트(필수)**: 작가기획 → 평가 피드백 → 작가 재기획 → 재평가를 최소 2라운드 실행한다. `reviewGate.loopEvidence.workflow="blog_plan_loop.workflow.js"`, `rounds >= 2`, 마지막 `evaluatorScore >= 92`, 마지막 `decision=passed`, 재기획 흔적이 없으면 발행 실패다. 신규 심층 글은 마지막 관전 시나리오와 이미지 SSOT도 같은 루프에서 평가한다.
- 병렬 4 에이전트(마찰 0)는 클리셰를 통과시킨다 → **적대 토론**으로: 재무분석가 vs 산업·역사가(서로 다른 관통선 경합) → 회의론자(둘 다 "템플릿 클리셰"로 격파) + 독자대리인(재미) → **단일 관통선 + 정직성 가드**로 수렴.
- 산출: **독자질문 1(관통선)** + **핵심 인싸이트 1(그 질문의 답)** + 막 구조표 + **섹션별 독해 구조표** + 막별 테이블 + 제목/description 후보 + **막별 비주얼 기획**(고정 템플릿 아님. 이야기가 요구하는 차트·표·카드를 막마다 정한다: 부문 믹스=도넛, OPM 궤적=라인, peer=바, 수주 runway=런웨이 차트. 카드뉴스 `imagePlan`처럼 블로그 차트도 스토리가 정한다). 각 비주얼은 `placement`, `insertAfter`, `narrativeUse` 로 본문 중간 삽입 위치와 독자 이해 역할까지 결정한다.
- **핵심 인싸이트 1 (필수·확실히)**: 관통선(질문)의 *답*을 한 문장으로. ① 상식과 다르고 ② 기억되며 ③ 다음 공시에 적용 가능해야 한다. 내러티브가 장면→숫자→반전을 거쳐 **이 한 문장에 필연적으로 착지**한다(요약 박스가 아니라 이야기가 도달하는 결론). 관통선이 재미의 문이라면 인싸이트는 독자가 쥐고 나가는 단백질. 예(HD): "24% 마진은 변압기 비중 61→70% 쏠림이 만든 시간 독점의 가격이고, 그 비중이 지표다".
- 평가·개선 루프: 막을 나열한 뒤 "이 막을 빼면 더 궁금해지나?" 안 약해지면 삭제·흡수.
- ⚠ **Workflow 팬아웃 시**: craft·관통선은 신뢰하되 **모든 수치·인과는 메인 스레드 dartlab 재검증**(에이전트 산출 환각 다수). dartlab 검증 = 메인 순차(OOM 가드, 회사 동시 import ≤ 2), 토론·WebSearch만 워크플로(에이전트 dartlab 호출 금지).
- → BLOG.md §Phase 1

## 3. 블로그 작가 루프
- **집필**: 막별 재무분석가(데이터+해석) → 스토리작가(장면+리듬). 매 막 "왜?"로 시작, 끝에 다음 막으로의 인과 다리 1 문장.
- **편집 게이트(마스터라이터)**: 첫 2 문단 재작성 · 모든 H2 검사(궁금증 심화·메커니즘·리스크 반전·판단 닫힘) · 막을 `장면→숫자→반전→판단`으로 · 보고서톤/제작어 제거 · "틀리는 조건" 3~5 개. → _reference/BLOG_MASTER_WRITER.md
- 막 개수 = 6 막 기본·고정 아님(한 막 3,500 자↑ 분할, 질문 흐려지면 합침).

## 4. 블로그 평가 루프 (품질 게이트)
- **독자 에이전트** 6 항목: 재미 · 집중 끊긴 곳 · 독자질문 생존 · "어?" 횟수 · 기억 문장 · 점수.
- **인싸이트 도달 게이트 (확실히·필수)**: 독자 에이전트가 글을 덮고 **묻지 않아도** 핵심 인싸이트를 한 문장으로 되뇐다. 그게 기획의 인싸이트와 일치하고 **뻔하지 않으면**(상식·업계 상식이면 실패) 통과. 못 되뇌거나 뻔하면 = 내러티브가 인싸이트를 묻거나 애초에 인싸이트가 얕은 것 → 재작성. 재미있게 읽혔는데 남는 게 없으면(칼로리만·단백질 0) 발행 차단.
- **적대검증**: 본문 강한 수치 전부 메인 dartlab 재계산(NPM 행 누락 · 연도 귀속 · 배율 오류 사례 다수). 검증표에 없는 숫자 = 발행 차단.
- **정직성 가드**: 영업이익 vs 순이익 분리 · 분기/연간 라벨 명시 · 일회성 분리 · 매핑 artifact 무시 · 연결 vs 그룹 실체 구분.
- **발행 하드 게이트(단일 검사 진입점)**: `uv run python -X utf8 blog/_scripts/publishGate.py --post blog/<카테고리>/<폴더>`. 위반 시 exit 1. 내부에서 `auditBlog.py` 하드 계약, `audit_seo.py` SEO 95 이상, HF 원격 실재, Git 바이너리 0건을 함께 검사한다. 신규 글은 `contractVersion: 2`, 시나리오형 마지막 H2, 이미지 `assetKey`·중앙 `media/catalog.json`·본문 HF URL·CREDITS 정합까지 통과해야 한다. `audit_seo.py`나 `auditBlog.py`를 따로 실행한 결과는 발행 승인으로 쓰지 않는다. CI는 push diff에서 바뀐 글 폴더만 같은 진입점으로 검사한다.
- **깊이 게이트(회사 심층 리포트 한정)**: 측정은 **본문 기준**(표·SVG·코드 제외한 읽는 글자수. audit_seo·auditBlog 공통). 하한 **14,000자** 미만이면 `auditBlog.py` 가 "얕음(shallow deep report)"로 리라이트 후보 표시. 심층 완성 목표 **20,000자 이상**(현재 상위 3%만 도달, 최고작 티어), 장기 야심은 4만자. 길이는 막·증거·시나리오의 산물이지 패딩이 아니다(반복도 가드와 짝, 표 복붙·문장 늘리기 차단). 교육·소식·신용 카테고리는 구조상 단문이라 제외.
- → BLOG.md §Phase 4

## 5. 카드뉴스 루프
- **3 종 구분**: ① 회사 카드(블로그 글 frontmatter `carousel:`, code 있음) ② 에디토리얼(인스타 톤, Hook Engine 후킹 채점) ③ 이슈 카드(standalone, `blog/_issues/{slug}`, 블로그 글 없음).
- **기획**: `plan_card_news.py` → `cards.plan.json`(imagePlan 7장 이상, visualPlan, reviewGate).
- **데이터 시각 게이트**: 숫자·비교·현금·마진·주가 같은 데이터 주장 카드는 `visualPlan.dataExplanation` + `evidenceRefs` + 실제 slide `visual` 또는 `visuals[]` 계약(`finCard` 또는 `table`)을 붙인다. 배경 이미지만 있는 숫자 카드는 발행 차단. 한 카드에 하나로 부족하면 `table`+`finCard` 처럼 최대 4개까지 같이 붙이고, 계획 수량과 실제 수량이 다르면 발행 차단한다.
- **작가 패널 게이트(공개물 필수, 자동통과 금지)**: 훅 강도·서사 스파인·디자인/이미지 적합성·정직성 독립 검토 → 합의 수정 → 같은 패널 재평가. `reviewGate.status="passed"` + `reviewGate.loopEvidence.rounds >= 2` + 최종 `evaluatorScore >= 92` 전 `build_carousel_contracts.py` 발행 차단.
- → _scripts/CARDS.md (카드 파이프라인 상세 SSOT)

## 6. 이미지: 생성 / 수급 / 평가·개선
- **기획**: `brief.json.imagePlan[]`이 이미지 의미 계약의 SSOT다. 각 항목은 고유 `assetKey`, `sourcePolicy: auto`, 피사체, 검색어, 본문 위치, 서사 용도를 가진다.
- **자율 수급**: 파이프라인이 사실 적합성으로 경로를 선택한다. 실제 제품·인물·현장처럼 정확성이 중요한 피사체는 공식 출처 또는 라이선스가 확인된 실사를 쓴다. 개념·원리·추상 장면은 `image_gen`을 쓴다. 한 경로가 실패하면 묻고 멈추지 않고 다른 적합 경로로 전환한다. 핀터레스트·구글 이미지 무단 사용은 금지다. FLUX는 운영자의 명시 지시가 있을 때만 쓴다.
- **미디어 SSOT**: 블로그 SVG/WebP/JPG/PNG/GIF는 Git에 넣지 않는다. 포스트 `assets/`, 팟캐스트 커버, `landing/static/thumbnails/`는 로컬 검수·합성 staging이고, HF `dartlab-media/objects/sha256/<앞2자>/<전체해시>.<확장자>`에 같은 바이트를 한 번만 둔다. durable 원본과 서빙본은 HF 하나다.
- **Git 계약**: `brief.json.imagePlan[]`이 래스터 의미를, `assets/CREDITS.md`가 출처를, 중앙 `media/catalog.json` 하나가 래스터 `assets`, SVG `diagrams`, OG/card 역할과 HF 객체 SHA-256 대응을 가진다. 본문과 frontmatter는 카탈로그에서 파생한 HF URL만 쓴다.
- **공유 경계**: v2 기술 카드도 중앙 카탈로그의 같은 `objects/sha256/` 경로를 쓴다. `sns/assets/{subjectKey}`와 `ingest_blog_assets.py`는 legacy 회사 공유풀 호환용이며 새 블로그 이미지의 SSOT가 아니다. 깨끗한 체크아웃에서 재생성이 필요하면 `seedBlogMedia.py --post blog/<카테고리>/<폴더>`로 staging을 복원한다.
- **평가·개선**: 색복잡도 감사와 눈검수를 함께 한다. 피사체 오매치, 가짜 공식 로고·문서, 식별 인물 왜곡이 있으면 다른 실사 또는 `image_gen`으로 교체한다. `publishGate.py`가 assetKey, HF 실재, 본문 URL, CREDITS, Git 바이너리 0건을 막는다.
- **레거시 폐기 게이트**: HF 옛 폴더는 `consolidateHfMedia.py --apply --delete-legacy`로만 지운다. 이 명령은 원격 manifest·객체 무결성과 배포된 `/cards`·`/blog`·`/terminal` 번들의 새 경로 전환을 자동 검증하며, 실패 시 삭제하지 않는다. 배선도와 순서 정본은 [OPERATIONS.md](OPERATIONS.md)의 `미디어 SSOT 배선과 레거시 폐기` 절이다.

## 7. 발행
- **블로그**: 이미지·OG를 로컬에서 눈검수한 뒤 `publishBlogAssets.py --post <글폴더>`로 HF 발행·본문 치환 -> `publishGate.py --post <글폴더>` 통과 -> 빌드 확인 -> 커밋. 재무는 `<CompanyFinancials code="…" />` 라이브 태그(빌드타임 데이터 SSOT 직독). → BLOG.md §Phase 5
- **카드**: `build_carousel_contracts.py` -> hfMedia `manifests/carousels.json` 단일 런타임 뷰 + `objects/sha256/` 객체. 데이터만 올리므로 사이트 재빌드는 필요 없다.
- **자산**: `build_index.py` → `publish_assets_hf.py` → HF `dartlab-media`.
- **발행 후**: 월 SEO 스코어링 · 내부링크 맵 · KnowledgeDB `insights` 백필(블로그=`backfill_blog_insights.py`, 카드=향후 `source="cards"`).

---
정본 위치: 블로그 단계 상세 [BLOG.md](BLOG.md) · 카드 [_scripts/CARDS.md](_scripts/CARDS.md) · 작가 게이트 [_reference/BLOG_MASTER_WRITER.md](_reference/BLOG_MASTER_WRITER.md) · 스크립트 [_scripts/README.md](_scripts/README.md).
