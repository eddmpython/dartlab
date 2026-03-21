<!--
	SkeletonTable — 테이블 로딩 플레이스홀더.
	3-5행의 시머 스켈레톤으로 데이터 로딩 중임을 시각적으로 표시.
-->
<script>
	let { rows = 4, cols = 4 } = $props();
</script>

<div class="overflow-hidden rounded-lg border border-dl-border/10">
	<div class="flex gap-0 border-b border-dl-border/10 bg-dl-bg-card/30 px-3 py-2.5">
		{#each Array(cols) as _, c}
			<div class="flex-1 px-2">
				<div class="skeleton-line h-[10px] w-{c === 0 ? 'full' : '[60%]'}"></div>
			</div>
		{/each}
	</div>
	{#each Array(rows) as _, r}
		<div class="flex gap-0 px-3 py-2.5 border-b border-dl-border/5" style="--stagger-index: {r}">
			{#each Array(cols) as _, c}
				<div class="flex-1 px-2">
					<div class="skeleton-line h-[10px]" style="width: {c === 0 ? 70 + r * 5 : 40 + (c * 15) % 50}%"></div>
				</div>
			{/each}
		</div>
	{/each}
</div>
