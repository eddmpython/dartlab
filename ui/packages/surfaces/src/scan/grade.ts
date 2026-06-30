/**
 * scan 엔진의 등급 컬럼들 (한국어) → 톤 (good/warn/bad/neutral) 매핑.
 *
 * dartlab.scan() 의 sub-engine 들이 각자 다른 등급 체계를 씀:
 *   - profGrade   : 우수 / 양호 / 보통 / 저수익 / 적자
 *   - debtGrade   : 안전 / 관찰 / 주의 / 고위험
 *   - qualGrade   : 우수 / 양호 / 보통 / 주의 / 위험
 *   - liqGrade    : 우수 / 양호 / 보통 / 주의 / 위험
 *   - growthGrade : 고성장 / 성장 / 정체 / 역성장
 *   - govGrade    : A / B / C / D / E
 *   - auditRisk   : "" / 저위험 / 중위험 / 고위험
 *   - capClass    : "" / A / B / C
 *   - cfPattern   : 환원형 / 건전형 / 공격성장형 / 신생형 / 적자생존형 / ...
 *   - stability   : 안정 / 보통 / 불안정
 *
 * 톤 매핑은 그리드 행 색·등급 칩 색상에 사용.
 */

export type Tone = 'good' | 'warn' | 'bad' | 'neutral';

const PROF_TONE: Record<string, Tone> = {
	'우수': 'good',
	'양호': 'good',
	'보통': 'neutral',
	'저수익': 'warn',
	'적자': 'bad'
};

const DEBT_TONE: Record<string, Tone> = {
	'안전': 'good',
	'관찰': 'neutral',
	'주의': 'warn',
	'고위험': 'bad',
	'위험': 'bad'
};

const QUAL_LIQ_TONE: Record<string, Tone> = {
	'우수': 'good',
	'양호': 'good',
	'보통': 'neutral',
	'주의': 'warn',
	'위험': 'bad'
};

const GROWTH_TONE: Record<string, Tone> = {
	'고성장': 'good',
	'성장': 'good',
	'정체': 'neutral',
	'역성장': 'bad',
	'쇠퇴': 'bad'
};

const ABCDE_TONE: Record<string, Tone> = {
	'A': 'good',
	'B': 'good',
	'C': 'neutral',
	'D': 'warn',
	'E': 'bad'
};

const AUDIT_TONE: Record<string, Tone> = {
	'저위험': 'good',
	'중위험': 'warn',
	'고위험': 'bad',
	'위험': 'bad'
};

const CF_TONE: Record<string, Tone> = {
	'환원형': 'good',
	'건전형': 'good',
	'공격성장형': 'neutral',
	'신생형': 'warn',
	'적자생존형': 'bad'
};

const STABILITY_TONE: Record<string, Tone> = {
	'안정': 'good',
	'보통': 'neutral',
	'불안정': 'warn'
};

/** 등급 컬럼별 톤 lookup. */
export function gradeTone(metricKey: string, value: unknown): Tone {
	if (value == null || value === '') return 'neutral';
	const v = String(value);
	switch (metricKey) {
		case 'profGrade':
			return PROF_TONE[v] ?? 'neutral';
		case 'debtGrade':
			return DEBT_TONE[v] ?? 'neutral';
		case 'qualGrade':
		case 'liqGrade':
			return QUAL_LIQ_TONE[v] ?? 'neutral';
		case 'growthGrade':
			return GROWTH_TONE[v] ?? 'neutral';
		case 'govGrade':
		case 'capClass':
			return ABCDE_TONE[v] ?? 'neutral';
		case 'auditRisk':
			return AUDIT_TONE[v] ?? 'neutral';
		case 'cfPattern':
			return CF_TONE[v] ?? 'neutral';
		case 'stability':
			return STABILITY_TONE[v] ?? 'neutral';
		default:
			return 'neutral';
	}
}

// 신호색 SSOT · tokens.css(--dl-good/warn/bad/ink-mute) 참조. 전부 CSS 컨텍스트(style:color·color-mix·
// style:--cg)에서만 소비되므로 var() 사용 가능(canvas 0 확인). 한 곳(tokens.css)에서 전 surface 신호색 제어.
/** qualGrade 기준 행 배경 톤 (CSS color-mix 인풋). */
export function rowTintColor(qualGrade: unknown): string {
	const tone = gradeTone('qualGrade', qualGrade);
	switch (tone) {
		case 'good':
			return 'var(--dl-good)';
		case 'warn':
			return 'var(--dl-warn)';
		case 'bad':
			return 'var(--dl-bad)';
		case 'neutral':
		default:
			return 'transparent';
	}
}

/** 톤 → 표시 색상 (등급 칩). */
export function toneColor(tone: Tone): string {
	switch (tone) {
		case 'good':
			return 'var(--dl-good)';
		case 'warn':
			return 'var(--dl-warn)';
		case 'bad':
			return 'var(--dl-bad)';
		case 'neutral':
		default:
			return 'var(--dl-ink-mute)';
	}
}
