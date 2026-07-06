// 팟캐스트 기획 루프 (NotebookLM 소스 문서 생성, durable SSOT)
//
// 우리 파이프라인은 오디오를 만들지 않는다. NotebookLM 이 오디오 개요로 바꿀 "완결 산문 소스 문서"
// (기획서 script.md)를 만든다. 기획작가 agent 가 소스 문서를 쓰면, 매 라운드 독립 두 심사가 동시에
// 깐다: (1) 전문 평가자가 6대원칙으로 점수, (2) 적대적 회의자(skeptic)가 억지수치·틀린프레임·과장·
// 외부의존을 죽이려 든다. 둘 다 통과해야 합격. 숫자는 메인 스레드 dartlab 직독으로 args.evidence 주입.
//
// 실행: Workflow({ scriptPath: "blog/_podcasts/_lib/podcast_plan_loop.workflow.js",
//                  args: { topic, lane, evidence } })
//   lane: 'dartlab' | 'company' | 'economy' | 'disclosure' | 'quant'  (기본 'company')
// 산물: { plan, loopLog, passed, rounds, lane }  (passed=false 면 발행 금지)
//   plan.sections 를 blog/_podcasts/_lib/plan_episode.py 로 script.md + episode.yaml 로 저작한다.
// 발행 게이트 SSOT: blog/_podcasts/README.md. 발행자: blog/_podcasts/_lib/publish_podcast.py.

export const meta = {
  name: 'podcast-plan-loop',
  description: '팟캐스트 기획 루프: 기획작가가 NotebookLM 소스 문서 초안 -> 평가자(6원칙)+회의자(적대적) 동시 심사, 둘 다 통과까지 반복',
  phases: [
    { title: '기획', detail: '기획작가가 검증 데이터로 완결 산문 소스 문서 초안' },
    { title: '평가개선', detail: '평가자+회의자 동시 심사 후 기획작가 개선, 둘 다 통과까지 반복' },
  ],
}

const PRINCIPLES = `팟캐스트 소스 문서 6대원칙(합격선):
1. 완결·따라오기: 처음 듣는 사람도 따라오게 배경을 먼저 깔고, 오프닝에서 던진 질문을 클로징이 갚는다. 소제목만 훑어도 한 편의 논증으로 완결. 순서 바꿔도 말 되면 실패.
2. 인사이트: 통념과 충돌하는 사실 + 왜 가능한가(메커니즘) + 앞으로 무엇을 다르게 들을까(렌즈)까지. 제목 재진술이면 실패. 다 듣고도 세계관 그대로면 실패. 우열·투자권유·단정은 절대 금지.
3. 귀 정합: 이건 듣는 콘텐츠다. 모든 숫자에 분모·기간·비교대상을 문장으로 붙여 귀로만 이해되게 쓴다. "표를 보면" 같은 시각 의존 금지. 그래프 없이 말로 성립해야 한다.
4. 쉬움·담백: 소리 내어 읽어 자연스러운 한국어(다/요/까 종결). 설명 안 한 약어 금지(capex는 설비투자로 푼다. 단 AI는 일반어라 그대로). 허황된 비유·추상 표현 금지. 뜻을 비유로 감싸 두 번 들어야 하는 문장은 실패. 구체 주어(회사·숫자)에 사실을 붙이고, 앞 문장과 뒤 문장이 원인·결과로 딱 붙게 쓴다.
5. 재미·호기심: 오프닝이 궁금하게 멈추는 갭(답은 숨김). 클로징은 오프닝 약속을 판단으로 갚고, 다음에 확인할 지표(whereToLook) 2~3개로 닫는다. "앞으로 중요합니다" 식 공허한 마무리 금지.
6. 구조 독창성: 매 에피소드가 같은 뼈대를 반복하면 실패. 주제마다 고유한 뼈대를 찾는다. 보기: 가치사슬에서 진짜와 이름표만 가르기, 첫 매출까지의 시간표, 원인의 사슬, 승자와 패자의 분해, 널리 퍼진 오해 하나를 데이터로 정정. 직전 에피소드들과 뼈대가 겹치면 감점.
NotebookLM 적합성: 산출물은 NotebookLM 이 유일 소스로 진행자 2인 대담을 즉흥 생성할 "완결 산문 문서"다. 잘 먹음 = 소제목 있는 완결 산문·문맥 붙은 숫자·명시적 "하지 않는 말" 섹션. 안 먹음 = 불릿만·파편·외부 링크로 근거 미루기·문서 밖 지식 가정. 대담 대본(2인 배분)은 우리가 쓰지 않는다. 우리는 "무엇을 말할지" 완결 소스만 쓴다.
표기 규칙: em dash(긴 줄표) 금지. 부연은 마침표나 괄호로, 범위는 물결(~). 문장은 다/요/까로 끝낸다.`

const LANE_GUIDANCE = {
  dartlab: 'lane dartlab: DartLab 도구 자체가 주제. 무엇을 어떻게 해주는지 쉬운 말로. 회사 종목이 아니라 도구·데이터·방법론이 주인공. stockCode 는 빈 값.',
  company: 'lane company: 회사 하나가 주인공. 그 회사 공시 직독으로 통념을 깨는 반전 하나를 세운다. 숫자는 그 회사 분기 시계열을 말로 풀어 쓴다. episode.yaml 의 stockCode 는 6자리 필수.',
  economy: 'lane economy: 거시·경제 흐름이 주제. 추상 지표를 사람이 체감하는 단위로 번역한다. 여러 지표를 횡단하되 한 줄기 이야기로.',
  disclosure: 'lane disclosure: 공시·제도가 주제. 공시 원문에서 나오는 사실로 흔한 오해를 정정한다.',
  quant: 'lane quant: 퀀트·팩터가 주제. 내부어(OOS·Sharpe·MDD 등)를 쉬운 한국어로 풀어 귀로 이해되게 한다.',
}

const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'titlePlan', 'oneLineMessage', 'insight', 'sections', 'closingWhereToLook', 'forbiddenAngles'],
  properties: {
    title: { type: 'string', description: '에피소드 제목(RSS·오디오 개요). SEO+궁금증 규율: (1) 검색되는 고유명(회사명·티커·핵심 키워드)을 앞 15자 안에 둔다(모바일 검색은 앞부분만 노출). (2) 상식과 충돌하는 훅 또는 열린 질문("어떻게 ~했나", "~일까")으로 궁금증 갭을 열되 답은 숨긴다. (3) 핵심 숫자 1개(분모·기간 함의)로 구체화한다. (4) 낚시(내용 불일치)·목표가·확정전망·수익보장 금지. em dash 금지, 구분자는 콜론 또는 전각바(ㅣ). 예: "SK하이닉스: 다섯 번 죽을 뻔한 회사가 어떻게 AI 시대 이익률 58%를 찍었나". 유튜브 검색용 변형은 README 제목 규율 참조.' },
    titlePlan: {
      type: 'object', additionalProperties: false,
      required: ['candidates', 'selectedReason', 'rssTitle', 'youtubeTitle', 'uploadSlugCamel'],
      properties: {
        candidates: {
          type: 'array', minItems: 3,
          description: '제목 후보 3개 이상. 후보마다 훅, 검색 키워드, 버린 이유 또는 채택 이유를 쓴다.',
          items: {
            type: 'object', additionalProperties: false,
            required: ['title', 'hook', 'searchLead', 'verdict', 'reason'],
            properties: {
              title: { type: 'string' },
              hook: { type: 'string', description: '궁금증 갭. 답을 닫으면 실패.' },
              searchLead: { type: 'string', description: '앞 15자 안에 들어가는 검색 키워드.' },
              verdict: { type: 'string', enum: ['selected', 'rejected'] },
              reason: { type: 'string' },
            },
          },
        },
        selectedReason: { type: 'string', description: '채택 제목이 왜 가장 강한지. 클릭 훅과 정직성 둘 다 설명.' },
        rssTitle: { type: 'string', description: 'episode.yaml title 로 쓸 제목. 짧고 완결된 궁금증.' },
        youtubeTitle: { type: 'string', description: 'youtube.md 제목. 검색 키워드 앞, 60자 안팎, 낚시 금지.' },
        uploadSlugCamel: { type: 'string', description: '_uploads 파일명에 쓸 camelCase 영문 slug. 공백, 하이픈, 밑줄, 한글 금지.' },
      },
    },
    oneLineMessage: { type: 'string', description: '이 에피소드가 답하는 질문과 결론을 한 문장으로.' },
    insight: {
      type: 'object', additionalProperties: false,
      required: ['commonBelief', 'twistFact', 'whatToWatch', 'freshnessArgument', 'evidenceRefs'],
      properties: {
        commonBelief: { type: 'string' },
        twistFact: { type: 'string', description: '통념과 충돌하는 사실 + 메커니즘. 제목 재진술 금지. 변명해야 하는 억지 수치 금지.' },
        whatToWatch: { type: 'string' },
        freshnessArgument: { type: 'string', description: '왜 이게 이미 도는 서사의 재탕이 아닌가. 새로 나온 지점 한 문장.' },
        evidenceRefs: { type: 'array', items: { type: 'string' }, description: 'script 의 모든 숫자 출처(ref). 진행자 앵커용.' },
      },
    },
    sections: {
      type: 'array', minItems: 5,
      description: '완결 산문 소스 문서의 절. order 순서로 읽으면 한 편. 각 body 는 2~4문단의 산문(불릿 금지).',
      items: {
        type: 'object', additionalProperties: false, required: ['order', 'heading', 'body'],
        properties: {
          order: { type: 'integer' },
          heading: { type: 'string', description: '소제목 (예: 왜 지금 이 이야기인가, 배경, 핵심 사실, 다르게 보기, 정리와 다음).' },
          body: { type: 'string', description: '2~4문단 산문. 숫자에 분모·기간·비교대상을 문장으로. 시각 의존 금지.' },
        },
      },
    },
    closingWhereToLook: { type: 'array', items: { type: 'string' }, minItems: 2, description: '클로징이 남기는 확인점 2~3개.' },
    forbiddenAngles: { type: 'array', items: { type: 'string' }, description: '이 에피소드에서 하지 않는 말(매수/매도/목표가/수익 보장/확정 전망 등).' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['decision', 'scores', 'findings', 'rationale'],
  properties: {
    decision: { type: 'string', enum: ['pass', 'revise'] },
    scores: {
      type: 'object', additionalProperties: false, required: ['완결', '인사이트', '귀정합', '쉬움', '재미'],
      properties: { 완결: { type: 'integer' }, 인사이트: { type: 'integer' }, 귀정합: { type: 'integer' }, 쉬움: { type: 'integer' }, 재미: { type: 'integer' } },
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
  type: 'object', additionalProperties: false, required: ['verdict', 'kills', 'softNotes'],
  properties: {
    verdict: { type: 'string', enum: ['survive', 'kill'] },
    kills: {
      type: 'array',
      description: 'kill 사유. 네 하드 축만. 재탕(recycled)은 여기 넣지 않는다(소프트 권고).',
      items: {
        type: 'object', additionalProperties: false, required: ['axis', 'why', 'fix'],
        properties: {
          axis: { type: 'string', enum: ['forced-metric', 'misleading-frame', 'overclaim', 'external-dependency'] },
          why: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
    softNotes: { type: 'array', items: { type: 'string' }, description: '재탕 의심 등 권고. kill 사유 아님.' },
  },
}

// Workflow 는 args 를 JSON 문자열로 넘긴다. 객체로 파싱해 쓴다.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const topic = A.topic
const evidence = A.evidence
const lane = A.lane || 'company'
const laneNote = LANE_GUIDANCE[lane] || LANE_GUIDANCE.company
const PASS_MIN = 85

phase('기획')
let plan = await agent(
  `너는 dartlab 팟캐스트 기획작가다. 주제 "${topic}"로 NotebookLM 에 넣을 완결 산문 소스 문서를 쓴다. NotebookLM 이 이 문서 하나만 보고 진행자 2인 대담을 만든다. 그러니 문서 자체가 완결 논증이어야 하고 문서 밖 지식에 기대면 안 된다.

${laneNote}

${PRINCIPLES}

검증된 데이터(메인 스레드에서 dartlab 직독으로 확인. 숫자는 오직 이 안에서만 쓴다. 새 숫자 지어내기 금지):
${evidence}

지시:
- 위 lane 지침을 지킨다.
- 제목도 기획한다. titlePlan.candidates 는 최소 3개, 채택 1개와 기각 이유를 함께 낸다. rssTitle 은 title 과 같아야 한다. youtubeTitle 은 검색 키워드를 앞에 두고, uploadSlugCamel 은 _uploads 파일명에 바로 쓸 영문 camelCase 로 낸다.
- sections 는 완결 산문. 예시 흐름: (1) 왜 지금 이 이야기인가(오프닝 훅, 답 숨김) (2) 배경: 알아야 할 최소한 (3) 핵심 사실(반전과 메커니즘, 숫자에 분모·기간) (4) 다르게 보기(렌즈) (5) 정리와 다음(오프닝 약속을 갚고 whereToLook 로 닫음). 주제에 맞으면 뼈대를 바꿔도 된다.
- 본문 900~1500단어(한국어, 8~15분 오디오). 불릿 금지, 문단 산문. 시각 의존("표를 보면") 금지, 귀로만 이해되게.
- 약어 풀기(AI는 그대로). em dash 금지. 문장은 다/요/까로 끝냄.
- forbiddenAngles 에 이 편에서 하지 않는 말(투자권유·단정 등)을 명시한다.

전체 소스 문서를 스키마대로 낸다.`,
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
      `너는 dartlab 팟캐스트 전문 평가자다(편집장·회의적 청취자·정직성 에디터 겸). 아래 소스 문서를 6대원칙으로 깐다. 도장 찍지 마라. 약점을 구체적으로 잡고 고칠 방법을 적어라. 하나라도 합격선 미달이면 decision=revise.

lane(${lane}) 지침: ${laneNote}

${PRINCIPLES}

검증 데이터(문서의 모든 숫자는 이 안에 있어야 한다. 없는 숫자가 있으면 정직성 위반):
${evidence}

특히 깐다:
- 인사이트가 통념-반전-렌즈-메커니즘이 다 살아있고 의외인가. (재탕은 감점 요소지 단독 탈락 사유 아님.)
- 제목 후보 루프가 실제로 돌았나. titlePlan.candidates 가 3개 이상이고, rssTitle 이 title 과 일치하며, youtubeTitle 과 uploadSlugCamel 이 표면별 규율을 지키나.
- 귀로만 들어 이해되나. 시각 의존 표현이 있나. 숫자에 분모·기간·비교대상이 문장으로 붙나.
- 처음 듣는 사람이 따라오나, 오프닝이 궁금하게 멈추나, 클로징이 오프닝 약속을 갚고 whereToLook 로 닫나.
- 소제목만 훑어 한 편으로 완결되나. 문서 밖 지식에 기대지 않고 완결되나(NotebookLM 적합).
- 숫자가 전부 검증 데이터 안에 있나, 과장·투자권유·단정 없나.
scores는 0~100. 5개 중 하나라도 ${PASS_MIN} 미만이면 revise.

소스 문서:
${JSON.stringify(plan)}`,
      { label: `평가자 r${round}`, phase: '평가개선', schema: VERDICT_SCHEMA }
    ),
    () => agent(
      `너는 dartlab 팟캐스트 회의자(skeptic)다. 네 임무는 통과시키는 게 아니라 이 소스 문서를 죽이는 것이다. 기본값은 kill. 아래 네 하드 축 중 하나라도 걸리면 verdict=kill 과 kills[](축·이유·고칠방법)를 낸다. 네 축이 다 깨끗하면 survive.

- (소프트 권고) recycled: 인사이트가 이미 널리 도는 서사의 재포장 같으면 softNotes 에 적는다. 이것만으로는 kill 하지 않는다.
- forced-metric: "이런 뜻은 아니다"라고 변명해야 하는 억지 비율·지표가 있나. 있으면 kill.
- misleading-frame: 주인공이 제목의 실제 주어와 다른가. 동행을 인과로 둔갑시켰나. 그러면 kill.
- overclaim: 과장·투자권유·우열 단정·확정 전망이 있나. 있으면 kill.
- external-dependency: 문서가 문서 밖 지식·링크·시각물에 기대야만 이해되나(NotebookLM 이 유일 소스로 못 만듦). 그러면 kill.

검증 데이터:
${evidence}

소스 문서:
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
    skeptic: skeptic && skeptic.verdict, kills: (skeptic && skeptic.kills) || [], softNotes: (skeptic && skeptic.softNotes) || [],
    findings: (verdict && verdict.findings) || [], rationale: verdict && verdict.rationale, passed,
  })
  if (passed) break
  if (round === MAX_ROUNDS) break
  plan = await agent(
    `너는 dartlab 팟캐스트 기획작가다. 평가자와 회의자가 약점을 잡았다. 둘 다 모두 반영해 소스 문서를 다시 쓴다(전체 스키마 재출력). 통과가 목적이 아니라 진짜 좋은 에피소드가 목적이다. 회의자가 죽인 축은 표면 수정이 아니라 인사이트·프레임·문장을 실제로 바꿔서 살려라.

lane(${lane}) 지침: ${laneNote}

${PRINCIPLES}

검증 데이터(숫자는 이 안에서만):
${evidence}

평가자 지적(전부 반영):
${JSON.stringify(verdict.findings)}
평가자 총평: ${verdict.rationale}

회의자가 죽인 하드 축(전부 살려라):
${JSON.stringify(skeptic.kills)}
회의자 소프트 권고(가능하면 반영):
${JSON.stringify(skeptic.softNotes || [])}

직전 소스 문서:
${JSON.stringify(plan)}

개선된 전체 소스 문서를 스키마대로 낸다. 제목도 다시 기획한다. 기존 제목을 고집하지 말고 후보 3개를 다시 비교한 뒤 채택한다.`,
    { label: `기획작가 개선 r${round}`, phase: '평가개선', schema: PLAN_SCHEMA }
  )
}

return { plan, loopLog, passed, rounds: loopLog.length, lane }
