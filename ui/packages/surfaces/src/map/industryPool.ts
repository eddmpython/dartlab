// Profit-pool stage 롤업 · `map/industries/{id}.json` 의 stages[].nodes[] 를
// stage 단위 (매출규모 × revenue-weighted 영업이익률 × coverageRatio) 격자로 변환한다.
// "이 산업의 이익은 어느 공정 단계가 버나" (McKinsey profit pool: 이익집중 ≠ 매출집중).
//
// ★dual-source SSOT (mainPlan/industry-analysis-lab/07-implementation-plan.md §구멍1):
//   엔진 `buildIndustrySummary`(panel Σ영업이익/Σ매출) 가 **캐논**이고, 본 브라우저 롤업은
//   **표시용**이다. 브라우저는 per-node `opMargin`(이미 비율) 기반이라 커버리지·값이 엔진과
//   갈릴 수 있어, coverageRatio 를 *항상* 노출한다 (결손 0 채움 금지 · 빠진 노드는 가중에서
//   제외하고 분모로만 카운트).

export interface ProfitPoolNode {
	revenue?: number | null;
	opMargin?: number | null;
}

export interface ProfitPoolStage {
	key?: string;
	name?: string;
	stream?: string | null;
	nodes?: ProfitPoolNode[];
}

export interface IndustryStageRollup {
	key: string;
	name: string;
	stream: string | null;
	/** stage 전체 노드 Σ매출 (industries/{id}.json 원자료 단위 = 억원). */
	revenue: number;
	/** revenue-weighted 영업이익률(%) = Σ(rev×opMargin)/Σrev, opMargin present 노드만. 없으면 null (0 아님). */
	opMarginPct: number | null;
	/** stage 전체 노드 수. */
	companyCount: number;
	/** opMargin 산출가능 노드 / companyCount (0~1). 결손 노출용. */
	coverageRatio: number;
}

function round1(v: number): number {
	return Math.round(v * 10) / 10;
}

function round3(v: number): number {
	return Math.round(v * 1000) / 1000;
}

/**
 * stages 배열을 profit-pool 격자 rollup 으로. 엔진 캐논과 같은 산식 (revenue-weighted,
 * present-only, coverage 노출, 0 채움 금지) 을 브라우저 표시층에서 미러한다.
 */
export function rollupProfitPool(stages: ProfitPoolStage[] | null | undefined): IndustryStageRollup[] {
	const out: IndustryStageRollup[] = [];
	for (const stage of stages || []) {
		const nodes = stage.nodes || [];
		let revSum = 0; // 전체 매출 (표시용)
		let revBoth = 0; // opMargin present 노드의 매출 (가중 분모)
		let weighted = 0; // Σ(rev × opMargin)
		let nBoth = 0;
		for (const n of nodes) {
			const rev = typeof n.revenue === 'number' ? n.revenue : null;
			const om = typeof n.opMargin === 'number' ? n.opMargin : null;
			if (rev != null) revSum += rev;
			if (rev != null && om != null) {
				revBoth += rev;
				weighted += rev * om;
				nBoth += 1;
			}
		}
		const count = nodes.length;
		out.push({
			key: stage.key ?? '',
			name: stage.name ?? stage.key ?? '',
			stream: stage.stream ?? null,
			revenue: revSum,
			opMarginPct: revBoth > 0 ? round1(weighted / revBoth) : null,
			companyCount: count,
			coverageRatio: count > 0 ? round3(nBoth / count) : 0
		});
	}
	return out;
}
