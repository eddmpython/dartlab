// 결정론 답변 조립기 (Tier 0) · 질문 의도 분류 + financeSignals/search/constraint 출력을 인용 달린
// 한국어 완성문으로 조립한다. 0모델·0다운로드·환각 0(숫자는 결정론 SSOT 직접). 공시뷰어 질문의 다수
// (숫자·추세·유무·규모·조건)는 여기서 즉답된다. LLM(Tier 1)은 "왜?/종합/본문해석" 소수에만 opt-in.
//
// 재사용: searchIndex.parseConstraint, diff.FinanceSignal. 새 데이터구조 0 · 기존 출력 필드만 소비.

import { parseConstraint, type SearchHit } from './searchIndex';
import type { FinanceSignal } from './diff';

export type Intent = 'constraint' | 'ratio' | 'trend' | 'flip' | 'magnitude' | 'existence' | 'lookup';

export interface ComposeResult {
	intent: Intent;
	answer: string; // 결정론 한국어 답 (lookup 은 안내 문구)
	citedSignal: FinanceSignal | null; // 재무 인용(있으면 칩으로 다이얼로그 연결)
	suggestLlm: boolean; // "왜/종합/해석" → LLM 확장 권유
}

function won(v: number): string {
	const a = Math.abs(v);
	const sign = v < 0 ? '-' : '';
	if (a >= 1e12) return `${sign}${(a / 1e12).toFixed(2)}조`;
	if (a >= 1e8) return `${sign}${(a / 1e8).toFixed(1)}억`;
	if (a >= 1e4) return `${sign}${(a / 1e4).toFixed(0)}만`;
	return `${sign}${a.toLocaleString()}`;
}

// bounded 의도 패턴 · 끝없이 늘면 덕지덕지 신호(searchIndex.parseConstraint 규율과 동일).
const FLIP_RE = /전환|흑자|적자|돌아|마이너스|손실로/;
const TREND_RE = /추세|증감|늘|줄|변화|증가|감소|성장|하락|개선|악화|나아|어때|어떻/;
const MAG_RE = /규모|얼마|금액|총액|몇\s*(억|조|원)|수준|크기|많/;
const EXIST_RE = /있나|있는지|여부|존재|했나|하나요|있습니까|없나|있어/;
const WHY_RE = /왜|이유|원인|때문|배경|어째/;
const SYNTH_RE = /종합|전반|평가|요약|설명|정리|건전|어떤\s*회사|투자/;

// 재무비율 · 분자/분모 계정을 financeSignals 에서 찾아 동일기간 나눠 산출(생성 아닌 계산). label = 표준화 계정명.
// 매출은 업종별 드리프트(제조 '매출액' vs 금융/IT '영업수익')라 분모 후보 2개. bounded · 끝없이 늘면 덕지덕지.
interface RatioDef {
	key: string;
	numer: string[];
	denom: string[];
}
const REVENUE_LABELS = ['매출액', '영업수익'];
const RATIO_TRIGGERS: RatioDef[] = [
	{ key: '부채비율', numer: ['부채총계'], denom: ['자본총계'] },
	{ key: '자기자본비율', numer: ['자본총계'], denom: ['자산총계'] },
	{ key: '유동비율', numer: ['유동자산'], denom: ['유동부채'] },
	{ key: '영업이익률', numer: ['영업이익'], denom: REVENUE_LABELS },
	{ key: '순이익률', numer: ['당기순이익'], denom: REVENUE_LABELS }
];
const RATIO_RE = new RegExp(RATIO_TRIGGERS.map((r) => r.key).join('|'));

export function classifyIntent(q: string, hasConstraint: boolean): Intent {
	if (hasConstraint) return 'constraint';
	if (RATIO_RE.test(q.replace(/\s/g, ''))) return 'ratio'; // 비율 먼저 · "영업이익률"이 trend(영업이익)로 새지 않게
	if (FLIP_RE.test(q)) return 'flip';
	if (TREND_RE.test(q)) return 'trend';
	if (MAG_RE.test(q)) return 'magnitude';
	if (EXIST_RE.test(q)) return 'existence';
	return 'lookup';
}

// 질문어 → 재무계정 매칭 (label 부분일치 + 경량 동의어). 더 구체(긴) 라벨 우선.
// 단축어 → 정식 계정명 후보(질문에 단축어 있으면 probe 에 정식명들 덧붙여 매칭). "부채"⊂"부채총계" 부분어 +
// 업종별 변형(제조=매출액, IT/금융=영업수익) 해소. searchIndex.SYNONYMS 와 같은 큐레이션 · bounded.
const ACCT_SYN: Record<string, string[]> = {
	판관비: ['판매비와관리비'],
	순이익: ['당기순이익'],
	영업현금: ['영업활동현금흐름'],
	영업현금흐름: ['영업활동현금흐름'],
	현금흐름: ['영업활동현금흐름'],
	매출: ['매출액', '영업수익'],
	수익: ['영업수익', '매출액'],
	돈: ['매출액', '영업수익', '당기순이익'], // "돈을 어떻게 버나" 의미형 → 매출/순이익 결정론 매칭(신설 사전 0)
	// '사업'은 동의어 제외 · "주요 사업 *내용*이 뭐야"(서술형)를 매출 숫자로 확신-오정렬시킴. 돈 버는 질문은
	// '돈'·'수익'·'실적'이 이미 커버하고, 서술형 사업질문은 lookup(근거 섹션 점프)이 정답(확신오정렬 > 정렬실패).
	실적: ['영업이익', '매출액', '당기순이익'], // "실적 어때"
	부채: ['부채총계'],
	자산: ['자산총계'],
	자본: ['자본총계'],
	차입금: ['차입금'],
	이익잉여: ['이익잉여금'],
	배당: ['배당금지급'] // CF 실지급액. 이익잉여금(누적)은 배당액 아님 → 오해 방지로 제외(없으면 thin)
};
// 라벨 변형 · 전체("수익(매출액)")·괄호제거("수익")·괄호내용("매출액", 단 3자+ 만 = 손실/이익/손익 2자 노이즈 배제).
function labelVariants(label: string): string[] {
	const noSp = label.replace(/\s/g, '');
	const stripped = noSp.replace(/\([^)]*\)/g, '');
	const out = new Set<string>();
	if (noSp.length >= 2) out.add(noSp);
	if (stripped.length >= 2) out.add(stripped);
	for (const m of noSp.matchAll(/\(([^)]*)\)/g)) if (m[1].length >= 3) out.add(m[1]);
	return [...out];
}
function matchSignal(q: string, signals: FinanceSignal[]): FinanceSignal | null {
	const nq = q.replace(/\s/g, '');
	let probe = nq;
	for (const [k, vs] of Object.entries(ACCT_SYN)) if (nq.includes(k)) probe += vs.join('');
	let best: FinanceSignal | null = null;
	let bestLen = 0;
	let bestFull = Infinity;
	for (const s of signals) {
		const full = s.label.replace(/\s/g, '').length;
		for (const v of labelVariants(s.label)) {
			if (!probe.includes(v)) continue;
			// 더 긴 매칭 우선; 동률이면 *전체 라벨이 짧은* 본 계정 우선 · "당기순이익" > "(비지배주주지분)당기순이익"
			// (괄호제거 변형이 동률을 만들어 하위 라인이 잘못 선택되던 버그 차단).
			if (v.length > bestLen || (v.length === bestLen && full < bestFull)) {
				best = s;
				bestLen = v.length;
				bestFull = full;
			}
		}
	}
	return best;
}

function dirWord(d: FinanceSignal['direction']): string {
	return d === 'up' ? '증가' : d === 'down' ? '감소' : d === 'flat' ? '거의 변화 없음' : '등락 혼조';
}

// 주제격 조사 · 마지막 글자 받침 유무로 은/는 선택("부채총계는"·"영업이익은"). 한글 아니면 는.
function topicJosa(word: string): string {
	const ch = word.trim().slice(-1);
	const code = ch.charCodeAt(0);
	if (code < 0xac00 || code > 0xd7a3) return '는';
	return (code - 0xac00) % 28 !== 0 ? '은' : '는';
}

// 표준 계정명(공백제거) 정확 일치로 신호 1개 선택 · 비율 분자/분모용. labels 순서 = 우선순위(매출액 우선 등).
function findSig(signals: FinanceSignal[], labels: string[]): FinanceSignal | null {
	for (const lab of labels) {
		const s = signals.find((x) => x.label.replace(/\s/g, '') === lab);
		if (s) return s;
	}
	return null;
}
// 분자/분모 동일 기간 정렬 후 비율(%) 시계열(최신좌측). 생성 아닌 계산 · financeSignals.points 직접.
function ratioSeries(numer: FinanceSignal, denom: FinanceSignal): { period: string; value: number }[] {
	const dmap = new Map(denom.points.map((p) => [p.period, p.value]));
	const out: { period: string; value: number }[] = [];
	for (const np of numer.points) {
		const dv = dmap.get(np.period);
		if (dv != null && dv !== 0) out.push({ period: np.period, value: (np.value / dv) * 100 });
	}
	return out;
}

export function composeAnswer(q: string, hits: SearchHit[], addedTerms: string[], signals: FinanceSignal[]): ComposeResult {
	const { c } = parseConstraint(q);
	const intent = classifyIntent(q, !!c);
	const suggestLlm = WHY_RE.test(q) || SYNTH_RE.test(q);
	// lookup 도 계정 매칭 시도 · "무슨 사업으로 돈을 버나"(추세어 없음)처럼 추세/규모 키워드는 없지만 계정어(돈→매출)가
	// 있으면 thin lookup 대신 수치 답(sig 분기의 magnitude fallthrough). constraint/existence 만 제외.
	const sig = intent === 'constraint' || intent === 'existence' ? null : matchSignal(q, signals);

	// 조건(금액) · search 가 이미 amount 필터+내림차순
	if (intent === 'constraint') {
		if (!hits.length) return { intent, answer: `'${q}' 조건을 만족하는 항목을 색인에서 찾지 못했습니다.`, citedSignal: null, suggestLlm: false };
		const top = hits.slice(0, 4).map((h) => h.block || h.section).filter(Boolean).join(', ');
		return { intent, answer: `조건을 만족하는 항목 ${hits.length}건을 찾았습니다: ${top}${hits.length > 4 ? ' 등' : ''}. 근거를 클릭해 금액을 확인하세요.`, citedSignal: null, suggestLlm: false };
	}

	// 재무비율 · 분자/분모 계정을 동일기간 나눠 계산(생성0). 분모 부재(금융업 등)면 raw 절대값 폴백(거짓정밀 금지).
	if (intent === 'ratio') {
		const nq = q.replace(/\s/g, '');
		const def = RATIO_TRIGGERS.find((r) => nq.includes(r.key));
		if (def) {
			const nSig = findSig(signals, def.numer);
			const dSig = findSig(signals, def.denom);
			if (nSig && dSig) {
				const series = ratioSeries(nSig, dSig);
				if (series.length) {
					const cur = series[0];
					const prevTxt = series[1] ? `, 직전 ${series[1].value.toFixed(1)}%` : '';
					return {
						intent,
						answer: `${def.key}${topicJosa(def.key)} ${cur.period} 기준 ${cur.value.toFixed(1)}%입니다${prevTxt}.`,
						citedSignal: nSig,
						suggestLlm
					};
				}
			}
			const raw = nSig ?? dSig;
			if (raw) {
				return {
					intent,
					answer: `${def.key} 산출 계정이 부족합니다(금융업 등 비적용일 수 있음). ${raw.label} 최근값은 ${won(raw.latest)}원입니다(${raw.points[0].period}).`,
					citedSignal: raw,
					suggestLlm
				};
			}
			return { intent, answer: `${def.key}을(를) 산출할 재무 계정을 데이터에서 찾지 못했습니다.`, citedSignal: null, suggestLlm: true };
		}
	}

	// 재무 정렬숫자에서 직접 답(가장 정확) · TREND/FLIP/MAGNITUDE
	if (sig) {
		if (intent === 'flip') {
			const j = topicJosa(sig.label);
			const ans = sig.signFlip
				? `${sig.label}${j} ${sig.flipAt} 기간에 ${sig.latest < 0 ? '흑자 → 적자' : '적자 → 흑자'}로 전환됐습니다. 최근값 ${won(sig.latest)}원(${sig.points[0].period}).`
				: `${sig.label}${j} 조회 기간 내 흑↔적자 전환이 없습니다. 최근값 ${won(sig.latest)}원(${sig.points[0].period}, ${sig.latest < 0 ? '적자' : '흑자'}).`;
			return { intent, answer: ans, citedSignal: sig, suggestLlm };
		}
		if (intent === 'trend') {
			const oldest = sig.points[sig.points.length - 1];
			const pct = sig.deltaPct == null ? '' : `, 직전 대비 ${sig.deltaPct > 0 ? '+' : ''}${Math.round(sig.deltaPct * 100)}%`;
			const streak = (sig.direction === 'up' || sig.direction === 'down') && sig.monotoneRun >= 3 ? ` (${sig.monotoneRun}개 기간 연속 ${dirWord(sig.direction)})` : '';
			return {
				intent,
				answer: `${sig.label}${topicJosa(sig.label)} ${oldest.period}~${sig.points[0].period} ${dirWord(sig.direction)} 추세입니다. 최근값 ${won(sig.latest)}원${pct}${streak}.`,
				citedSignal: sig,
				suggestLlm
			};
		}
		// magnitude · 특정 연도 조회("2023년 영업이익") 우선, 없으면 최신값 + YoY 라벨.
		const yr = q.match(/(20\d{2})/);
		if (yr) {
			const pt = sig.points.find((p) => p.period.startsWith(yr[1]));
			if (pt) return { intent, answer: `${sig.label}의 ${pt.period} 값은 ${won(pt.value)}원입니다.`, citedSignal: sig, suggestLlm };
			const span = `${sig.points[sig.points.length - 1].period}~${sig.points[0].period}`;
			return { intent, answer: `${sig.label}의 ${yr[1]}년 값은 데이터에 없습니다(제공: ${span}, 연간 기준).`, citedSignal: sig, suggestLlm };
		}
		const yoy = sig.deltaPct != null ? ` (전년 대비 ${sig.deltaPct > 0 ? '+' : ''}${Math.round(sig.deltaPct * 100)}%)` : '';
		return {
			intent,
			answer: `${sig.label} 최근 보고값은 ${won(sig.latest)}원입니다(${sig.points[0].period})${sig.prev != null ? `, 직전 ${won(sig.prev)}원${yoy}` : ''}.`,
			citedSignal: sig,
			suggestLlm
		};
	}

	// 유무
	if (intent === 'existence') {
		if (hits.length) {
			const t = hits[0];
			const syn = addedTerms.length ? `, 동의어 ${addedTerms.slice(0, 3).join('·')} 포함` : '';
			return { intent, answer: `관련 공시가 있습니다 · ${[t.section, t.block].filter(Boolean).join(' > ')}: ${t.snippet}… (관련 ${hits.length}건${syn}).`, citedSignal: null, suggestLlm };
		}
		const syn = addedTerms.length ? ` (동의어 ${addedTerms.slice(0, 3).join('·')}까지 검색)` : '';
		return { intent, answer: `색인에서 '${q}' 관련 항목은 확인되지 않았습니다${syn}. 표 본문은 라벨만 색인되므로 부재를 단정하지 않습니다.`, citedSignal: null, suggestLlm: false };
	}

	// 규모(재무 매칭 실패) → 본문 근거 폴백
	if (intent === 'magnitude' && hits.length) {
		return { intent, answer: `'${q}' 관련 공시 본문 ${hits.length}건을 찾았습니다. 최상위: ${[hits[0].section, hits[0].block].filter(Boolean).join(' > ')}. 근거에서 금액을 확인하세요.`, citedSignal: null, suggestLlm };
	}

	// lookup / 폴백
	if (hits.length) return { intent: 'lookup', answer: `관련 근거 ${hits.length}건을 찾았습니다. 근거를 클릭하면 해당 위치로 이동합니다.`, citedSignal: null, suggestLlm: true };
	return { intent: 'lookup', answer: `'${q}' 관련 근거를 찾지 못했습니다. 다른 표현으로 질문해 보세요.`, citedSignal: null, suggestLlm: false };
}
