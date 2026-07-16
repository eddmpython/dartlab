import type { UniverseVisualStatus, UniverseVisualToken } from '@dartlab/ui-contracts';

export const UNIVERSE_VISUAL_TOKENS: Readonly<Record<UniverseVisualStatus, UniverseVisualToken>> = Object.freeze({
	fact: { stroke: 'solid-2', pattern: 'none', glyph: '✓', label: '근거 확인', color: '#45d39a', evidenceAction: 'openEvidence', ariaStatus: '원문 근거가 결속된 사실' },
	candidate: { stroke: 'dash-2-2', pattern: 'diagonal-open', glyph: '⌕', label: '근거 탐색 중', color: '#f5b84b', evidenceAction: 'findEvidence', ariaStatus: '근거를 찾아야 하는 관계 후보' },
	derived: { stroke: 'double-1', pattern: 'horizontal', glyph: 'ƒ', label: '계산 결과', color: '#64a8ff', evidenceAction: 'inspectDerivation', ariaStatus: '원천 자료에서 계산한 파생 결과' },
	disputed: { stroke: 'dash-dot-2', pattern: 'cross', glyph: '⑂', label: '근거 충돌', color: '#ff8d56', evidenceAction: 'compareEvidence', ariaStatus: '서로 충돌하는 근거가 있는 주장' },
	retracted: { stroke: 'strike-2', pattern: 'backslash', glyph: '↶', label: '철회됨', color: '#ff6577', evidenceAction: 'openRetraction', ariaStatus: '후속 공시로 철회된 과거 주장' },
	scenario: { stroke: 'dot-2', pattern: 'wave', glyph: '◇', label: '가정 시나리오', color: '#ac86ff', evidenceAction: 'inspectAssumptions', ariaStatus: '관측 사실이 아닌 명시적 가정 시나리오' },
	unknown: { stroke: 'gap-2', pattern: 'empty', glyph: '?', label: '판정 불가', color: '#76849a', evidenceAction: 'explainGap', ariaStatus: '근거 결손으로 상태를 판정할 수 없음' }
});
