// 카드뉴스 기획 루프 (구조화된 오케스트레이션, durable SSOT)
//
// 기획작가 agent 가 전체 기획안(인사이트·스파인·그래프·배경이미지·렌더계약)을 쓰면, 매 라운드
// 독립 두 심사가 동시에 깐다: (1) 전문 평가자가 5대원칙으로 점수, (2) 적대적 회의자(skeptic)가
// 인사이트를 죽이려 든다(재탕·억지수치·틀린프레임·일반이미지·과장). 둘 다 통과해야 합격(pass).
// 통과 못 하면 둘의 지적을 모두 반영해 재작성. 숫자는 메인 스레드 dartlab 직독으로 args.evidence 주입.
//
// 실행: Workflow({ scriptPath: "blog/_scripts/cards_plan_loop.workflow.js",
//                  args: { topic, cardType, evidence } })
//   cardType: 'company' | 'economy' | 'theme'  (기본 'theme')
// 산물: { plan, loopLog, passed, rounds }  (passed=false 면 발행 금지. plan 을 carousel.yaml + cards.plan.json 로 저작)
// 문서 SSOT: operation.content. 발행 게이트 SSOT: blog/_scripts/cards_plan.py.

export const meta = {
  name: 'cards-plan-loop',
  description: '카드뉴스 기획 루프: 기획작가 초안 → 평가자(5원칙)+회의자(적대적 인사이트 사냥) 동시 심사, 둘 다 통과까지 반복',
  phases: [
    { title: '기획', detail: '기획작가가 검증 데이터로 전체 기획안 초안(이미지 포함)' },
    { title: '평가개선', detail: '평가자+회의자 동시 심사 후 기획작가 개선, 둘 다 통과까지 반복' },
  ],
}

const PRINCIPLES = `카드뉴스 5대원칙(합격선):
1. 맥락: 큰문장만 위에서 아래로 읽어도 한 편의 짧은 글로 완결. 각 장은 앞장보다 질문을 하나 얹거나 갚는다. 순서 바꿔도 말 되면 실패.
2. 인사이트: 통념과 충돌하는 사실 + 왜 가능한가(메커니즘) + 앞으로 무엇을 다르게 볼까(렌즈)까지. 제목 재진술이면 실패. 다 읽고도 세계관 그대로면 실패. 추가 강행:
   (a) 재탕 금지: 이미 널리 도는 서사의 재포장이면 실패. 금융 좀 아는 독자가 "들어본 얘기"라 하면 실패(예: 'AI 순환 거래', '하이퍼스케일러 capex가 곧 엔비디아 매출'은 2024~2025년 닳은 서사다).
   (b) 억지 수치 금지: 핀 코멘트나 본문에서 "이런 뜻은 아니다"라고 변명해야 하는 비율·지표는 인사이트가 약한 것이다. 변명이 필요하면 실패.
   (c) 프레임 정직: 주인공이 제목의 실제 주어와 일치해야 한다. 인프라에 돈 쓰는 회사를 'AI 주인공'으로 둔갑시키지 마라(진짜 AI 주자=GPT·Claude·Gemini, 인프라=엔비디아·하이퍼스케일러를 섞지 마라).
3. 시각 정합: 주장 카드에는 그 주장을 증명하는 시각(그래프)이 붙는다. 큰문장을 가려도 그래프만으로 같은 긴장이 남아야 한다.
4. 쉬움: 소리 내어 읽어 자연스러운 한국어. 설명 안 한 약어 금지(AI는 인공지능, capex는 설비투자로 푼다). 긴 맥락 뒤 짧은 단언으로 리듬.
5. 재미·호기심·히트: 표지가 1초에 멈추는 호기심 갭(답은 숨김). 마지막은 표지 약속을 갚는 판단으로 닫음. 매 장이 완결돼 넘길 이유 없으면 실패.
6. 배경이미지: 회사명을 말하는 슬라이드의 배경은 그 회사의 실제 로고·제품·상호를 기본값으로 박는다. 주식·재무·교육 카드라 저작권 무관. 일반 장면(generic 팹·웨이퍼·데이터센터·추상 glow)으로 도망가면 차별성 0이라 실패. 회사가 특정 안 되는 개념 슬라이드만 일반 장면 허용. 그래프 슬라이드는 그래프가 시각물이라 배경을 비운다.
작가 craft: 표지 후크(결핍 제시·정답 숨김), 약속과 보상(표지 promise를 마지막이 payoff), 구체 장면화(비율을 사람이 그릴 단위로), 신뢰(주장 옆에 분모·기간 밝힌 실측 수치), 정직한 의외성(놀라움은 표현 아니라 숨은 사실에서. 우열·투자권유·단정 금지).
표기 규칙: em dash(긴 줄표) 금지. 부연은 마침표나 괄호로. 문장은 다/요/까로 끝낸다.`

const CONTRACTS = `렌더 계약 레지스트리(기획에서 그래프 모양까지 설계, 없으면 toBuild에 신설 선언):
- finCard: 인라인 재무그래프. series[{name,type:'bar'|'line',data:[]}] + periods:[]. 시계열은 항상 밀도 있게(분기 6점 이상, 빈 값/구멍 금지, data 길이=periods 길이). 추이는 line, 비교/구성은 bar.
- table: cols:[] + data:[{}]. 작은 수치 표.
- 필요한 시각이 위에 없으면 renderContracts.toBuild 에 '계약명: 무엇을 그리나 + 왜 기존 계약으로 안 되나'를 적는다(파이프라인이 그 계약을 신설하도록).`

const TYPE_GUIDANCE = {
  company: '타입 company: 회사 하나가 주인공. 그 회사 공시 직독으로 통념을 깨는 반전 하나를 세운다. 그래프는 그 회사의 분기 시계열. 배경은 그 회사 로고·제품.',
  economy: '타입 economy: 거시·경제 흐름이 주인공. 추상 지표를 사람이 체감하는 단위로 번역한다. 여러 지표를 횡단하되 한 줄기 이야기로.',
  theme: '타입 theme: 특정 주제가 주인공(회사 하나로 좁히지 않는다). 여러 회사·지표를 횡단해 주제를 증명한다. 개별 회사는 주제를 재는 계기로 쓰되, 그 회사를 말하는 장의 배경은 그 회사 로고·제품으로.',
}

const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'insight', 'spine', 'visuals', 'images', 'renderContracts'],
  properties: {
    title: { type: 'string' },
    insight: {
      type: 'object', additionalProperties: false,
      required: ['commonBelief', 'twistFact', 'whatToWatch', 'freshnessArgument', 'evidenceRefs'],
      properties: {
        commonBelief: { type: 'string' },
        twistFact: { type: 'string', description: '통념과 충돌하는 사실 + 메커니즘. 제목 재진술 금지. 뻔한 소리 금지. 변명해야 하는 억지 수치 금지.' },
        whatToWatch: { type: 'string' },
        freshnessArgument: { type: 'string', description: '왜 이게 이미 도는 서사의 재탕이 아닌가. 이 데이터에서 새로 나온 지점을 한 문장으로. 재탕이면 통과 못 한다.' },
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
    images: {
      type: 'array',
      description: '슬라이드별 배경 이미지 기획. spine 의 각 order 와 1:1. 회사명을 말하는 장은 그 회사 로고·제품을 박는다.',
      items: {
        type: 'object', additionalProperties: false, required: ['order', 'subjectCompany', 'bg'],
        properties: {
          order: { type: 'integer' },
          subjectCompany: { type: 'string', description: '이 장이 주인공으로 말하는 회사명. 특정 회사가 없으면 빈 문자열.' },
          bg: { type: 'string', description: 'subjectCompany 가 있으면 그 회사 로고·제품·상호 지시(일반 장면 금지). 없으면 개념 장면. 그래프 장이면 "(배경 없음)".' },
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

const SKEPTIC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdict', 'kills'],
  properties: {
    verdict: { type: 'string', enum: ['survive', 'kill'] },
    kills: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['axis', 'why', 'fix'],
        properties: {
          axis: { type: 'string', enum: ['recycled', 'forced-metric', 'misleading-frame', 'generic-image', 'overclaim'] },
          why: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

// Workflow 는 args 를 JSON 문자열로 넘긴다. 객체로 파싱해 쓴다.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const topic = A.topic
const evidence = A.evidence
const cardType = A.cardType || 'theme'
const typeNote = TYPE_GUIDANCE[cardType] || TYPE_GUIDANCE.theme
const PASS_MIN = 85

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
- 인사이트는 재탕 금지. 이미 도는 서사면 실패다. freshnessArgument 에 "왜 재탕이 아닌가"를 못 적으면 인사이트를 바꿔라. 변명해야 하는 억지 비율 금지. 프레임은 제목의 실제 주어와 일치(인프라 회사를 AI 주인공으로 둔갑 금지).
- 그래프는 기획에서 모양까지 설계. 시계열은 분기로 밀도 있게(6점 이상), 빈 값 금지, data 길이=periods 길이. 추이는 line.
- images: spine 의 각 장에 배경을 기획한다. 회사명을 말하는 장은 subjectCompany 에 그 회사명, bg 에 그 회사 로고·제품·상호를 박는다(일반 장면 금지). 회사 특정 안 되는 개념 장만 일반 장면. 그래프 장은 "(배경 없음)".
- 8~10장. 큰문장만 읽어도 한 편으로 완결. 표지는 호기심 갭, 마지막은 판단으로 닫음.
- 약어 풀기. em dash 금지. 문장은 다/요/까로 끝냄.

전체 기획안을 스키마대로 낸다.`,
  { label: '기획작가 초안', phase: '기획', schema: PLAN_SCHEMA }
)

phase('평가개선')
const loopLog = []
let verdict = null
let skeptic = null
let passed = false
const MAX_ROUNDS = 4
for (let round = 1; round <= MAX_ROUNDS; round++) {
  const [v, s] = await parallel([
    () => agent(
      `너는 dartlab 카드뉴스 전문 평가자다(편집장·스캔독해·정직성 에디터 겸). 아래 기획안을 5대원칙으로 깐다. 도장 찍지 마라. 약점을 구체적으로 잡고 고칠 방법을 적어라. 하나라도 합격선 미달이면 decision=revise.

타입(${cardType}) 지침: ${typeNote}

${PRINCIPLES}

검증 데이터(기획안의 모든 숫자는 이 안에 있어야 한다. 없는 숫자가 있으면 정직성 위반):
${evidence}

특히 깐다:
- 인사이트가 재탕인가(이미 도는 서사). 통념-반전-렌즈-메커니즘이 다 살아있고 의외인가. freshnessArgument 가 진짜 새 지점인가.
- 변명해야 하는 억지 수치가 있나. 프레임이 제목 실제 주어와 일치하나.
- 타입 지침을 어겼는가. 그래프가 주장을 증명하고 밀도 있나(분기 6점+), 큰문장 가려도 긴장이 남나.
- 큰문장만 읽어 한 편으로 완결되나, 표지가 1초에 멈추나, 마지막이 표지 약속을 갚나.
- 회사명을 말하는 장의 배경이 그 회사 로고·제품인가(일반 장면이면 시각정합·재미 감점).
- 숫자가 전부 검증 데이터 안에 있나, 과장·투자권유·단정 없나, 분모·기간 정직한가.
scores는 0~100. 5개 중 하나라도 ${PASS_MIN} 미만이면 revise.

기획안:
${JSON.stringify(plan)}`,
      { label: `평가자 r${round}`, phase: '평가개선', schema: VERDICT_SCHEMA }
    ),
    () => agent(
      `너는 dartlab 카드뉴스 회의자(skeptic)다. 네 임무는 통과시키는 게 아니라 이 인사이트를 죽이는 것이다. 기본값은 kill. 아래 다섯 축을 다 통과해야만 survive 다. 하나라도 걸리면 verdict=kill 과 kills[](축·이유·고칠방법)를 낸다.

- recycled: 인사이트가 이미 널리 도는 서사의 재포장인가. 금융 좀 아는 독자가 "들어본 얘기"라 하면 kill. (예: 'AI 순환 거래', 'capex가 곧 엔비디아 매출' 류)
- forced-metric: 핀 코멘트나 본문에서 "이런 뜻은 아니다"라고 변명해야 하는 억지 비율·지표가 있나. 있으면 kill.
- misleading-frame: 주인공이 제목의 실제 주어와 다른가. 인프라에 돈 쓰는 회사를 'AI 주인공'으로 둔갑시켰나. 그러면 kill.
- generic-image: 회사명을 말하는 장의 배경(images[].bg)이 그 회사 로고·제품이 아니라 일반 장면인가. 하나라도 있으면 kill.
- overclaim: 동행을 인과로 단정하거나 과장·투자권유·우열 단정이 있나. 있으면 kill.

검증 데이터:
${evidence}

기획안:
${JSON.stringify(plan)}`,
      { label: `회의자 r${round}`, phase: '평가개선', schema: SKEPTIC_SCHEMA }
    ),
  ])
  verdict = v
  skeptic = s
  const minScore = verdict ? Math.min(...Object.values(verdict.scores)) : 0
  const evalPass = verdict && verdict.decision === 'pass' && minScore >= PASS_MIN
  const skepticPass = skeptic && skeptic.verdict === 'survive'
  passed = evalPass && skepticPass
  loopLog.push({
    round, decision: verdict && verdict.decision, scores: verdict && verdict.scores, minScore,
    skeptic: skeptic && skeptic.verdict, kills: (skeptic && skeptic.kills) || [],
    findings: (verdict && verdict.findings) || [], rationale: verdict && verdict.rationale, passed,
  })
  if (passed) break
  if (round === MAX_ROUNDS) break
  plan = await agent(
    `너는 dartlab 카드뉴스 기획작가다. 평가자와 회의자가 약점을 잡았다. 둘 다 모두 반영해 기획안을 다시 쓴다(전체 스키마 재출력). 통과가 목적이 아니라 진짜 좋은 카드가 목적이다. 회의자가 죽인 축은 표면 수정이 아니라 인사이트·프레임·이미지를 실제로 바꿔서 살려라.

타입(${cardType}) 지침: ${typeNote}

${PRINCIPLES}

${CONTRACTS}

검증 데이터(숫자는 이 안에서만):
${evidence}

평가자 지적(전부 반영):
${JSON.stringify(verdict.findings)}
평가자 총평: ${verdict.rationale}

회의자가 죽인 축(전부 살려라):
${JSON.stringify(skeptic.kills)}

직전 기획안:
${JSON.stringify(plan)}

개선된 전체 기획안을 스키마대로 낸다.`,
    { label: `기획작가 개선 r${round}`, phase: '평가개선', schema: PLAN_SCHEMA }
  )
}

return { plan, loopLog, passed, rounds: loopLog.length, cardType }
