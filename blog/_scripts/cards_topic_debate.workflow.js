// 카드뉴스 주제 토론 (구조화된 오케스트레이션, durable SSOT)
//
// 운영자가 고정 주제 대신 "관심 영역"만 줄 때, 기획작가 패널이 후보 주제를 서로 다른 각도로 제안하고,
// 토론(독립 옹호/반박)으로 깎은 뒤, 최강 주제 1개 + 타입 + 뽑을 데이터 목록으로 수렴한다.
// 산물(chosen.dataNeeds)은 메인 스레드가 dartlab 직독으로 evidence 를 모으는 입력이 된다.
// 그 다음 cards_plan_loop.workflow.js(기획 루프)로 넘어간다.
//
// 실행: Workflow({ scriptPath: "blog/_scripts/cards_topic_debate.workflow.js",
//                  args: { interest, typeHint, recentTopics } })
//   interest: 운영자의 관심 영역(자유 문장).  typeHint: 'company'|'economy'|'theme'|'auto'(기본 auto).
//   recentTopics: 최근 발행 슬러그/주제 배열(겹침 회피용, 선택).
// 산물: { chosen:{topic,type,angle,why,dataNeeds[]}, runnerUp, candidates[] }
// 문서 SSOT: operation.content.

export const meta = {
  name: 'cards-topic-debate',
  description: '카드뉴스 주제 토론: 관심 영역에서 기획작가 패널이 후보 제안 후 토론, 최강 주제와 타입으로 수렴',
  phases: [
    { title: '제안', detail: '기획작가 4인이 서로 다른 각도로 후보 주제 제안' },
    { title: '토론', detail: '평가자 3인이 독립 옹호/반박' },
    { title: '수렴', detail: '최강 주제 + 타입 + 데이터 목록 확정' },
  ],
}

const DATA_NOTE = `dartlab 데이터 가용성(데이터 확보 가능성 판단용): 한국 상장사 DART 재무·공시, 미국 상장사 EDGAR 재무, 거시지표(금리·환율·물가 등), scan(성장·수익성 등 횡단 랭킹), 신규수주·세그먼트. 가격 시계열. 후보 주제는 이 데이터로 실측 그래프를 뽑을 수 있어야 한다. 뽑기 어려운 주제(여론·미공개·정성)는 감점.`

const PRINCIPLES_BRIEF = `좋은 카드 주제의 잠재력: (1)통념과 충돌하는 의외의 사실을 dartlab 실측으로 세울 수 있다 (2)그래프로 증명 가능하고 분기로 밀도 있게 그릴 수 있다 (3)최근 발행과 겹치지 않는 신선함 (4)비전문가도 1초에 궁금해할 호기심 (5)다 보고 나면 세계를 다르게 보게 됨. 회사 잘했다식 요약, 뻔한 결론(돈 받치는 동안만 간다 등)은 약하다.`

const TYPES = `타입: company(회사 하나가 주인공) / economy(거시·경제 흐름이 주인공) / theme(특정 주제를 여러 회사·지표 횡단으로). typeHint가 auto면 주제에 가장 맞는 타입을 고른다.`

const PROPOSAL_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['candidates'],
  properties: {
    candidates: {
      type: 'array', minItems: 2, maxItems: 2,
      items: {
        type: 'object', additionalProperties: false,
        required: ['topic', 'type', 'angle', 'twistHypothesis', 'dataNeeds', 'freshness'],
        properties: {
          topic: { type: 'string', description: '카드 제목형 주제 한 줄.' },
          type: { type: 'string', enum: ['company', 'economy', 'theme'] },
          angle: { type: 'string', description: '어떤 각도로 푸나.' },
          twistHypothesis: { type: 'string', description: '세울 수 있을 법한 통념 충돌 사실 가설.' },
          dataNeeds: { type: 'array', items: { type: 'string' }, description: 'dartlab으로 뽑을 구체 데이터(예: Company.panel 삼성전자 IS 분기).' },
          freshness: { type: 'string', description: '최근편과 어떻게 다른가.' },
        },
      },
    },
  },
}

const CRITIQUE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['pickTopic', 'why', 'rejectTopic', 'rejectWhy'],
  properties: {
    pickTopic: { type: 'string', description: '후보 중 가장 강한 것 하나.' },
    why: { type: 'string' },
    rejectTopic: { type: 'string', description: '가장 약한 것 하나.' },
    rejectWhy: { type: 'string' },
  },
}

const FINAL_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['chosen', 'runnerUp', 'rationale'],
  properties: {
    chosen: {
      type: 'object', additionalProperties: false, required: ['topic', 'type', 'angle', 'why', 'dataNeeds'],
      properties: {
        topic: { type: 'string' },
        type: { type: 'string', enum: ['company', 'economy', 'theme'] },
        angle: { type: 'string' },
        why: { type: 'string' },
        dataNeeds: { type: 'array', items: { type: 'string' } },
      },
    },
    runnerUp: {
      type: 'object', additionalProperties: false, required: ['topic', 'why'],
      properties: { topic: { type: 'string' }, why: { type: 'string' } },
    },
    rationale: { type: 'string' },
  },
}

// Workflow 는 args 를 JSON 문자열로 넘긴다. 객체로 파싱해 쓴다.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const interest = A.interest
const typeHint = A.typeHint || 'auto'
const recent = Array.isArray(A.recentTopics) ? A.recentTopics.join(', ') : (A.recentTopics || '없음')

const LENSES = [
  '돈의 흐름(누가 벌고 누가 쓰나, 현금·투자·마진)',
  '시간의 반전(전에는 이랬는데 지금은 정반대가 된 추세)',
  '숨은 연결(서로 무관해 보이는 둘이 같은 돈/원인으로 묶임)',
  '체감의 격차(뉴스 헤드라인과 공시 실측이 어긋나는 지점)',
]

phase('제안')
const proposalSets = await parallel(
  LENSES.map((lens, i) => () =>
    agent(
      `너는 dartlab 카드뉴스 기획작가다. 운영자 관심 영역에서 카드뉴스 주제 후보 2개를 제안한다.

운영자 관심 영역: "${interest}"
배정된 각도(이 렌즈로만 발상): ${lens}
타입 힌트: ${typeHint}

${TYPES}
${PRINCIPLES_BRIEF}
${DATA_NOTE}
최근 발행(겹치면 감점): ${recent}

배정된 각도로만 발상해 다른 작가와 겹치지 않게 한다. 후보 2개를 스키마대로 낸다.`,
      { label: `기획작가 제안 ${i + 1}`, phase: '제안', schema: PROPOSAL_SCHEMA }
    )
  )
)
const candidates = proposalSets.filter(Boolean).flatMap((r) => r.candidates)

phase('토론')
const critiques = await parallel(
  [0, 1, 2].map((i) => () =>
    agent(
      `너는 dartlab 카드뉴스 전문 평가자다. 아래 후보 주제들을 좋은 카드 잠재력으로 비교한다. 가장 강한 것 하나를 골라 옹호하고, 가장 약한 것 하나를 반박한다.

${PRINCIPLES_BRIEF}
${DATA_NOTE}
최근 발행(겹치면 감점): ${recent}

후보들:
${JSON.stringify(candidates)}

너만의 독립 판단으로 고른다(다른 평가자 눈치 보지 마라).`,
      { label: `평가자 토론 ${i + 1}`, phase: '토론', schema: CRITIQUE_SCHEMA }
    )
  )
)

phase('수렴')
const final = await agent(
  `너는 dartlab 카드뉴스 편집장이다. 기획작가들의 후보와 평가자들의 토론을 읽고 발행할 주제 하나를 확정한다.

운영자 관심 영역: "${interest}"
${TYPES}
${PRINCIPLES_BRIEF}
${DATA_NOTE}
최근 발행(겹치면 감점): ${recent}

후보들:
${JSON.stringify(candidates)}

평가자 토론:
${JSON.stringify(critiques.filter(Boolean))}

최강 주제 1개를 고르고, 타입을 정하고, 메인 스레드가 dartlab으로 뽑을 구체 데이터 목록(dataNeeds)을 적는다. 차점도 한 줄 남긴다. 통과용 안전한 주제가 아니라 진짜 의외의 주제를 고른다.`,
  { label: '편집장 수렴', phase: '수렴', schema: FINAL_SCHEMA }
)

return { chosen: final.chosen, runnerUp: final.runnerUp, rationale: final.rationale, candidates }
