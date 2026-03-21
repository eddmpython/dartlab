<!--
	VirtualScroller — 순수 Svelte 5 가상 스크롤.
	1000행+ 테이블에서 DOM 노드를 최소화.
-->
<script>
	let {
		items = [],
		itemHeight = 32,
		overscan = 5,
		containerHeight = 400,
		children,
	} = $props();

	let scrollTop = $state(0);
	let containerEl = $state(null);

	let totalHeight = $derived(items.length * itemHeight);

	let visibleRange = $derived.by(() => {
		const start = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
		const visibleCount = Math.ceil(containerHeight / itemHeight) + 2 * overscan;
		const end = Math.min(items.length, start + visibleCount);
		return { start, end };
	});

	let visibleItems = $derived(
		items.slice(visibleRange.start, visibleRange.end).map((item, i) => ({
			item,
			index: visibleRange.start + i,
			offsetY: (visibleRange.start + i) * itemHeight,
		}))
	);

	function onScroll() {
		if (containerEl) scrollTop = containerEl.scrollTop;
	}
</script>

<div
	bind:this={containerEl}
	class="overflow-y-auto"
	style="height: {containerHeight}px"
	onscroll={onScroll}
>
	<div style="height: {totalHeight}px; position: relative">
		{#each visibleItems as { item, index, offsetY } (index)}
			<div style="position: absolute; top: {offsetY}px; left: 0; right: 0; height: {itemHeight}px">
				{@render children(item, index)}
			</div>
		{/each}
	</div>
</div>
