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
//                  args: { topic, corpName, stockCode, evidence, recentTitles } })
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
표기: em dash(긴 줄표) 금지. 부연은 마침표·괄호, 범위는 물결(~). 문장은 다/요/까.`

const IMAGE_NOTE = `이미지 기획(내용 연상 강제): hero 1장 + 본문 inline 2~3장 이상. inline 이미지는 뒤에 자동으로 붙는 장식이 아니라 어느 막의 어느 설명 뒤에 들어갈지 insertAfterAct·placement·narrativeUse 로 결정한다. 각 이미지는 무조건 이 글의 내용·회사·제품·현장을 연상시켜야 한다. 회사 로고·상징품·실제 제품도 허용(주식·재무·교육 맥락이라 저작권 무관). 범용 스카이라인·추상 배경으로 도망가면 실패. query 는 실사 CC0 수급용 영어 검색어(그 회사 제품·현장·상징을 앞에), keywords 는 제목/태그 매칭용(오매치 차단). 예(봉제완구 회사): query "plush stuffed animals teddy bear shelf", keywords ["plush","teddy","stuffed","toy"].`

const VISUAL_NOTE = `막별 비주얼: 이야기가 요구하는 차트·표·그래프 세트를 막마다 정한다(고정 템플릿 아님). 추이=line, 비교/구성=bar, 부문믹스=도넛/스택, 두 계열 대비=grouped, 공정·회사·근거 지도=table. 한 막에 하나로 부족하면 같은 actOrder 에 2~4개를 기획한다. 시각물은 글 뒤 자동 부록이 아니라 본문 중간 설명 장치다. placement·insertAfter·narrativeUse 로 어느 문장 뒤에 왜 들어가는지 적는다. 각 차트는 그 막의 주장을 증명해야 하고, 큰 숫자를 가려도 차트만으로 같은 긴장이 남아야 한다. 손수 못생긴 차트 금지. kind·title·proves·seriesHint 를 명확히 적어 메인 스레드가 정식 렌더로 그리게 한다.`

const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'titleContract', 'description', 'readerQuestion', 'insight', 'acts', 'visuals', 'imagePlan', 'honestyGuards', 'evidenceMap'],
  properties: {
    title: { type: 'string', description: '제목(60자 이하, 회사명 앞·궁금증 갭). 예: "오로라월드, 매출은 2배가 됐는데 이익은 왜 널뛸까".' },
    titleContract: {
      type: 'object', additionalProperties: false,
      required: ['workingTitle', 'selectedTitle', 'hookQuestion', 'readerGap', 'promise', 'whySelected', 'candidates', 'rejectedPatterns'],
      properties: {
        workingTitle: { type: 'string' },
        selectedTitle: { type: 'string', description: '최종 선택 제목. title 과 같아야 한다.' },
        hookQuestion: { type: 'string', description: '제목이 첫 1초에 만들 독자 질문.' },
        readerGap: { type: 'string', description: '독자의 기존 상식과 글이 갚을 사실 사이의 간격.' },
        promise: { type: 'string', description: '제목이 약속하고 결론이 갚을 내용.' },
        whySelected: { type: 'string', description: '왜 다른 후보보다 이 제목이 더 강한가.' },
        candidates: {
          type: 'array', minItems: 3,
          items: {
            type: 'object', additionalProperties: false, required: ['title', 'hook', 'risk'],
            properties: {
              title: { type: 'string' },
              hook: { type: 'string' },
              risk: { type: 'string' },
            },
          },
        },
        rejectedPatterns: { type: 'array', items: { type: 'string' } },
      },
    },
    description: { type: 'string', description: 'SEO description(80~200자). 첫 2줄이 검색 스니펫.' },
    readerQuestion: { type: 'string', description: '관통선 = 독자 질문 1개. 제목 없이 이 질문만으로 읽고 싶어야 함.' },
    insight: {
      type: 'object', additionalProperties: false,
      required: ['commonBelief', 'twistFact', 'whatToWatch', 'freshnessArgument', 'evidenceRefs'],
      properties: {
        commonBelief: { type: 'string', description: '시장·대중의 통념.' },
        twistFact: { type: 'string', description: '핵심 인싸이트 = 관통선의 답. 통념과 충돌하는 사실 + 메커니즘. 제목 재진술·억지 수치 금지.' },
        whatToWatch: { type: 'string', description: '다음 공시에서 볼 지표(이 인싸이트가 맞는지 검증할 곳).' },
        freshnessArgument: { type: 'string', description: '왜 이미 도는 서사의 재탕이 아닌가.' },
        evidenceRefs: { type: 'array', items: { type: 'string' }, description: '이 인싸이트를 받치는 dartlab 실측 근거(evidence 안에서).' },
      },
    },
    acts: {
      type: 'array', minItems: 6,
      description: '막 구조. order 순으로 읽으면 한 편. 관통선이 인싸이트에 필연적으로 착지.',
      items: {
        type: 'object', additionalProperties: false, required: ['order', 'heading', 'purpose', 'scene', 'keyNumbers', 'causalBridge'],
        properties: {
          order: { type: 'integer' },
          heading: { type: 'string', description: 'H2 소제목(고유·궁금증형).' },
          purpose: { type: 'string', enum: ['배경', '궁금증심화', '메커니즘공개', '리스크반전', '판단닫힘'] },
          scene: { type: 'string', description: '이 막의 장면(제품·공장·공시·자본배분 중 하나). 보고서톤 금지.' },
          keyNumbers: { type: 'array', items: { type: 'string' }, description: '이 막에서 쓸 dartlab 실측 수치(evidence 안에서).' },
          causalBridge: { type: 'string', description: '다음 막으로 넘어가는 인과 다리 1문장.' },
        },
      },
    },
    visuals: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['actOrder', 'kind', 'title', 'proves', 'placement', 'insertAfter', 'narrativeUse'],
        properties: {
          actOrder: { type: 'integer', description: '어느 막에 붙나.' },
          kind: { type: 'string', description: 'line|bar|grouped|donut|stack|table 등.' },
          title: { type: 'string' },
          proves: { type: 'string', description: '이 차트가 증명하는 주장.' },
          seriesHint: { type: 'string', description: '어떤 계열·기간(evidence 기준).' },
          placement: { type: 'string', description: '본문 안 위치. 예: act 3 middle, after mechanism paragraph.' },
          insertAfter: { type: 'string', description: '어떤 설명·문장 뒤에 삽입할지.' },
          narrativeUse: { type: 'string', description: '독자가 이 시각물을 보고 어떤 이해를 얻어야 하는지.' },
        },
      },
    },
    imagePlan: {
      type: 'array', minItems: 3,
      description: '내용 연상 이미지 기획(로고·상징품 허용). hero 1 + inline 2~3.',
      items: {
        type: 'object', additionalProperties: false, required: ['slot', 'subject', 'query', 'keywords', 'placement', 'narrativeUse'],
        properties: {
          slot: { type: 'string', enum: ['hero', 'inline'] },
          subject: { type: 'string', description: '무엇을 연상시키나(회사 제품·현장·상징).' },
          query: { type: 'string', description: '실사 CC0 수급용 영어 검색어(그 회사 제품·현장·상징 앞에).' },
          keywords: { type: 'array', items: { type: 'string' }, description: '제목/태그 매칭용 키워드(오매치 차단).' },
          insertAfterAct: { type: 'integer', description: 'inline 이미지면 어느 막 뒤에 삽입할지. hero 는 0.' },
          placement: { type: 'string', description: 'hero 또는 본문 안 위치.' },
          narrativeUse: { type: 'string', description: '이 이미지가 독자의 이해를 어떻게 돕는지.' },
        },
      },
    },
    honestyGuards: { type: 'array', items: { type: 'string' }, description: '이 글에 적용할 정직성 가드(영업이익 vs 순이익 분리 등).' },
    evidenceMap: {
      type: 'array', minItems: 3,
      description: '본문에 쓸 DART/EDGAR/dartlab/scan 근거 지도. 숫자·공시 위치·기간·어느 막에서 쓰는지까지 적는다.',
      items: {
        type: 'object', additionalProperties: false, required: ['claim', 'sourceType', 'period', 'sourceRef', 'howUsed'],
        properties: {
          claim: { type: 'string', description: '이 근거가 받치는 주장.' },
          sourceType: { type: 'string', enum: ['DART', 'EDGAR', 'dartlab', 'scan', 'external'] },
          period: { type: 'string', description: '연도·분기·표본 기간. EDGAR는 fiscal year/quarter를 명시.' },
          sourceRef: { type: 'string', description: 'DART 보고서·EDGAR 10-K/10-Q·dartlab 호출·scan 축.' },
          howUsed: { type: 'string', description: '어느 막/시각물에서 어떻게 쓰는지.' },
        },
      },
    },
  },
}

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
          axis: { type: 'string', enum: ['weak-title', 'cliche-template', 'forced-metric', 'misleading-frame', 'shallow', 'generic-image', 'appendix-visual', 'overclaim'] },
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

const CONTENT_GUIDANCE = {
  'company-reports': `기업이야기: 회사 하나의 내러티브를 깊게 판다. 사업 구조, 공시 문장, 제품·고객·수주·원가·자본배치·현금흐름을 한 회사 안에서 연결한다. DART 또는 EDGAR 근거와 dartlab 실측을 분리하고, 다음 공시에서 볼 렌즈로 닫는다.`,
  'tech-story': `기술이야기: 기술이 주어다. 기술 원리, 공정 파이프라인·네트워크망, 어느 칸에 어떤 회사가 있고 왜 그 회사가 병목·표준·원가·고객 접점을 쥐는지 설명한다. 한국사는 DART, 미국사는 EDGAR를 연결한다. 돈 이야기만 앞세우거나 "누가 돈을 버나" 템플릿이면 실패다.`,
  'data-reports': `데이터 리포트: scan과 전종목 파서로 전체 시장의 특이점을 찾는다. 개별 회사는 대표 사례일 뿐이다. 표본·분모·제외 조건·정제 전후를 드러내고, DART·EDGAR 전체 유니버스 또는 제외 사유를 명시한다. 순위표 나열로 끝나면 실패다.`,
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

${PRINCIPLES}

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
${PRINCIPLES}

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

${PRINCIPLES}

${VISUAL_NOTE}

${IMAGE_NOTE}

검증된 데이터(숫자는 오직 이 안에서만):
${evidence}

관통선 경합:
${JSON.stringify(props)}

회의론자·독자대리인 격파:
${JSON.stringify(critiques.filter(Boolean))}

단일 관통선 1개로 좁히고(클리셰 격파 반영), 후보 제목 3개 이상을 비교해 최종 제목을 고른 뒤 titleContract 를 채운다. 핵심 인싸이트(관통선의 답)를 세우고, 막 구조(6막+, 관통선이 인싸이트에 착지)·막별 비주얼·이미지 기획(내용 연상, 로고·상징품 허용)·DART/EDGAR/dartlab/scan evidenceMap·정직성 가드를 확정한다. 비주얼과 이미지는 글 뒤 부록이 아니라 본문 중간에서 독자의 이해를 바꾸는 장치로 placement·insertAfter·narrativeUse 까지 결정한다. 통과용 안전한 관통선이 아니라 진짜 의외의 관통선을 고른다. 전체 기획안을 스키마대로 낸다.`,
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

${PRINCIPLES}

6항목: 1.재밌나(YES/NO+이유) 2.어디서 집중 끊기나 3.독자질문(관통선)이 끝까지 살아있나 4."어?" 몇 번 5.기억에 남는 문장 6.점수. 특히: 제목이 첫 1초에 멈추는가, titleContract 의 후보·독자 갭·선택 이유가 살아있는가, 관통선이 끝까지 살아 인싸이트에 착지하나, 막이 궁금증심화·메커니즘·리스크반전·판단닫힘 중 하나를 하나, 깊이가 얕지 않나, 첫 2문단이 긴장으로 시작하나. 비주얼이 본문 중간에서 설명을 실제로 돕나, 아니면 뒤에 자동으로 붙는 부록처럼 보이나.

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
- generic-image: imagePlan 이미지가 내용·회사·제품을 연상시키지 않고 범용 스카이라인·추상인가. 하나라도 있으면 kill.
- appendix-visual: visuals/imagePlan 이 본문 중간 placement 없이 뒤에 자동으로 붙는 부록처럼 기획됐나. 필요한 표·그래프·테이블 조합을 빼먹었나. 그러면 kill.
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

${PRINCIPLES}

${VISUAL_NOTE}

${IMAGE_NOTE}

검증 데이터(숫자는 이 안에서만):
${evidence}

독자 평가자 지적(전부 반영):
${JSON.stringify((reader && reader.findings) || [])}

회의자가 죽인 하드 축(전부 살려라):
${JSON.stringify((skeptic && skeptic.kills) || [])}

직전 기획안:
${JSON.stringify(plan)}

개선된 전체 기획안을 스키마대로 낸다.`,
    { label: `기획작가 개선 r${round}`, phase: '평가개선', schema: PLAN_SCHEMA }
  )
}

plan.reviewGate = {
  status: passed ? 'passed' : 'planned',
  requiredRounds: [
    { id: 'titleHook', status: passed ? 'passed' : 'todo' },
    { id: 'writerPanel', status: passed ? 'passed' : 'todo' },
    { id: 'honestyEvidence', status: passed ? 'passed' : 'todo' },
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
