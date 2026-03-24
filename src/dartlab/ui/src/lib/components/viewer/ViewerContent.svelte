<script>
	import ViewerHeading from "./ViewerHeading.svelte";
	import ViewerText from "./ViewerText.svelte";
	import ViewerTable from "./ViewerTable.svelte";
	import ViewerToolbar from "./ViewerToolbar.svelte";

	let { doc = null, onPeriodChange = null } = $props();

	let collapsedHeadings = $state(new Set());
	let collapsedFolds = $state(new Set());
	let viewMode = $state("unified"); // unified | changesOnly
	let visibleCount = $state(40);
	let sentinel = $state(null);

	$effect(() => { if (doc) { visibleCount = 40; collapsedHeadings = new Set(); collapsedFolds = new Set(); } });

	$effect(() => {
		if (!sentinel) return;
		const obs = new IntersectionObserver((entries) => {
			if (entries[0]?.isIntersecting) visibleCount = Math.min(visibleCount + 30, doc?.blocks?.length || 999);
		}, { rootMargin: "600px" });
		obs.observe(sentinel);
		return () => obs.disconnect();
	});

	function isVisible(block) {
		// heading 접기: 조상 heading이 접혀있으면 숨김
		let pid = block.parentId;
		while (pid) {
			if (collapsedHeadings.has(pid)) return false;
			const parent = doc.blocks.find(b => b.id === pid);
			pid = parent?.parentId || null;
		}
		// changesOnly 모드
		if (viewMode === "changesOnly" && block.status === "unchanged" && block.kind !== "heading") return false;
		return true;
	}

	function toggleHeading(id) {
		const next = new Set(collapsedHeadings);
		if (next.has(id)) next.delete(id); else next.add(id);
		collapsedHeadings = next;
	}

	function toggleFold(groupId) {
		const next = new Set(collapsedFolds);
		if (next.has(groupId)) next.delete(groupId); else next.add(groupId);
		collapsedFolds = next;
	}

	let visibleBlocks = $derived(() => {
		if (!doc?.blocks) return [];
		const result = [];
		let foldGroupSeen = new Set();
		for (const block of doc.blocks) {
			if (!isVisible(block)) continue;
			// fold 그룹: 접혀있으면 첫 블록만 placeholder로
			if (block.foldable && block.foldGroupId && !collapsedFolds.has(block.foldGroupId)) {
				if (!foldGroupSeen.has(block.foldGroupId)) {
					foldGroupSeen.add(block.foldGroupId);
					const count = doc.blocks.filter(b => b.foldGroupId === block.foldGroupId).length;
					result.push({ _foldPlaceholder: true, foldGroupId: block.foldGroupId, count });
				}
				continue;
			}
			result.push(block);
		}
		return result;
	});
</script>

{#if doc}
	<ViewerToolbar {doc} bind:viewMode {onPeriodChange} />

	<div class="vw2-blocks">
		{#each visibleBlocks().slice(0, visibleCount) as block (block._foldPlaceholder ? `fold-${block.foldGroupId}` : block.id)}
			{#if block._foldPlaceholder}
				<button class="vw2-fold-bar" onclick={() => toggleFold(block.foldGroupId)}>
					<span class="vw2-fold-label">변경 없음 {block.count}개 블록</span>
					<span class="vw2-fold-expand">펼치기</span>
				</button>
			{:else if block.kind === "heading"}
				<ViewerHeading {block} collapsed={collapsedHeadings.has(block.id)} onToggle={() => toggleHeading(block.id)} />
			{:else if block.kind === "text"}
				<ViewerText {block} />
			{:else if block.kind === "table"}
				<ViewerTable {block} />
			{/if}
		{/each}
		{#if visibleCount < (visibleBlocks().length || 0)}
			<div bind:this={sentinel} class="h-4"></div>
		{/if}
	</div>
{/if}
