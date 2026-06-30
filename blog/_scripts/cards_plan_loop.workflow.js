// 카드뉴스 기획 루프 (구조화된 오케스트레이션, durable SSOT)
//
// 기획작가 agent 가 전체 기획안(인사이트·스파인·그래프·렌더계약)을 쓰면, 전문 평가자 agent 가
// 5대원칙으로 비평하고 재작성을 강제한다. 그 피드백을 기획작가가 받아 다시 쓴다. 통과(pass)까지 루프.
// 숫자는 메인 스레드 dartlab 직독으로 검증해 args.evidence 로 주입한다(에이전트 숫자 환각 방지).
//
// 실행: Workflow({ scriptPath: "blog/_scripts/cards_plan_loop.workflow.js",
//                  args: { topic, cardType, evidence } })
//   cardType: 'company' | 'economy' | 'theme'  (기본 'theme')
// 산물: { plan, loopLog, passed, rounds }  (plan 을 carousel.yaml + cards.plan.json 로 저작)
// 문서 SSOT: operation.content. 발행 게이트 SSOT: blog/_scripts/cards_plan.py.

export const meta = {
  name: 'cards-plan-loop',
  description: '카드뉴스 기획 루프: 기획작가가 전체 기획안을 쓰고 전문 평가자가 5대원칙으로 비평, 통과까지 반복(타입 인식)',
  phases: [
    { title: '기획', detail: '기획작가가 검증 데이터로 전체 기획안 초안' },
    { title: '평가개선', detail: '평가자 비평 후 기획작가 개선, 통과까지 반복' },
  ],
}

const PRINCIPLES = `카드뉴스 5대원칙(합격선):
1. 맥락: 큰문장만 위에서 아래로 읽어도 한 편의 짧은 글로 완결. 각 장은 앞장보다 질문을 하나 얹거나 갚는다. 순서 바꿔도 말 되면 실패.
2. 인사이트: 통념과 충돌하는 사실 + 왜 가능한가(메커니즘) + 앞으로 무엇을 다르게 볼까(렌즈)까지. 제목 재진술이면 실패. 다 읽고도 세계관 그대로면 실패. 누구나 하는 뻔한 소리는 실패.
3. 시각 정합: 주장 카드에는 그 주장을 증명하는 시각(그래프)이 붙는다. 큰문장을 가려도 그래프만으로 같은 긴장이 남아야 한다.
4. 쉬움: 소리 내어 읽어 자연스러운 한국어. 설명 안 한 약어 금지(AI는 인공지능, capex는 설비투자로 푼다). 긴 맥락 뒤 짧은 단언으로 리듬.
5. 재미·호기심·히트: 표지가 1초에 멈추는 호기심 갭(답은 숨김). 마지막은 표지 약속을 갚는 판단으로 닫음. 매 장이 완결돼 넘길 이유 없으면 실패.
작가 craft: 표지 후크(결핍 제시·정답 숨김), 약속과 보상(표지 promise를 마지막이 payoff), 구체 장면화(비율을 사람이 그릴 단위로), 신뢰(주장 옆에 분모·기간 밝힌 실측 수치), 정직한 의외성(놀라움은 표현 아니라 숨은 사실에서. 우열·투자권유·단정 금지).
표기 규칙: em dash(긴 줄표) 금지. 부연은 마침표나 괄호로. 문장은 다/요/까로 끝낸다.`

const CONTRACTS = `렌더 계약 레지스트리(기획에서 그래프 모양까지 설계, 없으면 toBuild에 신설 선언):
- finCard: 인라인 재무그래프. series[{name,type:'bar'|'line',data:[]}] + periods:[]. 시계열은 항상 밀도 있게(분기 6점 이상, 빈 값/구멍 금지, data 길이=periods 길이). 추이는 line, 비교/구성은 bar.
- table: cols:[] + data:[{}]. 작은 수치 표.
- 필요한 시각이 위에 없으면 renderContracts.toBuild 에 '계약명: 무엇을 그리나 + 왜 기존 계약으로 안 되나'를 적는다(파이프라인이 그 계약을 신설하도록).`

const TYPE_GUIDANCE = {
  company: '타입 company: 회사 하나가 주인공. 그 회사 공시 직독으로 통념을 깨는 반전 하나를 세운다. 그래프는 그 회사의 분기 시계열.',
  economy: '타입 economy: 거시·경제 흐름이 주인공. 추상 지표를 사람이 체감하는 단위로 번역한다. 여러 지표를 횡단하되 한 줄기 이야기로.',
  theme: '타입 theme: 특정 주제가 주인공(회사 하나로 좁히지 않는다). 여러 회사·지표를 횡단해 주제를 증명한다. 개별 회사는 주제를 재는 계기로만 쓴다.',
}

const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'insight', 'spine', 'visuals', 'renderContracts'],
  properties: {
    title: { type: 'string' },
    insight: {
      type: 'object', additionalProperties: false,
      required: ['commonBelief', 'twistFact', 'whatToWatch', 'evidenceRefs'],
      properties: {
        commonBelief: { type: 'string' },
        twistFact: { type: 'string', description: '통념과 충돌하는 사실 + 메커니즘. 제목 재진술 금지. 뻔한 소리 금지.' },
        whatToWatch: { type: 'string' },
        evidenceRefs: { type: 'array', items: { type: 'string' } },
      },
    },
    spine: {
      type: 'array', minItems: 8,
      items: {
        type: 'object', additionalProperties: false, required: ['order', 'layout', 'bigSentence'],
        properties: {
          order: { type: 'integer' },
          layout: { type: 'string', enum: ['editorial', 'editorialBeat', 'editorialStat'] },
          bigSentence: { type: 'string' },
          sub: { type: 'string' },
          visualOrder: { type: 'integer' },
        },
      },
    },
    visuals: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['order', 'kind', 'proves'],
        properties: {
          order: { type: 'integer' },
          kind: { type: 'string' },
          title: { type: 'string' },
          unit: { type: 'string' },
          periods: { type: 'array', items: { type: 'string' } },
          series: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false, required: ['name', 'type', 'data'],
              properties: { name: { type: 'string' }, type: { type: 'string', enum: ['bar', 'line'] }, data: { type: 'array', items: { type: 'number' } } },
            },
          },
          proves: { type: 'string' },
        },
      },
    },
    renderContracts: {
      type: 'object', additionalProperties: false, required: ['used', 'toBuild'],
      properties: { used: { type: 'array', items: { type: 'string' } }, toBuild: { type: 'array', items: { type: 'string' } } },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['decision', 'scores', 'findings', 'rationale'],
  properties: {
    decision: { type: 'string', enum: ['pass', 'revise'] },
    scores: {
      type: 'object', additionalProperties: false, required: ['맥락', '인사이트', '시각정합', '쉬움', '재미'],
      properties: { 맥락: { type: 'integer' }, 인사이트: { type: 'integer' }, 시각정합: { type: 'integer' }, 쉬움: { type: 'integer' }, 재미: { type: 'integer' } },
    },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['principle', 'problem', 'fix'],
        properties: { principle: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } },
      },
    },
    rationale: { type: 'string' },
  },
}

// Workflow 는 args 를 JSON 문자열로 넘긴다. 객체로 파싱해 쓴다.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const topic = A.topic
const evidence = A.evidence
const cardType = A.cardType || 'theme'
const typeNote = TYPE_GUIDANCE[cardType] || TYPE_GUIDANCE.theme

phase('기획')
let plan = await agent(
  `너는 dartlab 카드뉴스 기획작가다. 주제 "${topic}"로 카드뉴스 한 편의 완전한 기획안을 짠다.

${typeNote}

${PRINCIPLES}

${CONTRACTS}

검증된 데이터(메인 스레드에서 dartlab 직독으로 확인. 숫자는 오직 이 안에서만 쓴다. 새 숫자 지어내기 금지):
${evidence}

지시:
- 위 타입 지침을 지킨다.
- 인사이트는 뻔한 소리 금지. 데이터가 말하는 의외의 사실을 찾아라.
- 그래프는 기획에서 모양까지 설계한다. 시계열은 분기로 밀도 있게(6점 이상), 빈 값 금지, data 길이=periods 길이. 추이는 line.
- 8~10장. 큰문장만 읽어도 한 편으로 완결. 표지는 호기심 갭, 마지막은 판단으로 닫음.
- 약어 풀기. em dash 금지. 문장은 다/요/까로 끝냄.

전체 기획안을 스키마대로 낸다.`,
  { label: '기획작가 초안', phase: '기획', schema: PLAN_SCHEMA }
)

phase('평가개선')
const loopLog = []
let verdict = null
const MAX_ROUNDS = 4
for (let round = 1; round <= MAX_ROUNDS; round++) {
  verdict = await agent(
    `너는 dartlab 카드뉴스 전문 평가자다(편집장·스캔독해·정직성 에디터 겸). 아래 기획안을 5대원칙으로 깐다. 도장 찍지 마라. 약점을 구체적으로 잡고 고칠 방법을 적어라. 하나라도 합격선 미달이면 decision=revise.

타입(${cardType}) 지침: ${typeNote}

${PRINCIPLES}

검증 데이터(기획안의 모든 숫자는 이 안에 있어야 한다. 없는 숫자가 있으면 정직성 위반):
${evidence}

특히 깐다:
- 인사이트가 뻔한가. 통념-반전-렌즈-메커니즘이 다 살아있고 의외인가.
- 타입 지침을 어겼는가(theme인데 회사 하나로 좁혔다 등).
- 그래프가 주장을 증명하나, 밀도 있나(분기 6점+), 큰문장 가려도 그래프만으로 긴장이 남나.
- 큰문장만 읽어 한 편으로 완결되나, 표지가 1초에 멈추나, 마지막이 표지 약속을 갚나.
- 숫자가 전부 검증 데이터 안에 있나, 과장·투자권유·단정 없나, 분모·기간 정직한가.
scores는 0~100. 5개 중 하나라도 80 미만이면 revise.

기획안:
${JSON.stringify(plan)}`,
    { label: `평가자 r${round}`, phase: '평가개선', schema: VERDICT_SCHEMA }
  )
  loopLog.push({ round, decision: verdict.decision, scores: verdict.scores, findings: verdict.findings, rationale: verdict.rationale })
  if (verdict.decision === 'pass') break
  if (round === MAX_ROUNDS) break
  plan = await agent(
    `너는 dartlab 카드뉴스 기획작가다. 평가자가 약점을 잡았다. 모두 반영해 기획안을 다시 쓴다(전체 스키마 재출력). 통과가 목적이 아니라 진짜 좋은 카드가 목적이다.

타입(${cardType}) 지침: ${typeNote}

${PRINCIPLES}

${CONTRACTS}

검증 데이터(숫자는 이 안에서만):
${evidence}

평가자 지적(전부 반영):
${JSON.stringify(verdict.findings)}
총평: ${verdict.rationale}

직전 기획안:
${JSON.stringify(plan)}

개선된 전체 기획안을 스키마대로 낸다.`,
    { label: `기획작가 개선 r${round}`, phase: '평가개선', schema: PLAN_SCHEMA }
  )
}

return { plan, loopLog, passed: verdict && verdict.decision === 'pass', rounds: loopLog.length, cardType }
