<script lang="ts">
	/**
	 * 자동 발굴 신호 카드 5종 · 행 미선택 시 디테일 자리에 표시.
	 *
	 *  1. ROE 급상승 TOP  · roeDelta desc, top 10
	 *  2. 영업이익률 급상승 · opMarginDelta desc, top 10
	 *  3. 부채비율 급증 위험 · debtRatioDelta desc, top 10
	 *  4. 매출액 증가 · revenueYoyPct desc, top 10
	 *  5. 우량주 (qualGrade 우수 + roe 15+ + 부채 100-)
	 *
	 * 카드 → 클릭 = 자동 필터 + 정렬 적용 (onApply).
	 */
	import type { ScanNode, FilterCond, SortKey } from './types';
	import { fmtPct } from '@dartlab/ui-format/pct';
	import { fmtKrw } from '@dartlab/ui-format/krw';

	interface Props {
		nodes: ScanNode[];
		onApply: (cards: { conds: FilterCond[]; sort: SortKey; cols?: string[] }) => void;
		onCompanyClick: (id: string) => void;
	}

	let { nodes, onApply, onCompanyClick }: Props = $props();

	type Ranked = { n: ScanNode; v: number; metric: string };
	const SIGNAL_LIMIT = 10;
	const MIN_PRIMARY_SIGNAL_COUNT = 5;

	function topByMetric(
		key: string,
		dir: 'desc' | 'asc' = 'desc',
		limit = SIGNAL_LIMIT,
		guard?: (n: ScanNode, v: number) => boolean
	) {
		const list = nodes
			.map((n) => {
				const v = (n as Record<string, unknown>)[key];
				if (typeof v !== 'number' || !Number.isFinite(v)) return null;
				if (guard && !guard(n, v)) return null;
				return { n, v, metric: key };
			})
			.filter((x): x is Ranked => x !== null);
		return list.sort((a, b) => (dir === 'desc' ? b.v - a.v : a.v - b.v)).slice(0, limit);
	}

	function fillSignals(primary: Ranked[], fallbacks: Ranked[], limit = SIGNAL_LIMIT): Ranked[] {
		const out: Ranked[] = [];
		const seen = new Set<string>();
		for (const item of [...primary, ...fallbacks]) {
			if (seen.has(item.n.id)) continue;
			seen.add(item.n.id);
			out.push(item);
			if (out.length >= limit) break;
		}
		return out;
	}

	function usePrimaryOrFallback(primary: Ranked[], fallbacks: Ranked[]): Ranked[] {
		if (primary.length >= MIN_PRIMARY_SIGNAL_COUNT) return fillSignals(primary, fallbacks);
		return fillSignals(fallbacks, []);
	}

	function fallbackUniverse(): Ranked[] {
		return topByMetric('revenue', 'desc', SIGNAL_LIMIT, (_n, v) => v > 0);
	}

	function formatRanked(r: Ranked): string {
		if (r.metric === 'revenue' || r.metric === 'marketCap') return fmtKrw(r.v);
		if (r.metric === 'industryRank') return `${r.v}위`;
		return fmtPct(r.v, {
			withSign: r.metric.endsWith('Delta') || r.metric === 'revenueYoyPct' || r.metric === 'revCagr'
		});
	}

	// 극단치 noise 필터. 조건이 빡빡해도 현재 지표와 매출 규모로 채워 항상 후보가 보이게 한다.
	let roeRising = $derived.by(() =>
		usePrimaryOrFallback(
			topByMetric('roeDelta', 'desc', SIGNAL_LIMIT, (n, v) => {
				const cur = n.roe as number | undefined;
				return v >= 3 && v <= 300 && (typeof cur !== 'number' || cur >= 0);
			}),
			[
				...topByMetric('roe', 'desc', SIGNAL_LIMIT, (_n, v) => v >= 5 && v <= 120),
				...fallbackUniverse()
			]
		)
	);
	let marginRising = $derived.by(() =>
		usePrimaryOrFallback(
			topByMetric('opMarginDelta', 'desc', SIGNAL_LIMIT, (n, v) => {
				const cur = n.opMargin as number | undefined;
				return v >= 3 && v <= 120 && (typeof cur !== 'number' || cur >= -20);
			}),
			[
				...topByMetric('opMargin', 'desc', SIGNAL_LIMIT, (_n, v) => v > 0 && v <= 120),
				...fallbackUniverse()
			]
		)
	);
	let debtSurge = $derived.by(() =>
		usePrimaryOrFallback(
			topByMetric('debtRatioDelta', 'desc', SIGNAL_LIMIT, (n, v) => {
				const cur = n.debtRatio as number | undefined;
				return v >= 10 && v <= 500 && typeof cur === 'number' && cur > 0 && cur <= 500;
			}),
			[
				...topByMetric('debtRatio', 'desc', SIGNAL_LIMIT, (_n, v) => v >= 100 && v <= 500),
				...fallbackUniverse()
			]
		)
	);
	let revenueRising = $derived.by(() =>
		usePrimaryOrFallback(
			topByMetric('revenueYoyPct', 'desc', SIGNAL_LIMIT, (_n, v) => v >= 5 && v <= 500),
			[
				...topByMetric('revCagr', 'desc', SIGNAL_LIMIT, (_n, v) => v > 0 && v <= 300),
				...fallbackUniverse()
			]
		)
	);

	let qualityCompounders = $derived.by(() => {
		const strict = nodes
			.filter((n) => {
				const q = n.qualGrade as string | undefined;
				const roe = n.roe as number | undefined;
				const debt = n.debtRatio as number | undefined;
				return (
					(q === '우수' || q === '양호') &&
					typeof roe === 'number' &&
					roe >= 15 &&
					roe <= 80 &&
					typeof debt === 'number' &&
					debt <= 100
				);
			})
			.map((n) => ({ n, v: n.roe as number, metric: 'roe' }))
			.sort((a, b) => b.v - a.v)
			.slice(0, SIGNAL_LIMIT);
		return fillSignals(strict, [
			...topByMetric('roe', 'desc', SIGNAL_LIMIT, (n, v) => {
				const debt = n.debtRatio as number | undefined;
				return v >= 10 && v <= 120 && (typeof debt !== 'number' || debt <= 200);
			}),
			...fallbackUniverse()
		]);
	});

	function applyRoeRising() {
		const primary = roeRising[0]?.metric === 'roeDelta';
		onApply({
			conds: primary ? [] : [{ metric: 'roe', op: '>=', value: 5 }],
			sort: { key: primary ? 'roeDelta' : 'roe', dir: 'desc' },
			cols: ['roeDelta', 'roe', 'opMargin', 'profGrade']
		});
	}
	function applyMarginRising() {
		const primary = marginRising[0]?.metric === 'opMarginDelta';
		onApply({
			conds: [{ metric: 'opMargin', op: '>=', value: 0 }],
			sort: { key: primary ? 'opMarginDelta' : 'opMargin', dir: 'desc' },
			cols: ['opMarginDelta', 'opMargin', 'revenueYoyPct']
		});
	}
	function applyDebtSurge() {
		const primary = debtSurge[0]?.metric === 'debtRatioDelta';
		onApply({
			conds: [],
			sort: { key: primary ? 'debtRatioDelta' : 'debtRatio', dir: 'desc' },
			cols: ['debtRatioDelta', 'debtRatio', 'icr', 'debtGrade']
		});
	}
	function applyRevenueRising() {
		const metric = revenueRising[0]?.metric;
		const sortKey = metric === 'revenueYoyPct' || metric === 'revCagr' ? metric : 'revenue';
		onApply({
			conds: sortKey === 'revenue' ? [{ metric: 'revenue', op: '>=', value: 0 }] : [{ metric: sortKey, op: '>=', value: 0 }],
			sort: { key: sortKey, dir: 'desc' },
			cols: ['revenueYoyPct', 'revCagr', 'revenue', 'opMargin']
		});
	}
	function applyQuality() {
		onApply({
			conds: [
				{ metric: 'roe', op: '>=', value: 15 },
				{ metric: 'debtRatio', op: '<=', value: 100 },
				{ metric: 'qualGrade', op: '!=', value: '주의' },
				{ metric: 'qualGrade', op: '!=', value: '위험' }
			],
			sort: { key: 'roe', dir: 'desc' },
			cols: ['qualGrade', 'roe', 'debtRatio']
		});
	}
</script>

<aside class="insights" aria-label="자동 발굴 신호">
	<header class="i-head">
		<span class="i-eyebrow">자동 발굴 신호</span>
		<span class="i-sub">회사 클릭 = 디테일 / 카드 → 클릭 = 그리드 필터</span>
	</header>

	<div class="i-grid">
		<!-- ROE 급상승 -->
		<div class="card good">
			<div class="card-head">
				<span class="card-title">ROE 급상승 회사</span>
				<button type="button" class="card-cta" onclick={applyRoeRising}>전체 보기 →</button>
			</div>
			<div class="card-desc">전기 대비 ROE 개선. 없으면 현재 ROE 상위 표시</div>
			<ul class="card-list">
				{#each roeRising as r (r.n.id)}
					<li>
						<button type="button" class="r-row" onclick={() => onCompanyClick(r.n.id)}>
							<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
							<span class="r-label">{r.n.label}</span>
							<span class="r-val good">{formatRanked(r)}</span>
						</button>
					</li>
				{/each}
				{#if roeRising.length === 0}
					<li class="empty-row">조건에 맞는 회사 없음</li>
				{/if}
			</ul>
		</div>

		<!-- 영업이익률 급상승 -->
		<div class="card good">
			<div class="card-head">
				<span class="card-title">영업이익률 개선</span>
				<button type="button" class="card-cta" onclick={applyMarginRising}>전체 보기 →</button>
			</div>
			<div class="card-desc">영업이익률 개선. 없으면 현재 영업이익률 상위 표시</div>
			<ul class="card-list">
				{#each marginRising as r (r.n.id)}
					<li>
						<button type="button" class="r-row" onclick={() => onCompanyClick(r.n.id)}>
							<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
							<span class="r-label">{r.n.label}</span>
							<span class="r-val good">{formatRanked(r)}</span>
						</button>
					</li>
				{/each}
				{#if marginRising.length === 0}
					<li class="empty-row">조건에 맞는 회사 없음</li>
				{/if}
			</ul>
		</div>

		<!-- 부채비율 급증 (위험 신호) -->
		<div class="card bad">
			<div class="card-head">
				<span class="card-title">부채비율 급증 위험</span>
				<button type="button" class="card-cta" onclick={applyDebtSurge}>전체 보기 →</button>
			</div>
			<div class="card-desc">부채비율 급등 위험. 없으면 현재 부채비율 상위 표시</div>
			<ul class="card-list">
				{#each debtSurge as r (r.n.id)}
					<li>
						<button type="button" class="r-row" onclick={() => onCompanyClick(r.n.id)}>
							<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
							<span class="r-label">{r.n.label}</span>
							<span class="r-val bad">{formatRanked(r)}</span>
						</button>
					</li>
				{/each}
				{#if debtSurge.length === 0}
					<li class="empty-row">조건에 맞는 회사 없음</li>
				{/if}
			</ul>
		</div>

		<!-- 매출액 증가 -->
		<div class="card good">
			<div class="card-head">
				<span class="card-title">매출액 증가 회사</span>
				<button type="button" class="card-cta" onclick={applyRevenueRising}>전체 보기 →</button>
			</div>
			<div class="card-desc">매출 YoY 증가 상위. 없으면 CAGR·매출 규모 기준 폴백</div>
			<ul class="card-list">
				{#each revenueRising as r (r.n.id)}
					<li>
						<button type="button" class="r-row" onclick={() => onCompanyClick(r.n.id)}>
							<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
							<span class="r-label">{r.n.label}</span>
							<span class="r-val good">{formatRanked(r)}</span>
						</button>
					</li>
				{/each}
				{#if revenueRising.length === 0}
					<li class="empty-row">조건에 맞는 회사 없음</li>
				{/if}
			</ul>
		</div>

		<!-- 우량주 (Quality Compounder) -->
		<div class="card good">
			<div class="card-head">
				<span class="card-title">Quality Compounder</span>
				<button type="button" class="card-cta" onclick={applyQuality}>전체 보기 →</button>
			</div>
			<div class="card-desc">ROE 15%↑ + 부채 100%↓. 없으면 ROE·부채 기준 폴백</div>
			<ul class="card-list">
				{#each qualityCompounders as r (r.n.id)}
					<li>
						<button type="button" class="r-row" onclick={() => onCompanyClick(r.n.id)}>
							<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
							<span class="r-label">{r.n.label}</span>
							<span class="r-val good">{formatRanked(r)}</span>
						</button>
					</li>
				{/each}
				{#if qualityCompounders.length === 0}
					<li class="empty-row">조건에 맞는 회사 없음</li>
				{/if}
			</ul>
		</div>
	</div>
</aside>

<style>
	.insights {
		flex-shrink: 0;
		background: #0a0e18;
		border: 1px solid #1e2433;
		border-radius: 6px;
		padding: 8px 10px;
		display: flex;
		flex-direction: column;
		gap: 6px;
		height: var(--scan-bottom-panel-height, 258px);
		max-height: var(--scan-bottom-panel-height, 258px);
		min-height: var(--scan-bottom-panel-height, 258px);
		overflow-y: auto;
	}
	.i-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
	}
	.i-eyebrow {
		font-size: 10px;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}
	.i-sub {
		font-size: 10px;
		color: #64748b;
	}
	.i-grid {
		display: grid;
		grid-template-columns: repeat(5, minmax(0, 1fr));
		gap: 6px;
		flex: 1;
		min-height: 0;
	}
	@media (max-width: 1280px) {
		.i-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	@media (max-width: 768px) {
		.i-grid {
			grid-template-columns: 1fr;
		}
	}

	.card {
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 5px;
		padding: 7px 8px;
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
		min-height: 0;
		position: relative;
	}
	.card.good::before {
		content: '';
		position: absolute;
		left: 0;
		top: 12px;
		bottom: 12px;
		width: 2px;
		background: #22c55e;
		border-radius: 2px;
		opacity: 0.6;
	}
	.card.bad::before {
		content: '';
		position: absolute;
		left: 0;
		top: 12px;
		bottom: 12px;
		width: 2px;
		background: #ef4444;
		border-radius: 2px;
		opacity: 0.6;
	}
	.card-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		padding-left: 7px;
		gap: 5px;
	}
	.card-title {
		font-size: 10.5px;
		font-weight: 600;
		color: #f1f5f9;
		letter-spacing: -0.01em;
	}
	.card-cta {
		font-size: 10px;
		background: transparent;
		border: none;
		color: var(--amber);
		cursor: pointer;
		font-family: inherit;
		padding: 0;
	}
	.card-cta:hover {
		text-decoration: underline;
	}
	.card-desc {
		font-size: 9px;
		color: #64748b;
		line-height: 1.35;
		padding-left: 7px;
	}

	.card-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 1px;
		flex: 1;
		justify-content: flex-start;
	}
	.r-row {
		display: flex;
		align-items: center;
		gap: 5px;
		padding: 1px 3px 1px 7px;
		background: transparent;
		border: none;
		border-radius: 3px;
		cursor: pointer;
		text-align: left;
		font-family: inherit;
		color: inherit;
		width: 100%;
	}
	.r-row:hover {
		background: rgba(var(--amber-rgb), 0.06);
	}
	.r-dot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.r-label {
		flex: 1;
		font-size: 9px;
		color: #cbd5e1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.r-val {
		font-family: monospace;
		font-size: 8.5px;
		font-variant-numeric: tabular-nums;
	}
	.r-val.good {
		color: #22c55e;
	}
	.r-val.bad {
		color: #ef4444;
	}
	.empty-row {
		padding: 8px 4px 4px 8px;
		color: #475569;
		font-size: 10px;
	}
</style>
