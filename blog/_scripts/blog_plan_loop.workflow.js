// 블로그 심층 리포트 기획·평가 루프 (구조화된 오케스트레이션, durable SSOT)
//
// 카드/팟캐스트의 plan_loop 워크플로와 파리티. 지금까지 블로그만 turnkey 루프가 없어 "단독 작업(에이전트 체인
// 스킵)"으로 흘러 클리셰·얕음·이미지 부실이 게이트를 통과했다(BLOG.md:158 경고 위반). 이 워크플로가 그 구멍을 막는다.
//
// 흐름:
//   Phase 1 경합(적대 토론): 재무분석가 vs 산업·역사가가 서로 다른 관통선을 경합 제안 후 회의론자(클리셰 격파) +
//     독자대리인(재미 생존) 이 동시에 깐다. 편집장이 단일 관통선 + 핵심 인싸이트 + 막 구조 + 막별 비주얼 +
//     이미지 기획(내용 연상, 로고·상징품 허용) + 정직성 가드로 수렴한다.
//   Phase 2 평가개선(독자 루프): 독자 평가자(BLOG.md Phase4 6항목) + 회의자(적대 kill) 동시 심사 후 둘 다 통과까지
//     기획작가가 재작성. MAX_ROUNDS 안에 통과 못 하면 passed=false(발행 금지).
//
// 숫자·인과는 메인 스레드 dartlab 직독으로 args.evidence 에 주입(에이전트는 dartlab 호출 안 함, 환각 방지).
//
// 실행: Workflow({ scriptPath: "blog/_scripts/blog_plan_loop.workflow.js",
//                  args: { contentKind, topic, corpName, stockCode, evidence, recentTitles } })
// 산물: { plan, loopLog, passed, rounds }
//   passed=false 면 발행 금지. plan 을 index.md 집필 + imagePlan 수급 + visuals 차트의 입력으로 쓴다.
// 문서 SSOT: operation.content · BLOG.md Phase 1/2/4 · PIPELINE.md.

export const meta = {
  name: 'blog-plan-loop',
  description: '블로그 심층 리포트 기획 루프: 재무분석가 vs 산업역사가 적대 토론 후 회의론자+독자대리인 격파, 편집장 수렴, 독자평가+회의자 둘 다 통과까지 반복',
  phases: [
    { title: '경합', detail: '재무분석가 vs 산업역사가 관통선 경합 후 회의론자+독자대리인 격파, 편집장 수렴' },
    { title: '평가개선', detail: '독자 평가자(6항목)+회의자(적대 kill) 동시 심사 후 기획작가 개선, 둘 다 92점 이상까지 반복' },
  ],
}

const PRINCIPLES = `블로그 심층 리포트 원칙(합격선):
0. 제목 후크: 제목은 본문을 다 쓴 뒤 붙이는 라벨이 아니라 기획의 첫 약속이다. 후보 3개 이상을 비교하고, 독자의 상식과 글이 끝까지 갚을 질문 사이에 호기심 갭을 만든다. "정리", "분석", "이야기", "총정리", "돈을 못 번다"식 반복 템플릿은 실패다.
1. 단일 관통선: 사람들이 이 회사에서 진짜 궁금해할 이상한 점 1개("매출 2배인데 왜 이익은 널뛰나"류). 회사소개·실적요약·"좋은 회사"는 관통선이 아니다. 좋은 관통선은 이상한 숫자·상식과 다른 결과·갑자기 바뀐 장면·아직 공시로 덜 검증된 서사에서 나온다.
2. 핵심 인싸이트 1: 관통선의 답을 한 문장으로. (a)통념과 충돌 (b)기억되고 (c)다음 공시에 적용 가능. 제목 재진술이면 실패. 다 읽고도 세계관 그대로면 실패.
3. 막 구조: 각 막은 궁금증 심화·메커니즘 공개·리스크 반전·판단 닫힘 중 하나를 한다. 막 제목을 나열해 "이 막을 빼면 더 궁금해지나" 안 약해지면 삭제. 매 막은 장면·숫자·반전·판단으로, 끝에 다음 막으로의 인과 다리 1문장.
4. 정직성: 영업이익 vs 순이익 분리, 분기/연간 라벨 명시, 일회성 분리, 매핑 artifact 무시, 연결 vs 그룹 실체 구분. dartlab 미검증 사실은 외부 맥락으로 분리. 억지 수치("이런 뜻은 아니다" 변명 필요) 금지.
5. 깊이: 얕은 요약이 아니라 메커니즘까지 판다. 심층 리포트는 본문(표·차트 제외 읽는 글자) 14,000자 이상, 목표 20,000자. 다만 길이는 막·증거·시나리오의 산물이지 패딩이 아니다(반복·표 복붙·문장 늘리기 금지).
6. 재미: 첫 2문단이 회사 배경이 아니라 이상한 숫자와 긴장으로 시작. "어?" 순간 4번+. 마지막은 요약이 아니라 다음 공시를 보는 기준으로 닫음.
7. 참고글 연결: 선행 글에 이미 설명한 회사·기술·데이터·투자 개념이 있으면 relatedPosts 에 검색어, 링크, 배치 이유를 남긴다. 본문에서는 반복 설명을 줄이고 필요한 문단 뒤에 참고글을 연결한다.
표기: em dash(긴 줄표) 금지. 부연은 마침표·괄호, 범위는 물결(~). 문장은 다/요/까.`

const IMAGE_NOTE = `이미지 기획(내용 연상 강제): hero 1장 + 본문 inline 2~3장 이상. inline 이미지는 뒤에 자동으로 붙는 장식이 아니라 어느 막의 어느 설명 뒤에 들어갈지 insertAfterAct·placement·narrativeUse 로 결정한다. 각 이미지는 무조건 이 글의 내용·회사·제품·현장을 연상시켜야 한다. 회사 로고·상징품·실제 제품도 허용(주식·재무·교육 맥락이라 저작권 무관). 범용 스카이라인·추상 배경으로 도망가면 실패. query 는 실사 CC0 수급용 영어 검색어(그 회사 제품·현장·상징을 앞에), keywords 는 제목/태그 매칭용(오매치 차단). 예(봉제완구 회사): query "plush stuffed animals teddy bear shelf", keywords ["plush","teddy","stuffed","toy"].`

const VISUAL_NOTE = `막별 비주얼: 이야기가 요구하는 차트·표·그래프 세트를 막마다 정한다(고정 템플릿 아님). 추이=line, 비교/구성=bar, 부문믹스=도넛/스택, 두 계열 대비=grouped, 공정·회사·근거 지도=table. 한 막에 하나로 부족하면 같은 actOrder 에 2~4개를 기획한다. 시각물은 글 뒤 자동 부록이 아니라 본문 중간 설명 장치다. placement·insertAfter·narrativeUse 로 어느 문장 뒤에 왜 들어가는지 적는다. 각 차트는 그 막의 주장을 증명해야 하고, 큰 숫자를 가려도 차트만으로 같은 긴장이 남아야 한다. 손수 못생긴 차트 금지. kind·title·proves·seriesHint 를 명확히 적어 메인 스레드가 정식 렌더로 그리게 한다.`

const SECTION_NOTE = `섹션별 독해 구조(강제): 모든 주요 H2 섹션은 기획에서 먼저 설계한다. 순서는 1) 섹션 타이틀 2) 한 줄 서브타이틀/훅 3) 이미지·표·도식·코드 출력 같은 시각 앵커 4) 설명적 서술 5) 실제 예시 6) 보완 설명·오해 방지 7) 다음 섹션 연결문이다. 기획안의 sections[] 에 heading, subtitle, visualAnchor, explanation, example, support, transition, evaluation 을 모두 채운다. 평가자는 섹션마다 이 흐름이 끊기면 재기획을 요구한다.`

const DARTLAB_PLAIN_NOTE = `dartlab 이야기 직관성 게이트:
1. 화면 먼저, 설명 나중. 각 H2는 독자가 보는 코드, 출력 표, 계정명, 기간, 값, 공시 문장 중 하나를 앞쪽에 둔다.
2. 한 문단은 "무엇을 본다 -> 그게 무슨 뜻이다 -> 그래서 다음에 무엇을 한다" 순서로 쓴다.
3. "구조", "흐름", "표면", "경계", "맥락", "감각", "역할" 같은 말은 실제 코드나 값 없이 혼자 서면 실패다.
4. "중요하다", "핵심이다", "연결된다"로 끝내지 않는다. 무엇이 어디에 보이고, 독자가 어떤 칸을 확인해야 하는지까지 쓴다.
5. 예시는 반드시 실제 호출, 실제 계정, 실제 기간, 실제 값, 실제 공시 문장 중 하나를 담는다.
6. 앞 섹션의 결과를 다음 섹션 첫 문장에 다시 잡아 준다. 독자가 글 사이에서 길을 잃으면 실패다.`

// 필드가 무엇을 담아야 하는지는 프롬프트(FIELD_GUIDE)가 말한다. 스키마는 형태만 말한다.
// 설명문을 스키마에 넣었더니 JSON 이 7KB 를 넘어 구조화 출력이 안전 분류기에 통째로 막혔다
// ("output schema too large to classify safely", 2026-07-10). 편집장 수렴과 기획작가 개선이
// 전부 실패해 루프가 어느 카테고리에서도 안 돌았다.
const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'titleContract', 'description', 'readerQuestion', 'insight', 'acts', 'sections', 'visuals', 'imagePlan', 'relatedPosts', 'honestyGuards', 'evidenceMap'],
  properties: {
    title: { type: 'string' },
    titleContract: {
      type: 'object', additionalProperties: false,
      required: ['workingTitle', 'selectedTitle', 'hookQuestion', 'readerGap', 'promise', 'whySelected', 'candidates', 'rejectedPatterns'],
      properties: {
        workingTitle: { type: 'string' },
        selectedTitle: { type: 'string' },
        hookQuestion: { type: 'string' },
        readerGap: { type: 'string' },
        promise: { type: 'string' },
        whySelected: { type: 'string' },
        candidates: {
          type: 'array', minItems: 3,
          items: {
            type: 'object', additionalProperties: false, required: ['title', 'hook', 'risk'],
            properties: { title: { type: 'string' }, hook: { type: 'string' }, risk: { type: 'string' } },
          },
        },
        rejectedPatterns: { type: 'array', items: { type: 'string' } },
      },
    },
    description: { type: 'string' },
    readerQuestion: { type: 'string' },
    insight: {
      type: 'object', additionalProperties: false,
      required: ['commonBelief', 'twistFact', 'whatToWatch', 'freshnessArgument', 'evidenceRefs'],
      properties: {
        commonBelief: { type: 'string' },
        twistFact: { type: 'string' },
        whatToWatch: { type: 'string' },
        freshnessArgument: { type: 'string' },
        evidenceRefs: { type: 'array', items: { type: 'string' } },
      },
    },
    acts: {
      type: 'array', minItems: 6,
      items: {
        type: 'object', additionalProperties: false, required: ['order', 'heading', 'purpose', 'scene', 'keyNumbers', 'causalBridge'],
        properties: {
          order: { type: 'integer' },
          heading: { type: 'string' },
          purpose: { type: 'string', enum: ['배경', '궁금증심화', '메커니즘공개', '리스크반전', '판단닫힘'] },
          scene: { type: 'string' },
          keyNumbers: { type: 'array', items: { type: 'string' } },
          causalBridge: { type: 'string' },
        },
      },
    },
    sections: {
      type: 'array', minItems: 6,
      items: {
        type: 'object', additionalProperties: false,
        required: ['order', 'heading', 'subtitle', 'visualAnchor', 'explanation', 'example', 'support', 'transition', 'evaluation'],
        properties: {
          order: { type: 'integer' },
          heading: { type: 'string' },
          subtitle: { type: 'string' },
          visualAnchor: { type: 'string' },
          explanation: { type: 'string' },
          example: { type: 'string' },
          support: { type: 'string' },
          transition: { type: 'string' },
          evaluation: { type: 'string' },
        },
      },
    },
    visuals: {
      type: 'array', minItems: 3,
      items: {
        type: 'object', additionalProperties: false, required: ['actOrder', 'kind', 'title', 'proves', 'placement', 'insertAfter', 'narrativeUse'],
        properties: {
          actOrder: { type: 'integer' },
          kind: { type: 'string' },
          title: { type: 'string' },
          proves: { type: 'string' },
          seriesHint: { type: 'string' },
          placement: { type: 'string' },
          insertAfter: { type: 'string' },
          narrativeUse: { type: 'string' },
        },
      },
    },
    imagePlan: {
      type: 'array', minItems: 3,
      items: {
        type: 'object', additionalProperties: false, required: ['slot', 'subject', 'query', 'keywords', 'placement', 'narrativeUse'],
        properties: {
          slot: { type: 'string', enum: ['hero', 'inline'] },
          subject: { type: 'string' },
          query: { type: 'string' },
          keywords: { type: 'array', items: { type: 'string' } },
          insertAfterAct: { type: 'integer' },
          placement: { type: 'string' },
          narrativeUse: { type: 'string' },
        },
      },
    },
    relatedPosts: {
      type: 'object', additionalProperties: false,
      required: ['searches', 'links', 'placementRule'],
      properties: {
        searches: { type: 'array', minItems: 1, items: { type: 'string' } },
        links: {
          type: 'array',
          items: {
            type: 'object', additionalProperties: false, required: ['path', 'title', 'reason', 'placement'],
            properties: { path: { type: 'string' }, title: { type: 'string' }, reason: { type: 'string' }, placement: { type: 'string' } },
          },
        },
        placementRule: { type: 'string' },
      },
    },
    honestyGuards: { type: 'array', items: { type: 'string' } },
    evidenceMap: {
      type: 'array', minItems: 3,
      items: {
        type: 'object', additionalProperties: false, required: ['claim', 'sourceType', 'period', 'sourceRef', 'howUsed'],
        properties: {
          claim: { type: 'string' },
          sourceType: { type: 'string', enum: ['DART', 'EDGAR', 'dartlab', 'scan', 'external', 'price', 'macro', 'internal-blog'] },
          period: { type: 'string' },
          sourceRef: { type: 'string' },
          howUsed: { type: 'string' },
        },
      },
    },
  },
}

// 스키마에서 뺀 필드 설명. 프롬프트로 준다.
const FIELD_GUIDE = `필드 정의:
- title: 60자 이하. 궁금증 갭. 예 "오로라월드, 매출은 2배가 됐는데 이익은 왜 널뛸까".
- titleContract.selectedTitle 은 title 과 같아야 한다. hookQuestion 은 제목이 첫 1초에 만드는 독자 질문. readerGap 은 독자의 상식과 글이 갚을 사실 사이의 간격. promise 는 제목이 약속하고 결론이 갚을 내용. whySelected 는 왜 다른 후보보다 이 제목이 강한가. candidates 는 후보 3개 이상(title, hook, risk).
- description: SEO description 80~200자. 첫 2줄이 검색 스니펫.
- readerQuestion: 관통선 = 독자 질문 1개. 제목 없이 이 질문만으로 읽고 싶어야 한다.
- insight: commonBelief 통념. twistFact 관통선의 답(통념과 충돌하는 사실 + 메커니즘, 제목 재진술·억지 수치 금지). whatToWatch 다음에 볼 지표. freshnessArgument 왜 재탕이 아닌가. evidenceRefs 이 인싸이트를 받치는 실측 근거(evidence 안에서).
- acts: order 순으로 읽으면 한 편. heading 은 고유·궁금증형 H2. scene 은 장면(보고서톤 금지). keyNumbers 는 evidence 안의 실측 수치. causalBridge 는 다음 막으로 넘어가는 인과 다리 1문장.
- sections: 실제 H2별 독해 설계. heading 은 섹션 타이틀. subtitle 은 한 줄 훅. visualAnchor 는 이미지·표·도식·코드 출력 중 무엇을 앞쪽에 둘지. explanation 은 쉬운 설명. example 은 실제 예시. support 는 보완 설명·오해 방지. transition 은 다음 섹션 연결문. evaluation 은 평가·개선 루프에서 확인할 기준.
- visuals: actOrder 어느 막에 붙나. kind 는 line, bar, grouped, donut, stack, table 등. proves 는 이 시각물이 증명하는 주장. seriesHint 는 어떤 계열·기간. placement, insertAfter, narrativeUse 로 본문 어느 문장 뒤에 왜 들어가는지.
- imagePlan: slot 은 hero 또는 inline. subject 는 무엇을 연상시키나. query 는 실사 CC0 수급용 영어 검색어. keywords 는 오매치 차단용. insertAfterAct 는 inline 이면 어느 막 뒤(hero 는 0). placement, narrativeUse 필수.
- relatedPosts: searches 는 착수 전 검색할 내부 글 키워드. links 의 path 는 /blog/슬러그. reason 은 왜 연결하는가. placementRule 은 참고글을 본문 어디에 어떤 요약과 함께 놓을지.
- honestyGuards: 이 글에 적용할 정직성 가드(영업이익 vs 순이익 분리 등).
- evidenceMap: claim 이 받치는 주장. sourceType 은 DART, EDGAR, dartlab, scan, external, price, macro, internal-blog 중 하나. period 는 연도·분기·표본 기간(EDGAR 는 fiscal 명시). sourceRef 는 DART 보고서·EDGAR 10-K/10-Q·dartlab 호출. howUsed 는 어느 막이나 시각물에서 어떻게 쓰는지.`

const PROPOSAL_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['readerQuestion', 'twistFact', 'why', 'actSketch'],
  properties: {
    readerQuestion: { type: 'string', description: '이 렌즈로 세운 관통선 1개.' },
    twistFact: { type: 'string', description: '관통선의 답(통념 충돌 사실 + 메커니즘).' },
    why: { type: 'string', description: '왜 이게 독자가 진짜 궁금해할 지점인가.' },
    actSketch: { type: 'array', items: { type: 'string' }, description: '막 제목 스케치 5~7개.' },
  },
}

const CRITIQUE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdict', 'clicheKills', 'funNotes', 'strongerAngle'],
  properties: {
    verdict: { type: 'string', enum: ['survive', 'kill'], description: '관통선들이 클리셰/동어반복이면 kill.' },
    clicheKills: { type: 'array', items: { type: 'string' }, description: '클리셰·동어반복·K수출 상투 등 격파 사유.' },
    funNotes: { type: 'array', items: { type: 'string' }, description: '독자대리인: 재미·궁금증이 죽는 지점.' },
    strongerAngle: { type: 'string', description: '더 강한 관통선이 있으면 제시(없으면 빈 문자열).' },
  },
}

const READER_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['decision', 'fun', 'dropOff', 'questionAlive', 'huhCount', 'memorableLine', 'score', 'findings'],
  properties: {
    decision: { type: 'string', enum: ['pass', 'revise'] },
    fun: { type: 'string', description: '재밌나? YES/NO + 이유.' },
    dropOff: { type: 'string', description: '어디서 집중 끊기나.' },
    questionAlive: { type: 'string', description: '독자 질문(관통선)이 끝까지 살아있나.' },
    huhCount: { type: 'integer', description: '"어?" 순간 횟수.' },
    memorableLine: { type: 'string', description: '기억에 남는 문장.' },
    score: { type: 'integer', description: '0~100.' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['where', 'problem', 'fix'],
        properties: { where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } },
      },
    },
  },
}

const SKEPTIC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdict', 'kills'],
  properties: {
    verdict: { type: 'string', enum: ['survive', 'kill'] },
    kills: {
      type: 'array',
      description: 'kill 사유. 하드 축만.',
      items: {
        type: 'object', additionalProperties: false, required: ['axis', 'why', 'fix'],
        properties: {
          axis: { type: 'string', enum: ['weak-title', 'cliche-template', 'forced-metric', 'misleading-frame', 'shallow', 'abstract-writing', 'weak-section-flow', 'generic-image', 'appendix-visual', 'weak-reference', 'overclaim'] },
          why: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

// Workflow 는 args 를 JSON 문자열로 넘긴다. 객체로 파싱해 쓴다.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const topic = A.topic || ''
const corpName = A.corpName || ''
const stockCode = A.stockCode || ''
const evidence = A.evidence || ''
const recent = Array.isArray(A.recentTitles) ? A.recentTitles.join(' / ') : (A.recentTitles || '없음')
const contentKind = A.contentKind || (stockCode ? 'company-reports' : 'tech-story')
const PASS_MIN = 92
const MAX_ROUNDS = 8

// 장르별 기획 구조 하한. 6 막 인과와 이미지 3 장은 심층 서사 장르의 골격이지 교육 연재의 골격이
// 아니다. 하한을 두면 채우기용 막과 채우기용 이미지가 붙는다. 값은 blog/_scripts/auditBlog.py 의
// GENRE_PLAN_SHAPE 와 같아야 한다(어긋나면 발행 게이트가 잡는다).
const PLAN_SHAPE = { 'dartlab-stories': { acts: 3, visuals: 1, images: 1 } }
const shape = PLAN_SHAPE[contentKind] || { acts: 6, visuals: 3, images: 3 }
PLAN_SCHEMA.properties.acts.minItems = shape.acts
PLAN_SCHEMA.properties.sections.minItems = shape.acts
PLAN_SCHEMA.properties.visuals.minItems = shape.visuals
PLAN_SCHEMA.properties.imagePlan.minItems = shape.images
PLAN_SCHEMA.properties.imagePlan.description =
  `내용 연상 이미지 기획(로고·상징품 허용). 그 편에 정말 필요한 만큼만. 최소 ${shape.images} 장(hero 포함).`
// 막의 목적도 장르를 따른다. 교육 연재의 단계는 궁금증심화·리스크반전이 아니라 학습 흐름이다.
if (contentKind === 'dartlab-stories') {
  PLAN_SCHEMA.properties.acts.items.properties.purpose.enum = [
    '왜배우나', '직접해본다', '개념정착', '경계밝히기', '다음으로',
  ]
}

// 교육 연재는 심층 리포트의 부분집합이 아니다. 원칙을 "덮어쓰기" 로 얹으면 관통선·인싸이트·재미
// 항목이 여전히 "이상한 숫자 미스터리" 를 요구해, 기획자는 미스터리 훅을 세우고 평가자는 그 훅을
// 이 편이 안 갚는다고 깎는다. 88~89 점에서 영영 도는 함정이었다(2026-07-10 실측).
// 그래서 이 장르는 자기 원칙을 따로 가진다. 평가자·회의자도 같은 원칙으로 심사한다.
const STORY_PRINCIPLES = `dartlab 이야기(교육 연재) 원칙(합격선):
0. 제목 파이프라인: 먼저 외부 검색자가 칠 말 하나를 고른다(DART 공시분석, 재무제표 파이썬, 사업보고서 코드). 제목은 18자 안팎, 최대 24자다. 구조는 "검색어, 즉시 효용" 또는 "대상, 행동 한 줄"만 인정한다. "무엇인가", "사용법 정리", "총정리", "하는 법"만 늘인 제목, 브랜드 소개형 제목, 긴 문장형 제목은 실패다. 후보 3개 모두 이 기준을 통과해야 한다.
1. 관통선: 독자가 지금 당장 하고 싶은 일 하나("재무제표를 어떻게 꺼내나"). 회사의 이상한 숫자가 아니다. 이 연재의 주어는 도구이지 회사가 아니다.
2. 핵심 인싸이트: 이 편이 가르치는 개념 하나. 다 읽고 나면 독자가 그 개념으로 새로운 것을 직접 해 볼 수 있어야 한다. 통념 반전이 아니라 능력 획득이 payoff 다.
3. 단계 구조: 최소 3단계. 무엇을 왜 배우나, 직접 해 본다, 무엇을 얻었고 다음은 무엇인가. 6막 인과가 아니다. 각 단계는 앞 단계가 준 능력을 딛는다.
3-1. 섹션 구조: 모든 주요 섹션은 타이틀, 한 줄 훅, 시각 앵커(실제 코드 출력·표·도식·이미지), 쉬운 설명, 실제 예시, 보완 설명, 다음 연결문 순서로 설계한다. sections[] 에 이 구조를 먼저 채우고, 본문은 그 설계를 따라 쓴다.
4. 정직성: 브라우저에서 안 되는 것을 그 자리에서 밝힌다. 실행해 보지 않은 코드는 싣지 않는다. 본문의 숫자는 실제로 돌려서 얻은 값이다. 코드 줄 수를 세어 말할 때는 화면에 보이는 줄 수와 맞춘다.
5. 깊이: 본문(코드·표 제외 읽는 글자) 3,000자 이상, 목표 5,000자. 14,000자가 아니다. 코드만 던지고 왜를 안 적으면 문서지 이야기가 아니고, 설명을 늘려 채우면 패딩이다.
6. 재미: 첫 코드칸에서 결과가 나온다. 성공 체험이 설명보다 먼저다. 회사 실적 미스터리로 낚지 않는다. 마지막은 요약이 아니라 독자가 지금 바꿔 볼 한 줄로 닫는다.
7. 참고글 연결: 선행 편과 관련 글을 relatedPosts 로 잇는다. 앞 편이 세운 개념을 다시 설명하지 않고 링크한다.
8. 출력 기준: .shape, 행열 크기, 몇 행 몇 열 같은 디버그 신호는 기획 근거가 아니다. 독자가 봐야 할 것은 실제 계정명, 기간 열, 값, 공시 문장이다.
9. 도구 비중: select 자체를 설명하는 편은 만들지 않는다. 필요한 줄을 좁힐 때만 짧게 쓴다. trace 는 출처가 헷갈릴 때 쓰는 점검 도구이며 독립 학습 목표가 아니다.
10. 내부 점검어 금지: 내부 기능 개수, 인증 개수, n/n 점검 표현은 독자에게 중요하지 않다. 실제로 무엇을 열고 어떤 값이 보이는지만 쓴다.
11. 직관성: 추상 설명이 화면보다 먼저 오면 실패다. 각 섹션은 코드, 출력 표, 계정, 기간, 값, 공시 문장 중 하나를 먼저 붙잡고 그다음 쉬운 말로 푼다. "구조", "흐름", "표면", "경계", "맥락", "감각", "역할" 같은 단어는 실제 코드나 값 없이 혼자 서면 허공 설명으로 본다.
표기: em dash(긴 줄표) 금지. 부연은 마침표·괄호, 범위는 물결(~). 문장은 다/요/까. 독자용 문구에 "축"(axis) 이라는 내부 용어를 쓰지 않는다.`

const NOTES =
  contentKind === 'dartlab-stories'
    ? {
        principles: STORY_PRINCIPLES,
        section: `${SECTION_NOTE}\n\n${DARTLAB_PLAIN_NOTE}`,
        image: `이미지 기획: 그 편에 정말 필요한 그림만 적는다. 고정 하한 없음(최소 hero 1장). 채우기용 inline 이미지는 실패다. 교육 연재의 피사체는 회사·제품이 아니라 도구·데이터·코드다(노트북, 코드 화면, 문서, 서버). 범용 스카이라인·추상 배경으로 도망가면 실패. query 는 실사 CC0 수급용 영어 검색어, keywords 는 오매치 차단용. 각 이미지에 placement·narrativeUse 를 적는다.`,
        visual: `비주얼: 이 연재의 주된 시각물은 코드 실행 결과 표 그 자체다. 별도 차트를 억지로 만들지 않는다. 표를 보여 줄 때는 .shape 나 행열 크기가 아니라 실제 계정명, 기간 열, 값, 공시 문장을 시각 앵커로 삼는다. 개념을 설명하는 도해가 정말 필요할 때만 최소 1개 기획한다.`,
      }
    : { principles: PRINCIPLES, section: SECTION_NOTE, image: IMAGE_NOTE, visual: VISUAL_NOTE }

const CONTENT_GUIDANCE = {
  'company-reports': `기업이야기: 회사 하나의 내러티브를 깊게 판다. 사업 구조, 공시 문장, 제품·고객·수주·원가·자본배치·현금흐름을 한 회사 안에서 연결한다. DART 또는 EDGAR 근거와 dartlab 실측을 분리하고, 다음 공시에서 볼 렌즈로 닫는다.`,
  'tech-story': `기술이야기: 기술이 주어다. 기술 원리, 공정 파이프라인·네트워크망, 어느 칸에 어떤 회사가 있고 왜 그 회사가 병목·표준·원가·고객 접점을 쥐는지 설명한다. 한국사는 DART, 미국사는 EDGAR를 연결한다. 돈 이야기만 앞세우거나 "누가 돈을 버나" 템플릿이면 실패다.`,
  'data-reports': `데이터 리포트: scan과 전종목 파서로 전체 시장의 특이점을 찾는다. 개별 회사는 대표 사례일 뿐이다. 표본·분모·제외 조건·정제 전후를 드러내고, DART·EDGAR 전체 유니버스 또는 제외 사유를 명시한다. 순위표 나열로 끝나면 실패다.`,
  'investment-stories': `투자이야기: 투자자가 시장을 읽을 때 쓰는 언어와 프레임이 주어다. 주가, 경제 변수, 증권사 표현, 투자 용어, 기술적투자 보조지표, 기술투자 관점을 설명한다. 지지선·목표가·보조지표를 매수·매도 결론으로 쓰면 실패다. 선행 회사·기술·데이터 글이 있으면 relatedPosts 로 연결하고, 독자가 다음 차트·공시·경제지표에서 무엇을 확인할지로 닫는다.`,
  'dartlab-stories': `dartlab 이야기: dartlab 자체가 주어인 교육 연재다. 독자는 아무것도 모른 채 도착한다. 한 편에 개념 하나를 가르치고, 본문 python 코드블록을 독자가 브라우저에서 그대로 실행하게 만든다. 코드는 공개 호출 계약 안의 dartlab 함수와 Company 메서드만 쓴다. 브라우저에서 안 되는 것(실시간 시세·뉴스 수집 등)은 숨기지 말고 그 자리에서 밝힌다. 6 막 인과가 아니라 3 단계 이상의 학습 단계로 짠다: 무엇을 왜 배우나, 직접 해 본다, 무엇을 얻었고 다음은 무엇인가. imagePlan 은 그 편에 정말 필요한 그림만 적는다. 채우기용 이미지, 코드 없는 설명, 실행해 보지 않은 코드는 실패다. .shape 와 행열 크기, 내부 기능 개수, 인증 개수는 독자에게 의미 있는 근거가 아니므로 금지한다. select 와 trace 는 필요할 때 쓰는 도구일 뿐 독립 주제가 아니다.`,
}

const LENSES_BY_KIND = {
  'company-reports': [
    { role: '재무분석가', lens: '재무제표 안에서 이상한 숫자·전환점·괴리(영업이익 vs 순이익, 이익 vs 현금, 마진 급변, 운전자본·자본배분)를 관통선으로 세운다.' },
    { role: '산업·역사가', lens: '이 회사의 역사·업종·사업모델의 변곡(사업 전환, 해외·신제품, 사이클, 경쟁구도 이동)을 관통선으로 세운다.' },
  ],
  'tech-story': [
    { role: '기술·공정 아키텍트', lens: '기술 원리, 공정 단계, 병목, 표준, 양산 난도, 네트워크망에서 관통선을 세운다. 회사는 기술 지도의 칸에 배치한다.' },
    { role: '공시·재무 해석가', lens: 'DART와 EDGAR의 사업 설명·세그먼트·손익·수주·개발비에서 기술이 숫자로 남는 흔적을 관통선으로 세운다.' },
  ],
  'data-reports': [
    { role: '전수 스캔 분석가', lens: 'scan·전종목 파서로 시장 전체에서 튀는 분포, 꼬리값, 제거 전후, 표본 왜곡을 관통선으로 세운다.' },
    { role: '사례·공시 해석가', lens: '대표 회사의 DART·EDGAR 문장과 다년 숫자로 전수 결과가 왜 그런지 설명할 관통선을 세운다.' },
  ],
  'investment-stories': [
    { role: '시장언어 해설가', lens: '주가, 금리, 환율, 물가, 컨센서스, 목표주가, 밸류에이션 같은 시장 언어를 독자가 실제로 해석할 질문으로 바꾼다. 결론은 추천이 아니라 다음에 볼 기준이어야 한다.' },
    { role: '기술적투자·지표 해설가', lens: '지지선, 저항선, 이동평균, RSI, MACD, 거래량, 거래대금 같은 보조지표를 기간·기준·틀리는 조건까지 포함해 관통선으로 세운다.' },
  ],
  'dartlab-stories': [
    { role: '교육설계자', lens: '아무것도 모르는 독자가 이 한 편으로 무엇을 할 수 있게 되는지에서 관통선을 세운다. 선수지식은 최소로, 첫 성공 체험은 첫 코드블록 안에 온다. shape 같은 개발자 신호를 설명하면 실패다.' },
    { role: 'dartlab 엔지니어', lens: '공개 호출 계약과 브라우저에서 실제로 도는 경계에서 관통선을 세운다. panel, analysis, credit, scan 처럼 반복 사용 가치가 큰 표면을 우선하고, select 와 trace 는 필요 순간에만 작게 쓴다.' },
  ],
}

const HEAD = `대상: ${corpName || topic} (${stockCode})
콘텐츠 종류: ${contentKind}
장르 지침: ${CONTENT_GUIDANCE[contentKind] || CONTENT_GUIDANCE['company-reports']}
주제 힌트: ${topic}
최근 발행 제목(관통선·프레임 겹치면 감점): ${recent}`

// Phase 1: 경합(적대 토론)
phase('경합')
const LENSES = LENSES_BY_KIND[contentKind] || LENSES_BY_KIND['company-reports']
const proposals = await parallel(
  LENSES.map(({ role, lens }) => () =>
    agent(
      `너는 dartlab 블로그 ${role}다. 아래 회사에서 독자가 진짜 궁금해할 관통선 1개를 네 렌즈로 세운다.

${HEAD}
배정 렌즈(이 각도로만): ${lens}

${NOTES.principles}

검증된 데이터(숫자는 오직 이 안에서만. 새 숫자 지어내기 금지):
${evidence}

네 렌즈로 가장 강한 관통선 1개와 그 답(twistFact), 막 제목 스케치를 낸다. 다른 역할과 겹치지 않게 네 각도를 밀어라.`,
      { label: `${role} 제안`, phase: '경합', schema: PROPOSAL_SCHEMA }
    )
  )
)
const props = proposals.filter(Boolean)

const critiques = await parallel([
  () => agent(
    `너는 dartlab 블로그 회의론자다. 아래 두 관통선을 "템플릿 클리셰"로 격파하는 게 임무다. 동어반복("수요 레버리지"), K수출 상투("남이 열어준 문"), "좋은 회사인데 비싸다"류, 이미 널리 도는 서사면 clicheKills 에 적고 verdict=kill. 둘 다 진짜 의외면 survive. 더 강한 각이 보이면 strongerAngle 에 적는다.

${HEAD}
${NOTES.principles}

검증 데이터:
${evidence}

관통선 후보:
${JSON.stringify(props)}`,
    { label: '회의론자', phase: '경합', schema: CRITIQUE_SCHEMA }
  ),
  () => agent(
    `너는 dartlab 블로그 독자대리인이다. 비전문가 독자로서 이 관통선들이 재미있고 끝까지 궁금한지 검사한다. 첫 질문만으로 읽고 싶은가, 중간에 지루해질 지점은 어디인가를 funNotes 에 적는다. 재미가 살면 survive, 죽으면 kill.

${HEAD}

관통선 후보:
${JSON.stringify(props)}`,
    { label: '독자대리인', phase: '경합', schema: CRITIQUE_SCHEMA }
  ),
])

let plan = await agent(
  `너는 dartlab 블로그 편집장이다. 장르별 전문가의 관통선 경합과 회의론자·독자대리인의 격파를 읽고, 발행할 심층 리포트 한 편의 완전한 기획안으로 수렴한다.

${HEAD}

${NOTES.principles}

${NOTES.section}

${NOTES.visual}

${NOTES.image}

검증된 데이터(숫자는 오직 이 안에서만):
${evidence}

관통선 경합:
${JSON.stringify(props)}

회의론자·독자대리인 격파:
${JSON.stringify(critiques.filter(Boolean))}

단일 관통선 1개로 좁히고(클리셰 격파 반영), 후보 제목 3개 이상을 비교해 최종 제목을 고른 뒤 titleContract 를 채운다. 핵심 인싸이트(관통선의 답)를 세우고, 막 구조(6막+, 관통선이 인싸이트에 착지)·섹션별 독해 구조(sections)·막별 비주얼·이미지 기획(내용 연상, 로고·상징품 허용)·relatedPosts(검색어·링크·배치 규칙)·DART/EDGAR/dartlab/scan/price/macro/internal-blog evidenceMap·정직성 가드를 확정한다. 비주얼과 이미지는 글 뒤 부록이 아니라 본문 중간에서 독자의 이해를 바꾸는 장치로 placement·insertAfter·narrativeUse 까지 결정한다. 통과용 안전한 관통선이 아니라 진짜 의외의 관통선을 고른다. 전체 기획안을 스키마대로 낸다.

${FIELD_GUIDE}`,
  { label: '편집장 수렴', phase: '경합', schema: PLAN_SCHEMA }
)

// Phase 2: 평가개선(독자 루프)
phase('평가개선')
const loopLog = []
let passed = false
for (let round = 1; round <= MAX_ROUNDS; round++) {
  const [reader, skeptic] = await parallel([
    () => agent(
      `너는 dartlab 블로그 독자 에이전트다(비전문가 실독자). 이 기획안이 실제 글이 됐을 때를 상상해 6항목으로 깐다. 도장 찍지 마라. score 0~100, ${PASS_MIN} 미만이면 decision=revise. 약점은 findings 에 구체적으로.

${NOTES.principles}

${NOTES.section}

7항목: 1.재밌나(YES/NO+이유) 2.어디서 집중 끊기나 3.독자질문(관통선)이 끝까지 살아있나 4."어?" 몇 번 5.기억에 남는 문장 6.직관적으로 읽히나 7.점수. 특히: 제목이 첫 1초에 멈추는가, titleContract 의 후보·독자 갭·선택 이유가 살아있는가, 관통선이 끝까지 살아 인싸이트에 착지하나, 막이 궁금증심화·메커니즘·리스크반전·판단닫힘 중 하나를 하나, 깊이가 얕지 않나, 첫 2문단이 긴장으로 시작하나. sections[] 가 섹션마다 타이틀, 훅, 시각 앵커, 설명, 예시, 보완, 다음 연결을 실제로 기획했나. dartlab 이야기는 각 섹션이 코드·출력 표·계정·기간·값 중 하나에서 출발하나. "구조", "흐름", "표면", "경계", "맥락", "감각" 같은 말이 실제 화면 없이 떠 있지 않나. 비주얼이 본문 중간에서 설명을 실제로 돕나, 아니면 뒤에 자동으로 붙는 부록처럼 보이나. relatedPosts 가 선행 글 검색과 자연스러운 참고글 연결을 기획했나.

검증 데이터(기획 수치는 이 안에 있어야):
${evidence}

기획안:
${JSON.stringify(plan)}`,
      { label: `독자평가 r${round}`, phase: '평가개선', schema: READER_SCHEMA }
    ),
    () => agent(
      `너는 dartlab 블로그 회의자(skeptic)다. 임무는 통과가 아니라 이 기획안을 죽이는 것. 기본값 kill. 아래 하드 축 중 하나라도 걸리면 verdict=kill 과 kills[]. 다 깨끗하면 survive.

- weak-title: 제목이 설명형·총정리형·반복 템플릿이거나, 독자가 끝까지 따라갈 질문을 만들지 못하는가.
- cliche-template: 관통선·프레임이 템플릿 클리셰·동어반복·재탕인가.
- forced-metric: "이런 뜻은 아니다" 변명해야 하는 억지 비율·지표가 있나.
- misleading-frame: 주인공이 제목의 실제 주어와 다른가(인프라 회사를 AI 주인공으로 둔갑 등). 영업이익과 순이익, 연결과 그룹을 뭉갰나.
- shallow: 막이 요약 나열이라 메커니즘까지 안 파는가. 심층인 척 얕은가.
- abstract-writing: 설명이 코드·표·값보다 먼저 오거나, "구조", "흐름", "표면", "경계", "맥락", "감각", "역할" 같은 말이 실제 화면 없이 떠 있나.
- weak-section-flow: sections[] 가 없거나, 섹션마다 타이틀, 훅, 시각 앵커, 설명, 예시, 보완, 다음 연결이 기획되지 않았나.
- generic-image: imagePlan 이미지가 내용·회사·제품을 연상시키지 않고 범용 스카이라인·추상인가. 하나라도 있으면 kill.
- appendix-visual: visuals/imagePlan 이 본문 중간 placement 없이 뒤에 자동으로 붙는 부록처럼 기획됐나. 필요한 표·그래프·테이블 조합을 빼먹었나. 그러면 kill.
- weak-reference: relatedPosts 가 비어 있거나, 선행 글 검색어·링크 배치 이유 없이 억지 내부 링크만 붙였나.
- overclaim: 동행을 인과로 단정, 과장·투자권유·우열 단정이 있나.

검증 데이터:
${evidence}

기획안:
${JSON.stringify(plan)}`,
      { label: `회의자 r${round}`, phase: '평가개선', schema: SKEPTIC_SCHEMA }
    ),
  ])
  const readerPass = reader && reader.decision === 'pass' && reader.score >= PASS_MIN
  const skepticPass = skeptic && skeptic.verdict === 'survive'
  passed = Boolean(readerPass && skepticPass)
  loopLog.push({
    round, score: reader && reader.score, decision: reader && reader.decision, huhCount: reader && reader.huhCount,
    skeptic: skeptic && skeptic.verdict, kills: (skeptic && skeptic.kills) || [], findings: (reader && reader.findings) || [], passed,
  })
  if (passed && round >= 2) break
  if (round === MAX_ROUNDS) break
  plan = await agent(
    `너는 dartlab 블로그 기획작가다. 독자 평가자와 회의자가 약점을 잡았다. 둘 다 모두 반영해 기획안을 다시 쓴다(전체 스키마 재출력). 통과가 목적이 아니라 진짜 좋은 심층 리포트가 목적이다. 회의자가 죽인 축은 표면 수정이 아니라 제목·관통선·프레임·깊이·이미지를 실제로 바꿔 살려라.

${HEAD}

${NOTES.principles}

${NOTES.section}

${NOTES.visual}

${NOTES.image}

검증 데이터(숫자는 이 안에서만):
${evidence}

독자 평가자 지적(전부 반영):
${JSON.stringify((reader && reader.findings) || [])}

회의자가 죽인 하드 축(전부 살려라):
${JSON.stringify((skeptic && skeptic.kills) || [])}

직전 기획안:
${JSON.stringify(plan)}

개선된 전체 기획안을 스키마대로 낸다.

${FIELD_GUIDE}`,
    { label: `기획작가 개선 r${round}`, phase: '평가개선', schema: PLAN_SCHEMA }
  )
}

plan.reviewGate = {
  status: passed ? 'passed' : 'planned',
  requiredRounds: [
    { id: 'titleHook', status: passed ? 'passed' : 'todo' },
    { id: 'writerPanel', status: passed ? 'passed' : 'todo' },
    { id: 'honestyEvidence', status: passed ? 'passed' : 'todo' },
    { id: 'sectionFlow', status: passed ? 'passed' : 'todo' },
    { id: 'visualStoryPlan', status: passed ? 'passed' : 'todo' },
    { id: 'imageFit', status: passed ? 'passed' : 'todo' },
    { id: 'readerFit', status: passed ? 'passed' : 'todo' },
    { id: 'reevaluation', status: passed ? 'passed' : 'todo' },
  ],
  decisionLog: loopLog.map((r) => ({
    round: `r${r.round}`,
    decision: r.passed ? 'passed' : 'revise',
    note: JSON.stringify({ score: r.score, findings: r.findings || [], kills: r.kills || [] }),
  })),
  loopEvidence: {
    workflow: 'blog_plan_loop.workflow.js',
    rounds: loopLog.map((r) => ({
      round: r.round,
      planner: r.round === 1 ? '기획작가 초안' : '기획작가 개선안',
      evaluator: JSON.stringify({ score: r.score, decision: r.decision, huhCount: r.huhCount, findings: r.findings || [] }),
      skeptic: JSON.stringify({ verdict: r.skeptic, kills: r.kills || [] }),
      decision: r.passed ? 'passed' : 'revise',
      evaluatorScore: r.score || 0,
      plannerRevision: r.passed ? '최종 통과안' : '평가자와 회의자 지적을 반영해 다음 라운드에서 재작성',
    })),
    note: '작가기획, 평가 피드백, 작가 재기획, 재평가 루프 실행 산물. 최종 92점 이상만 발행',
  },
}

return { plan, loopLog, passed, rounds: loopLog.length, corpName, stockCode, contentKind }
