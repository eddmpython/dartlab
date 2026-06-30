// 뷰어 명령 버스 · 채팅(현재=결정론, 미래=모델 tool-call)이 뒷화면(공시뷰어)을 조작하는 단일 계약.
// 순수 타입 + executeAction 디스패처 + deriveActions 결정론 프로듀서. Svelte/$state 0 · 호스트가
// ViewerApi 로 자기 mutator 를 주입한다. 모든 변형은 executeAction 한 곳을 통과(라이브 상태 검증 게이트):
// 모델은 절대 Svelte state 를 직접 못 만지고 schema-제약 액션만 제안, 호스트가 검증·실행한다.
import type { SearchHit } from './searchIndex';
import type { CompanyHit } from './companyNames';
import type { Intent } from './answerCompose';

// ── 액션 스키마 · 채팅이 emit 하는 계약(JSON 직렬화 가능). 각 variant = 호스트 함수 1:1. ──
export type ViewerAction =
	| { kind: 'navigateCompany'; code: string; carryQ?: string }
	| { kind: 'focusEvidence'; hit: SearchHit }
	| { kind: 'setSection'; sectionKey: string }
	| { kind: 'setBlock'; sectionKey: string; leaf: string }
	| { kind: 'setPeriod'; period: string }
	| { kind: 'shiftWindow'; dir: 'newer' | 'older' }
	| { kind: 'setCols'; n: 3 | 6 | 9 }
	| { kind: 'toggleAnnual' }
	| { kind: 'openFinance' }
	| { kind: 'closeFinance' }
	| { kind: 'addCompare'; code: string }
	| { kind: 'removeCompare'; code: string };

export type ViewerActionKind = ViewerAction['kind'];

// 호스트(+page.svelte)가 주입하는 능력 집합 · 기존 mutator 1:1 + 검증용 라이브 상태 게터.
export interface ViewerApi {
	navigateCompany: (code: string, carryQ: string) => void;
	focusEvidence: (hit: SearchHit) => void;
	setSection: (sectionKey: string) => void;
	setBlock: (sectionKey: string, leaf: string) => void;
	setPeriod: (period: string) => void;
	moveNewer: () => void;
	moveOlder: () => void;
	setCols: (n: 3 | 6 | 9) => void;
	toggleAnnual: () => void;
	openFinance: () => void;
	closeFinance: () => void;
	addCompare: (code: string) => void;
	removeCompare: (code: string) => void;
	// 검증 게터(라이브 상태) · 환각·무효 차단
	hasSection: (sectionKey: string) => boolean;
	hasPeriod: (period: string) => boolean; // visiblePeriods 기준
	knownCode: (code: string) => boolean; // 데이터셋 보유 + self 아님
}

export interface ActionResult {
	ok: boolean;
	reason?: string; // 거부 사유(테스트·디버그·미래 모델 피드백)
}

// 단일 디스패처 · 라이브 상태 검증 후 호스트 mutator 호출. 무효면 no-op + reason. 여기만 뒷화면을 바꾼다.
export function executeAction(a: ViewerAction, api: ViewerApi): ActionResult {
	switch (a.kind) {
		case 'navigateCompany':
			if (!api.knownCode(a.code)) return { ok: false, reason: `unknown or self code: ${a.code}` };
			api.navigateCompany(a.code, a.carryQ ?? '');
			return { ok: true };
		case 'focusEvidence':
			if (!api.hasSection(a.hit.sectionKey)) return { ok: false, reason: `no section: ${a.hit.sectionKey}` };
			api.focusEvidence(a.hit);
			return { ok: true };
		case 'setSection':
			if (!api.hasSection(a.sectionKey)) return { ok: false, reason: `no section: ${a.sectionKey}` };
			api.setSection(a.sectionKey);
			return { ok: true };
		case 'setBlock':
			if (!api.hasSection(a.sectionKey)) return { ok: false, reason: `no section: ${a.sectionKey}` };
			api.setBlock(a.sectionKey, a.leaf);
			return { ok: true };
		case 'setPeriod':
			if (!api.hasPeriod(a.period)) return { ok: false, reason: `period not visible: ${a.period}` };
			api.setPeriod(a.period);
			return { ok: true };
		case 'shiftWindow':
			if (a.dir === 'newer') api.moveNewer();
			else api.moveOlder();
			return { ok: true };
		case 'setCols':
			api.setCols(a.n);
			return { ok: true };
		case 'toggleAnnual':
			api.toggleAnnual();
			return { ok: true };
		case 'openFinance':
			api.openFinance();
			return { ok: true };
		case 'closeFinance':
			api.closeFinance();
			return { ok: true };
		case 'addCompare':
			if (!api.knownCode(a.code)) return { ok: false, reason: `unknown or self code: ${a.code}` };
			api.addCompare(a.code); // addCompany 자체가 dup/>=6 가드 → 중복 가드 불필요(SSOT 1곳)
			return { ok: true };
		case 'removeCompare':
			api.removeCompare(a.code);
			return { ok: true };
	}
}

// ── 결정론 드라이버 · 질문 + 기존 휴리스틱 산출물 → 액션 목록. AI 0. ──
// 호출측(AskDrawer)이 이미 가진 resolveCompanies 결과·search hits·composeAnswer.intent 를 받아
// 액션으로 표현(로직 중복 0). 같은 액션 스키마를 나중에 모델이 emit → 동일 executeAction 통과.
export interface DeriveInput {
	q: string;
	targets: CompanyHit[]; // resolveCompanies(q, code) 결과
	hits: SearchHit[]; // search(index, q) 결과
	intent: Intent; // composeAnswer().intent
	topHit: SearchHit | null; // 답이 인용한 최상위 근거(있으면 자동 셀 점프)
	visiblePeriods: string[]; // 연도 토큰 검증용
}

const YEAR_RE = /(20\d{2})/;

export function deriveActions(input: DeriveInput): ViewerAction[] {
	const { q, targets, hits, intent, topHit, visiblePeriods } = input;
	void hits; // 현재 미사용(topHit 로 충분) · 시그니처 안정성 위해 입력엔 유지
	const out: ViewerAction[] = [];

	// (1) 타 회사 단일 감지 → 이동(원질문 carryQ). 이동이면 다른 액션 무의미(새 회사서 재실행) → 단독 반환.
	if (targets.length === 1) {
		return [{ kind: 'navigateCompany', code: targets[0].code, carryQ: q }];
	}
	// targets.length >= 2 (모호) → 액션 0 (AskDrawer 가 후보 칩 turn 으로 처리, 클릭 시 navigateCompany)

	// (2) 재무/비율 의도 → 재무 다이얼로그 열기(정량 표가 답의 자연 귀착지).
	if (intent === 'ratio') out.push({ kind: 'openFinance' });

	// (3) 답이 인용한 최상위 근거 → 자동 셀 점프(근거칩 클릭의 자동화: 섹션 이동 + 기간 + glow 한 방).
	if (topHit) out.push({ kind: 'focusEvidence', hit: topHit });

	// (4) 질문에 연도 토큰 + 그 기간이 보이면 → 그 시점으로 윈도 이동(명시 의도).
	const yr = q.match(YEAR_RE);
	if (yr) {
		const p = visiblePeriods.find((x) => x.startsWith(yr[1]));
		if (p) out.push({ kind: 'setPeriod', period: p });
	}
	return out;
}
