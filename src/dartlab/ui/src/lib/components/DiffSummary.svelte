<!--
	DiffSummary — topic 변경 요약 카드.
	diff/{topic}/summary API 응답을 시각화한다.
-->
<script>
	import { TrendingUp, Minus, ArrowRight } from "lucide-svelte";

	let { summary = null } = $props();
</script>

{#if summary}
	<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20">
		<div class="flex items-center gap-3 text-[11px] text-dl-text-dim">
			<span class="font-mono">{summary.totalPeriods} periods</span>
			{#if summary.changedCount > 0}
				<span class="flex items-center gap-1">
					<TrendingUp size={11} class="text-dl-accent" />
					<span class="text-dl-accent">변경 {summary.changedCount}회</span>
					<span class="text-dl-text-dim/60">({(summary.changeRate * 100).toFixed(1)}%)</span>
				</span>
			{:else}
				<span class="flex items-center gap-1">
					<Minus size={11} />
					<span>변경 없음</span>
				</span>
			{/if}
			{#if summary.latestFrom && summary.latestTo}
				<span class="flex items-center gap-1 ml-auto">
					<span class="font-mono">{summary.latestFrom}</span>
					<ArrowRight size={10} />
					<span class="font-mono">{summary.latestTo}</span>
				</span>
			{/if}
		</div>

		{#if summary.added?.length > 0 || summary.removed?.length > 0}
			<div class="text-[11px] leading-relaxed">
				{#each summary.added.slice(0, 2) as line}
					<div class="text-dl-success/80 truncate">+ {line}</div>
				{/each}
				{#each summary.removed.slice(0, 2) as line}
					<div class="text-dl-primary-light/70 truncate">- {line}</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}
