// 도구 표시명. 내부 도구 id 를 그대로 노출하지 않고 한국어 한 낱말로 바꾼다.
// 예전에는 과정 요약과 도구 카드가 같은 표를 따로 들고 있어 한쪽만 늘어났다. 표는 여기 하나뿐이다.

const TOOL_LABELS: Record<string, string> = {
	RunPython: '코드 실행',
	'run python': '코드 실행',
	EngineCall: '엔진 호출',
	'engine call': '엔진 호출',
	ReadSkill: '스킬 조회',
	'read skill': '스킬 조회',
	GetSkillBody: '스킬 본문',
	ReadCapability: 'API 조회',
	'read capability': 'API 조회',
	WebSearch: '웹 검색',
	'web search': '웹 검색',
	Read: '파일 인용',
	SaveArtifact: '산출물 저장',
	CompileVisual: '차트 생성',
	CompileFinancialDashboard: '재무 대시보드',
	PeerCompareN: '동종사 비교',
	DCFValuation: 'DCF 가치평가',
	SensitivityAnalysis: '민감도 분석',
	ScenarioCompareN: '시나리오 비교',
	ScenarioOverlay: '시나리오 오버레이',
	CreditScorecard: '신용 스코어카드',
	RegressionForecast: '회귀 예측',
	SearchPastSessions: '과거 세션 검색',
	// 광고 목록에 있는데 표에 없어 영어 내부 id 가 그대로 화면에 뜨던 것들.
	ReadSkillMarket: '스킬 마켓 검색',
	ExternalReachDoctor: '외부 조사 점검',
	CreateUserSkill: '사용자 스킬 작성',
	Verify: '근거 검증',
	verify: '근거 검증'
};

/** 표에 없으면 원본 이름 그대로. 모르는 이름을 지어내지 않는다. */
export function toolLabel(name: string): string {
	return TOOL_LABELS[name] ?? name;
}

/** 경과 시간 한 낱말. 1 초 미만은 굳이 소수점을 보이지 않는다. */
export function durationLabel(durationMs: number | null): string {
	if (durationMs === null || durationMs < 0) return '';
	if (durationMs < 1000) return `${durationMs}ms`;
	const seconds = durationMs / 1000;
	return seconds < 10 ? `${seconds.toFixed(1)}초` : `${Math.round(seconds)}초`;
}
