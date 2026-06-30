// 관점 5종 · 같은 회사를 5개 렌즈로(투자자 질문 축으로 분리). 데이터 작업대 리얼타임.
// built=false 는 후속 사이클에서 리얼타임 구현(현재는 정직 '준비 중' 표기).
export interface PerspectiveMeta {
	key: string;
	label: string;
	question: string; // 한 줄 정의 · 투자자가 답을 얻는 질문
	focusQuestions: string[];
	built: boolean;
}

export const PERSPECTIVES: PerspectiveMeta[] = [
	{
		key: 'earningsPower',
		label: '수익성',
		question: '수익의 규모와 질',
		focusQuestions: ['매출과 이익은 어떻게 움직였나', '마진은 개선되나', '이익이 현금으로 돌아오나'],
		built: true
	},
	{
		key: 'liquidity',
		label: '재무안정성',
		question: '부채 부담과 현금흐름',
		focusQuestions: ['현금은 어떻게 도나', '부채 상환 여력은', '재무건전성은 견고한가'],
		built: true
	},
	{
		key: 'capitalReturn',
		label: '주주환원',
		question: '주주 환원과 주식 희석',
		focusQuestions: ['배당은 얼마나', '자사주는 소각하나 적립하나', '주식 희석 이력'],
		built: true
	},
	{
		key: 'market',
		label: '시장평가',
		question: '시장의 가치 평가',
		focusQuestions: ['주가는 어떻게 움직였나', '시장과 얼마나 동행하나', '이익 대비 얼마에 거래되나'],
		built: true
	},
	{
		key: 'ownership',
		label: '지배구조',
		question: '소유구조와 회계 신뢰성',
		focusQuestions: ['소유구조는 어떠한가', '인력과 보상은', '회계는 신뢰할 만한가'],
		built: true
	}
];

export function findPerspective(key: string): PerspectiveMeta {
	return PERSPECTIVES.find((p) => p.key === key) ?? PERSPECTIVES[0];
}
