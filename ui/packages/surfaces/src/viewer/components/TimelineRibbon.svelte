<script lang="ts">
	// 타임라인 리본 · 전체 기간 축(최신좌측) 칩 + 현재 윈도우 강조 + 좌(최신)/우(과거) 이동.
	// ui/web TimelineRibbon 이식, scan 디자인(다크 #050811 + 오렌지 단일 액센트).
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	let {
		periods,
		windowPeriods,
		onpick,
		onnewer,
		onolder,
		canNewer,
		canOlder
	}: {
		periods: string[];
		windowPeriods: string[];
		onpick: (p: string) => void;
		onnewer: () => void;
		onolder: () => void;
		canNewer: boolean;
		canOlder: boolean;
	} = $props();

	const winSet = $derived(new Set(windowPeriods));
	const windowStart = $derived(windowPeriods[0]);
	const windowLast = $derived(windowPeriods[windowPeriods.length - 1]);
</script>

{#if periods.length}
	<div class="ribbon">
		<button type="button" class="chev" disabled={!canNewer} onclick={onnewer} title="더 최신으로" aria-label="더 최신으로">
			<ChevronLeft size={16} />
		</button>
		<div class="track">
			<div class="chips">
				{#each periods as p (p)}
					<button
						type="button"
						class="chip"
						class:in-window={winSet.has(p)}
						class:start={p === windowStart}
						class:end={p === windowLast}
						onclick={() => onpick(p)}
						title={p}
					>
						{p}
					</button>
				{/each}
			</div>
		</div>
		<button type="button" class="chev" disabled={!canOlder} onclick={onolder} title="더 과거로" aria-label="더 과거로">
			<ChevronRight size={16} />
		</button>
	</div>
{/if}

<style>
	.ribbon {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.chev {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		flex-shrink: 0;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #050811;
		color: #cbd5e1;
		cursor: pointer;
	}
	.chev:hover:not(:disabled) {
		border-color: var(--amber);
		color: var(--amber);
	}
	.chev:disabled {
		opacity: 0.3;
		cursor: default;
	}
	.track {
		min-width: 0;
		flex: 1 1 auto;
		overflow-x: auto;
		scrollbar-width: thin;
	}
	.chips {
		display: flex;
		align-items: stretch;
		gap: 1px;
	}
	.chip {
		flex-shrink: 0;
		padding: 4px 8px;
		font-family: monospace;
		font-size: 10px;
		border: 1px solid transparent;
		border-top-color: #1e2433;
		border-bottom-color: #1e2433;
		background: transparent;
		color: #94a3b8;
		cursor: pointer;
		white-space: nowrap;
		transition: background 0.12s, color 0.12s;
	}
	.chip:hover {
		background: rgba(var(--amber-rgb), 0.06);
		color: #e2e8f0;
	}
	.chip.in-window {
		background: rgba(var(--amber-rgb), 0.12);
		border-color: rgba(var(--amber-rgb), 0.4);
		color: #f1f5f9;
	}
	.chip.start {
		border-top-left-radius: 5px;
		border-bottom-left-radius: 5px;
		border-left-color: rgba(var(--amber-rgb), 0.4);
	}
	.chip.end {
		border-top-right-radius: 5px;
		border-bottom-right-radius: 5px;
		border-right-color: rgba(var(--amber-rgb), 0.4);
	}
</style>
