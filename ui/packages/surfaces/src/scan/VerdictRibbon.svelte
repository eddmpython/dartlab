<script lang="ts">
	/**
	 * 판정격자 리본 · 조건이 있을 때만 그리드 위에 1 줄로 붙는다.
	 *
	 * 답하는 질문 셋:
	 *   "몇 사에서 몇 사로 줄었나"        -> 워터폴 (유니버스 -> 조건별 생존)
	 *   "왜 줄었나. 미달인가 데이터가 없나" -> 조건 칩의 탈락/판정불능 분리
	 *   "0 건인데 뭘 풀어야 하나"          -> 근접후보 수 + 임계 역산 제안
	 *
	 * 부제·각주를 달지 않는다. 숫자만 말한다.
	 */
	import type { MetricDef } from './types';
	import { condLabel, type VerdictGrid } from './verdict';

	interface Props {
		grid: VerdictGrid;
		metrics: Record<string, MetricDef>;
		nearMissCount: number;
		includeUnknown: boolean;
		showNearMiss: boolean;
		/** 조건 i 의 임계를 target 사가 되도록 완화. null 이면 역산 불가. */
		relaxFor: (condIndex: number, target: number) => number | null;
		onToggleUnknown: () => void;
		onToggleNearMiss: () => void;
		onRelax: (condIndex: number, value: number) => void;
		onRemoveCond: (condIndex: number) => void;
	}

	let {
		grid,
		metrics,
		nearMissCount,
		includeUnknown,
		showNearMiss,
		relaxFor,
		onToggleUnknown,
		onToggleNearMiss,
		onRelax,
		onRemoveCond
	}: Props = $props();

	const num = (n: number) => n.toLocaleString('ko-KR');
	const fmt = (n: number) => n.toLocaleString('ko-KR', { maximumFractionDigits: 1 });

	/** 결과가 빈약할 때만 완화를 제안한다. 목표는 20 사. */
	const TARGET = 20;
	let relaxHints = $derived.by(() => {
		if (grid.members.length >= TARGET || grid.conds.length === 0) return [];
		return grid.conds
			.map((c, i) => ({ i, cond: c, value: relaxFor(i, TARGET) }))
			.filter((h) => h.value !== null && h.value !== h.cond.value)
			.slice(0, 2);
	});

	/** 마지막 생존자 수 = members. 결측 포함 보기면 판정불능도 남는다. */
	let survived = $derived(includeUnknown ? grid.members.length + grid.excludedForMissing : grid.members.length);
</script>

{#if grid.conds.length > 0}
	<div class="ribbon" aria-label="조건 판정 요약">
		<span class="step start">{num(grid.universe)}</span>

		{#each grid.funnel as step, i (i)}
			<span class="arrow" aria-hidden="true">›</span>
			<button
				type="button"
				class="step cond"
				class:killer={step.survivors === 0}
				onclick={() => onRemoveCond(i)}
				title="클릭하면 이 조건을 제거합니다"
			>
				<span class="cond-name">{condLabel(step.cond, metrics)}</span>
				<span class="cond-n">{num(step.survivors)}</span>
				{#if step.unknown > 0}
					<span class="cond-unknown" title="데이터 부재로 판정 불가">?{num(step.unknown)}</span>
				{/if}
			</button>
		{/each}

		<span class="tally">
			<strong>{num(survived)}</strong>사
		</span>

		{#if grid.excludedForMissing > 0}
			<button
				type="button"
				class="chip"
				class:on={includeUnknown}
				onclick={onToggleUnknown}
				title="조건에 미달한 것이 아니라 데이터가 없어 판정하지 못한 종목"
			>
				결측 {num(grid.excludedForMissing)}
			</button>
		{/if}

		{#if nearMissCount > 0}
			<button type="button" class="chip" class:on={showNearMiss} onclick={onToggleNearMiss}>
				근접 {num(nearMissCount)}
			</button>
		{/if}

		{#each relaxHints as h (h.i)}
			<button
				type="button"
				class="chip relax"
				onclick={() => onRelax(h.i, h.value as number)}
				title="이 임계로 바꾸면 {TARGET}사가 됩니다"
			>
				{metrics[h.cond.metric]?.label ?? h.cond.metric}
				{h.cond.op}
				{fmt(h.value as number)}
				<span class="relax-n">{TARGET}사</span>
			</button>
		{/each}
	</div>
{/if}

<style>
	.ribbon {
		display: flex;
		align-items: center;
		gap: 4px;
		flex-wrap: wrap;
		padding: 4px 0;
		font-size: 11px;
		font-family: var(--dl-font-mono, monospace);
		color: var(--dl-ink-mute, #94a3b8);
	}
	.step {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		height: 22px;
		padding: 0 8px;
		border: 1px solid var(--dl-line, #1e2433);
		border-radius: 3px;
		background: var(--dl-bg-sunken, #050811);
		color: var(--dl-ink-mute, #94a3b8);
		font-family: inherit;
		font-size: 11px;
		line-height: 1;
		white-space: nowrap;
	}
	.start {
		color: var(--dl-ink-dim, #64748b);
	}
	.cond {
		cursor: pointer;
	}
	.cond:hover {
		border-color: var(--dl-line-strong, #334155);
		color: var(--dl-ink, #f1f5f9);
	}
	.cond.killer {
		border-color: rgba(var(--dl-accent-rgb), 0.5);
	}
	.cond-name {
		font-family: var(--dl-font-ui, inherit);
	}
	.cond-n {
		color: var(--dl-ink, #f1f5f9);
		font-variant-numeric: tabular-nums;
	}
	.cond-unknown {
		color: var(--dl-warn, #fbbf24);
		font-variant-numeric: tabular-nums;
	}
	.arrow {
		color: var(--dl-ink-dim, #475569);
	}
	.tally {
		margin-left: 4px;
		color: var(--dl-ink-mute, #94a3b8);
	}
	.tally strong {
		color: var(--dl-accent);
		font-variant-numeric: tabular-nums;
		font-size: 12px;
	}
	.chip {
		height: 22px;
		padding: 0 8px;
		border: 1px solid var(--dl-line, #1e2433);
		border-radius: 3px;
		background: transparent;
		color: var(--dl-ink-mute, #94a3b8);
		font-family: inherit;
		font-size: 11px;
		line-height: 1;
		cursor: pointer;
		white-space: nowrap;
	}
	.chip:hover {
		border-color: var(--dl-line-strong, #334155);
		color: var(--dl-ink, #f1f5f9);
	}
	.chip.on {
		border-color: rgba(var(--dl-accent-rgb), 0.5);
		background: rgba(var(--dl-accent-rgb), 0.08);
		color: var(--dl-accent);
	}
	.chip.relax {
		border-style: dashed;
		border-color: var(--dl-warn, #fbbf24);
		color: var(--dl-warn, #fbbf24);
	}
	.chip.relax:hover {
		background: rgba(251, 191, 36, 0.08);
	}
	.relax-n {
		margin-left: 4px;
		color: var(--dl-ink-dim, #64748b);
		font-variant-numeric: tabular-nums;
	}
</style>
