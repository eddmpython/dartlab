<script lang="ts">
	/**
	 * 컬럼 그룹 toggle bar · 그리드 위쪽에 가로로.
	 *
	 * 사용자가 그룹 (재무/비율/등급/주가/공시 등) 단위로 컬럼 펼침/접기.
	 * 그룹 클릭 = 해당 그룹 컬럼 모두 add (기존 active 와 union) / remove.
	 * 헤더에 메트릭 추가/삭제 메뉴는 별도 (이 PR-A 에서는 그룹 단위만).
	 */
	import type { MetricKey } from './metrics';
	import { GROUP_META, METRICS_BY_GROUP, PINNED_COLUMNS } from './metrics';
	import type { MetricGroup } from './metrics';

	interface Props {
		activeColumns: MetricKey[];
		loadingGroups?: Set<MetricGroup>;
		onToggle: (next: MetricKey[], group: MetricGroup) => void;
	}

	let { activeColumns, loadingGroups = new Set<MetricGroup>(), onToggle }: Props = $props();

	let activeSet = $derived(new Set(activeColumns));

	const GROUPS: MetricGroup[] = [
		'identity',
		'income',
		'health',
		'governance',
		'quality',
		'workforce',
		'changes',
		'financeIncome',
		'financeBalance',
		'financeCashflow',
		'financeRatio',
		'financeGrowth',
		'price',
		'valuation',
		'disclosure'
	];

	function groupState(g: MetricGroup): 'all' | 'partial' | 'none' {
		const cols = METRICS_BY_GROUP[g] || [];
		if (cols.length === 0) return 'none';
		const onCount = cols.filter((m) => activeSet.has(m.key)).length;
		if (onCount === 0) return 'none';
		if (onCount === cols.length) return 'all';
		return 'partial';
	}

	function toggleGroup(g: MetricGroup) {
		const cols = METRICS_BY_GROUP[g] || [];
		const state = groupState(g);
		const next = new Set(activeColumns);
		if (state === 'all') {
			// 모두 제거 · 단 PINNED 는 보존
			for (const m of cols) {
				if (!PINNED_COLUMNS.includes(m.key)) next.delete(m.key);
			}
		} else {
			// 모두 추가
			for (const m of cols) next.add(m.key);
		}
		onToggle(Array.from(next), g);
	}
</script>

<div class="bar" role="toolbar" aria-label="컬럼 그룹">
	{#each GROUPS as g (g)}
		{@const meta = GROUP_META[g]}
		{@const state = groupState(g)}
		{@const cols = METRICS_BY_GROUP[g] || []}
		{@const loading = loadingGroups.has(g)}
		{#if cols.length > 0}
			<button
				type="button"
				class="grp"
				class:on={state === 'all'}
				class:partial={state === 'partial'}
				class:loading
				style:--cg={meta.color}
				onclick={() => toggleGroup(g)}
				aria-busy={loading}
				title="{meta.label} ({cols.length}개)"
			>
				{#if loading}
					<span class="spinner" aria-hidden="true"></span>
				{:else}
					<span class="dot" aria-hidden="true"></span>
				{/if}
				<span class="lbl">{meta.label}</span>
				<span class="cnt">{cols.filter((m) => activeSet.has(m.key)).length}/{cols.length}</span>
			</button>
		{/if}
	{/each}
</div>

<style>
	.bar {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		padding: 8px 0;
	}
	.grp {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 6px 10px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #94a3b8;
		font-size: 11px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s, border-color 0.15s, color 0.15s;
	}
	.grp:hover {
		background: #0b1120;
		border-color: #334155;
		color: #f1f5f9;
	}
	.grp.partial {
		border-color: var(--cg);
		color: #cbd5e1;
	}
	.grp.on {
		background: color-mix(in srgb, var(--cg) 12%, transparent);
		border-color: var(--cg);
		color: #f1f5f9;
	}
	.grp.loading {
		border-color: color-mix(in srgb, var(--cg) 70%, #1e2433);
		color: #f1f5f9;
	}
	.dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--cg);
		opacity: 0.5;
	}
	.spinner {
		width: 9px;
		height: 9px;
		flex: 0 0 auto;
		border-radius: 50%;
		border: 1.5px solid color-mix(in srgb, var(--cg) 24%, #334155);
		border-top-color: var(--cg);
		animation: spin 0.75s linear infinite;
	}
	.grp.partial .dot,
	.grp.on .dot {
		opacity: 1;
	}
	.lbl {
		letter-spacing: -0.01em;
	}
	.cnt {
		font-family: monospace;
		font-size: 10px;
		color: #64748b;
	}
	.grp.on .cnt {
		color: var(--cg);
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.spinner {
			animation: none;
		}
	}
</style>
