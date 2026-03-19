<!--
	TimelineBar — 기간 선택 바.
	periods 배열을 받아 가로 타임라인으로 표시한다.
	선택한 기간을 onSelect로 전달.
-->
<script>
	let {
		periods = [],           // ["2025Q4", "2025Q3", ...]
		selected = null,        // 현재 선택된 기간
		onSelect = null,        // (period) => void
	} = $props();

	function isAnnual(p) { return /^\d{4}$/.test(p) || /^\d{4}Q4$/.test(p); }
	function displayLabel(p) {
		// 2025Q4 → '25.4Q, 2025Q1 → '25.1Q, 2025 → '25
		const m = p.match(/^(\d{4})(Q([1-4]))?$/);
		if (!m) return p;
		const shortYear = "'" + m[1].slice(2);
		return m[3] ? `${shortYear}.${m[3]}Q` : shortYear;
	}
</script>

{#if periods.length > 0}
	<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin">
		{#each periods as p}
			<button
				class="flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					{selected === p
						? 'bg-dl-primary/20 text-dl-primary-light font-medium'
						: isAnnual(p)
							? 'text-dl-text-muted hover:text-dl-text hover:bg-white/5'
							: 'text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5'}"
				onclick={() => onSelect?.(p)}
				title={p}
			>
				{displayLabel(p)}
			</button>
		{/each}
	</div>
{/if}
