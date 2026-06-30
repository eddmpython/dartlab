// Skill 카테고리 색상 SSOT · graph 시각화 + 카드 그리드 공통 사용.
// SCHEMA.md §1 "start · runtime · operation · engines · recipes" 와 정합.

export const categoryColor: Record<string, string> = {
	start: '#3b82f6', // blue
	runtime: '#a855f7', // purple
	operation: '#22c55e', // green
	engines: '#f97316', // orange
	recipes: '#f472b6', // pink
	// deprecated alias 폴백
	screens: '#64748b',
	finance: '#64748b',
	visuals: '#64748b',
	basic: '#64748b',
	user: '#64748b',
	capability: '#64748b'
};

export const edgeStyleByKind: Record<string, { stroke: string; dash: string; width: number }> = {
	successor: { stroke: '#22c55e', dash: '0', width: 1.8 },
	predecessor: { stroke: '#22c55e', dash: '0', width: 1.0 },
	linkedRecipe: { stroke: '#f97316', dash: '0', width: 2.2 },
	knowledge: { stroke: '#94a3b8', dash: '4 4', width: 1.2 },
	source: { stroke: '#cbd5e1', dash: '2 6', width: 0.8 }
};

export function colorOf(category: string): string {
	return categoryColor[category] ?? '#64748b';
}
